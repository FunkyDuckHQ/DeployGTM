from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.platform.account_matrix import build_account_matrix
from scripts.platform.crm_push_plan import build_crm_push_plan
from scripts.platform.deliverable import build_signal_audit_deliverable
from scripts.platform.icp_strategy import generate_icp_strategy
from scripts.platform.intake import create_customer_outcome_intake
from scripts.platform.signal_strategy import build_signal_strategy


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
    crm_plan_path = build_crm_push_plan("acme-space", projects_dir=tmp_path)
    deliverable_dir = build_signal_audit_deliverable("acme-space", projects_dir=tmp_path)

    strategy = json.loads(strategy_path.read_text())
    signals = json.loads(signal_path.read_text())
    matrix = json.loads(matrix_path.read_text())
    crm_plan = json.loads(crm_plan_path.read_text())

    assert strategy["strategy"]["icps"]
    assert len(signals["signals"]) == 20
    scores = matrix["accounts"][0]["scores"]
    assert {"icp_fit_score", "urgency_score", "engagement_score", "confidence_score", "activation_priority"} <= set(scores)
    assert crm_plan["dry_run"] is True
    assert crm_plan["writes_enabled"] is False
    assert (deliverable_dir / "signal_audit_summary.md").exists()
    assert (deliverable_dir / "target_accounts.csv").exists()
