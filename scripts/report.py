"""
DeployGTM — Weekly Signal & Pipeline Report

Generates a clean markdown report from pipeline output files.
Used for: DeployGTM's own weekly review + client retainer weekly reports.

What it covers:
  - Signals processed this week, broken down by type
  - Priority account leaderboard (top accounts by score)
  - Outreach sent vs. pending
  - ICP verdict breakdown
  - Open loops / accounts needing follow-up
  - Recommended next actions

Can optionally pull live pipeline stage data from HubSpot to show
which accounts have replied, booked, or converted.

Usage:
  # Report from all output/ files (last 7 days by default)
  python scripts/report.py generate

  # Report for a specific date range
  python scripts/report.py generate --since 2026-04-01 --until 2026-04-17

  # Report for a specific client project
  python scripts/report.py generate --project deploygtm-own

  # Include live HubSpot stage data
  python scripts/report.py generate --include-hubspot

  # Save to a specific file
  python scripts/report.py generate --output output/week_of_2026-04-14.md
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import click
import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

HS_BASE = "https://api.hubapi.com"


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_output_files(
    output_dir: str = "output",
    since: Optional[str] = None,
    until: Optional[str] = None,
    project_filter: Optional[str] = None,
) -> list[dict]:
    """Load pipeline JSON files filtered by date range and optional project."""
    out_path = Path(output_dir)
    if not out_path.exists():
        return []

    files = sorted(out_path.glob("*.json"))
    records = []

    for f in files:
        # Filter by date in filename (format: domain_YYYY-MM-DD.json)
        parts = f.stem.rsplit("_", 3)
        if len(parts) >= 1:
            # Last part should be YYYY-MM-DD
            try:
                file_date = parts[-1]
                datetime.strptime(file_date, "%Y-%m-%d")
                if since and file_date < since:
                    continue
                if until and file_date > until:
                    continue
            except ValueError:
                pass  # filename doesn't have date, include it

        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        # Project filter: match on batch_input path or domain
        if project_filter:
            meta = data.get("meta", {})
            batch_input = meta.get("batch_input", "")
            if project_filter not in batch_input and project_filter not in data.get("domain", ""):
                continue

        data["_filename"] = f.name
        records.append(data)

    return records


def fetch_hubspot_stages(domains: list[str]) -> dict[str, str]:
    """
    Pull lifecycle stage + last activity for each domain from HubSpot.
    Returns {domain: stage_label}.
    """
    token = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")
    if not token:
        return {}

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    stage_map = {}

    for domain in domains:
        try:
            resp = requests.post(
                f"{HS_BASE}/crm/v3/objects/companies/search",
                headers=headers,
                json={
                    "filterGroups": [{"filters": [
                        {"propertyName": "domain", "operator": "EQ", "value": domain}
                    ]}],
                    "properties": ["name", "lifecyclestage", "hs_last_activity_date"],
                    "limit": 1,
                },
                timeout=10,
            )
            results = resp.json().get("results", [])
            if results:
                props = results[0].get("properties", {})
                stage_map[domain] = props.get("lifecyclestage", "unknown")
        except requests.RequestException:
            pass

    return stage_map


def build_report(
    records: list[dict],
    since: str,
    until: str,
    hs_stages: dict[str, str],
    project: Optional[str] = None,
) -> str:
    """Build the full markdown report string."""

    lines = []

    # ── Header ──────────────────────────────────────────────────────────────
    title = f"DeployGTM — Weekly Signal Report"
    if project:
        title += f" · {project}"
    lines += [
        f"# {title}",
        f"**Period:** {since} → {until}",
        f"**Generated:** {date.today().isoformat()}",
        f"**Accounts reviewed:** {len(records)}",
        "",
    ]

    if not records:
        lines.append("_No pipeline records found for this period._")
        return "\n".join(lines)

    # ── Signal breakdown ─────────────────────────────────────────────────────
    signal_counts = Counter(r.get("signal", {}).get("type", "unknown") for r in records)
    lines += ["## Signals this week", ""]
    for sig_type, count in signal_counts.most_common():
        lines.append(f"- **{sig_type}**: {count} account{'s' if count != 1 else ''}")
    lines.append("")

    # ── Priority leaderboard ─────────────────────────────────────────────────
    scored = [r for r in records if r.get("score", {}).get("priority")]
    scored.sort(key=lambda r: r["score"]["priority"], reverse=True)

    immediate = [r for r in scored if r["score"]["priority"] >= 12]
    this_week = [r for r in scored if 8 <= r["score"]["priority"] < 12]
    nurture    = [r for r in scored if 5 <= r["score"]["priority"] < 8]
    skipped    = [r for r in records if r.get("score", {}).get("priority", 0) < 5]

    lines += ["## Priority breakdown", ""]
    lines.append(f"| Tier | Count |")
    lines.append(f"|------|-------|")
    lines.append(f"| 🔴 Reach out immediately (≥12) | {len(immediate)} |")
    lines.append(f"| 🟡 This week (8–11) | {len(this_week)} |")
    lines.append(f"| 🟢 Nurture (5–7) | {len(nurture)} |")
    lines.append(f"| ⚪ Skipped (<5) | {len(skipped)} |")
    lines.append("")

    # ── Top accounts ─────────────────────────────────────────────────────────
    top = scored[:15]
    if top:
        lines += ["## Top accounts by priority", ""]
        lines.append("| Priority | Company | Domain | Signal | ICP | Contacts | HubSpot Stage |")
        lines.append("|----------|---------|--------|--------|-----|----------|---------------|")
        for r in top:
            sc = r.get("score", {})
            sig = r.get("signal", {})
            research = r.get("research", {})
            contacts = [c for c in r.get("contacts", []) if c.get("email")]
            domain = r.get("domain", "")
            stage = hs_stages.get(domain, "—")
            lines.append(
                f"| {sc.get('priority', '?')}/15 "
                f"| {r.get('company', '?')} "
                f"| {domain} "
                f"| {sig.get('type', '?')} "
                f"| {research.get('icp_verdict', '?')} "
                f"| {len(contacts)} "
                f"| {stage} |"
            )
        lines.append("")

    # ── Outreach status ──────────────────────────────────────────────────────
    with_outreach = [r for r in records if r.get("outreach")]
    without_outreach = [r for r in scored if not r.get("outreach") and r["score"]["priority"] >= 8]

    lines += ["## Outreach", ""]
    lines.append(f"- Outreach generated: **{len(with_outreach)}** accounts")
    if without_outreach:
        lines.append(f"- Priority accounts missing outreach: **{len(without_outreach)}**")
        for r in without_outreach[:5]:
            lines.append(f"  - {r.get('company')} ({r.get('domain')}) — priority {r['score']['priority']}/15")
    lines.append("")

    # ── ICP verdict breakdown ─────────────────────────────────────────────────
    verdicts = Counter(r.get("research", {}).get("icp_verdict", "unknown") for r in records)
    lines += ["## ICP verdicts", ""]
    for verdict, count in [("yes", verdicts.get("yes", 0)),
                            ("maybe", verdicts.get("maybe", 0)),
                            ("no", verdicts.get("no", 0))]:
        if count:
            lines.append(f"- **{verdict}**: {count}")
    lines.append("")

    # ── Confidence distribution ──────────────────────────────────────────────
    confidences = Counter(r.get("research", {}).get("confidence", "unknown") for r in records)
    low_conf = [r for r in records if r.get("research", {}).get("confidence") == "low"
                and r.get("score", {}).get("priority", 0) >= 8]
    if low_conf:
        lines += ["## Low-confidence accounts needing verification", ""]
        lines.append("_These scored high but Claude flagged low confidence — verify before outreach:_")
        lines.append("")
        for r in low_conf[:8]:
            conf_notes = r.get("research", {}).get("confidence_notes", "")
            lines.append(f"- **{r.get('company')}** ({r.get('domain')}): {conf_notes}")
        lines.append("")

    # ── Accounts needing follow-up (HubSpot data) ────────────────────────────
    if hs_stages:
        replied = {d: s for d, s in hs_stages.items() if s in ("lead", "opportunity", "customer")}
        if replied:
            lines += ["## HubSpot — Active pipeline", ""]
            for domain, stage in replied.items():
                matching = next((r for r in records if r.get("domain") == domain), None)
                name = matching.get("company", domain) if matching else domain
                lines.append(f"- **{name}** ({domain}): {stage}")
            lines.append("")

    # ── Next actions ─────────────────────────────────────────────────────────
    lines += ["## Recommended next actions", ""]
    action_num = 1

    if immediate:
        lines.append(f"{action_num}. **Send outreach to {len(immediate)} immediate-priority accounts** — "
                     f"these have active signals and strong ICP fit")
        action_num += 1

    if without_outreach:
        lines.append(f"{action_num}. **Generate outreach for {len(without_outreach)} priority accounts** "
                     f"missing messages — run `python scripts/pipeline.py run` for each")
        action_num += 1

    if low_conf:
        lines.append(f"{action_num}. **Manually verify {len(low_conf)} low-confidence accounts** "
                     f"before outreach — LinkedIn + website check")
        action_num += 1

    if len(skipped) > 5:
        lines.append(f"{action_num}. **Review {len(skipped)} skipped accounts** — "
                     f"some may have updated signals worth re-evaluating")
        action_num += 1

    lines += [
        "",
        "---",
        f"_Report generated by DeployGTM pipeline · {len(records)} accounts · {date.today().isoformat()}_",
    ]

    return "\n".join(lines)


# ─── CLI ──────────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """Weekly signal and pipeline report generator."""
    pass


@cli.command()
@click.option("--since", default=None,
              help="Start date YYYY-MM-DD (default: 7 days ago)")
@click.option("--until", default=None,
              help="End date YYYY-MM-DD (default: today)")
@click.option("--project", "-p", default=None,
              help="Filter to records from a specific project batch")
@click.option("--include-hubspot", is_flag=True,
              help="Pull live pipeline stage data from HubSpot")
@click.option("--output", "-o", default=None,
              help="Save report to file (default: print to stdout)")
@click.option("--output-dir", default="output")
@click.option("--config", "config_path", default="config.yaml")
def generate(since, until, project, include_hubspot, output, output_dir, config_path):
    """Generate a weekly signal and pipeline report."""
    today = date.today().isoformat()
    since = since or (date.today() - timedelta(days=7)).isoformat()
    until = until or today

    click.echo(f"Generating report: {since} → {until}", err=True)

    records = load_output_files(output_dir, since=since, until=until, project_filter=project)
    click.echo(f"Loaded {len(records)} pipeline records", err=True)

    hs_stages = {}
    if include_hubspot and os.environ.get("HUBSPOT_ACCESS_TOKEN"):
        click.echo("Fetching HubSpot stage data...", err=True)
        domains = [r.get("domain", "") for r in records if r.get("domain")]
        hs_stages = fetch_hubspot_stages(domains)

    report = build_report(records, since=since, until=until, hs_stages=hs_stages, project=project)

    if output:
        out_path = Path(output)
    else:
        out_path = Path(output_dir) / f"weekly_report_{today}.md"

    out_path.write_text(report)
    click.echo(f"Report saved: {out_path}", err=True)

    # Also print to stdout so it can be piped / read
    click.echo(report)


if __name__ == "__main__":
    cli()
