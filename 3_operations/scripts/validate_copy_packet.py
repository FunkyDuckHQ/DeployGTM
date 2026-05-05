#!/usr/bin/env python3
"""Validate a DeployGTM prospect copy packet.

This is intentionally not an LLM judge. It validates the contract around copy:
required shape, source trace, QA score, hard fails, and banned phrases.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_RUBRIC_PATH = Path("templates/copy-quality-rubric.json")
DEFAULT_MAX_EMAIL_WORDS = 140
REQUIRED_TOP_LEVEL_FIELDS = {
    "copy_packet_id",
    "client_id",
    "workflow_name",
    "target_company",
    "context_bundle_ref",
    "message_strategy",
    "emails",
    "qa_result",
    "source_trace",
}
REQUIRED_EMAIL_FIELDS = {"step", "send_day", "subject", "body", "cta", "claims_used", "source_refs", "qa_status"}
REQUIRED_QA_FIELDS = {"total_score", "decision", "dimension_scores", "hard_fail_flags", "review_notes"}


@dataclass
class CopyValidationResult:
    valid: bool
    copy_packet_path: str
    checked_at: str
    score: float | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def word_count(value: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", value))


def contains_phrase(value: str, phrase: str) -> bool:
    return phrase.lower() in value.lower()


def validate_dimension_scores(packet: dict[str, Any], rubric: dict[str, Any], result: CopyValidationResult) -> None:
    qa_result = packet.get("qa_result", {})
    dimension_scores = qa_result.get("dimension_scores", {})
    if not isinstance(dimension_scores, dict):
        result.errors.append("qa_result.dimension_scores must be an object")
        return

    expected = {dimension["id"]: dimension["max_points"] for dimension in rubric.get("dimensions", [])}
    missing = sorted(dimension_id for dimension_id in expected if dimension_id not in dimension_scores)
    if missing:
        result.errors.append(f"qa_result.dimension_scores missing rubric dimensions: {', '.join(missing)}")

    for dimension_id, score in dimension_scores.items():
        if not isinstance(score, (int, float)):
            result.errors.append(f"qa_result.dimension_scores.{dimension_id} must be numeric")
            continue
        max_points = expected.get(dimension_id)
        if max_points is not None and score > max_points:
            result.errors.append(f"qa_result.dimension_scores.{dimension_id} exceeds max points {max_points}")
        if score < 0:
            result.errors.append(f"qa_result.dimension_scores.{dimension_id} cannot be negative")


def validate_email(email: dict[str, Any], index: int, banned_phrases: list[str], result: CopyValidationResult) -> None:
    missing = sorted(field for field in REQUIRED_EMAIL_FIELDS if field not in email)
    if missing:
        result.errors.append(f"emails[{index}] missing required fields: {', '.join(missing)}")
        return

    for field_name in ["subject", "body", "cta"]:
        if not isinstance(email.get(field_name), str) or not email[field_name].strip():
            result.errors.append(f"emails[{index}].{field_name} must be a non-empty string")

    claims_used = email.get("claims_used")
    source_refs = email.get("source_refs")
    if not isinstance(claims_used, list):
        result.errors.append(f"emails[{index}].claims_used must be a list")
    if not isinstance(source_refs, list) or not source_refs:
        result.errors.append(f"emails[{index}].source_refs must be a non-empty list")
    if isinstance(claims_used, list) and claims_used and not source_refs:
        result.errors.append(f"emails[{index}] has claims_used but no source_refs")

    searchable = f"{email.get('subject', '')}\n{email.get('body', '')}\n{email.get('cta', '')}"
    for phrase in banned_phrases:
        if contains_phrase(searchable, phrase):
            result.errors.append(f"emails[{index}] contains banned phrase: {phrase}")

    body_words = word_count(str(email.get("body", "")))
    if body_words > DEFAULT_MAX_EMAIL_WORDS:
        result.warnings.append(f"emails[{index}].body has {body_words} words; target is {DEFAULT_MAX_EMAIL_WORDS} or fewer")


def validate_copy_packet(packet_path: Path, rubric_path: Path = DEFAULT_RUBRIC_PATH) -> CopyValidationResult:
    result = CopyValidationResult(valid=False, copy_packet_path=str(packet_path), checked_at=utc_now())

    try:
        packet = load_json(packet_path)
    except json.JSONDecodeError as exc:
        result.errors.append(f"Invalid JSON in {packet_path}: {exc}")
        return result
    except FileNotFoundError:
        result.errors.append(f"Missing copy packet: {packet_path}")
        return result

    try:
        rubric = load_json(rubric_path)
    except json.JSONDecodeError as exc:
        result.errors.append(f"Invalid JSON in {rubric_path}: {exc}")
        return result
    except FileNotFoundError:
        result.errors.append(f"Missing rubric: {rubric_path}")
        return result

    missing = sorted(field for field in REQUIRED_TOP_LEVEL_FIELDS if field not in packet)
    if missing:
        result.errors.append(f"copy packet missing required fields: {', '.join(missing)}")

    if packet.get("workflow_name") != "DeployGTM Prospect Copy":
        result.errors.append("workflow_name must be DeployGTM Prospect Copy")

    emails = packet.get("emails", [])
    if not isinstance(emails, list) or not emails:
        result.errors.append("emails must be a non-empty list")
    else:
        banned_phrases = list(rubric.get("banned_phrases", []))
        for index, email in enumerate(emails):
            if not isinstance(email, dict):
                result.errors.append(f"emails[{index}] must be an object")
                continue
            validate_email(email, index, banned_phrases, result)

    source_trace = packet.get("source_trace", [])
    if not isinstance(source_trace, list) or not source_trace:
        result.errors.append("source_trace must be a non-empty list")

    qa_result = packet.get("qa_result", {})
    if not isinstance(qa_result, dict):
        result.errors.append("qa_result must be an object")
    else:
        missing_qa = sorted(field for field in REQUIRED_QA_FIELDS if field not in qa_result)
        if missing_qa:
            result.errors.append(f"qa_result missing required fields: {', '.join(missing_qa)}")

        score = qa_result.get("total_score")
        if isinstance(score, (int, float)):
            result.score = float(score)
            if result.score < float(rubric.get("pass_threshold", 85)):
                result.errors.append(f"qa_result.total_score {result.score:g} is below pass threshold {rubric.get('pass_threshold', 85)}")
        else:
            result.errors.append("qa_result.total_score must be numeric")

        hard_fail_flags = qa_result.get("hard_fail_flags", [])
        if not isinstance(hard_fail_flags, list):
            result.errors.append("qa_result.hard_fail_flags must be a list")
        elif hard_fail_flags:
            result.errors.append(f"qa_result.hard_fail_flags must be empty to pass: {', '.join(map(str, hard_fail_flags))}")

        if qa_result.get("decision") != "pass":
            result.errors.append("qa_result.decision must be pass")

        validate_dimension_scores(packet, rubric, result)

    result.valid = not result.errors
    return result


def result_to_dict(result: CopyValidationResult) -> dict[str, Any]:
    return asdict(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a DeployGTM prospect copy packet.")
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC_PATH)
    args = parser.parse_args()

    result = validate_copy_packet(args.packet, args.rubric)
    print(json.dumps(result_to_dict(result), indent=2))
    if not result.valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
