"""
DeployGTM — HubSpot Sequence Step Builder

Generates ready-to-paste follow-up email templates for HubSpot sequences.
Uses the brain/ messaging framework + Claude to produce persona-specific
sequence steps with HubSpot merge tags.

Sequences handle automated follow-ups for large batches. The first email
is always personalized from the pipeline — sequences cover touches 2–4.

Output: a Markdown file you paste into HubSpot sequence editor.

Usage:
  python scripts/sequence_builder.py generate
  python scripts/sequence_builder.py generate --persona founder_seller
  python scripts/sequence_builder.py generate --output master/hubspot_sequences.md
  make generate-sequences
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import anthropic
import click
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"

PERSONAS = ["founder_seller", "first_sales_leader", "revops_growth"]

PERSONA_LABELS = {
    "founder_seller": "Founder-Seller (CEO doing sales)",
    "first_sales_leader": "First Sales Leader (VP Sales, Head of Sales, Founding AE)",
    "revops_growth": "RevOps / Growth (Solo ops, GTM, Demand Gen)",
}

PERSONA_CONTEXT = {
    "founder_seller": (
        "CEO or co-founder still doing sales themselves. Pain: drowning in "
        "product + sales + recruiting with no time to build outbound properly. "
        "They want a system so they can focus on closing and product."
    ),
    "first_sales_leader": (
        "First VP Sales, Head of Sales, or Founding AE. Hired to close deals "
        "but inherited nothing — no CRM hygiene, no sequences, no signal detection. "
        "They want infrastructure underneath them so they can actually sell."
    ),
    "revops_growth": (
        "Solo RevOps or Growth person managing too many disconnected tools. "
        "Pain: no orchestration layer, tools don't talk to each other. "
        "They want the full stack wired up correctly."
    ),
}


def load_brain(brain_path: str = "brain") -> str:
    brain_dir = Path(brain_path)
    files = ["messaging.md", "personas.md", "product.md", "objections.md"]
    sections = []
    for fname in files:
        fpath = brain_dir / fname
        if fpath.exists():
            sections.append(f"## {fname}\n\n{fpath.read_text().strip()}")
    return "\n\n---\n\n".join(sections)


def generate_sequence_steps(
    persona: str,
    brain_context: str,
    api_key: Optional[str] = None,
) -> dict:
    """Generate 3 sequence step templates for a persona."""
    client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    label = PERSONA_LABELS[persona]
    context = PERSONA_CONTEXT[persona]

    system_prompt = f"""You are the DeployGTM sequence writer. You generate follow-up email templates for HubSpot sequences.

{brain_context}

Rules:
- These are TEMPLATES, not personalized messages. Use HubSpot merge tags: {{{{contact.firstname}}}}, {{{{company.name}}}}, {{{{owner.firstname}}}}
- The first email (touch 1) is sent separately as a personalized message from the pipeline — you're writing touches 2, 3, 4
- Touch 2 (day 3-4): Add value, reference the original email, under 80 words
- Touch 3 (day 7-8): One or two sentences. "Still relevant?" Forward the original.
- Touch 4 (day 14-15): Breakup email. "Happy to park this."
- Each touch must feel like it was written by a human who actually gives a shit, not a sales robot
- No AI language, no filler, no "I hope this email finds you well"
- Subject lines for touches 2-4 should be "Re: [original subject]" (handled by HubSpot threading)
"""

    user_prompt = f"""Generate 3 HubSpot sequence step email templates for this persona.

PERSONA: {label}
CONTEXT: {context}

These are follow-up steps AFTER the personalized first email has already been sent.
Each step should feel like a natural follow-up to an email about:
"You're probably still doing outbound manually. I build the pipeline engine — signals, enrichment, CRM, outreach. 2-week Signal Audit, $3,500, you walk away with a working system."

Return JSON only:
{{
  "touch_2": {{
    "delay_days": 3,
    "subject": "Re: [original subject]",
    "body": "the email body — use {{{{contact.firstname}}}}, {{{{company.name}}}}, {{{{owner.firstname}}}}"
  }},
  "touch_3": {{
    "delay_days": 7,
    "subject": "Re: [original subject]",
    "body": "the email body"
  }},
  "touch_4": {{
    "delay_days": 14,
    "subject": "Re: [original subject]",
    "body": "the email body"
  }}
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(raw)


def format_sequence_md(persona: str, steps: dict) -> str:
    label = PERSONA_LABELS[persona]
    lines = [
        f"## Sequence: {label}",
        "",
        f"**HubSpot sequence name:** `DeployGTM — {label.split('(')[0].strip()}`",
        "",
        "> Note: Touch 1 (initial email) is sent separately via the pipeline with full personalization.",
        "> Enroll contacts here AFTER the personalized first email is sent.",
        "",
    ]

    for touch_key, touch_num in [("touch_2", 2), ("touch_3", 3), ("touch_4", 4)]:
        step = steps.get(touch_key, {})
        delay = step.get("delay_days", "?")
        subject = step.get("subject", "")
        body = step.get("body", "")

        lines += [
            f"### Step {touch_num - 1} (Touch {touch_num}) — Day {delay}",
            "",
            f"**Subject:** {subject}",
            "",
            "**Body:**",
            "```",
            body,
            "```",
            "",
        ]

    return "\n".join(lines)


# ─── CLI ──────────────────────────────────────────────────────────────────────


@click.group()
def cli():
    """DeployGTM Sequence Builder — generate HubSpot sequence step templates."""
    pass


@cli.command()
@click.option("--persona", default=None,
              type=click.Choice(PERSONAS + ["all"]),
              help="Persona to generate for. Default: all three.")
@click.option("--output", default=None,
              help="Output file path. Default: master/hubspot_sequences.md")
@click.option("--brain", "brain_path", default="brain", show_default=True)
def generate(persona: Optional[str], output: Optional[str], brain_path: str):
    """Generate HubSpot sequence step templates for one or all personas."""
    personas_to_build = PERSONAS if (persona is None or persona == "all") else [persona]
    out_path = Path(output) if output else Path("master/hubspot_sequences.md")

    brain_context = load_brain(brain_path)

    sections = [
        "# DeployGTM — HubSpot Sequence Step Templates",
        "",
        "*Generated by scripts/sequence_builder.py. Paste these into HubSpot → Automation → Sequences.*",
        "",
        "**How to use:**",
        "1. Create a new sequence in HubSpot for each persona below",
        "2. Name it exactly as shown",
        "3. Add email steps with the content below",
        "4. Get the sequence ID from the URL bar",
        "5. Add IDs to `config.yaml` under `tools.hubspot.sequences`",
        "6. See `master/playbooks/hubspot-setup.md` for full setup steps",
        "",
        "---",
        "",
    ]

    for p in personas_to_build:
        label = PERSONA_LABELS[p]
        click.echo(f"Generating sequence steps: {label}...")
        try:
            steps = generate_sequence_steps(p, brain_context)
            section_md = format_sequence_md(p, steps)
            sections.append(section_md)
            sections.append("---")
            sections.append("")
        except Exception as e:
            click.echo(f"  ✗ Failed for {p}: {e}", err=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(sections))

    click.echo(f"\n✓ Sequences written to: {out_path}")
    click.echo(f"\nNext steps:")
    click.echo(f"  1. Open {out_path}")
    click.echo(f"  2. Create sequences in HubSpot (see master/playbooks/hubspot-setup.md)")
    click.echo(f"  3. Paste the step content into each sequence")
    click.echo(f"  4. Copy sequence IDs from HubSpot URL bar")
    click.echo(f"  5. Add to config.yaml under tools.hubspot.sequences")


if __name__ == "__main__":
    cli()
