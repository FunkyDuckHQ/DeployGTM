"""
Offline tests for:
  - projects/deploygtm-own/scripts/research_accounts.py
  - projects/deploygtm-own/scripts/enrich_matrix.py

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


def _make_matrix(tmpdir: Path, accounts: list[dict]) -> Path:
    """Write a minimal accounts.json and return the data dir."""
    data_dir = tmpdir / "data"
    data_dir.mkdir(exist_ok=True)
    matrix = {
        "client_name": "test",
        "voice_notes": "Direct.",
        "accounts": accounts,
    }
    (data_dir / "test_accounts.json").write_text(json.dumps(matrix))
    return data_dir


def _base_account(**kwargs) -> dict:
    base = {
        "company": "TestCo",
        "domain": "testco.com",
        "icp_tier": 1,
        "status": "monitor",
        "why_now_signal": {"type": "funding", "date": "2026-03-01", "description": "Seed raise"},
    }
    base.update(kwargs)
    return base


# ─── research_accounts.py ────────────────────────────────────────────────────


class TestResearchAccounts(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="dgtm-research-"))
        (self.tmpdir / "data").mkdir()
        (self.tmpdir / "outputs").mkdir()

        self.gen = _load("generate_outreach", MATRIX_SCRIPTS_DIR / "generate_outreach.py")
        self.gen.DATA_DIR = self.tmpdir / "data"
        self.gen.OUTPUTS_DIR = self.tmpdir / "outputs"
        sys.modules["generate_outreach"] = self.gen

        self.score = _load("score_engine", MATRIX_SCRIPTS_DIR / "score_engine.py")
        sys.modules["score_engine"] = self.score

        self.research = _load("t_research", MATRIX_SCRIPTS_DIR / "research_accounts.py")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        for mod in ["t_research", "generate_outreach", "score_engine"]:
            sys.modules.pop(mod, None)

    def _account(self, **kwargs) -> dict:
        return _base_account(**kwargs)

    def test_fetch_web_snapshot_returns_string(self):
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = "<html><body><h1>TestCo</h1><p>We build SaaS.</p></body></html>"
            mock_get.return_value = mock_resp

            result = self.research._fetch_web_snapshot("testco.com", max_chars=500)
            self.assertIsInstance(result, str)
            self.assertIn("TestCo", result)

    def test_fetch_web_snapshot_handles_failure(self):
        with patch("requests.get", side_effect=Exception("timeout")):
            result = self.research._fetch_web_snapshot("testco.com")
            self.assertEqual(result, "")

    def test_research_account_dry_run_skips_claude(self):
        account = self._account()

        with patch.object(self.research, "_fetch_web_snapshot", return_value="fake web content"):
            mock_enrich = MagicMock(return_value={"name": "TestCo", "industry": "SaaS"})
            with patch.dict(sys.modules, {"apollo": MagicMock(enrich_company=mock_enrich)}):
                result = self.research.research_account(
                    account, client_context="", dry_run=True
                )
        # dry-run: no fit_score written, no Claude call
        self.assertEqual(result, {})
        self.assertNotIn("fit_score", account)

    def test_research_account_sets_fit_score(self):
        account = self._account()
        claude_response = {
            "fit_score": 8.5,
            "fit_dimensions": {
                "stage_fit": 2, "size_fit": 2, "tech_signals": 1,
                "gtm_maturity": 2, "buyer_type": 1
            },
            "pain_hypothesis": "Founder drowning in manual prospecting.",
            "fit_rationale": "Classic Seed SaaS. Good fit.",
            "company_profile": {
                "what_they_do": "Email platform",
                "stage": "seed",
                "employee_count": 15,
                "tech_stack_signals": ["Clay", "HubSpot"],
                "gtm_signal": "Hiring AE",
            },
            "confidence": "high",
        }

        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=json.dumps(claude_response))]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_msg

        with patch.object(self.research, "_fetch_web_snapshot", return_value=""):
            with patch.dict(sys.modules, {"apollo": MagicMock(enrich_company=MagicMock(return_value={}))}):
                with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                    with patch("anthropic.Anthropic", return_value=mock_client):
                        self.research.research_account(account, client_context="test ICP")

        self.assertEqual(account["fit_score"], 8.5)
        self.assertIn("pain_hypothesis", account)
        self.assertIn("company_profile", account)
        self.assertIn("researched_at", account)
        self.assertIn("current_score", account)

    def test_research_account_handles_bad_json(self):
        account = self._account()

        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="not json at all")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_msg

        with patch.object(self.research, "_fetch_web_snapshot", return_value=""):
            with patch.dict(sys.modules, {"apollo": MagicMock(enrich_company=MagicMock(return_value={}))}):
                with patch("anthropic.Anthropic", return_value=mock_client):
                    result = self.research.research_account(account, client_context="")

        self.assertEqual(result, {})
        self.assertNotIn("fit_score", account)

    def test_research_matrix_skips_already_researched(self):
        account = _base_account(researched_at="2026-04-01")
        _make_matrix(self.tmpdir, [account])

        with patch.object(self.research, "research_account") as mock_ra:
            done = self.research.research_matrix(
                "test", tiers=[1, 2], force=False, dry_run=True
            )
        self.assertEqual(done, [])
        mock_ra.assert_not_called()

    def test_research_matrix_force_reruns(self):
        account = _base_account(researched_at="2026-04-01")
        _make_matrix(self.tmpdir, [account])

        with patch.object(self.research, "research_account", return_value={}) as mock_ra:
            done = self.research.research_matrix(
                "test", tiers=[1, 2], force=True, dry_run=True, delay=0
            )
        self.assertEqual(done, ["TestCo"])
        mock_ra.assert_called_once()

    def test_research_matrix_tier_filter(self):
        accounts = [
            _base_account(company="Tier1Co", domain="tier1.co", icp_tier=1),
            _base_account(company="Tier3Co", domain="tier3.co", icp_tier=3),
        ]
        _make_matrix(self.tmpdir, accounts)

        called_with = []

        def fake_research(acc, ctx, **kw):
            called_with.append(acc["company"])
            return {}

        with patch.object(self.research, "research_account", side_effect=fake_research):
            self.research.research_matrix("test", tiers=[1], dry_run=True, delay=0)

        self.assertIn("Tier1Co", called_with)
        self.assertNotIn("Tier3Co", called_with)


# ─── enrich_matrix.py ────────────────────────────────────────────────────────


class TestEnrichMatrix(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="dgtm-enrich-"))
        (self.tmpdir / "data").mkdir()
        (self.tmpdir / "outputs").mkdir()

        self.gen = _load("generate_outreach2", MATRIX_SCRIPTS_DIR / "generate_outreach.py")
        self.gen.DATA_DIR = self.tmpdir / "data"
        self.gen.OUTPUTS_DIR = self.tmpdir / "outputs"
        sys.modules["generate_outreach"] = self.gen

        self.enrich = _load("t_enrich", MATRIX_SCRIPTS_DIR / "enrich_matrix.py")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        for mod in ["t_enrich", "generate_outreach2", "generate_outreach"]:
            sys.modules.pop(mod, None)

    def test_titles_for_account_founder_persona(self):
        account = _base_account(target_persona="founder_seller")
        titles = self.enrich._titles_for_account(account)
        self.assertIn("CEO", titles)
        self.assertNotIn("RevOps", titles)

    def test_titles_for_account_revops_persona(self):
        account = _base_account(target_persona="revops_growth")
        titles = self.enrich._titles_for_account(account)
        self.assertIn("RevOps", titles)
        self.assertNotIn("CEO", titles)

    def test_titles_for_account_default_when_no_persona(self):
        account = _base_account()
        titles = self.enrich._titles_for_account(account)
        self.assertIn("CEO", titles)
        self.assertIn("VP Sales", titles)
        self.assertIn("RevOps", titles)

    def test_enrich_account_dry_run_skips_profiling(self):
        account = _base_account()
        mock_contacts = [
            {"name": "Jane Smith", "title": "CEO", "email": "jane@testco.com",
             "email_status": "verified", "linkedin_url": "", "phone": "",
             "confidence": "high", "source": "apollo"},
        ]

        with patch.dict(sys.modules, {"apollo": MagicMock(find_contacts=MagicMock(return_value=mock_contacts))}):
            result = self.enrich.enrich_account(account, client_context="", dry_run=True)

        # dry-run: contacts returned from Apollo but not profiled
        self.assertEqual(result, mock_contacts)
        self.assertNotIn("contacts", account)

    def test_enrich_account_stores_contacts(self):
        account = _base_account()
        mock_contacts = [
            {"name": "Jane Smith", "title": "CEO", "email": "jane@testco.com",
             "email_status": "verified", "linkedin_url": "", "phone": "",
             "confidence": "high", "source": "apollo"},
        ]
        profile_response = {
            "pain_hypothesis": "Jane spends 3hrs/day on manual prospecting.",
            "conversation_hooks": ["Hook 1", "Hook 2"],
            "seniority": "executive",
            "influence_level": "decision_maker",
            "likely_objections": ["Too busy", "Budget timing"],
            "outreach_tone": "direct",
            "confidence": "high",
        }

        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=json.dumps(profile_response))]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_msg

        with patch.dict(sys.modules, {"apollo": MagicMock(find_contacts=MagicMock(return_value=mock_contacts))}):
            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                with patch("anthropic.Anthropic", return_value=mock_client):
                    self.enrich.enrich_account(account, client_context="test ICP", contact_delay=0)

        self.assertIn("contacts", account)
        self.assertEqual(len(account["contacts"]), 1)
        self.assertIn("profile", account["contacts"][0])
        self.assertIn("contacts_enriched_at", account)
        self.assertEqual(account["contacts"][0]["profile"]["influence_level"], "decision_maker")

    def test_enrich_account_handles_no_contacts(self):
        account = _base_account()
        # Apollo returns the fallback stub (empty email)
        apollo_miss = [{"name": "", "title": "Unknown", "email": "",
                        "email_status": "not_found", "linkedin_url": "",
                        "phone": "", "confidence": "low",
                        "source": "apollo_miss — manual LinkedIn lookup needed"}]

        with patch.dict(sys.modules, {"apollo": MagicMock(find_contacts=MagicMock(return_value=apollo_miss))}):
            result = self.enrich.enrich_account(account, client_context="", contact_delay=0)

        # Should not crash; stub returned, no profiling attempted (no email)
        self.assertEqual(len(result), 1)
        self.assertNotIn("profile", result[0])

    def test_enrich_matrix_skips_already_enriched(self):
        account = _base_account(contacts_enriched_at="2026-04-01")
        _make_matrix(self.tmpdir, [account])

        with patch.object(self.enrich, "enrich_account") as mock_ea:
            done = self.enrich.enrich_matrix("test", tiers=[1, 2], dry_run=True)

        self.assertEqual(done, [])
        mock_ea.assert_not_called()

    def test_enrich_matrix_force_reruns(self):
        account = _base_account(contacts_enriched_at="2026-04-01")
        _make_matrix(self.tmpdir, [account])

        with patch.object(self.enrich, "enrich_account", return_value=[]) as mock_ea:
            done = self.enrich.enrich_matrix("test", tiers=[1, 2], force=True, dry_run=True, delay=0)

        self.assertEqual(done, ["TestCo"])
        mock_ea.assert_called_once()

    def test_enrich_matrix_tier_filter(self):
        accounts = [
            _base_account(company="T1Co", domain="t1.co", icp_tier=1),
            _base_account(company="T3Co", domain="t3.co", icp_tier=3),
        ]
        _make_matrix(self.tmpdir, accounts)

        called_with = []

        def fake_enrich(acc, ctx, **kw):
            called_with.append(acc["company"])
            return []

        with patch.object(self.enrich, "enrich_account", side_effect=fake_enrich):
            self.enrich.enrich_matrix("test", tiers=[1], dry_run=True, delay=0)

        self.assertIn("T1Co", called_with)
        self.assertNotIn("T3Co", called_with)


if __name__ == "__main__":
    unittest.main()
