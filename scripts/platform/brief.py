from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .llm import Provider, call_json


PROJECTS_DIR = Path("projects")
BRAIN_DIR = Path("brain")

BRIEF_SYSTEM = """\
You are a GTM strategist preparing account briefs for B2B sales reps at DeployGTM.

Your job: given one target account's data, produce a concise, actionable brief that a
rep can read in under 2 minutes before outreach or a discovery call.

Rules:
- Every section must be specific to THIS account and THIS signal — not generic.
- Talking points must reference observable evidence (the signal, the company's situation).
- Objections must come from the client's real objection list — do not invent new ones.
- Recommended ask must be concrete (e.g., "Book a Signal Audit discovery call" not "connect").
- Return valid JSON only. No explanation, no markdown outside the JSON block.
"""

BRIEF_SCHEMA = """\
Return this exact JSON shape:
{
  "account_snapshot": {
    "company": "<company name>",
    "domain": "<domain>",
    "icp_match": "<matched ICP segment name>",
    "persona_to_target": "<exact job title to reach>",
    "activation_priority": <integer score>,
    "signal": "<one sentence: what was observed and when>"
  },
  "why_now": "<one sentence: why this account is worth contacting right now, tied to the signal>",
  "talking_points": [
    "<specific, evidence-based talking point 1>",
    "<specific, evidence-based talking point 2>",
    "<specific, evidence-based talking point 3>"
  ],
  "likely_objections": [
    {
      "objection": "<the objection they're likely to raise>",
      "response": "<how to handle it, from DeployGTM playbook>"
    }
  ],
  "recommended_ask": "<one concrete ask — what should happen at the end of the first conversation>",
  "disqualify_if": "<one condition that would immediately remove this account from pursuit>"
}

Generate 3-5 talking points and 2-3 likely objections.
Every talking point must be tied to the signal or the account's situation — not generic.
Objections must come from the DeployGTM objection list provided — pick the most likely ones for this account.
"""


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _read_brain_file(filename: str) -> str:
    path = BRAIN_DIR / filename
    return path.read_text().strip() if path.exists() else ""


def _fallback_brief(account: dict) -> dict:
    company = account.get("company", "Unknown")
    domain = account.get("domain", "")
    matched_icp = account.get("matched_icp", "Primary ICP")
    persona = account.get("recommended_persona", "Decision maker")
    scores = account.get("scores", {})
    activation = scores.get("activation_priority", 0)
    signal = (account.get("signals") or [{}])[0]
    signal_summary = signal.get("summary", "signal detected")
    angle = account.get("recommended_angle", "")

    return {
        "account_snapshot": {
            "company": company,
            "domain": domain,
            "icp_match": matched_icp,
            "persona_to_target": persona,
            "activation_priority": activation,
            "signal": signal_summary,
        },
        "why_now": angle or f"{company} is showing buying signals that indicate near-term readiness.",
        "talking_points": [
            f"Observed: {signal_summary}",
            "Most companies at this stage lack signal-to-pipeline infrastructure.",
            "Signal Audit delivers a working system in 2 weeks for $3,500.",
        ],
        "likely_objections": [
            {
                "objection": "We already have tools like Clay or Apollo.",
                "response": "Having tools isn't the same as having a system. The missing piece is orchestration — signal detection, scoring, and the closed-loop that connects them.",
            },
            {
                "objection": "We're not sure about the budget right now.",
                "response": "Understood. When does budget open up? I'd rather talk when you can act than waste both our time now.",
            },
        ],
        "recommended_ask": "Book a 20-minute Signal Audit discovery call.",
        "disqualify_if": "No named owner for the problem or signal cannot be verified.",
    }


def _build_brief_prompt(
    account: dict,
    intake: dict,
    icp_strategy: dict,
    objections_brain: str,
    personas_brain: str,
) -> str:
    company = account.get("company", "Unknown")
    domain = account.get("domain", "")
    matched_icp = account.get("matched_icp", "")
    recommended_persona = account.get("recommended_persona", "")
    recommended_angle = account.get("recommended_angle", "")
    signals = account.get("signals", [{}])
    signal = signals[0] if signals else {}
    signal_type = signal.get("type", "manual")
    signal_summary = signal.get("summary", "")
    signal_date = signal.get("date", "")
    signal_source = signal.get("source", "")

    scores = account.get("scores", {})
    icp_fit = scores.get("icp_fit_score", "")
    urgency = scores.get("urgency_score", "")
    activation = scores.get("activation_priority", "")
    rationale = scores.get("rationale", [])
    rationale_text = "; ".join(rationale) if isinstance(rationale, list) else str(rationale)
    disqualifiers = scores.get("disqualifiers", [])

    copy = account.get("copy", {})
    first_touch = copy.get("first_touch", "")
    angle = copy.get("angle", recommended_angle)

    offer = intake.get("offer", "the client's offer")
    outcome = intake.get("target_outcome", "the target outcome")

    # Pull ICP-specific context
    icp_context = ""
    for icp in icp_strategy.get("strategy", {}).get("icps", []):
        if icp.get("name") == matched_icp:
            must_have = "; ".join(icp.get("must_have", []))
            disq_list = "; ".join(icp.get("disqualifiers", []))
            angle_tmpl = icp.get("angle_template", "")
            icp_context = (
                f"ICP must-have criteria: {must_have}\n"
                f"ICP disqualifiers: {disq_list}\n"
                f"ICP angle template: {angle_tmpl}"
            )
            break

    disq_text = "; ".join(disqualifiers) if disqualifiers else "None flagged"

    return f"""\
DEPLOYGTM BUYER PERSONAS
========================
{personas_brain}

DEPLOYGTM OBJECTION HANDLING PLAYBOOK
======================================
{objections_brain}

ACCOUNT DATA
============
Company: {company}
Domain: {domain}
Matched ICP: {matched_icp}
{icp_context}

Recommended persona: {recommended_persona}
Recommended angle: {angle or recommended_angle}

Signal type: {signal_type}
Signal date: {signal_date}
Signal source: {signal_source}
Signal summary: {signal_summary}

ICP fit score: {icp_fit}
Urgency score: {urgency}
Activation priority: {activation}
Score rationale: {rationale_text}
Disqualifiers flagged: {disq_text}

First-touch copy (already drafted):
{first_touch}

CLIENT CONTEXT
==============
Offer: {offer}
Target outcome: {outcome}

TASK
====
Generate an account brief for this specific account. Use the objection handling
playbook above to select the 2-3 most likely objections for this account's situation.
{BRIEF_SCHEMA}"""


def _generate_brief_for_account(
    account: dict,
    intake: dict,
    icp_strategy: dict,
    objections_brain: str,
    personas_brain: str,
) -> dict:
    prompt = _build_brief_prompt(account, intake, icp_strategy, objections_brain, personas_brain)
    fallback = _fallback_brief(account)

    result = call_json(
        prompt=prompt,
        system=BRIEF_SYSTEM,
        task="brief",
        provider=Provider.CLAUDE,
        fallback=fallback,
        max_tokens=800,
        temperature=0.3,
    )

    return result if result else fallback


def build_briefs(client_slug: str, projects_dir: Path = PROJECTS_DIR) -> Path:
    platform_dir = projects_dir / client_slug / "platform"
    matrix_path = platform_dir / "accounts.json"

    if not matrix_path.exists():
        raise FileNotFoundError(f"accounts.json not found at {matrix_path}. Run account-matrix first.")

    intake = _load_json(platform_dir / "intake.json")
    icp_strategy = _load_json(platform_dir / "icp_strategy.json")
    matrix = _load_json(matrix_path)
    objections_brain = _read_brain_file("objections.md")
    personas_brain = _read_brain_file("personas.md")

    accounts = matrix.get("accounts", [])
    briefs = {}
    for account in accounts:
        company = account.get("company", "unknown")
        domain = account.get("domain", "")
        key = domain or company.lower().replace(" ", "-")
        briefs[key] = _generate_brief_for_account(
            account, intake, icp_strategy, objections_brain, personas_brain
        )

    briefs_path = platform_dir / "account_briefs.json"
    output = {
        "schema_version": "v1.0",
        "client_slug": client_slug,
        "generated_on": date.today().isoformat(),
        "briefs": briefs,
    }
    briefs_path.write_text(json.dumps(output, indent=2))

    return briefs_path
