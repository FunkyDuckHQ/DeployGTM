"""
DeployGTM — Account Research (Claude)

Researches a target account and produces:
  - Company summary
  - Founder / key people
  - Funding + stage
  - Who they sell to
  - ICP assessment (yes / no / maybe + reason)
  - Pain hypothesis
  - Confidence level + source notes

Uses the Claude API with prompt caching on brain/ context files for efficiency.

Standalone:
  python scripts/research.py --company "Acme" --domain "acme.com" \\
      --signal funding --signal-date 2024-03-01 \\
      --signal-summary "Raised $4M Seed from a16z"
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
    """Concatenate all brain/ markdown files into a single context block."""
    brain_dir = Path(brain_path)
    files = ["product.md", "icp.md", "personas.md", "messaging.md", "objections.md"]
    sections = []
    for fname in files:
        fpath = brain_dir / fname
        if fpath.exists():
            sections.append(f"## {fname}\n\n{fpath.read_text().strip()}")
    return "\n\n---\n\n".join(sections)


def research_account(
    company: str,
    domain: str,
    signal_type: str,
    signal_date: Optional[str],
    signal_summary: str,
    brain_context: str,
    api_key: Optional[str] = None,
) -> dict:
    """
    Research one account using Claude.

    Returns a dict with all structured research fields.
    """
    client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    system_prompt = f"""You are the research engine for DeployGTM, a GTM engineering practice.
Your job is to research a target company and assess whether it is a strong ICP fit.

Below is the complete context for DeployGTM — what we sell, who we target, and how we message:

<deploygtm_context>
{brain_context}
</deploygtm_context>

Always respond with valid JSON only. No markdown fences. No prose outside the JSON object."""

    user_prompt = f"""Research this company and return a structured assessment.

Company: {company}
Domain: {domain}
Signal type: {signal_type}
Signal date: {signal_date or "unknown"}
Signal summary: {signal_summary or "No additional context provided."}

Return a JSON object with exactly these fields:

{{
  "company": "{company}",
  "domain": "{domain}",
  "one_liner": "What does this company do in one sentence",
  "founders": ["Name — Title", "..."],
  "employees_estimate": 0,
  "funding_stage": "seed | series_a | series_b | bootstrap | unknown",
  "funding_amount": "e.g. $4M or unknown",
  "who_they_sell_to": "Description of their buyer (title, company size, industry)",
  "business_model": "b2b_saas | b2b | b2c | marketplace | unknown",
  "b2b_saas": true,
  "seed_to_series_a": true,
  "employees_5_30": true,
  "technical_buyer": true,
  "us_based": true,
  "needs_pipeline": true,
  "hubspot_or_open": true,
  "icp_verdict": "yes | no | maybe",
  "icp_reason": "One sentence explaining the verdict",
  "pain_hypothesis": "What is their most likely GTM pain right now, given their stage and signal? 2–3 sentences.",
  "signal_context": "Why does this signal matter for them specifically?",
  "confidence": "high | medium | low",
  "confidence_notes": "What you found vs. what you guessed. Be specific.",
  "sources_used": ["list of URLs or data sources referenced"]
}}

Use what you know about this company. If you don't know something, set it to null or "unknown" — do not fabricate.
For the boolean fields (b2b_saas, seed_to_series_a, etc.) return true/false/null.
The pain_hypothesis should lead with their specific situation, not generic GTM advice."""

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
        # Best-effort: strip any accidental markdown fences
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned)

    result["_model"] = MODEL
    result["_input_tokens"] = message.usage.input_tokens
    result["_output_tokens"] = message.usage.output_tokens

    return result


# ─── CLI ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--company", "-c", required=True, help="Company name")
@click.option("--domain", "-d", required=True, help="Company domain (e.g. acme.com)")
@click.option("--signal", "-s", required=True,
              type=click.Choice(["funding", "hiring", "gtm_struggle", "agency_churn", "tool_adoption", "manual"]),
              help="Signal type that triggered research")
@click.option("--signal-date", default=None, help="Signal date YYYY-MM-DD")
@click.option("--signal-summary", default="", help="Free-text description of the signal")
@click.option("--brain-path", default="brain", help="Path to brain/ directory")
@click.option("--output", "-o", default=None, help="Write result to this JSON file path")
def cli(company, domain, signal, signal_date, signal_summary, brain_path, output):
    """Research one account with Claude and print structured output."""
    brain_context = load_brain(brain_path)

    click.echo(f"Researching {company} ({domain})...")
    result = research_account(
        company=company,
        domain=domain,
        signal_type=signal,
        signal_date=signal_date,
        signal_summary=signal_summary,
        brain_context=brain_context,
    )

    pretty = json.dumps(result, indent=2)

    if output:
        Path(output).write_text(pretty)
        click.echo(f"Saved to {output}")
    else:
        click.echo(pretty)

    click.echo(f"\n[tokens: {result['_input_tokens']} in / {result['_output_tokens']} out]")


if __name__ == "__main__":
    cli()
