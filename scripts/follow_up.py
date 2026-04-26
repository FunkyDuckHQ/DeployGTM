"""
DeployGTM — Follow-Up Cadence Manager

Tracks outreach sent dates and identifies contacts due for follow-up touches.
Generates follow-up messages using Claude and can create HubSpot tasks.

Cadence (from brain/messaging.md):
  Touch 1 (day 3):  Add one new piece of value — signal, example, question
  Touch 2 (day 7):  One sentence. "Still relevant?" or forward with one-liner
  Touch 3 (day 14): Closing the loop. "Happy to park this if timing is off."

After 3 touches with no response: pause, tag in HubSpot, wait for next signal.

Usage:
  python scripts/follow_up.py due
  python scripts/follow_up.py generate --file output/acme_com.json --email ceo@acme.com --touch 1
  python scripts/follow_up.py log --file output/acme_com.json --email ceo@acme.com --touch 1
  python scripts/follow_up.py status --file output/acme_com.json
  python scripts/follow_up.py create-tasks
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import anthropic
import click
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"

TOUCH_DAYS = {1: 3, 2: 7, 3: 14}

TOUCH_GUIDANCE = {
    1: "Day-3 follow-up. Add one new piece of value: a relevant signal about them, a brief relevant example, or a sharp question. Reference the original message. Still under 80 words.",
    2: "Day-7 follow-up. One or two sentences only. 'Still relevant?' or forward the original email with a one-liner on top. Strip everything that's not essential.",
    3: "Day-14 breakup email. Closing the loop. 'Happy to park this if timing is off.' Give them an easy out. Under 50 words.",
}


# ─── Data helpers ─────────────────────────────────────────────────────────────


def load_output_file(path: Path) -> dict:
    return json.loads(path.read_text())


def save_output_file(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2))


def load_brain(brain_path: str = "brain") -> str:
    brain_dir = Path(brain_path)
    files = ["messaging.md", "personas.md", "icp.md"]
    sections = []
    for fname in files:
        fpath = brain_dir / fname
        if fpath.exists():
            sections.append(f"## {fname}\n\n{fpath.read_text().strip()}")
    return "\n\n---\n\n".join(sections)


def get_follow_up_log(data: dict) -> dict:
    """Return follow_up_log from output file, initializing if missing."""
    if "follow_up_log" not in data:
        data["follow_up_log"] = {}
    return data["follow_up_log"]


def init_contact_log(log: dict, email: str, sent_date: Optional[str] = None) -> dict:
    if email not in log:
        log[email] = {
            "outreach_sent": sent_date or date.today().isoformat(),
            "followup_1_sent": None,
            "followup_2_sent": None,
            "followup_3_sent": None,
            "status": "active",
            "notes": "",
        }
    return log[email]


def days_since(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        d = date.fromisoformat(date_str)
        return (date.today() - d).days
    except ValueError:
        return None


def next_touch_due(entry: dict) -> Optional[tuple[int, int]]:
    """
    Return (touch_number, days_overdue) for the next pending follow-up.
    Returns None if all touches are done or status is not active.
    """
    if entry.get("status") != "active":
        return None

    base = entry.get("outreach_sent")
    if not base:
        return None

    for touch in [1, 2, 3]:
        sent_key = f"followup_{touch}_sent"
        if entry.get(sent_key):
            continue
        threshold = TOUCH_DAYS[touch]
        elapsed = days_since(base)
        if elapsed is None:
            return None
        overdue = elapsed - threshold
        if overdue >= 0:
            return (touch, overdue)
        break  # not due yet for any remaining touch

    return None


# ─── Claude generation ────────────────────────────────────────────────────────


def generate_follow_up_message(
    data: dict,
    email: str,
    touch: int,
    brain_context: str,
    api_key: Optional[str] = None,
) -> dict:
    """Generate a follow-up message for a specific contact and touch number."""
    client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    original_outreach = data.get("outreach", {}).get(email, {})
    original_primary = original_outreach.get("primary", {})
    original_subject = original_primary.get("subject", "")
    original_body = original_primary.get("body", "")
    persona = original_outreach.get("persona", "founder_seller")

    research = data.get("research", {})
    company = data.get("company", "")
    signal = data.get("signal", {})

    contact = next(
        (c for c in data.get("contacts", []) if c.get("email") == email),
        {},
    )
    contact_name = contact.get("name", "")
    contact_title = contact.get("title", "")

    system_prompt = f"""You are the DeployGTM follow-up writer.

{brain_context}

Rules:
- Follow the messaging brain rules exactly
- No AI language, no "I hope this finds you well", no filler
- Lead with signal or value, not pleasantries
- Match the persona and tone of the original message
- The follow-up must be clearly shorter than the original
"""

    user_prompt = f"""Write follow-up #{touch} for this prospect.

GUIDANCE: {TOUCH_GUIDANCE[touch]}

PROSPECT:
- Company: {company}
- Contact: {contact_name} ({contact_title})
- Persona: {persona}
- Signal: {signal.get('type', '')} on {signal.get('date', '')}
- Pain hypothesis: {research.get('pain_hypothesis', '')}
- ICP verdict: {research.get('icp_verdict', '')}

ORIGINAL MESSAGE SENT:
Subject: {original_subject}
Body: {original_body}

Return JSON only, no other text:
{{
  "subject": "Re: [original subject] or new subject if appropriate",
  "body": "the follow-up message body",
  "notes": "brief note on the angle used"
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=600,
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


# ─── CLI ──────────────────────────────────────────────────────────────────────


@click.group()
def cli():
    """DeployGTM Follow-Up Cadence Manager."""
    pass


@cli.command()
@click.option("--output-dir", default="output", show_default=True,
              help="Directory to scan for pipeline output files.")
@click.option("--config", "config_path", default="config.yaml", show_default=True)
def due(output_dir: str, config_path: str):
    """List all contacts with follow-up touches due today."""
    out_dir = Path(output_dir)
    files = sorted(out_dir.glob("*.json"))

    if not files:
        click.echo("No output files found.")
        return

    rows = []

    for fpath in files:
        try:
            data = load_output_file(fpath)
        except Exception:
            continue

        log = data.get("follow_up_log", {})
        meta_date = data.get("meta", {}).get("run_date")

        for email, contacts in data.get("outreach", {}).items():
            entry = log.get(email)
            if not entry:
                # Outreach generated but never logged as sent — init with pipeline run date
                entry = init_contact_log({}, email, meta_date)
                entry_exists = False
            else:
                entry_exists = True

            result = next_touch_due(entry)
            if result:
                touch, overdue = result
                contact = next(
                    (c for c in data.get("contacts", []) if c.get("email") == email),
                    {},
                )
                rows.append({
                    "file": fpath.name,
                    "company": data.get("company", ""),
                    "name": contact.get("name", email),
                    "title": contact.get("title", ""),
                    "email": email,
                    "touch": touch,
                    "overdue": overdue,
                    "status": entry.get("status", "active"),
                    "outreach_sent": entry.get("outreach_sent", meta_date),
                })

    if not rows:
        click.echo("No follow-ups due. Check back later.")
        return

    rows.sort(key=lambda r: (-r["overdue"], r["company"]))

    click.echo(f"\n{'='*70}")
    click.echo(f"  Follow-Ups Due  ({date.today().isoformat()})")
    click.echo(f"{'='*70}")
    click.echo(f"  {'Company':<20} {'Contact':<20} {'Touch':<8} {'Overdue':<10} File")
    click.echo(f"  {'-'*20} {'-'*20} {'-'*8} {'-'*10} {'-'*25}")

    for r in rows:
        overdue_str = f"+{r['overdue']}d" if r["overdue"] > 0 else "today"
        click.echo(
            f"  {r['company']:<20} {r['name']:<20} "
            f"#{r['touch']:<7} {overdue_str:<10} {r['file']}"
        )

    click.echo(f"\n  {len(rows)} follow-up(s) due.")
    click.echo(
        f"\n  Generate: python scripts/follow_up.py generate "
        f"--file output/<file> --email <email> --touch <N>"
    )


@cli.command()
@click.option("--file", "file_path", required=True, type=click.Path(exists=True),
              help="Pipeline output JSON file.")
@click.option("--email", required=True, help="Contact email address.")
@click.option("--touch", required=True, type=click.Choice(["1", "2", "3"]),
              help="Follow-up touch number (1, 2, or 3).")
@click.option("--brain", "brain_path", default="brain", show_default=True)
@click.option("--save", is_flag=True, default=False,
              help="Save generated follow-up back to the output file.")
def generate(file_path: str, email: str, touch: str, brain_path: str, save: bool):
    """Generate a follow-up message for a contact."""
    touch_num = int(touch)
    fpath = Path(file_path)
    data = load_output_file(fpath)

    if email not in data.get("outreach", {}):
        click.echo(f"Error: No outreach found for {email} in {file_path}.", err=True)
        click.echo("Available emails: " + ", ".join(data.get("outreach", {}).keys()))
        raise SystemExit(1)

    click.echo(f"\nGenerating follow-up #{touch_num} for {email}...")
    brain_context = load_brain(brain_path)

    msg = generate_follow_up_message(
        data=data,
        email=email,
        touch=touch_num,
        brain_context=brain_context,
    )

    click.echo(f"\n{'─'*60}")
    click.echo(f"  Follow-Up #{touch_num}  ({TOUCH_DAYS[touch_num]}-day touch)")
    click.echo(f"  To: {email}")
    click.echo(f"{'─'*60}")
    click.echo(f"\nSubject: {msg.get('subject', '')}")
    click.echo(f"\n{msg.get('body', '')}")
    if msg.get("notes"):
        click.echo(f"\n[Note: {msg['notes']}]")

    if save:
        followups = data.setdefault("generated_followups", {})
        contact_followups = followups.setdefault(email, {})
        contact_followups[f"followup_{touch_num}"] = msg
        save_output_file(fpath, data)
        click.echo(f"\n  Saved to {file_path}")
    else:
        click.echo(f"\n  (Use --save to write this to the output file)")


@cli.command()
@click.option("--file", "file_path", required=True, type=click.Path(exists=True),
              help="Pipeline output JSON file.")
@click.option("--email", required=True, help="Contact email address.")
@click.option("--touch", required=True, type=click.Choice(["0", "1", "2", "3"]),
              help="Touch number. 0 = initial outreach, 1-3 = follow-ups.")
@click.option("--date", "sent_date", default=None,
              help="Date sent (YYYY-MM-DD). Defaults to today.")
@click.option("--status", default=None,
              type=click.Choice(["active", "replied", "booked", "closed", "paused"]),
              help="Update contact status.")
@click.option("--notes", default=None, help="Optional notes to append.")
def log(file_path: str, email: str, touch: str, sent_date: Optional[str],
        status: Optional[str], notes: Optional[str]):
    """Log a follow-up as sent (updates the output file)."""
    touch_num = int(touch)
    actual_date = sent_date or date.today().isoformat()
    fpath = Path(file_path)
    data = load_output_file(fpath)

    follow_up_log = get_follow_up_log(data)
    entry = init_contact_log(follow_up_log, email, data.get("meta", {}).get("run_date"))

    if touch_num == 0:
        entry["outreach_sent"] = actual_date
        click.echo(f"  Logged: initial outreach sent to {email} on {actual_date}")
    else:
        key = f"followup_{touch_num}_sent"
        entry[key] = actual_date
        click.echo(f"  Logged: follow-up #{touch_num} sent to {email} on {actual_date}")

    if status:
        entry["status"] = status
        click.echo(f"  Status updated: {status}")

    if notes:
        existing = entry.get("notes", "")
        entry["notes"] = f"{existing}\n{actual_date}: {notes}".strip()

    save_output_file(fpath, data)
    click.echo(f"  Saved to {file_path}")


@cli.command()
@click.option("--file", "file_path", required=True, type=click.Path(exists=True),
              help="Pipeline output JSON file.")
def status(file_path: str):
    """Show follow-up status for all contacts in an output file."""
    fpath = Path(file_path)
    data = load_output_file(fpath)

    company = data.get("company", fpath.stem)
    signal = data.get("signal", {})
    log = data.get("follow_up_log", {})
    meta_date = data.get("meta", {}).get("run_date", "unknown")

    click.echo(f"\n{'='*60}")
    click.echo(f"  {company} — Follow-Up Status")
    click.echo(f"  Signal: {signal.get('type', '?')} / Pipeline run: {meta_date}")
    click.echo(f"{'='*60}")

    outreach_emails = list(data.get("outreach", {}).keys())
    if not outreach_emails:
        click.echo("  No outreach generated for this account.")
        return

    for email in outreach_emails:
        contact = next(
            (c for c in data.get("contacts", []) if c.get("email") == email),
            {},
        )
        name = contact.get("name", email)
        title = contact.get("title", "")
        entry = log.get(email, {})

        click.echo(f"\n  {name} ({title})")
        click.echo(f"  {email}")

        if not entry:
            click.echo("  Status:  not tracked (use 'log --touch 0' to mark outreach sent)")
            continue

        click.echo(f"  Status:  {entry.get('status', 'active')}")
        click.echo(f"  Sent:    {entry.get('outreach_sent', '—')}")

        for t in [1, 2, 3]:
            key = f"followup_{t}_sent"
            sent = entry.get(key)
            if sent:
                click.echo(f"  Touch {t}: sent {sent}")
            else:
                base = entry.get("outreach_sent")
                if base:
                    threshold = TOUCH_DAYS[t]
                    elapsed = days_since(base)
                    if elapsed is not None:
                        remaining = threshold - elapsed
                        if remaining <= 0:
                            click.echo(f"  Touch {t}: DUE ({abs(remaining)}d overdue)")
                        else:
                            click.echo(f"  Touch {t}: in {remaining}d")
                    else:
                        click.echo(f"  Touch {t}: pending")
                else:
                    click.echo(f"  Touch {t}: pending (no sent date logged)")

        if entry.get("notes"):
            click.echo(f"  Notes:   {entry['notes']}")


@cli.command("create-tasks")
@click.option("--output-dir", default="output", show_default=True)
@click.option("--with-copy/--no-copy", default=True, show_default=True,
              help="Generate pre-written email copy and embed it in each task body.")
@click.option("--brain", "brain_path", default="brain", show_default=True)
@click.option("--dry-run", is_flag=True, default=False)
def create_tasks(output_dir: str, with_copy: bool, brain_path: str, dry_run: bool):
    """Create HubSpot tasks for all contacts with follow-ups due.

    By default generates the pre-written follow-up copy via Claude and embeds
    it in the task body so reps can review and send without leaving HubSpot.
    Use --no-copy for lightweight tasks without generated copy.
    """
    try:
        from hubspot import create_task as hs_create_task
    except ImportError:
        click.echo("Error: hubspot module not found.", err=True)
        raise SystemExit(1)

    brain_context = load_brain(brain_path) if with_copy else ""
    out_dir = Path(output_dir)
    files = sorted(out_dir.glob("*.json"))
    tasks_created = 0
    files_modified = []

    for fpath in files:
        try:
            data = load_output_file(fpath)
        except Exception:
            continue

        log = data.get("follow_up_log", {})
        meta_date = data.get("meta", {}).get("run_date")
        company = data.get("company", "")
        file_dirty = False

        for email in data.get("outreach", {}):
            entry = log.get(email)
            if not entry:
                entry = init_contact_log({}, email, meta_date)

            result = next_touch_due(entry)
            if not result:
                continue

            touch, overdue = result
            contact = next(
                (c for c in data.get("contacts", []) if c.get("email") == email),
                {},
            )
            name = contact.get("name", email)
            overdue_str = f" (+{overdue}d overdue)" if overdue > 0 else ""

            # Generate copy if requested
            task_body_text = ""
            msg: dict = {}
            if with_copy:
                click.echo(f"  Generating copy: {company} / {name} (touch #{touch})...")
                try:
                    msg = generate_follow_up_message(
                        data=data,
                        email=email,
                        touch=touch,
                        brain_context=brain_context,
                    )
                    task_body_text = (
                        f"Subject: {msg.get('subject', '')}\n\n"
                        f"{msg.get('body', '')}"
                    )
                    # Save copy back to output file
                    followups = data.setdefault("generated_followups", {})
                    followups.setdefault(email, {})[f"followup_{touch}"] = msg
                    file_dirty = True
                except Exception as exc:
                    click.echo(f"  WARN: copy generation failed: {exc}", err=True)
                    task_body_text = TOUCH_GUIDANCE[touch]
            else:
                task_body_text = TOUCH_GUIDANCE[touch]

            subject = f"Follow-up #{touch}: {name} ({company}){overdue_str}"

            if dry_run:
                click.echo(f"  [dry-run] Task: {subject}")
                if msg:
                    click.echo(f"    Subject: {msg.get('subject', '')}")
                    preview = (msg.get("body") or "")[:120].replace("\n", " ")
                    click.echo(f"    Body:    {preview}...")
                continue

            task_id = hs_create_task(
                subject=subject,
                body=task_body_text,
                due_date=date.today().isoformat(),
                dry_run=dry_run,
            )
            if task_id:
                click.echo(f"  ✓ Task created: {subject}")
                tasks_created += 1
            else:
                click.echo(f"  ✗ Task failed for {name} ({company})", err=True)

        if file_dirty and not dry_run:
            save_output_file(fpath, data)
            files_modified.append(fpath.name)

    if dry_run:
        click.echo("\n  Dry run complete. No tasks created.")
    else:
        click.echo(f"\n  {tasks_created} task(s) created in HubSpot.")
        if files_modified:
            click.echo(f"  Copy saved to: {', '.join(files_modified)}")


@cli.command()
@click.option("--file", "file_path", required=True, type=click.Path(exists=True),
              help="Pipeline output JSON file.")
@click.option("--email", required=True, help="Contact email address.")
@click.option("--reply-summary", required=True,
              help="Summary of what they replied. Quote the key parts.")
@click.option("--brain", "brain_path", default="brain", show_default=True)
@click.option("--save", is_flag=True, default=False,
              help="Save generated response to the output file and update status to replied.")
def respond(file_path: str, email: str, reply_summary: str, brain_path: str, save: bool):
    """Generate a suggested response to a prospect reply."""
    fpath = Path(file_path)
    data = load_output_file(fpath)

    if email not in data.get("outreach", {}):
        click.echo(f"Error: No outreach found for {email}.", err=True)
        raise SystemExit(1)

    original_outreach = data["outreach"][email]
    original_primary = original_outreach.get("primary", {})
    research = data.get("research", {})
    company = data.get("company", "")
    signal = data.get("signal", {})

    contact = next(
        (c for c in data.get("contacts", []) if c.get("email") == email),
        {},
    )
    contact_name = contact.get("name", "")
    contact_title = contact.get("title", "")
    persona = original_outreach.get("persona", "founder_seller")

    brain_context = load_brain(brain_path)
    api_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    sent_followups = []
    log_entry = data.get("follow_up_log", {}).get(email, {})
    generated = data.get("generated_followups", {}).get(email, {})
    for t in [1, 2, 3]:
        if log_entry.get(f"followup_{t}_sent"):
            fu = generated.get(f"followup_{t}", {})
            if fu.get("body"):
                sent_followups.append(f"Follow-up #{t}: {fu['body']}")

    followups_context = "\n\n".join(sent_followups) if sent_followups else "No follow-ups sent yet."

    system_prompt = f"""You are the DeployGTM response writer. A prospect has replied to outreach and you need to write the next message to advance the conversation toward a call or a close.

{brain_context}

Rules:
- The goal is to book a call or get a clear next step
- Match their energy — if they're brief, be brief; if they're engaged, be warmer
- Don't over-sell; they replied, which means there's interest — don't blow it with a wall of text
- Under 80 words unless they asked a specific question that requires a real answer
- No AI language, no filler
- If they objected, address it using the objection framework
- If they asked about pricing, answer directly: Signal Audit $3,500 / 2 weeks; Retainer $7,500/month
"""

    user_prompt = f"""A prospect replied to our outreach. Write the ideal response.

PROSPECT:
- Company: {company}
- Contact: {contact_name} ({contact_title})
- Persona: {persona}
- Pain hypothesis: {research.get('pain_hypothesis', '')}
- Signal: {signal.get('type', '')} on {signal.get('date', '')}

ORIGINAL MESSAGE WE SENT:
Subject: {original_primary.get('subject', '')}
Body: {original_primary.get('body', '')}

FOLLOW-UPS SENT:
{followups_context}

THEIR REPLY (summary):
{reply_summary}

Return JSON only:
{{
  "subject": "Re: [original subject]",
  "body": "the response body",
  "next_step": "what we want to happen after this message",
  "notes": "brief note on the angle and why"
}}"""

    response = api_client.messages.create(
        model=MODEL,
        max_tokens=600,
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

    msg = json.loads(raw)

    click.echo(f"\n{'─'*60}")
    click.echo(f"  Suggested Response to {contact_name} ({company})")
    click.echo(f"{'─'*60}")
    click.echo(f"\nSubject: {msg.get('subject', '')}")
    click.echo(f"\n{msg.get('body', '')}")
    click.echo(f"\nNext step: {msg.get('next_step', '')}")
    if msg.get("notes"):
        click.echo(f"[Note: {msg['notes']}]")

    if save:
        follow_up_log = get_follow_up_log(data)
        entry = init_contact_log(follow_up_log, email, data.get("meta", {}).get("run_date"))
        entry["status"] = "replied"
        today = date.today().isoformat()
        existing_notes = entry.get("notes", "")
        entry["notes"] = f"{existing_notes}\n{today}: replied — {reply_summary}".strip()

        replies = data.setdefault("reply_log", {})
        replies.setdefault(email, []).append({
            "date": today,
            "summary": reply_summary,
            "suggested_response": msg,
        })

        save_output_file(fpath, data)
        click.echo(f"\n  Status set to 'replied'. Saved to {file_path}")
    else:
        click.echo(f"\n  (Use --save to log the reply and update status)")


if __name__ == "__main__":
    cli()
