"""
DeployGTM — CRM Audit

Scans output/ files for data quality issues before pushing to HubSpot.
Run this before any push to catch problems early.

Flags:
  - Missing email addresses (can't enroll in sequences)
  - Low-confidence enrichments (may contain wrong data)
  - Contacts without outreach generated
  - Accounts below activation threshold
  - Stale files (>30 days since pipeline run)
  - Duplicate domains in output/
  - Disqualified accounts still in output/
  - Contacts already marked replied/booked (may need different treatment)

Usage:
  python scripts/crm_audit.py scan
  python scripts/crm_audit.py scan --min-priority 8 --fix-missing-outreach
  make audit
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import click
import yaml


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def days_since(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        return (date.today() - date.fromisoformat(date_str)).days
    except ValueError:
        return None


def load_output_file(path: Path) -> dict:
    return json.loads(path.read_text())


# ─── Issue types ──────────────────────────────────────────────────────────────

SEVERITY_COLORS = {
    "error": "\033[31m",
    "warn": "\033[33m",
    "info": "\033[36m",
}
RESET = "\033[0m"


def issue(severity: str, message: str) -> dict:
    return {"severity": severity, "message": message}


def audit_file(data: dict, fpath: Path, min_priority: int, stale_days: int) -> list[dict]:
    issues = []
    company = data.get("company", fpath.stem)
    score = data.get("score", {})
    research = data.get("research", {})
    meta = data.get("meta", {})
    contacts = data.get("contacts", [])
    outreach = data.get("outreach", {})
    follow_up_log = data.get("follow_up_log", {})

    # ── Scoring issues ────────────────────────────────────────────────────────
    priority = score.get("priority")
    if priority is None:
        issues.append(issue("error", "No priority score — file may be incomplete"))
    elif priority < min_priority:
        issues.append(issue("warn",
            f"Priority {priority} is below activation threshold ({min_priority}) — should this be here?"))

    icp_verdict = research.get("icp_verdict", "")
    if icp_verdict == "disqualified":
        issues.append(issue("warn",
            f"ICP verdict is DISQUALIFIED — review before pushing to HubSpot"))

    # ── Enrichment confidence ─────────────────────────────────────────────────
    confidence = research.get("confidence", "")
    if confidence == "low":
        issues.append(issue("warn",
            "Enrichment confidence is LOW — verify manually before sending outreach"))

    # ── Contact issues ────────────────────────────────────────────────────────
    if not contacts:
        issues.append(issue("error",
            "No contacts found — cannot enroll in sequences or push contact data"))
    else:
        no_email = [c for c in contacts if not c.get("email")]
        if no_email:
            names = ", ".join(c.get("name", "?") for c in no_email)
            issues.append(issue("error",
                f"Contacts missing email: {names} — cannot send outreach"))

        unverified = [
            c for c in contacts
            if c.get("email") and c.get("email_status") not in ("verified", "likely")
        ]
        if unverified:
            names = ", ".join(c.get("name", "?") for c in unverified)
            issues.append(issue("warn",
                f"Unverified emails: {names} — higher bounce risk"))

        # ── Outreach issues ───────────────────────────────────────────────────
        contacts_with_email = [c for c in contacts if c.get("email")]
        missing_outreach = [
            c for c in contacts_with_email
            if c.get("email") not in outreach
        ]
        if missing_outreach:
            names = ", ".join(c.get("name", "?") for c in missing_outreach)
            issues.append(issue("warn",
                f"Contacts without outreach generated: {names}"))

    if not outreach and contacts:
        issues.append(issue("error",
            "Outreach not generated — run pipeline.py again without --skip-outreach"))

    # ── Staleness ─────────────────────────────────────────────────────────────
    run_date = meta.get("run_date")
    if run_date:
        age = days_since(run_date)
        if age is not None and age > stale_days:
            issues.append(issue("warn",
                f"File is {age} days old — signals may have changed, consider re-enriching"))

    # ── Follow-up status ──────────────────────────────────────────────────────
    booked = [
        email for email, entry in follow_up_log.items()
        if entry.get("status") == "booked"
    ]
    if booked:
        issues.append(issue("info",
            f"Call booked for: {', '.join(booked)} — don't enroll in sequences"))

    paused = [
        email for email, entry in follow_up_log.items()
        if entry.get("status") == "paused"
    ]
    if paused:
        issues.append(issue("info",
            f"Paused (3 touches, no reply): {', '.join(paused)}"))

    return issues


# ─── CLI ──────────────────────────────────────────────────────────────────────


@click.group()
def cli():
    """DeployGTM CRM Audit — data quality gate for output/ files."""
    pass


@cli.command()
@click.option("--output-dir", default="output", show_default=True,
              help="Directory to scan.")
@click.option("--config", "config_path", default="config.yaml", show_default=True)
@click.option("--min-priority", default=None, type=int,
              help="Flag files below this priority. Defaults to config scoring.activate_this_week.")
@click.option("--stale-days", default=30, show_default=True,
              help="Flag files older than this many days.")
@click.option("--errors-only", is_flag=True, default=False,
              help="Only show errors, not warnings or info.")
@click.option("--ready-to-push", is_flag=True, default=False,
              help="List only files that are clean and ready to push.")
def scan(output_dir: str, config_path: str, min_priority: Optional[int],
         stale_days: int, errors_only: bool, ready_to_push: bool):
    """Scan output/ files for data quality issues."""
    config = load_config(config_path)
    threshold = min_priority or config.get("scoring", {}).get("activate_this_week", 8)

    out_dir = Path(output_dir)
    files = sorted(out_dir.glob("*.json"))

    if not files:
        click.echo(f"No output files found in {output_dir}/")
        return

    # Check for duplicate domains
    seen_domains: dict[str, list[str]] = {}
    for fpath in files:
        try:
            data = load_output_file(fpath)
            domain = data.get("domain", "")
            if domain:
                seen_domains.setdefault(domain, []).append(fpath.name)
        except Exception:
            continue

    duplicate_domains = {d: fs for d, fs in seen_domains.items() if len(fs) > 1}

    # Audit each file
    results: list[tuple[Path, dict, list[dict]]] = []
    for fpath in files:
        try:
            data = load_output_file(fpath)
        except Exception as e:
            click.echo(f"  ✗ Could not read {fpath.name}: {e}", err=True)
            continue

        file_issues = audit_file(data, fpath, threshold, stale_days)

        domain = data.get("domain", "")
        if domain in duplicate_domains and len(duplicate_domains[domain]) > 1:
            dups = [f for f in duplicate_domains[domain] if f != fpath.name]
            file_issues.append(issue("warn",
                f"Duplicate domain — also exists as: {', '.join(dups)}"))

        results.append((fpath, data, file_issues))

    # Display
    error_count = 0
    warn_count = 0
    clean_count = 0
    push_ready: list[str] = []

    click.echo(f"\n{'='*65}")
    click.echo(f"  CRM Audit — {out_dir}/  ({len(files)} files, threshold ≥{threshold})")
    click.echo(f"{'='*65}")

    for fpath, data, file_issues in results:
        company = data.get("company", fpath.stem)
        score = data.get("score", {})
        priority = score.get("priority", "?")
        action = score.get("action", "?")
        run_date = data.get("meta", {}).get("run_date", "?")

        visible_issues = file_issues
        if errors_only:
            visible_issues = [i for i in file_issues if i["severity"] == "error"]

        has_errors = any(i["severity"] == "error" for i in file_issues)
        has_warns = any(i["severity"] == "warn" for i in file_issues)

        if has_errors:
            error_count += 1
            status = f"\033[31m✗ ERRORS\033[0m"
        elif has_warns:
            warn_count += 1
            status = f"\033[33m⚠ WARNINGS\033[0m"
        else:
            clean_count += 1
            push_ready.append(fpath.name)
            status = f"\033[32m✓ CLEAN\033[0m"

        if ready_to_push and not (not has_errors and not has_warns):
            continue

        click.echo(f"\n  {company}  (Priority {priority} / {action})  {status}")
        click.echo(f"  {fpath.name}  —  {run_date}")

        for iss in visible_issues:
            sev = iss["severity"]
            color = SEVERITY_COLORS.get(sev, "")
            icon = {"error": "✗", "warn": "⚠", "info": "ℹ"}.get(sev, "-")
            click.echo(f"    {color}{icon} [{sev.upper()}]{RESET} {iss['message']}")

        if not visible_issues and not ready_to_push:
            click.echo(f"    \033[32mNo issues found — ready to push\033[0m")

    # Summary
    click.echo(f"\n{'─'*65}")
    click.echo(f"  Summary: {clean_count} clean  {warn_count} warnings  {error_count} errors")

    if push_ready and not ready_to_push:
        click.echo(f"\n  Ready to push ({len(push_ready)}):")
        for fname in push_ready:
            click.echo(f"    python scripts/hubspot.py push --file {out_dir}/{fname}")

    if error_count > 0:
        click.echo(f"\n  Fix errors before pushing — {error_count} file(s) will cause CRM problems.")
    elif warn_count > 0:
        click.echo(f"\n  Review warnings before pushing — {warn_count} file(s) have soft issues.")
    else:
        click.echo(f"\n  All files clean. Safe to push.")

    click.echo(f"{'='*65}\n")


@cli.command()
@click.option("--output-dir", default="output", show_default=True)
def summary(output_dir: str):
    """Show a high-level pipeline summary across all output files."""
    out_dir = Path(output_dir)
    files = sorted(out_dir.glob("*.json"))

    if not files:
        click.echo("No output files.")
        return

    total = len(files)
    by_action: dict[str, int] = {}
    by_signal: dict[str, int] = {}
    by_verdict: dict[str, int] = {}
    by_status: dict[str, int] = {}
    contact_total = 0
    email_total = 0
    outreach_total = 0
    stale = 0
    cutoff = (date.today() - timedelta(days=30)).isoformat()

    for fpath in files:
        try:
            data = load_output_file(fpath)
        except Exception:
            continue

        action = data.get("score", {}).get("action", "unknown")
        by_action[action] = by_action.get(action, 0) + 1

        sig = data.get("signal", {}).get("type", "unknown")
        by_signal[sig] = by_signal.get(sig, 0) + 1

        verdict = data.get("research", {}).get("icp_verdict", "unknown")
        by_verdict[verdict] = by_verdict.get(verdict, 0) + 1

        contacts = data.get("contacts", [])
        contact_total += len(contacts)
        email_total += sum(1 for c in contacts if c.get("email"))
        outreach_total += len(data.get("outreach", {}))

        for entry in data.get("follow_up_log", {}).values():
            status = entry.get("status", "active")
            by_status[status] = by_status.get(status, 0) + 1

        run_date = data.get("meta", {}).get("run_date", "")
        if run_date and run_date < cutoff:
            stale += 1

    click.echo(f"\n{'='*55}")
    click.echo(f"  Pipeline Summary  ({total} accounts)")
    click.echo(f"{'='*55}")

    click.echo(f"\n  By action:")
    for action, count in sorted(by_action.items(), key=lambda x: -x[1]):
        click.echo(f"    {action:<30} {count}")

    click.echo(f"\n  By signal type:")
    for sig, count in sorted(by_signal.items(), key=lambda x: -x[1]):
        click.echo(f"    {sig:<30} {count}")

    click.echo(f"\n  ICP verdicts:")
    for v, count in sorted(by_verdict.items(), key=lambda x: -x[1]):
        click.echo(f"    {v:<30} {count}")

    click.echo(f"\n  Contacts + outreach:")
    click.echo(f"    Total contacts found:      {contact_total}")
    click.echo(f"    Contacts with email:        {email_total}")
    click.echo(f"    Outreach messages generated:{outreach_total}")

    if by_status:
        click.echo(f"\n  Follow-up status:")
        for status, count in sorted(by_status.items(), key=lambda x: -x[1]):
            click.echo(f"    {status:<30} {count}")

    if stale:
        click.echo(f"\n  Stale files (>30 days):     {stale}")

    click.echo(f"\n{'='*55}\n")


if __name__ == "__main__":
    cli()
