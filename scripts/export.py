"""
DeployGTM — Export to HubSpot Import CSV

Reads all JSON files from output/ and flattens them into two HubSpot-ready CSVs:
  - output/export_contacts_YYYY-MM-DD.csv   (one row per contact)
  - output/export_companies_YYYY-MM-DD.csv  (one row per company)

Both CSVs use HubSpot's standard import column names + DeployGTM custom properties.
Import companies first, then contacts.

Usage:
  # Export everything in output/
  python scripts/export.py run

  # Export only files from a specific date
  python scripts/export.py run --date 2024-03-15

  # Export and show what would be in each file without writing
  python scripts/export.py run --dry-run

  # Export and immediately push both CSVs to HubSpot via API
  python scripts/export.py run --push-to-hubspot
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import click
import yaml
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


# HubSpot column name mappings
COMPANY_FIELDS = [
    ("name",             "Company name"),
    ("domain",           "Company Domain Name"),
    ("industry",         "Industry"),
    ("employee_count",   "Number of Employees"),
    ("city",             "City"),
    ("state",            "State/Region"),
    ("linkedin_url",     "LinkedIn Company Page"),
    ("funding_stage",    "Recent Deal Amount"),    # closest HubSpot standard field
    ("signal_type",      "deploygtm_signal_type"),
    ("signal_date",      "deploygtm_signal_date"),
    ("signal_source",    "deploygtm_signal_source"),
    ("signal_summary",   "deploygtm_signal_summary"),
    ("icp_fit",          "deploygtm_icp_fit_score"),
    ("signal_strength",  "deploygtm_signal_strength"),
    ("priority",         "deploygtm_priority_score"),
    ("pain_hypothesis",  "deploygtm_pain_hypothesis"),
    ("confidence",       "deploygtm_enrichment_confidence"),
    ("icp_verdict",      "deploygtm_icp_verdict"),
    ("one_liner",        "Description"),
]

CONTACT_FIELDS = [
    ("email",            "Email"),
    ("first_name",       "First Name"),
    ("last_name",        "Last Name"),
    ("title",            "Job Title"),
    ("linkedin_url",     "LinkedIn Bio"),
    ("phone",            "Phone Number"),
    ("company_domain",   "Associated Company"),    # HubSpot uses domain to associate
    ("signal_type",      "deploygtm_signal_type"),
    ("signal_date",      "deploygtm_signal_date"),
    ("signal_source",    "deploygtm_signal_source"),
    ("signal_summary",   "deploygtm_signal_summary"),
    ("icp_fit",          "deploygtm_icp_fit_score"),
    ("signal_strength",  "deploygtm_signal_strength"),
    ("priority",         "deploygtm_priority_score"),
    ("pain_hypothesis",  "deploygtm_pain_hypothesis"),
    ("confidence",       "deploygtm_enrichment_confidence"),
    ("outreach_angle",   "deploygtm_outreach_angle"),
    ("email_subject",    "deploygtm_email_subject"),
    ("email_body",       "deploygtm_email_body"),
]


def load_output_files(output_dir: str = "output", filter_date: Optional[str] = None) -> list[dict]:
    """Load all pipeline JSON files from output/."""
    out_path = Path(output_dir)
    if not out_path.exists():
        return []

    files = sorted(out_path.glob("*.json"))
    # Exclude summary CSVs that got misnamed
    files = [f for f in files if not f.name.startswith("batch_summary")]

    if filter_date:
        files = [f for f in files if filter_date in f.name]

    results = []
    for f in files:
        try:
            data = json.loads(f.read_text())
            data["_source_file"] = str(f)
            results.append(data)
        except (json.JSONDecodeError, OSError) as e:
            click.echo(f"  Warning: could not read {f.name}: {e}", err=True)

    return results


def flatten_to_company_row(data: dict) -> dict:
    """Extract company fields from a pipeline output record."""
    research = data.get("research", {})
    apollo = data.get("apollo_company", {})
    signal = data.get("signal", {})
    score = data.get("score", {})

    # Prefer Apollo firmographic data for factual fields, research for context fields
    row = {
        "name": apollo.get("name") or research.get("company") or data.get("company", ""),
        "domain": data.get("domain", ""),
        "industry": apollo.get("industry", ""),
        "employee_count": apollo.get("employee_count") or research.get("employees_estimate", ""),
        "city": apollo.get("city", ""),
        "state": apollo.get("state", ""),
        "linkedin_url": apollo.get("linkedin_url") or research.get("linkedin_url", ""),
        "funding_stage": apollo.get("funding_stage") or research.get("funding_stage", ""),
        "signal_type": signal.get("type", ""),
        "signal_date": signal.get("date", ""),
        "signal_source": signal.get("source", ""),
        "signal_summary": signal.get("summary", ""),
        "icp_fit": score.get("icp_fit", ""),
        "signal_strength": score.get("signal_strength", ""),
        "priority": score.get("priority", ""),
        "pain_hypothesis": research.get("pain_hypothesis", ""),
        "confidence": research.get("confidence", ""),
        "icp_verdict": research.get("icp_verdict", ""),
        "one_liner": research.get("one_liner", ""),
    }
    return row


def flatten_to_contact_rows(data: dict) -> list[dict]:
    """Extract one row per contact from a pipeline output record."""
    contacts = data.get("contacts", [])
    signal = data.get("signal", {})
    score = data.get("score", {})
    research = data.get("research", {})
    outreach_map = data.get("outreach", {})
    domain = data.get("domain", "")

    rows = []
    for contact in contacts:
        email = contact.get("email", "")
        if not email:
            continue

        name_parts = (contact.get("name") or "").split()
        first = name_parts[0] if name_parts else ""
        last = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        outreach = outreach_map.get(email, {})
        primary = outreach.get("primary", {})

        row = {
            "email": email,
            "first_name": first,
            "last_name": last,
            "title": contact.get("title", ""),
            "linkedin_url": contact.get("linkedin_url", ""),
            "phone": contact.get("phone", ""),
            "company_domain": domain,
            "signal_type": signal.get("type", ""),
            "signal_date": signal.get("date", ""),
            "signal_source": signal.get("source", ""),
            "signal_summary": signal.get("summary", ""),
            "icp_fit": score.get("icp_fit", ""),
            "signal_strength": score.get("signal_strength", ""),
            "priority": score.get("priority", ""),
            "pain_hypothesis": research.get("pain_hypothesis", ""),
            "confidence": research.get("confidence", ""),
            "outreach_angle": outreach.get("persona", ""),
            "email_subject": primary.get("subject", ""),
            "email_body": primary.get("body", ""),
        }
        rows.append(row)

    return rows


def write_csv(rows: list[dict], field_map: list[tuple], path: Path):
    """Write rows to CSV using HubSpot column names."""
    hs_columns = [hs_name for _, hs_name in field_map]
    internal_keys = [key for key, _ in field_map]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=hs_columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            hs_row = {}
            for key, hs_name in zip(internal_keys, hs_columns):
                hs_row[hs_name] = str(row.get(key, "") or "")
            writer.writerow(hs_row)


# ─── CLI ──────────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """Export pipeline output to HubSpot import CSVs."""
    pass


@cli.command()
@click.option("--date", "filter_date", default=None,
              help="Only export files from this date (YYYY-MM-DD)")
@click.option("--min-priority", default=None, type=int,
              help="Only export accounts with priority >= this")
@click.option("--dry-run", is_flag=True, help="Print counts without writing files")
@click.option("--push-to-hubspot", is_flag=True,
              help="After exporting CSVs, push directly to HubSpot via API")
@click.option("--output-dir", default="output", help="Output directory")
@click.option("--config", "config_path", default="config.yaml")
def run(filter_date, min_priority, dry_run, push_to_hubspot, output_dir, config_path):
    """Export all pipeline output to HubSpot import CSVs."""
    config = load_config(config_path)
    today = date.today().isoformat()

    click.echo(f"\nLoading output files from {output_dir}/...")
    records = load_output_files(output_dir, filter_date)
    click.echo(f"Found {len(records)} pipeline records")

    if min_priority:
        records = [r for r in records if r.get("score", {}).get("priority", 0) >= min_priority]
        click.echo(f"Filtered to {len(records)} records with priority >= {min_priority}")

    if not records:
        click.echo("Nothing to export.")
        return

    # Build company rows (deduplicated by domain)
    seen_domains = set()
    company_rows = []
    for rec in records:
        domain = rec.get("domain", "")
        if domain and domain not in seen_domains:
            company_rows.append(flatten_to_company_row(rec))
            seen_domains.add(domain)

    # Build contact rows
    contact_rows = []
    for rec in records:
        contact_rows.extend(flatten_to_contact_rows(rec))

    click.echo(f"\n  Companies: {len(company_rows)}")
    click.echo(f"  Contacts:  {len(contact_rows)}")

    if dry_run:
        click.echo("\n[dry run] No files written.")
        # Preview first 3 companies
        click.echo("\nTop companies by priority:")
        sorted_cos = sorted(company_rows, key=lambda x: int(x.get("priority") or 0), reverse=True)
        for co in sorted_cos[:5]:
            click.echo(f"  [{co['priority']}/15] {co['name']} ({co['domain']}) — {co['icp_verdict']}")
        return

    out_path = Path(output_dir)
    companies_file = out_path / f"export_companies_{today}.csv"
    contacts_file  = out_path / f"export_contacts_{today}.csv"

    write_csv(company_rows, COMPANY_FIELDS, companies_file)
    write_csv(contact_rows, CONTACT_FIELDS, contacts_file)

    click.echo(f"\n  Companies CSV: {companies_file}")
    click.echo(f"  Contacts CSV:  {contacts_file}")
    click.echo(f"\nHubSpot import order:")
    click.echo(f"  1. Import {companies_file.name}  (Companies object)")
    click.echo(f"  2. Import {contacts_file.name}   (Contacts object, match on email)")

    if push_to_hubspot:
        click.echo("\nPushing to HubSpot via API...")
        from hubspot import push_pipeline_output
        hs_config = config.get("tools", {}).get("hubspot", {})
        if hs_config.get("require_confirmation", True):
            click.confirm(f"Push {len(records)} accounts to HubSpot?", abort=True)
        pushed = 0
        for rec in records:
            try:
                push_pipeline_output(rec, dry_run=False)
                pushed += 1
            except Exception as e:
                click.echo(f"  Error pushing {rec.get('domain')}: {e}", err=True)
        click.echo(f"  Pushed {pushed}/{len(records)} accounts.")


if __name__ == "__main__":
    cli()
