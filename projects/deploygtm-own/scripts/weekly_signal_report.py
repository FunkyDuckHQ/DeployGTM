"""
DeployGTM — Weekly Signal Report (client-agnostic)

For a given client, pulls their account matrix and writes a markdown report
covering:
  - What moved this week (new signals per account)
  - New signals surfaced outside the matrix
  - Outreach priority order (by icp_tier × signal strength)
  - Engagement threshold flags (accounts that crossed an outreach trigger)

BirdDog integration is optional. With BIRDDOG_API_KEY in .env the report pulls
real signals; without it, the report falls back to the why_now_signal already
captured in the matrix (plus any recorded variant activity from the SQLite
tracker).

Usage:
  python projects/deploygtm-own/scripts/weekly_signal_report.py \\
      --client peregrine-space

  # Write to a specific location instead of the default
  python projects/deploygtm-own/scripts/weekly_signal_report.py \\
      --client peregrine-space --out /tmp/report.md

Default output: projects/deploygtm-own/outputs/<client>/weekly_<YYYY-MM-DD>.md
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import click

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DB_PATH = DATA_DIR / "variants.db"

SIGNAL_WEIGHT = {
    "funding": 3,
    "contract_award": 3,
    "sbir_award": 3,
    "program_announcement": 3,
    "hiring": 2,
    "leadership_change": 2,
    "acquisition": 2,
    "product_launch": 2,
    "conference_signal": 1,
    "manual": 1,
}

ENGAGEMENT_THRESHOLD = 12  # icp_tier_score × signal_weight


# ─── Matrix loading (shared convention with generate_outreach.py) ────────────


def _matrix_path(client: str) -> Path:
    normalized = client.replace("-", "_")
    for candidate in (
        DATA_DIR / f"{normalized}_accounts.json",
        DATA_DIR / f"{client}_accounts.json",
        DATA_DIR / f"{client.split('-')[0]}_accounts.json",
    ):
        if candidate.exists():
            return candidate
    if DATA_DIR.exists():
        for f in DATA_DIR.glob("*_accounts.json"):
            try:
                if json.loads(f.read_text()).get("client_name") == client:
                    return f
            except (OSError, json.JSONDecodeError):
                continue
    raise FileNotFoundError(f"No account matrix found for client '{client}'.")


def load_matrix(client: str) -> dict:
    return json.loads(_matrix_path(client).read_text())


# ─── Signal fetching ─────────────────────────────────────────────────────────


def fetch_birddog_signals(domains: list[str], days_back: int = 7) -> dict[str, list[dict]]:
    """Attempt to pull BirdDog signals for the given domains.

    Returns a dict keyed by domain. Silently returns {} when the BirdDog client
    is unavailable (no key, import failure, or API error) — the caller should
    fall back to matrix signals.
    """
    if not os.environ.get("BIRDDOG_API_KEY"):
        return {}
    try:
        sys.path.insert(0, str(PROJECT_ROOT.parents[1] / "scripts"))
        import birddog  # type: ignore
        raw = birddog.pull_signals(days_back=days_back)
    except Exception as e:
        print(f"NOTE: BirdDog fetch failed ({e}). Using matrix signals only.", file=sys.stderr)
        return {}
    by_domain: dict[str, list[dict]] = {}
    wanted = {d.lower() for d in domains}
    for s in raw:
        dom = (s.get("domain") or "").lower()
        if dom in wanted:
            by_domain.setdefault(dom, []).append(s)
    return by_domain


# ─── Variant tracker integration ─────────────────────────────────────────────


def recent_variant_activity(client: str, since_iso: str) -> dict:
    """Pull variant activity from the SQLite tracker (if DB exists)."""
    if not DB_PATH.exists():
        return {"sent": 0, "responded": 0, "by_angle": [], "recent": []}
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        sent = conn.execute(
            "SELECT COUNT(*) FROM variants WHERE client_name=? AND date_sent>=?",
            (client, since_iso),
        ).fetchone()[0]
        responded = conn.execute(
            "SELECT COUNT(*) FROM variants "
            "WHERE client_name=? AND date_sent>=? AND response_received=1",
            (client, since_iso),
        ).fetchone()[0]
        by_angle = conn.execute(
            "SELECT angle_variant, COUNT(*) AS n, SUM(response_received) AS r "
            "FROM variants WHERE client_name=? AND date_sent>=? "
            "GROUP BY angle_variant ORDER BY r DESC, n DESC",
            (client, since_iso),
        ).fetchall()
        recent = conn.execute(
            "SELECT company, angle_variant, date_sent, response_sentiment "
            "FROM variants WHERE client_name=? AND date_sent>=? "
            "ORDER BY date_sent DESC LIMIT 10",
            (client, since_iso),
        ).fetchall()
        return {
            "sent": sent,
            "responded": responded,
            "by_angle": [dict(r) for r in by_angle],
            "recent": [dict(r) for r in recent],
        }
    finally:
        conn.close()


# ─── Scoring & formatting ────────────────────────────────────────────────────


def priority_score(account: dict) -> int:
    tier = account.get("icp_tier", 3)
    tier_score = {1: 5, 2: 3, 3: 1}.get(tier, 1)
    signal_type = account.get("why_now_signal", {}).get("type", "manual")
    return tier_score * SIGNAL_WEIGHT.get(signal_type, 1)


def _render_signal_line(a: dict, birddog_signals: list[dict]) -> str:
    if birddog_signals:
        pieces = []
        for s in birddog_signals[:2]:
            pieces.append(
                f"[BirdDog] {s.get('signal_type')}: {s.get('signal_summary') or '(no summary)'} "
                f"({s.get('signal_date')})"
            )
        return " · ".join(pieces)
    sig = a.get("why_now_signal", {})
    d = f" ({sig.get('date')})" if sig.get("date") else ""
    return f"[matrix] {sig.get('type')}: {sig.get('description')}{d} — src: {sig.get('source')}"


def build_report(
    matrix: dict,
    birddog_by_domain: dict[str, list[dict]],
    variant_stats: dict,
    days_back: int,
) -> str:
    client = matrix.get("client_name", "unknown")
    accounts = matrix.get("accounts", [])
    today = date.today().isoformat()

    scored = sorted(
        accounts,
        key=lambda a: (priority_score(a), -a.get("icp_tier", 3)),
        reverse=True,
    )

    flagged = [a for a in scored if priority_score(a) >= ENGAGEMENT_THRESHOLD]
    new_bird_signal_accounts = [
        a for a in accounts if birddog_by_domain.get((a.get("domain") or "").lower())
    ]

    lines: list[str] = []
    lines.append(f"# Weekly Signal Report — {client}")
    lines.append("")
    lines.append(f"_Generated: {today}  ·  Window: last {days_back} days_  ·  "
                 f"Accounts in matrix: {len(accounts)}_")
    lines.append("")

    # What moved
    lines.append(f"## What moved (last {days_back} days)")
    lines.append("")
    if new_bird_signal_accounts:
        for a in new_bird_signal_accounts:
            dom = (a.get("domain") or "").lower()
            sigs = birddog_by_domain.get(dom, [])
            lines.append(f"- **{a['company']}** — {len(sigs)} new BirdDog signal(s)")
            for s in sigs[:3]:
                lines.append(
                    f"  - {s.get('signal_type')}: {s.get('signal_summary') or '(no summary)'}  "
                    f"({s.get('signal_date')})"
                )
    else:
        lines.append("_No new BirdDog signals in window. Matrix why-now signals listed in the priority table below._")
    lines.append("")

    # New signals (outside matrix)
    lines.append("## New signals surfaced outside the matrix")
    lines.append("")
    matrix_domains = {(a.get("domain") or "").lower() for a in accounts}
    outside = [
        (d, sigs) for d, sigs in birddog_by_domain.items()
        if d and d not in matrix_domains
    ]
    if outside:
        for d, sigs in outside:
            lines.append(f"- **{d}** — {len(sigs)} signal(s). Consider adding to matrix.")
    else:
        lines.append("_None this week._")
    lines.append("")

    # Outreach priority
    lines.append("## Outreach priority (by icp_tier × signal strength)")
    lines.append("")
    lines.append("| Score | Tier | Company | Segment | Why now |")
    lines.append("|------:|:----:|---------|---------|---------|")
    for a in scored:
        sc = priority_score(a)
        dom = (a.get("domain") or "").lower()
        signal_text = _render_signal_line(a, birddog_by_domain.get(dom, []))
        # Markdown table cells: escape pipes
        signal_text = signal_text.replace("|", "\\|")
        lines.append(
            f"| {sc} | {a.get('icp_tier', '?')} | "
            f"{a.get('company', '')} | {a.get('segment', '')} | {signal_text} |"
        )
    lines.append("")

    # Engagement threshold flags
    lines.append(f"## Engagement threshold flags (score ≥ {ENGAGEMENT_THRESHOLD})")
    lines.append("")
    if flagged:
        lines.append(f"These accounts crossed the outreach trigger this week — "
                     f"**send the next variant**.")
        lines.append("")
        for a in flagged:
            persona = a.get("persona", {})
            lines.append(
                f"- **{a['company']}** ({a.get('domain')}) — "
                f"persona: {persona.get('title', '')}. "
                f"Angle: _{a.get('angle', '')}_"
            )
    else:
        lines.append("_No accounts above threshold this week._")
    lines.append("")

    # Status distribution — where each account sits in the lifecycle
    lines.append("## Status distribution")
    lines.append("")
    status_order = ["monitor", "active", "outreach_sent", "replied",
                    "meeting_booked", "no_fit", "paused"]
    counts = {s: 0 for s in status_order}
    for a in accounts:
        s = a.get("status") or "monitor"
        if s in counts:
            counts[s] += 1
        else:
            counts.setdefault(s, 0)
            counts[s] += 1
    lines.append("| Status | Count |")
    lines.append("|--------|------:|")
    for s in status_order:
        lines.append(f"| {s} | {counts.get(s, 0)} |")
    lines.append("")

    # Variant activity
    lines.append(f"## Variant activity (last {days_back} days)")
    lines.append("")
    lines.append(f"- Sent: **{variant_stats['sent']}**   ·   "
                 f"Responded: **{variant_stats['responded']}**")
    if variant_stats["by_angle"]:
        lines.append("")
        lines.append("| Angle | Sent | Responses |")
        lines.append("|-------|-----:|----------:|")
        for row in variant_stats["by_angle"]:
            lines.append(f"| {row['angle_variant']} | {row['n']} | {row['r'] or 0} |")
    if variant_stats["recent"]:
        lines.append("")
        lines.append("**Recent sends:**")
        for r in variant_stats["recent"]:
            sent = r["response_sentiment"] or "—"
            lines.append(f"- {r['date_sent']}  ·  {r['company']}  ·  {r['angle_variant']}  ·  response: {sent}")
    lines.append("")

    lines.append("---")
    lines.append(f"_Report generated by weekly_signal_report.py — {today}_")
    lines.append("")
    return "\n".join(lines)


# ─── CLI ─────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--client", required=True, help="Client slug.")
@click.option("--days-back", default=7, show_default=True, type=int,
              help="Signal lookback window in days.")
@click.option("--out", default=None, type=click.Path(),
              help="Override output path. Default: outputs/<client>/weekly_<date>.md")
@click.option("--stdout", is_flag=True, help="Print to stdout instead of writing a file.")
def main(client: str, days_back: int, out: Optional[str], stdout: bool):
    """Generate this week's signal report for a client."""
    matrix = load_matrix(client)
    domains = [a.get("domain", "") for a in matrix.get("accounts", []) if a.get("domain")]

    birddog_by_domain = fetch_birddog_signals(domains, days_back=days_back)
    since = (date.today() - timedelta(days=days_back)).isoformat()
    variant_stats = recent_variant_activity(client, since)

    content = build_report(matrix, birddog_by_domain, variant_stats, days_back)

    if stdout:
        click.echo(content)
        return

    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        client_dir = OUTPUTS_DIR / client
        client_dir.mkdir(parents=True, exist_ok=True)
        out_path = client_dir / f"weekly_{date.today().isoformat()}.md"

    out_path.write_text(content)
    size = out_path.stat().st_size
    click.echo(f"Report written: {out_path}  ({size:,} bytes)")
    if not birddog_by_domain:
        click.echo("  (No BIRDDOG_API_KEY set or BirdDog unreachable — used matrix signals only.)")


if __name__ == "__main__":
    main()
