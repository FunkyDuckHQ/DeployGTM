"""
DeployGTM — Email Engagement Sync

Pulls engagement events from an outbound email platform (Supersend by default)
and writes them back into the client's account matrix as score-affecting
events. Closes the feedback loop between sent outreach and the dynamic ICP
score engine.

Event mapping:
  reply (positive)    → record_event(sentiment=positive)   → status=replied
  reply (negative)    → record_event(sentiment=negative)   → status=no_fit
  bounce (hard)       → record_event(sentiment=negative)   → status=no_fit
  unsubscribe         → record_event(sentiment=negative)   → status=no_fit
  click               → record_event(birddog_signal=engaged)
  open (3+ unique)    → record_event(birddog_signal=engaged)
  send                → status=outreach_sent (only if currently 'active' or 'monitor')

Account matching:
  1. Try recipient email against any account's contacts[*].email
  2. Fall back to recipient email domain → account.domain
  3. Skip the event if no match (logged in --verbose)

Idempotency:
  Each account stores `email_engagement` with the last-synced event id /
  timestamp per provider. Re-runs skip events already applied.

Providers:
  supersend  (default) — pulls from Supersend's events endpoint
  generic    — accepts a JSON file of events via --events-file (for webhooks
               you receive elsewhere, or for testing)

Usage:
  # Pull last 7 days of Supersend events into the deploygtm matrix
  python scripts/email_sync.py --client deploygtm --since 7

  # Replay events from a JSON file (e.g. webhook archive, testing)
  python scripts/email_sync.py --client deploygtm \\
      --provider generic --events-file /tmp/events.json

  # Dry-run — show what would change, don't write
  python scripts/email_sync.py --client deploygtm --dry-run --verbose

Environment:
  SUPERSEND_API_KEY        — required for --provider supersend
  SUPERSEND_BASE_URL       — optional; defaults to https://api.supersend.io/v1
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

import click

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
MATRIX_SCRIPTS_DIR = REPO_ROOT / "projects" / "deploygtm-own" / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(MATRIX_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(MATRIX_SCRIPTS_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

from generate_outreach import _matrix_path, load_client_matrix  # noqa: E402
from score_engine import record_event  # noqa: E402
from derive_icp import load_profile  # noqa: E402


# ─── Event normalisation ─────────────────────────────────────────────────────

# Provider-specific event types → normalised types used by this module.
_EVENT_ALIASES = {
    "email.sent": "send",
    "email.delivered": "send",
    "email.opened": "open",
    "email.open": "open",
    "email.clicked": "click",
    "email.click": "click",
    "email.replied": "reply",
    "email.reply": "reply",
    "email.bounced": "bounce",
    "email.bounce": "bounce",
    "email.unsubscribed": "unsubscribe",
    "email.unsubscribe": "unsubscribe",
    "email.complained": "unsubscribe",
}

NORMALISED_EVENTS = {"send", "open", "click", "reply", "bounce", "unsubscribe"}

# Open threshold before we treat repeat-opens as engagement (single opens are
# noise — bots, link previews, prefetchers).
OPEN_ENGAGEMENT_THRESHOLD = 3


def _normalise_event(raw_type: str) -> Optional[str]:
    """Normalise a provider-specific event type or return None if irrelevant."""
    t = (raw_type or "").lower().strip()
    if t in NORMALISED_EVENTS:
        return t
    return _EVENT_ALIASES.get(t)


def _classify_reply_sentiment(body: str) -> str:
    """Crude reply-sentiment classifier.

    Used as a fallback when the provider doesn't supply one. Returns one of
    'positive' | 'neutral' | 'negative'. Replaceable with a Claude call later
    via classify_reply_with_claude().
    """
    if not body:
        return "neutral"
    text = body.lower()
    negative = (
        "unsubscribe", "stop emailing", "remove me", "not interested",
        "wrong person", "no thanks", "no thank you", "don't email",
        "do not email", "leave me alone", "spam",
    )
    positive = (
        "let's chat", "lets chat", "happy to talk", "send a calendar",
        "send calendar", "book a time", "send a link", "interested",
        "tell me more", "sounds good", "let's set up", "lets set up",
        "20 minutes", "worth a call",
    )
    if any(p in text for p in negative):
        return "negative"
    if any(p in text for p in positive):
        return "positive"
    # Any reply at all is mildly positive — they engaged.
    return "neutral"


# ─── Account matching ─────────────────────────────────────────────────────────


def _index_accounts(matrix: dict) -> tuple[dict, dict]:
    """Build (email_idx, domain_idx) for fast lookup against incoming events.

    email_idx:  lowercased email → account dict
    domain_idx: lowercased domain → account dict (first match wins)
    """
    email_idx: dict = {}
    domain_idx: dict = {}
    for account in matrix.get("accounts", []):
        domain = (account.get("domain") or "").lower().strip()
        if domain and domain not in domain_idx:
            domain_idx[domain] = account
        for contact in account.get("contacts", []) or []:
            email = (contact.get("email") or "").lower().strip()
            if email:
                email_idx[email] = account
    return email_idx, domain_idx


def _match_account(
    recipient_email: str,
    email_idx: dict,
    domain_idx: dict,
) -> Optional[dict]:
    """Resolve an event recipient to a matrix account, or None."""
    if not recipient_email:
        return None
    addr = recipient_email.lower().strip()
    if addr in email_idx:
        return email_idx[addr]
    domain = addr.split("@", 1)[1] if "@" in addr else ""
    if domain and domain in domain_idx:
        return domain_idx[domain]
    return None


# ─── Provider: Supersend ─────────────────────────────────────────────────────


def fetch_supersend_events(
    since: datetime,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    page_size: int = 200,
    timeout: int = 30,
) -> list[dict]:
    """Fetch engagement events from Supersend since `since` (UTC datetime).

    Returns a list of provider-shaped event dicts. Caller normalises them.
    Network errors raise click.ClickException so the CLI exits cleanly.
    """
    import requests  # type: ignore

    key = api_key or os.environ.get("SUPERSEND_API_KEY", "")
    if not key:
        raise click.ClickException(
            "SUPERSEND_API_KEY not set. Add it to .env or pass --api-key."
        )

    url = (base_url or os.environ.get("SUPERSEND_BASE_URL")
           or "https://api.supersend.io/v1") + "/events"

    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }

    events: list[dict] = []
    cursor: Optional[str] = None

    while True:
        params: dict = {
            "since": since.replace(tzinfo=timezone.utc).isoformat(),
            "limit": page_size,
        }
        if cursor:
            params["cursor"] = cursor

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        except requests.RequestException as exc:
            raise click.ClickException(f"Supersend request failed: {exc}")

        if resp.status_code == 401:
            raise click.ClickException("Supersend rejected the API key (401).")
        if resp.status_code >= 400:
            raise click.ClickException(
                f"Supersend returned {resp.status_code}: {resp.text[:200]}"
            )

        body = resp.json()
        events.extend(body.get("events", body.get("data", [])))
        cursor = body.get("next_cursor") or body.get("cursor")
        if not cursor:
            break

    return events


# ─── Provider: generic (events file) ─────────────────────────────────────────


def load_events_file(path: Path) -> list[dict]:
    """Load a JSON events file. Supports either a list or {"events": [...]}."""
    raw = json.loads(path.read_text())
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return raw.get("events") or raw.get("data") or []
    raise click.ClickException(f"Unexpected events file shape in {path}")


# ─── Event application ───────────────────────────────────────────────────────


def _coerce_event(raw: dict) -> Optional[dict]:
    """Extract a normalised event from a provider record, or None to skip."""
    event_type = _normalise_event(raw.get("type") or raw.get("event") or "")
    if not event_type:
        return None

    recipient = (
        raw.get("recipient")
        or raw.get("to")
        or raw.get("email")
        or (raw.get("contact") or {}).get("email")
        or ""
    )
    if not recipient:
        return None

    timestamp = (
        raw.get("timestamp")
        or raw.get("occurred_at")
        or raw.get("created_at")
        or ""
    )

    return {
        "id": raw.get("id") or raw.get("event_id") or f"{event_type}:{recipient}:{timestamp}",
        "type": event_type,
        "recipient": recipient,
        "timestamp": timestamp,
        "body": raw.get("body") or raw.get("reply_body") or "",
        "sentiment": (raw.get("sentiment") or "").lower() or None,
        "raw_type": raw.get("type") or raw.get("event") or "",
    }


def _apply_event(
    account: dict,
    event: dict,
    profile: Optional[dict],
) -> Optional[str]:
    """Apply one event to an account. Returns a description of the change, or
    None if skipped (no-op, idempotent dedupe, etc.).
    """
    engagement = account.setdefault("email_engagement", {
        "applied_event_ids": [],
        "open_counts": {},  # recipient_email → unique-day open count
        "last_event_at": None,
    })

    if event["id"] in engagement["applied_event_ids"]:
        return None  # already applied

    etype = event["type"]
    recipient = event["recipient"].lower()
    today = date.today().isoformat()

    description: Optional[str] = None

    if etype == "send":
        # Mark as outreach_sent only when not already further along.
        current = account.get("status", "monitor")
        if current in ("monitor", "active"):
            account["status"] = "outreach_sent"
            account["last_updated"] = today
            record_event(account, "status_change", "outreach_sent",
                         reason="email_send", profile=profile)
            description = f"send → status=outreach_sent"
        else:
            description = f"send (status={current}, no change)"

    elif etype == "open":
        counts = engagement["open_counts"]
        counts[recipient] = counts.get(recipient, 0) + 1
        if counts[recipient] == OPEN_ENGAGEMENT_THRESHOLD:
            record_event(account, "birddog_signal", "engaged",
                         reason=f"opens:{recipient}", profile=profile)
            description = f"open #{counts[recipient]} → engaged"
        else:
            description = f"open #{counts[recipient]}"

    elif etype == "click":
        record_event(account, "birddog_signal", "engaged",
                     reason=f"click:{recipient}", profile=profile)
        description = "click → engaged"

    elif etype == "reply":
        sentiment = event.get("sentiment") or _classify_reply_sentiment(event.get("body", ""))
        if sentiment not in ("positive", "neutral", "negative"):
            sentiment = "neutral"
        record_event(account, "sentiment", sentiment,
                     reason=f"reply:{recipient}", profile=profile)
        # Replied (positive/neutral) → status=replied. Negative → no_fit.
        if sentiment == "negative":
            account["status"] = "no_fit"
        elif account.get("status") in ("outreach_sent", "active", "monitor"):
            account["status"] = "replied"
        account["last_updated"] = today
        record_event(account, "status_change", account["status"],
                     reason=f"reply_sentiment={sentiment}", profile=profile)
        description = f"reply ({sentiment}) → status={account['status']}"

    elif etype == "bounce":
        record_event(account, "sentiment", "negative",
                     reason=f"bounce:{recipient}", profile=profile)
        account["status"] = "no_fit"
        account["last_updated"] = today
        description = "bounce → status=no_fit"

    elif etype == "unsubscribe":
        record_event(account, "sentiment", "negative",
                     reason=f"unsubscribe:{recipient}", profile=profile)
        account["status"] = "no_fit"
        account["last_updated"] = today
        description = "unsubscribe → status=no_fit"

    engagement["applied_event_ids"].append(event["id"])
    engagement["last_event_at"] = event.get("timestamp") or today
    return description


# ─── Main sync ───────────────────────────────────────────────────────────────


def sync_events(
    client: str,
    events: Iterable[dict],
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """Apply a stream of provider events to a client's matrix.

    Returns a summary dict: {"matched": int, "unmatched": int, "applied": int,
    "skipped": int, "by_type": {...}, "changes": [...]}.
    """
    matrix = load_client_matrix(client)
    profile = load_profile(client)
    email_idx, domain_idx = _index_accounts(matrix)

    summary: dict = {
        "matched": 0,
        "unmatched": 0,
        "applied": 0,
        "skipped": 0,
        "by_type": {},
        "changes": [],
    }

    for raw in events:
        event = _coerce_event(raw)
        if not event:
            continue

        summary["by_type"][event["type"]] = summary["by_type"].get(event["type"], 0) + 1

        account = _match_account(event["recipient"], email_idx, domain_idx)
        if not account:
            summary["unmatched"] += 1
            if verbose:
                click.echo(f"  unmatched: {event['type']:<12} {event['recipient']}")
            continue

        summary["matched"] += 1
        change = _apply_event(account, event, profile)
        if change is None:
            summary["skipped"] += 1
            if verbose:
                click.echo(f"  skipped:   {event['type']:<12} {account['company']} (already applied)")
            continue

        summary["applied"] += 1
        summary["changes"].append({
            "company": account["company"],
            "domain": account["domain"],
            "change": change,
            "score": account.get("current_score"),
        })
        if verbose:
            click.echo(f"  applied:   {account['company']:<25} {change}")

    if not dry_run and summary["applied"] > 0:
        path = _matrix_path(client)
        path.write_text(json.dumps(matrix, indent=2) + "\n")

    return summary


# ─── CLI ─────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--client", required=True, help="Client slug.")
@click.option("--provider", default="supersend",
              type=click.Choice(["supersend", "generic"]),
              help="Where to pull events from.")
@click.option("--since", default=7, type=int, show_default=True,
              help="Days back to pull (Supersend only).")
@click.option("--events-file", default=None,
              type=click.Path(exists=True, dir_okay=False, path_type=Path),
              help="JSON events file (for --provider generic).")
@click.option("--api-key", default=None,
              help="Override SUPERSEND_API_KEY for this run.")
@click.option("--dry-run", is_flag=True,
              help="Compute changes without writing the matrix.")
@click.option("--verbose", is_flag=True,
              help="Print one line per event.")
def main(
    client: str,
    provider: str,
    since: int,
    events_file: Optional[Path],
    api_key: Optional[str],
    dry_run: bool,
    verbose: bool,
):
    """Sync email engagement events into a client's account matrix."""
    if provider == "supersend":
        cutoff = datetime.utcnow() - timedelta(days=since)
        click.echo(f"Pulling Supersend events since {cutoff.date().isoformat()}...")
        events = fetch_supersend_events(cutoff, api_key=api_key)
    else:
        if not events_file:
            raise click.ClickException("--events-file is required for --provider generic")
        click.echo(f"Loading events from {events_file}...")
        events = load_events_file(events_file)

    click.echo(f"  {len(events)} event(s) fetched.\n")

    summary = sync_events(client, events, dry_run=dry_run, verbose=verbose)

    click.echo(f"\nMatched:   {summary['matched']}")
    click.echo(f"Unmatched: {summary['unmatched']}")
    click.echo(f"Applied:   {summary['applied']}")
    click.echo(f"Skipped:   {summary['skipped']} (already applied)")
    if summary["by_type"]:
        click.echo(f"By type:   {summary['by_type']}")

    if dry_run:
        click.echo("\n(dry-run) no matrix changes written.")
    elif summary["applied"]:
        click.echo(f"\nMatrix updated: {_matrix_path(client)}")


if __name__ == "__main__":
    main()
