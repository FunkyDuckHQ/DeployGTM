"""
DeployGTM — Signals to Matrix Bridge

Reads signals from data/signals_intake.csv (or any signals CSV) and adds
new accounts to a client's account matrix JSON. Claude ICP-scores each new
account against the client's context and assigns tier, persona, and angle.

Existing accounts (matched by domain) are updated if the incoming signal is
newer. Accounts already in active outreach (outreach_sent / replied /
meeting_booked) are never overwritten.

CSV format (output of scripts/signals.py):
  company, domain, signal_type, signal_date, signal_source, signal_summary

Usage:
  python scripts/signals_to_matrix.py --client deploygtm
  python scripts/signals_to_matrix.py --client deploygtm --input data/yc_w26_targets.csv
  python scripts/signals_to_matrix.py --client deploygtm --dry-run
  python scripts/signals_to_matrix.py --client deploygtm --no-score
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from typing import Optional

import click

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
PROJECTS_DIR = REPO_ROOT / "projects"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


# ─── Matrix path resolution (works with both platform and legacy layouts) ─────


def _matrix_path(client: str) -> Path:
    """Resolve accounts.json for a client. Tries platform layout first."""
    platform = PROJECTS_DIR / client / "platform" / "accounts.json"
    if platform.exists():
        return platform
    # Legacy: deploygtm-own/data/<client>_accounts.json
    normalized = client.replace("-", "_")
    legacy = REPO_ROOT / "projects" / "deploygtm-own" / "data" / f"{normalized}_accounts.json"
    if legacy.exists():
        return legacy
    # Default to platform layout (will be created on first write)
    return platform


def load_client_matrix(client: str) -> dict:
    path = _matrix_path(client)
    if not path.exists():
        return {"client_name": client, "accounts": []}
    return json.loads(path.read_text())


# ─── Constants ────────────────────────────────────────────────────────────────

# Map CSV signal_type values → matrix schema enum
_SIGNAL_MAP = {
    "funding": "funding",
    "funded": "funding",
    "seed": "funding",
    "series_a": "funding",
    "series_b": "funding",
    "raise": "funding",
    "hiring": "hiring",
    "sdr_hire": "hiring",
    "bdr_hire": "hiring",
    "ae_hire": "hiring",
    "sales_hire": "hiring",
    "leadership_change": "leadership_change",
    "new_cro": "leadership_change",
    "new_vp_sales": "leadership_change",
    "acquisition": "acquisition",
    "product_launch": "product_launch",
    "conference": "conference_signal",
    "conference_signal": "conference_signal",
    "sbir": "sbir_award",
    "sbir_award": "sbir_award",
    "contract": "contract_award",
    "contract_award": "contract_award",
    "program": "program_announcement",
    "manual": "manual",
}

# Statuses that protect an account from being overwritten
_PROTECTED = {"outreach_sent", "replied", "meeting_booked"}


# ─── CSV helpers ──────────────────────────────────────────────────────────────


def read_signals_csv(path: Path) -> list[dict]:
    """Read a signals CSV and return normalized rows."""
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # Normalize keys: strip whitespace + lowercase
            normalized = {k.strip().lower(): (v or "").strip() for k, v in row.items()}
            if normalized.get("domain") or normalized.get("company"):
                rows.append(normalized)
    return rows


def _norm_domain(domain: str) -> str:
    return domain.strip().lower().removeprefix("www.").rstrip("/")


def _norm_signal_type(raw: str) -> str:
    key = raw.strip().lower().replace("-", "_").replace(" ", "_")
    return _SIGNAL_MAP.get(key, "manual")


# ─── Matrix helpers ───────────────────────────────────────────────────────────


def _find_by_domain(matrix: dict, domain: str) -> Optional[dict]:
    norm = _norm_domain(domain)
    for account in matrix.get("accounts", []):
        if _norm_domain(account.get("domain", "")) == norm:
            return account
    return None


def _build_stub(row: dict) -> dict:
    """Build a minimal schema-valid account stub from a CSV row."""
    return {
        "company": row.get("company") or "VERIFY",
        "domain": _norm_domain(row.get("domain", "")),
        "icp_tier": 2,
        "market": "VERIFY",
        "segment": "VERIFY",
        "persona": "founder_seller",
        "angle": "VERIFY",
        "why_now_signal": {
            "type": _norm_signal_type(row.get("signal_type", "manual")),
            "date": row.get("signal_date") or "VERIFY",
            "description": row.get("signal_summary") or "VERIFY",
            "source": row.get("signal_source", ""),
        },
        "product_fit": "VERIFY",
        "heritage_risk": "none",
        "status": "monitor",
    }


# ─── ICP scoring via Claude ───────────────────────────────────────────────────


def _score_batch(
    stubs: list[dict],
    client_context: str,
    api_key: Optional[str] = None,
) -> list[Optional[dict]]:
    """Score a batch of account stubs via Claude. Returns list of score dicts or None (disqualify)."""
    import anthropic  # type: ignore

    ai = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    # Compact representation for prompt — strip VERIFY noise
    compact = [
        {
            "company": s["company"],
            "domain": s["domain"],
            "signal_type": s["why_now_signal"]["type"],
            "signal_date": s["why_now_signal"]["date"],
            "signal_summary": s["why_now_signal"]["description"],
        }
        for s in stubs
    ]

    system = f"""You are the DeployGTM ICP scoring engine.

CLIENT CONTEXT:
{client_context}

For each account, assign:
- icp_tier: 1 (excellent fit), 2 (good fit), 3 (monitor only). Return null to disqualify.
- persona: "founder_seller", "first_sales_leader", or "revops_growth"
- angle: 8-12 word outreach angle specific to their signal and pain
- product_fit: one sentence — why DeployGTM's service fits their situation
- market: their market (e.g. "developer tools", "fintech", "healthtech")
- segment: "just_raised", "first_sales_hire", "clay_no_results", "churned_agency", or "solo_revops"

Tier rules:
- Tier 1: recent Seed/A + clear ICP fit (B2B SaaS, 5-30 employees, technical buyer)
- Tier 2: good ICP fit with moderate or slightly older signal
- Tier 3: marginal fit or weak signal — monitor for stronger trigger
- null: disqualify — B2C, enterprise-only, pre-product, wrong stage

Return JSON array only, same length and order as input:
[{{"icp_tier": 1, "persona": "...", "angle": "...", "product_fit": "...", "market": "...", "segment": "..."}}]
Use null for disqualified accounts."""

    user = f"Score these accounts:\n\n{json.dumps(compact, indent=2)}"

    response = ai.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(raw)


def _apply_scores(stubs: list[dict], scores: list[Optional[dict]]) -> tuple[list[dict], list[str]]:
    """Apply Claude scores to stubs. Returns (scored_accounts, disqualified_domains)."""
    scored = []
    disqualified = []

    for stub, score in zip(stubs, scores):
        if score is None:
            disqualified.append(stub["domain"])
            continue
        stub["icp_tier"] = score.get("icp_tier", 2)
        stub["persona"] = score.get("persona", "founder_seller")
        stub["angle"] = score.get("angle", "VERIFY")
        stub["product_fit"] = score.get("product_fit", "VERIFY")
        stub["market"] = score.get("market", "VERIFY")
        stub["segment"] = score.get("segment", "VERIFY")
        scored.append(stub)

    return scored, disqualified


# ─── Main logic ────────────────────────────────────────────────────────────────


def run_bridge(
    client: str,
    input_path: Path,
    dry_run: bool = False,
    no_score: bool = False,
    batch_size: int = 10,
) -> dict:
    """Bridge signals CSV → client matrix. Returns result summary."""
    matrix = load_client_matrix(client)
    rows = read_signals_csv(input_path)

    added: list[dict] = []
    updated: list[str] = []
    skipped: list[dict] = []
    disqualified: list[str] = []

    new_stubs: list[dict] = []

    for row in rows:
        domain = _norm_domain(row.get("domain", ""))
        company = row.get("company", "")

        if not domain and not company:
            skipped.append({"reason": "empty row"})
            continue

        existing = _find_by_domain(matrix, domain) if domain else None

        if existing:
            if existing.get("status") in _PROTECTED:
                skipped.append({"reason": f"protected status={existing['status']}", "domain": domain})
                continue

            # Update signal if the incoming one is more recent
            new_date = row.get("signal_date", "")
            old_date = existing.get("why_now_signal", {}).get("date", "")
            if new_date and new_date > old_date:
                sig = existing.setdefault("why_now_signal", {})
                sig["date"] = new_date
                sig["description"] = row.get("signal_summary") or sig.get("description", "")
                sig["type"] = _norm_signal_type(row.get("signal_type", "manual"))
                sig["source"] = row.get("signal_source", sig.get("source", ""))
                updated.append(domain)
            else:
                skipped.append({"reason": "already in matrix, signal not newer", "domain": domain})
        else:
            new_stubs.append(_build_stub(row))

    # Score new accounts in batches
    if new_stubs and not no_score:
        context_path = PROJECTS_DIR / client / "context.md"
        client_context = context_path.read_text() if context_path.exists() else ""

        click.echo(f"  Scoring {len(new_stubs)} new account(s) with Claude...")

        for i in range(0, len(new_stubs), batch_size):
            batch = new_stubs[i : i + batch_size]
            click.echo(f"  Batch {i // batch_size + 1}: {len(batch)} account(s)...")
            scores = _score_batch(batch, client_context)
            scored, dis = _apply_scores(batch, scores)
            added.extend(scored)
            disqualified.extend(dis)

        for stub in added:
            matrix.setdefault("accounts", []).append(stub)

    elif new_stubs:
        # --no-score: add all stubs with VERIFY markers for manual review
        for stub in new_stubs:
            added.append(stub)
            matrix.setdefault("accounts", []).append(stub)

    if not dry_run and (added or updated):
        path = _matrix_path(client)
        path.write_text(json.dumps(matrix, indent=2) + "\n")

    return {
        "added": len(added),
        "updated": len(updated),
        "skipped": len(skipped),
        "disqualified": len(disqualified),
        "added_accounts": added,
    }


# ─── CLI ─────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--client", required=True, help="Client slug.")
@click.option("--input", "input_path",
              default="data/signals_intake.csv", show_default=True,
              type=click.Path(), help="Signals CSV file.")
@click.option("--dry-run", is_flag=True,
              help="Show what would be added without writing.")
@click.option("--no-score", is_flag=True,
              help="Skip Claude ICP scoring. Add all accounts with VERIFY markers.")
@click.option("--batch-size", default=10, show_default=True,
              help="Accounts per Claude scoring batch.")
def main(
    client: str,
    input_path: str,
    dry_run: bool,
    no_score: bool,
    batch_size: int,
):
    """Bridge a signals CSV into a client's account matrix JSON."""
    path = Path(input_path)
    if not path.exists():
        raise click.ClickException(f"Input file not found: {path}")

    click.echo(f"\nBridging signals → matrix  |  client: {client}")
    click.echo(f"Input: {path}")
    if dry_run:
        click.echo("(dry-run — nothing will be written)\n")
    if no_score:
        click.echo("(--no-score: accounts added with VERIFY markers)\n")

    result = run_bridge(
        client, path,
        dry_run=dry_run,
        no_score=no_score,
        batch_size=batch_size,
    )

    click.echo(f"\nResults:")
    click.echo(f"  Added:        {result['added']}")
    click.echo(f"  Updated:      {result['updated']}")
    click.echo(f"  Skipped:      {result['skipped']}")
    click.echo(f"  Disqualified: {result['disqualified']}")

    if result["added_accounts"]:
        click.echo(f"\nNew accounts:")
        for a in result["added_accounts"]:
            tier = a.get("icp_tier", "?")
            verify = " [VERIFY]" if a.get("market") == "VERIFY" else ""
            click.echo(f"  [T{tier}] {a['company']} ({a['domain']}){verify}")

    if not dry_run and (result["added"] or result["updated"]):
        click.echo(f"\nNext: make verify-signals CLIENT={client}")


if __name__ == "__main__":
    main()
