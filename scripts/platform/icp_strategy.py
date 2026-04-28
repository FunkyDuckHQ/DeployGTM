from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .context_pack import build_context_pack
from .intake import load_intake


PROJECTS_DIR = Path("projects")


def _derive_market_hypotheses(principles: list[dict]) -> list[str]:
    hypotheses = []
    for p in principles:
        text = (p.get("principle_text") or "").lower()
        if "icp" in text:
            hypotheses.append("Prioritize segments with strongest ICP-fit confidence first.")
        if "signal" in text:
            hypotheses.append("Weight active, verifiable signals above static firmographics.")
        if "open loops" in text or "blocker" in text:
            hypotheses.append("Exclude accounts blocked by unresolved procurement or integration constraints.")

    if not hypotheses:
        hypotheses.append("Start with one market segment and iterate weekly based on scoring outcomes.")

    seen = set()
    unique = []
    for h in hypotheses:
        if h not in seen:
            seen.add(h)
            unique.append(h)
    return unique[:5]


def _derive_icps(client_slug: str, intake: dict, principles: list[dict]) -> list[dict]:
    outcome = intake.get("target_outcome") or "the desired customer outcome"
    offer = intake.get("offer") or "the customer's offer"
    source_trace = [
        trace
        for principle in principles
        for trace in principle.get("source_trace", [])
    ][:4]

    return [
        {
            "name": "Primary outcome owner",
            "description": f"Companies where a named owner is accountable for {outcome}.",
            "fit_criteria": [
                "Clear business pain tied to the target outcome",
                "A buyer persona has budget or execution ownership",
                "The account shows public evidence of timing or change",
                "The customer's offer can plausibly resolve the pain",
            ],
            "personas": [
                {
                    "title": "Economic owner",
                    "problem_ownership_reason": f"Owns whether {offer} can create the promised business result.",
                },
                {
                    "title": "Operational owner",
                    "problem_ownership_reason": "Feels the current workflow pain and can validate urgency.",
                },
            ],
            "disqualifiers": [
                "No named owner for the problem",
                "Problem is not painful enough to change behavior",
                "Signal is stale or cannot be verified",
            ],
            "source_trace": source_trace,
        },
        {
            "name": "Expansion or adjacent segment",
            "description": f"Accounts adjacent to the primary ICP where signals suggest emerging demand for {offer}.",
            "fit_criteria": [
                "Same pain pattern appears in a nearby segment",
                "Signal recency is strong enough to justify testing",
                "Messaging can be adapted without changing the core offer",
            ],
            "personas": [
                {
                    "title": "Functional leader",
                    "problem_ownership_reason": "Owns the team or process affected by the pain.",
                }
            ],
            "disqualifiers": [
                "Requires a materially different product",
                "Requires a channel the client cannot support",
            ],
            "source_trace": source_trace,
        },
    ]


def generate_icp_strategy(client_slug: str, projects_dir: Path = PROJECTS_DIR) -> Path:
    pack = build_context_pack(client_slug)
    intake = load_intake(client_slug, projects_dir=projects_dir)

    output_dir = projects_dir / client_slug / "platform"
    output_dir.mkdir(parents=True, exist_ok=True)
    context_pack_path = output_dir / "context_pack.json"
    out_path = output_dir / "icp_strategy.json"

    # Persist the exact context pack used for this strategy run.
    context_pack_path.write_text(json.dumps(pack, indent=2))

    principles = pack.get("principles", [])
    strategy = {
        "schema_version": "v1.0",
        "client_slug": client_slug,
        "generated_on": date.today().isoformat(),
        "inputs": {
            "context_pack_path": str(context_pack_path),
            "principle_count": len(principles),
            "intake_path": str(output_dir / "intake.json"),
        },
        "strategy": {
            "principles": principles,
            "icps": _derive_icps(client_slug, intake, principles),
            "market_hypotheses": _derive_market_hypotheses(principles),
            "scoring_matrix": {
                "icp_fit_score": "0-100 based on customer-specific fit criteria, disqualifiers, and evidence confidence.",
                "urgency_score": "0-100 based on current BirdDog/manual signals, source strength, and recency decay.",
                "engagement_score": "0-100 based on email/CRM engagement once tests begin; defaults to 0 during audit.",
                "confidence_score": "0-100 based on source quality and completeness of enrichment.",
                "activation_priority": "Weighted blend used for action ordering; does not hide ICP fit or urgency.",
            },
            "segment_rules": [
                "Only include segments with clear problem ownership by a named persona.",
                "Prefer segments with publicly verifiable timing signals."
            ],
            "persona_rules": [
                "Map each segment to one primary buyer title.",
                "Require one sentence on why that persona owns the problem."
            ],
            "angle_rules": [
                "Angles must be directional claims, not generic pain statements.",
                "Each angle must tie back to one observable signal category."
            ]
        },
    }

    out_path.write_text(json.dumps(strategy, indent=2))
    return out_path
