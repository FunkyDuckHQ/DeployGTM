from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Iterable

from scripts.score import calculate_activation_priority, score_urgency


PROJECTS_DIR = Path("projects")


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _read_targets(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            {str(k).strip().lower(): (v or "").strip() for k, v in row.items()}
            for row in reader
            if (row.get("company") or row.get("domain"))
        ]


def _fit_from_row(row: dict, icp_strategy: dict) -> tuple[int, list[str]]:
    reasons = []
    score = 45
    summary = " ".join(
        [
            row.get("signal_summary", ""),
            row.get("company", ""),
            row.get("signal_type", ""),
        ]
    ).lower()

    for word in ("hiring", "funding", "launch", "growth", "sales", "crm", "pipeline", "manual"):
        if word in summary:
            score += 6
            reasons.append(f"evidence contains {word}")

    if row.get("domain"):
        score += 10
        reasons.append("domain present")

    icps = icp_strategy.get("strategy", {}).get("icps", [])
    if icps:
        score += 5
        reasons.append("customer-specific ICP strategy present")

    return max(1, min(100, score)), reasons or ["default fit score pending enrichment"]


def _confidence_from_row(row: dict) -> tuple[int, str]:
    if row.get("signal_source", "").lower() == "birddog":
        return 80, "BirdDog signal source"
    if row.get("signal_summary") and row.get("signal_date"):
        return 65, "signal summary and date present"
    if row.get("domain"):
        return 45, "domain present but signal evidence incomplete"
    return 25, "incomplete target record"


def _account_record(row: dict, icp_strategy: dict) -> dict:
    signal_type = row.get("signal_type") or "manual"
    signal_date = row.get("signal_date") or None
    birddog_score = row.get("birddog_score")
    urgency, decay = score_urgency(
        signal_type,
        signal_date,
        birddog_score=int(birddog_score) if str(birddog_score).isdigit() else None,
    )
    fit, fit_reasons = _fit_from_row(row, icp_strategy)
    confidence, confidence_reason = _confidence_from_row(row)
    engagement = int(row.get("engagement_score") or 0)
    activation = calculate_activation_priority(
        icp_fit_score=fit,
        urgency_score=urgency,
        engagement_score=engagement,
        confidence_score=confidence,
    )

    return {
        "company": row.get("company") or row.get("domain") or "Unknown",
        "domain": row.get("domain", ""),
        "signals": [
            {
                "type": signal_type,
                "date": signal_date,
                "source": row.get("signal_source") or "manual",
                "summary": row.get("signal_summary") or "",
                "birddog_score": birddog_score or None,
            }
        ],
        "scores": {
            "icp_fit_score": fit,
            "urgency_score": urgency,
            "engagement_score": engagement,
            "confidence_score": confidence,
            "activation_priority": activation,
            "decay": decay,
            "rationale": fit_reasons + [confidence_reason],
        },
        "buyer_profiles": [],
        "contacts": [],
        "copy": {
            "status": "draft_required",
            "sequence_mode": "draft_only",
            "first_touch": "",
            "followups": [],
        },
        "crm": {
            "scope": "deploygtm_found_leads_tasks_only",
            "planned_action": "review_before_push",
        },
    }


def build_account_matrix(
    client_slug: str,
    projects_dir: Path = PROJECTS_DIR,
    rows: Iterable[dict] | None = None,
) -> Path:
    project_dir = projects_dir / client_slug
    platform_dir = project_dir / "platform"
    platform_dir.mkdir(parents=True, exist_ok=True)

    intake = _load_json(platform_dir / "intake.json")
    icp_strategy = _load_json(platform_dir / "icp_strategy.json")
    target_rows = list(rows) if rows is not None else _read_targets(project_dir / "targets.csv")

    accounts = [_account_record(row, icp_strategy) for row in target_rows]
    matrix = {
        "schema_version": "v1.0",
        "client_slug": client_slug,
        "generated_on": date.today().isoformat(),
        "client": {
            "client_name": intake.get("client_name", client_slug),
            "domain": intake.get("domain", ""),
            "target_outcome": intake.get("target_outcome", ""),
            "crm_provider": intake.get("crm_provider", "hubspot"),
        },
        "scoring": {
            "model": "icp_fit + urgency + engagement + confidence",
            "activation_priority_formula": "45% ICP fit + 35% urgency + 10% engagement + 10% confidence",
            "managed_sending": "deferred",
        },
        "accounts": accounts,
    }

    out_path = platform_dir / "accounts.json"
    out_path.write_text(json.dumps(matrix, indent=2))
    return out_path


def sample_target_rows() -> list[dict]:
    return [
        {
            "company": "Acme Analytics",
            "domain": "acmeanalytics.example",
            "signal_type": "hiring",
            "signal_date": date.today().isoformat(),
            "signal_source": "manual",
            "signal_summary": "Hiring first sales leader after new product launch",
            "birddog_score": "78",
        },
        {
            "company": "Northstar Ops",
            "domain": "northstarops.example",
            "signal_type": "funding",
            "signal_date": date.today().isoformat(),
            "signal_source": "manual",
            "signal_summary": "Recent funding and public growth goals",
            "birddog_score": "82",
        },
    ]
