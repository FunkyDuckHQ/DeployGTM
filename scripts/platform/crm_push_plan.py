from __future__ import annotations

import json
from datetime import date
from pathlib import Path


PROJECTS_DIR = Path("projects")


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def build_crm_push_plan(
    client_slug: str,
    projects_dir: Path = PROJECTS_DIR,
    min_activation_priority: int = 60,
) -> Path:
    platform_dir = projects_dir / client_slug / "platform"
    platform_dir.mkdir(parents=True, exist_ok=True)

    matrix = _load_json(platform_dir / "accounts.json")
    intake = _load_json(platform_dir / "intake.json")
    accounts = matrix.get("accounts", [])

    planned = []
    deferred = []
    for account in accounts:
        score = account.get("scores", {})
        priority = int(score.get("activation_priority") or 0)
        if priority < min_activation_priority:
            deferred.append(
                {
                    "company": account.get("company"),
                    "domain": account.get("domain"),
                    "activation_priority": priority,
                    "reason": "below activation threshold",
                }
            )
            continue

        planned.append(
            {
                "company": {
                    "name": account.get("company"),
                    "domain": account.get("domain"),
                    "properties": {
                        "deploygtm_activation_priority": priority,
                        "deploygtm_icp_fit_score": score.get("icp_fit_score"),
                        "deploygtm_urgency_score": score.get("urgency_score"),
                        "deploygtm_confidence_score": score.get("confidence_score"),
                    },
                },
                "contacts": account.get("contacts", []),
                "tasks": [
                    {
                        "type": "sales_follow_up",
                        "subject": f"Review DeployGTM signal lead: {account.get('company')}",
                        "body": "Review buyer profile, signal rationale, and drafted copy before outreach.",
                    }
                ],
                "notes": [
                    {
                        "body": "\n".join(score.get("rationale", [])) or "DeployGTM signal audit account.",
                    }
                ],
                "deal": {
                    "name": f"{account.get('company')} - DeployGTM-found opportunity",
                    "stage": "outreach_ready",
                    "source": "DeployGTM Signal Audit",
                },
                "copy": account.get("copy", {}),
            }
        )

    plan = {
        "schema_version": "v1.0",
        "client_slug": client_slug,
        "generated_on": date.today().isoformat(),
        "dry_run": True,
        "writes_enabled": False,
        "requires_explicit_approval": True,
        "crm_provider": intake.get("crm_provider", matrix.get("client", {}).get("crm_provider", "hubspot")),
        "scope": "deploygtm_found_leads_tasks_only",
        "min_activation_priority": min_activation_priority,
        "planned_records": planned,
        "deferred_records": deferred,
        "guardrails": [
            "Do not ingest or modify the entire client CRM in v1.",
            "Do not send email from this plan.",
            "Do not write to production CRM without explicit confirmation.",
            "Only push DeployGTM-found accounts, contacts, notes, tasks, and deals.",
        ],
    }

    out_path = platform_dir / "crm_push_plan.json"
    out_path.write_text(json.dumps(plan, indent=2))
    return out_path
