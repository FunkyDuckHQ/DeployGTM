"""
DeployGTM — Contact Enrichment + Individual Profiling

For each account in the matrix (tier 1+2 by default, not already enriched),
this script:
  1. Calls Apollo find_contacts() with persona-appropriate title filters
  2. For each contact found, asks Claude to build an individual profile:
       - pain_hypothesis  (tailored to their role, not the company's generic pain)
       - conversation_hooks  (2-3 openers tied to role + company context)
       - seniority / influence_level
       - likely_objections
  3. Stores contacts (with profiles) under account["contacts"] in accounts.json
  4. Marks account["contacts_enriched_at"] so reruns are idempotent

Persona → title mapping:
  founder_seller      → CEO, Co-Founder, Founder, CTO
  first_sales_leader  → VP Sales, Head of Sales, Founding AE, VP Revenue
  revops_growth       → RevOps, Head of Growth, Head of Operations, Growth

Usage:
  python projects/deploygtm-own/scripts/enrich_matrix.py --client deploygtm

  # Force re-enrich a specific account
  python projects/deploygtm-own/scripts/enrich_matrix.py \\
      --client deploygtm --company "Loops" --force
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import date
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

from generate_outreach import _matrix_path, load_client_matrix  # noqa: E402


# ─── Persona → title mapping ──────────────────────────────────────────────────

PERSONA_TITLES: dict[str, list[str]] = {
    "founder_seller":     ["CEO", "Co-Founder", "Founder", "CTO"],
    "first_sales_leader": ["VP Sales", "Head of Sales", "Founding AE", "VP Revenue", "Chief Revenue Officer"],
    "revops_growth":      ["RevOps", "Head of Revenue Operations", "Head of Growth", "Head of Operations", "Growth"],
}

# Default: cast wide to catch the most relevant person
_DEFAULT_TITLES = (
    PERSONA_TITLES["founder_seller"]
    + PERSONA_TITLES["first_sales_leader"]
    + PERSONA_TITLES["revops_growth"]
)


def _titles_for_account(account: dict) -> list[str]:
    """Return ordered title list based on account's target_persona field."""
    persona = account.get("target_persona", "")
    return PERSONA_TITLES.get(persona, _DEFAULT_TITLES)


# ─── Claude contact profiling ──────────────────────────────────────────────────

_PROFILE_SYSTEM = """\
You are a B2B sales intelligence analyst for DeployGTM, a GTM engineering
practice. You build contact profiles that help craft hyper-personalised
outreach — not generic cold emails.

You will receive:
- The contact's name, title, and LinkedIn URL (if known)
- The company's context: what they do, stage, pain hypothesis, company profile
- The ICP context for the client running this outreach

For each contact, respond in valid JSON with EXACTLY these fields:
{
  "pain_hypothesis": "<one sentence — their specific pain at THIS title in THIS company right now>",
  "conversation_hooks": [
    "<hook 1 — specific opener tied to their role + company signal>",
    "<hook 2 — alternative angle>"
  ],
  "seniority": "<executive|senior|mid|junior>",
  "influence_level": "<decision_maker|strong_influence|gatekeeper|end_user>",
  "likely_objections": [
    "<objection 1>",
    "<objection 2>"
  ],
  "outreach_tone": "<direct|consultative|peer>",
  "confidence": "<high|medium|low>"
}

Rules:
- Pain hypothesis must reference THEIR role, not the company's generic pain
- Conversation hooks must be specific enough to quote directly in an email opener
- No AI-sounding language. No "leveraging synergies." No "I hope this email finds you well."
- If you have low confidence due to sparse data, say so in the confidence field
"""


def _profile_contact(
    contact: dict,
    account: dict,
    client_context: str,
    api_key: Optional[str] = None,
) -> dict:
    """Call Claude to build a profile for one contact. Returns profile dict."""
    import anthropic

    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise click.ClickException("ANTHROPIC_API_KEY not set.")

    client_obj = anthropic.Anthropic(api_key=key)

    company_summary = {
        "company": account.get("company", ""),
        "domain": account.get("domain", ""),
        "what_they_do": account.get("company_profile", {}).get("what_they_do", ""),
        "stage": account.get("company_profile", {}).get("stage", ""),
        "employee_count": account.get("company_profile", {}).get("employee_count"),
        "gtm_signal": account.get("company_profile", {}).get("gtm_signal", ""),
        "pain_hypothesis": account.get("pain_hypothesis", ""),
        "why_now_signal": account.get("why_now_signal", {}),
        "fit_score": account.get("fit_score"),
    }

    user_content = f"""Contact:
  Name: {contact.get('name', 'Unknown')}
  Title: {contact.get('title', 'Unknown')}
  LinkedIn: {contact.get('linkedin_url', 'not available')}

Company context:
{json.dumps(company_summary, indent=2)}

Client ICP context (first 1000 chars):
{client_context[:1000]}
"""

    msg = client_obj.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": _PROFILE_SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_content}],
    )

    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


# ─── Per-account enrichment ────────────────────────────────────────────────────


def _load_context(client: str) -> str:
    context_path = REPO_ROOT / "projects" / client / "context.md"
    if context_path.exists():
        return context_path.read_text()[:4000]
    return ""


def enrich_account(
    account: dict,
    client_context: str,
    max_contacts: int = 4,
    dry_run: bool = False,
    verbose: bool = False,
    contact_delay: float = 0.5,
) -> list[dict]:
    """Find contacts + build profiles for one account. Mutates account in place."""
    from apollo import find_contacts

    domain = account.get("domain", "")
    company = account.get("company", "")

    titles = _titles_for_account(account)
    click.echo(f"  Enriching {company} ({domain})...")

    # 1. Find contacts via Apollo
    raw_contacts: list[dict] = []
    try:
        raw_contacts = find_contacts(domain, titles=titles, max_contacts=max_contacts)
        found = [c for c in raw_contacts if c.get("email")]
        click.echo(f"    Apollo: {len(found)} contact(s) found")
        if verbose:
            for c in found:
                click.echo(f"      {c['name']} — {c['title']} — {c['email']} ({c['confidence']})")
    except Exception as e:
        click.echo(f"    WARN Apollo find_contacts failed: {e}", err=True)

    if dry_run:
        click.echo("    (dry-run) skipping Claude profiling.")
        return raw_contacts

    # 2. Profile each contact via Claude
    profiled: list[dict] = []
    for contact in raw_contacts:
        if not contact.get("email"):
            profiled.append(contact)
            continue
        try:
            profile = _profile_contact(contact, account, client_context)
            enriched = {**contact, "profile": profile, "profiled_at": date.today().isoformat()}
            profiled.append(enriched)
            if verbose:
                click.echo(f"      Profiled {contact['name']}: {profile.get('influence_level', '?')}")
        except json.JSONDecodeError as e:
            click.echo(f"    WARN Claude returned invalid JSON for {contact['name']}: {e}", err=True)
            profiled.append(contact)
        except Exception as e:
            click.echo(f"    WARN profiling failed for {contact['name']}: {e}", err=True)
            profiled.append(contact)

        if contact_delay > 0:
            time.sleep(contact_delay)

    # 3. Write back to account
    account["contacts"] = profiled
    account["contacts_enriched_at"] = date.today().isoformat()

    return profiled


# ─── Batch runner ──────────────────────────────────────────────────────────────


def enrich_matrix(
    client: str,
    tiers: Optional[list[int]] = None,
    company_filter: Optional[str] = None,
    max_contacts: int = 4,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    delay: float = 1.0,
) -> list[str]:
    """Enrich all matching accounts. Returns list of enriched company names."""
    matrix = load_client_matrix(client)
    client_context = _load_context(client)
    enriched_companies: list[str] = []

    for account in matrix.get("accounts", []):
        if company_filter and account["company"].lower() != company_filter.lower():
            continue
        if tiers and account.get("icp_tier") not in tiers:
            continue
        if not force and account.get("contacts_enriched_at"):
            if verbose:
                click.echo(f"  Skipping {account['company']} (enriched {account['contacts_enriched_at']})")
            continue

        enrich_account(
            account,
            client_context,
            max_contacts=max_contacts,
            dry_run=dry_run,
            verbose=verbose,
            contact_delay=0.5,
        )
        enriched_companies.append(account["company"])

        if delay > 0:
            time.sleep(delay)

    if not dry_run and enriched_companies:
        path = _matrix_path(client)
        path.write_text(json.dumps(matrix, indent=2) + "\n")
        click.echo(f"\n  Saved {len(enriched_companies)} enriched account(s) to {path.name}.")

    return enriched_companies


# ─── CLI ─────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--client", required=True, help="Client slug.")
@click.option("--tier", "tier_str", default="1,2", show_default=True,
              help="Comma-separated tier filter.")
@click.option("--company", "company_filter", default=None,
              help="Enrich only this company (exact name match).")
@click.option("--max-contacts", default=4, show_default=True,
              help="Max contacts to find per account.")
@click.option("--force", is_flag=True,
              help="Re-enrich even if contacts_enriched_at is already set.")
@click.option("--dry-run", is_flag=True,
              help="Pull Apollo data but skip Claude profiling and writes.")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--delay", default=1.0, show_default=True,
              help="Seconds to wait between accounts.")
def main(
    client: str,
    tier_str: str,
    company_filter: Optional[str],
    max_contacts: int,
    force: bool,
    dry_run: bool,
    verbose: bool,
    delay: float,
):
    """Find contacts + build individual profiles for matrix accounts."""
    tiers = [int(t.strip()) for t in tier_str.split(",") if t.strip().isdigit()]

    click.echo(f"\nEnriching {client} contacts (tiers: {tiers})...")
    if dry_run:
        click.echo("(dry-run mode — no writes)")

    done = enrich_matrix(
        client=client,
        tiers=tiers,
        company_filter=company_filter,
        max_contacts=max_contacts,
        force=force,
        dry_run=dry_run,
        verbose=verbose,
        delay=delay,
    )

    click.echo(f"\nDone. Enriched {len(done)} account(s).")
    if done:
        click.echo("Next: run `make outreach-batch` to generate personalised variants.")


if __name__ == "__main__":
    main()
