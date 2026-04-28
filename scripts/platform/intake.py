from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from .bootstrap_client import bootstrap_client, slugify


PROJECTS_DIR = Path("projects")


@dataclass
class CustomerOutcomeIntake:
    schema_version: str
    engagement_type: str
    client_name: str
    client_slug: str
    domain: str
    target_outcome: str
    offer: str
    constraints: list[str] = field(default_factory=list)
    current_tools: dict[str, str] = field(default_factory=dict)
    crm_provider: str = "hubspot"
    known_context: str = ""
    sequencing_mode: str = "draft_only"
    crm_scope: str = "deploygtm_found_leads_tasks_only"
    managed_sending: str = "deferred_until_deliverability_controls_exist"
    created_on: str = field(default_factory=lambda: date.today().isoformat())


def _split_list(raw: str | list[str] | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return [item.strip() for item in str(raw).split(";") if item.strip()]


def _parse_tools(raw: str | dict[str, str] | None) -> dict[str, str]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return {str(k): str(v) for k, v in raw.items() if str(k).strip()}

    tools: dict[str, str] = {}
    for item in str(raw).split(";"):
        if not item.strip():
            continue
        if ":" in item:
            key, value = item.split(":", 1)
            tools[key.strip().lower()] = value.strip()
        else:
            tools[item.strip().lower()] = "unknown"
    return tools


def _context_markdown(intake: CustomerOutcomeIntake) -> str:
    constraints = "\n".join(f"- {item}" for item in intake.constraints) or "- None provided yet"
    tools = "\n".join(f"- {k}: {v}" for k, v in intake.current_tools.items()) or "- None provided yet"
    known_context = intake.known_context or "None provided yet."
    return f"""# {intake.client_name} - Signal Audit Context

## Status
Signal Audit intake captured.

## Engagement type
{intake.engagement_type}

## Customer outcome
{intake.target_outcome}

## Offer being tested
{intake.offer}

## Client overview
- Company: {intake.client_name}
- Website: https://{intake.domain}
- CRM provider: {intake.crm_provider}

## Constraints
{constraints}

## Current tools
{tools}

## Known context
{known_context}

## Delivery boundaries
- CRM scope: {intake.crm_scope}
- Sequencing mode: {intake.sequencing_mode}
- Managed sending: {intake.managed_sending}

## Signal Audit deliverables
- Real accounts
- Real ICP and urgency scores
- BirdDog-ready signal strategy
- Enriched target profiles
- Rep-ready copy and CRM tasks
"""


def create_customer_outcome_intake(
    *,
    client_name: str,
    domain: str,
    target_outcome: str,
    offer: str,
    client_slug: str | None = None,
    constraints: str | list[str] | None = None,
    current_tools: str | dict[str, str] | None = None,
    crm_provider: str = "hubspot",
    known_context: str = "",
    projects_dir: Path = PROJECTS_DIR,
    force: bool = False,
) -> Path:
    slug = client_slug or slugify(client_name)
    bootstrap_client(
        client_name=client_name,
        domain=domain,
        client_slug=slug,
        projects_dir=projects_dir,
        force=force,
    )

    project_dir = projects_dir / slug
    platform_dir = project_dir / "platform"
    platform_dir.mkdir(parents=True, exist_ok=True)

    intake = CustomerOutcomeIntake(
        schema_version="v1.0",
        engagement_type="signal_audit",
        client_name=client_name,
        client_slug=slug,
        domain=domain,
        target_outcome=target_outcome,
        offer=offer,
        constraints=_split_list(constraints),
        current_tools=_parse_tools(current_tools),
        crm_provider=crm_provider,
        known_context=known_context,
    )

    intake_path = platform_dir / "intake.json"
    if force or not intake_path.exists():
        intake_path.write_text(json.dumps(asdict(intake), indent=2))

    context_path = project_dir / "context.md"
    if force or not context_path.exists():
        context_path.write_text(_context_markdown(intake))

    for name, body in {
        "handoff.md": f"# {client_name} - Handoff\n\n## Current state\nSignal Audit intake captured.\n",
        "open-loops.md": f"# {client_name} - Open Loops\n\n## Need to verify\n- BirdDog API support for signal definitions and recommended accounts\n",
    }.items():
        path = project_dir / name
        if force or not path.exists():
            path.write_text(body)

    targets_path = project_dir / "targets.csv"
    if force or not targets_path.exists():
        targets_path.write_text("company,domain,signal_type,signal_date,signal_source,signal_summary,birddog_score\n")

    return intake_path


def load_intake(client_slug: str, projects_dir: Path = PROJECTS_DIR) -> dict:
    path = projects_dir / client_slug / "platform" / "intake.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())
