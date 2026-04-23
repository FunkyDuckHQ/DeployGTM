from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.platform.bootstrap_client import bootstrap_client
from scripts.platform.icp_strategy import generate_icp_strategy


def test_bootstrap_creates_platform_files(tmp_path: Path):
    result = bootstrap_client(
        client_name="Acme Space",
        domain="acme.space",
        projects_dir=tmp_path,
    )

    assert result.client_slug == "acme-space"
    assert (tmp_path / "acme-space" / "platform" / "client_profile.json").exists()
    assert (tmp_path / "acme-space" / "platform" / "accounts.json").exists()


def test_strategy_generator_writes_expected_shape(tmp_path: Path):
    # seed minimal project context + brain priors for deterministic strategy output
    client_dir = tmp_path / "acme-space"
    client_dir.mkdir(parents=True, exist_ok=True)
    (client_dir / "context.md").write_text("- objective: build repeatable outbound\n- current state: no scoring system")
    (client_dir / "handoff.md").write_text("- decisions already made: signal-first")
    (client_dir / "open-loops.md").write_text("- need to decide: market priority")

    # monkeypatch module paths by importing and replacing globals
    from scripts.platform import context_pack as cp
    from scripts.platform import icp_strategy as strat

    cp.PROJECTS_DIR = tmp_path
    strat.PROJECTS_DIR = tmp_path

    out = generate_icp_strategy("acme-space", projects_dir=tmp_path)
    data = json.loads(out.read_text())
    context_pack = tmp_path / "acme-space" / "platform" / "context_pack.json"

    assert data["client_slug"] == "acme-space"
    assert data["strategy"]["principles"]
    assert data["strategy"]["market_hypotheses"]
    assert data["strategy"]["segment_rules"]
    assert context_pack.exists()
