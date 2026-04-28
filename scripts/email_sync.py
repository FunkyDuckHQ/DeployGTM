"""DeployGTM — SuperSend email event sync.

Maps SuperSend events back to account domains in a client matrix and updates
engagement fields used by scoring and prioritization.
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

# Prefer local overrides first, then default .env.
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
    t = (raw_type or "").lower().strip()
    aliases = {
        "email_sent": "sent",
        "opened": "open",
        "clicked": "click",
        "replied": "reply",
        "bounced": "bounce",
    }
    return aliases.get(t, t)


def _ensure_engagement(account: dict[str, Any]) -> dict[str, Any]:
    engagement = account.setdefault("engagement", {})
    engagement.setdefault("status", "active")
    engagement.setdefault("open_count", 0)
    engagement.setdefault("click_count", 0)
    engagement.setdefault("reply_count", 0)
    engagement.setdefault("bounce_count", 0)
    engagement.setdefault("unsubscribe_count", 0)
    engagement.setdefault("sentiment", "none")
    engagement.setdefault("sentiment_mod", 0)
    engagement.setdefault("events", [])
    return engagement


def compute_score(account: dict[str, Any]) -> int | None:
    """Compute total score from a base score plus engagement modifier when available."""
    score = account.get("score")
    if not isinstance(score, dict):
        return None

    base = score.get("priority")
    mod = account.get("engagement", {}).get("sentiment_mod", 0)
    if not isinstance(base, int):
        return None
    if not isinstance(mod, int):
        mod = 0

    score["priority_adjusted"] = max(1, min(15, base + mod))
    return score["priority_adjusted"]


def record_event(account: dict[str, Any], event_type: str, payload: dict[str, Any]) -> None:
    """Apply one SuperSend event to one account's engagement state."""
    event_type = _normalize_event_type(event_type)
    engagement = _ensure_engagement(account)

    if event_type == "open":
        engagement["open_count"] += 1
        # Mild nudge when repeatedly opened but no reply yet.
        if engagement["open_count"] >= 3 and engagement["reply_count"] == 0:
            engagement["sentiment_mod"] = max(engagement["sentiment_mod"], 1)
            if engagement["sentiment"] == "none":
                engagement["sentiment"] = "neutral"

    elif event_type == "click":
        engagement["click_count"] += 1

    elif event_type == "reply":
        engagement["reply_count"] += 1
        engagement["sentiment"] = "positive"
        engagement["sentiment_mod"] = max(engagement["sentiment_mod"], 2)

    elif event_type == "bounce":
        engagement["bounce_count"] += 1
        engagement["sentiment"] = "negative"
        engagement["sentiment_mod"] = min(engagement["sentiment_mod"], -2)

        # Hard bounce handling for immediate disqualification.
        bounce_category = (
            payload.get("bounce_category")
            or payload.get("bounceCategory")
            or payload.get("contact", {}).get("bounce_category")
            or ""
        ).lower()
        if bounce_category in {"hard", "invalid_recipient", "policy_block"}:
            engagement["status"] = "disqualified"

    elif event_type == "unsubscribe":
        engagement["unsubscribe_count"] += 1
        engagement["sentiment"] = "negative"
        engagement["sentiment_mod"] = min(engagement["sentiment_mod"], -2)
        engagement["status"] = "disqualified"

    elif event_type == "sent":
        # no scoring effect; tracked for audit trail.
        pass

    engagement["events"].append(
        {
            "type": event_type,
            "ts": payload.get("created_at") or payload.get("timestamp") or payload.get("date"),
        }
    )
    engagement["events"] = engagement["events"][-100:]

    compute_score(account)


def _account_domain(account: dict[str, Any]) -> str:
    return (account.get("domain") or "").strip().lower()


def load_matrix(client_slug: str) -> tuple[Path, dict[str, Any]]:
    matrix_path = PROJECTS_DIR / client_slug / "platform" / "accounts.json"
    if not matrix_path.exists():
        raise FileNotFoundError(f"accounts matrix not found: {matrix_path}")

    data = json.loads(matrix_path.read_text())
    if "accounts" not in data or not isinstance(data["accounts"], list):
        raise ValueError(f"invalid matrix format in {matrix_path}")

    return matrix_path, data


def save_matrix(path: Path, matrix: dict[str, Any]) -> None:
    path.write_text(json.dumps(matrix, indent=2))


def log_execution(
    *,
    client_slug: str,
    mode: str,
    counts: dict[str, int],
    events_fetched: int,
    dry_run: bool,
    update_profile: bool,
    profile_update_status: str,
) -> Path:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / f"email_sync_{client_slug}.jsonl"
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "client_slug": client_slug,
        "mode": mode,
        "events_fetched": events_fetched,
        "counts": counts,
        "dry_run": dry_run,
        "update_profile": update_profile,
        "profile_update_status": profile_update_status,
    }
    with log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return log_path


def maybe_flag_profile_update(client_slug: str, matrix: dict[str, Any], threshold: int = 30) -> str:
    """
    Flag that ICP profile should be re-derived once enough reply signal accumulates.
    Does not auto-run derive ICP; only writes a marker artifact.
    """
    total_replies = sum(
        int((a.get("engagement", {}).get("reply_count") or 0))
        for a in matrix.get("accounts", [])
    )
    if total_replies < threshold:
        return "below_threshold"

    out = PROJECTS_DIR / client_slug / "platform" / "profile_update_needed.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "flag": "profile_update_needed",
                "reason": "reply_threshold_reached",
                "reply_count": total_replies,
                "threshold": threshold,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
    )
    return "flagged"


def _extract_event_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [p for p in payload if isinstance(p, dict)]
    if isinstance(payload, dict):
        if isinstance(payload.get("events"), list):
            return [p for p in payload["events"] if isinstance(p, dict)]
        if isinstance(payload.get("data"), list):
            return [p for p in payload["data"] if isinstance(p, dict)]
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
    by_domain = { _account_domain(a): a for a in matrix["accounts"] if _account_domain(a) }

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

    url = os.getenv("SUPERSEND_EVENTS_URL", DEFAULT_EVENTS_URL)
    params: dict[str, Any] = {"limit": limit}
    if event_type:
        params["type"] = event_type

    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return _extract_event_list(resp.json())


@click.group()
def cli() -> None:
    """Sync SuperSend engagement events into a client account matrix."""


@cli.command("ingest")
@click.option("--client", "client_slug", required=True, help="Client/project slug")
@click.option("--payload", "payload_path", required=True, type=click.Path(exists=True), help="Webhook/event JSON payload file")
@click.option("--dry-run", is_flag=True, help="Apply logic but do not write matrix changes")
@click.option("--update-profile", is_flag=True, help="Flag profile refresh once reply threshold is met")
def ingest_cmd(client_slug: str, payload_path: str, dry_run: bool, update_profile: bool) -> None:
    matrix_path, matrix = load_matrix(client_slug)
    payload = json.loads(Path(payload_path).read_text())
    events = _extract_event_list(payload)

    counts = apply_events(matrix, events)
    profile_status = "not_requested"
    if update_profile:
        profile_status = maybe_flag_profile_update(client_slug, matrix)

    if not dry_run:
        save_matrix(matrix_path, matrix)

    log_path = log_execution(
        client_slug=client_slug,
        mode="ingest",
        counts=counts,
        events_fetched=len(events),
        dry_run=dry_run,
        update_profile=update_profile,
        profile_update_status=profile_status,
    )

    click.echo(f"{'[dry-run] ' if dry_run else ''}Updated matrix: {matrix_path}")
    click.echo(json.dumps(counts, indent=2))
    click.echo(f"Execution log: {log_path}")


@cli.command("poll")
@click.option("--client", "client_slug", required=True, help="Client/project slug")
@click.option("--limit", default=100, show_default=True, help="Max events to request")
@click.option("--type", "event_type", default=None, help="Optional event type filter")
@click.option("--dry-run", is_flag=True, help="Apply logic but do not write matrix changes")
@click.option("--update-profile", is_flag=True, help="Flag profile refresh once reply threshold is met")
def poll_cmd(client_slug: str, limit: int, event_type: str | None, dry_run: bool, update_profile: bool) -> None:
    matrix_path, matrix = load_matrix(client_slug)
    events = fetch_events(limit=limit, event_type=event_type)

    counts = apply_events(matrix, events)
    profile_status = "not_requested"
    if update_profile:
        profile_status = maybe_flag_profile_update(client_slug, matrix)

    if not dry_run:
        save_matrix(matrix_path, matrix)

    log_path = log_execution(
        client_slug=client_slug,
        mode="poll",
        counts=counts,
        events_fetched=len(events),
        dry_run=dry_run,
        update_profile=update_profile,
        profile_update_status=profile_status,
    )

    click.echo(f"Fetched events: {len(events)}")
    click.echo(f"{'[dry-run] ' if dry_run else ''}Updated matrix: {matrix_path}")
    click.echo(json.dumps(counts, indent=2))
    click.echo(f"Execution log: {log_path}")


if __name__ == "__main__":
    cli()
