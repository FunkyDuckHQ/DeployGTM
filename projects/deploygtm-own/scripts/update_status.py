"""
DeployGTM — Update an Account's Status in the Client Matrix

Writes back to data/<client>_accounts.json with:
  - updated status (one of the schema enum values)
  - last_updated bumped to today
  - optional dated note appended to notes field

Used directly via CLI for manual updates, and imported by activate_account.py
to auto-mark accounts as 'outreach_sent' after a successful HubSpot push.

Usage:
  python projects/deploygtm-own/scripts/update_status.py \\
      --client deploygtm --company "Loops" --status outreach_sent

  python projects/deploygtm-own/scripts/update_status.py \\
      --client deploygtm --company "Loops" --status replied --note "Tyler replied yes to call"
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import click

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_outreach import _matrix_path, find_account, load_client_matrix  # noqa: E402


VALID_STATUSES = {
    "monitor",
    "active",
    "outreach_sent",
    "replied",
    "meeting_booked",
    "no_fit",
    "paused",
}


def set_status(
    client: str,
    company: str,
    status: str,
    note: Optional[str] = None,
) -> dict:
    """Update an account's status in the client matrix file.

    Returns the updated account dict. Raises ValueError if the status is
    not in the schema enum or the company is not found.
    """
    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status '{status}'. Must be one of: {sorted(VALID_STATUSES)}"
        )

    matrix = load_client_matrix(client)
    account = find_account(matrix, company)

    today = date.today().isoformat()
    account["status"] = status
    account["last_updated"] = today

    if note:
        prefix = f"[{today}] {status}: {note}"
        existing = (account.get("notes") or "").strip()
        account["notes"] = f"{existing}\n{prefix}".strip() if existing else prefix

    # Replace the account in the matrix (find_account returns by reference but
    # we rewrite the whole file regardless to keep the contract explicit).
    path = _matrix_path(client)
    path.write_text(json.dumps(matrix, indent=2) + "\n")

    return account


@click.command()
@click.option("--client", required=True, help="Client slug.")
@click.option("--company", required=True, help="Company name as in the matrix.")
@click.option("--status", required=True,
              type=click.Choice(sorted(VALID_STATUSES)),
              help="New status value (one of the schema enum values).")
@click.option("--note", default=None,
              help="Optional note. Appended to account.notes with date + status prefix.")
def main(client: str, company: str, status: str, note: Optional[str]):
    """Update one account's status in the client matrix."""
    account = set_status(client, company, status, note)
    click.echo(f"Updated: {account['company']} → status={status}, last_updated={account['last_updated']}")
    if note:
        click.echo(f"Note appended: {note}")


if __name__ == "__main__":
    main()
