"""
DeployGTM — Pre-Call Research Brief

Generates a tight, conversation-focused brief before a discovery or close call.
Different from research.py (which optimizes for cold outreach).
This optimizes for BEING IN THE ROOM — what to know, what to ask, how to close.

Looks up existing output/ JSON first (fast). Falls back to Claude research if
the account hasn't been through the pipeline yet.

Usage:
  python scripts/precall.py --company "Acme AI" --domain acme.ai
  python scripts/precall.py --company "Acme AI" --domain acme.ai --contact "Evan Park"
  python scripts/precall.py --domain acme.ai --contact evan@acme.ai
  make precall DOMAIN=acme.ai CONTACT="Evan Park"

Output: printed to stdout. Pipe to a file or copy from terminal.
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Optional

import anthropic
import click
import yaml
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"
ROOT = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "output"
BRAIN_DIR = ROOT / "brain"


def load_config() -> dict:
    with open(ROOT / "config.yaml") as f:
        return yaml.safe_load(f)


def load_brain() -> str:
    files = ["personas.md", "messaging.md", "product.md", "objections.md"]
    sections = []
    for fname in files:
        fpath = BRAIN_DIR / fname
        if fpath.exists():
            sections.append(fpath.read_text().strip())
    return "\n\n---\n\n".join(sections)


def find_output_file(domain: str) -> Optional[dict]:
    """Look up existing pipeline output for this domain."""
    slug = domain.lower().replace(".", "_").replace("-", "_")
    candidates = list(OUTPUT_DIR.glob(f"*{slug}*.json")) + list(OUTPUT_DIR.glob(f"*{domain.replace('.','_')}*.json"))
    if not candidates:
        return None
    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    try:
        return json.loads(newest.read_text())
    except Exception:
        return None


def generate_brief(
    company: str,
    domain: str,
    contact_name: Optional[str],
    pipeline_data: Optional[dict],
    brain_context: str,
    api_key: Optional[str] = None,
) -> str:
    client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    if pipeline_data:
        research = pipeline_data.get("research", {})
        score = pipeline_data.get("score", {})
        signal = pipeline_data.get("signal", {})
        contacts = pipeline_data.get("contacts", [])
        outreach = pipeline_data.get("outreach", {})

        contact_info = ""
        if contact_name:
            matched = next(
                (c for c in contacts if contact_name.lower() in c.get("name", "").lower()
                 or contact_name.lower() == c.get("email", "").lower()),
                None
            )
            if matched:
                contact_info = f"""
Name: {matched.get('name', contact_name)}
Title: {matched.get('title', 'unknown')}
Email: {matched.get('email', '')}
LinkedIn: {matched.get('linkedin_url', '')}
"""
            else:
                contact_info = f"Name: {contact_name} (not enriched — check LinkedIn manually)"

        context = f"""
## Company: {company} ({domain})

### Research
{research.get('summary', 'Not available')}

### Pain hypothesis
{research.get('pain_hypothesis', 'Not available')}

### ICP verdict
{research.get('icp_verdict', 'unknown')} (confidence: {research.get('confidence', '?')})

### Signal that triggered outreach
Type: {signal.get('type', 'unknown')}
Date: {signal.get('date', '?')}
Summary: {signal.get('summary', signal.get('signal_summary', '?'))}

### Score
ICP Fit: {score.get('icp_fit', '?')} / 5
Signal Strength: {score.get('signal_strength', '?')} / 3
Priority: {score.get('priority', '?')}
Rationale: {score.get('rationale', '')}

### Contact
{contact_info or 'No specific contact provided'}

### Outreach sent
{f"Initial email sent to: {list(outreach.keys())}" if outreach else "No outreach sent yet"}
"""
    else:
        context = f"""
## Company: {company} ({domain})

Note: This account has not been through the pipeline yet.
Working from first principles — research the company from your training data.
Contact: {contact_name or 'unknown'}
"""

    system_prompt = f"""You are DeployGTM's pre-call research assistant. You generate focused, conversational call prep briefs.

The caller is Matthew Stegenga — 10+ years B2B SaaS sales, founder-seller background, technical understanding of GTM stacks. He's about to get on a discovery or close call and needs 5 minutes of preparation, not a research essay.

## About DeployGTM
{brain_context[:1500]}

## Rules
- Every section should be SHORT. Bullets, not paragraphs.
- Focus on WHAT TO SAY and WHAT TO LISTEN FOR — not background trivia.
- Discovery questions should be open-ended and reveal pain, budget readiness, or decision process.
- Objections should have a 1-sentence response.
- The close language should feel natural and direct, not scripted.
- If data is missing, say "unknown — ask." Don't hallucinate specifics.
- Today's date: {date.today().isoformat()}"""

    user_prompt = f"""Generate a pre-call brief for this account.

{context}

Return a structured brief with these sections:

1. **In the room** (3 bullets): The most important things to know walking into this call. Context that should be in your head before they say a word.

2. **Why they might be calling** (2-3 bullets): Based on their signal and situation, what are they probably hoping to get from this call? What would make them feel like the 30 minutes was worth it?

3. **Where the pain lives** (2-3 bullets): The most specific pain points to probe — not generic "they need pipeline" but specific to their stage, signal, and persona.

4. **5 discovery questions**: Sharp, open-ended questions that will surface the real situation. Each question should be one sentence. Ordered by importance.

5. **Likely objections + 1-sentence responses** (2-3 objections): The ones most likely to come up in this specific conversation.

6. **How to position DeployGTM here**: One paragraph, max 3 sentences. Specific to this company's situation — not a generic pitch.

7. **How to close this call** (2-3 sentences): The exact words Matthew might use to end the call with a clear next step. Should feel conversational, not scripted.

8. **Watch-outs** (1-2 bullets): Anything that might be a disqualifier or red flag to probe during the call."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )

    return response.content[0].text.strip()


# ─── CLI ──────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--company", "-c", default=None, help="Company name")
@click.option("--domain", "-d", required=True, help="Company domain (acme.com)")
@click.option("--contact", default=None, help="Contact name or email (optional)")
@click.option("--fresh", is_flag=True, default=False,
              help="Skip output/ lookup and generate from scratch")
def precall(company: Optional[str], domain: str, contact: Optional[str], fresh: bool):
    """Generate a focused pre-call brief for a discovery or close call."""
    pipeline_data = None
    if not fresh:
        pipeline_data = find_output_file(domain)

    if pipeline_data:
        company = company or pipeline_data.get("company", domain)
        click.echo(f"Found pipeline data for {company}. Generating call brief...\n")
    else:
        company = company or domain
        click.echo(f"No pipeline data found for {domain}. Generating from first principles...\n")

    brain_context = load_brain()

    brief = generate_brief(
        company=company,
        domain=domain,
        contact_name=contact,
        pipeline_data=pipeline_data,
        brain_context=brain_context,
    )

    separator = "─" * 60
    header = f"Pre-Call Brief — {company}"
    if contact:
        header += f" / {contact}"
    header += f"  ({date.today().isoformat()})"

    click.echo(f"\n{separator}")
    click.echo(f"  {header}")
    click.echo(f"{separator}\n")
    click.echo(brief)
    click.echo(f"\n{separator}\n")


if __name__ == "__main__":
    precall()
