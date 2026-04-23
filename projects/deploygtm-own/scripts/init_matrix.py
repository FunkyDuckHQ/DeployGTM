"""
DeployGTM — Initialize a Client Account Matrix

Creates a schema-valid stub at data/<client>_accounts.json with:
  - client_name set
  - voice_notes placeholder (with a nudge to fill it in)
  - accounts: one example entry pre-filled with the structure every field
    expects, so the user sees the shape and can duplicate it.

After this runs, the three other artifacts (generate_outreach, variant_tracker,
weekly_signal_report) work against --client <slug> immediately.

Usage:
  python projects/deploygtm-own/scripts/init_matrix.py --client acme-corp
  python projects/deploygtm-own/scripts/init_matrix.py --client acme-corp --force
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import click


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SCHEMA_FILE = PROJECT_ROOT / "account_matrix_schema.json"


def stub(client: str) -> dict:
    return {
        "client_name": client,
        "voice_notes": (
            "REPLACE THIS — describe the client's tone in 2-4 sentences. "
            "Sentence length. Vocabulary register. Things to avoid. "
            "Preferred close ('20 minutes?' vs 'worth a call?'). This is the "
            "single field the outreach generator uses to match voice."
        ),
        "accounts": [
            {
                "company": "Example Corp",
                "domain": "example.com",
                "icp_tier": 1,
                "market": "REPLACE — broad market grouping (e.g. B2B SaaS, NewSpace)",
                "segment": "REPLACE — meaningful subdivision a rep would recognize",
                "persona": {
                    "title": "Chief Technology Officer",
                    "why_they_feel_it": (
                        "REPLACE — why this specific person feels the pain in "
                        "their frame, not the client's"
                    ),
                },
                "angle": (
                    "REPLACE — one-sentence directional argument. Not a pain "
                    "point. Something a rep can build a message around."
                ),
                "why_now_signal": {
                    "type": "funding",
                    "description": "REPLACE — what specifically happened",
                    "source": "REPLACE — Crunchbase / SAM.gov / LinkedIn / etc.",
                    "date": date.today().isoformat(),
                },
                "product_fit": (
                    "REPLACE — specifically what about the client's product "
                    "solves this account's problem. Precise, not generic."
                ),
                "heritage_risk": "Low",
                "status": "monitor",
                "last_updated": date.today().isoformat(),
            }
        ],
    }


def target_path(client: str) -> Path:
    normalized = client.replace("-", "_")
    return DATA_DIR / f"{normalized}_accounts.json"


@click.command()
@click.option("--client", required=True, help="Client slug (e.g. acme-corp).")
@click.option("--force", is_flag=True, help="Overwrite if the file already exists.")
def main(client: str, force: bool):
    """Scaffold a new client account matrix stub in data/."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = target_path(client)

    if out.exists() and not force:
        click.echo(f"File already exists: {out}")
        click.echo("Use --force to overwrite.")
        sys.exit(1)

    data = stub(client)
    out.write_text(json.dumps(data, indent=2) + "\n")

    click.echo(f"Wrote stub: {out}")
    click.echo("")
    click.echo("Next steps:")
    click.echo(f"  1. Edit {out} — fill in voice_notes, then replace the example account.")
    click.echo(f"  2. Validate against {SCHEMA_FILE.relative_to(PROJECT_ROOT.parents[1])}")
    click.echo(f"  3. Generate variants: make outreach-variants CLIENT={client} COMPANY=\"<name>\"")
    click.echo(f"  4. Weekly report:      make weekly-report CLIENT={client}")


if __name__ == "__main__":
    main()
