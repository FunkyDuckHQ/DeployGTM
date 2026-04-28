"""
DeployGTM — Derive ICP Scoring Profile from context.md

Reads the client's context.md and asks Claude to generate a structured
ICP scoring profile tailored to that client's product and ICP. The profile
becomes the source of truth for:

  - research_accounts.py  → fit dimensions to score each account on
  - score_engine.py       → signal weights and per-signal decay rates
  - enrich_matrix.py      → persona-to-title mapping for Apollo searches

Output: projects/deploygtm-own/data/<client>_icp_profile.json

Why this exists
---------------
ICP scoring dimensions are NOT universal. GTM maturity is a top signal for
DeployGTM's own ICP (companies that need GTM infrastructure) but is irrelevant
for Peregrine Space's ICP (NewSpace primes and contractors). The dimensions
must come from the client's context, not be hardcoded in the scoring code.

Usage:
  # Generate / regenerate profile from context.md
  python scripts/derive_icp.py --client deploygtm-own

  # Regenerate even if profile already exists
  python scripts/derive_icp.py --client peregrine-space --force

  # Dry-run — print derived profile, don't write
  python scripts/derive_icp.py --client deploygtm-own --dry-run
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

REPO_ROOT = Path(__file__).resolve().parent.parent

if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


# ─── Paths ───────────────────────────────────────────────────────────────────

PROJECTS_DIR = REPO_ROOT / "projects"
MATRIX_DATA_DIR = REPO_ROOT / "projects" / "deploygtm-own" / "data"


def context_path(client: str) -> Path:
    return PROJECTS_DIR / client / "context.md"


def profile_path(client: str) -> Path:
    """ICP profile lives next to the account matrix for that client."""
    normalized = client.replace("-", "_")
    return MATRIX_DATA_DIR / f"{normalized}_icp_profile.json"


# ─── Default profile (universal fallback) ─────────────────────────────────────

DEFAULT_PROFILE: dict = {
    "fit_dimensions": [
        {
            "name": "stage_fit",
            "weight": 2.0,
            "max_raw": 2,
            "description": "Company stage matches the buying window",
            "high_signal": "Active stage with budget to spend",
            "low_signal": "Pre-revenue or too mature to need help",
        },
        {
            "name": "size_fit",
            "weight": 1.0,
            "max_raw": 2,
            "description": "Company size matches the client's ICP",
            "high_signal": "Within target headcount range",
            "low_signal": "Too small or too large for the client's offering",
        },
        {
            "name": "buyer_pain_signal",
            "weight": 1.5,
            "max_raw": 2,
            "description": "Visible signs the company has the pain the client solves",
            "high_signal": "Public statements or behavior indicating acute pain",
            "low_signal": "No visible pain signals",
        },
        {
            "name": "buyer_type",
            "weight": 0.5,
            "max_raw": 2,
            "description": "Buyer persona present and decision-making structure clear",
            "high_signal": "Decision-maker buyer is identifiable and accessible",
            "low_signal": "Buyer absent, decision unclear, or wrong buyer type",
        },
    ],
    "fit_max_score": 10.0,
    "tier_fit_fallback": {1: 7.0, 2: 4.5, 3: 2.0},
    "signal_weights": {
        "funding": 3,
        "hiring": 2,
        "leadership_change": 2,
        "acquisition": 2,
        "product_launch": 1,
        "manual": 1,
    },
    "signal_decay_days": {
        "default": 60,
    },
    "status_deltas": {
        "active": 1,
        "outreach_sent": 2,
        "replied": 6,
        "meeting_booked": 12,
        "no_fit": -15,
        "paused": -3,
        "monitor": 0,
    },
    "sentiment_deltas": {
        "positive": 4,
        "neutral": 1,
        "negative": -2,
    },
    "personas": {
        "decision_maker": ["CEO", "Founder", "President"],
    },
    "disqualifiers": [],
}


# ─── Claude derivation ────────────────────────────────────────────────────────

_DERIVE_SYSTEM = """\
You are a B2B GTM analyst designing the scoring framework for a client's
outbound prospecting motion. Your job is to translate the client's context
(their product, their ICP, their buyer personas, their disqualifiers) into a
structured ICP scoring profile that downstream automation can use to score
target accounts.

You will receive the client's context.md. Your output is a single JSON object
with these fields:

{
  "client_product_summary": "<one sentence — what the client sells and to whom>",

  "fit_dimensions": [
    // 3-5 dimensions specific to THIS client's ICP. Each scored 0-2.
    // Weight reflects how much that dimension matters to the buying decision.
    // Max weighted contribution across all dimensions should sum to 10.
    {
      "name": "<snake_case_name>",
      "weight": <number, e.g. 2.0>,
      "max_raw": 2,
      "description": "<one sentence — what this dimension measures>",
      "high_signal": "<concrete description of what a 2 looks like>",
      "low_signal": "<concrete description of what a 0 looks like>"
    }
  ],

  "fit_max_score": 10.0,

  "signal_weights": {
    // The buying-intent signals that matter for THIS client's ICP.
    // Values 1-4 indicating how predictive each signal is of buying intent.
    // Use snake_case keys. Examples for a SaaS GTM practice would be:
    //   funding, hiring_ae_sdr, churned_agency_cro, linkedin_pain_post
    // Examples for a defense/aerospace ICP would be:
    //   sbir_award, contract_award, program_announcement
    "<signal_name>": <1-4>
  },

  "signal_decay_days": {
    // Half-life in days for each signal type. Different signals have different
    // natural action windows. A founder LinkedIn post about pain decays in days;
    // a contract award stays warm for months.
    "default": 60,
    "<signal_name>": <days>
  },

  "personas": {
    // Buyer personas for THIS client's ICP, mapped to title strings Apollo
    // can search for. Persona keys should be snake_case (e.g. founder_seller,
    // first_sales_leader, program_manager, technical_lead).
    "<persona_key>": ["<Title 1>", "<Title 2>"]
  },

  "disqualifiers": [
    // Hard filters — companies matching any of these should be removed,
    // not scored. Specific to this client's ICP.
    "<disqualifier description>"
  ]
}

Critical:
- Dimensions, signals, and personas MUST be derived from the client's actual
  product and ICP, not generic B2B SaaS defaults.
- For a defense/aerospace client, "GTM maturity" is irrelevant — drop it.
  For a fintech client, "regulatory environment" might be a dimension.
- If context.md is sparse, infer reasonable defaults but flag low confidence
  in your weights (use lower weights for dimensions you're guessing at).
- Output valid JSON only. No prose, no markdown fences, no commentary.
"""


def _derive_with_claude(
    client: str,
    context_md: str,
    api_key: Optional[str] = None,
) -> dict:
    """Call Claude to derive an ICP profile from the client's context.md."""
    import anthropic

    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise click.ClickException("ANTHROPIC_API_KEY not set.")

    client_obj = anthropic.Anthropic(api_key=key)

    user_content = f"""Client slug: {client}

context.md (first 6000 chars):
{context_md[:6000]}
"""

    msg = client_obj.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": _DERIVE_SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_content}],
    )

    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise click.ClickException(
            f"Claude returned invalid JSON for ICP profile derivation: {e}\n"
            f"First 500 chars: {raw[:500]}"
        )


# ─── Profile loading / merging (shared) ───────────────────────────────────────


def _deep_merge(base: dict, override: dict) -> dict:
    """Shallow-merge top-level keys; for dict values, merge one level deep."""
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = {**out[key], **value}
        else:
            out[key] = value
    return out


def load_profile(client: str) -> dict:
    """Return DEFAULT_PROFILE merged with the client's profile (if any)."""
    profile = json.loads(json.dumps(DEFAULT_PROFILE))  # deep copy
    path = profile_path(client)
    if path.exists():
        try:
            client_overrides = json.loads(path.read_text())
            profile = _deep_merge(profile, client_overrides)
        except (OSError, json.JSONDecodeError) as e:
            click.echo(f"  WARN: failed to load {path}: {e}", err=True)
    return profile


def write_profile(client: str, profile: dict) -> Path:
    """Write the profile JSON to disk and return the path."""
    profile = dict(profile)
    profile["client"] = client
    profile["derived_at"] = date.today().isoformat()

    path = profile_path(client)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2) + "\n")
    return path


# ─── CLI ─────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--client", required=True, help="Client slug.")
@click.option("--force", is_flag=True, help="Regenerate even if profile already exists.")
@click.option("--dry-run", is_flag=True, help="Print derived profile, don't write.")
def main(client: str, force: bool, dry_run: bool):
    """Derive an ICP scoring profile from the client's context.md."""
    ctx_path = context_path(client)
    if not ctx_path.exists():
        raise click.ClickException(
            f"context.md not found for client '{client}' at {ctx_path}.\n"
            f"Run `make engage CLIENT={client} ...` first."
        )

    out_path = profile_path(client)
    if out_path.exists() and not force and not dry_run:
        raise click.ClickException(
            f"ICP profile already exists at {out_path}.\n"
            f"Use --force to regenerate, or --dry-run to preview."
        )

    click.echo(f"\nDeriving ICP profile for {client}...")
    click.echo(f"  Reading {ctx_path.relative_to(REPO_ROOT)}")

    context_md = ctx_path.read_text()
    derived = _derive_with_claude(client, context_md)

    click.echo(f"\n  Product summary: {derived.get('client_product_summary', '')[:100]}")
    dims = derived.get("fit_dimensions", [])
    click.echo(f"  Fit dimensions ({len(dims)}):")
    for d in dims:
        click.echo(f"    {d['name']:<25} weight={d['weight']:>4}  max={d['max_raw']}")
    click.echo(f"  Signal weights: {list(derived.get('signal_weights', {}).keys())}")
    click.echo(f"  Personas: {list(derived.get('personas', {}).keys())}")

    if dry_run:
        click.echo("\n(dry-run — not written)")
        click.echo(json.dumps(derived, indent=2))
        return

    path = write_profile(client, derived)
    click.echo(f"\n  Wrote {path.relative_to(REPO_ROOT)}")
    click.echo("\nNext: `make research-accounts CLIENT={}` to score target accounts.".format(client))


if __name__ == "__main__":
    main()
