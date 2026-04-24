"""
DeployGTM — Batch Outreach Variant Generator

Runs the single-account generator across every tier-1 (or filtered subset) of
accounts in a client's matrix in one shot. Reuses a single Anthropic client so
the cached system prompt (voice_notes + hard rules) is served from cache on
every call after the first.

Usage:
  python projects/deploygtm-own/scripts/batch_outreach.py --client peregrine-space
  python projects/deploygtm-own/scripts/batch_outreach.py --client peregrine-space --tier 1,2
  python projects/deploygtm-own/scripts/batch_outreach.py --client peregrine-space --limit 3 --dry-run

Output:
  One .txt per account in projects/deploygtm-own/outputs/<client>/.
  Cache hit stats printed at the end.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import click

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed. Run: pip install anthropic", file=sys.stderr)
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_outreach import (  # noqa: E402
    MODEL,
    build_prompts,
    find_account,
    format_output,
    load_client_matrix,
    log_variant_to_tracker,
    parse_variants,
    word_count,
    write_output,
)
from verify_signals import audit_account  # noqa: E402


def _parse_tiers(raw: str) -> set[int]:
    tiers: set[int] = set()
    for piece in raw.split(","):
        piece = piece.strip()
        if not piece:
            continue
        if piece not in {"1", "2", "3"}:
            raise click.BadParameter(f"--tier values must be 1, 2, or 3 (got {piece!r})")
        tiers.add(int(piece))
    if not tiers:
        raise click.BadParameter("--tier must contain at least one tier")
    return tiers


def _filter_accounts(matrix: dict, tiers: set[int]) -> list[dict]:
    return [a for a in matrix.get("accounts", []) if a.get("icp_tier") in tiers]


def _call_once(client: anthropic.Anthropic, system: str, user: str):
    """One cached request. Returns (text, usage_dict)."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    )
    usage = {
        "input":          getattr(resp.usage, "input_tokens", 0),
        "output":         getattr(resp.usage, "output_tokens", 0),
        "cache_read":     getattr(resp.usage, "cache_read_input_tokens", 0) or 0,
        "cache_creation": getattr(resp.usage, "cache_creation_input_tokens", 0) or 0,
    }
    return resp.content[0].text.strip(), usage


@click.command()
@click.option("--client", required=True, help="Client slug (matches client_name in matrix).")
@click.option("--tier", default="1", show_default=True,
              help="Comma-separated tier filter (e.g. '1' or '1,2').")
@click.option("--limit", type=int, default=None,
              help="Process at most N accounts (useful for smoke tests).")
@click.option("--dry-run", is_flag=True, help="List accounts and skip the API calls.")
@click.option("--no-write", is_flag=True, help="Print outputs instead of writing to disk.")
@click.option("--log-variant", type=click.IntRange(1, 3), default=None,
              help="Log variant N for every account to the tracker DB.")
@click.option("--force", is_flag=True,
              help="Run even on accounts with unresolved VERIFY/FILL IN markers.")
def main(client: str, tier: str, limit: Optional[int], dry_run: bool,
         no_write: bool, log_variant: Optional[int], force: bool):
    """Generate outreach variants across every account in a tier filter."""
    tiers = _parse_tiers(tier)
    matrix = load_client_matrix(client)
    accounts = _filter_accounts(matrix, tiers)

    if limit is not None:
        accounts = accounts[:limit]

    if not accounts:
        raise click.ClickException(f"No accounts match tier filter {sorted(tiers)}.")

    # Split ready vs. blocked. Skip blocked unless --force.
    ready: list[dict] = []
    skipped: list[tuple[dict, list[str]]] = []
    for a in accounts:
        issues = audit_account(a)
        if issues and not force:
            skipped.append((a, issues))
        else:
            ready.append(a)

    click.echo(f"Client:   {matrix.get('client_name')}")
    click.echo(f"Tiers:    {sorted(tiers)}")
    click.echo(f"Accounts: {len(accounts)} ({len(ready)} ready, {len(skipped)} skipped)")
    for a in ready:
        click.echo(f"  - [T{a.get('icp_tier')}] {a.get('company')} "
                   f"({a.get('why_now_signal', {}).get('type', '?')})")
    if skipped:
        click.echo("")
        click.echo("SKIPPED (run `make verify-signals CLIENT=" + client +
                   "` for details, or re-run with --force):")
        for a, issues in skipped:
            click.echo(f"  - {a.get('company')}: {', '.join(issues)}")

    if not ready:
        click.echo("\nNothing to generate. Resolve blockers or pass --force.")
        return

    accounts = ready  # only process ready accounts from here on

    if dry_run:
        click.echo("\n(dry-run — no API calls)")
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise click.ClickException("ANTHROPIC_API_KEY not set. Add it to .env or your shell.")

    api = anthropic.Anthropic()

    totals = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0}
    ok = 0
    failed: list[tuple[str, str]] = []

    click.echo("")
    for idx, account in enumerate(accounts, start=1):
        company = account.get("company", "<unknown>")
        click.echo(f"[{idx}/{len(accounts)}] {company}")
        try:
            system, user = build_prompts(matrix, account)
            raw, usage = _call_once(api, system, user)
            for k in totals:
                totals[k] += usage.get(k, 0)

            variants = parse_variants(raw)
            for i, v in enumerate(variants, start=1):
                wc = word_count(v.get("body", ""))
                flag = " [OVER 75]" if wc > 75 else ""
                click.echo(f"    v{i}: {wc}w{flag} — {v.get('angle_label', '')}")

            content = format_output(matrix, account, variants)
            if no_write:
                click.echo("\n" + content + "\n")
            else:
                out_path = write_output(client, company, content)
                try:
                    rel = out_path.relative_to(Path.cwd())
                except ValueError:
                    rel = out_path
                click.echo(f"    saved: {rel}")

            if log_variant is not None:
                chosen = variants[log_variant - 1]
                rid = log_variant_to_tracker(client, company, chosen)
                if rid:
                    click.echo(f"    logged v{log_variant} (id={rid})")

            ok += 1
        except Exception as e:
            click.echo(f"    FAILED: {e}", err=True)
            failed.append((company, str(e)))

    click.echo("")
    click.echo("=" * 60)
    click.echo(f"Done: {ok}/{len(accounts)} succeeded")
    if failed:
        click.echo(f"Failures: {len(failed)}")
        for company, err in failed:
            click.echo(f"  - {company}: {err}")
    click.echo("")
    click.echo("Token usage (aggregate across all calls):")
    click.echo(f"  input (uncached):  {totals['input']}")
    click.echo(f"  cache_creation:    {totals['cache_creation']}")
    click.echo(f"  cache_read (HIT):  {totals['cache_read']}")
    click.echo(f"  output:            {totals['output']}")
    if totals["cache_read"] > 0:
        saved = totals["cache_read"]
        click.echo(f"  → cache served {saved} tokens that would have been re-billed at 1x rate")


if __name__ == "__main__":
    main()
