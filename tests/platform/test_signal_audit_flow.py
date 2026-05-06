"""
Signal Audit end-to-end flow test.

Runs entirely offline via LLM_SKIP=true — no API keys required.
LLM calls return deterministic fallback values so the schema and
pipeline structure are verified without network calls.
"""
from pathlib import Path
import json
import os
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.platform.account_matrix import build_account_matrix
from scripts.platform.brief import build_briefs
from scripts.platform.crm_push_plan import build_crm_push_plan
from scripts.platform.deliverable import build_signal_audit_deliverable
from scripts.platform.icp_strategy import generate_icp_strategy
from scripts.platform.intake import create_customer_outcome_intake
from scripts.platform.messaging import build_messaging
from scripts.platform.signal_strategy import build_signal_strategy


@pytest.fixture(autouse=True)
def llm_skip(monkeypatch):
    """Force LLM_SKIP=true for all tests in this file — no API calls."""
    monkeypatch.setenv("LLM_SKIP", "true")


def test_signal_audit_artifacts_run_no_write_flow(tmp_path: Path):
    intake_path = create_customer_outcome_intake(
        client_name="Acme Space",
        domain="acme.space",
        target_outcome="create qualified pipeline",
        offer="AI workflow tool",
        client_slug="acme-space",
        projects_dir=tmp_path,
    )
    assert intake_path.exists()

    strategy_path = generate_icp_strategy("acme-space", projects_dir=tmp_path)
    signal_path = build_signal_strategy("acme-space", projects_dir=tmp_path)
    matrix_path = build_account_matrix(
        "acme-space",
        projects_dir=tmp_path,
        rows=[
            {
                "company": "Northstar Ops",
                "domain": "northstar.example",
                "signal_type": "hiring",
                "signal_date": "2026-04-01",
                "signal_source": "BirdDog",
                "signal_summary": "Hiring sales ops after launch",
                "birddog_score": "80",
            }
        ],
    )
    messaging_path = build_messaging("acme-space", projects_dir=tmp_path)
    briefs_path = build_briefs("acme-space", projects_dir=tmp_path)
    crm_plan_path = build_crm_push_plan("acme-space", projects_dir=tmp_path)
    deliverable_dir = build_signal_audit_deliverable("acme-space", projects_dir=tmp_path)

    strategy = json.loads(strategy_path.read_text())
    signals = json.loads(signal_path.read_text())
    matrix = json.loads(messaging_path.read_text())  # messaging writes back to accounts.json
    crm_plan = json.loads(crm_plan_path.read_text())
    briefs = json.loads(briefs_path.read_text())

    assert strategy["strategy"]["icps"]
    assert len(signals["signals"]) == 20
    scores = matrix["accounts"][0]["scores"]
    assert {"icp_fit_score", "urgency_score", "engagement_score", "confidence_score", "activation_priority"} <= set(scores)
    # messaging step populates copy field
    copy = matrix["accounts"][0]["copy"]
    assert "first_touch" in copy
    assert "subject_line" in copy
    # briefs step produces per-account briefs keyed by domain
    assert briefs["briefs"]
    assert crm_plan["dry_run"] is True
    assert crm_plan["writes_enabled"] is False
    assert (deliverable_dir / "signal_audit_summary.md").exists()
    assert (deliverable_dir / "target_accounts.csv").exists()


def test_intake_does_not_overwrite_existing_handoff(tmp_path: Path):
    """handoff.md and open-loops.md must survive a second intake call."""
    # First call creates the files
    create_customer_outcome_intake(
        client_name="Preserve Co",
        domain="preserve.co",
        target_outcome="keep my context",
        offer="something useful",
        client_slug="preserve-co",
        projects_dir=tmp_path,
    )

    handoff_path = tmp_path / "preserve-co" / "handoff.md"
    loops_path = tmp_path / "preserve-co" / "open-loops.md"

    # Simulate rich human-written content
    rich_handoff = "# Rich Handoff\n\nThis was written by a human and must not be lost."
    rich_loops = "# Rich Open Loops\n\n- Real blocker that matters"
    handoff_path.write_text(rich_handoff)
    loops_path.write_text(rich_loops)

    # Second intake call (with force=True on intake.json/context.md)
    create_customer_outcome_intake(
        client_name="Preserve Co",
        domain="preserve.co",
        target_outcome="keep my context",
        offer="something useful",
        client_slug="preserve-co",
        projects_dir=tmp_path,
        force=True,
    )

    assert handoff_path.read_text() == rich_handoff, "handoff.md was overwritten"
    assert loops_path.read_text() == rich_loops, "open-loops.md was overwritten"


def test_account_scores_use_full_range_with_varied_input(tmp_path: Path):
    """
    With LLM_SKIP=true the heuristic fallback runs.
    Accounts with richer signal data should score higher than sparse ones.
    """
    create_customer_outcome_intake(
        client_name="Score Test",
        domain="scoretest.example",
        target_outcome="prove scoring differentiates",
        offer="B2B SaaS tool",
        client_slug="score-test",
        projects_dir=tmp_path,
    )
    generate_icp_strategy("score-test", projects_dir=tmp_path)

    matrix_path = build_account_matrix(
        "score-test",
        projects_dir=tmp_path,
        rows=[
            {
                "company": "Signal Rich Co",
                "domain": "rich.example",
                "signal_type": "funding",
                "signal_date": "2026-04-01",
                "signal_source": "BirdDog",
                "signal_summary": "Raised Seed, hiring sales, pipeline pain",
                "birddog_score": "85",
            },
            {
                "company": "Signal Poor Co",
                "domain": "poor.example",
                "signal_type": "manual",
                "signal_date": None,
                "signal_source": "manual",
                "signal_summary": "",
                "birddog_score": None,
            },
        ],
    )

    matrix = json.loads(matrix_path.read_text())
    accounts = {a["company"]: a["scores"] for a in matrix["accounts"]}
    rich = accounts["Signal Rich Co"]
    poor = accounts["Signal Poor Co"]

    # The richer account should score higher on urgency (BirdDog + date)
    assert rich["urgency_score"] > poor["urgency_score"], (
        f"Expected rich urgency {rich['urgency_score']} > poor urgency {poor['urgency_score']}"
    )


def test_messaging_produces_copy_for_all_accounts(tmp_path: Path):
    """
    With LLM_SKIP=true, messaging falls back to deterministic template copy.
    Every account must get a non-empty first_touch and subject_line after the step.
    """
    create_customer_outcome_intake(
        client_name="Msg Test",
        domain="msgtest.example",
        target_outcome="generate qualified pipeline",
        offer="B2B SaaS tool",
        client_slug="msg-test",
        projects_dir=tmp_path,
    )
    generate_icp_strategy("msg-test", projects_dir=tmp_path)
    build_account_matrix(
        "msg-test",
        projects_dir=tmp_path,
        rows=[
            {
                "company": "Alpha Corp",
                "domain": "alpha.example",
                "signal_type": "funding",
                "signal_date": "2026-04-01",
                "signal_source": "BirdDog",
                "signal_summary": "Raised Seed, hiring first AE",
                "birddog_score": "82",
            },
            {
                "company": "Beta LLC",
                "domain": "beta.example",
                "signal_type": "hiring",
                "signal_date": "2026-03-15",
                "signal_source": "manual",
                "signal_summary": "Posted VP Sales job",
                "birddog_score": None,
            },
        ],
    )

    matrix_path = build_messaging("msg-test", projects_dir=tmp_path)
    matrix = json.loads(matrix_path.read_text())

    for account in matrix["accounts"]:
        copy = account.get("copy", {})
        assert copy.get("first_touch"), f"Missing first_touch for {account['company']}"
        assert copy.get("subject_line"), f"Missing subject_line for {account['company']}"
        assert copy.get("status") == "drafted", f"Status not 'drafted' for {account['company']}"


def test_briefs_produce_structured_output_per_account(tmp_path: Path):
    """
    With LLM_SKIP=true, briefs fall back to deterministic templates.
    Every account should have a brief with required keys.
    """
    create_customer_outcome_intake(
        client_name="Brief Test",
        domain="brieftest.example",
        target_outcome="prove outbound pipeline ROI",
        offer="Pipeline Engine retainer",
        client_slug="brief-test",
        projects_dir=tmp_path,
    )
    generate_icp_strategy("brief-test", projects_dir=tmp_path)
    build_account_matrix(
        "brief-test",
        projects_dir=tmp_path,
        rows=[
            {
                "company": "Gamma Inc",
                "domain": "gamma.example",
                "signal_type": "hiring",
                "signal_date": "2026-04-10",
                "signal_source": "LinkedIn",
                "signal_summary": "Hiring RevOps Manager",
                "birddog_score": "70",
            }
        ],
    )
    build_messaging("brief-test", projects_dir=tmp_path)

    briefs_path = build_briefs("brief-test", projects_dir=tmp_path)
    briefs_data = json.loads(briefs_path.read_text())

    assert briefs_data["briefs"], "No briefs generated"
    required_keys = {"account_snapshot", "why_now", "talking_points", "likely_objections", "recommended_ask"}
    for key, brief in briefs_data["briefs"].items():
        missing = required_keys - set(brief.keys())
        assert not missing, f"Brief for {key} missing keys: {missing}"
        assert brief["talking_points"], f"No talking points for {key}"
        assert brief["likely_objections"], f"No objections for {key}"
