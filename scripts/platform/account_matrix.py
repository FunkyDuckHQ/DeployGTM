from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Iterable

from scripts.score import calculate_activation_priority, score_urgency
from .llm import Provider, call_json


PROJECTS_DIR = Path("projects")

SCORING_SYSTEM = """\
You are a GTM analyst scoring target accounts for a B2B sales engagement.

Your job: given an account's data and the client's ICP definitions, score the account
on ICP fit and confidence. Be honest — differentiate between accounts. A score of 60
for every account is useless. Use the full 0-100 range.

Rules:
- ICP fit is about how well this company matches the ideal customer profile criteria.
- Confidence is about how much evidence we have (signals, enrichment, domain verified).
- Rationale must be one specific sentence explaining the dominant factor in the score.
- If an account has a clear disqualifier, score it 10-25 on ICP fit and say why.
- Return valid JSON only. No explanation, no markdown outside the JSON block.
"""

SCORING_SCHEMA = """\
Return this exact JSON shape:
{
  "icp_fit_score": <integer 0-100>,
  "confidence_score": <integer 0-100>,
  "icp_tier": <integer 1, 2, or 3>,
  "rationale": "<one specific sentence explaining the dominant scoring factor>",
  "key_fit_signals": ["<observable reason this account fits or doesn't>"],
  "disqualifiers_present": ["<any hard disqualifiers, empty list if none>"]
}
"""


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _read_targets(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            {str(k).strip().lower(): (v or "").strip() for k, v in row.items()}
            for row in reader
            if (row.get("company") or row.get("domain"))
        ]


def _icp_criteria_text(icp_strategy: dict) -> str:
    icps = icp_strategy.get("strategy", {}).get("icps", [])
    if not icps:
        return "No ICP definitions loaded — use general B2B SaaS criteria."
    lines = []
    for icp in icps:
        name = icp.get("name", "ICP")
        desc = icp.get("description", "")
        fit = "; ".join(icp.get("fit_criteria", []))
        disq = "; ".join(icp.get("disqualifiers", []))
        personas = ", ".join(p.get("title", "") for p in icp.get("personas", []))
        lines.append(
            f"Segment: {name}\n"
            f"  Description: {desc}\n"
            f"  Fit criteria: {fit}\n"
            f"  Personas: {personas}\n"
            f"  Disqualifiers: {disq}"
        )
    return "\n\n".join(lines)


def _score_account_with_llm(
    row: dict,
    icp_strategy: dict,
    intake: dict,
) -> tuple[int, int, list[str], list[str]]:
    """
    Call LLM to score a single account.
    Returns (icp_fit_score, confidence_score, rationale_list, disqualifiers).
    Falls back to keyword heuristic on error.
    """
    company = row.get("company") or row.get("domain") or "Unknown"
    domain = row.get("domain", "")
    notes = row.get("notes") or row.get("signal_summary") or ""
    industry = row.get("industry") or row.get("segment") or ""
    employees = row.get("employees") or ""
    stage = row.get("funding_stage") or row.get("signal_type") or ""

    icp_text = _icp_criteria_text(icp_strategy)
    offer = intake.get("offer") or "the client's offer"
    outcome = intake.get("target_outcome") or "the target outcome"

    prompt = f"""\
CLIENT OFFER: {offer}
CLIENT OUTCOME: {outcome}

ICP DEFINITIONS:
{icp_text}

ACCOUNT TO SCORE:
Company: {company}
Domain:  {domain}
Industry/Segment: {industry}
Employees: {employees}
Stage: {stage}
Notes/Signals: {notes}

Score this account against the ICP definitions above.
{SCORING_SCHEMA}"""

    fallback_score = _heuristic_fit(row, icp_strategy)
    result = call_json(
        prompt=prompt,
        system=SCORING_SYSTEM,
        task="account_scoring",
        provider=Provider.OPENAI,  # GPT-4o default; falls back to Claude if no key
        fallback={
            "icp_fit_score": fallback_score,
            "confidence_score": 45,
            "icp_tier": 2,
            "rationale": "Heuristic score — LLM unavailable.",
            "key_fit_signals": [],
            "disqualifiers_present": [],
        },
        max_tokens=512,
        temperature=0.1,  # Low temp for consistent scoring
    )

    fit = max(1, min(100, int(result.get("icp_fit_score", fallback_score))))
    conf = max(1, min(100, int(result.get("confidence_score", 45))))
    rationale = [result.get("rationale", "LLM score")]
    rationale.extend(result.get("key_fit_signals", []))
    disqualifiers = result.get("disqualifiers_present", [])

    return fit, conf, rationale, disqualifiers


def _heuristic_fit(row: dict, icp_strategy: dict) -> int:
    """Fallback keyword scoring used when LLM is skipped or fails."""
    score = 45
    summary = " ".join([
        row.get("signal_summary", ""),
        row.get("company", ""),
        row.get("signal_type", ""),
        row.get("notes", ""),
        row.get("industry", ""),
    ]).lower()

    for word in ("hiring", "funding", "launch", "growth", "sales", "crm", "pipeline", "manual"):
        if word in summary:
            score += 6

    if row.get("domain"):
        score += 10

    icps = icp_strategy.get("strategy", {}).get("icps", [])
    if icps:
        score += 5

    return max(1, min(100, score))


def _confidence_from_row(row: dict) -> tuple[int, str]:
    if row.get("signal_source", "").lower() == "birddog":
        return 80, "BirdDog signal source"
    if row.get("signal_summary") and row.get("signal_date"):
        return 65, "signal summary and date present"
    if row.get("domain"):
        return 45, "domain present but signal evidence incomplete"
    return 25, "incomplete target record"


def _account_record(row: dict, icp_strategy: dict, intake: dict) -> dict:
    signal_type = row.get("signal_type") or "manual"
    signal_date = row.get("signal_date") or None
    birddog_score = row.get("birddog_score")

    urgency, decay = score_urgency(
        signal_type,
        signal_date,
        birddog_score=int(birddog_score) if str(birddog_score).isdigit() else None,
    )

    # LLM scoring replaces the old keyword heuristic for ICP fit and confidence
    fit, confidence, rationale, disqualifiers = _score_account_with_llm(
        row, icp_strategy, intake
    )

    engagement = int(row.get("engagement_score") or 0)
    activation = calculate_activation_priority(
        icp_fit_score=fit,
        urgency_score=urgency,
        engagement_score=engagement,
        confidence_score=confidence,
    )

    record = {
        "company": row.get("company") or row.get("domain") or "Unknown",
        "domain": row.get("domain", ""),
        "signals": [
            {
                "type": signal_type,
                "date": signal_date,
                "source": row.get("signal_source") or "manual",
                "summary": row.get("signal_summary") or "",
                "birddog_score": birddog_score or None,
            }
        ],
        "scores": {
            "icp_fit_score": fit,
            "urgency_score": urgency,
            "engagement_score": engagement,
            "confidence_score": confidence,
            "activation_priority": activation,
            "decay": decay,
            "rationale": rationale,
        },
        "buyer_profiles": [],
        "contacts": [],
        "copy": {
            "status": "draft_required",
            "sequence_mode": "draft_only",
            "first_touch": "",
            "followups": [],
        },
        "crm": {
            "scope": "deploygtm_found_leads_tasks_only",
            "planned_action": "review_before_push",
        },
    }

    if disqualifiers:
        record["scores"]["disqualifiers"] = disqualifiers

    return record


def build_account_matrix(
    client_slug: str,
    projects_dir: Path = PROJECTS_DIR,
    rows: Iterable[dict] | None = None,
) -> Path:
    project_dir = projects_dir / client_slug
    platform_dir = project_dir / "platform"
    platform_dir.mkdir(parents=True, exist_ok=True)

    intake = _load_json(platform_dir / "intake.json")
    icp_strategy = _load_json(platform_dir / "icp_strategy.json")
    target_rows = list(rows) if rows is not None else _read_targets(project_dir / "targets.csv")

    accounts = [_account_record(row, icp_strategy, intake) for row in target_rows]

    matrix = {
        "schema_version": "v1.0",
        "client_slug": client_slug,
        "generated_on": date.today().isoformat(),
        "llm_provider": "openai_with_claude_fallback",
        "client": {
            "client_name": intake.get("client_name", client_slug),
            "domain": intake.get("domain", ""),
            "target_outcome": intake.get("target_outcome", ""),
            "crm_provider": intake.get("crm_provider", "hubspot"),
        },
        "scoring": {
            "model": "llm_icp_fit + urgency_decay + engagement + llm_confidence",
            "activation_priority_formula": "45% ICP fit + 35% urgency + 10% engagement + 10% confidence",
            "managed_sending": "deferred",
        },
        "accounts": accounts,
    }

    out_path = platform_dir / "accounts.json"
    out_path.write_text(json.dumps(matrix, indent=2))
    return out_path


def sample_target_rows() -> list[dict]:
    return [
        {
            "company": "Acme Analytics",
            "domain": "acmeanalytics.example",
            "signal_type": "hiring",
            "signal_date": date.today().isoformat(),
            "signal_source": "manual",
            "signal_summary": "Hiring first sales leader after new product launch",
            "birddog_score": "78",
        },
        {
            "company": "Northstar Ops",
            "domain": "northstarops.example",
            "signal_type": "funding",
            "signal_date": date.today().isoformat(),
            "signal_source": "manual",
            "signal_summary": "Recent funding and public growth goals",
            "birddog_score": "82",
        },
    ]
