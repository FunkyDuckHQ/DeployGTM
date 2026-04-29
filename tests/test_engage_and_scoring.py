"""
Offline tests for:
  - scripts/crm_adapter.py      (routing, CsvAdapter, NullAdapter, stubs)
  - scripts/engage.py           (context building logic, guard conditions)
  - score_engine.py             (compute_score, apply_score, thresholds, decay)

No API keys, no network calls required.
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
MATRIX_SCRIPTS_DIR = REPO_ROOT / "projects" / "deploygtm-own" / "scripts"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── crm_adapter.py ───────────────────────────────────────────────────────────


class TestCrmAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = _load("t_crm_adapter", SCRIPTS_DIR / "crm_adapter.py")

    def tearDown(self):
        sys.modules.pop("t_crm_adapter", None)

    def test_get_adapter_hubspot_returns_hubspot_class(self):
        a = self.adapter.get_adapter("hubspot")
        self.assertIsInstance(a, self.adapter.HubSpotAdapter)

    def test_get_adapter_csv_returns_csv_class(self):
        a = self.adapter.get_adapter("csv")
        self.assertIsInstance(a, self.adapter.CsvAdapter)

    def test_get_adapter_none_returns_null(self):
        a = self.adapter.get_adapter("none")
        self.assertIsInstance(a, self.adapter.NullAdapter)

    def test_get_adapter_unknown_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.adapter.get_adapter("mycrm_doesnt_exist")
        self.assertIn("mycrm_doesnt_exist", str(ctx.exception))

    def test_null_adapter_returns_none_for_all_ops(self):
        a = self.adapter.NullAdapter()
        self.assertIsNone(a.upsert_company({"company": "X", "domain": "x.com"}))
        self.assertIsNone(a.create_deal("X", "outreach_sent"))
        self.assertIsNone(a.create_note("id123", "body"))
        self.assertIsNone(a.create_task("subj", "body"))

    def test_salesforce_stub_raises(self):
        a = self.adapter.SalesforceAdapter()
        with self.assertRaises(NotImplementedError):
            a.upsert_company({"company": "X"})

    def test_attio_stub_raises(self):
        a = self.adapter.AttioAdapter()
        with self.assertRaises(NotImplementedError):
            a.create_deal("X", "stage")

    def test_csv_adapter_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a = self.adapter.CsvAdapter(output_dir=Path(tmpdir))
            result = a.upsert_company({"company": "Acme", "domain": "acme.com"}, dry_run=True)
            self.assertIsNotNone(result)
            # No CSV file should have been created
            self.assertEqual(list(Path(tmpdir).glob("*.csv")), [])

    def test_csv_adapter_writes_company_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a = self.adapter.CsvAdapter(output_dir=Path(tmpdir))
            a.upsert_company({"company": "Acme", "domain": "acme.com"})
            csv_path = Path(tmpdir) / "crm_export_companies.csv"
            self.assertTrue(csv_path.exists())
            content = csv_path.read_text()
            self.assertIn("acme.com", content)

    def test_csv_adapter_writes_deal_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a = self.adapter.CsvAdapter(output_dir=Path(tmpdir))
            a.create_deal("Acme", "outreach_sent")
            csv_path = Path(tmpdir) / "crm_export_deals.csv"
            self.assertTrue(csv_path.exists())
            self.assertIn("outreach_sent", csv_path.read_text())

    def test_csv_adapter_writes_task_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a = self.adapter.CsvAdapter(output_dir=Path(tmpdir))
            a.create_task("Follow-up #1: Acme", "Subject: Hi\n\nBody here")
            csv_path = Path(tmpdir) / "crm_export_tasks.csv"
            self.assertTrue(csv_path.exists())

    def test_get_adapter_for_client_reads_crm_from_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            client_dir = Path(tmpdir) / "my-client"
            client_dir.mkdir()
            (client_dir / "context.md").write_text("# Context\ncrm: csv\n")
            adapter = self.adapter.get_adapter_for_client("my-client", projects_dir=Path(tmpdir))
            self.assertIsInstance(adapter, self.adapter.CsvAdapter)

    def test_get_adapter_for_client_defaults_to_hubspot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            client_dir = Path(tmpdir) / "no-crm-client"
            client_dir.mkdir()
            (client_dir / "context.md").write_text("# Context\nNo CRM mentioned.\n")
            adapter = self.adapter.get_adapter_for_client("no-crm-client", projects_dir=Path(tmpdir))
            self.assertIsInstance(adapter, self.adapter.HubSpotAdapter)

    def test_get_adapter_for_client_missing_context_defaults_to_hubspot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            client_dir = Path(tmpdir) / "new-client"
            client_dir.mkdir()
            # No context.md
            adapter = self.adapter.get_adapter_for_client("new-client", projects_dir=Path(tmpdir))
            self.assertIsInstance(adapter, self.adapter.HubSpotAdapter)


# ─── engage.py ────────────────────────────────────────────────────────────────


class TestEngage(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="dgtm-engage-"))
        sys.modules.setdefault("anthropic", MagicMock())
        self.engage = _load("t_engage", SCRIPTS_DIR / "engage.py")
        self.engage.PROJECTS_DIR = self.tmpdir

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        sys.modules.pop("t_engage", None)

    def test_raises_if_context_exists_without_force(self):
        import click
        client_dir = self.tmpdir / "existing-client"
        client_dir.mkdir()
        (client_dir / "context.md").write_text("# Existing context")

        with self.assertRaises(click.ClickException) as ctx:
            self.engage.run_engage(
                client="existing-client",
                domain="example.com",
                objective="Build outbound",
            )
        self.assertIn("existing-client", str(ctx.exception))

    def test_creates_client_dir_if_missing(self):
        # Mock Claude API call
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="# Test Context\ncrm: none\n")]
        mock_ai = MagicMock()
        mock_ai.messages.create.return_value = mock_response

        with patch.object(self.engage, "_build_context", return_value="# Context\ncrm: none\n"), \
             patch.object(self.engage, "_try_drive_sync", return_value="Drive sync skipped"), \
             patch.object(self.engage, "_scaffold_matrix", return_value=None):
            result = self.engage.run_engage(
                client="new-client-xyz",
                domain="xyz.com",
                objective="Build outbound for fintech",
            )

        self.assertTrue((self.tmpdir / "new-client-xyz").exists())
        self.assertTrue(result.exists())

    def test_force_overwrites_existing_context(self):
        client_dir = self.tmpdir / "force-client"
        client_dir.mkdir()
        (client_dir / "context.md").write_text("# Old context")

        with patch.object(self.engage, "_build_context", return_value="# New context\ncrm: none\n"), \
             patch.object(self.engage, "_try_drive_sync", return_value="skipped"), \
             patch.object(self.engage, "_scaffold_matrix", return_value=None):
            self.engage.run_engage(
                client="force-client",
                domain="force.com",
                objective="Rebuild",
                force=True,
            )

        content = (client_dir / "context.md").read_text()
        self.assertIn("New context", content)

    def test_website_fetch_returns_string(self):
        """_fetch_website returns a string (may be empty if requests unavailable)."""
        result = self.engage._fetch_website("example.com", timeout=1)
        self.assertIsInstance(result, str)

    def test_try_drive_sync_handles_missing_env_gracefully(self):
        import os
        os.environ.pop("GDRIVE_INTAKE_FOLDER_ID", None)
        result = self.engage._try_drive_sync("any-client")
        self.assertIsInstance(result, str)
        self.assertIn("skipped", result.lower())


# ─── score_engine.py ──────────────────────────────────────────────────────────


class TestScoreEngine(unittest.TestCase):
    """Tests for score_engine.py — skipped until scoring is promoted to scripts/platform/."""

    def setUp(self):
        if not (MATRIX_SCRIPTS_DIR / "score_engine.py").exists():
            self.skipTest("score_engine.py not present — pending platform promotion")
        self.tmpdir = Path(tempfile.mkdtemp(prefix="dgtm-score-"))
        (self.tmpdir / "data").mkdir()
        (self.tmpdir / "outputs").mkdir()

        gen = _load("generate_outreach", MATRIX_SCRIPTS_DIR / "generate_outreach.py")
        gen.DATA_DIR = self.tmpdir / "data"
        gen.OUTPUTS_DIR = self.tmpdir / "outputs"
        sys.modules["generate_outreach"] = gen

        self.score = _load("t_score_engine", MATRIX_SCRIPTS_DIR / "score_engine.py")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        sys.modules.pop("t_score_engine", None)
        sys.modules.pop("generate_outreach", None)

    def _account(self, tier=1, signal="funding", signal_date="2026-04-01", status="monitor"):
        return {
            "company": "TestCo",
            "domain": "test.co",
            "icp_tier": tier,
            "why_now_signal": {"type": signal, "date": signal_date, "description": "test"},
            "status": status,
        }

    def test_tier1_funding_higher_than_tier3_manual(self):
        high = self.score.compute_score(self._account(tier=1, signal="funding"))
        low = self.score.compute_score(self._account(tier=3, signal="manual"))
        self.assertGreater(high, low)

    def test_met_status_raises_score(self):
        base = self.score.compute_score(self._account(status="monitor"))
        met = self.score.compute_score(self._account(status="meeting_booked"))
        self.assertGreater(met, base)

    def test_no_fit_status_decreases_score(self):
        base = self.score.compute_score(self._account(status="monitor"))
        bad = self.score.compute_score(self._account(status="no_fit"))
        self.assertLess(bad, base)

    def test_old_signal_penalized(self):
        fresh = self.score.compute_score(self._account(signal_date="2026-04-01"))
        stale = self.score.compute_score(self._account(signal_date="2024-01-01"))
        self.assertGreater(fresh, stale)

    def test_score_never_negative(self):
        bad_account = self._account(tier=3, signal="manual", signal_date="2020-01-01", status="no_fit")
        score = self.score.compute_score(bad_account)
        self.assertGreaterEqual(score, 0)

    def test_apply_score_stores_current_score(self):
        account = self._account()
        self.score.apply_score(account)
        self.assertIn("current_score", account)
        self.assertIsInstance(account["current_score"], float)

    def test_apply_score_appends_history(self):
        account = self._account()
        self.score.apply_score(account, reason="test")
        self.score.apply_score(account, reason="test2")
        self.assertEqual(len(account["score_history"]), 2)

    def test_apply_score_records_delta(self):
        account = self._account()
        self.score.apply_score(account, reason="first")
        # Manually change score to simulate change
        account["current_score"] = 999.0
        self.score.apply_score(account, reason="second")
        last = account["score_history"][-1]
        self.assertIn("delta", last)

    def test_record_event_sentiment_positive_raises_score(self):
        account = self._account(tier=2, signal="funding", status="outreach_sent")
        self.score.apply_score(account, reason="baseline")
        before = account["current_score"]
        self.score.record_event(account, "sentiment", "positive", "replied positively")
        after = account["current_score"]
        self.assertGreater(after, before)

    def test_threshold_labels(self):
        self.assertEqual(self.score.threshold_label(13), "HOT")
        self.assertEqual(self.score.threshold_label(9), "ENGAGE")
        self.assertEqual(self.score.threshold_label(5), "WATCH")
        self.assertEqual(self.score.threshold_label(2), "COLD")

    def test_hot_threshold_constant(self):
        self.assertEqual(self.score.HOT_THRESHOLD, 12)

    def test_engagement_threshold_constant(self):
        self.assertEqual(self.score.ENGAGEMENT_THRESHOLD, 8)

    def test_set_fit_score_updates_account(self):
        account = self._account(tier=3)
        # Before: no fit_score, uses fallback
        before = self.score.compute_score(account)
        # After: explicit fit_score raises it
        self.score.set_fit_score(account, 9.0, rationale="manual test")
        self.assertEqual(account["fit_score"], 9.0)
        after = account["current_score"]
        self.assertGreater(after, before)

    def test_fit_score_fallback_used_when_not_set(self):
        account = self._account(tier=1)
        # No fit_score set — should use TIER_FIT_FALLBACK[1] = 7.0
        score = self.score.compute_score(account)
        # Score should be >= 7.0 (fit_score floor for tier 1)
        self.assertGreaterEqual(score, 7.0)

    def test_stale_signal_no_bonus(self):
        # A very old signal should contribute ~0 bonus (recency → 0)
        account = self._account(tier=1, signal="funding", signal_date="2020-01-01")
        score = self.score.compute_score(account)
        # Score should equal approximately fit_score only (7.0 for tier 1)
        self.assertAlmostEqual(score, 7.0, delta=0.5)

    def test_get_prioritized_sorts_descending(self):
        # Seed a matrix with two accounts
        matrix = {
            "client_name": "test",
            "voice_notes": "Direct.",
            "accounts": [
                {**self._account(tier=3, signal="manual"), "company": "LowCo", "domain": "low.co"},
                {**self._account(tier=1, signal="funding"), "company": "HighCo", "domain": "high.co"},
            ],
        }
        import generate_outreach as gen
        matrix_path = gen.DATA_DIR / "test_accounts.json"
        matrix_path.write_text(json.dumps(matrix))

        results = self.score.get_prioritized("test")
        self.assertEqual(results[0]["company"], "HighCo")
        self.assertEqual(results[-1]["company"], "LowCo")


if __name__ == "__main__":
    unittest.main()
