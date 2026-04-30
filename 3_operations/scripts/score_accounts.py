#!/usr/bin/env python3
"""Score DeployGTM client accounts for ICP fit, urgency, and route.

Phase 1 is intentionally file-based. The scorer loads client inputs and
configuration from `clients/{client_id}/` so service delivery can reuse the
same workflow across clients before any API, MCP, or vendor integration exists.
"""

from __future__ import annotations

import argparse
import json
import math
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


CLIENTS_ROOT = Path("clients")


@dataclass
class ClientPaths:
    client_id: str
    root: Path
    accounts: Path
    scoring: Path
    signals: Path
    output: Path
    runs: Path


@dataclass
class ScoreResult:
    account_id: str
    company_name: str
    icp_score: float
    urgency_score: float
    route: str
    evidence: list[dict[str, Any]]
    component_scores: dict[str, float]


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return max(minimum, min(maximum, value))


def decayed_strength(original_strength: float, observed_at: date, half_life_days: int, as_of: date) -> float:
    days_since = max((as_of - observed_at).days, 0)
    if half_life_days <= 0:
        return original_strength
    return original_strength * math.pow(0.5, days_since / half_life_days)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_client_paths(client_id: str, clients_root: Path = CLIENTS_ROOT) -> ClientPaths:
    root = clients_root / client_id
    return ClientPaths(
        client_id=client_id,
        root=root,
        accounts=root / "inputs" / "accounts.json",
        scoring=root / "config" / "scoring.json",
        signals=root / "config" / "signal_definitions.json",
        output=root / "outputs" / "score_snapshots.json",
        runs=root / "runs",
    )


def score_icp(account: dict[str, Any], scoring_config: dict[str, Any]) -> tuple[float, dict[str, float]]:
    components = scoring_config.get("icp_components", {})
    component_scores: dict[str, float] = {}
    score = 0.0

    for field, max_points in components.items():
        value = min(float(account.get(field, 0)), float(max_points))
        component_scores[field] = round(value, 2)
        score += value

    negative_field = scoring_config.get("negative_adjustment_field", "negative_adjustment")
    negative_adjustment = float(account.get(negative_field, 0))
    component_scores[negative_field] = round(negative_adjustment, 2)
    score += negative_adjustment

    return clamp(score), component_scores


def score_urgency(
    account: dict[str, Any],
    signal_defs: dict[str, dict[str, Any]],
    scoring_config: dict[str, Any],
    as_of: date,
) -> tuple[float, list[dict[str, Any]]]:
    total = 0.0
    evidence: list[dict[str, Any]] = []

    for signal in account.get("signals", []):
        definition = signal_defs.get(signal.get("signal_definition_id"), {})
        half_life = int(
            signal.get("decay_half_life_days")
            or definition.get("decay_half_life_days")
            or scoring_config.get("default_decay_half_life_days", 30)
        )
        observed_at = parse_date(signal["observed_at"])
        current_strength = decayed_strength(float(signal.get("original_strength", 0)), observed_at, half_life, as_of)
        confidence = float(signal.get("confidence", scoring_config.get("default_signal_confidence", 0.5)))
        urgency_weight = float(definition.get("urgency_weight", scoring_config.get("default_signal_weight", 10)))
        contribution = (current_strength / 100) * urgency_weight * confidence
        total += contribution
        evidence.append(
            {
                "signal_id": signal.get("signal_id"),
                "signal_type": signal.get("signal_type"),
                "summary": signal.get("summary"),
                "source_url": signal.get("source_url"),
                "observed_at": signal.get("observed_at"),
                "original_strength": signal.get("original_strength"),
                "current_strength": round(current_strength, 2),
                "confidence": confidence,
                "urgency_weight": urgency_weight,
                "urgency_contribution": round(contribution, 2),
                "ability_to_act_evidence": signal.get("ability_to_act_evidence"),
                "willingness_to_act_evidence": signal.get("willingness_to_act_evidence"),
            }
        )

    return clamp(total * float(scoring_config.get("urgency_multiplier", 4))), evidence


def matches_conditions(icp_score: float, urgency_score: float, conditions: dict[str, Any]) -> bool:
    checks = {
        "min_icp": icp_score >= float(conditions.get("min_icp", 0)),
        "max_icp": icp_score <= float(conditions.get("max_icp", 100)),
        "min_urgency": urgency_score >= float(conditions.get("min_urgency", 0)),
        "max_urgency": urgency_score <= float(conditions.get("max_urgency", 100)),
    }
    return all(checks[key] for key in checks if key in conditions)


def choose_route(icp_score: float, urgency_score: float, scoring_config: dict[str, Any] | None = None) -> str:
    if scoring_config is None:
        scoring_config = {
            "route_thresholds": [
                {"route": "manual_sales_review_and_enrich", "conditions": {"min_icp": 80, "min_urgency": 70}},
                {"route": "enrich_and_campaign_test", "conditions": {"min_icp": 80, "min_urgency": 40}},
                {"route": "enrich_selectively_or_monitor", "conditions": {"min_icp": 80}},
                {"route": "manual_sales_review", "conditions": {"min_icp": 65, "max_icp": 79.99, "min_urgency": 80}},
                {"route": "monitor_or_test_cohort", "conditions": {"min_icp": 65, "max_icp": 79.99, "min_urgency": 50}},
                {"route": "human_review_only", "conditions": {"max_icp": 64.99, "min_urgency": 85}},
                {"route": "hold_or_monitor", "conditions": {"min_icp": 50}},
                {"route": "exclude", "conditions": {}},
            ]
        }

    for threshold in scoring_config.get("route_thresholds", []):
        if matches_conditions(icp_score, urgency_score, threshold.get("conditions", {})):
            return threshold["route"]
    return "exclude"


def score_accounts_data(
    account_data: dict[str, Any],
    signal_data: dict[str, Any],
    scoring_config: dict[str, Any],
    as_of: date,
) -> dict[str, Any]:
    signal_defs = {item["signal_definition_id"]: item for item in signal_data.get("signal_definitions", [])}

    results: list[ScoreResult] = []
    for account in account_data.get("accounts", []):
        icp, component_scores = score_icp(account, scoring_config)
        urgency, evidence = score_urgency(account, signal_defs, scoring_config, as_of)
        route = choose_route(icp, urgency, scoring_config)
        results.append(
            ScoreResult(
                account_id=account["account_id"],
                company_name=account["company_name"],
                icp_score=round(icp, 2),
                urgency_score=round(urgency, 2),
                route=route,
                evidence=evidence,
                component_scores=component_scores,
            )
        )

    return {
        "client_id": account_data.get("client_id") or scoring_config.get("client_id"),
        "generated_at": as_of.isoformat(),
        "source_notes": account_data.get("source_notes", []),
        "score_snapshots": [
            {
                "account_id": result.account_id,
                "company_name": result.company_name,
                "icp_score": result.icp_score,
                "urgency_score": result.urgency_score,
                "component_scores": result.component_scores,
                "recommended_route": result.route,
                "evidence": result.evidence,
            }
            for result in sorted(results, key=lambda item: (item.icp_score, item.urgency_score), reverse=True)
        ],
    }


def score_accounts(accounts_path: Path, signals_path: Path, as_of: date, scoring_path: Path | None = None) -> dict[str, Any]:
    scoring_config = load_json(scoring_path) if scoring_path else {
        "icp_components": {
            "firmographic_fit": 20,
            "segment_fit": 20,
            "pain_hypothesis": 15,
            "ability_to_buy": 15,
            "strategic_value": 10,
            "evidence_confidence": 20,
        },
        "urgency_multiplier": 4,
    }
    return score_accounts_data(load_json(accounts_path), load_json(signals_path), scoring_config, as_of)


def score_client(client_id: str, as_of: date, clients_root: Path = CLIENTS_ROOT, output_path: Path | None = None) -> tuple[dict[str, Any], ClientPaths]:
    paths = get_client_paths(client_id, clients_root)
    output = score_accounts(paths.accounts, paths.signals, as_of, paths.scoring)
    write_json(output_path or paths.output, output)
    return output, paths


def write_run_log(
    client_id: str,
    workflow: str,
    inputs_used: list[Path],
    config_used: list[Path],
    outputs_written: list[Path],
    errors: list[str] | None,
    runs_dir: Path,
    execution_id: str | None = None,
) -> Path:
    execution_id = execution_id or f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    payload = {
        "execution_id": execution_id,
        "timestamp": utc_now(),
        "client_id": client_id,
        "workflow": workflow,
        "inputs_used": [str(path) for path in inputs_used],
        "config_used": [str(path) for path in config_used],
        "outputs_written": [str(path) for path in outputs_written],
        "errors": errors or [],
    }
    path = runs_dir / f"{execution_id}.json"
    write_json(path, payload)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Score DeployGTM client accounts.")
    parser.add_argument("--client", default="peregrine_space")
    parser.add_argument("--clients-root", type=Path, default=CLIENTS_ROOT)
    parser.add_argument("--accounts", type=Path)
    parser.add_argument("--signals", type=Path)
    parser.add_argument("--scoring", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--log-run", action="store_true")
    args = parser.parse_args()

    as_of = parse_date(args.as_of)
    paths = get_client_paths(args.client, args.clients_root)
    accounts_path = args.accounts or paths.accounts
    signals_path = args.signals or paths.signals
    scoring_path = args.scoring or paths.scoring
    output_path = args.output or paths.output
    errors: list[str] = []

    try:
        output = score_accounts(accounts_path, signals_path, as_of, scoring_path)
        write_json(output_path, output)
        print(json.dumps(output, indent=2))
    except Exception as exc:
        errors.append(str(exc))
        if args.log_run:
            write_run_log(
                args.client,
                "score_accounts",
                [accounts_path],
                [scoring_path, signals_path],
                [output_path],
                errors,
                paths.runs,
            )
        raise

    if args.log_run:
        write_run_log(
            args.client,
            "score_accounts",
            [accounts_path],
            [scoring_path, signals_path],
            [output_path],
            errors,
            paths.runs,
        )


if __name__ == "__main__":
    main()
