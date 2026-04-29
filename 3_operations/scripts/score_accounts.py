#!/usr/bin/env python3
"""Score DeployGTM sandbox accounts for ICP fit, urgency, and route.

This is intentionally small and inspectable. It turns JSON account inputs into
JSON ScoreSnapshot-style output so the scoring model can be refined with real
examples before any vendor or CRM writes exist.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

ICP_COMPONENTS = {
    "firmographic_fit": 20,
    "segment_fit": 20,
    "pain_hypothesis": 15,
    "ability_to_buy": 15,
    "strategic_value": 10,
    "evidence_confidence": 20,
}


@dataclass
class ScoreResult:
    account_id: str
    company_name: str
    icp_score: float
    urgency_score: float
    route: str
    evidence: list[dict[str, Any]]


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


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


def score_icp(account: dict[str, Any]) -> float:
    score = 0.0
    for field, max_points in ICP_COMPONENTS.items():
        score += min(float(account.get(field, 0)), max_points)
    score += float(account.get("negative_adjustment", 0))
    return clamp(score)


def score_urgency(account: dict[str, Any], signal_defs: dict[str, dict[str, Any]], as_of: date) -> tuple[float, list[dict[str, Any]]]:
    total = 0.0
    evidence: list[dict[str, Any]] = []

    for signal in account.get("signals", []):
        definition = signal_defs.get(signal.get("signal_definition_id"), {})
        half_life = int(signal.get("decay_half_life_days") or definition.get("decay_half_life_days") or 30)
        observed_at = parse_date(signal["observed_at"])
        current_strength = decayed_strength(float(signal.get("original_strength", 0)), observed_at, half_life, as_of)
        confidence = float(signal.get("confidence", 0.5))
        urgency_weight = float(definition.get("urgency_weight", 10))
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
                "urgency_contribution": round(contribution, 2),
                "ability_to_act_evidence": signal.get("ability_to_act_evidence"),
                "willingness_to_act_evidence": signal.get("willingness_to_act_evidence"),
            }
        )

    return clamp(total * 4), evidence


def choose_route(icp_score: float, urgency_score: float) -> str:
    if icp_score >= 80 and urgency_score >= 70:
        return "manual_sales_review_and_enrich"
    if icp_score >= 80 and urgency_score >= 40:
        return "enrich_and_campaign_test"
    if icp_score >= 80:
        return "enrich_selectively_or_monitor"
    if icp_score >= 65 and urgency_score >= 80:
        return "manual_sales_review"
    if icp_score >= 65 and urgency_score >= 50:
        return "monitor_or_test_cohort"
    if urgency_score >= 85:
        return "human_review_only"
    if icp_score >= 50:
        return "hold_or_monitor"
    return "exclude"


def score_accounts(accounts_path: Path, signals_path: Path, as_of: date) -> dict[str, Any]:
    account_data = load_json(accounts_path)
    signal_data = load_json(signals_path)
    signal_defs = {item["signal_definition_id"]: item for item in signal_data.get("signal_definitions", [])}

    results: list[ScoreResult] = []
    for account in account_data.get("accounts", []):
        icp = score_icp(account)
        urgency, evidence = score_urgency(account, signal_defs, as_of)
        route = choose_route(icp, urgency)
        results.append(
            ScoreResult(
                account_id=account["account_id"],
                company_name=account["company_name"],
                icp_score=round(icp, 2),
                urgency_score=round(urgency, 2),
                route=route,
                evidence=evidence,
            )
        )

    return {
        "client_id": account_data.get("client_id"),
        "generated_at": as_of.isoformat(),
        "source_notes": account_data.get("source_notes", []),
        "score_snapshots": [
            {
                "account_id": result.account_id,
                "company_name": result.company_name,
                "icp_score": result.icp_score,
                "urgency_score": result.urgency_score,
                "recommended_route": result.route,
                "evidence": result.evidence,
            }
            for result in sorted(results, key=lambda item: (item.icp_score, item.urgency_score), reverse=True)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Score DeployGTM sandbox accounts.")
    parser.add_argument("--accounts", type=Path, default=Path("examples/peregrine/accounts.json"))
    parser.add_argument("--signals", type=Path, default=Path("examples/peregrine/signal_definitions.json"))
    parser.add_argument("--output", type=Path, default=Path("3_operations/outputs/peregrine_score_snapshots.json"))
    parser.add_argument("--as-of", default=date.today().isoformat())
    args = parser.parse_args()

    output = score_accounts(args.accounts, args.signals, parse_date(args.as_of))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
