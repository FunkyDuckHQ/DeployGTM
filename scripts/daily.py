"""
DeployGTM — Daily Briefing

Morning operations command. Run this first thing to know exactly where you are.
No API calls — reads local files only, so it's instant.

Shows:
  - Follow-ups due today across all output/ accounts
  - Active projects with open actions
  - Recent pipeline output summary (last 7 days)
  - Quick links to the next actions

Usage:
  python scripts/daily.py
  make daily
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import click


# ─── Helpers ──────────────────────────────────────────────────────────────────


def days_since(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        return (date.today() - date.fromisoformat(date_str)).days
    except ValueError:
        return None


TOUCH_DAYS = {1: 3, 2: 7, 3: 14}


def next_touch_due(entry: dict) -> Optional[tuple[int, int]]:
    if entry.get("status") != "active":
        return None
    base = entry.get("outreach_sent")
    if not base:
        return None
    for touch in [1, 2, 3]:
        if entry.get(f"followup_{touch}_sent"):
            continue
        elapsed = days_since(base)
        if elapsed is None:
            return None
        overdue = elapsed - TOUCH_DAYS[touch]
        if overdue >= 0:
            return (touch, overdue)
        break
    return None


def load_output_files(output_dir: Path) -> list[dict]:
    """Load output JSON files from output/ and output/[client]/ subdirectories."""
    results = []
    # Top-level files (own pipeline)
    top_level = sorted(output_dir.glob("*.json"))
    # Client subdirectory files (signal_audit.py writes here)
    client_files = sorted(output_dir.glob("*/*.json"))
    for fpath in top_level + client_files:
        try:
            data = json.loads(fpath.read_text())
            # Use relative path so follow-up commands work correctly
            rel = fpath.relative_to(output_dir)
            data["_file"] = str(rel)
            data["_client"] = fpath.parent.name if fpath.parent != output_dir else None
            results.append(data)
        except Exception:
            continue
    return results


def get_project_dirs(projects_dir: Path) -> list[Path]:
    skip = {"client-template"}
    return sorted(
        [d for d in projects_dir.iterdir()
         if d.is_dir() and d.name not in skip],
        key=lambda d: d.name,
    )


def read_open_loops(proj_dir: Path) -> list[str]:
    loops_file = proj_dir / "open-loops.md"
    if not loops_file.exists():
        return []
    text = loops_file.read_text()
    lines = []
    in_need_to_build = False
    for line in text.splitlines():
        if line.startswith("## Need to build"):
            in_need_to_build = True
            continue
        if line.startswith("## ") and in_need_to_build:
            break
        if in_need_to_build and line.startswith("- ") and "~~" not in line:
            item = line.lstrip("- ").strip()
            if item and item != "":
                lines.append(item)
    return lines


def section(title: str) -> None:
    click.echo(f"\n{'─'*65}")
    click.echo(f"  {title}")
    click.echo(f"{'─'*65}")


# ─── CLI ──────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--output-dir", default="output", show_default=True)
@click.option("--projects-dir", default="projects", show_default=True)
@click.option("--days", default=7, show_default=True,
              help="Show pipeline output from the last N days.")
def briefing(output_dir: str, projects_dir: str, days: int):
    """Morning briefing — know where you are in 10 seconds."""
    today = date.today()

    click.echo(f"\n{'='*65}")
    click.echo(f"  DeployGTM Daily Briefing — {today.isoformat()}")
    click.echo(f"{'='*65}")

    # ── 1. Follow-ups due ─────────────────────────────────────────────────────
    section("Follow-Ups Due")

    output_files = load_output_files(Path(output_dir))
    followup_rows = []

    for data in output_files:
        log = data.get("follow_up_log", {})
        meta_date = data.get("meta", {}).get("run_date")
        company = data.get("company", data["_file"])

        for email, outreach in data.get("outreach", {}).items():
            entry = log.get(email, {})
            if not entry:
                if meta_date and days_since(meta_date) is not None and days_since(meta_date) >= 3:
                    entry = {
                        "outreach_sent": meta_date,
                        "status": "active",
                        "followup_1_sent": None,
                        "followup_2_sent": None,
                        "followup_3_sent": None,
                    }
                else:
                    continue

            result = next_touch_due(entry)
            if result:
                touch, overdue = result
                contact = next(
                    (c for c in data.get("contacts", []) if c.get("email") == email),
                    {},
                )
                followup_rows.append({
                    "company": company,
                    "name": contact.get("name", email),
                    "touch": touch,
                    "overdue": overdue,
                    "file": data["_file"],
                    "status": entry.get("status", "active"),
                })

    if followup_rows:
        followup_rows.sort(key=lambda r: (-r["overdue"], r["company"]))
        for r in followup_rows:
            overdue_str = f"+{r['overdue']}d overdue" if r["overdue"] > 0 else "due today"
            click.echo(f"  → {r['company']} / {r['name']} — Touch #{r['touch']} ({overdue_str})")
            click.echo(f"    make followup-generate FILE=output/{r['file']} EMAIL=<email> TOUCH={r['touch']}")
    else:
        click.echo("  No follow-ups due. Check back tomorrow.")

    # ── 2. Recent pipeline output ─────────────────────────────────────────────
    section(f"Pipeline Activity (last {days} days)")

    cutoff = today - timedelta(days=days)
    recent = [
        d for d in output_files
        if d.get("meta", {}).get("run_date", "") >= cutoff.isoformat()
    ]

    if recent:
        by_action: dict[str, list[str]] = {}
        for d in recent:
            action = d.get("score", {}).get("action", "unknown")
            company = d.get("company", d["_file"])
            by_action.setdefault(action, []).append(company)

        for action, companies in sorted(by_action.items()):
            click.echo(f"  [{action}]  " + ", ".join(companies))

        replied = [
            d.get("company", d["_file"])
            for d in recent
            for entry in d.get("follow_up_log", {}).values()
            if entry.get("status") == "replied"
        ]
        if replied:
            click.echo(f"\n  Replied: " + ", ".join(set(replied)))

        booked = [
            d.get("company", d["_file"])
            for d in recent
            for entry in d.get("follow_up_log", {}).values()
            if entry.get("status") == "booked"
        ]
        if booked:
            click.echo(f"  Booked:  " + ", ".join(set(booked)))
    else:
        click.echo(f"  No pipeline output from the last {days} days.")
        click.echo(f"  Run: make batch  or  python scripts/pipeline.py run ...")

    # ── 3. Active projects ─────────────────────────────────────────────────────
    section("Active Projects — Open Actions")

    proj_dir = Path(projects_dir)
    if proj_dir.exists():
        project_dirs = get_project_dirs(proj_dir)
        any_loops = False
        for pd in project_dirs:
            context_file = pd / "context.md"
            if not context_file.exists():
                continue
            context_text = context_file.read_text()
            if "active" not in context_text.lower() and "status" not in context_text.lower():
                continue

            loops = read_open_loops(pd)
            if loops:
                any_loops = True
                click.echo(f"\n  {pd.name.upper()}")
                for loop in loops[:3]:
                    click.echo(f"  → {loop}")
                if len(loops) > 3:
                    click.echo(f"    (+{len(loops) - 3} more — see projects/{pd.name}/open-loops.md)")

        if not any_loops:
            click.echo("  All project open loops are clear.")

    # ── 4. Pending rep alerts ──────────────────────────────────────────────────
    alerts_dir = Path("output/alerts")
    if alerts_dir.exists():
        alert_files = sorted(alerts_dir.glob("*.md"))
        if alert_files:
            section("Pending Rep Alerts — Ready to Send")
            for af in alert_files:
                # Peek at priority line
                try:
                    text = af.read_text()
                    priority_line = next(
                        (l for l in text.splitlines() if "**Priority:**" in l), ""
                    )
                    priority = priority_line.split("**Priority:**")[-1].split("/")[0].strip() if priority_line else "?"
                    action_line = next(
                        (l for l in text.splitlines() if "**Action:**" in l), ""
                    )
                    action = action_line.split("**Action:**")[-1].strip().rstrip("  ") if action_line else ""
                    company = af.stem.replace("_", ".")
                    click.echo(f"  → {company}  [Priority {priority}/15  {action}]")
                    click.echo(f"    cat {af}")
                except Exception:
                    click.echo(f"  → {af.stem}")

    # ── 5. Quick commands ──────────────────────────────────────────────────────
    section("Quick Commands")
    click.echo("  make intake COMPANY=\"Acme\" DOMAIN=acme.ai  — start with a new prospect")
    click.echo("  make followup-due          — full follow-up queue")
    click.echo("  make signals               — find new accounts (Apollo + YC)")
    click.echo("  make batch                 — run pipeline on signals_intake.csv")
    click.echo("  make batch-resume          — resume interrupted batch")
    click.echo("  make report                — weekly signal report")
    click.echo("  make push-hubspot          — push priority accounts to HubSpot")
    click.echo("  make birddog-pull          — pull signals from BirdDog")

    click.echo(f"\n{'='*65}\n")


if __name__ == "__main__":
    briefing()
