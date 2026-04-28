"""
DeployGTM — Company Research + ICP Fit Scoring

For each account in the matrix that hasn't been researched yet (or --force),
this script:
  1. Pulls firmographic data via Apollo enrich_company
  2. Fetches a short web snapshot of the company's site
  3. Asks Claude to evaluate ICP fit across five dimensions and produce a
     fit_score (0–10), pain_hypothesis, fit_rationale, and company_profile
  4. Writes fit_score + research fields back to accounts.json
  5. Triggers score_engine.apply_score so current_score is immediately
     updated to reflect the new fit_score

fit_score dimensions (Claude evaluates each 0–2, sum = 0–10):
  1. Stage fit       — Seed/A is ideal; pre-revenue or Series B+ penalised
  2. Size fit        — 5–30 employees ideal
  3. Tech signals    — SaaS stack, Clay/Apollo present, modern tooling
  4. GTM maturity    — founder-led or just hired first AE, no pipeline infra
  5. Buyer type      — technical + business buyer (both present)

Usage:
  python projects/deploygtm-own/scripts/research_accounts.py \\
      --client deploygtm --tier 1,2

  # Force re-research even if already researched
  python projects/deploygtm-own/scripts/research_accounts.py \\
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
import requests

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

from generate_outreach import _matrix_path, load_client_matrix, find_account  # noqa: E402
from score_engine import set_fit_score  # noqa: E402


# ─── Web snapshot ─────────────────────────────────────────────────────────────

_HTML_TAG = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s{2,}")
_FETCH_TIMEOUT = 8
_FETCH_PATHS = ["/", "/about", "/product", "/pricing"]


def _fetch_web_snapshot(domain: str, max_chars: int = 3000) -> str:
    """Return stripped text from the company's homepage (best-effort)."""
    base = domain.rstrip("/")
    if not base.startswith("http"):
        base = f"https://{base}"

    headers = {"User-Agent": "Mozilla/5.0 (compatible; DeployGTM-research/1.0)"}
    chunks: list[str] = []

    for path in _FETCH_PATHS:
        if sum(len(c) for c in chunks) >= max_chars:
            break
        try:
            resp = requests.get(f"{base}{path}", headers=headers,
                                timeout=_FETCH_TIMEOUT, allow_redirects=True)
            if resp.status_code == 200:
                text = _HTML_TAG.sub(" ", resp.text)
                text = _WHITESPACE.sub(" ", text).strip()
                chunks.append(text[:1000])
        except Exception:
            continue

    return "\n\n".join(chunks)[:max_chars] if chunks else ""


# ─── Claude research call ──────────────────────────────────────────────────────

_RESEARCH_SYSTEM = """\
You are a B2B GTM analyst helping DeployGTM evaluate whether a company is an
ideal client for a GTM engineering practice.

DeployGTM's ideal client:
- B2B SaaS, Seed to Series A
- 5–30 employees
- Founder still doing sales OR just hired first 1–2 AEs
- No repeatable pipeline infrastructure yet
- Buying or open to HubSpot
- Technical or enterprise buyers

You will receive:
- Firmographic data from Apollo (may be partial)
- A short web snapshot (may be empty if blocked)
- The client's ICP context

Respond in valid JSON with EXACTLY these fields:
{
  "fit_score": <number 0–10, one decimal>,
  "fit_dimensions": {
    "stage_fit":    <0–2>,
    "size_fit":     <0–2>,
    "tech_signals": <0–2>,
    "gtm_maturity": <0–2>,
    "buyer_type":   <0–2>
  },
  "pain_hypothesis": "<one sentence — what's their most likely GTM pain right now>",
  "fit_rationale": "<two sentences — why this score>",
  "company_profile": {
    "what_they_do": "<one sentence>",
    "stage": "<seed|series_a|series_b_plus|bootstrap|unknown>",
    "employee_count": <integer or null>,
    "tech_stack_signals": ["<tool1>", "<tool2>"],
    "gtm_signal": "<what the web/data tells us about their GTM motion>"
  },
  "confidence": "<high|medium|low>"
}

Label your inferences:
- [confirmed] = from Apollo or official company data
- [researched] = from the web snapshot
- [inferred] = your judgment from partial signals
"""


def _research_with_claude(
    account: dict,
    firmographics: dict,
    web_snapshot: str,
    client_context: str,
    api_key: Optional[str] = None,
) -> dict:
    """Call Claude to produce fit_score and company profile. Returns parsed dict."""
    import anthropic

    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise click.ClickException("ANTHROPIC_API_KEY not set.")

    client_obj = anthropic.Anthropic(api_key=key)

    user_content = f"""Company: {account['company']}
Domain: {account['domain']}

Apollo firmographics:
{json.dumps(firmographics, indent=2)}

Web snapshot (first {len(web_snapshot)} chars):
{web_snapshot or '[no web content retrieved]'}

Client ICP context (first 1500 chars):
{client_context[:1500]}
"""

    msg = client_obj.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": _RESEARCH_SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_content}],
    )

    raw = msg.content[0].text.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


# ─── Per-account research ──────────────────────────────────────────────────────


def _load_context(client: str) -> str:
    """Load context.md for the client, return as string (best-effort)."""
    context_path = REPO_ROOT / "projects" / client / "context.md"
    if context_path.exists():
        return context_path.read_text()[:4000]
    return ""


def research_account(
    account: dict,
    client_context: str,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """Research one account: Apollo → web → Claude → set fit_score.

    Modifies account in place. Returns the research result dict from Claude.
    """
    domain = account.get("domain", "")
    company = account.get("company", "")

    click.echo(f"  Researching {company} ({domain})...")

    # 1. Apollo firmographics
    firmographics: dict = {}
    try:
        from apollo import enrich_company
        firmographics = enrich_company(domain)
        if verbose:
            click.echo(f"    Apollo: {firmographics.get('industry', '?')}, "
                       f"{firmographics.get('employee_count', '?')} employees, "
                       f"stage={firmographics.get('funding_stage', '?')}")
    except Exception as e:
        click.echo(f"    WARN Apollo enrichment failed: {e}", err=True)

    # 2. Web snapshot
    web_snapshot = ""
    try:
        web_snapshot = _fetch_web_snapshot(domain)
        if verbose:
            click.echo(f"    Web snapshot: {len(web_snapshot)} chars")
    except Exception as e:
        click.echo(f"    WARN web fetch failed: {e}", err=True)

    if dry_run:
        click.echo(f"    (dry-run) skipping Claude call.")
        return {}

    # 3. Claude research
    try:
        result = _research_with_claude(account, firmographics, web_snapshot, client_context)
    except json.JSONDecodeError as e:
        click.echo(f"    ERROR: Claude returned invalid JSON: {e}", err=True)
        return {}
    except Exception as e:
        click.echo(f"    ERROR: Claude research failed: {e}", err=True)
        return {}

    # 4. Write back to account
    fit_score = float(result.get("fit_score", 0))
    rationale = result.get("fit_rationale", "")

    account["fit_score"] = round(min(10.0, max(0.0, fit_score)), 2)
    account["pain_hypothesis"] = result.get("pain_hypothesis", "")
    account["fit_rationale"] = rationale
    account["fit_dimensions"] = result.get("fit_dimensions", {})
    account["company_profile"] = result.get("company_profile", {})
    account["research_confidence"] = result.get("confidence", "low")
    account["researched_at"] = date.today().isoformat()

    # Update firmographics if Apollo returned data
    if firmographics and not firmographics.get("error"):
        account.setdefault("firmographics", {}).update(firmographics)

    # 5. Recompute score
    set_fit_score(account, fit_score, rationale=f"research_{date.today().isoformat()}")

    click.echo(
        f"    fit_score={account['fit_score']}  "
        f"score={account.get('current_score', '?')}  "
        f"confidence={account['research_confidence']}"
    )

    return result


# ─── Batch runner ─────────────────────────────────────────────────────────────


def research_matrix(
    client: str,
    tiers: Optional[list[int]] = None,
    company_filter: Optional[str] = None,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    delay: float = 1.0,
) -> list[str]:
    """Research all matching accounts. Returns list of researched company names."""
    matrix = load_client_matrix(client)
    client_context = _load_context(client)
    researched: list[str] = []

    for account in matrix.get("accounts", []):
        # Filter: company name
        if company_filter and account["company"].lower() != company_filter.lower():
            continue

        # Filter: tiers
        if tiers and account.get("icp_tier") not in tiers:
            continue

        # Skip if already researched (unless --force)
        if not force and account.get("researched_at"):
            if verbose:
                click.echo(f"  Skipping {account['company']} (researched {account['researched_at']})")
            continue

        research_account(account, client_context, dry_run=dry_run, verbose=verbose)
        researched.append(account["company"])

        if delay > 0:
            time.sleep(delay)

    if not dry_run and researched:
        path = _matrix_path(client)
        path.write_text(json.dumps(matrix, indent=2) + "\n")
        click.echo(f"\n  Saved {len(researched)} researched account(s) to {path.name}.")

    return researched


# ─── CLI ─────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--client", required=True, help="Client slug.")
@click.option("--tier", "tier_str", default="1,2", show_default=True,
              help="Comma-separated tier filter (e.g. 1 or 1,2).")
@click.option("--company", "company_filter", default=None,
              help="Research only this company (exact name match).")
@click.option("--force", is_flag=True,
              help="Re-research even if researched_at is already set.")
@click.option("--dry-run", is_flag=True,
              help="Pull Apollo + web data but skip Claude call and writes.")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--delay", default=1.0, show_default=True,
              help="Seconds to wait between Claude calls.")
def main(
    client: str,
    tier_str: str,
    company_filter: Optional[str],
    force: bool,
    dry_run: bool,
    verbose: bool,
    delay: float,
):
    """Research accounts via Apollo + web + Claude and set fit_score."""
    tiers = [int(t.strip()) for t in tier_str.split(",") if t.strip().isdigit()]

    click.echo(f"\nResearching {client} accounts (tiers: {tiers})...")
    if dry_run:
        click.echo("(dry-run mode — no writes)")

    done = research_matrix(
        client=client,
        tiers=tiers,
        company_filter=company_filter,
        force=force,
        dry_run=dry_run,
        verbose=verbose,
        delay=delay,
    )

    click.echo(f"\nDone. Researched {len(done)} account(s).")
    if done:
        click.echo("Next: run `make enrich-contacts` to find key contacts.")


if __name__ == "__main__":
    main()
