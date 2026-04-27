"""
DeployGTM — Engagement Intake

Starts a new client engagement (or DeployGTM's own outbound campaign) by
researching the company and building a populated context.md. The AI does
the research — you provide the company name, domain, and what you've been
hired to do. Everything else is inferred, researched, or flagged for review.

context.md entries are labeled:
  [confirmed]  — from a document you provided or Drive
  [researched] — from live website fetch or AI knowledge
  [inferred]   — AI reasoning, needs your review

Usage:
  # New client engagement
  python scripts/engage.py \\
    --client peregrine-space --domain peregrine.space \\
    --objective "Build their outbound targeting NewSpace prime contractors. Weekly Slack digest."

  # DeployGTM's own outbound
  python scripts/engage.py \\
    --client deploygtm-own --domain deploygtm.com \\
    --objective "Find Signal Audit clients. Seed-A founders who just raised or are hiring sales."

  # Fetch live website for richer research
  python scripts/engage.py --client acme --domain acme.com --fetch \\
    --objective "..."

  # Explicit CRM
  python scripts/engage.py --client acme --domain acme.com --crm salesforce \\
    --objective "..."
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import click

REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECTS_DIR = REPO_ROOT / "projects"

if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


# ─── Website fetcher ──────────────────────────────────────────────────────────


def _fetch_website(domain: str, timeout: int = 10) -> str:
    """Fetch the company website and return cleaned text (best-effort)."""
    import re
    try:
        import requests  # type: ignore
    except ImportError:
        return ""

    pages_to_try = [
        f"https://{domain}",
        f"https://{domain}/about",
        f"https://{domain}/product",
        f"https://{domain}/pricing",
    ]

    combined = []
    for url in pages_to_try:
        try:
            resp = requests.get(url, timeout=timeout, headers={
                "User-Agent": "Mozilla/5.0 (compatible; DeployGTM-research/1.0)"
            })
            if resp.status_code == 200:
                # Strip HTML tags and collapse whitespace
                text = re.sub(r"<[^>]+>", " ", resp.text)
                text = re.sub(r"\s+", " ", text).strip()
                combined.append(f"[{url}]\n{text[:3000]}")
        except Exception:
            continue

    return "\n\n".join(combined)


# ─── Drive sync ───────────────────────────────────────────────────────────────


def _try_drive_sync(client: str) -> str:
    """Attempt to sync Drive docs. Returns summary message."""
    intake_folder_id = os.environ.get("GDRIVE_INTAKE_FOLDER_ID")
    if not intake_folder_id:
        return "Drive sync skipped (GDRIVE_INTAKE_FOLDER_ID not set)"

    try:
        from sync_client_context import sync_context  # type: ignore
        count = sync_context(client, dry_run=False)
        if count:
            return f"Drive sync: {count} file(s) pulled"
        return "Drive sync: no new files"
    except Exception as exc:
        return f"Drive sync skipped: {exc}"


# ─── Claude research ──────────────────────────────────────────────────────────


_RESEARCH_SYSTEM = """You are building a GTM engagement context file for DeployGTM.

DeployGTM is a GTM engineering practice. We build outbound pipeline infrastructure
for early-stage B2B SaaS companies. We research clients to understand:
  1. Who they are and what they sell
  2. Who their buyers are (ICP — title, company size, industry, pain points)
  3. What signals indicate a buyer is ready to purchase
  4. What their current GTM stack looks like
  5. What we've been hired to deliver for them

Label every piece of information with one of:
  [confirmed]  — explicitly stated in docs or objective
  [researched] — from provided website content or well-established public knowledge
  [inferred]   — AI reasoning from available signals, needs human review

Output a complete context.md in markdown. Use this structure exactly:

# <Company Name> — Engagement Context

## Status
- Engagement started: <today>
- Type: <Signal Audit | Pipeline Engine Retainer | Internal — own outbound | Other>
- CRM: <detected or "unknown">
- Objective: <verbatim from input>

## About the Company
[1-3 sentences: what they make, their stage, market position]

## Their ICP (Who They Sell To)
- **Buyer titles:** [title list]
- **Company profile:** [size, stage, industry]
- **Key pain points:** [2-4 bullets]
- **Buying trigger:** [what makes them ready to buy]

## Signals to Monitor
[5-8 signals specific to this company's buyer, ranked by relevance]
- Signal type | Why it indicates buying intent | How to detect it

## Their Stack
- CRM: [detected or unknown]
- Outreach: [detected or unknown]
- Other tools: [detected or unknown]

## Key People
[Any contacts mentioned in objective or docs]

## Engagement Objectives
[Verbatim from objective input]

## Work Breakdown
[Derived from objectives — what needs to happen to deliver this]
| # | Task | Owner | Status | Notes |
|---|------|-------|--------|-------|
[Fill with derived tasks]

## Deliverables Checklist
[Concrete outputs Matthew owes the client, with due dates if known]
- [ ] [deliverable]

## Tracking Log
| Date | Action | Result | Learning |
|------|--------|--------|----------|
| <today> | Engagement started | context.md created | |

End the file with a line: `crm: <type>` (lowercase, one of: hubspot, salesforce, attio, pipedrive, csv, none, unknown)"""


def _build_context(
    client: str,
    domain: str,
    objective: str,
    crm_hint: Optional[str],
    website_content: str,
    existing_context: str,
    api_key: Optional[str] = None,
) -> str:
    """Call Claude to research the company and build context.md."""
    import anthropic  # type: ignore

    ai = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    sections = [
        f"CLIENT SLUG: {client}",
        f"DOMAIN: {domain}",
        f"TODAY: {date.today().isoformat()}",
        f"OBJECTIVE (what Matthew has been hired to do):\n{objective}",
    ]

    if crm_hint:
        sections.append(f"CRM (provided explicitly): {crm_hint}")

    if website_content:
        sections.append(f"LIVE WEBSITE CONTENT:\n{website_content[:6000]}")

    if existing_context:
        sections.append(f"EXISTING CONTEXT / DRIVE DOCS:\n{existing_context[:4000]}")

    user = "\n\n".join(sections) + "\n\nBuild the context.md now."

    response = ai.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=[{
            "type": "text",
            "text": _RESEARCH_SYSTEM,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user}],
        thinking={"type": "adaptive"},
    )

    for block in response.content:
        if block.type == "text":
            return block.text.strip()

    return ""


# ─── Main logic ───────────────────────────────────────────────────────────────


def run_engage(
    client: str,
    domain: str,
    objective: str,
    crm: Optional[str] = None,
    fetch: bool = False,
    force: bool = False,
) -> Path:
    """Run the full engagement intake. Returns path to written context.md."""
    client_dir = PROJECTS_DIR / client
    context_path = client_dir / "context.md"

    # Create project directory if it doesn't exist
    client_dir.mkdir(parents=True, exist_ok=True)

    if context_path.exists() and not force:
        click.echo(
            f"  context.md already exists for '{client}'.\n"
            f"  Use --force to overwrite, or edit it directly."
        )
        raise click.ClickException(
            f"Engagement already started for '{client}'. Use --force to rebuild."
        )

    # 1. Drive sync (best-effort)
    click.echo("Syncing Google Drive...")
    drive_msg = _try_drive_sync(client)
    click.echo(f"  {drive_msg}")

    # 2. Read any existing context (from Drive sync)
    existing_context = context_path.read_text() if context_path.exists() else ""

    # 3. Fetch website (optional)
    website_content = ""
    if fetch:
        click.echo(f"Fetching {domain}...")
        website_content = _fetch_website(domain)
        pages = website_content.count("[http")
        click.echo(f"  Fetched {pages} page(s) ({len(website_content)} chars)")
    else:
        click.echo(f"  (Use --fetch to pull live website content for richer research)")

    # 4. Research + build context.md
    click.echo(f"\nResearching {domain} with Claude...")
    context_md = _build_context(
        client=client,
        domain=domain,
        objective=objective,
        crm_hint=crm,
        website_content=website_content,
        existing_context=existing_context,
    )

    if not context_md:
        raise click.ClickException("Claude returned empty context. Check API key and try again.")

    # 5. Write context.md
    context_path.write_text(context_md + "\n")
    click.echo(f"  Written: {context_path}")

    # 6. Scaffold matrix stub if it doesn't exist
    _scaffold_matrix(client, domain)

    return context_path


def _scaffold_matrix(client: str, domain: str) -> None:
    """Create an empty accounts.json stub if one doesn't exist for this client."""
    matrix_scripts_dir = REPO_ROOT / "projects" / "deploygtm-own" / "scripts"
    if str(matrix_scripts_dir) not in sys.path:
        sys.path.insert(0, str(matrix_scripts_dir))

    try:
        from init_matrix import target_path, stub  # type: ignore
        path = target_path(client)
        if not path.exists():
            path.write_text(json.dumps(stub(client), indent=2) + "\n")
            click.echo(f"  Scaffolded: {path.name}")
    except Exception:
        pass  # Matrix scaffold is best-effort; doesn't block engagement start


# ─── CLI ─────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--client", required=True,
              help="Client slug (also used as project directory name).")
@click.option("--domain", required=True,
              help="Company domain (e.g. acme.com).")
@click.option("--objective", required=True,
              help="What you've been hired to do. Free-form. "
                   "E.g. 'Build their outbound targeting fintech CTOs. Weekly report.'")
@click.option("--crm", default=None,
              help="Client's CRM type: hubspot | salesforce | attio | pipedrive | csv | none. "
                   "Auto-detected from research if omitted.")
@click.option("--fetch", is_flag=True,
              help="Fetch the company website for richer research context.")
@click.option("--force", is_flag=True,
              help="Overwrite an existing context.md.")
def main(
    client: str,
    domain: str,
    objective: str,
    crm: Optional[str],
    fetch: bool,
    force: bool,
):
    """Start a new client engagement. Researches the company and builds context.md."""
    click.echo(f"\nStarting engagement: {client} ({domain})")
    click.echo(f"Objective: {objective[:80]}{'...' if len(objective) > 80 else ''}\n")

    context_path = run_engage(
        client=client,
        domain=domain,
        objective=objective,
        crm=crm,
        fetch=fetch,
        force=force,
    )

    click.echo(f"\nEngagement ready.")
    click.echo(f"  Review:  {context_path}")
    click.echo(f"  Next:    make signals-to-matrix CLIENT={client}")
    click.echo(f"  Or:      make verify-signals CLIENT={client}")


if __name__ == "__main__":
    main()
