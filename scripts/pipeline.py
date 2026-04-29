"""
DeployGTM — Pipeline Orchestrator

The main entry point. Runs the full signal → research → enrich → score → outreach loop
for one account at a time, then saves the result to output/ for review before CRM push.

Usage:
  # Full pipeline — research, enrich, score, generate outreach
  python scripts/pipeline.py run \\
      --company "Acme" --domain "acme.com" \\
      --signal funding --signal-date 2024-03-15 \\
      --signal-summary "Raised $4M Seed led by a16z"

  # Dry run — skips nothing, but shows what HubSpot push would look like
  python scripts/pipeline.py run --company "Acme" --domain "acme.com" \\
      --signal hiring --signal-date 2024-03-10 --dry-run

  # Push saved output to HubSpot (requires explicit confirmation)
  python scripts/pipeline.py push --file output/acme_com_2024-03-15.json

  # Score-only — evaluate a company without researching it
  python scripts/pipeline.py score \\
      --company "Acme" --signal funding --signal-date 2024-03-15 \\
      --b2b-saas --seed-to-series-a --employees 12 --technical-buyer --us-based

  # Setup HubSpot custom properties (run once per account)
  python scripts/pipeline.py setup-hubspot
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import click
import yaml
from dotenv import load_dotenv

load_dotenv()

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent))

from research import research_account, load_brain
from apollo import find_contacts, enrich_company
from score import score_account
from outreach import generate_outreach, detect_persona
from hubspot import push_pipeline_output, setup_properties


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def output_path(domain: str, config: dict) -> Path:
    out_dir = Path(config.get("output", {}).get("path", "output"))
    out_dir.mkdir(exist_ok=True)
    filename = f"{domain.replace('.', '_')}_{date.today().isoformat()}.json"
    return out_dir / filename


# ─── run ──────────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """DeployGTM pipeline orchestrator."""
    pass


@cli.command()
@click.option("--company", "-c", required=True, help="Company name")
@click.option("--domain", "-d", required=True, help="Company domain (e.g. acme.com)")
@click.option("--signal", "-s", required=True,
              type=click.Choice(["funding", "hiring", "gtm_struggle", "agency_churn",
                                  "tool_adoption", "manual"]),
              help="Signal type that triggered this run")
@click.option("--signal-date", default=None, help="Signal date YYYY-MM-DD")
@click.option("--signal-source", default="manual",
              help="Where the signal came from (e.g. BirdDog, LinkedIn, Crunchbase)")
@click.option("--signal-summary", default="",
              help="Free-text description of the signal")
@click.option("--skip-apollo", is_flag=True,
              help="Skip Apollo enrichment (use if Apollo is disabled or rate-limited)")
@click.option("--skip-outreach", is_flag=True,
              help="Skip outreach generation (score and research only)")
@click.option("--push-to-hubspot", is_flag=True,
              help="Push to HubSpot immediately after pipeline (prompts for confirmation)")
@click.option("--dry-run", is_flag=True,
              help="Run everything but do not write to HubSpot")
@click.option("--config", "config_path", default="config.yaml")
def run(company, domain, signal, signal_date, signal_source, signal_summary,
        skip_apollo, skip_outreach, push_to_hubspot, dry_run, config_path):
    """Run the full enrichment pipeline for one account."""

    config = load_config(config_path)
    brain_path = config.get("brain", {}).get("path", "brain")

    click.echo(f"\n{'='*60}")
    click.echo(f"  DeployGTM Pipeline")
    click.echo(f"  {company} ({domain})")
    click.echo(f"  Signal: {signal} / {signal_date or 'no date'}")
    click.echo(f"{'='*60}\n")

    output = {
        "company": company,
        "domain": domain,
        "signal": {
            "type": signal,
            "date": signal_date,
            "source": signal_source,
            "summary": signal_summary,
        },
        "research": {},
        "apollo_company": {},
        "contacts": [],
        "score": {},
        "outreach": {},
        "meta": {
            "run_date": date.today().isoformat(),
            "config": config_path,
        },
    }

    # ── Step 1: Account Research (Claude) ──────────────────────────────────
    click.echo("Step 1/4: Researching account with Claude...")
    brain_context = load_brain(brain_path)
    try:
        research = research_account(
            company=company,
            domain=domain,
            signal_type=signal,
            signal_date=signal_date,
            signal_summary=signal_summary,
            brain_context=brain_context,
        )
        output["research"] = research
        click.echo(f"  ✓ {research.get('one_liner', 'Research complete')}")
        click.echo(f"  ICP verdict: {research.get('icp_verdict', '?')} — {research.get('icp_reason', '')}")
        click.echo(f"  Confidence: {research.get('confidence', '?')}")
    except Exception as e:
        click.echo(f"  ✗ Research failed: {e}", err=True)
        research = {}

    # ── Step 2: Scoring ────────────────────────────────────────────────────
    click.echo("\nStep 2/4: Scoring account...")
    score = score_account(
        account=research,
        signal_type=signal,
        signal_date=signal_date,
        config=config,
    )
    output["score"] = score

    click.echo(f"  ICP Fit:         {score['icp_fit']}/5")
    click.echo(f"  Signal Strength: {score['signal_strength']}/3")
    click.echo(f"  Priority:        {score['priority']}/15  →  {score['action']}")

    skip_threshold = config.get("scoring", {}).get("skip_below", 5)
    if score["priority"] < skip_threshold:
        click.echo(f"\n  ⚠  Priority {score['priority']} is below skip threshold ({skip_threshold}).")
        if not click.confirm("  Continue anyway?", default=False):
            click.echo("  Pipeline stopped. Account not saved.")
            return

    # ── Step 3: Contact Enrichment (Apollo) ────────────────────────────────
    apollo_enabled = config.get("tools", {}).get("apollo", {}).get("enabled", True)

    if not skip_apollo and apollo_enabled:
        click.echo("\nStep 3/4: Enriching contacts via Apollo...")
        try:
            apollo_co = enrich_company(domain)
            output["apollo_company"] = apollo_co
            click.echo(f"  Company: {apollo_co.get('name', domain)} "
                       f"({apollo_co.get('employee_count', '?')} employees, "
                       f"{apollo_co.get('funding_stage', '?')})")

            contacts = find_contacts(domain, config=config)
            output["contacts"] = contacts
            for c in contacts:
                status = "✓" if c.get("email_status") in ("verified", "likely") else "~"
                click.echo(f"  {status} {c.get('name', '?')} — {c.get('title', '?')} — {c.get('email', 'no email')}")
        except Exception as e:
            click.echo(f"  ✗ Apollo enrichment failed: {e}", err=True)
            click.echo("  Continuing without contact data. Add manually in HubSpot.")
    else:
        click.echo("\nStep 3/4: Apollo skipped (disabled or --skip-apollo set).")
        click.echo("  Add contacts manually via HubSpot or Apollo dashboard.")

    # ── Step 4: Outreach Generation ────────────────────────────────────────
    if not skip_outreach and output["contacts"]:
        click.echo("\nStep 4/4: Generating outreach...")
        outreach_map = {}

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
                    signal_type=signal,
                    signal_date=signal_date,
                    signal_summary=signal_summary,
                    brain_context=brain_context,
                )
                outreach_map[email] = msg
                click.echo(f"\n  → {name} ({title})  [{msg.get('persona', '?')}]")
                click.echo(f"     Subject: {msg.get('primary', {}).get('subject', '')}")
                click.echo(f"     Preview: {str(msg.get('primary', {}).get('body', ''))[:120]}...")
            except Exception as e:
                click.echo(f"  ✗ Outreach failed for {name}: {e}", err=True)

        output["outreach"] = outreach_map
    elif skip_outreach:
        click.echo("\nStep 4/4: Outreach generation skipped (--skip-outreach).")
    else:
        click.echo("\nStep 4/4: No contacts found — skipping outreach generation.")

    # ── Save output ────────────────────────────────────────────────────────
    out_file = output_path(domain, config)
    out_file.write_text(json.dumps(output, indent=2))
    click.echo(f"\n{'─'*60}")
    click.echo(f"Saved to: {out_file}")
    click.echo(f"{'─'*60}\n")

    # ── Optional: Push to HubSpot ──────────────────────────────────────────
    if push_to_hubspot and not dry_run:
        click.echo("Pushing to HubSpot...")
        hs_config = config.get("tools", {}).get("hubspot", {})
        if hs_config.get("require_confirmation", True):
            click.confirm("Confirm push to production CRM?", abort=True)
        push_pipeline_output(output, dry_run=False)
        click.echo("HubSpot push complete.\n")
    elif dry_run:
        click.echo("[Dry run] Simulating HubSpot push...")
        push_pipeline_output(output, dry_run=True)
    else:
        click.echo(f"To push to HubSpot:\n  python scripts/pipeline.py push --file {out_file}\n")


# ─── push ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--file", "-f", "input_file", required=True,
              help="Path to JSON file from pipeline run")
@click.option("--dry-run", is_flag=True)
@click.option("--config", "config_path", default="config.yaml")
def push(input_file, dry_run, config_path):
    """Push a saved pipeline output to HubSpot CRM."""
    config = load_config(config_path)

    if not dry_run and config.get("tools", {}).get("hubspot", {}).get("require_confirmation", True):
        click.echo(f"\nAbout to push to HubSpot CRM: {input_file}")
        click.confirm("Confirm?", abort=True)

    data = json.loads(Path(input_file).read_text())
    results = push_pipeline_output(data, dry_run=dry_run)

    click.echo(f"\nPush {'(dry run) ' if dry_run else ''}complete.")
    click.echo(f"  Company: {results['company_id']}")
    click.echo(f"  Contacts: {results['contact_ids']}")


# ─── score-only ───────────────────────────────────────────────────────────────

@cli.command("score")
@click.option("--company", "-c", required=True)
@click.option("--domain", "-d", default="", help="Optional domain for no-write score smoke tests")
@click.option("--signal", "-s", required=True,
              type=click.Choice(["funding", "hiring", "gtm_struggle", "agency_churn",
                                  "tool_adoption", "manual"]))
@click.option("--signal-date", default=None)
@click.option("--signal-summary", default="", help="Optional signal summary for no-write score smoke tests")
@click.option("--b2b-saas/--no-b2b-saas", default=False)
@click.option("--seed-to-series-a/--no-seed-to-series-a", default=False)
@click.option("--employees", default=None, type=int, help="Headcount (auto-maps to employees_5_30)")
@click.option("--technical-buyer/--no-technical-buyer", default=False)
@click.option("--us-based/--no-us-based", default=False)
@click.option("--needs-pipeline/--no-needs-pipeline", default=False)
@click.option("--hubspot-or-open/--no-hubspot-or-open", default=False)
@click.option("--config", "config_path", default="config.yaml")
def score_cmd(company, domain, signal, signal_date, signal_summary, b2b_saas, seed_to_series_a,
              employees, technical_buyer, us_based, needs_pipeline,
              hubspot_or_open, config_path):
    """Quick score for an account without running the full pipeline."""
    config = load_config(config_path)

    account = {
        "b2b_saas": b2b_saas,
        "seed_to_series_a": seed_to_series_a,
        "employees": employees,
        "technical_buyer": technical_buyer,
        "us_based": us_based,
        "needs_pipeline": needs_pipeline,
        "hubspot_or_open": hubspot_or_open,
        "signal_summary": signal_summary,
    }

    result = score_account(account, signal, signal_date, config)

    label = f"{company} ({domain})" if domain else company
    click.echo(f"\n  {label}")
    click.echo(f"  ICP Fit:         {result['icp_fit']}/5")
    click.echo(f"  Signal Strength: {result['signal_strength']}/3")
    click.echo(f"  Priority:        {result['priority']}/15")
    click.echo(f"  Action:          {result['action']}")
    click.echo(f"\n  {result['signal_rationale']}")
    for r in result["icp_rationale"]:
        click.echo(f"    {r}")


# ─── setup-hubspot ────────────────────────────────────────────────────────────

@cli.command("setup-hubspot")
@click.option("--dry-run", is_flag=True)
def setup_hubspot(dry_run):
    """Create all DeployGTM custom properties in HubSpot (run once)."""
    if not dry_run:
        click.echo("\n⚠️  This creates custom contact properties in your HubSpot account.")
        click.confirm("Continue?", abort=True)
    setup_properties(dry_run=dry_run)


# ─── new-client ───────────────────────────────────────────────────────────────

@cli.command("new-client")
@click.option("--client", "-c", required=True,
              help="Client slug (lowercase, hyphens, e.g. acme-corp)")
@click.option("--domain", "-d", required=True, help="Client domain (e.g. acme.com)")
def new_client(client, domain):
    """
    Create a new client project + brain stubs. Shortcut for signal_audit.py new.

    Sets up:
      projects/<client>/context.md, handoff.md, open-loops.md, targets.csv
      brain/clients/<client>/icp.md, personas.md, messaging.md
    """
    import subprocess
    result = subprocess.run([
        sys.executable, "scripts/signal_audit.py", "new",
        "--client", client,
        "--domain", domain,
    ], check=False)
    sys.exit(result.returncode)


if __name__ == "__main__":
    cli()
