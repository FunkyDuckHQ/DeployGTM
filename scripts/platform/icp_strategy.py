from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .context_pack import build_context_pack


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


def generate_icp_strategy(client_slug: str, projects_dir: Path = PROJECTS_DIR) -> Path:
    pack = build_context_pack(client_slug)

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
        },
        "strategy": {
            "principles": principles,
            "market_hypotheses": _derive_market_hypotheses(principles),
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
