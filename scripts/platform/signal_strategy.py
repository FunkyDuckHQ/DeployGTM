from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .icp_strategy import generate_icp_strategy


PROJECTS_DIR = Path("projects")


SIGNAL_TEMPLATES = [
    ("funding_recent", "Recent funding", "capital_event", 90, "Funding announcement in the last 90 days"),
    ("sales_hiring", "Sales hiring", "hiring", 75, "New SDR, AE, RevOps, or sales leadership job posts"),
    ("exec_change", "Revenue leadership change", "leadership", 70, "New CRO, VP Sales, VP Marketing, or founder GTM change"),
    ("product_launch", "Product launch", "market_motion", 65, "New product, tier, integration, or market expansion"),
    ("geo_expansion", "Geographic expansion", "market_motion", 55, "New market, region, office, or localized GTM motion"),
    ("tech_adoption", "Relevant tool adoption", "technology", 60, "New CRM, data, warehouse, outbound, or workflow tool detected"),
    ("tech_replacement", "Tool replacement window", "technology", 65, "Public signal that an existing system is being replaced"),
    ("competitor_hiring", "Competitor pressure", "market", 60, "Competitors are hiring, launching, or entering their segment"),
    ("partner_motion", "Partner ecosystem activity", "market", 50, "New channel, marketplace, or integration partner motion"),
    ("security_compliance", "Compliance pressure", "risk", 50, "New security, compliance, procurement, or audit requirement"),
    ("review_negativity", "Negative reviews", "pain", 70, "Recent reviews mention pain the client solves"),
    ("social_pain", "Public pain post", "pain", 85, "Founder or buyer posts about a problem the client solves"),
    ("community_question", "Community buying question", "pain", 70, "Target persona asks for recommendations or alternatives"),
    ("agency_churn", "Agency/vendor churn", "pain", 70, "Account shows dissatisfaction with current agency, vendor, or workaround"),
    ("manual_workaround", "Manual process workaround", "pain", 65, "Job posts or content imply spreadsheet/manual operating pain"),
    ("budget_cycle", "Budget or planning window", "timing", 55, "Annual planning, budget allocation, or board pressure signal"),
    ("event_attendance", "Relevant event activity", "timing", 45, "Account attends, sponsors, or speaks at market-relevant events"),
    ("content_theme", "Repeated content theme", "education", 45, "Company repeatedly publishes around the problem space"),
    ("customer_trigger", "Their customer trigger", "downstream", 60, "Their own customers are changing in ways that create demand"),
    ("data_quality_gap", "Data quality gap", "operations", 65, "Signals of incomplete CRM, messy data, or reporting gaps"),
]


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _icp_names(strategy: dict) -> list[str]:
    icps = strategy.get("strategy", {}).get("icps", [])
    names = [icp.get("name") for icp in icps if icp.get("name")]
    return names or ["Primary ICP", "Expansion ICP"]


def build_signal_strategy(client_slug: str, projects_dir: Path = PROJECTS_DIR) -> Path:
    platform_dir = projects_dir / client_slug / "platform"
    platform_dir.mkdir(parents=True, exist_ok=True)

    icp_path = platform_dir / "icp_strategy.json"
    if not icp_path.exists():
        generate_icp_strategy(client_slug, projects_dir=projects_dir)

    icp_strategy = _load_json(icp_path)
    intake = _load_json(platform_dir / "intake.json")
    icps = _icp_names(icp_strategy)
    outcome = intake.get("target_outcome") or "the customer's stated outcome"
    offer = intake.get("offer") or "the customer's offer"

    signals = []
    for index, (signal_id, name, category, weight, description) in enumerate(SIGNAL_TEMPLATES, start=1):
        mapped_icp = icps[(index - 1) % len(icps)]
        signals.append(
            {
                "id": signal_id,
                "display_order": index,
                "name": name,
                "category": category,
                "description": description,
                "why_it_matters": f"Indicates a possible path to {outcome} for buyers of {offer}.",
                "mapped_icp": mapped_icp,
                "bird_dog_query_hint": f"{name}: {description}. Prioritize accounts matching {mapped_icp}.",
                "evidence_required": [
                    "company domain",
                    "source URL or source system",
                    "observed date",
                    "one-sentence summary",
                ],
                "urgency_weight": weight,
                "decay": {
                    "half_life_days": 30 if weight >= 70 else 60,
                    "stale_after_days": 90,
                },
                "crm_note_template": f"{name} signal: {{signal_summary}}. Relevance: {mapped_icp}.",
            }
        )

    strategy = {
        "schema_version": "v1.0",
        "client_slug": client_slug,
        "generated_on": date.today().isoformat(),
        "source": {
            "intake_path": str(platform_dir / "intake.json"),
            "icp_strategy_path": str(icp_path),
        },
        "signals": signals,
        "bird_dog": {
            "write_mode": "manifest_only_until_api_verified",
            "recommended_account_workflow": "Upload or configure these signals first, then review BirdDog recommended accounts before adding to monitoring.",
            "fallback_account_monitoring": "If custom signal creation is unavailable, export top-scored accounts to BirdDog watchlists and pull alerts back into accounts.json.",
        },
    }

    out_path = platform_dir / "signal_strategy.json"
    out_path.write_text(json.dumps(strategy, indent=2))

    manifest_path = platform_dir / "birddog_signal_manifest.json"
    manifest = {
        "schema_version": "v1.0",
        "client_slug": client_slug,
        "write_mode": "manual_review_required",
        "signals": [
            {
                "name": signal["name"],
                "category": signal["category"],
                "query_hint": signal["bird_dog_query_hint"],
                "urgency_weight": signal["urgency_weight"],
            }
            for signal in signals
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))

    return out_path
