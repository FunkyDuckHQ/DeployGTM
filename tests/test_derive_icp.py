"""
Offline tests for scripts/derive_icp.py — ICP profile derivation, loading,
and merging with defaults.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestDeriveIcp(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="dgtm-icp-"))
        (self.tmpdir / "projects" / "testclient").mkdir(parents=True)
        (self.tmpdir / "projects" / "deploygtm-own" / "data").mkdir(parents=True)

        self.derive = _load("t_derive_icp", SCRIPTS_DIR / "derive_icp.py")
        # Redirect paths to tmpdir
        self.derive.PROJECTS_DIR = self.tmpdir / "projects"
        self.derive.MATRIX_DATA_DIR = self.tmpdir / "projects" / "deploygtm-own" / "data"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        sys.modules.pop("t_derive_icp", None)

    def test_default_profile_has_required_fields(self):
        p = self.derive.DEFAULT_PROFILE
        self.assertIn("fit_dimensions", p)
        self.assertIn("signal_weights", p)
        self.assertIn("signal_decay_days", p)
        self.assertIn("status_deltas", p)
        self.assertIn("personas", p)
        self.assertEqual(p["fit_max_score"], 10.0)

    def test_profile_path_normalises_dash_to_underscore(self):
        path = self.derive.profile_path("peregrine-space")
        self.assertEqual(path.name, "peregrine_space_icp_profile.json")

    def test_load_profile_returns_default_when_no_file(self):
        p = self.derive.load_profile("nonexistent")
        self.assertEqual(p["fit_max_score"], 10.0)
        # Should contain all default top-level keys
        for key in ("fit_dimensions", "signal_weights", "signal_decay_days",
                    "status_deltas", "personas"):
            self.assertIn(key, p)

    def test_load_profile_merges_client_overrides(self):
        # Write a partial client profile
        path = self.derive.profile_path("testclient")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "client_product_summary": "Custom test product",
            "signal_weights": {"sbir_award": 4},
            "personas": {"program_manager": ["Program Manager"]},
        }))

        p = self.derive.load_profile("testclient")

        # Client field present
        self.assertEqual(p["client_product_summary"], "Custom test product")
        # Client signal merged with defaults
        self.assertEqual(p["signal_weights"]["sbir_award"], 4)
        self.assertIn("funding", p["signal_weights"])  # default still there
        # Client persona merged with defaults
        self.assertIn("program_manager", p["personas"])

    def test_deep_merge_overrides_scalar_top_level(self):
        base = {"fit_max_score": 10.0, "signal_weights": {"a": 1}}
        override = {"fit_max_score": 12.0}
        merged = self.derive._deep_merge(base, override)
        self.assertEqual(merged["fit_max_score"], 12.0)
        self.assertEqual(merged["signal_weights"], {"a": 1})

    def test_deep_merge_merges_nested_dicts(self):
        base = {"signal_weights": {"funding": 3, "hiring": 2}}
        override = {"signal_weights": {"funding": 4, "sbir": 5}}
        merged = self.derive._deep_merge(base, override)
        self.assertEqual(merged["signal_weights"], {"funding": 4, "hiring": 2, "sbir": 5})

    def test_write_profile_adds_metadata(self):
        path = self.derive.write_profile("testclient", {
            "client_product_summary": "A thing",
            "fit_dimensions": [],
        })
        self.assertTrue(path.exists())
        data = json.loads(path.read_text())
        self.assertEqual(data["client"], "testclient")
        self.assertIn("derived_at", data)
        self.assertEqual(data["client_product_summary"], "A thing")

    def test_derive_with_claude_calls_anthropic(self):
        fake_response = {
            "client_product_summary": "Test product summary",
            "fit_dimensions": [
                {"name": "test_dim", "weight": 2.0, "max_raw": 2,
                 "description": "x", "high_signal": "y", "low_signal": "z"},
            ],
            "fit_max_score": 10.0,
            "signal_weights": {"test_signal": 3},
            "signal_decay_days": {"default": 60},
            "personas": {"test_persona": ["Test Title"]},
            "disqualifiers": ["No fit"],
        }

        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=json.dumps(fake_response))]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_msg

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("anthropic.Anthropic", return_value=mock_client):
                result = self.derive._derive_with_claude(
                    "testclient",
                    "# Test context\nThis is a test ICP.",
                )

        self.assertEqual(result["client_product_summary"], "Test product summary")
        self.assertEqual(len(result["fit_dimensions"]), 1)
        mock_client.messages.create.assert_called_once()

    def test_derive_with_claude_strips_markdown_fences(self):
        fenced = "```json\n" + json.dumps({"client_product_summary": "X",
                                            "fit_dimensions": [], "fit_max_score": 10.0,
                                            "signal_weights": {}, "signal_decay_days": {},
                                            "personas": {}, "disqualifiers": []}) + "\n```"
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=fenced)]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_msg

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("anthropic.Anthropic", return_value=mock_client):
                result = self.derive._derive_with_claude("test", "context")

        self.assertEqual(result["client_product_summary"], "X")

    def test_derive_with_claude_raises_on_invalid_json(self):
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="not valid json")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_msg

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("anthropic.Anthropic", return_value=mock_client):
                import click
                with self.assertRaises(click.ClickException):
                    self.derive._derive_with_claude("test", "context")


class TestScoreEngineWithProfile(unittest.TestCase):
    """Verify score_engine respects a custom profile passed in.

    NOTE: score_engine lives in projects/deploygtm-own/scripts/ which is
    not present in this consolidated branch. These tests are skipped until
    the scoring logic is promoted to scripts/platform/.
    """

    def setUp(self):
        score_engine_path = REPO_ROOT / "projects" / "deploygtm-own" / "scripts" / "score_engine.py"
        if not score_engine_path.exists():
            self.skipTest("score_engine.py not present in this branch — pending platform promotion")
        self.tmpdir = Path(tempfile.mkdtemp(prefix="dgtm-score-profile-"))
        (self.tmpdir / "data").mkdir()
        (self.tmpdir / "outputs").mkdir()

        gen = _load("generate_outreach", REPO_ROOT / "projects" / "deploygtm-own" / "scripts" / "generate_outreach.py")
        gen.DATA_DIR = self.tmpdir / "data"
        gen.OUTPUTS_DIR = self.tmpdir / "outputs"
        sys.modules["generate_outreach"] = gen

        # derive_icp must be importable for score_engine
        self.derive = _load("derive_icp", SCRIPTS_DIR / "derive_icp.py")
        sys.modules["derive_icp"] = self.derive

        self.score = _load("t_score_with_profile", REPO_ROOT / "projects" / "deploygtm-own" / "scripts" / "score_engine.py")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        for mod in ["t_score_with_profile", "generate_outreach", "derive_icp"]:
            sys.modules.pop(mod, None)

    def test_custom_profile_signal_weight_used(self):
        account = {
            "company": "TestCo", "domain": "test.co", "icp_tier": 2,
            "fit_score": 5.0, "status": "monitor",
            "why_now_signal": {"type": "sbir_award", "date": "2026-04-15"},
        }

        # Default profile doesn't know "sbir_award" — should give weight 1
        default_score = self.score.compute_score(account)

        # Custom profile boosts sbir_award to weight 4
        custom_profile = {
            "signal_weights": {"sbir_award": 4},
            "signal_decay_days": {"default": 60},
            "status_deltas": {"monitor": 0},
            "sentiment_deltas": {},
            "tier_fit_fallback": {1: 7.0, 2: 4.5, 3: 2.0},
        }
        custom_score = self.score.compute_score(account, profile=custom_profile)

        self.assertGreater(custom_score, default_score)

    def test_custom_profile_decay_used(self):
        # Old signal — recency near 0 with default 60-day half-life
        account = {
            "company": "TestCo", "domain": "test.co", "icp_tier": 2,
            "fit_score": 5.0, "status": "monitor",
            "why_now_signal": {"type": "linkedin_pain_post", "date": "2026-04-01"},
        }

        # With short half-life (14 days), 27-day-old signal has minimal recency
        short_decay_profile = {
            "signal_weights": {"linkedin_pain_post": 4},
            "signal_decay_days": {"linkedin_pain_post": 14, "default": 60},
            "status_deltas": {"monitor": 0},
            "sentiment_deltas": {},
            "tier_fit_fallback": {1: 7.0, 2: 4.5, 3: 2.0},
        }
        # With long half-life (180 days), same signal still has high recency
        long_decay_profile = {
            "signal_weights": {"linkedin_pain_post": 4},
            "signal_decay_days": {"linkedin_pain_post": 180, "default": 60},
            "status_deltas": {"monitor": 0},
            "sentiment_deltas": {},
            "tier_fit_fallback": {1: 7.0, 2: 4.5, 3: 2.0},
        }

        short = self.score.compute_score(account, profile=short_decay_profile)
        long_ = self.score.compute_score(account, profile=long_decay_profile)

        self.assertGreater(long_, short)

    def test_no_profile_falls_back_to_defaults(self):
        # Should not crash when profile is None
        account = {
            "company": "TestCo", "domain": "test.co", "icp_tier": 1,
            "status": "monitor",
            "why_now_signal": {"type": "funding", "date": "2026-04-15"},
        }
        score = self.score.compute_score(account)
        self.assertGreater(score, 0)


if __name__ == "__main__":
    unittest.main()
