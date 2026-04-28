"""
DeployGTM — Dynamic ICP Score Engine

Score = fit_score + signal_bonus + status_mod + sentiment_mod

  fit_score     : 0–10 set by research_accounts.py.  Never decays.
                  Falls back to a tier estimate if research hasn't run yet.
  signal_bonus  : SIGNAL_WEIGHT × 3 × recency_factor.  Decays to 0 over
                  2 × DECAY_HALF_LIFE_DAYS.  0 when no verified signal date.
  status_mod    : lifecycle stage contribution (replied/meeting_booked push
                  scores up regardless of signal age)
  sentiment_mod : most-recent variant response sentiment

Separation of concerns
  fit_score    answers "is this a good ICP fit?" — set once by AI research
  signal_bonus answers "is now the right time?" — decays as the signal ages
  status_mod   answers "how engaged are they?" — lifts score as deals progress

Score thresholds:
  >= 12  → HOT — activate immediately
  >= 8   → ENGAGE — batch outreach
  >= 4   → WATCH — monitor, not ready
  < 4    → COLD — deprioritise

Used by:
  - research_accounts.py  (sets fit_score after company research)
  - weekly_signal_report.py
  - verify_signals.py
  - batch_outreach.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.resolve().parents[2]

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_outreach import _matrix_path, load_client_matrix  # noqa: E402


# ─── Weights ──────────────────────────────────────────────────────────────────

# Fallback fit_score estimate when research hasn't run yet
TIER_FIT_FALLBACK = {1: 7.0, 2: 4.5, 3: 2.0}

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
SIGNAL_MULTIPLIER = 3  # max bonus = SIGNAL_WEIGHT × SIGNAL_MULTIPLIER

# Status transitions — reflect engagement progress, not signal strength
STATUS_DELTA = {
    "active": 1,
    "outreach_sent": 2,
    "replied": 6,
    "meeting_booked": 12,
    "no_fit": -15,
    "paused": -3,
    "monitor": 0,
}

SENTIMENT_DELTA = {
    "positive": 4,
    "neutral": 1,
    "negative": -2,
}

# Signal bonus decays to 0 over 2 × DECAY_HALF_LIFE_DAYS
DECAY_HALF_LIFE_DAYS = 60

HOT_THRESHOLD = 12
ENGAGEMENT_THRESHOLD = 8
WATCH_THRESHOLD = 4


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _signal_age_days(signal_date_str: str) -> Optional[int]:
    """Return days since the signal date, or None if absent / VERIFY marker."""
    if not signal_date_str or "VERIFY" in signal_date_str.upper():
        return None
    try:
        d = date.fromisoformat(signal_date_str[:10])
        return max(0, (date.today() - d).days)
    except ValueError:
        return None


def _recency_factor(age_days: Optional[int]) -> float:
    """Linear decay from 1.0 (fresh) to 0.0 at 2 × half-life. 0 if no date."""
    if age_days is None:
        return 0.0
    max_age = DECAY_HALF_LIFE_DAYS * 2
    return max(0.0, 1.0 - age_days / max_age)


# ─── Core scoring ─────────────────────────────────────────────────────────────


def compute_score(account: dict) -> float:
    """Compute the current dynamic score for one account.

    Does NOT modify the account dict — call apply_score() to persist.
    """
    tier = account.get("icp_tier", 3)
    signal = account.get("why_now_signal", {})
    signal_type = signal.get("type", "manual")
    signal_date = signal.get("date", "")
    status = account.get("status", "monitor")

    # Base: research-derived fit score (never decays)
    fit_score: float = account.get("fit_score") or TIER_FIT_FALLBACK.get(tier, 2.0)

    # Signal bonus: decays with signal age; 0 if no verified date
    age_days = _signal_age_days(signal_date)
    recency = _recency_factor(age_days)
    signal_bonus = SIGNAL_WEIGHT.get(signal_type, 1) * SIGNAL_MULTIPLIER * recency

    # Status modifier
    status_mod = STATUS_DELTA.get(status, 0)

    # Variant sentiment modifier (most recent in history)
    sentiment_mod = 0.0
    for event in reversed(account.get("score_history", [])):
        if event.get("type") == "sentiment":
            sentiment_mod = SENTIMENT_DELTA.get(event.get("value", ""), 0)
            break

    raw = fit_score + signal_bonus + status_mod + sentiment_mod
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


def set_fit_score(account: dict, fit_score: float, rationale: str = "") -> dict:
    """Set the research-derived fit_score and recompute. Returns account."""
    account["fit_score"] = round(min(10.0, max(0.0, fit_score)), 2)
    history = account.setdefault("score_history", [])
    history.append({
        "date": date.today().isoformat(),
        "type": "fit_score_set",
        "value": account["fit_score"],
        "reason": rationale or "research",
        "score": account.get("current_score"),
    })
    return apply_score(account, reason=f"fit_score={account['fit_score']}")


# ─── Matrix-level operations ──────────────────────────────────────────────────


def score_matrix(client: str, save: bool = True) -> list[dict]:
    """Recompute scores for all accounts in a client matrix.

    Returns list of change dicts for accounts whose score shifted > 0.1.
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
                "fit_score": account.get("fit_score"),
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
    click.echo(f"  {'Company':<25} {'Fit':>5} {'Old':>6} {'New':>6} {'Delta':>7} {'Status':<15} Label")
    click.echo(f"  {'-'*25} {'-'*5} {'-'*6} {'-'*6} {'-'*7} {'-'*15} {'-'*8}")
    for c in sorted(significant, key=lambda x: x["new_score"] or 0, reverse=True):
        old = c["old_score"] or 0
        new = c["new_score"] or 0
        delta = new - old
        fit = c.get("fit_score") or "—"
        fit_str = f"{fit:.1f}" if isinstance(fit, float) else fit
        label = threshold_label(new)
        click.echo(
            f"  {c['company']:<25} {fit_str:>5} {old:>6.1f} {new:>6.1f} "
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

    click.echo(f"\n  {'#':<4} {'Company':<25} {'Fit':>5} {'Score':>6} {'Tier':<6} {'Status':<16} {'Signal':<14} Label")
    click.echo(f"  {'-'*4} {'-'*25} {'-'*5} {'-'*6} {'-'*6} {'-'*16} {'-'*14} {'-'*6}")
    for i, a in enumerate(accounts, 1):
        score = a["current_score"]
        fit = a.get("fit_score")
        fit_str = f"{fit:.1f}" if fit is not None else "—"
        click.echo(
            f"  {i:<4} {a['company']:<25} {fit_str:>5} {score:>6.1f} "
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
