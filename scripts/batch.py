"""
DeployGTM — Batch Pipeline Runner

Processes a CSV of target accounts through the full pipeline:
  research → enrich → score → outreach → save output

Respects rate limits. Skips accounts below priority threshold.
Generates a summary CSV when done.

CSV format (see data/batch_template.csv):
  company, domain, signal_type, signal_date, signal_source, signal_summary

Usage:
  # Run batch on a CSV file
  python scripts/batch.py run --input data/yc_w26_targets.csv

  # Dry run — skip Apollo and outreach, just score and log
  python scripts/batch.py run --input data/yc_w26_targets.csv --score-only

  # Resume — skip domains already in output/
  python scripts/batch.py run --input data/yc_w26_targets.csv --resume

  # Review summary of a completed batch
  python scripts/batch.py summary --input data/yc_w26_targets.csv
"""

from __future__ import annotations

import csv
import json
import sys
import time
from datetime import date
from pathlib import Path
from typing import Optional

import click
import yaml
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from research import research_account, load_brain
from apollo import find_contacts, enrich_company
from score import score_account
from outreach import generate_outreach


REQUIRED_COLUMNS = {"company", "domain", "signal_type"}

# Seconds to wait between accounts — be a good API citizen
INTER_ACCOUNT_DELAY = 3
# Seconds to wait after Apollo calls
APOLLO_DELAY = 1


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def output_exists(domain: str, config: dict) -> Optional[Path]:
    """Check if pipeline output already exists for this domain (any date)."""
    out_dir = Path(config.get("output", {}).get("path", "output"))
    slug = domain.replace(".", "_")
    matches = list(out_dir.glob(f"{slug}_*.json"))
    return matches[0] if matches else None


def output_path(domain: str, config: dict) -> Path:
    out_dir = Path(config.get("output", {}).get("path", "output"))
    out_dir.mkdir(exist_ok=True)
    filename = f"{domain.replace('.', '_')}_{date.today().isoformat()}.json"
    return out_dir / filename


def read_batch_csv(csv_path: str) -> list[dict]:
    """Parse batch input CSV. Returns list of row dicts."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Normalize column names
        if reader.fieldnames is None:
            raise ValueError(f"CSV file appears empty: {csv_path}")

        missing = REQUIRED_COLUMNS - {c.strip().lower() for c in reader.fieldnames}
        if missing:
            raise ValueError(
                f"CSV missing required columns: {missing}\n"
                f"Required: {REQUIRED_COLUMNS}\n"
                f"Found: {reader.fieldnames}"
            )

        for i, row in enumerate(reader, 1):
            normalized = {k.strip().lower(): (v or "").strip() for k, v in row.items()}
            if not normalized.get("company") or not normalized.get("domain"):
                click.echo(f"  Row {i}: skipping — missing company or domain", err=True)
                continue
            rows.append(normalized)

    return rows


def write_summary(results: list[dict], summary_path: Path):
    """Write batch summary CSV."""
    if not results:
        return

    fieldnames = [
        "company", "domain", "signal_type", "signal_date",
        "icp_fit", "signal_strength", "priority", "action",
        "icp_verdict", "confidence",
        "contacts_found", "outreach_generated",
        "output_file", "status", "error",
    ]

    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)


# ─── run ──────────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """Batch pipeline runner."""
    pass


@cli.command()
@click.option("--input", "-i", "input_file", required=True,
              help="Path to batch input CSV (see data/batch_template.csv)")
@click.option("--score-only", is_flag=True,
              help="Only research and score — skip Apollo and outreach generation")
@click.option("--skip-below", default=None, type=int,
              help="Skip accounts with priority below this (default: from config.yaml)")
@click.option("--resume", is_flag=True,
              help="Skip accounts that already have output files")
@click.option("--limit", default=None, type=int,
              help="Process at most N accounts (useful for testing)")
@click.option("--config", "config_path", default="config.yaml")
def run(input_file, score_only, skip_below, resume, limit, config_path):
    """Run the pipeline on every row in a CSV file."""
    config = load_config(config_path)
    threshold = skip_below or config.get("scoring", {}).get("skip_below", 5)
    apollo_enabled = config.get("tools", {}).get("apollo", {}).get("enabled", True)
    brain_path = config.get("brain", {}).get("path", "brain")

    rows = read_batch_csv(input_file)
    click.echo(f"\nLoaded {len(rows)} accounts from {input_file}")

    if limit:
        rows = rows[:limit]
        click.echo(f"Limiting to first {limit} accounts (--limit)")

    brain_context = load_brain(brain_path)
    results = []
    processed = skipped_resume = skipped_threshold = errors = 0

    for i, row in enumerate(rows, 1):
        company = row["company"]
        domain = row["domain"]
        signal_type = row.get("signal_type", "manual")
        signal_date = row.get("signal_date") or None
        signal_source = row.get("signal_source", "manual")
        signal_summary = row.get("signal_summary", "")

        click.echo(f"\n[{i}/{len(rows)}] {company} ({domain})")

        summary = {
            "company": company,
            "domain": domain,
            "signal_type": signal_type,
            "signal_date": signal_date,
            "status": "pending",
            "error": "",
        }

        # Resume check
        if resume:
            existing = output_exists(domain, config)
            if existing:
                click.echo(f"  → skipped (output exists: {existing.name})")
                summary["status"] = "skipped_resume"
                summary["output_file"] = str(existing)
                results.append(summary)
                skipped_resume += 1
                continue

        try:
            # Step 1: Research
            click.echo(f"  Researching...")
            research = research_account(
                company=company,
                domain=domain,
                signal_type=signal_type,
                signal_date=signal_date,
                signal_summary=signal_summary,
                brain_context=brain_context,
            )
            summary["icp_verdict"] = research.get("icp_verdict", "?")
            summary["confidence"] = research.get("confidence", "?")
            click.echo(f"  ICP: {research.get('icp_verdict')} — {research.get('icp_reason', '')}")

            # Step 2: Score
            score = score_account(
                account=research,
                signal_type=signal_type,
                signal_date=signal_date,
                config=config,
            )
            summary.update({
                "icp_fit": score["icp_fit"],
                "signal_strength": score["signal_strength"],
                "priority": score["priority"],
                "action": score["action"],
            })
            click.echo(f"  Score: {score['icp_fit']}/5 × {score['signal_strength']}/3 = {score['priority']}  →  {score['action']}")

            # Threshold check
            if score["priority"] < threshold:
                click.echo(f"  → skipped (priority {score['priority']} < threshold {threshold})")
                summary["status"] = "skipped_threshold"
                results.append(summary)
                skipped_threshold += 1
                time.sleep(INTER_ACCOUNT_DELAY)
                continue

            output = {
                "company": company,
                "domain": domain,
                "signal": {
                    "type": signal_type,
                    "date": signal_date,
                    "source": signal_source,
                    "summary": signal_summary,
                },
                "research": research,
                "apollo_company": {},
                "contacts": [],
                "score": score,
                "outreach": {},
                "meta": {"run_date": date.today().isoformat(), "batch_input": input_file},
            }

            # Step 3: Apollo (optional)
            if not score_only and apollo_enabled:
                click.echo(f"  Enriching contacts via Apollo...")
                try:
                    apollo_co = enrich_company(domain)
                    output["apollo_company"] = apollo_co
                    contacts = find_contacts(domain, config=config)
                    output["contacts"] = contacts
                    summary["contacts_found"] = sum(1 for c in contacts if c.get("email"))
                    click.echo(f"  Found {summary['contacts_found']} contacts")
                    time.sleep(APOLLO_DELAY)
                except Exception as e:
                    click.echo(f"  Apollo failed: {e}", err=True)
                    summary["contacts_found"] = 0

            # Step 4: Outreach (optional)
            if not score_only and output["contacts"]:
                click.echo(f"  Generating outreach...")
                outreach_map = {}
                gen_count = 0
                for contact in output["contacts"]:
                    email = contact.get("email", "")
                    name = contact.get("name", "")
                    title = contact.get("title", "")
                    if not email or not name:
                        continue
                    try:
                        msg = generate_outreach(
                            research=research,
                            contact_name=name,
                            contact_title=title,
                            signal_type=signal_type,
                            signal_date=signal_date,
                            signal_summary=signal_summary,
                            brain_context=brain_context,
                        )
                        outreach_map[email] = msg
                        gen_count += 1
                    except Exception as e:
                        click.echo(f"  Outreach failed for {name}: {e}", err=True)
                output["outreach"] = outreach_map
                summary["outreach_generated"] = gen_count
                click.echo(f"  Generated {gen_count} outreach messages")

            # Save output
            out_file = output_path(domain, config)
            out_file.write_text(json.dumps(output, indent=2))
            summary["output_file"] = str(out_file)
            summary["status"] = "complete"
            processed += 1
            click.echo(f"  ✓ Saved: {out_file.name}")

        except Exception as e:
            click.echo(f"  ✗ Error: {e}", err=True)
            summary["status"] = "error"
            summary["error"] = str(e)
            errors += 1

        results.append(summary)
        time.sleep(INTER_ACCOUNT_DELAY)

    # Write summary
    summary_path = Path(input_file).with_suffix("") / Path(f"_summary_{date.today().isoformat()}.csv")
    summary_path = Path("output") / f"batch_summary_{date.today().isoformat()}.csv"
    write_summary(results, summary_path)

    click.echo(f"\n{'='*60}")
    click.echo(f"  Batch complete")
    click.echo(f"  Processed:        {processed}")
    click.echo(f"  Skipped (resume): {skipped_resume}")
    click.echo(f"  Skipped (score):  {skipped_threshold}")
    click.echo(f"  Errors:           {errors}")
    click.echo(f"  Summary CSV:      {summary_path}")
    click.echo(f"{'='*60}\n")
    click.echo(f"Next step: python scripts/export.py --push-to-hubspot")


@cli.command()
@click.option("--date", "run_date", default=None,
              help="Show summary for this date (YYYY-MM-DD, default: today)")
@click.option("--config", "config_path", default="config.yaml")
def summary(run_date, config_path):
    """Show summary of a completed batch run."""
    config = load_config(config_path)
    run_date = run_date or date.today().isoformat()
    summary_path = Path("output") / f"batch_summary_{run_date}.csv"

    if not summary_path.exists():
        click.echo(f"No batch summary found for {run_date}: {summary_path}")
        return

    with open(summary_path, newline="") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    complete = [r for r in rows if r["status"] == "complete"]
    immediate = [r for r in complete if int(r.get("priority") or 0) >= 12]
    this_week = [r for r in complete if 8 <= int(r.get("priority") or 0) < 12]

    click.echo(f"\nBatch summary for {run_date}")
    click.echo(f"  Total accounts:       {total}")
    click.echo(f"  Fully processed:      {len(complete)}")
    click.echo(f"  Reach out IMMEDIATELY:{len(immediate)}")
    click.echo(f"  Reach out this week:  {len(this_week)}")
    click.echo(f"\nTop priority accounts:")
    for r in sorted(complete, key=lambda x: int(x.get("priority") or 0), reverse=True)[:10]:
        click.echo(f"  [{r['priority']}/15] {r['company']} ({r['domain']}) — {r['action']}")


if __name__ == "__main__":
    cli()
