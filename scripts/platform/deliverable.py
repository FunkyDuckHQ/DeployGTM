from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path


PROJECTS_DIR = Path("projects")


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def build_signal_audit_deliverable(client_slug: str, projects_dir: Path = PROJECTS_DIR) -> Path:
    project_dir = projects_dir / client_slug
    platform_dir = project_dir / "platform"
    deliverable_dir = project_dir / "deliverable"
    deliverable_dir.mkdir(parents=True, exist_ok=True)

    intake = _load_json(platform_dir / "intake.json")
    icp_strategy = _load_json(platform_dir / "icp_strategy.json")
    signal_strategy = _load_json(platform_dir / "signal_strategy.json")
    matrix = _load_json(platform_dir / "accounts.json")
    crm_plan = _load_json(platform_dir / "crm_push_plan.json")

    client_name = intake.get("client_name") or matrix.get("client", {}).get("client_name") or client_slug
    today = date.today().isoformat()

    summary_path = deliverable_dir / "signal_audit_summary.md"
    accounts = matrix.get("accounts", [])
    top_accounts = sorted(
        accounts,
        key=lambda a: int(a.get("scores", {}).get("activation_priority") or 0),
        reverse=True,
    )

    briefs = _load_json(platform_dir / "account_briefs.json")

    # Check which steps have run
    messaging_run = any(
        a.get("copy", {}).get("status") == "drafted"
        for a in accounts
    )
    briefs_run = bool(briefs.get("briefs"))

    lines = [
        f"# {client_name} - Signal Audit Summary",
        "",
        f"Generated: {today}",
        "",
        "## Outcome",
        intake.get("target_outcome", "Not captured"),
        "",
        "## What was built",
        "- Customer outcome intake",
        "- Context pack",
        "- ICP strategy",
        "- 20-signal BirdDog-ready signal strategy",
        "- Account matrix with separate ICP, urgency, engagement, confidence, and activation scores",
        f"- First-touch messaging: {'drafted for all accounts' if messaging_run else 'not yet generated — run messaging step'}",
        f"- Account briefs: {'generated' if briefs_run else 'not yet generated — run briefs step'}",
        "- CRM push plan for DeployGTM-found leads and tasks only",
        "",
        "## Top accounts",
    ]

    if top_accounts:
        for account in top_accounts[:10]:
            score = account.get("scores", {})
            lines.append(
                f"- {account.get('company')} ({account.get('domain')}): "
                f"activation {score.get('activation_priority')}, "
                f"ICP {score.get('icp_fit_score')}, urgency {score.get('urgency_score')}"
            )
    else:
        lines.append("- No accounts scored yet. Add targets or run the dry-run sample.")

    lines += [
        "",
        "## ICPs",
    ]
    for icp in icp_strategy.get("strategy", {}).get("icps", []):
        lines.append(f"- {icp.get('name')}: {icp.get('description')}")

    lines += [
        "",
        "## Signals",
        f"{len(signal_strategy.get('signals', []))} signal definitions are ready for BirdDog/manual review.",
        "",
        "## CRM plan",
        f"Planned records: {len(crm_plan.get('planned_records', []))}",
        f"Deferred records: {len(crm_plan.get('deferred_records', []))}",
        "Writes enabled: false",
    ]
    summary_path.write_text("\n".join(lines) + "\n")

    accounts_path = deliverable_dir / "target_accounts.csv"
    with accounts_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "Company",
            "Domain",
            "Matched ICP",
            "Recommended Persona",
            "ICP Fit Score",
            "Urgency Score",
            "Engagement Score",
            "Confidence Score",
            "Activation Priority",
            "Signal Type",
            "Signal Date",
            "Signal Summary",
            "First Touch Subject",
            "First Touch Copy",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for account in top_accounts:
            score = account.get("scores", {})
            signal = (account.get("signals") or [{}])[0]
            copy = account.get("copy", {})
            writer.writerow(
                {
                    "Company": account.get("company", ""),
                    "Domain": account.get("domain", ""),
                    "Matched ICP": account.get("matched_icp", ""),
                    "Recommended Persona": account.get("recommended_persona", ""),
                    "ICP Fit Score": score.get("icp_fit_score", ""),
                    "Urgency Score": score.get("urgency_score", ""),
                    "Engagement Score": score.get("engagement_score", ""),
                    "Confidence Score": score.get("confidence_score", ""),
                    "Activation Priority": score.get("activation_priority", ""),
                    "Signal Type": signal.get("type", ""),
                    "Signal Date": signal.get("date", ""),
                    "Signal Summary": signal.get("summary", ""),
                    "First Touch Subject": copy.get("subject_line", ""),
                    "First Touch Copy": copy.get("first_touch", ""),
                }
            )

    return deliverable_dir
