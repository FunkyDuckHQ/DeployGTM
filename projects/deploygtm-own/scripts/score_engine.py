"""
DeployGTM — Dynamic ICP Score Engine

Computes a live account score that evolves based on three factors:

  base_score        = tier_weight × signal_weight
  interaction_delta = Σ events × event_weight  (status transitions, reply sentiment)
  freshness_penalty = signal_age_days / DECAY_HALF_LIFE × base_score × DECAY_RATE

  current_score = base_score + interaction_delta - freshness_penalty

The score is stored back into the account dict as `current_score` (float).
A `score_history` list records every change with timestamp and reason.

Used by:
  - weekly_signal_report.py  (surface priority changes)
  - verify_signals.py        (flag accounts that crossed the engagement threshold)
  - batch_outreach.py        (order accounts by score when filtering)

Score thresholds:
  >= 15  → hot lead, activate immediately
  >= 12  → engagement threshold (batch outreach)
  >= 8   → active monitoring
  < 8    → watch list only
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.resolve().parents[2]

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_outreach import _matrix_path, load_client_matrix  # noqa: E402


# ─── Weights ──────────────────────────────────────────────────────────────────

TIER_WEIGHT = {1: 5, 2: 3, 3: 1}

SIGNAL_WEIGHT = {
    "funding": 3,
    "hiring": 2,
    "leadership_change": 2,
    "acquisition": 2,
    "product_launch": 1,
    "contract_award": 3,
    "program_announcement": 2,
    "sbir_award": 3,
    "conference_signal": 1,
    "manual": 1,
}

# Status transitions that modify score
STATUS_DELTA = {
    "active": 2,
    "outreach_sent": 3,
    "replied": 8,
    "meeting_booked": 15,
    "no_fit": -20,
    "paused": -5,
    "monitor": 0,
}

# Variant response sentiment (from variant_tracker)
SENTIMENT_DELTA = {
    "positive": 6,
    "neutral": 2,
    "negative": -2,
}

# Freshness decay: score decays 20% per half-life period
DECAY_RATE = 0.20
DECAY_HALF_LIFE_DAYS = 60

HOT_THRESHOLD = 15
ENGAGEMENT_THRESHOLD = 12
WATCH_THRESHOLD = 8


# ─── Core scoring ─────────────────────────────────────────────────────────────


def _signal_age_days(signal_date_str: str) -> int:
    """Return days since the signal date, or 0 if unparseable."""
    if not signal_date_str or "VERIFY" in signal_date_str.upper():
        return 0
    try:
        d = date.fromisoformat(signal_date_str[:10])
        return max(0, (date.today() - d).days)
    except ValueError:
        return 0


def compute_score(account: dict) -> float:
    """Compute the current dynamic score for one account.

    Does NOT modify the account dict — call apply_score() to persist.
    """
    tier = account.get("icp_tier", 3)
    signal_type = account.get("why_now_signal", {}).get("type", "manual")
    signal_date = account.get("why_now_signal", {}).get("date", "")
    status = account.get("status", "monitor")

    # Base
    base = TIER_WEIGHT.get(tier, 1) * SIGNAL_WEIGHT.get(signal_type, 1)

    # Status modifier
    status_mod = STATUS_DELTA.get(status, 0)

    # Freshness decay
    age_days = _signal_age_days(signal_date)
    decay_periods = age_days / DECAY_HALF_LIFE_DAYS
    freshness_penalty = base * DECAY_RATE * decay_periods

    # Variant response modifier (most recent sentiment in score_history)
    sentiment_mod = 0.0
    for event in reversed(account.get("score_history", [])):
        if event.get("type") == "sentiment":
            sentiment_mod = SENTIMENT_DELTA.get(event.get("value", ""), 0)
            break

    raw = base + status_mod + sentiment_mod - freshness_penalty
    return round(max(0.0, raw), 2)


def apply_score(account: dict, reason: str = "recalculated") -> dict:
    """Compute and store current_score + append to score_history. Returns account."""
    prev = account.get("current_score")
    new_score = compute_score(account)

    account["current_score"] = new_score

    history = account.setdefault("score_history", [])
    entry: dict = {
        "date": date.today().isoformat(),
        "score": new_score,
        "reason": reason,
        "type": "recalculate",
    }
    if prev is not None:
        entry["delta"] = round(new_score - prev, 2)
    history.append(entry)

    return account


def record_event(
    account: dict,
    event_type: str,
    value: str,
    reason: str = "",
) -> dict:
    """Record a score-affecting event (sentiment, birddog_signal, etc.) and recompute.

    event_type: "sentiment" | "birddog_signal" | "status_change"
    value:      event-specific string (sentiment: positive/neutral/negative; etc.)
    """
    history = account.setdefault("score_history", [])
    history.append({
        "date": date.today().isoformat(),
        "type": event_type,
        "value": value,
        "reason": reason,
        "score": account.get("current_score"),
    })
    return apply_score(account, reason=reason or f"{event_type}={value}")


# ─── Matrix-level operations ──────────────────────────────────────────────────


def score_matrix(client: str, save: bool = True) -> list[dict]:
    """Recompute scores for all accounts in a client matrix.

    Returns list of (account, old_score, new_score) tuples for changed accounts.
    If save=True, writes the updated matrix back to disk.
    """
    matrix = load_client_matrix(client)
    changed = []

    for account in matrix.get("accounts", []):
        old = account.get("current_score")
        apply_score(account, reason="weekly_refresh")
        new = account["current_score"]
        if old is None or abs(new - old) > 0.1:
            changed.append({
                "company": account["company"],
                "domain": account["domain"],
                "old_score": old,
                "new_score": new,
                "status": account.get("status", "monitor"),
            })

    if save:
        path = _matrix_path(client)
        path.write_text(json.dumps(matrix, indent=2) + "\n")

    return changed


def get_prioritized(client: str, min_score: float = 0) -> list[dict]:
    """Return accounts sorted by current_score descending, optionally filtered."""
    matrix = load_client_matrix(client)
    accounts = []
    for a in matrix.get("accounts", []):
        score = a.get("current_score") or compute_score(a)
        if score >= min_score:
            accounts.append({**a, "current_score": score})
    return sorted(accounts, key=lambda x: x["current_score"], reverse=True)


def threshold_label(score: float) -> str:
    """Return a human-readable tier label for a score."""
    if score >= HOT_THRESHOLD:
        return "HOT"
    if score >= ENGAGEMENT_THRESHOLD:
        return "ENGAGE"
    if score >= WATCH_THRESHOLD:
        return "WATCH"
    return "COLD"


# ─── CLI ─────────────────────────────────────────────────────────────────────


import click  # noqa: E402


@click.group()
def cli():
    """Dynamic ICP score engine for the account matrix."""
    pass


@cli.command("refresh")
@click.option("--client", required=True, help="Client slug.")
@click.option("--min-delta", default=0.5, show_default=True,
              help="Only report accounts whose score changed by this much.")
def refresh(client: str, min_delta: float):
    """Recompute scores for all accounts and report changes."""
    changed = score_matrix(client, save=True)
    significant = [c for c in changed if abs((c["new_score"] or 0) - (c["old_score"] or 0)) >= min_delta]

    if not significant:
        click.echo(f"  No significant score changes (threshold: {min_delta}).")
        return

    click.echo(f"\n  Score changes for {client}:")
    click.echo(f"  {'Company':<25} {'Old':>6} {'New':>6} {'Delta':>7} {'Status':<15} Label")
    click.echo(f"  {'-'*25} {'-'*6} {'-'*6} {'-'*7} {'-'*15} {'-'*8}")
    for c in sorted(significant, key=lambda x: x["new_score"] or 0, reverse=True):
        old = c["old_score"] or 0
        new = c["new_score"] or 0
        delta = new - old
        label = threshold_label(new)
        click.echo(
            f"  {c['company']:<25} {old:>6.1f} {new:>6.1f} "
            f"{'▲' if delta > 0 else '▼'}{abs(delta):>5.1f}  "
            f"{c['status']:<15} {label}"
        )


@cli.command("list")
@click.option("--client", required=True, help="Client slug.")
@click.option("--min-score", default=0.0, show_default=True)
def list_scores(client: str, min_score: float):
    """List all accounts ranked by current score."""
    accounts = get_prioritized(client, min_score=min_score)
    if not accounts:
        click.echo("  No accounts found.")
        return

    click.echo(f"\n  {'#':<4} {'Company':<25} {'Score':>6} {'Tier':<6} {'Status':<16} {'Signal':<14} Label")
    click.echo(f"  {'-'*4} {'-'*25} {'-'*6} {'-'*6} {'-'*16} {'-'*14} {'-'*6}")
    for i, a in enumerate(accounts, 1):
        score = a["current_score"]
        click.echo(
            f"  {i:<4} {a['company']:<25} {score:>6.1f} "
            f"T{a.get('icp_tier', '?'):<5} {a.get('status', '?'):<16} "
            f"{a.get('why_now_signal', {}).get('type', '?'):<14} "
            f"{threshold_label(score)}"
        )


@cli.command("record-event")
@click.option("--client", required=True)
@click.option("--company", required=True)
@click.option("--event", required=True, type=click.Choice(["sentiment", "birddog_signal", "status_change"]))
@click.option("--value", required=True, help="Event value (e.g. positive, negative, new_signal).")
@click.option("--reason", default="", help="Optional note on why this event occurred.")
def record(client: str, company: str, event: str, value: str, reason: str):
    """Record a score-affecting event for one account."""
    matrix = load_client_matrix(client)
    from generate_outreach import find_account  # noqa: E402
    account = find_account(matrix, company)
    record_event(account, event_type=event, value=value, reason=reason)
    path = _matrix_path(client)
    path.write_text(json.dumps(matrix, indent=2) + "\n")
    click.echo(
        f"  Recorded {event}={value} for {company}. "
        f"New score: {account['current_score']} ({threshold_label(account['current_score'])})"
    )


if __name__ == "__main__":
    cli()
