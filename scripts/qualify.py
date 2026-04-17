"""
DeployGTM — Inbound Qualifier

Quick ICP qualification for inbound leads: replies to outreach, warm intros,
conference connections, referrals. Faster than the full pipeline — no Apollo
enrichment by default, just Claude research + brain/ scoring.

Produces a qualification brief: ICP verdict, service recommendation,
key questions to ask, and red flags to watch for.

Usage:
  python scripts/qualify.py run --company "Acme" --domain acme.com
  python scripts/qualify.py run --company "Acme" --domain acme.com \\
      --context "They replied to my cold email asking about pricing. CEO, 12-person team."
  python scripts/qualify.py run --company "Acme" --domain acme.com --enrich
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
    files = ["icp.md", "personas.md", "product.md", "objections.md"]
    sections = []
    for fname in files:
        fpath = brain_dir / fname
        if fpath.exists():
            sections.append(f"## {fname}\n\n{fpath.read_text().strip()}")
    return "\n\n---\n\n".join(sections)


def qualify_account(
    company: str,
    domain: str,
    context: str,
    brain_context: str,
    api_key: Optional[str] = None,
) -> dict:
    """
    Run Claude qualification on an inbound lead.

    Returns:
      icp_fit (1-5), icp_verdict, icp_reason,
      service_recommendation, service_rationale,
      questions_to_ask (list), red_flags (list),
      pain_hypothesis, confidence, one_liner
    """
    client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    system_prompt = f"""You are the DeployGTM inbound qualifier. Your job is to rapidly assess whether an inbound lead is a good fit for DeployGTM's services.

{brain_context}

Be direct and honest. Disqualify clearly when the fit isn't there. We'd rather work with 5 right clients than 20 wrong ones.

ICP scoring:
- 5: Perfect fit — B2B SaaS, Seed–Series A, 5–30 employees, no pipeline infrastructure, active buying signal, technical buyers, US-based
- 4: Strong fit — meets most criteria, one or two soft misses
- 3: Possible — worth a conversation but needs validation
- 2: Weak — significant gaps, proceed with caution
- 1: Disqualify — pre-product, B2C, wrong stage, or clear disqualifier present

Service recommendation:
- "Signal Audit ($3,500)" — they don't know what they need yet; diagnostic is the right entry
- "Pipeline Engine Retainer ($7,500/mo)" — they know the problem, need the system operated
- "Not qualified" — hard disqualifier present; decline or defer
- "More info needed" — can't assess without another conversation
"""

    user_prompt = f"""Qualify this inbound lead. Research the company and give me a full qualification brief.

COMPANY: {company}
DOMAIN: {domain}
CONTEXT (what we know about this inbound): {context or "No additional context provided."}

Return JSON only — no preamble, no markdown fences:
{{
  "icp_fit": <1-5>,
  "icp_verdict": "qualified" | "possible" | "disqualified",
  "icp_reason": "<2-3 sentence explanation of the fit score>",
  "pain_hypothesis": "<what they're probably experiencing right now>",
  "service_recommendation": "Signal Audit ($3,500)" | "Pipeline Engine Retainer ($7,500/mo)" | "Not qualified" | "More info needed",
  "service_rationale": "<why this service, not another>",
  "questions_to_ask": ["<sharp question 1>", "<sharp question 2>", "<sharp question 3>"],
  "red_flags": ["<red flag 1 if any>"],
  "one_liner": "<one sentence description of the company and their situation>",
  "confidence": "high" | "medium" | "low",
  "confidence_note": "<what would change the assessment>"
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
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


def print_qualification_brief(result: dict, company: str, domain: str) -> None:
    verdict = result.get("icp_verdict", "?").upper()
    fit = result.get("icp_fit", "?")
    rec = result.get("service_recommendation", "?")
    confidence = result.get("confidence", "?")

    verdict_color = {
        "QUALIFIED": "\033[32m",
        "POSSIBLE": "\033[33m",
        "DISQUALIFIED": "\033[31m",
    }.get(verdict, "")
    reset = "\033[0m"

    print(f"\n{'='*65}")
    print(f"  Qualification Brief — {company} ({domain})")
    print(f"{'='*65}")
    print(f"\n  {result.get('one_liner', '')}")
    print(f"\n  Verdict:     {verdict_color}{verdict}{reset}  (ICP Fit: {fit}/5, Confidence: {confidence})")
    print(f"  Recommend:   {rec}")
    print(f"\n  ICP Reason:")
    print(f"  {result.get('icp_reason', '')}")
    print(f"\n  Pain Hypothesis:")
    print(f"  {result.get('pain_hypothesis', '')}")
    print(f"\n  Service Rationale:")
    print(f"  {result.get('service_rationale', '')}")

    questions = result.get("questions_to_ask", [])
    if questions:
        print(f"\n  Questions to Ask:")
        for q in questions:
            print(f"  → {q}")

    red_flags = result.get("red_flags", [])
    if red_flags and red_flags[0]:
        print(f"\n  Red Flags:")
        for rf in red_flags:
            print(f"  ⚠  {rf}")

    note = result.get("confidence_note", "")
    if note:
        print(f"\n  Confidence Note: {note}")

    print(f"\n{'='*65}\n")


# ─── CLI ──────────────────────────────────────────────────────────────────────


@click.group()
def cli():
    """DeployGTM Inbound Qualifier — fast ICP assessment for inbound leads."""
    pass


@cli.command()
@click.option("--company", required=True, help="Company name.")
@click.option("--domain", required=True, help="Company domain (e.g. acme.com).")
@click.option("--context", default="", help="What we know about this inbound: reply content, referral context, signal that triggered the conversation.")
@click.option("--enrich", is_flag=True, default=False,
              help="Also run Apollo company enrichment before qualifying.")
@click.option("--brain", "brain_path", default="brain", show_default=True)
@click.option("--save", is_flag=True, default=False,
              help="Save qualification brief to output/<domain>_qualify.json")
def run(company: str, domain: str, context: str, enrich: bool,
        brain_path: str, save: bool):
    """Qualify an inbound lead against the DeployGTM ICP."""
    click.echo(f"\nQualifying: {company} ({domain})...")

    if enrich:
        try:
            from apollo import enrich_company
            click.echo("  Running Apollo enrichment...")
            apollo_data = enrich_company(domain)
            enrich_context = (
                f"Apollo data: {apollo_data.get('employee_count', '?')} employees, "
                f"industry: {apollo_data.get('industry', '?')}, "
                f"funding stage: {apollo_data.get('funding_stage', '?')}, "
                f"founded: {apollo_data.get('founded_year', '?')}."
            )
            context = f"{context}\n{enrich_context}".strip()
        except Exception as e:
            click.echo(f"  Apollo enrichment failed: {e}. Continuing without it.", err=True)

    brain_context = load_brain(brain_path)
    result = qualify_account(
        company=company,
        domain=domain,
        context=context,
        brain_context=brain_context,
    )

    print_qualification_brief(result, company, domain)

    if save:
        out_path = Path("output") / f"{domain.replace('.', '_')}_qualify.json"
        out_path.parent.mkdir(exist_ok=True)
        payload = {
            "company": company,
            "domain": domain,
            "context": context,
            "qualification": result,
        }
        out_path.write_text(json.dumps(payload, indent=2))
        click.echo(f"  Saved to {out_path}")


@cli.command()
@click.option("--file", "file_path", required=True, type=click.Path(exists=True),
              help="Existing pipeline output JSON to re-qualify.")
@click.option("--context", default="", help="Additional context for this re-qualification.")
@click.option("--brain", "brain_path", default="brain", show_default=True)
def requalify(file_path: str, context: str, brain_path: str):
    """Re-qualify an account from an existing pipeline output file."""
    data = json.loads(Path(file_path).read_text())
    company = data.get("company", "")
    domain = data.get("domain", "")

    existing_context = []
    research = data.get("research", {})
    if research.get("one_liner"):
        existing_context.append(f"Prior research: {research['one_liner']}")
    if research.get("pain_hypothesis"):
        existing_context.append(f"Pain hypothesis: {research['pain_hypothesis']}")
    score = data.get("score", {})
    if score.get("priority"):
        existing_context.append(
            f"Prior score: ICP Fit {score.get('icp_fit')}/5, "
            f"Signal Strength {score.get('signal_strength')}/3, "
            f"Priority {score.get('priority')}/15"
        )
    signal = data.get("signal", {})
    if signal.get("type"):
        existing_context.append(
            f"Original signal: {signal['type']} on {signal.get('date', '?')}"
        )

    full_context = "\n".join(existing_context)
    if context:
        full_context = f"{full_context}\nNew context: {context}".strip()

    click.echo(f"\nRe-qualifying: {company} ({domain})...")
    brain_context = load_brain(brain_path)
    result = qualify_account(
        company=company,
        domain=domain,
        context=full_context,
        brain_context=brain_context,
    )

    print_qualification_brief(result, company, domain)


if __name__ == "__main__":
    cli()
