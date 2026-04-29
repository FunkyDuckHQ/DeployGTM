"""
DeployGTM — ICP Scoring Engine

Scores accounts on two dimensions:
  ICP Fit (1–5) × Signal Strength (1–3) = Priority

Priority thresholds (from config.yaml):
  ≥ 12 → reach out immediately
  8–11 → reach out this week
  5–7  → nurture / monitor
  < 5  → skip

Can be imported by pipeline.py or run standalone:
  python scripts/score.py --help
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from typing import Optional

import click
import yaml


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


# ─── ICP Fit (1–5) ────────────────────────────────────────────────────────────

ICP_CRITERIA = {
    "b2b_saas":         {"weight": 2, "label": "B2B SaaS"},
    "seed_to_series_a": {"weight": 2, "label": "Seed–Series A stage"},
    "employees_5_30":   {"weight": 1, "label": "5–30 employees"},
    "technical_buyer":  {"weight": 1, "label": "Sells to technical/enterprise buyers"},
    "us_based":         {"weight": 1, "label": "US-based"},
    "needs_pipeline":   {"weight": 1, "label": "No repeatable outbound pipeline"},
    "hubspot_or_open":  {"weight": 1, "label": "Uses HubSpot or open to it"},
}


def score_icp_fit(account: dict) -> tuple[int, list[str]]:
    """
    Score ICP fit 1–5 based on how many weighted criteria are met.

    account keys (all optional, default False/None):
      b2b_saas, seed_to_series_a, employees_5_30, technical_buyer,
      us_based, needs_pipeline, hubspot_or_open
      employees (int) — used to auto-derive employees_5_30 if present
      funding_stage (str) — "seed" / "series_a" / "series_b" etc.
      business_model (str) — "b2b_saas" / "b2b" / "b2c" etc.

    Returns (score 1–5, list of rationale strings)
    """
    hits = []
    misses = []

    # Auto-derive from structured fields if explicit booleans not set
    resolved = dict(account)
    if "employees" in account and "employees_5_30" not in account:
        emp = account["employees"]
        if isinstance(emp, int):
            resolved["employees_5_30"] = 5 <= emp <= 30

    if "funding_stage" in account and "seed_to_series_a" not in account:
        stage = str(account.get("funding_stage", "")).lower()
        resolved["seed_to_series_a"] = stage in ("seed", "series_a", "series a")

    if "business_model" in account and "b2b_saas" not in account:
        bm = str(account.get("business_model", "")).lower()
        resolved["b2b_saas"] = "saas" in bm or bm == "b2b_saas"

    total_weight = sum(c["weight"] for c in ICP_CRITERIA.values())
    earned_weight = 0

    for key, meta in ICP_CRITERIA.items():
        if resolved.get(key):
            earned_weight += meta["weight"]
            hits.append(f"✓ {meta['label']}")
        else:
            misses.append(f"✗ {meta['label']}")

    # Map earned weight to 1–5 scale
    ratio = earned_weight / total_weight
    if ratio >= 0.90:
        score = 5
    elif ratio >= 0.70:
        score = 4
    elif ratio >= 0.50:
        score = 3
    elif ratio >= 0.30:
        score = 2
    else:
        score = 1

    rationale = hits + misses
    return score, rationale


# ─── Signal Strength (1–3) ────────────────────────────────────────────────────

SIGNAL_WEIGHTS = {
    "funding":      3,   # Just raised — has budget + pressure
    "hiring":       3,   # Posting sales roles — investing in GTM
    "gtm_struggle": 3,   # Founder posting pain publicly — high intent
    "agency_churn": 2,   # Tried advice route — ready to build
    "tool_adoption":2,   # Adopted Clay/Apollo — has tools, needs system
    "manual":       1,   # No specific signal, just ICP match
}


def _signal_age_days(signal_date: Optional[str]) -> int | None:
    if signal_date is None:
        return None
    try:
        sig_date = datetime.strptime(signal_date, "%Y-%m-%d").date()
    except ValueError:
        return None
    return max(0, (date.today() - sig_date).days)


def score_signal_strength(signal_type: str, signal_date: Optional[str]) -> tuple[int, str]:
    """
    Score signal strength 1–3.

    signal_type: one of the SIGNAL_WEIGHTS keys
    signal_date: ISO date string (YYYY-MM-DD) or None

    Returns (score, rationale string)
    """
    base = SIGNAL_WEIGHTS.get(signal_type, 1)

    if signal_date is None:
        return 1, f"Signal type '{signal_type}' but no date — treated as background signal"

    days_ago = _signal_age_days(signal_date)
    if days_ago is None:
        return 1, f"Could not parse signal_date '{signal_date}'"

    if days_ago <= 30:
        recency_mult = 1.0
        recency_label = f"active ({days_ago}d ago)"
    elif days_ago <= 90:
        recency_mult = 0.67
        recency_label = f"recent ({days_ago}d ago)"
    else:
        recency_mult = 0.33
        recency_label = f"stale ({days_ago}d ago)"

    raw = base * recency_mult
    score = max(1, min(3, round(raw)))

    rationale = f"{signal_type} signal, {recency_label} → strength {score}/3"
    return score, rationale


def score_urgency(signal_type: str, signal_date: Optional[str], birddog_score: Optional[int] = None) -> tuple[int, dict]:
    """Score current urgency on a 0-100 scale with explicit recency decay."""
    base_weight = SIGNAL_WEIGHTS.get(signal_type, 1)
    base = {1: 35, 2: 60, 3: 80}.get(base_weight, 35)
    if birddog_score is not None:
        base = max(base, min(100, int(birddog_score)))

    days_ago = _signal_age_days(signal_date)
    if days_ago is None:
        decay_multiplier = 0.45
        label = "undated"
    elif days_ago <= 14:
        decay_multiplier = 1.0
        label = f"hot ({days_ago}d old)"
    elif days_ago <= 30:
        decay_multiplier = 0.85
        label = f"active ({days_ago}d old)"
    elif days_ago <= 90:
        decay_multiplier = 0.60
        label = f"recent ({days_ago}d old)"
    else:
        decay_multiplier = 0.30
        label = f"stale ({days_ago}d old)"

    score = max(0, min(100, round(base * decay_multiplier)))
    return score, {
        "signal_type": signal_type,
        "signal_date": signal_date,
        "days_ago": days_ago,
        "decay_multiplier": decay_multiplier,
        "label": label,
        "rationale": f"{signal_type} urgency is {label}",
    }


def score_confidence(account: dict) -> tuple[int, str]:
    confidence = str(account.get("confidence") or account.get("enrichment_confidence") or "").lower()
    if confidence == "high":
        return 90, "high source confidence"
    if confidence == "medium":
        return 65, "medium source confidence"
    if confidence == "low":
        return 40, "low source confidence"
    if account:
        return 55, "partial account evidence present"
    return 25, "little account evidence present"


def calculate_activation_priority(
    *,
    icp_fit_score: int,
    urgency_score: int,
    engagement_score: int,
    confidence_score: int,
) -> int:
    """Blend scores while preserving ICP fit and urgency as separate fields."""
    return round(
        (icp_fit_score * 0.45)
        + (urgency_score * 0.35)
        + (engagement_score * 0.10)
        + (confidence_score * 0.10)
    )


# ─── Priority ─────────────────────────────────────────────────────────────────

def calculate_priority(
    icp_fit: int,
    signal_strength: int,
    config: Optional[dict] = None,
) -> tuple[int, str]:
    """
    Priority = ICP Fit × Signal Strength.
    Returns (priority_score, action_label).
    """
    if config is None:
        config = load_config()

    thresholds = config.get("scoring", {})
    immediately = thresholds.get("activate_immediately", 12)
    this_week   = thresholds.get("activate_this_week", 8)
    nurture     = thresholds.get("nurture", 5)

    priority = icp_fit * signal_strength

    if priority >= immediately:
        action = "REACH OUT IMMEDIATELY"
    elif priority >= this_week:
        action = "Reach out this week"
    elif priority >= nurture:
        action = "Add to nurture / monitor"
    else:
        action = "Skip — not ICP or signal too weak"

    return priority, action


# ─── Full score ───────────────────────────────────────────────────────────────

def score_account(account: dict, signal_type: str, signal_date: Optional[str], config: Optional[dict] = None) -> dict:
    """
    Run the full scoring pipeline on one account.

    Returns a dict with all scores, rationales, and recommended action.
    """
    if config is None:
        config = load_config()

    icp_fit, icp_rationale = score_icp_fit(account)
    signal_strength, signal_rationale = score_signal_strength(signal_type, signal_date)
    priority, action = calculate_priority(icp_fit, signal_strength, config)
    urgency_score, decay = score_urgency(
        signal_type,
        signal_date,
        birddog_score=account.get("birddog_score"),
    )
    confidence_score, confidence_rationale = score_confidence(account)
    engagement_score = int(account.get("engagement_score") or 0)
    icp_fit_score = icp_fit * 20
    activation_priority = calculate_activation_priority(
        icp_fit_score=icp_fit_score,
        urgency_score=urgency_score,
        engagement_score=engagement_score,
        confidence_score=confidence_score,
    )

    return {
        # Legacy fields retained for existing pipeline commands.
        "icp_fit": icp_fit,
        "signal_strength": signal_strength,
        "priority": priority,
        "action": action,
        "icp_rationale": icp_rationale,
        "signal_rationale": signal_rationale,
        # Signal Audit vNext scoring fields.
        "icp_fit_score": icp_fit_score,
        "urgency_score": urgency_score,
        "engagement_score": engagement_score,
        "confidence_score": confidence_score,
        "activation_priority": activation_priority,
        "decay": decay,
        "confidence_rationale": confidence_rationale,
        "activation_rationale": [
            f"ICP fit contributes {icp_fit_score}/100",
            f"Urgency contributes {urgency_score}/100 from current signal timing",
            f"Engagement contributes {engagement_score}/100 until outbound tests run",
            f"Confidence contributes {confidence_score}/100 from research evidence",
        ],
    }


# ─── CLI (standalone use) ─────────────────────────────────────────────────────

@click.command()
@click.option("--account-json", "-a", required=True, help="JSON string or @path to file with account fields")
@click.option("--signal-type", "-s", required=True,
              type=click.Choice(list(SIGNAL_WEIGHTS.keys())), help="Signal type")
@click.option("--signal-date", "-d", default=None, help="Signal date YYYY-MM-DD (leave blank if unknown)")
@click.option("--config", "config_path", default="config.yaml", help="Path to config.yaml")
def cli(account_json: str, signal_type: str, signal_date: Optional[str], config_path: str):
    """Score a single account from the command line."""
    if account_json.startswith("@"):
        with open(account_json[1:]) as f:
            account = json.load(f)
    else:
        account = json.loads(account_json)

    config = load_config(config_path)
    result = score_account(account, signal_type, signal_date, config)

    click.echo(f"\n{'─'*50}")
    click.echo(f"  ICP Fit:        {result['icp_fit']}/5")
    click.echo(f"  Signal Strength:{result['signal_strength']}/3")
    click.echo(f"  Priority:       {result['priority']}/15")
    click.echo(f"  Urgency:        {result['urgency_score']}/100")
    click.echo(f"  Activation:     {result['activation_priority']}/100")
    click.echo(f"  Action:         {result['action']}")
    click.echo(f"{'─'*50}")
    click.echo("\nICP criteria:")
    for r in result["icp_rationale"]:
        click.echo(f"  {r}")
    click.echo(f"\nSignal: {result['signal_rationale']}")
    click.echo()


if __name__ == "__main__":
    cli()
