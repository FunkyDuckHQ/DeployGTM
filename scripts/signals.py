"""
DeployGTM — Signal Detection (BirdDog-free)

Finds buying signals from free/owned sources and writes them to
signals_intake.csv for the batch pipeline to process.

Sources:
  apollo-hiring   Companies posting SDR/BDR/AE/VP Sales roles (Apollo API)
  apollo-funded   Companies that recently raised Seed or Series A (Apollo API)
  yc-batch        YC batch companies from the public YC directory
  merge           Deduplicate and merge multiple signal files into one

Usage:
  # Find companies hiring sales roles → add to signals file
  python scripts/signals.py apollo-hiring --output data/signals_intake.csv

  # Find recently funded B2B SaaS companies
  python scripts/signals.py apollo-funded --days 90 --output data/signals_intake.csv

  # Fetch YC W26 companies and save as batch targets
  python scripts/signals.py yc-batch --batch W26 --output data/yc_w26_targets.csv

  # Merge signals from multiple files (deduplicates by domain)
  python scripts/signals.py merge \
      --input data/signals_intake.csv \
      --input data/yc_w26_targets.csv \
      --output data/all_signals.csv

  # Full run: pull all sources and merge
  python scripts/signals.py all --output data/signals_intake.csv
"""

from __future__ import annotations

import csv
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import click
import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))
from apollo import _apollo_post, _apollo_key  # reuse retry logic

APOLLO_BASE = "https://api.apollo.io/v1"
YC_API_BASE = "https://www.ycombinator.com"


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def read_existing_domains(csv_path: str) -> set[str]:
    """Return set of domains already in a signals CSV to avoid duplicates."""
    p = Path(csv_path)
    if not p.exists():
        return set()
    with open(p, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row.get("domain", "").strip().lower() for row in reader if row.get("domain")}


def append_signals(signals: list[dict], output_path: str, dedupe: bool = True):
    """Append signal rows to a CSV, skipping domains already present."""
    out = Path(output_path)
    fieldnames = ["company", "domain", "signal_type", "signal_date", "signal_source", "signal_summary"]

    existing_domains = read_existing_domains(output_path) if dedupe else set()
    new_rows = [s for s in signals if s.get("domain", "").lower() not in existing_domains]

    if not new_rows:
        click.echo(f"  No new signals to add (all domains already present in {output_path})")
        return 0

    write_header = not out.exists() or out.stat().st_size == 0
    with open(out, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(new_rows)

    return len(new_rows)


# ─── Apollo: Hiring signals ───────────────────────────────────────────────────

SALES_TITLES = [
    "VP Sales", "VP of Sales", "Head of Sales",
    "Account Executive", "AE",
    "SDR", "Sales Development Representative",
    "BDR", "Business Development Representative",
    "VP Revenue", "Chief Revenue Officer", "CRO",
    "Head of Revenue", "Revenue Operations",
]

ICP_FUNDING_STAGES = ["seed", "series_a"]
ICP_EMPLOYEE_RANGES = ["1,10", "11,20", "21,50"]


def apollo_hiring_signals(
    max_companies: int = 50,
    config: Optional[dict] = None,
) -> list[dict]:
    """
    Find B2B SaaS companies (Seed/A, 5–30 employees) that are actively
    hiring for sales roles via Apollo's organization search.
    """
    api_key = _apollo_key()
    today = date.today().isoformat()
    found = {}  # domain → signal dict

    for title in SALES_TITLES[:6]:  # Top 6 most signal-rich titles
        if len(found) >= max_companies:
            break

        payload = {
            "api_key": api_key,
            "page": 1,
            "per_page": 25,
            "organization_latest_funding_stage_cd": [0, 1],  # Seed, Series A
            "organization_num_employees_ranges": ICP_EMPLOYEE_RANGES,
            "organization_locations": ["United States"],
            "q_organization_keyword_tags": ["saas", "b2b"],
            "person_titles": [title],
            "contact_email_status_v2": ["verified", "likely"],
        }

        try:
            data = _apollo_post("mixed_people/search", payload, timeout=20)
        except requests.RequestException as e:
            click.echo(f"  Apollo hiring search error for '{title}': {e}", err=True)
            continue

        for person in data.get("people", []):
            org = person.get("organization") or {}
            domain = (org.get("primary_domain") or org.get("website_url") or "").lower()
            if not domain or domain in found:
                continue

            # Clean domain
            domain = domain.replace("https://", "").replace("http://", "").split("/")[0].strip()
            if not domain or "." not in domain:
                continue

            company = org.get("name", "")
            stage = org.get("latest_funding_stage", "").lower()
            employees = org.get("estimated_num_employees", 0) or 0

            # Tighter ICP filter
            if employees > 50:
                continue

            signal_summary = (
                f"Hiring for {title} at {company} "
                f"({stage}, ~{employees} employees, US-based)"
            )

            found[domain] = {
                "company": company,
                "domain": domain,
                "signal_type": "hiring",
                "signal_date": today,
                "signal_source": "Apollo",
                "signal_summary": signal_summary,
            }

        time.sleep(0.8)

    return list(found.values())


# ─── Apollo: Funding signals ──────────────────────────────────────────────────

def apollo_funded_signals(
    days_back: int = 90,
    max_companies: int = 50,
) -> list[dict]:
    """
    Find B2B SaaS companies that raised Seed or Series A within the last N days.
    """
    api_key = _apollo_key()
    today = date.today()
    cutoff = (today - timedelta(days=days_back)).isoformat()
    found = {}

    payload = {
        "api_key": api_key,
        "page": 1,
        "per_page": 50,
        "organization_latest_funding_stage_cd": [0, 1],
        "organization_num_employees_ranges": ICP_EMPLOYEE_RANGES,
        "organization_locations": ["United States"],
        "q_organization_keyword_tags": ["saas", "b2b"],
        "organization_latest_funding_date_range": {
            "min": cutoff,
            "max": today.isoformat(),
        },
    }

    try:
        data = _apollo_post("organizations/search", payload, timeout=20)
    except requests.RequestException as e:
        click.echo(f"  Apollo funding search error: {e}", err=True)
        return []

    for org in data.get("organizations", []):
        domain = (org.get("primary_domain") or org.get("website_url") or "").lower()
        domain = domain.replace("https://", "").replace("http://", "").split("/")[0].strip()
        if not domain or "." not in domain or domain in found:
            continue

        stage = org.get("latest_funding_stage", "").lower()
        amount = org.get("latest_funding_amount")
        funding_date = (org.get("latest_funding_date") or today.isoformat())[:10]
        employees = org.get("estimated_num_employees", 0) or 0

        if employees > 50:
            continue

        amount_str = f"${amount:,}" if amount else "undisclosed amount"
        found[domain] = {
            "company": org.get("name", ""),
            "domain": domain,
            "signal_type": "funding",
            "signal_date": funding_date,
            "signal_source": "Apollo",
            "signal_summary": f"Raised {amount_str} ({stage}) — {employees} employees, US-based",
        }

    return list(found.values())


# ─── YC Batch ─────────────────────────────────────────────────────────────────

def yc_batch_companies(batch: str = "W26", industry_filter: str = "b2b") -> list[dict]:
    """
    Fetch YC batch companies from the public YC directory.
    Returns companies matching ICP (B2B SaaS).
    """
    today = date.today().isoformat()
    results = []

    # YC's public companies API
    url = f"{YC_API_BASE}/companies"
    params = {"batch": batch}

    try:
        resp = requests.get(url, params=params, timeout=20,
                            headers={"User-Agent": "Mozilla/5.0 (compatible; research)"})

        if resp.status_code != 200:
            # Try alternate endpoint format
            resp = requests.get(
                f"https://api.ycombinator.com/v0.1/companies",
                params={"batch": batch, "industry": "B2B"},
                timeout=20,
            )

        if resp.status_code == 200:
            ct = resp.headers.get("content-type", "")
            if "json" in ct:
                data = resp.json()
                companies = data if isinstance(data, list) else data.get("companies", [])

                for co in companies:
                    name = co.get("name") or co.get("company_name", "")
                    domain = (co.get("url") or co.get("website") or "").lower()
                    domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
                    if not domain or not name:
                        continue

                    # Filter for B2B SaaS
                    tags = " ".join([
                        str(co.get("tags") or ""),
                        str(co.get("industries") or ""),
                        str(co.get("description") or ""),
                    ]).lower()

                    if "b2c" in tags or "consumer" in tags:
                        continue
                    if industry_filter and industry_filter.lower() not in tags:
                        continue

                    results.append({
                        "company": name,
                        "domain": domain,
                        "signal_type": "funding",
                        "signal_date": today,
                        "signal_source": f"YC {batch}",
                        "signal_summary": (
                            f"YC {batch} company — just completed Demo Day, "
                            f"raised Seed round. {(co.get('one_liner') or '')[:120]}"
                        ),
                    })
            else:
                # HTML response — YC may require JS rendering
                click.echo(
                    f"  YC returned HTML (likely requires browser). "
                    f"Try manually exporting from ycombinator.com/companies?batch={batch}",
                    err=True,
                )
        else:
            click.echo(f"  YC directory returned {resp.status_code}", err=True)

    except requests.RequestException as e:
        click.echo(f"  Could not fetch YC directory: {e}", err=True)

    # If API failed, return empty with helpful instructions
    if not results:
        _write_yc_instructions(batch)

    return results


def _write_yc_instructions(batch: str):
    """Write instructions for manually populating the YC target list."""
    instructions = Path(f"data/yc_{batch.lower()}_instructions.md")
    instructions.write_text(f"""# How to populate data/yc_{batch.lower()}_targets.csv

## Manual approach (most reliable)

1. Go to: https://www.ycombinator.com/companies?batch={batch}
2. Filter: Industry = "B2B Software and Services"
3. Export or copy company names and domains
4. Add rows to data/yc_{batch.lower()}_targets.csv:
   company,domain,signal_type,signal_date,signal_source,signal_summary

## Signal type for all YC {batch} companies
signal_type: funding
signal_date: [Demo Day date]
signal_source: YC {batch}
signal_summary: YC {batch} — just raised Seed, need GTM infrastructure

## Why these are high priority
YC {batch} companies just raised at Demo Day. They have:
- Fresh capital to spend on GTM
- Pressure from investors to show traction
- No pipeline infrastructure yet
- Founders doing sales themselves

ICP Fit: 5/5. Signal Strength: 3/3. Priority: 15/15.
These are the warmest possible cold outreach targets.

## Alternative: Use Fundraise Insider or Growth List
- https://fundraiseinsider.com (tracks Seed/A closes)
- Growth List newsletter
- Crunchbase Pro → filter by funding date + stage + employee count
""")
    click.echo(f"  Instructions saved: {instructions}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """Free signal detection — feeds data/signals_intake.csv."""
    pass


@cli.command("apollo-hiring")
@click.option("--max-companies", default=50, type=int)
@click.option("--output", "-o", default="data/signals_intake.csv")
@click.option("--no-dedupe", is_flag=True, help="Don't skip domains already in output file")
def cmd_hiring(max_companies, output, no_dedupe):
    """Find B2B SaaS companies posting sales roles via Apollo."""
    click.echo(f"\nSearching Apollo for companies hiring sales roles...")

    try:
        signals = apollo_hiring_signals(max_companies=max_companies)
    except EnvironmentError as e:
        click.echo(f"Error: {e}", err=True)
        return

    click.echo(f"Found {len(signals)} companies with hiring signals")
    for s in signals[:5]:
        click.echo(f"  {s['company']} ({s['domain']}) — {s['signal_summary'][:60]}...")

    added = append_signals(signals, output, dedupe=not no_dedupe)
    click.echo(f"\nAdded {added} new signals to {output}")
    click.echo(f"Next: python scripts/batch.py run --input {output}")


@cli.command("apollo-funded")
@click.option("--days", default=90, type=int, help="Look back N days for funding events")
@click.option("--max-companies", default=50, type=int)
@click.option("--output", "-o", default="data/signals_intake.csv")
@click.option("--no-dedupe", is_flag=True)
def cmd_funded(days, max_companies, output, no_dedupe):
    """Find B2B SaaS companies that recently raised Seed or Series A via Apollo."""
    click.echo(f"\nSearching Apollo for companies funded in last {days} days...")

    try:
        signals = apollo_funded_signals(days_back=days, max_companies=max_companies)
    except EnvironmentError as e:
        click.echo(f"Error: {e}", err=True)
        return

    click.echo(f"Found {len(signals)} recently funded companies")
    for s in signals[:5]:
        click.echo(f"  {s['company']} ({s['domain']}) — {s['signal_summary'][:60]}...")

    added = append_signals(signals, output, dedupe=not no_dedupe)
    click.echo(f"\nAdded {added} new signals to {output}")


@cli.command("yc-batch")
@click.option("--batch", "-b", default="W26", help="YC batch code (e.g. W26, S25)")
@click.option("--output", "-o", default=None, help="Output CSV (default: data/yc_<batch>.csv)")
@click.option("--no-dedupe", is_flag=True)
def cmd_yc(batch, output, no_dedupe):
    """Fetch YC batch companies from the public YC directory."""
    output = output or f"data/yc_{batch.lower()}_targets.csv"
    click.echo(f"\nFetching YC {batch} companies...")

    signals = yc_batch_companies(batch=batch)

    if signals:
        click.echo(f"Found {len(signals)} B2B companies from YC {batch}")
        for s in signals[:5]:
            click.echo(f"  {s['company']} ({s['domain']})")
        added = append_signals(signals, output, dedupe=not no_dedupe)
        click.echo(f"\nAdded {added} companies to {output}")
    else:
        click.echo(f"Could not fetch automatically — check data/yc_{batch.lower()}_instructions.md")

    click.echo(f"\nNext: python scripts/batch.py run --input {output}")


@cli.command("merge")
@click.option("--input", "-i", "inputs", multiple=True, required=True,
              help="Input CSV files (use multiple times)")
@click.option("--output", "-o", required=True, help="Output merged CSV")
def cmd_merge(inputs, output):
    """Merge multiple signal CSVs, deduplicating by domain."""
    fieldnames = ["company", "domain", "signal_type", "signal_date", "signal_source", "signal_summary"]
    seen = set()
    all_rows = []

    for inp in inputs:
        p = Path(inp)
        if not p.exists():
            click.echo(f"  Skipping (not found): {inp}", err=True)
            continue
        with open(p, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                domain = row.get("domain", "").strip().lower()
                if domain and domain not in seen:
                    seen.add(domain)
                    all_rows.append(row)

    out = Path(output)
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    click.echo(f"\nMerged {len(all_rows)} unique companies → {output}")


@cli.command("all")
@click.option("--output", "-o", default="data/signals_intake.csv")
@click.option("--days", default=90, type=int, help="Days back for funding signals")
@click.option("--config", "config_path", default="config.yaml")
def cmd_all(output, days, config_path):
    """Pull signals from all Apollo sources and merge into one file."""
    click.echo(f"\nRunning all signal sources...")

    all_signals = []

    click.echo("\n1/2: Hiring signals...")
    try:
        hiring = apollo_hiring_signals(max_companies=50)
        click.echo(f"     {len(hiring)} hiring signals")
        all_signals.extend(hiring)
    except EnvironmentError as e:
        click.echo(f"     Skipped: {e}", err=True)

    time.sleep(1)

    click.echo("\n2/2: Funding signals...")
    try:
        funded = apollo_funded_signals(days_back=days, max_companies=50)
        click.echo(f"     {len(funded)} funding signals")
        all_signals.extend(funded)
    except EnvironmentError as e:
        click.echo(f"     Skipped: {e}", err=True)

    # Deduplicate
    seen = set()
    deduped = []
    for s in all_signals:
        d = s.get("domain", "").lower()
        if d and d not in seen:
            seen.add(d)
            deduped.append(s)

    added = append_signals(deduped, output)
    click.echo(f"\n{'='*50}")
    click.echo(f"Total unique signals found: {len(deduped)}")
    click.echo(f"New signals added to {output}: {added}")
    click.echo(f"\nNext:")
    click.echo(f"  python scripts/batch.py run --input {output}")
    click.echo(f"  python scripts/report.py generate")


if __name__ == "__main__":
    cli()
