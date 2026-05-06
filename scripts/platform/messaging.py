from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .llm import Provider, call_json


PROJECTS_DIR = Path("projects")
BRAIN_DIR = Path("brain")

MESSAGING_SYSTEM = """\
You are a B2B outbound copywriter working for DeployGTM, a GTM engineering practice.

You write first-touch cold outreach for Matthew Stegenga. Matthew sells Signal Audits
($3,500, 2-week engagement) and Pipeline Engine retainers ($7,500/month) to early-stage
B2B SaaS founders and sales leaders.

Non-negotiable rules:
- Under 100 words total. Every word earns its place.
- Lead with the specific signal — what was observed and where.
- Bridge to the pain they're probably experiencing right now.
- One clear ask at the end. Not "would love to connect." Something real.
- Write like a human who gives a shit. No AI language. No "I hope this finds you well."
  No "leveraging synergies." No "exciting opportunity."
- One signal, one pain, one ask. Do not pile on.
- Match the tone to the persona: founders want speed and autonomy; sales leaders want
  credibility and quick deployment; RevOps wants technical depth and system clarity.
- Return valid JSON only. No explanation, no markdown outside the JSON block.
"""

MESSAGING_SCHEMA = """\
Return this exact JSON shape:
{
  "subject_line": "<email subject, 4-8 words, specific to the signal>",
  "first_touch": "<the full message, under 100 words, no greeting like 'Hi [Name]'>",
  "linkedin_version": "<shorter version for LinkedIn DM, 2-3 sentences max>",
  "word_count": <integer: word count of first_touch>,
  "persona_matched": "<Founder-Seller | First Sales Leader | RevOps / Growth Person>",
  "signal_used": "<the specific signal you led with>",
  "angle": "<one sentence: the core pain hypothesis this message is built on>"
}

The first_touch must:
- Start with the signal (what was observed, specific and real)
- Bridge to the pain they're experiencing
- State the offer clearly (2-week Signal Audit, $3,500 or Pipeline Engine $7,500/month)
- End with one concrete ask
"""


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _read_messaging_brain() -> str:
    path = BRAIN_DIR / "messaging.md"
    return path.read_text().strip() if path.exists() else ""


def _read_personas_brain() -> str:
    path = BRAIN_DIR / "personas.md"
    return path.read_text().strip() if path.exists() else ""


def _fallback_message(account: dict, intake: dict) -> dict:
    company = account.get("company", "your company")
    signal_type = (account.get("signals") or [{}])[0].get("type", "activity")
    summary = (account.get("signals") or [{}])[0].get("summary", "")
    persona = account.get("recommended_persona", "Decision maker")
    angle = account.get("recommended_angle", "")
    offer = intake.get("offer", "our services")

    signal_line = summary or f"recent {signal_type} at {company}"
    pain_bridge = angle or f"companies at this stage often lack the infrastructure to act on it."

    first_touch = (
        f"Saw {signal_line}. {pain_bridge} "
        f"I do a 2-week Signal Audit for $3,500 — you walk away with a prioritized account list, "
        f"signal definitions, enriched contacts, and outreach templates. Worth a call?"
    )

    return {
        "subject_line": f"Signal Audit — {company}",
        "first_touch": first_touch,
        "linkedin_version": f"Saw {signal_line}. Worth a quick call about the Signal Audit?",
        "word_count": len(first_touch.split()),
        "persona_matched": "Founder-Seller",
        "signal_used": signal_line,
        "angle": angle or f"Indicates buying readiness for {offer}.",
    }


def _build_messaging_prompt(
    account: dict,
    intake: dict,
    icp_strategy: dict,
    messaging_brain: str,
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
    rationale = scores.get("rationale", [])
    rationale_text = "; ".join(rationale) if isinstance(rationale, list) else str(rationale)

    offer = intake.get("offer", "the client's offer")
    outcome = intake.get("target_outcome", "the target outcome")

    # Pull ICP angle template for matched segment
    angle_template = ""
    for icp in icp_strategy.get("strategy", {}).get("icps", []):
        if icp.get("name") == matched_icp:
            angle_template = icp.get("angle_template", "")
            break

    return f"""\
DEPLOYGTM MESSAGING FRAMEWORK
==============================
{messaging_brain}

BUYER PERSONAS
==============
{personas_brain}

ACCOUNT TO MESSAGE
==================
Company: {company}
Domain: {domain}
Matched ICP: {matched_icp}
Recommended persona title: {recommended_persona}
Recommended angle: {recommended_angle}
ICP angle template: {angle_template}

Signal type: {signal_type}
Signal date: {signal_date}
Signal source: {signal_source}
Signal summary: {signal_summary}

ICP fit score: {icp_fit}
Score rationale: {rationale_text}

CLIENT OFFER
============
Offer: {offer}
Outcome: {outcome}

TASK
====
Write first-touch cold outreach for this specific account using the signal above.
Apply the messaging framework strictly: signal → pain → offer → ask.
Match the persona from the buyer personas section.
{MESSAGING_SCHEMA}"""


def _generate_message_for_account(
    account: dict,
    intake: dict,
    icp_strategy: dict,
    messaging_brain: str,
    personas_brain: str,
) -> dict:
    prompt = _build_messaging_prompt(account, intake, icp_strategy, messaging_brain, personas_brain)
    fallback = _fallback_message(account, intake)

    result = call_json(
        prompt=prompt,
        system=MESSAGING_SYSTEM,
        task="messaging",
        provider=Provider.CLAUDE,
        fallback=fallback,
        max_tokens=600,
        temperature=0.4,
    )

    return {
        "status": "drafted",
        "sequence_mode": "draft_only",
        "first_touch": result.get("first_touch", fallback["first_touch"]),
        "subject_line": result.get("subject_line", fallback["subject_line"]),
        "linkedin_version": result.get("linkedin_version", fallback["linkedin_version"]),
        "word_count": result.get("word_count", len(result.get("first_touch", "").split())),
        "persona_matched": result.get("persona_matched", fallback["persona_matched"]),
        "signal_used": result.get("signal_used", fallback["signal_used"]),
        "angle": result.get("angle", fallback["angle"]),
        "followups": [],
    }


def build_messaging(client_slug: str, projects_dir: Path = PROJECTS_DIR) -> Path:
    platform_dir = projects_dir / client_slug / "platform"
    matrix_path = platform_dir / "accounts.json"

    if not matrix_path.exists():
        raise FileNotFoundError(f"accounts.json not found at {matrix_path}. Run account-matrix first.")

    intake = _load_json(platform_dir / "intake.json")
    icp_strategy = _load_json(platform_dir / "icp_strategy.json")
    matrix = _load_json(matrix_path)
    messaging_brain = _read_messaging_brain()
    personas_brain = _read_personas_brain()

    accounts = matrix.get("accounts", [])
    updated = []
    for account in accounts:
        copy = _generate_message_for_account(account, intake, icp_strategy, messaging_brain, personas_brain)
        account["copy"] = copy
        updated.append(account)

    matrix["accounts"] = updated
    matrix["messaging_generated_on"] = date.today().isoformat()
    matrix_path.write_text(json.dumps(matrix, indent=2))

    return matrix_path
