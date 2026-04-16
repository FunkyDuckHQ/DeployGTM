"""
DeployGTM — BirdDog Signal Monitoring Integration

BirdDog monitors target accounts for buying signals continuously.
We are an authorized BirdDog reseller (30% recurring commission).

This module handles:
  - Adding accounts to your BirdDog watchlist
  - Pulling recent signals/alerts
  - Converting BirdDog signals into pipeline.py input format
  - Generating batch CSV from triggered signals

When birddog.enabled = false in config.yaml, signals are captured manually
via data/signals_intake.csv.

Usage:
  # Check BirdDog status and account count
  python scripts/birddog.py status

  # Add accounts from a CSV to BirdDog watchlist
  python scripts/birddog.py add-accounts --input data/yc_w26_targets.csv

  # Pull recent signals and save as batch CSV
  python scripts/birddog.py pull-signals

  # Pull signals and immediately run them through the pipeline
  python scripts/birddog.py pull-signals --run-pipeline

  # List all monitored accounts
  python scripts/birddog.py list-accounts
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import click
import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

# BirdDog API — adjust base URL if they provide a different endpoint
BIRDDOG_BASE = "https://api.birddog.io/v1"

# Signal type mapping: BirdDog signal names → our internal signal types
SIGNAL_TYPE_MAP = {
    "funding":              "funding",
    "funding_announcement": "funding",
    "seed_round":           "funding",
    "series_a":             "funding",
    "job_posting":          "hiring",
    "hiring_sales":         "hiring",
    "executive_hire":       "hiring",
    "linkedin_post":        "gtm_struggle",
    "content_engagement":   "gtm_struggle",
    "agency_change":        "agency_churn",
    "technology_adoption":  "tool_adoption",
    "tech_stack_change":    "tool_adoption",
}


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def _key() -> str:
    key = os.environ.get("BIRDDOG_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "BIRDDOG_API_KEY is not set.\n"
            "Add it to your .env file. Get it from your BirdDog dashboard."
        )
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_key()}",
        "Content-Type": "application/json",
    }


# ─── API wrappers ─────────────────────────────────────────────────────────────

def get_status() -> dict:
    """Fetch BirdDog account info and monitored account count."""
    resp = requests.get(f"{BIRDDOG_BASE}/account", headers=_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def list_monitored_accounts(page: int = 1, per_page: int = 100) -> list[dict]:
    """List all accounts currently being monitored."""
    accounts = []
    while True:
        resp = requests.get(
            f"{BIRDDOG_BASE}/accounts",
            headers=_headers(),
            params={"page": page, "per_page": per_page},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("accounts") or data.get("data") or []
        accounts.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return accounts


def add_account(company: str, domain: str) -> dict:
    """Add a single account to BirdDog monitoring."""
    resp = requests.post(
        f"{BIRDDOG_BASE}/accounts",
        headers=_headers(),
        json={"name": company, "domain": domain},
        timeout=15,
    )
    if resp.status_code == 409:
        return {"status": "already_exists", "domain": domain}
    resp.raise_for_status()
    return resp.json()


def pull_signals(
    days_back: int = 7,
    signal_types: Optional[list[str]] = None,
    min_score: Optional[int] = None,
) -> list[dict]:
    """
    Pull recent signals from BirdDog.

    Returns a list of signal dicts, each normalized to pipeline format.
    """
    since = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {"since": since, "per_page": 100}
    if signal_types:
        params["types"] = ",".join(signal_types)
    if min_score:
        params["min_score"] = min_score

    resp = requests.get(
        f"{BIRDDOG_BASE}/signals",
        headers=_headers(),
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    raw_signals = resp.json().get("signals") or resp.json().get("data") or []

    return [_normalize_signal(s) for s in raw_signals]


def _normalize_signal(raw: dict) -> dict:
    """Convert a BirdDog signal to our pipeline's signal format."""
    raw_type = str(raw.get("type") or raw.get("signal_type") or "").lower().replace("-", "_")
    normalized_type = SIGNAL_TYPE_MAP.get(raw_type, "manual")

    # BirdDog may return date as ISO string or unix timestamp
    signal_date = raw.get("date") or raw.get("detected_at") or raw.get("created_at")
    if signal_date and isinstance(signal_date, (int, float)):
        signal_date = datetime.fromtimestamp(signal_date).strftime("%Y-%m-%d")
    elif signal_date and "T" in str(signal_date):
        signal_date = str(signal_date)[:10]

    account = raw.get("account") or raw.get("company") or {}

    return {
        "company": account.get("name") or raw.get("company_name", ""),
        "domain": account.get("domain") or raw.get("domain", ""),
        "signal_type": normalized_type,
        "signal_date": signal_date or date.today().isoformat(),
        "signal_source": "BirdDog",
        "signal_summary": raw.get("summary") or raw.get("description") or raw.get("title", ""),
        "birddog_signal_id": raw.get("id", ""),
        "birddog_score": raw.get("score") or raw.get("relevance_score"),
        "birddog_raw_type": raw_type,
    }


def signals_to_batch_csv(signals: list[dict], output_path: str) -> Path:
    """Write normalized signals to a batch input CSV for pipeline.py batch run."""
    out = Path(output_path)
    fieldnames = [
        "company", "domain", "signal_type", "signal_date",
        "signal_source", "signal_summary",
    ]
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for sig in signals:
            if sig.get("company") and sig.get("domain"):
                writer.writerow(sig)
    return out


# ─── CLI ──────────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """BirdDog signal monitoring integration."""
    pass


@cli.command()
def status():
    """Check BirdDog account status and monitored account count."""
    config = load_config()
    enabled = config.get("tools", {}).get("birddog", {}).get("enabled", False)

    if not enabled:
        click.echo("\nBirdDog is disabled (tools.birddog.enabled = false in config.yaml)")
        click.echo("Set BIRDDOG_API_KEY in .env and enable in config.yaml to activate.")
        return

    try:
        info = get_status()
        accounts = list_monitored_accounts()
        click.echo(f"\nBirdDog status: connected")
        click.echo(f"  Plan:              {info.get('plan', 'unknown')}")
        click.echo(f"  Monitored accounts:{len(accounts)}")
        click.echo(f"  Account limit:     {info.get('account_limit', 'unknown')}")
    except EnvironmentError as e:
        click.echo(f"\n{e}")
    except requests.RequestException as e:
        click.echo(f"\nBirdDog API error: {e}", err=True)


@cli.command("add-accounts")
@click.option("--input", "-i", "input_file", required=True,
              help="CSV with company and domain columns")
@click.option("--dry-run", is_flag=True)
def add_accounts(input_file, dry_run):
    """Add accounts from a CSV to BirdDog monitoring."""
    rows = []
    with open(input_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            normalized = {k.strip().lower(): (v or "").strip() for k, v in row.items()}
            if normalized.get("domain"):
                rows.append(normalized)

    click.echo(f"\nAdding {len(rows)} accounts to BirdDog...")
    added = skipped = errors = 0

    for row in rows:
        company = row.get("company", row["domain"])
        domain = row["domain"]

        if dry_run:
            click.echo(f"  [dry-run] Would add: {company} ({domain})")
            added += 1
            continue

        try:
            result = add_account(company, domain)
            if result.get("status") == "already_exists":
                click.echo(f"  ~ {domain} (already monitored)")
                skipped += 1
            else:
                click.echo(f"  + {domain}")
                added += 1
            time.sleep(0.3)
        except requests.RequestException as e:
            click.echo(f"  ✗ {domain}: {e}", err=True)
            errors += 1

    click.echo(f"\nDone. Added: {added}, Already monitored: {skipped}, Errors: {errors}")


@cli.command("pull-signals")
@click.option("--days", default=7, help="Look back N days (default 7)")
@click.option("--min-score", default=None, type=int,
              help="Only pull signals with BirdDog relevance score >= this")
@click.option("--output", "-o", default=None,
              help="Output CSV path (default: data/signals_YYYY-MM-DD.csv)")
@click.option("--run-pipeline", is_flag=True,
              help="After pulling signals, run batch pipeline on them")
@click.option("--config", "config_path", default="config.yaml")
def pull_signals_cmd(days, min_score, output, run_pipeline, config_path):
    """Pull recent signals from BirdDog and save as batch input CSV."""
    config = load_config(config_path)
    enabled = config.get("tools", {}).get("birddog", {}).get("enabled", False)

    if not enabled:
        click.echo("\nBirdDog is disabled. Set tools.birddog.enabled = true in config.yaml.")
        click.echo("For manual signal capture, edit data/signals_intake.csv and run:")
        click.echo("  python scripts/batch.py run --input data/signals_intake.csv")
        return

    click.echo(f"\nPulling signals from last {days} days...")

    try:
        signals = pull_signals(days_back=days, min_score=min_score)
    except (EnvironmentError, requests.RequestException) as e:
        click.echo(f"Error: {e}", err=True)
        return

    click.echo(f"Found {len(signals)} signals")

    if not signals:
        click.echo("No new signals. Check back tomorrow or expand the days window.")
        return

    # Show signal breakdown
    from collections import Counter
    type_counts = Counter(s["signal_type"] for s in signals)
    for sig_type, count in type_counts.most_common():
        click.echo(f"  {sig_type}: {count}")

    # Save to CSV
    out_path = output or f"data/signals_{date.today().isoformat()}.csv"
    Path("data").mkdir(exist_ok=True)
    csv_path = signals_to_batch_csv(signals, out_path)
    click.echo(f"\nSaved to: {csv_path}")

    if run_pipeline:
        click.echo("\nRunning batch pipeline on signals...")
        import subprocess
        subprocess.run([
            sys.executable, "scripts/batch.py", "run",
            "--input", str(csv_path),
            "--config", config_path,
        ], check=True)


@cli.command("list-accounts")
@click.option("--output", "-o", default=None, help="Save account list to CSV")
def list_accounts(output):
    """List all accounts currently monitored by BirdDog."""
    try:
        accounts = list_monitored_accounts()
    except (EnvironmentError, requests.RequestException) as e:
        click.echo(f"Error: {e}", err=True)
        return

    click.echo(f"\nMonitored accounts ({len(accounts)}):")
    for a in accounts:
        name = a.get("name") or a.get("company_name", "")
        domain = a.get("domain", "")
        click.echo(f"  {name} ({domain})")

    if output:
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["company", "domain"], extrasaction="ignore")
            writer.writeheader()
            for a in accounts:
                writer.writerow({
                    "company": a.get("name") or a.get("company_name", ""),
                    "domain": a.get("domain", ""),
                })
        click.echo(f"\nSaved to {output}")


if __name__ == "__main__":
    cli()
