"""
DeployGTM — Activate a Matrix Account into HubSpot

Takes a verified account from a client's account matrix and a chosen outreach
variant from the batch_outreach output files, then pushes to HubSpot:
  1. Upsert the company record (name + domain + DeployGTM custom fields)
  2. Create a deal at "outreach_sent" stage
  3. Create a note on the company record with the chosen variant body

After activating, log the follow-up cadence:
  python scripts/follow_up.py log --file output/<domain>.json --touch 1

Usage:
  # Dry-run — show what would be pushed without touching HubSpot
  python projects/deploygtm-own/scripts/activate_account.py \\
      --client deploygtm --company "Loops" --variant 1 --dry-run

  # Live push (requires HUBSPOT_ACCESS_TOKEN in .env)
  python projects/deploygtm-own/scripts/activate_account.py \\
      --client deploygtm --company "Loops" --variant 1
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional

import click

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.resolve().parents[2]

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

from generate_outreach import (  # noqa: E402
    OUTPUTS_DIR,
    load_client_matrix,
    find_account,
    slugify,
)
from verify_signals import audit_account  # noqa: E402
from update_status import set_status  # noqa: E402


# ─── Output file parsing ──────────────────────────────────────────────────────

_VARIANT_HEADER = re.compile(
    r"^--- Variant (\d+): (.+?) ---$", re.MULTILINE
)
_SUBJECT_LINE = re.compile(r"^Subject: (.+)$", re.MULTILINE)
_WORDS_LINE = re.compile(r"^Words:\s+\d+", re.MULTILINE)


def find_latest_output(client: str, company: str) -> Optional[Path]:
    """Return the most recent .txt output file for a company, or None."""
    client_dir = OUTPUTS_DIR / client
    if not client_dir.exists():
        return None
    slug = slugify(company)
    candidates = sorted(client_dir.glob(f"{slug}_*.txt"), reverse=True)
    return candidates[0] if candidates else None


def parse_output_file(path: Path) -> list[dict]:
    """Parse a batch_outreach .txt file into a list of variant dicts.

    Each dict has: variant_num (int), angle_label (str), subject (str), body (str).
    """
    text = path.read_text()
    headers = list(_VARIANT_HEADER.finditer(text))
    if not headers:
        raise ValueError(f"No variant headers found in {path}")

    variants: list[dict] = []
    for i, m in enumerate(headers):
        num = int(m.group(1))
        label = m.group(2).strip()
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        block = text[start:end].strip()

        subject = ""
        subject_m = _SUBJECT_LINE.search(block)
        if subject_m:
            subject = subject_m.group(1).strip()

        # Body is everything after the "Words: N" line
        words_m = _WORDS_LINE.search(block)
        if words_m:
            body = block[words_m.end():].strip()
        else:
            # Fallback: strip subject line
            body = re.sub(r"^Subject:.*\n?", "", block).strip()

        variants.append({
            "variant_num": num,
            "angle_label": label,
            "subject": subject,
            "body": body,
        })

    return variants


# ─── HubSpot push ─────────────────────────────────────────────────────────────


def _push_to_hubspot(
    account: dict,
    variant: dict,
    dry_run: bool = False,
) -> dict:
    """Push company + deal + note to HubSpot. Returns result dict."""
    try:
        from hubspot import upsert_company, create_or_update_deal, create_engagement_note
    except ImportError as e:
        raise click.ClickException(
            f"Could not import hubspot module: {e}. "
            "Ensure you are running from the repo root or scripts/ is on PYTHONPATH."
        )

    signal = account.get("why_now_signal", {})
    results: dict = {"company_id": None, "deal_id": None, "note_id": None}

    # 1. Company
    click.echo("  Upserting company...")
    company_id = upsert_company(
        {
            "name": account["company"],
            "company": account["company"],
            "domain": account["domain"],
        },
        dry_run=dry_run,
    )
    results["company_id"] = company_id
    if company_id:
        click.echo(f"  Company  → {company_id}")

    # 2. Deal
    click.echo("  Creating deal...")
    try:
        deal_id = create_or_update_deal(
            company_name=account["company"],
            stage="outreach_sent",
            company_id=company_id,
            dry_run=dry_run,
        )
        results["deal_id"] = deal_id
        if deal_id:
            click.echo(f"  Deal     → {deal_id}")
    except Exception as e:
        click.echo(f"  Deal creation failed: {e}", err=True)

    # 3. Note with variant content
    if company_id:
        click.echo("  Creating note...")
        note_body = (
            f"OUTREACH SENT — {account['company']} ({account['domain']})\n\n"
            f"Angle: {variant['angle_label']}\n"
            f"Signal: [{signal.get('type', '?')}] {signal.get('description', '')}\n\n"
            f"Subject: {variant['subject']}\n\n"
            f"{variant['body']}"
        )
        note_id = create_engagement_note(company_id, note_body, dry_run=dry_run)
        results["note_id"] = note_id
        if note_id:
            click.echo(f"  Note     → {note_id}")

    return results


# ─── Variant tracker log ──────────────────────────────────────────────────────


def _log_to_tracker(client: str, company: str, variant: dict) -> Optional[int]:
    try:
        from generate_outreach import log_variant_to_tracker
        return log_variant_to_tracker(client, company, {
            "angle_label": variant["angle_label"],
            "body": variant["body"],
        })
    except Exception as e:
        click.echo(f"  WARN: could not log to tracker: {e}", err=True)
        return None


# ─── CLI ─────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--client", required=True, help="Client slug.")
@click.option("--company", required=True, help="Company name (as in the matrix).")
@click.option("--variant", "variant_num", type=click.IntRange(1, 3), default=1,
              show_default=True, help="Variant number to activate (1–3).")
@click.option("--output-file", "output_file", default=None,
              help="Path to a specific .txt output file. Defaults to the latest for this company.")
@click.option("--dry-run", is_flag=True,
              help="Show what would be pushed without writing to HubSpot.")
@click.option("--skip-hubspot", is_flag=True,
              help="Skip HubSpot push entirely (just log to tracker).")
def main(
    client: str,
    company: str,
    variant_num: int,
    output_file: Optional[str],
    dry_run: bool,
    skip_hubspot: bool,
):
    """Push a chosen outreach variant for one matrix account to HubSpot."""

    # 1. Load and verify the account
    matrix = load_client_matrix(client)
    account = find_account(matrix, company)
    issues = audit_account(account)
    if issues:
        raise click.ClickException(
            f"Account has unresolved blockers — resolve before activating:\n"
            + "\n".join(f"  - {i}" for i in issues)
        )

    click.echo(f"\nActivating: {account['company']} ({account['domain']})")
    click.echo(f"Client:     {client}")
    signal = account.get("why_now_signal", {})
    click.echo(f"Signal:     [{signal.get('type', '?')}] {signal.get('description', '')[:80]}")

    # 2. Find and parse output file
    if output_file:
        txt_path = Path(output_file)
    else:
        txt_path = find_latest_output(client, company)

    if not txt_path or not txt_path.exists():
        raise click.ClickException(
            f"No output file found for '{company}' under outputs/{client}/. "
            f"Run `make outreach-variants CLIENT={client} COMPANY=\"{company}\"` first."
        )

    click.echo(f"Output file: {txt_path.name}")
    variants = parse_output_file(txt_path)

    if variant_num > len(variants):
        raise click.ClickException(
            f"Output file has {len(variants)} variant(s); --variant {variant_num} is out of range."
        )

    chosen = variants[variant_num - 1]
    click.echo(f"Variant {variant_num}: {chosen['angle_label']}")
    click.echo(f"Subject:    {chosen['subject']}")
    click.echo(f"Body ({len(chosen['body'].split())} words):")
    click.echo("")
    for line in chosen["body"].splitlines():
        click.echo(f"  {line}")
    click.echo("")

    if dry_run:
        click.echo("(dry-run) HubSpot push skipped.")
        _push_to_hubspot(account, chosen, dry_run=True)
        return

    # 3. Require explicit confirmation for live push
    if not skip_hubspot:
        if not click.confirm(
            "Push this variant to HubSpot? (creates company + deal + note)", default=False
        ):
            click.echo("Aborted.")
            return

        _push_to_hubspot(account, chosen, dry_run=False)

    # 4. Log to variant tracker
    rid = _log_to_tracker(client, company, chosen)
    if rid:
        click.echo(f"Logged to tracker (id={rid}).")

    # 5. Mark account status as outreach_sent in the matrix file
    if not skip_hubspot:
        try:
            set_status(
                client, company, "outreach_sent",
                note=f"Activated variant {variant_num}: {chosen['angle_label']}",
            )
            click.echo(f"Matrix status → outreach_sent")
        except Exception as e:
            click.echo(f"  WARN: could not update matrix status: {e}", err=True)

    click.echo("")
    click.echo("Done. Next steps:")
    click.echo(f"  1. Send the email manually or enroll in a HubSpot sequence.")
    click.echo(f"  2. When the prospect replies: make set-status CLIENT={client} "
               f"COMPANY=\"{company}\" STATUS=replied")
    click.echo(f"  3. Record sentiment: make variant-respond ID={rid or '?'} SENTIMENT=positive")


if __name__ == "__main__":
    main()
