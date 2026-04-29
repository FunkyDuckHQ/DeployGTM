from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

import click


PROJECTS_DIR = Path("projects")
BRAIN_DIR = Path("brain")


@dataclass
class Evidence:
    source_type: str
    source_ref: str
    evidence_snippet: str


@dataclass
class Principle:
    principle_text: str
    confidence: str
    source_trace: list[Evidence]


def _read_if_exists(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def _extract_bullets(text: str, max_items: int = 6) -> list[str]:
    bullets = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("- ") or s.startswith("* "):
            candidate = s[2:].strip()
            if candidate:
                bullets.append(candidate)
    return bullets[:max_items]


def _extract_first_sentence(text: str, fallback: str) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip())
    if not cleaned:
        return fallback
    match = re.split(r"(?<=[.!?])\s+", cleaned, maxsplit=1)
    return match[0][:280]


def _chunk_md_evidence(path: Path, source_type: str, max_items: int = 3) -> list[Evidence]:
    text = _read_if_exists(path)
    if not text:
        return []

    bullets = _extract_bullets(text, max_items=max_items)
    if bullets:
        return [Evidence(source_type=source_type, source_ref=str(path), evidence_snippet=b) for b in bullets]

    return [
        Evidence(
            source_type=source_type,
            source_ref=str(path),
            evidence_snippet=_extract_first_sentence(text, fallback="No extractable summary."),
        )
    ]


def _load_transcript_summaries(client_slug: str, limit: int = 3) -> list[Evidence]:
    transcript_dir = PROJECTS_DIR / client_slug / "transcripts"
    if not transcript_dir.exists():
        return []

    summaries: list[Evidence] = []
    for p in sorted(transcript_dir.glob("*.json"), reverse=True)[:limit]:
        try:
            obj = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue

        summary = obj.get("one_line_summary") or ""
        matters = obj.get("what_matters") or []
        if summary:
            summaries.append(Evidence("transcript_summary", str(p), summary))
        for item in matters[:2]:
            summaries.append(Evidence("transcript_summary", str(p), str(item)))
    return summaries


def _load_intake_evidence(client_slug: str) -> list[Evidence]:
    intake_path = PROJECTS_DIR / client_slug / "platform" / "intake.json"
    if not intake_path.exists():
        return []

    try:
        intake = json.loads(intake_path.read_text())
    except json.JSONDecodeError:
        return []

    evidence = []
    if intake.get("target_outcome"):
        evidence.append(Evidence("customer_outcome_intake", str(intake_path), str(intake["target_outcome"])))
    if intake.get("offer"):
        evidence.append(Evidence("customer_outcome_intake", str(intake_path), str(intake["offer"])))
    for item in intake.get("constraints", [])[:2]:
        evidence.append(Evidence("customer_outcome_intake", str(intake_path), str(item)))
    return evidence


def build_context_pack(client_slug: str) -> dict:
    client_dir = PROJECTS_DIR / client_slug

    intake_context = _load_intake_evidence(client_slug)
    client_context = _chunk_md_evidence(client_dir / "context.md", "client_context")
    client_handoff = _chunk_md_evidence(client_dir / "handoff.md", "client_context")
    client_loops = _chunk_md_evidence(client_dir / "open-loops.md", "client_context")
    transcript_context = _load_transcript_summaries(client_slug)

    priors_icp = _chunk_md_evidence(BRAIN_DIR / "icp.md", "master_brain")
    priors_personas = _chunk_md_evidence(BRAIN_DIR / "personas.md", "master_brain")
    priors_messaging = _chunk_md_evidence(BRAIN_DIR / "messaging.md", "master_brain")

    principles: list[Principle] = []

    if intake_context:
        principles.append(
            Principle(
                principle_text="Start every Signal Audit from the customer's stated outcome, offer, constraints, and CRM scope.",
                confidence="high",
                source_trace=intake_context[:3],
            )
        )

    if client_context:
        principles.append(
            Principle(
                principle_text="Anchor ICP strategy to explicit project objective and current state before scoring accounts.",
                confidence="high",
                source_trace=client_context[:2] + client_handoff[:1],
            )
        )

    if client_loops:
        principles.append(
            Principle(
                principle_text="Treat unresolved blockers in open loops as first-class constraints in strategy and execution order.",
                confidence="high",
                source_trace=client_loops[:2],
            )
        )

    if transcript_context:
        principles.append(
            Principle(
                principle_text="Promote repeated transcript insights into structured strategy inputs; avoid relying on chat memory.",
                confidence="medium",
                source_trace=transcript_context[:3],
            )
        )

    if priors_icp or priors_personas:
        principles.append(
            Principle(
                principle_text="Blend client specifics with DeployGTM's baseline ICP and persona priors for initial targeting assumptions.",
                confidence="medium",
                source_trace=(priors_icp[:2] + priors_personas[:2]),
            )
        )

    if priors_messaging:
        principles.append(
            Principle(
                principle_text="Keep strategy signal-first and concrete so downstream messaging remains grounded in observable triggers.",
                confidence="medium",
                source_trace=priors_messaging[:2],
            )
        )

    return {
        "client_slug": client_slug,
        "principles": [
            {
                "principle_text": p.principle_text,
                "confidence": p.confidence,
                "source_trace": [asdict(e) for e in p.source_trace],
            }
            for p in principles
        ],
        "sources_scanned": {
            "client_files": [
                str(client_dir / "platform" / "intake.json"),
                str(client_dir / "context.md"),
                str(client_dir / "handoff.md"),
                str(client_dir / "open-loops.md"),
            ],
            "brain_files": [
                str(BRAIN_DIR / "icp.md"),
                str(BRAIN_DIR / "personas.md"),
                str(BRAIN_DIR / "messaging.md"),
            ],
            "transcript_dir": str(client_dir / "transcripts"),
        },
    }


@click.group()
def cli() -> None:
    """Build context packs for phase-2 strategy generation."""


@cli.command("build")
@click.option("--client", "client_slug", required=True, help="Client/project slug under projects/")
@click.option("--output", "output_path", default=None, help="Optional output file path")
def build_cmd(client_slug: str, output_path: str | None) -> None:
    pack = build_context_pack(client_slug)

    out = Path(output_path) if output_path else PROJECTS_DIR / client_slug / "platform" / "context_pack.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pack, indent=2))

    click.echo(f"Saved context pack: {out}")
    click.echo(f"Principles: {len(pack['principles'])}")


if __name__ == "__main__":
    cli()
