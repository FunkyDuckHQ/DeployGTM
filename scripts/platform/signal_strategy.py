from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .icp_strategy import generate_icp_strategy
from .llm import Provider, call_json


PROJECTS_DIR = Path("projects")

SIGNAL_SYSTEM = """\
You are a GTM signal intelligence expert helping DeployGTM build BirdDog-ready
signal definitions for a specific client and market.

Your job: generate buying signals that are specific and observable for THIS client's
market — not a generic list that would apply to any B2B company.

Rules:
- Every signal must be observable via public sources (job boards, SAM.gov, press,
  LinkedIn, funding databases, government award databases, etc.).
- Signal names and descriptions must reflect the client's actual buyer universe.
- "why_it_matters" must explain the buying logic: what does this signal imply about
  budget availability, program timing, or decision urgency for THIS offer?
- Urgency weights: 90 = strongest buying signal, 40 = weakest worth tracking.
- Return valid JSON only. No explanation, no markdown outside the JSON block.
"""

SIGNAL_SCHEMA = """\
Return this exact JSON shape:
{
  "signals": [
    {
      "id": "<snake_case unique id>",
      "name": "<short display name, 2-5 words>",
      "category": "<one of: capital_event | hiring | leadership | market_motion | technology | pain | timing | education | downstream | operations | government | partnership>",
      "description": "<one sentence: what is observed and where>",
      "why_it_matters": "<one sentence: what this implies about budget, timing, or urgency for this specific offer>",
      "mapped_icps": ["<ICP segment name this signal most applies to — use exact names from ICP definitions above>"],
      "urgency_weight": <integer 40-90>,
      "half_life_days": <integer: days until signal loses 50% of its urgency value>,
      "stale_after_days": <integer: days until signal should be ignored entirely>
    }
  ]
}

Generate exactly 20 signals ordered from highest to lowest urgency_weight.
Mix categories — don't cluster more than 4 signals in one category.
Every signal must be specific to this client's market — observable via a named public source.
mapped_icps must contain at least one ICP name from the ICP definitions above — no generic labels.
"""


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _icp_summary(strategy: dict) -> str:
    icps = strategy.get("strategy", {}).get("icps", [])
    lines = []
    for icp in icps:
        name = icp.get("name", "")
        desc = icp.get("description", "")
        personas = ", ".join(p.get("title", "") for p in icp.get("personas", []))
        signals = "; ".join(icp.get("why_now_signals", [])[:3])
        lines.append(f"- {name}: {desc} | Personas: {personas} | Now signals: {signals}")
    return "\n".join(lines) or "No ICP definitions loaded."


def _build_signal_prompt(intake: dict, icp_strategy: dict) -> str:
    outcome = intake.get("target_outcome") or "unknown outcome"
    offer = intake.get("offer") or "unknown offer"
    constraints = "\n".join(f"- {c}" for c in intake.get("constraints", [])) or "- None"
    known_ctx = intake.get("known_context") or "None."
    icp_text = _icp_summary(icp_strategy)

    return f"""\
CLIENT CONTEXT
==============
Offer: {offer}
Target outcome: {outcome}

Known context:
{known_ctx}

Constraints:
{constraints}

ICP SEGMENTS
============
{icp_text}

TASK
====
Generate 20 BirdDog-ready signal definitions specific to this client's market and
buyer segments. These signals will be used to monitor target accounts and trigger
outreach when buying intent appears.

{SIGNAL_SCHEMA}"""


def _fallback_signals(intake: dict, icp_names: list[str]) -> list[dict]:
    """Generic fallback signals when LLM_SKIP=true or on hard error."""
    templates = [
        ("funding_recent", "Recent funding", "capital_event", 90, 30, 90,
         "Funding announcement in the last 90 days"),
        ("sales_hiring", "Sales hiring", "hiring", 75, 30, 90,
         "New SDR, AE, RevOps, or sales leadership job posts"),
        ("exec_change", "Revenue leadership change", "leadership", 70, 30, 90,
         "New CRO, VP Sales, VP Marketing, or founder GTM change"),
        ("product_launch", "Product launch", "market_motion", 65, 60, 90,
         "New product, tier, integration, or market expansion"),
        ("geo_expansion", "Geographic expansion", "market_motion", 55, 60, 90,
         "New market, region, office, or localized GTM motion"),
        ("tech_adoption", "Relevant tool adoption", "technology", 60, 60, 90,
         "New CRM, data, warehouse, outbound, or workflow tool detected"),
        ("tech_replacement", "Tool replacement window", "technology", 65, 30, 90,
         "Public signal that an existing system is being replaced"),
        ("competitor_hiring", "Competitor pressure", "market_motion", 60, 60, 90,
         "Competitors are hiring, launching, or entering their segment"),
        ("partner_motion", "Partner ecosystem activity", "partnership", 50, 60, 90,
         "New channel, marketplace, or integration partner motion"),
        ("security_compliance", "Compliance pressure", "operations", 50, 60, 90,
         "New security, compliance, procurement, or audit requirement"),
        ("review_negativity", "Negative reviews", "pain", 70, 30, 90,
         "Recent reviews mention pain the client solves"),
        ("social_pain", "Public pain post", "pain", 85, 14, 60,
         "Founder or buyer posts about a problem the client solves"),
        ("community_question", "Community buying question", "pain", 70, 14, 60,
         "Target persona asks for recommendations or alternatives"),
        ("agency_churn", "Agency or vendor churn", "pain", 70, 30, 90,
         "Account shows dissatisfaction with current agency or vendor"),
        ("manual_workaround", "Manual process workaround", "pain", 65, 60, 90,
         "Job posts or content imply spreadsheet or manual operating pain"),
        ("budget_cycle", "Budget or planning window", "timing", 55, 30, 90,
         "Annual planning, budget allocation, or board pressure signal"),
        ("event_attendance", "Relevant event activity", "timing", 45, 60, 90,
         "Account attends, sponsors, or speaks at market-relevant events"),
        ("content_theme", "Repeated content theme", "education", 45, 60, 90,
         "Company repeatedly publishes around the problem space"),
        ("customer_trigger", "Their customer trigger", "downstream", 60, 60, 90,
         "Their own customers are changing in ways that create demand"),
        ("data_quality_gap", "Data quality gap", "operations", 65, 60, 90,
         "Signals of incomplete CRM, messy data, or reporting gaps"),
    ]
    outcome = intake.get("target_outcome") or "the customer's stated outcome"
    offer = intake.get("offer") or "the customer's offer"
    result = []
    for i, (sid, name, cat, weight, half_life, stale, desc) in enumerate(templates, 1):
        mapped = icp_names[(i - 1) % len(icp_names)] if icp_names else "Primary ICP"
        result.append({
            "id": sid,
            "name": name,
            "category": cat,
            "description": desc,
            "why_it_matters": f"Indicates buying readiness for {offer} toward: {outcome[:80]}.",
            "urgency_weight": weight,
            "half_life_days": half_life,
            "stale_after_days": stale,
            "_mapped_icp": mapped,
        })
    return result


def _enrich_signals(signals: list[dict], icp_strategy: dict, intake: dict) -> list[dict]:
    """Add BirdDog envelope fields that the LLM doesn't need to produce."""
    icps = icp_strategy.get("strategy", {}).get("icps", [])
    icp_names = [icp.get("name") for icp in icps] or ["Primary ICP"]
    outcome = intake.get("target_outcome") or "the customer's stated outcome"

    enriched = []
    for i, sig in enumerate(signals):
        # Use LLM-assigned mapped_icps if present; fall back to first ICP (not round-robin)
        llm_mapped = sig.get("mapped_icps") or sig.pop("_mapped_icp", None)
        if isinstance(llm_mapped, list) and llm_mapped:
            mapped = llm_mapped[0]
            mapped_all = llm_mapped
        elif isinstance(llm_mapped, str) and llm_mapped:
            mapped = llm_mapped
            mapped_all = [llm_mapped]
        else:
            mapped = icp_names[0]
            mapped_all = [icp_names[0]]

        name = sig.get("name", "Signal")
        desc = sig.get("description", "")
        enriched.append({
            "id": sig.get("id", f"signal_{i+1}"),
            "display_order": i + 1,
            "name": name,
            "category": sig.get("category", "market_motion"),
            "description": desc,
            "why_it_matters": sig.get("why_it_matters", f"Indicates readiness toward: {outcome[:80]}."),
            "mapped_icp": mapped,
            "mapped_icps": mapped_all,
            "bird_dog_query_hint": f"{name}: {desc}. Prioritize accounts matching {', '.join(mapped_all)}.",
            "evidence_required": [
                "company domain",
                "source URL or source system",
                "observed date",
                "one-sentence summary",
            ],
            "urgency_weight": sig.get("urgency_weight", 60),
            "decay": {
                "half_life_days": sig.get("half_life_days", 30),
                "stale_after_days": sig.get("stale_after_days", 90),
            },
            "crm_note_template": f"{name} signal: {{signal_summary}}. Relevance: {', '.join(mapped_all)}.",
        })
    return enriched


def build_signal_strategy(client_slug: str, projects_dir: Path = PROJECTS_DIR) -> Path:
    platform_dir = projects_dir / client_slug / "platform"
    platform_dir.mkdir(parents=True, exist_ok=True)

    icp_path = platform_dir / "icp_strategy.json"
    if not icp_path.exists():
        generate_icp_strategy(client_slug, projects_dir=projects_dir)

    icp_strategy = _load_json(icp_path)
    intake = _load_json(platform_dir / "intake.json")

    icps = icp_strategy.get("strategy", {}).get("icps", [])
    icp_names = [icp.get("name") for icp in icps] or ["Primary ICP"]
    fallback_sigs = _fallback_signals(intake, icp_names)

    prompt = _build_signal_prompt(intake, icp_strategy)
    llm_out = call_json(
        prompt=prompt,
        system=SIGNAL_SYSTEM,
        task="signal_strategy",
        provider=Provider.CLAUDE,
        fallback={"signals": fallback_sigs},
    )

    raw_signals = llm_out.get("signals", fallback_sigs)
    # Ensure exactly 20 — truncate or pad with fallback
    if len(raw_signals) < 20:
        raw_signals.extend(fallback_sigs[len(raw_signals):20])
    raw_signals = raw_signals[:20]

    signals = _enrich_signals(raw_signals, icp_strategy, intake)

    strategy = {
        "schema_version": "v1.0",
        "client_slug": client_slug,
        "generated_on": date.today().isoformat(),
        "llm_provider": "claude",
        "source": {
            "intake_path": str(platform_dir / "intake.json"),
            "icp_strategy_path": str(icp_path),
        },
        "signals": signals,
        "bird_dog": {
            "write_mode": "manifest_only_until_api_verified",
            "recommended_account_workflow": (
                "Upload or configure these signals first, then review BirdDog "
                "recommended accounts before adding to monitoring."
            ),
            "fallback_account_monitoring": (
                "If custom signal creation is unavailable, export top-scored "
                "accounts to BirdDog watchlists and pull alerts back into accounts.json."
            ),
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
                "name": s["name"],
                "category": s["category"],
                "query_hint": s["bird_dog_query_hint"],
                "urgency_weight": s["urgency_weight"],
            }
            for s in signals
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))

    return out_path
