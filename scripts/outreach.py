"""
DeployGTM — Outreach Generation (Claude)

Generates personalized, signal-led outreach messages for each contact.

Uses brain/ files (or Octave if enabled) as the messaging context.
Produces 1 primary message + 2 follow-ups per contact.

Prompt caching is used on brain context — ~90% token cost reduction
when processing multiple contacts in the same session.

Standalone:
  python scripts/outreach.py --research-file output/acme_research.json \\
      --contact-name "Jane Smith" --contact-title "CEO" \\
      --signal funding --signal-date 2024-03-15
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


def load_brain(brain_path: str = "brain") -> str:
    brain_dir = Path(brain_path)
    files = ["product.md", "icp.md", "personas.md", "messaging.md", "objections.md"]
    sections = []
    for fname in files:
        fpath = brain_dir / fname
        if fpath.exists():
            sections.append(f"## {fname}\n\n{fpath.read_text().strip()}")
    return "\n\n---\n\n".join(sections)


def detect_persona(title: str) -> str:
    """Map a contact title to one of our three buyer personas."""
    title_lower = title.lower()

    founder_keywords = ["ceo", "founder", "co-founder", "chief executive", "president"]
    sales_keywords = ["vp sales", "head of sales", "vp revenue", "chief revenue",
                      "cro", "sales director", "founding ae", "ae", "account executive"]
    ops_keywords = ["revops", "revenue ops", "revenue operations", "marketing ops",
                    "growth", "operations", "gtm", "demand gen"]

    if any(k in title_lower for k in founder_keywords):
        return "founder_seller"
    if any(k in title_lower for k in sales_keywords):
        return "first_sales_leader"
    if any(k in title_lower for k in ops_keywords):
        return "revops_growth"

    return "founder_seller"  # default


def generate_outreach(
    research: dict,
    contact_name: str,
    contact_title: str,
    signal_type: str,
    signal_date: Optional[str],
    signal_summary: str,
    brain_context: str,
    api_key: Optional[str] = None,
) -> dict:
    """
    Generate a primary outreach message + 2 follow-ups for one contact.

    Returns dict with: persona, primary, followup_1, followup_2, notes
    """
    client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
    persona = detect_persona(contact_title)

    system_prompt = f"""You are the outreach copywriter for DeployGTM, a GTM engineering practice run by Matthew Stegenga.
You write cold outreach that is direct, human, and signal-led.

Here is the complete DeployGTM messaging context — ICP, personas, product, and messaging rules:

<deploygtm_context>
{brain_context}
</deploygtm_context>

CRITICAL RULES:
- Never use AI-sounding language. No "I hope this finds you well." No "leveraging synergies." No "exciting opportunity."
- Lead with the specific signal. Not "I was researching your company."
- Under 100 words for the primary message.
- Follow-ups should be even shorter — 2–3 sentences max.
- Write as Matthew Stegenga, first person.
- Respond with valid JSON only. No markdown fences."""

    user_prompt = f"""Write outreach for this contact.

CONTACT:
  Name: {contact_name}
  Title: {contact_title}
  Detected persona: {persona}

COMPANY RESEARCH:
{json.dumps(research, indent=2)}

SIGNAL:
  Type: {signal_type}
  Date: {signal_date or "unknown"}
  Summary: {signal_summary or research.get("signal_context", "")}

Return a JSON object with exactly these fields:

{{
  "persona": "{persona}",
  "primary": {{
    "subject": "Email subject line (no clickbait, no all-caps)",
    "body": "The main outreach message. Under 100 words. Lead with signal. Bridge to pain. Offer next step.",
    "channel": "email | linkedin"
  }},
  "followup_1": {{
    "send_on_day": 3,
    "body": "2–3 sentences. Add one new piece of value or a relevant question. Don't just bump.",
    "channel": "email"
  }},
  "followup_2": {{
    "send_on_day": 7,
    "body": "1–2 sentences. Either bump or close the loop gracefully.",
    "channel": "email"
  }},
  "linkedin_connection_note": "Under 300 chars. What you'd say in a LinkedIn connection request.",
  "pain_used": "The specific pain hypothesis this outreach is built around",
  "signal_used": "The specific signal this outreach references",
  "notes": "Any caveats about this message (e.g., missing info that would sharpen it)"
}}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned)

    result["_contact_name"] = contact_name
    result["_contact_title"] = contact_title
    result["_model"] = MODEL
    result["_input_tokens"] = message.usage.input_tokens
    result["_output_tokens"] = message.usage.output_tokens

    return result


# ─── CLI ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--research-file", "-r", required=True,
              help="Path to JSON file from research.py (or pipeline.py output)")
@click.option("--contact-name", "-n", required=True, help="Contact full name")
@click.option("--contact-title", "-t", required=True, help="Contact title")
@click.option("--signal", "-s", required=True,
              type=click.Choice(["funding", "hiring", "gtm_struggle", "agency_churn", "tool_adoption", "manual"]))
@click.option("--signal-date", default=None)
@click.option("--signal-summary", default="")
@click.option("--brain-path", default="brain")
@click.option("--output", "-o", default=None, help="Write result to JSON file")
def cli(research_file, contact_name, contact_title, signal, signal_date,
        signal_summary, brain_path, output):
    """Generate outreach messages for one contact."""
    research = json.loads(Path(research_file).read_text())
    brain_context = load_brain(brain_path)

    click.echo(f"Generating outreach for {contact_name} ({contact_title})...")

    result = generate_outreach(
        research=research,
        contact_name=contact_name,
        contact_title=contact_title,
        signal_type=signal,
        signal_date=signal_date,
        signal_summary=signal_summary,
        brain_context=brain_context,
    )

    click.echo(f"\n  Persona: {result['persona']}")
    click.echo(f"\n  SUBJECT: {result['primary']['subject']}")
    click.echo(f"\n  EMAIL:\n{result['primary']['body']}")
    click.echo(f"\n  FOLLOW-UP 1 (day {result['followup_1']['send_on_day']}):\n{result['followup_1']['body']}")
    click.echo(f"\n  FOLLOW-UP 2 (day {result['followup_2']['send_on_day']}):\n{result['followup_2']['body']}")

    if output:
        Path(output).write_text(json.dumps(result, indent=2))
        click.echo(f"\nSaved to {output}")

    click.echo(f"\n[tokens: {result['_input_tokens']} in / {result['_output_tokens']} out]")


if __name__ == "__main__":
    cli()
