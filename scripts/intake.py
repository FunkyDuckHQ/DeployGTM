"""
DeployGTM — Intake

"I'm working with XYZ company."

One command. Automatic from there:
  1. Look up company + auto-detect signals (Apollo)
  2. Research with Claude (product, ICP fit, pain hypothesis)
  3. Score: ICP Fit × Signal Strength = Priority
  4. Enrich contacts (Apollo)
  5. Generate outreach (primary + follow-ups + LinkedIn note)
  6. Push to HubSpot (company + contact + deal)
  7. Print rep alert: who to contact, what to say, why now
  8. Save alert to output/alerts/<domain>.md

Usage:
  python scripts/intake.py "Acme AI" acme.ai
  make intake COMPANY="Acme AI" DOMAIN=acme.ai

Options:
  --signal        Override auto-detected signal type
  --skip-hubspot  Don't push to HubSpot
  --skip-apollo   Skip contact enrichment (faster, no contacts)
  --dry-run       Full run, skip HubSpot write
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

sys.path.insert(0, str(Path(__file__).parent))

from apollo import _apollo_post, _apollo_key, find_contacts, enrich_company
from research import research_account, load_brain
from score import score_account
from outreach import generate_outreach
from hubspot import push_pipeline_output


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


# ─── Signal auto-detection ────────────────────────────────────────────────────


def detect_signals(domain: str) -> dict:
    """
    Look up a specific company in Apollo to auto-detect buying signals.
    Falls back to 'manual' if Apollo is unavailable or company not found.
    """
    today = date.today().isoformat()
    fallback = {"type": "manual", "date": today, "source": "manual",
                "summary": "Manually identified as a prospect."}

    try:
        api_key = _apollo_key()
    except Exception:
        return fallback

    try:
        # Company lookup by domain
        data = _apollo_post("organizations/search", {
            "api_key": api_key,
            "page": 1,
            "per_page": 1,
            "q_organization_domains": [domain],
        }, timeout=15)

        orgs = data.get("organizations", [])
        if not orgs:
            return {**fallback, "source": "Apollo",
                    "summary": "Not found in Apollo — manually identified."}

        org = orgs[0]
        stage = org.get("latest_funding_stage", "").lower()
        funding_date = (org.get("latest_funding_date") or "")[:10]
        funding_amount = org.get("latest_funding_amount")
        employees = org.get("estimated_num_employees", 0) or 0

        # Funding signal: raised in last 180 days
        cutoff = date.fromordinal(date.today().toordinal() - 180).isoformat()
        if funding_date and funding_date >= cutoff:
            amount_str = f"${funding_amount:,}" if funding_amount else "undisclosed"
            return {
                "type": "funding",
                "date": funding_date,
                "source": "Apollo",
                "summary": f"Raised {amount_str} ({stage}) — {employees} employees",
            }

        # Hiring signal: open sales roles
        hiring = _apollo_post("mixed_people/search", {
            "api_key": api_key,
            "page": 1,
            "per_page": 3,
            "q_organization_domains": [domain],
            "person_titles": ["VP Sales", "Account Executive", "SDR", "Head of Sales"],
        }, timeout=15)

        if hiring.get("people"):
            return {
                "type": "hiring",
                "date": today,
                "source": "Apollo",
                "summary": (f"Hiring for sales roles — {employees} employees"
                            + (f", {stage}" if stage else "")),
            }

        # Known company but no strong signal
        meta = ", ".join(filter(None, [stage, f"{employees} employees" if employees else ""]))
        return {
            "type": "manual",
            "date": today,
            "source": "Apollo",
            "summary": f"Manually identified." + (f" {meta}." if meta else ""),
        }

    except Exception:
        return fallback


# ─── Rep alert output ─────────────────────────────────────────────────────────


def print_rep_alert(data: dict, out_file: Path) -> None:
    """Print the clean rep-facing alert to terminal."""
    company = data.get("company", "")
    domain = data.get("domain", "")
    score = data.get("score", {})
    research = data.get("research", {})
    contacts = data.get("contacts", [])
    outreach_map = data.get("outreach", {})
    signal = data.get("signal", {})
    apollo_co = data.get("apollo_company", {})

    priority = score.get("priority", 0)
    icp_fit = score.get("icp_fit", 0)
    signal_strength = score.get("signal_strength", 0)
    action = score.get("action", "review")

    W = 65

    click.echo(f"\n{'═'*W}")
    click.echo(f"  {company.upper()} — Rep Alert")
    click.echo(f"{'═'*W}")

    # Score bar
    filled = "█" * priority
    empty = "░" * (15 - priority)
    click.echo(f"\n  Priority  {priority}/15  [{filled}{empty}]")
    click.echo(f"  ICP {icp_fit}/5  ·  Signal {signal_strength}/3  ·  → {action.upper()}")

    # Company snapshot
    click.echo(f"\n  {company}  ·  {domain}")
    if research.get("one_liner"):
        click.echo(f"  {research['one_liner']}")

    meta_parts = [
        str(apollo_co["employee_count"]) + " employees" if apollo_co.get("employee_count") else "",
        apollo_co.get("location", ""),
        apollo_co.get("funding_stage", ""),
    ]
    meta = "  ·  ".join(p for p in meta_parts if p)
    if meta:
        click.echo(f"  {meta}")

    # Signal
    click.echo(f"\n  Signal:  {signal.get('type','').upper()}  —  {signal.get('summary','')}")
    if signal.get("date"):
        click.echo(f"  Date:    {signal['date']}  ·  Source: {signal.get('source','?')}")

    # Pain
    if research.get("pain_hypothesis"):
        click.echo(f"\n  Pain:  {research['pain_hypothesis']}")

    # Why they fit
    icp_rationale = score.get("icp_rationale", [])
    if icp_rationale:
        click.echo(f"\n  Why they fit:")
        for r in icp_rationale[:3]:
            click.echo(f"    {r}")

    # Contacts + messages
    if contacts:
        click.echo(f"\n{'─'*W}")
        click.echo(f"  OUTREACH")
        click.echo(f"{'─'*W}")

        for contact in contacts:
            email = contact.get("email", "")
            name = contact.get("name", "")
            title = contact.get("title", "")
            linkedin = contact.get("linkedin_url", "")

            click.echo(f"\n  {name}  ·  {title}")
            if email:
                click.echo(f"  Email:    {email}")
            if linkedin:
                click.echo(f"  LinkedIn: {linkedin}")

            msgs = outreach_map.get(email, {})
            if not msgs:
                continue

            primary = msgs.get("primary", {})
            if primary.get("subject"):
                click.echo(f"\n  Subject: {primary['subject']}")
            if primary.get("body"):
                click.echo(f"  {'─'*55}")
                for line in primary["body"].strip().split("\n"):
                    click.echo(f"  {line}")
                click.echo(f"  {'─'*55}")

            note = msgs.get("linkedin_connection_note", "")
            if note:
                chars = len(note)
                flag = "✓" if chars <= 300 else "⚠ TOO LONG — trim before sending"
                click.echo(f"\n  LinkedIn Note  ({chars} chars {flag})")
                click.echo(f"  {'─'*55}")
                for line in note.strip().split("\n"):
                    click.echo(f"  {line}")
                click.echo(f"  {'─'*55}")

            fu1 = msgs.get("followup_1", {})
            if fu1.get("body"):
                click.echo(f"\n  Follow-Up #1  (send day 3)")
                preview_lines = fu1["body"].strip().split("\n")[:3]
                for line in preview_lines:
                    click.echo(f"  {line}")
                click.echo(f"  ...")
    else:
        click.echo(f"\n  No contacts found automatically.")
        click.echo(f"  → Search {domain} on LinkedIn or Apollo for: CEO, Founder, VP Sales")
        click.echo(f"  → Add contacts in HubSpot, then generate outreach:")
        click.echo(f"    make followup-generate FILE={out_file} EMAIL=<email> TOUCH=1")

    # Next actions
    first_email = contacts[0].get("email", "<email>") if contacts else "<email>"
    domain_safe = domain.replace(".", "_")

    click.echo(f"\n{'─'*W}")
    click.echo(f"  NEXT ACTIONS")
    click.echo(f"{'─'*W}")
    click.echo(f"  1. Send the message above")
    click.echo(f"  2. Log it:")
    click.echo(f"     python scripts/follow_up.py log \\")
    click.echo(f"       --file {out_file} --email {first_email} --touch 1")
    click.echo(f"  3. Follow-up queue: make followup-due")
    click.echo(f"  4. Full pipeline view: make ui")
    click.echo(f"\n  Alert saved: output/alerts/{domain_safe}.md")
    click.echo(f"{'═'*W}\n")


def save_alert_markdown(data: dict, alerts_dir: Path) -> Path:
    """Save rep alert as markdown for async review."""
    company = data.get("company", "")
    domain = data.get("domain", "")
    score = data.get("score", {})
    research = data.get("research", {})
    contacts = data.get("contacts", [])
    outreach_map = data.get("outreach", {})
    signal = data.get("signal", {})
    today = date.today().isoformat()

    alerts_dir.mkdir(parents=True, exist_ok=True)
    alert_file = alerts_dir / f"{domain.replace('.', '_')}.md"

    lines = [
        f"# {company} — Rep Alert",
        f"",
        f"**Date:** {today}  ",
        f"**Priority:** {score.get('priority', '?')}/15  ",
        f"**Action:** {score.get('action', '?').upper()}  ",
        f"**Signal:** {signal.get('type','?').upper()} — {signal.get('summary','')}  ",
        f"**Signal Date:** {signal.get('date','?')}",
        f"",
        f"---",
        f"",
        f"## Company",
        f"",
        f"{research.get('one_liner', '')}",
        f"",
        f"**Pain:** {research.get('pain_hypothesis', '')}",
        f"",
        f"**ICP Verdict:** {research.get('icp_verdict', '')} — {research.get('icp_reason', '')}",
        f"",
        f"### Why They Fit",
        f"",
    ]
    for r in score.get("icp_rationale", []):
        lines.append(f"- {r}")

    lines += ["", "---", "", "## Outreach", ""]

    for contact in contacts:
        email = contact.get("email", "")
        name = contact.get("name", "")
        title = contact.get("title", "")
        linkedin = contact.get("linkedin_url", "")

        lines += [f"### {name} — {title}", ""]
        if email:
            lines.append(f"- **Email:** {email}")
        if linkedin:
            lines.append(f"- **LinkedIn:** {linkedin}")
        lines.append("")

        msgs = outreach_map.get(email, {})
        primary = msgs.get("primary", {})
        if primary:
            lines += [
                f"**Subject:** {primary.get('subject', '')}",
                "",
                "```",
                primary.get("body", "").strip(),
                "```",
                "",
            ]

        note = msgs.get("linkedin_connection_note", "")
        if note:
            lines += [
                f"**LinkedIn Note** ({len(note)} chars):",
                "",
                "```",
                note.strip(),
                "```",
                "",
            ]

        fu1 = msgs.get("followup_1", {})
        if fu1.get("body"):
            lines += [
                "**Follow-Up #1** (send day 3):",
                "",
                "```",
                fu1["body"].strip(),
                "```",
                "",
            ]

    out_filename = f"{domain.replace('.', '_')}_{today}.json"
    first_email = contacts[0].get("email", "<email>") if contacts else "<email>"

    lines += [
        "---",
        "",
        "## After Sending",
        "",
        "```bash",
        f"python scripts/follow_up.py log \\",
        f"  --file output/{out_filename} \\",
        f"  --email {first_email} --touch 1",
        "```",
    ]

    alert_file.write_text("\n".join(lines))
    return alert_file


# ─── CLI ──────────────────────────────────────────────────────────────────────


@click.command()
@click.argument("company")
@click.argument("domain")
@click.option("--signal", default=None,
              type=click.Choice(["funding", "hiring", "gtm_struggle",
                                  "agency_churn", "tool_adoption", "manual"]),
              help="Override auto-detected signal type")
@click.option("--signal-summary", default=None,
              help="Override auto-detected signal summary")
@click.option("--skip-hubspot", is_flag=True,
              help="Skip HubSpot push (review first, push later)")
@click.option("--skip-apollo", is_flag=True,
              help="Skip Apollo enrichment — faster, no contacts found")
@click.option("--dry-run", is_flag=True,
              help="Full run, no HubSpot writes")
@click.option("--config", "config_path", default="config.yaml")
def intake(company, domain, signal, signal_summary, skip_hubspot,
           skip_apollo, dry_run, config_path):
    """
    Start working with a new prospect in one command.

    \b
    Automatically:
      - Detects signals (funding, hiring) via Apollo
      - Researches the company with Claude
      - Scores ICP fit × signal strength
      - Enriches contacts via Apollo
      - Generates personalized outreach
      - Pushes to HubSpot
      - Prints a rep-ready alert

    \b
    Example:
      python scripts/intake.py "Acme AI" acme.ai
      make intake COMPANY="Acme AI" DOMAIN=acme.ai
    """
    config = load_config(config_path)
    brain_path = config.get("brain", {}).get("path", "brain")
    today = date.today().isoformat()

    click.echo(f"\n{'='*65}")
    click.echo(f"  DeployGTM Intake")
    click.echo(f"  {company}  ·  {domain}")
    click.echo(f"{'='*65}\n")

    # ── 1. Detect signals ─────────────────────────────────────────────────────
    click.echo("1/5  Detecting signals...")
    detected = detect_signals(domain)
    sig_type = signal or detected["type"]
    sig_date = detected["date"]
    sig_source = detected["source"]
    sig_summary = signal_summary or detected["summary"]
    click.echo(f"     {sig_type.upper()} — {sig_summary}")

    # ── 2. Research ───────────────────────────────────────────────────────────
    click.echo("\n2/5  Researching with Claude...")
    brain_context = load_brain(brain_path)
    try:
        research = research_account(
            company=company,
            domain=domain,
            signal_type=sig_type,
            signal_date=sig_date,
            signal_summary=sig_summary,
            brain_context=brain_context,
        )
        click.echo(f"     {research.get('one_liner', 'Research complete')}")
        click.echo(f"     ICP: {research.get('icp_verdict', '?')} — {research.get('icp_reason', '')}")
    except Exception as e:
        click.echo(f"     Research failed: {e}", err=True)
        research = {}

    # ── 3. Score ──────────────────────────────────────────────────────────────
    click.echo("\n3/5  Scoring...")
    score = score_account(
        account=research,
        signal_type=sig_type,
        signal_date=sig_date,
        config=config,
    )
    click.echo(f"     Priority {score['priority']}/15  ICP {score['icp_fit']}/5  "
               f"Signal {score['signal_strength']}/3  →  {score['action'].upper()}")

    skip_threshold = config.get("scoring", {}).get("skip_below", 5)
    if score["priority"] < skip_threshold:
        click.echo(f"\n  ⚠  Priority {score['priority']} is below threshold ({skip_threshold}).")
        if not click.confirm("  This may not be worth pursuing. Continue?", default=False):
            click.echo("  Stopped.")
            return

    # ── 4. Enrich contacts ────────────────────────────────────────────────────
    apollo_enabled = config.get("tools", {}).get("apollo", {}).get("enabled", True)
    contacts = []
    apollo_co = {}

    if not skip_apollo and apollo_enabled:
        click.echo("\n4/5  Enriching contacts via Apollo...")
        try:
            apollo_co = enrich_company(domain)
            click.echo(f"     {apollo_co.get('name', domain)} — "
                       f"{apollo_co.get('employee_count', '?')} employees — "
                       f"{apollo_co.get('funding_stage', '?')}")
            contacts = find_contacts(domain, config=config)
            for c in contacts:
                click.echo(f"     → {c.get('name','?')}  {c.get('title','?')}  {c.get('email','no email')}")
        except Exception as e:
            click.echo(f"     Apollo error: {e}", err=True)
    else:
        click.echo("\n4/5  Apollo skipped.")

    # ── 5. Generate outreach ──────────────────────────────────────────────────
    outreach_map = {}
    if contacts:
        click.echo("\n5/5  Generating outreach...")
        for contact in contacts:
            email = contact.get("email", "")
            if not email or not contact.get("name"):
                continue
            try:
                msg = generate_outreach(
                    research=research,
                    contact_name=contact["name"],
                    contact_title=contact.get("title", ""),
                    signal_type=sig_type,
                    signal_date=sig_date,
                    signal_summary=sig_summary,
                    brain_context=brain_context,
                )
                outreach_map[email] = msg
                click.echo(f"     ✓ {contact['name']}  [{msg.get('persona','?')}]")
            except Exception as e:
                click.echo(f"     ✗ {contact.get('name', email)}: {e}", err=True)
    else:
        click.echo("\n5/5  No contacts — skipping outreach generation.")

    # ── Assemble output ───────────────────────────────────────────────────────
    out_dir = Path(config.get("output", {}).get("path", "output"))
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"{domain.replace('.', '_')}_{today}.json"

    output_data = {
        "company": company,
        "domain": domain,
        "signal": {
            "type": sig_type,
            "date": sig_date,
            "source": sig_source,
            "summary": sig_summary,
        },
        "research": research,
        "apollo_company": apollo_co,
        "contacts": contacts,
        "score": score,
        "outreach": outreach_map,
        "meta": {"run_date": today, "intake": True, "config": config_path},
    }
    out_file.write_text(json.dumps(output_data, indent=2))

    # ── Push to HubSpot ───────────────────────────────────────────────────────
    hs_token = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")
    if not skip_hubspot and not dry_run and hs_token:
        click.echo("\nPushing to HubSpot...")
        try:
            push_pipeline_output(output_data, dry_run=False)
            click.echo("  ✓ Company, contacts, and deal synced.")
        except Exception as e:
            click.echo(f"  ✗ HubSpot push failed: {e}", err=True)
            click.echo(f"  Push manually: python scripts/pipeline.py push --file {out_file}")
    elif not hs_token:
        click.echo("\n  No HUBSPOT_ACCESS_TOKEN — skipping push.")
        click.echo(f"  Push manually when ready: python scripts/pipeline.py push --file {out_file}")
    elif dry_run:
        click.echo("\n  [Dry run] HubSpot push skipped.")

    # ── Rep alert ─────────────────────────────────────────────────────────────
    save_alert_markdown(output_data, Path("output/alerts"))
    print_rep_alert(output_data, out_file)


if __name__ == "__main__":
    intake()
