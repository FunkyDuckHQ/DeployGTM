"""
DeployGTM — Transcript Processor

Processes voice memo transcripts and raw notes into structured project updates.

The context-engine.md workflow:
  1. Raw material lands in Google Drive Transcript Inbox (or is pasted here)
  2. Claude reads the transcript and extracts what matters
  3. Output is a structured session summary ready to update project files

What it produces for each transcript:
  - One-line summary
  - What matters / key decisions
  - Open loops / unresolved questions
  - Next 3 actions
  - Reusable language (any phrasing worth keeping)
  - Which project(s) were discussed

Can optionally write directly to the relevant project files
(context.md, handoff.md, open-loops.md) — always shows diff and confirms first.

Usage:
  # Process a transcript file
  python scripts/transcript.py process --file ~/Desktop/voice_memo.txt

  # Process and update project files (confirms before writing)
  python scripts/transcript.py process --file ~/Desktop/voice_memo.txt --update-project

  # Paste transcript interactively (end with Ctrl+D)
  python scripts/transcript.py process --stdin

  # Process a transcript and specify which project it belongs to
  python scripts/transcript.py process --file ~/Desktop/memo.txt --project mindra
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import anthropic
import click
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

MODEL = "claude-sonnet-4-6"

PROJECTS_DIR = Path("projects")


def list_projects() -> list[str]:
    """Return names of all project folders."""
    if not PROJECTS_DIR.exists():
        return []
    return [p.name for p in PROJECTS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")]


def extract_session_summary(
    transcript: str,
    project_hint: Optional[str] = None,
    api_key: Optional[str] = None,
) -> dict:
    """
    Use Claude to extract a structured session summary from a transcript.

    Returns dict with: summary, what_matters, open_loops, next_actions,
    reusable_language, projects_mentioned, decisions_made
    """
    client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    known_projects = list_projects()

    system_prompt = f"""You are the context engine for DeployGTM, Matthew Stegenga's GTM engineering practice.
Your job is to read raw voice memo transcripts and working notes, then extract exactly what matters.

Known active projects: {', '.join(known_projects) if known_projects else 'none yet'}

Rules:
- Be ruthlessly concise. One-liners over paragraphs.
- Separate what was decided from what is still open.
- Capture exact phrasing that should be reused in outreach or documents.
- Identify which project(s) are discussed by name.
- Do not invent context. If something is unclear, flag it as an open loop.
- Respond with valid JSON only. No markdown fences."""

    user_prompt = f"""Process this transcript and return a structured session summary.

{f'Project context hint: {project_hint}' if project_hint else ''}

TRANSCRIPT:
{transcript}

Return a JSON object with exactly these fields:

{{
  "one_line_summary": "What this session was about in one sentence",
  "what_matters": [
    "Key insight or decision (one per item)",
    "..."
  ],
  "decisions_made": [
    "A decision that was reached and should be treated as final",
    "..."
  ],
  "open_loops": [
    "Unresolved question or blocker",
    "..."
  ],
  "next_actions": [
    "Specific next action (verb + noun)",
    "...",
    "..."
  ],
  "reusable_language": [
    "Exact phrase worth keeping for outreach, positioning, or docs",
    "..."
  ],
  "projects_mentioned": ["project-name-1", "project-name-2"],
  "primary_project": "the single most relevant project, or null if unclear",
  "session_type": "client_work | job_process | internal | strategy | research | other",
  "follow_up_needed": true,
  "notes_for_handoff": "2-3 sentences a fresh model needs to pick this up cold"
}}

Only include items that are actually in the transcript. Empty arrays over invented content."""

    message = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": user_prompt}],
        system=system_prompt,
    )

    raw = message.content[0].text.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned)

    result["_model"] = MODEL
    result["_tokens"] = message.usage.input_tokens + message.usage.output_tokens
    result["_date"] = date.today().isoformat()

    return result


def format_session_for_display(summary: dict) -> str:
    """Format extraction result for terminal output."""
    lines = [
        f"\n{'='*60}",
        f"  {summary.get('one_line_summary', '')}",
        f"{'='*60}",
    ]

    if summary.get("what_matters"):
        lines.append("\nWhat matters:")
        for item in summary["what_matters"]:
            lines.append(f"  - {item}")

    if summary.get("decisions_made"):
        lines.append("\nDecisions made:")
        for item in summary["decisions_made"]:
            lines.append(f"  ✓ {item}")

    if summary.get("open_loops"):
        lines.append("\nOpen loops:")
        for item in summary["open_loops"]:
            lines.append(f"  ? {item}")

    if summary.get("next_actions"):
        lines.append("\nNext actions:")
        for i, item in enumerate(summary["next_actions"][:3], 1):
            lines.append(f"  {i}. {item}")

    if summary.get("reusable_language"):
        lines.append("\nReusable language:")
        for item in summary["reusable_language"]:
            lines.append(f'  "{item}"')

    if summary.get("notes_for_handoff"):
        lines.append(f"\nHandoff note: {summary['notes_for_handoff']}")

    lines.append(f"\nProject: {summary.get('primary_project') or 'unspecified'}")
    lines.append(f"Tokens used: {summary.get('_tokens', '?')}\n")

    return "\n".join(lines)


def update_project_open_loops(project: str, new_loops: list[str], confirm: bool = True) -> bool:
    """Append new open loops to a project's open-loops.md."""
    loops_file = PROJECTS_DIR / project / "open-loops.md"
    if not loops_file.exists():
        click.echo(f"  open-loops.md not found for {project}")
        return False

    current = loops_file.read_text()
    additions = "\n".join(f"- {loop}" for loop in new_loops)
    updated = f"{current}\n\n## Added {date.today().isoformat()}\n{additions}\n"

    click.echo(f"\n  Would add to {loops_file}:")
    click.echo(f"  {additions}")

    if confirm and not click.confirm("  Write this?", default=True):
        return False

    loops_file.write_text(updated)
    return True


def update_project_handoff(project: str, summary: dict, confirm: bool = True) -> bool:
    """Update a project's handoff.md with session summary."""
    handoff_file = PROJECTS_DIR / project / "handoff.md"
    if not handoff_file.exists():
        click.echo(f"  handoff.md not found for {project}")
        return False

    current = handoff_file.read_text()

    # Build the "What changed in the last session" block
    session_block = f"\n## Session update — {date.today().isoformat()}\n"
    session_block += f"{summary.get('one_line_summary', '')}\n\n"
    if summary.get("what_matters"):
        session_block += "What changed:\n"
        for item in summary["what_matters"][:3]:
            session_block += f"- {item}\n"
    if summary.get("next_actions"):
        session_block += "\nNext actions:\n"
        for i, item in enumerate(summary["next_actions"][:3], 1):
            session_block += f"{i}. {item}\n"

    click.echo(f"\n  Would append to {handoff_file}:")
    click.echo(session_block)

    if confirm and not click.confirm("  Append this?", default=True):
        return False

    handoff_file.write_text(current + session_block)
    return True


def save_project_transcript_summary(project: str, summary: dict) -> Path:
    """
    Persist transcript extraction JSON under projects/<project>/transcripts/.
    This provides durable machine-readable context for downstream strategy assembly.
    """
    transcript_dir = PROJECTS_DIR / project / "transcripts"
    transcript_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_file = transcript_dir / f"{stamp}_summary.json"
    out_file.write_text(json.dumps(summary, indent=2))
    return out_file


# ─── CLI ──────────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """Process voice memo transcripts into structured project updates."""
    pass


@cli.command()
@click.option("--file", "-f", "input_file", default=None,
              help="Path to transcript text file")
@click.option("--stdin", "from_stdin", is_flag=True,
              help="Read transcript from stdin (pipe or paste)")
@click.option("--project", "-p", default=None,
              help="Project name hint (e.g. mindra, peregrine-space)")
@click.option("--update-project", is_flag=True,
              help="Write extracted open loops + session note to project files (confirms first)")
@click.option("--output", "-o", default=None,
              help="Save full JSON output to file")
@click.option("--save-project-summary/--no-save-project-summary", default=True,
              help="Save JSON summary to projects/<project>/transcripts when project is known")
def process(input_file, from_stdin, project, update_project, output, save_project_summary):
    """Process a transcript and extract a structured session summary."""

    # Read transcript
    if from_stdin:
        click.echo("Paste transcript (end with Ctrl+D on empty line):")
        transcript = sys.stdin.read().strip()
    elif input_file:
        transcript = Path(input_file).read_text().strip()
    else:
        raise click.UsageError("Provide --file or --stdin")

    if not transcript:
        raise click.UsageError("Transcript is empty")

    click.echo(f"\nProcessing transcript ({len(transcript)} characters)...")
    summary = extract_session_summary(transcript, project_hint=project)

    click.echo(format_session_for_display(summary))

    if output:
        Path(output).write_text(json.dumps(summary, indent=2))
        click.echo(f"Full output saved to {output}")

    target_project = project or summary.get("primary_project")
    if save_project_summary and target_project and (PROJECTS_DIR / target_project).exists():
        saved = save_project_transcript_summary(target_project, summary)
        click.echo(f"Project transcript summary saved to {saved}")

    # Update project files
    if update_project:
        if not target_project:
            click.echo("\nCould not determine project. Re-run with --project <name>")
            return

        project_dir = PROJECTS_DIR / target_project
        if not project_dir.exists():
            click.echo(f"\nProject folder not found: {project_dir}")
            available = list_projects()
            if available:
                click.echo(f"Available projects: {', '.join(available)}")
            return

        click.echo(f"\nUpdating project files for: {target_project}")

        if summary.get("open_loops"):
            update_project_open_loops(target_project, summary["open_loops"])

        update_project_handoff(target_project, summary)

        click.echo(f"\nProject files updated for {target_project}.")
        click.echo("Commit changes when ready: git add projects/ && git commit -m '...'")


@cli.command("list-projects")
def cmd_list_projects():
    """List available project names."""
    projects = list_projects()
    if projects:
        click.echo("\nActive projects:")
        for p in sorted(projects):
            click.echo(f"  {p}")
    else:
        click.echo("No project folders found in projects/")


if __name__ == "__main__":
    cli()
