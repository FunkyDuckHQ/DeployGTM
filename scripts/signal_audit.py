"""
DeployGTM — Signal Audit Engagement Runner

Automates the 2-week Signal Audit workflow ($3,500 engagement).

Week 1: Discovery + Signal Mapping
  - Load client intake (ICP, personas, value prop, current tools)
  - Build target account list (50–100 companies)
  - Map signals relevant to their specific product
  - Set up BirdDog monitoring
  - Configure client brain (Octave replacement)

Week 2: Enrichment + Deliverable
  - Run batch enrichment on all target accounts
  - Generate pain hypotheses
  - Generate 3–5 outreach templates per persona
  - Build architecture recommendation
  - Compile deliverable package

Usage:
  # Start a new Signal Audit engagement
  python scripts/signal_audit.py new --client acme --domain acme.com

  # Run Week 1 workflow (after filling in client intake)
  python scripts/signal_audit.py week1 --client acme

  # Run Week 2 workflow (enrichment + deliverable)
  python scripts/signal_audit.py week2 --client acme

  # Compile final deliverable package
  python scripts/signal_audit.py deliverable --client acme

  # Show current engagement status
  python scripts/signal_audit.py status --client acme
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import anthropic
import click
import yaml
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

MODEL = "claude-sonnet-4-6"
PROJECTS_DIR = Path("projects")
BRAIN_CLIENTS_DIR = Path("brain/clients")


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def client_dir(client: str) -> Path:
    return PROJECTS_DIR / client


def client_brain_dir(client: str) -> Path:
    return BRAIN_CLIENTS_DIR / client


def client_output_dir(client: str) -> Path:
    out = Path("output") / client
    out.mkdir(parents=True, exist_ok=True)
    return out


def load_client_context(client: str) -> dict:
    ctx_file = client_dir(client) / "context.md"
    if not ctx_file.exists():
        raise FileNotFoundError(
            f"Client context not found: {ctx_file}\n"
            f"Run: python scripts/signal_audit.py new --client {client}"
        )
    return {"raw": ctx_file.read_text(), "path": str(ctx_file)}


def load_client_brain(client: str) -> str:
    """Load client-specific brain. Falls back to default brain if no client brain exists."""
    client_brain = client_brain_dir(client)
    base_brain = Path("brain")

    files = ["product.md", "icp.md", "personas.md", "messaging.md", "objections.md"]
    sections = []

    for fname in files:
        # Prefer client-specific override, fall back to default
        client_file = client_brain / fname
        default_file = base_brain / fname
        target = client_file if client_file.exists() else default_file

        if target.exists():
            sections.append(f"## {fname}\n\n{target.read_text().strip()}")

    # Also include the client's own context
    ctx_file = client_dir(client) / "context.md"
    if ctx_file.exists():
        sections.append(f"## client_context.md\n\n{ctx_file.read_text().strip()}")

    return "\n\n---\n\n".join(sections)


# ─── new ──────────────────────────────────────────────────────────────────────

CLIENT_CONTEXT_TEMPLATE = """# {client_title} — Signal Audit Context

## Status
Week 1 — Discovery in progress

## Engagement type
Signal Audit ($3,500 / 2-week)

## Client overview
- **Company:** {client_title}
- **Website:** https://{domain}
- **Stage:** [seed | series_a]
- **Funding amount:** unknown
- **Team size:** unknown
- **Product:** [What they build in one sentence]
- **Primary buyer:** [Title, company size, industry]

## Their ICP (who THEY sell to)
- Company type:
- Company size:
- Industry:
- Buyer title:
- Key pain points:

## Signals to monitor (what indicates a buyer is ready for their product)
-
-
-

## Current tools
- CRM:
- Outreach:
- Other:

## What's working in their GTM today
-

## What's broken or missing
-

## Intake call notes
[Paste notes from the 60-min intake interview here]

## Deliverables checklist
- [ ] Target account list (50–100 companies)
- [ ] Signal report (which accounts have active buying signals)
- [ ] 3–5 outreach message templates by persona
- [ ] System architecture recommendation
- [ ] BirdDog account list (30–50 accounts, already monitoring)
- [ ] Client brain / Octave configuration

## Tracking
| Date | Action | Result | Learning |
|------|--------|--------|---------|
| {today} | Engagement started | | |
"""

CLIENT_BRAIN_ICP_TEMPLATE = """# {client_title} — ICP (Who They Target)

## Fill this in from the intake call

**Company type:**
**Stage:**
**Team size:**
**Industry:**
**Buyer title:**
**Key pain points:**

## Signals that indicate their buyer is ready
-
-
-
"""

CLIENT_BRAIN_PERSONAS_TEMPLATE = """# {client_title} — Buyer Personas

## Fill this in from the intake call

## Persona 1: [Title]
**Pain:**
**What they want:**
**How to open:**

## Persona 2: [Title]
**Pain:**
**What they want:**
**How to open:**
"""

CLIENT_BRAIN_MESSAGING_TEMPLATE = """# {client_title} — Messaging Framework

## Product value prop (one sentence)
[What the client's product does for the buyer]

## Core rules
- Lead with signal
- Bridge to their buyer's specific pain
- Offer a concrete next step
- Under 100 words for primary outreach

## Message templates

### Persona 1: [Title]
**Subject:**
**Body:**

### Persona 2: [Title]
**Subject:**
**Body:**
"""


@click.group()
def cli():
    """Signal Audit engagement runner."""
    pass


@cli.command()
@click.option("--client", "-c", required=True, help="Client slug (lowercase, hyphens ok, e.g. acme-corp)")
@click.option("--domain", "-d", required=True, help="Client's domain (e.g. acme.com)")
def new(client, domain):
    """Create project folder and brain stub for a new Signal Audit client."""
    proj_dir = client_dir(client)
    brain_dir = client_brain_dir(client)

    if proj_dir.exists():
        click.echo(f"Project already exists: {proj_dir}")
        if not click.confirm("Re-initialize? (existing files will not be overwritten)"):
            return

    proj_dir.mkdir(parents=True, exist_ok=True)
    brain_dir.mkdir(parents=True, exist_ok=True)
    client_output_dir(client)

    client_title = client.replace("-", " ").replace("_", " ").title()
    today = date.today().isoformat()

    # Project files
    ctx_file = proj_dir / "context.md"
    if not ctx_file.exists():
        ctx_file.write_text(CLIENT_CONTEXT_TEMPLATE.format(
            client_title=client_title, domain=domain, today=today
        ))

    handoff_file = proj_dir / "handoff.md"
    if not handoff_file.exists():
        handoff_template = Path("master/templates/handoff-template.md")
        if handoff_template.exists():
            handoff_file.write_text(
                f"# {client_title} — Handoff\n\n" + handoff_template.read_text()
            )

    loops_file = proj_dir / "open-loops.md"
    if not loops_file.exists():
        loops_file.write_text(f"# {client_title} — Open Loops\n\n"
                              "## Waiting on\n-\n\n## Need to decide\n-\n\n"
                              "## Need to build\n-\n\n## Blocked by\n-\n")

    # Client brain stubs
    for fname, template in [
        ("icp.md", CLIENT_BRAIN_ICP_TEMPLATE),
        ("personas.md", CLIENT_BRAIN_PERSONAS_TEMPLATE),
        ("messaging.md", CLIENT_BRAIN_MESSAGING_TEMPLATE),
    ]:
        fpath = brain_dir / fname
        if not fpath.exists():
            fpath.write_text(template.format(client_title=client_title))

    # Targets CSV for batch runner
    targets_file = proj_dir / "targets.csv"
    if not targets_file.exists():
        targets_file.write_text("company,domain,signal_type,signal_date,signal_source,signal_summary\n")

    click.echo(f"\n✓ Created Signal Audit project: {proj_dir}")
    click.echo(f"✓ Created client brain stubs: {brain_dir}")
    click.echo(f"\nNext steps:")
    click.echo(f"  1. Fill in {ctx_file}")
    click.echo(f"  2. Fill in {brain_dir}/icp.md, personas.md, messaging.md")
    click.echo(f"  3. Populate {targets_file} with 50–100 target accounts")
    click.echo(f"  4. Run: python scripts/signal_audit.py week1 --client {client}")


# ─── status ───────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--client", "-c", required=True)
def status(client):
    """Show current status of a Signal Audit engagement."""
    proj_dir = client_dir(client)
    if not proj_dir.exists():
        click.echo(f"Project not found: {proj_dir}")
        return

    ctx = (proj_dir / "context.md").read_text() if (proj_dir / "context.md").exists() else ""
    targets_file = proj_dir / "targets.csv"
    out_dir = client_output_dir(client)

    target_count = 0
    if targets_file.exists():
        with open(targets_file) as f:
            target_count = sum(1 for line in f) - 1  # subtract header

    output_files = list(out_dir.glob("*.json"))
    scored = 0
    with_outreach = 0
    for f in output_files:
        try:
            data = json.loads(f.read_text())
            if data.get("score", {}).get("priority"):
                scored += 1
            if data.get("outreach"):
                with_outreach += 1
        except Exception:
            pass

    click.echo(f"\n{'='*50}")
    click.echo(f"  {client.replace('-', ' ').title()} — Signal Audit Status")
    click.echo(f"{'='*50}")
    click.echo(f"  Target accounts loaded:  {target_count}")
    click.echo(f"  Accounts enriched:       {scored}")
    click.echo(f"  Outreach generated:      {with_outreach}")
    click.echo(f"  Output files:            {len(output_files)}")

    # Parse checklist from context.md
    checklist_items = [line.strip() for line in ctx.split("\n") if line.strip().startswith("- [")]
    if checklist_items:
        click.echo(f"\n  Deliverables:")
        for item in checklist_items:
            click.echo(f"    {item}")
    click.echo()


# ─── week1 ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--client", "-c", required=True)
@click.option("--config", "config_path", default="config.yaml")
def week1(client, config_path):
    """
    Week 1: Build target account list + set up BirdDog monitoring.

    Before running:
      1. Complete the intake interview
      2. Fill in projects/<client>/context.md
      3. Fill in brain/clients/<client>/icp.md and personas.md
    """
    proj_dir = client_dir(client)
    targets_file = proj_dir / "targets.csv"

    click.echo(f"\nSignal Audit — Week 1: {client}")
    click.echo("="*50)

    # Check prerequisites
    brain_icp = client_brain_dir(client) / "icp.md"
    if brain_icp.exists():
        content = brain_icp.read_text()
        if "Fill this in" in content:
            click.echo(f"\n⚠️  brain/clients/{client}/icp.md has not been filled in yet.")
            click.echo(f"    Complete the intake interview first, then update that file.")
            if not click.confirm("Continue anyway?", default=False):
                return

    # Count targets
    if targets_file.exists():
        with open(targets_file) as f:
            rows = [l for l in f if l.strip() and not l.startswith("company")]
        click.echo(f"\nFound {len(rows)} target accounts in {targets_file}")
    else:
        click.echo(f"\n⚠️  No targets file found at {targets_file}")
        click.echo("    Add target accounts to this CSV and re-run.")
        return

    if not rows:
        click.echo("    Targets file is empty. Populate it first.")
        return

    # Add accounts to BirdDog
    config = load_config(config_path)
    birddog_enabled = config.get("tools", {}).get("birddog", {}).get("enabled", False)

    if birddog_enabled:
        click.echo(f"\nAdding {len(rows)} accounts to BirdDog...")
        result = subprocess.run([
            sys.executable, "scripts/birddog.py", "add-accounts",
            "--input", str(targets_file),
        ], capture_output=True, text=True)
        click.echo(result.stdout)
        if result.returncode != 0:
            click.echo(result.stderr, err=True)
    else:
        click.echo("\nBirdDog is disabled — accounts will be scored via manual signals only.")
        click.echo("Enable in config.yaml once your BirdDog API key is set.")

    click.echo(f"\n{'─'*50}")
    click.echo("Week 1 checklist:")
    click.echo("  ✓ Target account list loaded")
    click.echo(f"  {'✓' if birddog_enabled else '○'} BirdDog monitoring active")
    click.echo("  ○ Octave / client brain configured — fill in brain/clients/<client>/")
    click.echo("  ○ Signal mapping complete — update context.md 'Signals to monitor'")
    click.echo(f"\nWhen ready for Week 2:")
    click.echo(f"  python scripts/signal_audit.py week2 --client {client}")


# ─── week2 ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--client", "-c", required=True)
@click.option("--skip-below", default=5, help="Skip accounts with priority below this")
@click.option("--config", "config_path", default="config.yaml")
def week2(client, skip_below, config_path):
    """
    Week 2: Batch enrichment + outreach + deliverable prep.

    Runs the full pipeline on all target accounts, using the client's
    brain instead of the default DeployGTM brain.
    """
    proj_dir = client_dir(client)
    targets_file = proj_dir / "targets.csv"

    if not targets_file.exists():
        click.echo(f"Targets file not found: {targets_file}")
        return

    click.echo(f"\nSignal Audit — Week 2: {client}")
    click.echo("="*50)
    click.echo("Running batch enrichment (this takes a few minutes)...\n")

    # Patch brain path for this run by temporarily pointing to client brain
    # We do this by running batch.py with a custom env that overrides brain path
    # The cleanest approach: create a temp config pointing to client brain
    import tempfile

    config = load_config(config_path)
    client_config = dict(config)
    client_config["brain"] = {"path": str(client_brain_dir(client))}
    client_config["output"] = {"path": str(client_output_dir(client))}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(client_config, tmp)
        tmp_config = tmp.name

    try:
        result = subprocess.run([
            sys.executable, "scripts/batch.py", "run",
            "--input", str(targets_file),
            "--skip-below", str(skip_below),
            "--resume",
            "--config", tmp_config,
        ], check=False)
    finally:
        Path(tmp_config).unlink(missing_ok=True)

    if result.returncode == 0:
        click.echo(f"\nEnrichment complete. Output in: output/{client}/")
        click.echo(f"\nNext: compile the deliverable")
        click.echo(f"  python scripts/signal_audit.py deliverable --client {client}")
    else:
        click.echo("\nBatch run had errors — check output above.", err=True)


# ─── deliverable ──────────────────────────────────────────────────────────────

@cli.command()
@click.option("--client", "-c", required=True)
@click.option("--config", "config_path", default="config.yaml")
def deliverable(client, config_path):
    """
    Compile the final Signal Audit deliverable package.

    Generates:
      - deliverable/signal_report.md
      - deliverable/target_accounts.csv (HubSpot import ready)
      - deliverable/outreach_templates.md
      - deliverable/architecture_recommendation.md
    """
    proj_dir = client_dir(client)
    out_dir = client_output_dir(client)
    deliverable_dir = proj_dir / "deliverable"
    deliverable_dir.mkdir(exist_ok=True)

    client_title = client.replace("-", " ").replace("_", " ").title()
    today = date.today().isoformat()

    click.echo(f"\nCompiling deliverable for {client_title}...")

    # Load all output files
    output_files = sorted(out_dir.glob("*.json"))
    records = []
    for f in output_files:
        try:
            records.append(json.loads(f.read_text()))
        except Exception:
            pass

    click.echo(f"  {len(records)} enriched accounts")

    # ── 1. Signal Report ──────────────────────────────────────────────────
    from report import build_report
    signal_report = build_report(
        records,
        since=(date.today().replace(day=1)).isoformat(),
        until=today,
        hs_stages={},
        project=client,
    )
    signal_report_path = deliverable_dir / "signal_report.md"
    signal_report_path.write_text(signal_report)
    click.echo(f"  ✓ {signal_report_path.name}")

    # ── 2. Target accounts CSV ────────────────────────────────────────────
    import csv
    accounts_path = deliverable_dir / "target_accounts.csv"
    fieldnames = [
        "Company", "Domain", "Signal Type", "Signal Date", "Signal Summary",
        "ICP Fit", "Signal Strength", "Priority", "Action",
        "Pain Hypothesis", "Contacts Found", "Confidence",
    ]
    with open(accounts_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        sorted_records = sorted(records, key=lambda r: r.get("score", {}).get("priority", 0), reverse=True)
        for r in sorted_records:
            sc = r.get("score", {})
            sig = r.get("signal", {})
            research = r.get("research", {})
            contacts = [c for c in r.get("contacts", []) if c.get("email")]
            writer.writerow({
                "Company": r.get("company", ""),
                "Domain": r.get("domain", ""),
                "Signal Type": sig.get("type", ""),
                "Signal Date": sig.get("date", ""),
                "Signal Summary": sig.get("summary", ""),
                "ICP Fit": sc.get("icp_fit", ""),
                "Signal Strength": sc.get("signal_strength", ""),
                "Priority": sc.get("priority", ""),
                "Action": sc.get("action", ""),
                "Pain Hypothesis": research.get("pain_hypothesis", ""),
                "Contacts Found": len(contacts),
                "Confidence": research.get("confidence", ""),
            })
    click.echo(f"  ✓ {accounts_path.name}")

    # ── 3. Outreach templates ─────────────────────────────────────────────
    templates_path = deliverable_dir / "outreach_templates.md"
    template_lines = [
        f"# {client_title} — Outreach Templates",
        f"Generated: {today}",
        "",
        "These templates are calibrated to your ICP, buyer personas, and active signals.",
        "Personalize the [bracketed] fields before sending.",
        "",
    ]

    # Collect unique outreach messages across all records, deduplicated by persona
    seen_personas = set()
    for r in sorted_records:
        for email, outreach in r.get("outreach", {}).items():
            persona = outreach.get("persona", "")
            if persona in seen_personas:
                continue
            seen_personas.add(persona)

            primary = outreach.get("primary", {})
            f1 = outreach.get("followup_1", {})
            f2 = outreach.get("followup_2", {})
            company = r.get("company", "")
            signal_type = r.get("signal", {}).get("type", "")

            template_lines += [
                f"## Persona: {persona.replace('_', ' ').title()} · Signal: {signal_type}",
                f"_Example account: {company}_",
                "",
                f"**Subject:** {primary.get('subject', '')}",
                "",
                "**Email:**",
                f"> {primary.get('body', '')}",
                "",
                f"**Follow-up 1 (day {f1.get('send_on_day', 3)}):**",
                f"> {f1.get('body', '')}",
                "",
                f"**Follow-up 2 (day {f2.get('send_on_day', 7)}):**",
                f"> {f2.get('body', '')}",
                "",
                "---",
                "",
            ]

    templates_path.write_text("\n".join(template_lines))
    click.echo(f"  ✓ {templates_path.name}")

    # ── 4. Architecture recommendation ───────────────────────────────────
    arch_path = deliverable_dir / "architecture_recommendation.md"
    arch = _generate_architecture_recommendation(client, client_title, records)
    arch_path.write_text(arch)
    click.echo(f"  ✓ {arch_path.name}")

    click.echo(f"\n{'='*50}")
    click.echo(f"Deliverable package: {deliverable_dir}/")
    click.echo(f"  {signal_report_path.name}")
    click.echo(f"  {accounts_path.name}")
    click.echo(f"  {templates_path.name}")
    click.echo(f"  {arch_path.name}")
    click.echo(f"\nNext: walk through with client in a 60-min call.")
    click.echo(f"Show them what BirdDog already caught. Then ask:")
    click.echo(f'  "Do you want to run this yourself or want us to operate it?"')


def _generate_architecture_recommendation(client: str, client_title: str, records: list[dict]) -> str:
    """Generate a system architecture recommendation for the client."""
    today = date.today().isoformat()
    total = len(records)
    high_priority = sum(1 for r in records if r.get("score", {}).get("priority", 0) >= 8)

    return f"""# {client_title} — System Architecture Recommendation

Generated: {today}

## What we built in the Signal Audit

In two weeks, we:
- Identified and enriched {total} target accounts matching your ICP
- Found {high_priority} accounts with active buying signals
- Built signal-led outreach templates for each buyer persona
- Started BirdDog monitoring on your top accounts

## What the full system looks like

```
Signal Layer (continuous)
  BirdDog monitors your target accounts for:
  → Funding announcements
  → Sales hiring posts
  → Leadership changes
  → Tech stack adoption
  → Competitor displacement signals

       ↓ Signal triggers enrichment

Intelligence Layer (per signal)
  Claude researches each triggered account:
  → ICP fit score (1–5)
  → Signal strength (1–3)
  → Pain hypothesis
  → Outreach angle

       ↓ Score ≥ 8 → activate

Activation Layer
  → Contact enriched via Apollo
  → Persona-specific message generated
  → Enrolled in HubSpot sequence
  → Follow-ups automated (day 3, day 7, day 14)

       ↓ Reply or engagement

Recapture + Measurement
  → Replied: move to pipeline, notify you
  → Website visit: re-engage with new angle
  → No response after 3 touches: park until next signal
  → Weekly signal report: what fired, what replied, what converted
```

## Recommended tools

| Layer | Tool | Why |
|-------|------|-----|
| Signal monitoring | BirdDog | Already active on your top 30 accounts |
| Messaging context | Octave brain | Already configured with your ICP and personas |
| Enrichment | Apollo (free tier) + Claude | Contact finding + research |
| CRM | HubSpot | Sequences, pipeline tracking, reporting |
| Orchestration | DeployGTM scripts | Ties everything together |

## Two options for next steps

### Option A: Run it yourself
You keep the deliverable. BirdDog and the Octave brain stay active.
When BirdDog fires a signal, use the enrichment playbook to process it.
Estimated time: 3–5 hours/week.

### Option B: We operate it for you
Pipeline Engine Retainer — $7,500/month.
We monitor signals daily, enrich and score every trigger, generate and send outreach,
manage HubSpot, and send you a weekly signal report.
You focus on closing the meetings we book.

The system is already built. The question is who runs it.
"""


if __name__ == "__main__":
    cli()
