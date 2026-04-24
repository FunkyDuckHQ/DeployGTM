"""
DeployGTM — Signal Verification Checker

Scans a client's account matrix for accounts that cannot be used for outreach
yet — signals marked VERIFY, dates missing, or placeholder company names.

Usage:
  python projects/deploygtm-own/scripts/verify_signals.py --client deploygtm
  python projects/deploygtm-own/scripts/verify_signals.py --client deploygtm --strict

Exit codes:
  0 — all accounts ready (or strict mode not set)
  1 — one or more accounts blocked and --strict was passed
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_outreach import load_client_matrix  # noqa: E402


PLACEHOLDER_MARKERS = ("VERIFY", "FILL IN", "FILL_IN", "REPLACE")


def _contains_marker(s: str | None) -> bool:
    if not s:
        return False
    upper = s.upper()
    return any(m in upper for m in PLACEHOLDER_MARKERS)


def audit_account(account: dict) -> list[str]:
    """Return a list of issues that block this account from outreach.

    Empty list means the account is ready. Used both by the CLI and by
    batch_outreach.py to auto-skip blocked accounts.
    """
    issues: list[str] = []
    company = (account.get("company") or "").strip()
    if not company:
        issues.append("company is empty")
    elif _contains_marker(company) or company.startswith("<"):
        issues.append("company is a placeholder")

    domain = (account.get("domain") or "").strip()
    if not domain:
        issues.append("domain is empty")
    elif _contains_marker(domain):
        issues.append("domain is a placeholder")

    signal = account.get("why_now_signal") or {}
    if _contains_marker(signal.get("description")):
        issues.append("signal description needs verification")
    if _contains_marker(signal.get("date")):
        issues.append("signal date needs verification")
    elif not signal.get("date"):
        issues.append("signal date is missing")

    return issues


def audit_matrix(matrix: dict) -> tuple[list[dict], list[tuple[dict, list[str]]]]:
    """Split accounts into (ready, blocked_with_issues)."""
    ready: list[dict] = []
    blocked: list[tuple[dict, list[str]]] = []
    for acct in matrix.get("accounts", []):
        issues = audit_account(acct)
        if issues:
            blocked.append((acct, issues))
        else:
            ready.append(acct)
    return ready, blocked


@click.command()
@click.option("--client", required=True, help="Client slug (matches client_name in matrix).")
@click.option("--strict", is_flag=True, help="Exit 1 if any account is blocked.")
def main(client: str, strict: bool):
    """Audit a client's matrix for accounts ready vs. blocked on signal gaps."""
    matrix = load_client_matrix(client)
    ready, blocked = audit_matrix(matrix)
    total = len(ready) + len(blocked)

    click.echo(f"Client:  {matrix.get('client_name')}")
    click.echo(f"Total:   {total} accounts")
    click.echo(f"Ready:   {len(ready)}")
    click.echo(f"Blocked: {len(blocked)}")
    click.echo("")

    if ready:
        click.echo("READY for outreach:")
        for a in ready:
            signal_type = (a.get("why_now_signal") or {}).get("type", "?")
            click.echo(f"  [T{a.get('icp_tier')}] {a.get('company')}  ({signal_type})")
        click.echo("")

    if blocked:
        click.echo("BLOCKED (fix before running outreach):")
        for a, issues in blocked:
            click.echo(f"  [T{a.get('icp_tier')}] {a.get('company')}")
            for issue in issues:
                click.echo(f"      - {issue}")
        click.echo("")

    if strict and blocked:
        sys.exit(1)


if __name__ == "__main__":
    main()
