#!/usr/bin/env python3
"""Build an operator-readable route report from score snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROUTE_LABELS = {
    "manual_sales_review_and_enrich": "Manual sales review + enrich",
    "enrich_and_campaign_test": "Enrich + campaign test",
    "enrich_selectively_or_monitor": "Selective enrichment or monitor",
    "manual_sales_review": "Manual sales review",
    "monitor_or_test_cohort": "Monitor or test cohort",
    "human_review_only": "Human review only",
    "hold_or_monitor": "Hold or monitor",
    "exclude": "Exclude",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def format_evidence(evidence: list[dict[str, Any]]) -> str:
    if not evidence:
        return "- No evidence attached."

    lines: list[str] = []
    for item in evidence:
        lines.append(
            f"- {item.get('signal_type')}: {item.get('summary')} "
            f"(strength {item.get('current_strength')}, confidence {item.get('confidence')})"
        )
        if item.get("source_url"):
            lines.append(f"  Source: {item['source_url']}")
    return "\n".join(lines)


def next_action(route: str) -> str:
    if route == "manual_sales_review_and_enrich":
        return "Assign to founder/seller, enrich contacts, and draft founder-reviewed outreach."
    if route == "enrich_and_campaign_test":
        return "Enrich likely buyers and create a controlled message-market fit test."
    if route == "enrich_selectively_or_monitor":
        return "Monitor for urgency signals and enrich only if a timing event appears."
    if route in {"manual_sales_review", "human_review_only"}:
        return "Review manually before any automation."
    if route == "monitor_or_test_cohort":
        return "Keep in a small test cohort or monitor for stronger timing."
    if route == "hold_or_monitor":
        return "Hold until more evidence appears."
    return "Exclude from current motion."


def build_report(score_data: dict[str, Any]) -> str:
    lines = [
        f"# Route Report: {score_data.get('client_id', 'unknown')}",
        "",
        f"Generated at: {score_data.get('generated_at')}",
        "",
        "## Summary",
        "",
    ]

    snapshots = score_data.get("score_snapshots", [])
    route_counts: dict[str, int] = {}
    for snapshot in snapshots:
        route = snapshot.get("recommended_route", "unknown")
        route_counts[route] = route_counts.get(route, 0) + 1

    for route, count in sorted(route_counts.items()):
        lines.append(f"- {ROUTE_LABELS.get(route, route)}: {count}")

    lines.extend(["", "## Accounts", ""])

    for snapshot in snapshots:
        route = snapshot.get("recommended_route", "unknown")
        lines.extend(
            [
                f"### {snapshot.get('company_name')}",
                "",
                f"- ICP score: `{snapshot.get('icp_score')}`",
                f"- Urgency score: `{snapshot.get('urgency_score')}`",
                f"- Route: `{ROUTE_LABELS.get(route, route)}`",
                f"- Next action: {next_action(route)}",
                "",
                "Evidence:",
                "",
                format_evidence(snapshot.get("evidence", [])),
                "",
            ]
        )

    lines.extend(
        [
            "## Source Notes",
            "",
            "- Generated from `3_operations/outputs/peregrine_score_snapshots.json`.",
            "- Scoring logic lives in `3_operations/scripts/score_accounts.py`.",
            "- Sandbox source context references the Peregrine Space working brief in Drive.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a route report from score snapshots.")
    parser.add_argument("--input", type=Path, default=Path("3_operations/outputs/peregrine_score_snapshots.json"))
    parser.add_argument("--output", type=Path, default=Path("3_operations/outputs/peregrine_route_report.md"))
    args = parser.parse_args()

    report = build_report(load_json(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
