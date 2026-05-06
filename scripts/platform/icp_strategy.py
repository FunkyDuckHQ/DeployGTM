from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .context_pack import build_context_pack
from .intake import load_intake
from .llm import Provider, call_json


PROJECTS_DIR = Path("projects")
BRAIN_DIR = Path("brain")

ICP_SYSTEM = """\
You are a GTM strategy expert helping a B2B GTM engineering practice called DeployGTM.

Your job: given a client's intake data, project context, and master brain, produce a
precise ICP strategy document for THIS specific client and market — not generic
frameworks.

Rules:
- Name ICPs by real market segment (e.g. "Commercial NewSpace EO Operators", not
  "Primary outcome owner").
- Buyer personas must use real job titles for this market (e.g. "VP Mission Systems",
  not "Economic owner").
- Fit criteria and disqualifiers must be specific and verifiable, not abstract.
- Market hypotheses must be directional bets about THIS market, not platitudes.
- Return valid JSON only. No explanation, no markdown outside the JSON block.
"""

ICP_SCHEMA = """\
Return this exact JSON shape:
{
  "icps": [
    {
      "name": "<short segment label, 2-5 words>",
      "description": "<1-2 sentences: what these companies are and why they buy>",
      "fit_criteria": ["<verifiable criterion 1>", ...],
      "personas": [
        {
          "title": "<exact job title>",
          "problem_ownership_reason": "<one sentence: why this person owns the pain>"
        }
      ],
      "disqualifiers": ["<concrete disqualifier>", ...],
      "why_now_signals": ["<observable trigger that means act now>", ...]
    }
  ],
  "market_hypotheses": [
    "<directional bet about this specific market, 1 sentence>"
  ],
  "segment_rules": ["<rule>"],
  "persona_rules": ["<rule>"],
  "angle_rules": ["<rule>"]
}

Generate 2-3 ICPs. At least 3 fit_criteria, 2 disqualifiers, 2 why_now_signals per ICP.
"""


def _read_brain() -> str:
    brain_dir = BRAIN_DIR
    files = ["icp.md", "personas.md", "product.md", "objections.md", "messaging.md"]
    sections = []
    for fname in files:
        p = brain_dir / fname
        if p.exists():
            sections.append(f"### brain/{fname}\n\n{p.read_text().strip()}")
    return "\n\n---\n\n".join(sections)


def _build_icp_prompt(intake: dict, principles: list[dict], brain: str) -> str:
    constraints = "\n".join(f"- {c}" for c in intake.get("constraints", [])) or "- None specified"
    tools_raw = intake.get("current_tools") or {}
    tools = "\n".join(f"- {k}: {v}" for k, v in tools_raw.items()) or "- None"
    known_ctx = intake.get("known_context") or "None provided."

    principle_text = ""
    for p in principles[:8]:
        principle_text += f"- {p.get('principle_text', '')}\n"

    return f"""\
CLIENT INTAKE
=============
Company: {intake.get('client_name')}
Domain:  {intake.get('domain')}
Outcome: {intake.get('target_outcome')}
Offer:   {intake.get('offer')}

Constraints:
{constraints}

Current tools:
{tools}

Known context:
{known_ctx}

PRINCIPLES (derived from client context)
=========================================
{principle_text.strip()}

DEPLOYGTM MASTER BRAIN
=======================
{brain}

TASK
====
Generate the ICP strategy for this client's specific market.
{ICP_SCHEMA}"""


def _fallback_icps(intake: dict) -> dict:
    """Deterministic fallback used when LLM_SKIP=true or on hard error."""
    outcome = intake.get("target_outcome") or "the desired customer outcome"
    offer = intake.get("offer") or "the customer's offer"
    return {
        "icps": [
            {
                "name": "Primary buyer segment",
                "description": f"Companies where a named owner needs: {outcome[:120]}.",
                "fit_criteria": [
                    "Clear business pain tied to the target outcome",
                    "A buyer persona has budget or execution ownership",
                    "The account shows public evidence of timing or change",
                ],
                "personas": [
                    {
                        "title": "Decision maker",
                        "problem_ownership_reason": f"Owns whether {offer[:80]} delivers the promised result.",
                    }
                ],
                "disqualifiers": [
                    "No named owner for the problem",
                    "Signal is stale or cannot be verified",
                ],
                "why_now_signals": [
                    "Recent funding or budget event",
                    "Public statement of the problem",
                ],
            }
        ],
        "market_hypotheses": [
            "Active, verifiable signals outperform static firmographics for prioritization.",
        ],
        "segment_rules": ["Only include segments with a named persona and verifiable signal."],
        "persona_rules": ["Map each segment to one primary buyer title with clear ownership reason."],
        "angle_rules": ["Every outreach angle must tie back to one observable signal."],
    }


def generate_icp_strategy(client_slug: str, projects_dir: Path = PROJECTS_DIR) -> Path:
    pack = build_context_pack(client_slug)
    intake = load_intake(client_slug, projects_dir=projects_dir)

    output_dir = projects_dir / client_slug / "platform"
    output_dir.mkdir(parents=True, exist_ok=True)
    context_pack_path = output_dir / "context_pack.json"
    out_path = output_dir / "icp_strategy.json"

    context_pack_path.write_text(json.dumps(pack, indent=2))

    principles = pack.get("principles", [])
    brain = _read_brain()
    prompt = _build_icp_prompt(intake, principles, brain)
    fallback = _fallback_icps(intake)

    llm_out = call_json(
        prompt=prompt,
        system=ICP_SYSTEM,
        task="icp_strategy",
        provider=Provider.CLAUDE,
        fallback=fallback,
    )

    # Merge LLM output into the canonical strategy envelope
    strategy = {
        "schema_version": "v1.0",
        "client_slug": client_slug,
        "generated_on": date.today().isoformat(),
        "llm_provider": "claude",
        "inputs": {
            "context_pack_path": str(context_pack_path),
            "principle_count": len(principles),
            "intake_path": str(output_dir / "intake.json"),
        },
        "strategy": {
            "principles": principles,
            "icps": llm_out.get("icps", fallback["icps"]),
            "market_hypotheses": llm_out.get("market_hypotheses", fallback["market_hypotheses"]),
            "scoring_matrix": {
                "icp_fit_score": "0-100 based on customer-specific fit criteria, disqualifiers, and evidence confidence.",
                "urgency_score": "0-100 based on current BirdDog/manual signals, source strength, and recency decay.",
                "engagement_score": "0-100 based on email/CRM engagement once tests begin; defaults to 0 during audit.",
                "confidence_score": "0-100 based on source quality and completeness of enrichment.",
                "activation_priority": "Weighted blend used for action ordering; does not hide ICP fit or urgency.",
            },
            "segment_rules": llm_out.get("segment_rules", fallback["segment_rules"]),
            "persona_rules": llm_out.get("persona_rules", fallback["persona_rules"]),
            "angle_rules": llm_out.get("angle_rules", fallback["angle_rules"]),
        },
    }

    out_path.write_text(json.dumps(strategy, indent=2))
    return out_path
