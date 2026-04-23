"""
DeployGTM — Outreach Variant Generator (client-agnostic)

Takes a client name and a target account, loads the account from that client's
account matrix, and generates 3 distinct angle variants grounded in the
why_now_signal. Each variant is short, signal-led, and written in the client's
voice (from voice_notes in the matrix).

Hard rules for each variant:
  - Under 75 words
  - One verifiable reference (the why_now_signal fact)
  - One simple question
  - Nothing else — no sign-off fluff, no pitch dump, no "leveraging synergies"

Usage:
  python projects/deploygtm-own/scripts/generate_outreach.py \\
      --client peregrine-space \\
      --company "Xona Space Systems"

Output:
  projects/deploygtm-own/outputs/<client>/<company_slug>_<YYYY-MM-DD>.txt
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
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


MODEL = "claude-sonnet-4-20250514"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


# ─── Matrix loading ──────────────────────────────────────────────────────────


def _matrix_path(client: str) -> Path:
    """Resolve the account matrix file for a client.

    Tries in order:
      1. data/<client-slug-with-underscores>_accounts.json
      2. data/<client>_accounts.json
      3. data/<first-word-of-slug>_accounts.json  (e.g. peregrine-space → peregrine_accounts.json)
      4. Any data/*_accounts.json whose top-level client_name matches.
    """
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
    raise FileNotFoundError(
        f"No account matrix found for client '{client}'. "
        f"Expected: {DATA_DIR / (normalized + '_accounts.json')}"
    )


def load_client_matrix(client: str) -> dict:
    path = _matrix_path(client)
    data = json.loads(path.read_text())
    if data.get("client_name") != client:
        # Not fatal — but warn. We trust the filename convention.
        print(
            f"NOTE: client_name in file is '{data.get('client_name')}' — "
            f"requested '{client}'. Continuing with file contents.",
            file=sys.stderr,
        )
    return data


def find_account(matrix: dict, company: str) -> dict:
    target = company.strip().lower()
    for acct in matrix.get("accounts", []):
        if acct.get("company", "").strip().lower() == target:
            return acct
    # Try substring match as a fallback
    matches = [a for a in matrix.get("accounts", []) if target in a.get("company", "").lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(m["company"] for m in matches)
        raise ValueError(f"Ambiguous company '{company}'. Matches: {names}")
    raise ValueError(f"Company '{company}' not found in matrix for '{matrix.get('client_name')}'.")


# ─── Generation ──────────────────────────────────────────────────────────────


SYSTEM_TEMPLATE = """You write cold outreach for a GTM engineering practice. You write in the client's voice as defined below. You never sound like AI. You never pad. You never dump features.

<client_voice>
{voice_notes}
</client_voice>

HARD RULES — every variant must satisfy all of these:
1. Under 75 words. Count.
2. Exactly one verifiable reference — the why_now_signal fact provided. Reference it naturally, like a human would.
3. Exactly one simple question that invites a short reply.
4. No greeting fluff ("I hope this finds you well", "Hope your week is going well"). Open with the signal or the angle.
5. No feature dumping. No adjectives like "exciting", "innovative", "cutting-edge".
6. No sign-off block. No "Best regards". Just the body.
7. Three variants must take three DIFFERENT angles — do not reshuffle the same argument.

Return VALID JSON ONLY in this exact shape:
{{
  "variants": [
    {{"angle_label": "<short label, 3-5 words>", "subject": "<short subject line, 6 words max>", "body": "<the message, under 75 words>"}},
    {{"angle_label": "...", "subject": "...", "body": "..."}},
    {{"angle_label": "...", "subject": "...", "body": "..."}}
  ]
}}

No markdown fences. No commentary. JSON only."""


USER_TEMPLATE = """Target account: {company} ({domain})
Market / segment: {market} / {segment}
Persona: {persona_title} — {why_they_feel_it}

The directional argument for this account (use as creative fuel, not copy-paste):
{angle}

Why-now signal (this is the one verifiable fact you may reference):
  Type: {signal_type}
  What happened: {signal_description}
  Source: {signal_source}{signal_date_line}

Product fit for this account:
{product_fit}

Heritage/objection risk: {heritage_risk}

Write 3 distinct angle variants following every rule in the system prompt. Each should open differently. Each should take a different path to the same question."""


def _signal_date_line(signal: dict) -> str:
    d = signal.get("date")
    return f"\n  Date: {d}" if d else ""


def build_prompts(matrix: dict, account: dict) -> tuple[str, str]:
    signal = account.get("why_now_signal", {})
    persona = account.get("persona", {})

    system = SYSTEM_TEMPLATE.format(
        voice_notes=matrix.get("voice_notes", "").strip() or "Direct. Short sentences. No fluff."
    )
    user = USER_TEMPLATE.format(
        company=account.get("company", ""),
        domain=account.get("domain", ""),
        market=account.get("market", ""),
        segment=account.get("segment", ""),
        persona_title=persona.get("title", ""),
        why_they_feel_it=persona.get("why_they_feel_it", ""),
        angle=account.get("angle", ""),
        signal_type=signal.get("type", ""),
        signal_description=signal.get("description", ""),
        signal_source=signal.get("source", ""),
        signal_date_line=_signal_date_line(signal),
        product_fit=account.get("product_fit", ""),
        heritage_risk=account.get("heritage_risk", ""),
    )
    return system, user


def call_claude(system: str, user: str, api_key: Optional[str] = None) -> str:
    client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


def parse_variants(raw: str) -> list[dict]:
    """Parse model output into a list of variant dicts.

    Tolerates accidental markdown fences even though the prompt forbids them.
    """
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model returned invalid JSON: {e}\n---\n{raw}") from e
    variants = data.get("variants", [])
    if not isinstance(variants, list) or len(variants) != 3:
        raise ValueError(f"Expected exactly 3 variants, got {len(variants) if isinstance(variants, list) else '?'}.")
    return variants


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


# ─── Output ──────────────────────────────────────────────────────────────────


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower())
    return s.strip("_")


def format_output(matrix: dict, account: dict, variants: list[dict]) -> str:
    signal = account.get("why_now_signal", {})
    lines = []
    lines.append(f"Client:    {matrix.get('client_name')}")
    lines.append(f"Account:   {account.get('company')} ({account.get('domain')})")
    lines.append(f"Segment:   {account.get('market')} / {account.get('segment')}")
    lines.append(f"Persona:   {account.get('persona', {}).get('title', '')}")
    lines.append(f"Signal:    [{signal.get('type')}] {signal.get('description')}  (src: {signal.get('source')})")
    lines.append(f"Generated: {date.today().isoformat()}")
    lines.append("=" * 72)
    for i, v in enumerate(variants, start=1):
        body = v.get("body", "").strip()
        wc = word_count(body)
        over = "  ← OVER 75" if wc > 75 else ""
        lines.append("")
        lines.append(f"--- Variant {i}: {v.get('angle_label', '')} ---")
        lines.append(f"Subject: {v.get('subject', '')}")
        lines.append(f"Words:   {wc}{over}")
        lines.append("")
        lines.append(body)
    lines.append("")
    return "\n".join(lines)


def write_output(client: str, company: str, content: str) -> Path:
    client_dir = OUTPUTS_DIR / client
    client_dir.mkdir(parents=True, exist_ok=True)
    out_path = client_dir / f"{slugify(company)}_{date.today().isoformat()}.txt"
    out_path.write_text(content)
    return out_path


def log_variant_to_tracker(client: str, company: str, variant: dict) -> Optional[int]:
    """Insert one variant into the SQLite tracker. Returns row id or None on failure."""
    db_path = DATA_DIR / "variants.db"
    try:
        import sqlite3
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        # Ensure schema exists — same shape as variant_tracker.py
        conn.executescript("""
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
        """)
        cur = conn.execute(
            "INSERT INTO variants(client_name, company, angle_variant, angle_text, date_sent) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                client,
                company,
                variant.get("angle_label", "unlabeled"),
                variant.get("body", ""),
                date.today().isoformat(),
            ),
        )
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return rid
    except Exception as e:
        click.echo(f"  WARN: could not log to tracker: {e}", err=True)
        return None


# ─── CLI ─────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--client", required=True, help="Client slug (matches client_name in matrix).")
@click.option("--company", required=True, help="Target account company name (as in the matrix).")
@click.option("--dry-run", is_flag=True, help="Build prompts and skip the API call. Prints prompts.")
@click.option("--no-write", is_flag=True, help="Print output but do not write to disk.")
@click.option("--log-variant", type=click.IntRange(1, 3), default=None,
              help="Log variant N (1-3) to the SQLite tracker as sent-today.")
def main(client: str, company: str, dry_run: bool, no_write: bool, log_variant: Optional[int]):
    """Generate 3 outreach variants for one account in one client's matrix."""
    matrix = load_client_matrix(client)
    account = find_account(matrix, company)
    system, user = build_prompts(matrix, account)

    if dry_run:
        click.echo("=== SYSTEM ===")
        click.echo(system)
        click.echo("\n=== USER ===")
        click.echo(user)
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise click.ClickException("ANTHROPIC_API_KEY not set. Add it to .env or your shell.")

    click.echo(f"Generating 3 variants for {account['company']} (client: {client})...")
    raw = call_claude(system, user)
    variants = parse_variants(raw)

    for i, v in enumerate(variants, start=1):
        wc = word_count(v.get("body", ""))
        flag = " [OVER 75]" if wc > 75 else ""
        click.echo(f"  variant {i}: {wc} words{flag} — {v.get('angle_label', '')}")

    content = format_output(matrix, account, variants)

    if not no_write:
        out_path = write_output(client, account["company"], content)
        click.echo(f"\nSaved: {out_path.relative_to(Path.cwd()) if out_path.is_relative_to(Path.cwd()) else out_path}")
    else:
        click.echo("\n" + content)

    if log_variant is not None:
        chosen = variants[log_variant - 1]
        rid = log_variant_to_tracker(client, account["company"], chosen)
        if rid:
            click.echo(f"Logged variant {log_variant} to tracker (id={rid}).")


if __name__ == "__main__":
    main()
