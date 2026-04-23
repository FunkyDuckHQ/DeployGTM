"""
DeployGTM — Variant Tracker (client-agnostic, SQLite)

Closes the loop on the outreach generator. Every variant sent gets logged with
the angle label. When a response comes in, log it. Weekly reports surface which
angles actually get responses, by client.

Schema:
  variants(
    id                 INTEGER PRIMARY KEY,
    client_name        TEXT,
    company            TEXT,
    angle_variant      TEXT,   -- short angle label (e.g. "heritage-speed")
    angle_text         TEXT,   -- full body that was sent
    date_sent          TEXT,   -- ISO date
    response_received  INTEGER DEFAULT 0,  -- 0/1
    response_sentiment TEXT,   -- positive | neutral | negative | null
    next_action        TEXT
  )

DB path: projects/deploygtm-own/data/variants.db

Usage:
  # Log a new send
  python projects/deploygtm-own/scripts/variant_tracker.py log \\
      --client peregrine-space --company "Xona Space Systems" \\
      --angle-variant heritage-speed --angle-text "Saw the $19M..." \\
      [--date-sent 2026-04-23]

  # Record a response
  python projects/deploygtm-own/scripts/variant_tracker.py respond \\
      --id 3 --sentiment positive --next-action "book discovery"

  # List sends
  python projects/deploygtm-own/scripts/variant_tracker.py list --client peregrine-space

  # Weekly report: response rate by angle, per client
  python projects/deploygtm-own/scripts/variant_tracker.py report --client peregrine-space

  # Init schema + seed one sample row (for fresh setups / done-condition)
  python projects/deploygtm-own/scripts/variant_tracker.py seed
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import click


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "variants.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS variants (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name        TEXT NOT NULL,
    company            TEXT NOT NULL,
    angle_variant      TEXT NOT NULL,
    angle_text         TEXT NOT NULL,
    date_sent          TEXT NOT NULL,
    response_received  INTEGER NOT NULL DEFAULT 0,
    response_sentiment TEXT,
    next_action        TEXT,
    created_at         TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_variants_client      ON variants(client_name);
CREATE INDEX IF NOT EXISTS idx_variants_client_date ON variants(client_name, date_sent);
"""


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


# ─── Commands ────────────────────────────────────────────────────────────────


@click.group()
def cli():
    """Track outreach variants — what was sent, what came back, what worked."""


@cli.command()
@click.option("--client", required=True, help="Client slug.")
@click.option("--company", required=True, help="Target account company name.")
@click.option("--angle-variant", required=True, help="Short angle label (e.g. heritage-speed).")
@click.option("--angle-text", required=True, help="The body of the message that was sent.")
@click.option("--date-sent", default=None, help="ISO date (defaults to today).")
@click.option("--next-action", default=None, help="Next action / followup plan.")
def log(client: str, company: str, angle_variant: str, angle_text: str,
        date_sent: Optional[str], next_action: Optional[str]):
    """Log a variant that was just sent."""
    d = date_sent or date.today().isoformat()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO variants(client_name, company, angle_variant, angle_text, date_sent, next_action) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (client, company, angle_variant, angle_text, d, next_action),
        )
        conn.commit()
        click.echo(f"Logged variant id={cur.lastrowid}  {client} / {company} / {angle_variant}  ({d})")


@cli.command()
@click.option("--id", "variant_id", required=True, type=int, help="Row id from `log`.")
@click.option("--sentiment", type=click.Choice(["positive", "neutral", "negative"]), required=True)
@click.option("--next-action", default=None, help="Next action (optional).")
def respond(variant_id: int, sentiment: str, next_action: Optional[str]):
    """Record a response to a previously-logged variant."""
    with connect() as conn:
        row = conn.execute("SELECT id FROM variants WHERE id = ?", (variant_id,)).fetchone()
        if not row:
            raise click.ClickException(f"No variant with id={variant_id}")
        if next_action is not None:
            conn.execute(
                "UPDATE variants SET response_received=1, response_sentiment=?, next_action=? WHERE id=?",
                (sentiment, next_action, variant_id),
            )
        else:
            conn.execute(
                "UPDATE variants SET response_received=1, response_sentiment=? WHERE id=?",
                (sentiment, variant_id),
            )
        conn.commit()
        click.echo(f"Recorded {sentiment} response on variant id={variant_id}")


@cli.command(name="list")
@click.option("--client", default=None, help="Filter by client slug.")
@click.option("--since", default=None, help="Only rows with date_sent >= this ISO date.")
def list_cmd(client: Optional[str], since: Optional[str]):
    """List logged variants."""
    q = "SELECT id, client_name, company, angle_variant, date_sent, response_received, response_sentiment FROM variants"
    clauses, params = [], []
    if client:
        clauses.append("client_name = ?")
        params.append(client)
    if since:
        clauses.append("date_sent >= ?")
        params.append(since)
    if clauses:
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY date_sent DESC, id DESC"
    with connect() as conn:
        rows = conn.execute(q, params).fetchall()
    if not rows:
        click.echo("(no rows)")
        return
    click.echo(f"{'id':>4}  {'date':<10}  {'client':<20}  {'company':<28}  {'angle':<20}  resp")
    click.echo("-" * 100)
    for r in rows:
        flag = {0: "—", 1: r["response_sentiment"] or "yes"}[r["response_received"]]
        click.echo(
            f"{r['id']:>4}  {r['date_sent']:<10}  {r['client_name'][:20]:<20}  "
            f"{r['company'][:28]:<28}  {r['angle_variant'][:20]:<20}  {flag}"
        )


@cli.command()
@click.option("--client", required=True, help="Client slug to report on.")
@click.option("--since", default=None, help="Only rows with date_sent >= this ISO date (defaults to all time).")
def report(client: str, since: Optional[str]):
    """Weekly report — response rate by angle variant."""
    params: list = [client]
    where = "WHERE client_name = ?"
    if since:
        where += " AND date_sent >= ?"
        params.append(since)
    q = f"""
        SELECT angle_variant,
               COUNT(*) AS sent,
               SUM(response_received) AS responses,
               SUM(CASE WHEN response_sentiment='positive' THEN 1 ELSE 0 END) AS positive
          FROM variants
          {where}
      GROUP BY angle_variant
      ORDER BY responses DESC, sent DESC
    """
    with connect() as conn:
        rows = conn.execute(q, params).fetchall()
    if not rows:
        click.echo(f"No variants logged for {client}" + (f" since {since}" if since else "") + ".")
        return
    click.echo(f"\nVariant performance — client: {client}" + (f"  (since {since})" if since else ""))
    click.echo("=" * 72)
    click.echo(f"{'angle':<26}  {'sent':>5}  {'resp':>5}  {'pos':>4}  {'resp%':>6}")
    click.echo("-" * 72)
    for r in rows:
        sent = r["sent"] or 0
        resp = r["responses"] or 0
        pos = r["positive"] or 0
        pct = f"{(100 * resp / sent):.0f}%" if sent else "—"
        click.echo(f"{r['angle_variant'][:26]:<26}  {sent:>5}  {resp:>5}  {pos:>4}  {pct:>6}")
    click.echo("")


@cli.command()
def seed():
    """Initialize the schema and insert one sample row (Peregrine / Xona)."""
    with connect() as conn:
        existing = conn.execute(
            "SELECT id FROM variants WHERE client_name=? AND company=? AND angle_variant=?",
            ("peregrine-space", "Xona Space Systems", "heritage-speed"),
        ).fetchone()
        if existing:
            click.echo(f"Sample row already present (id={existing['id']}). Schema is ready.")
            return
        cur = conn.execute(
            "INSERT INTO variants(client_name, company, angle_variant, angle_text, date_sent, next_action) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "peregrine-space",
                "Xona Space Systems",
                "heritage-speed",
                "Saw the $19M Series A — PULSAR deployment timeline probably got tighter, "
                "not looser. Heritage payload qualification is the usual bottleneck there. "
                "Worth 20 minutes?",
                date.today().isoformat(),
                "Wait 3 days, then touch #1 via LinkedIn if no reply.",
            ),
        )
        conn.commit()
        click.echo(f"Seeded row id={cur.lastrowid}. DB at {DB_PATH}")


if __name__ == "__main__":
    cli()
