"""DeployGTM - SuperSend/email engagement sync.

Ingests email events into projects/<client>/platform/accounts.json.
This does not send email and does not write to CRM.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click
import requests
from dotenv import load_dotenv

from scripts.score import calculate_activation_priority


load_dotenv(".env.local")
load_dotenv()

PROJECTS_DIR = Path("projects")
LOGS_DIR = Path("logs")
DEFAULT_EVENTS_URL = "https://api.supersend.io/v2/events"


def _extract_domain(email: str | None) -> str:
    if not email or "@" not in email:
        return ""
    return email.rsplit("@", 1)[-1].lower().strip()


def _normalize_event_type(raw_type: str | None) -> str:
    event_type = (raw_type or "").lower().strip()
    aliases = {
        "email_sent": "sent",
        "opened": "open",
        "clicked": "click",
        "replied": "reply",
        "bounced": "bounce",
    }
    return aliases.get(event_type, event_type)


def _ensure_engagement(account: dict[str, Any]) -> dict[str, Any]:
    engagement = account.setdefault("engagement", {})
    engagement.setdefault("status", "active")
    engagement.setdefault("open_count", 0)
    engagement.setdefault("click_count", 0)
    engagement.setdefault("reply_count", 0)
    engagement.setdefault("bounce_count", 0)
    engagement.setdefault("unsubscribe_count", 0)
    engagement.setdefault("events", [])
    return engagement


def _engagement_score(engagement: dict[str, Any]) -> int:
    score = 0
    score += min(20, int(engagement.get("open_count") or 0) * 4)
    score += min(25, int(engagement.get("click_count") or 0) * 10)
    score += min(45, int(engagement.get("reply_count") or 0) * 30)
    score -= min(50, int(engagement.get("bounce_count") or 0) * 25)
    score -= min(60, int(engagement.get("unsubscribe_count") or 0) * 60)
    return max(0, min(100, score))


def recompute_activation(account: dict[str, Any]) -> None:
    scores = account.setdefault("scores", {})
    engagement = _ensure_engagement(account)
    scores["engagement_score"] = _engagement_score(engagement)
    scores["activation_priority"] = calculate_activation_priority(
        icp_fit_score=int(scores.get("icp_fit_score") or 0),
        urgency_score=int(scores.get("urgency_score") or 0),
        engagement_score=int(scores.get("engagement_score") or 0),
        confidence_score=int(scores.get("confidence_score") or 0),
    )


def record_event(account: dict[str, Any], event_type: str, payload: dict[str, Any]) -> None:
    event_type = _normalize_event_type(event_type)
    engagement = _ensure_engagement(account)

    if event_type == "open":
        engagement["open_count"] += 1
    elif event_type == "click":
        engagement["click_count"] += 1
    elif event_type == "reply":
        engagement["reply_count"] += 1
        engagement["status"] = "replied"
    elif event_type == "bounce":
        engagement["bounce_count"] += 1
        engagement["status"] = "delivery_issue"
    elif event_type == "unsubscribe":
        engagement["unsubscribe_count"] += 1
        engagement["status"] = "disqualified"
    elif event_type == "sent":
        pass

    engagement["events"].append(
        {
            "type": event_type,
            "ts": payload.get("created_at") or payload.get("timestamp") or payload.get("date"),
        }
    )
    engagement["events"] = engagement["events"][-100:]
    recompute_activation(account)


def load_matrix(client_slug: str) -> tuple[Path, dict[str, Any]]:
    matrix_path = PROJECTS_DIR / client_slug / "platform" / "accounts.json"
    if not matrix_path.exists():
        raise FileNotFoundError(f"accounts matrix not found: {matrix_path}")
    matrix = json.loads(matrix_path.read_text())
    if not isinstance(matrix.get("accounts"), list):
        raise ValueError(f"invalid account matrix shape: {matrix_path}")
    return matrix_path, matrix


def save_matrix(path: Path, matrix: dict[str, Any]) -> None:
    path.write_text(json.dumps(matrix, indent=2))


def _extract_event_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        if isinstance(payload.get("events"), list):
            return [item for item in payload["events"] if isinstance(item, dict)]
        if isinstance(payload.get("data"), list):
            return [item for item in payload["data"] if isinstance(item, dict)]
        return [payload]
    return []


def _event_contact_email(event: dict[str, Any]) -> str:
    return (
        event.get("contact", {}).get("email")
        or event.get("recipient")
        or event.get("email")
        or ""
    )


def apply_events(matrix: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, int]:
    by_domain = {
        (account.get("domain") or "").strip().lower(): account
        for account in matrix.get("accounts", [])
        if account.get("domain")
    }
    counters = defaultdict(int)

    for event in events:
        event_type = _normalize_event_type(event.get("type") or event.get("event"))
        if not event_type:
            counters["skipped_unknown_type"] += 1
            continue

        domain = _extract_domain(_event_contact_email(event))
        if not domain:
            counters["skipped_no_domain"] += 1
            continue

        account = by_domain.get(domain)
        if not account:
            counters["skipped_no_match"] += 1
            continue

        record_event(account, event_type, event)
        counters["applied"] += 1
        counters[f"event_{event_type}"] += 1

    return dict(counters)


def fetch_events(limit: int = 100, event_type: str | None = None) -> list[dict[str, Any]]:
    api_key = os.getenv("SUPERSEND_API_KEY")
    if not api_key:
        raise EnvironmentError("SUPERSEND_API_KEY not set in environment")

    params: dict[str, Any] = {"limit": limit}
    if event_type:
        params["type"] = event_type

    response = requests.get(
        os.getenv("SUPERSEND_EVENTS_URL", DEFAULT_EVENTS_URL),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return _extract_event_list(response.json())


def log_execution(*, client_slug: str, mode: str, counts: dict[str, int], events_fetched: int, dry_run: bool) -> Path:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / f"email_sync_{client_slug}.jsonl"
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "client_slug": client_slug,
        "mode": mode,
        "events_fetched": events_fetched,
        "counts": counts,
        "dry_run": dry_run,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return log_path


@click.group()
def cli() -> None:
    """Sync email engagement events into a client account matrix."""


@cli.command("ingest")
@click.option("--client", "client_slug", required=True, help="Client/project slug")
@click.option("--payload", "payload_path", required=True, type=click.Path(exists=True), help="Webhook/event JSON payload")
@click.option("--dry-run", is_flag=True, help="Apply logic but do not write matrix changes")
def ingest_cmd(client_slug: str, payload_path: str, dry_run: bool) -> None:
    matrix_path, matrix = load_matrix(client_slug)
    events = _extract_event_list(json.loads(Path(payload_path).read_text()))
    counts = apply_events(matrix, events)

    if not dry_run:
        save_matrix(matrix_path, matrix)

    log_path = log_execution(
        client_slug=client_slug,
        mode="ingest",
        counts=counts,
        events_fetched=len(events),
        dry_run=dry_run,
    )

    click.echo(f"{'[dry-run] ' if dry_run else ''}Email events processed for: {matrix_path}")
    click.echo(json.dumps(counts, indent=2))
    click.echo(f"Execution log: {log_path}")


@cli.command("poll")
@click.option("--client", "client_slug", required=True, help="Client/project slug")
@click.option("--limit", default=100, show_default=True)
@click.option("--type", "event_type", default=None)
@click.option("--dry-run", is_flag=True, help="Apply logic but do not write matrix changes")
def poll_cmd(client_slug: str, limit: int, event_type: str | None, dry_run: bool) -> None:
    matrix_path, matrix = load_matrix(client_slug)
    events = fetch_events(limit=limit, event_type=event_type)
    counts = apply_events(matrix, events)

    if not dry_run:
        save_matrix(matrix_path, matrix)

    log_path = log_execution(
        client_slug=client_slug,
        mode="poll",
        counts=counts,
        events_fetched=len(events),
        dry_run=dry_run,
    )

    click.echo(f"Fetched events: {len(events)}")
    click.echo(f"{'[dry-run] ' if dry_run else ''}Email events processed for: {matrix_path}")
    click.echo(json.dumps(counts, indent=2))
    click.echo(f"Execution log: {log_path}")


if __name__ == "__main__":
    cli()
