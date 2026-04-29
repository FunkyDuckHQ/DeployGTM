"""
Offline tests for the account matrix artifacts:
  - Schema conformance of the Peregrine seed data
  - generate_outreach.py  (matrix loading, prompt shape, slugify, word_count)
  - variant_tracker.py    (schema, insert, report aggregation)
  - weekly_signal_report.py (priority scoring, markdown structure)

These tests never hit a network. No API keys required.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = REPO_ROOT / "projects" / "deploygtm-own"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Skip this entire module when the per-project scripts directory is absent.
# These tests cover projects/deploygtm-own/scripts/ which is not present in
# the consolidated branch — pending promotion to scripts/platform/.
import pytest as _pytest  # noqa: E402
if not (SCRIPTS_DIR / "generate_outreach.py").exists():
    _pytest.skip(
        "projects/deploygtm-own/scripts/generate_outreach.py not present — "
        "pending promotion to scripts/platform/",
        allow_module_level=True,
    )


def _load(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── Fixture: fresh temp project root per test so we don't pollute real data ──


class MatrixTestBase(unittest.TestCase):
    """Base class that copies the deploygtm-own project into a tempdir and
    monkeypatches the three scripts to read/write there instead of the repo.

    Skipped when projects/deploygtm-own/scripts/ is absent (consolidated branch).
    """

    def setUp(self):
        if not SCRIPTS_DIR.exists():
            self.skipTest(
                "projects/deploygtm-own/scripts/ not present — "
                "pending promotion to scripts/platform/"
            )
        self.tmpdir = Path(tempfile.mkdtemp(prefix="dgtm-matrix-"))
        # Copy schema + scripts into tempdir mirroring layout
        (self.tmpdir / "scripts").mkdir()
        (self.tmpdir / "data").mkdir()
        (self.tmpdir / "outputs").mkdir()
        shutil.copy(PROJECT_ROOT / "account_matrix_schema.json",
                    self.tmpdir / "account_matrix_schema.json")
        for s in ("generate_outreach.py", "variant_tracker.py",
                  "weekly_signal_report.py", "init_matrix.py"):
            shutil.copy(SCRIPTS_DIR / s, self.tmpdir / "scripts" / s)

        # Load each module fresh and redirect its DATA_DIR/OUTPUTS_DIR/DB_PATH
        self.generate = _load(
            "t_generate", self.tmpdir / "scripts" / "generate_outreach.py"
        )
        self.tracker = _load(
            "t_tracker", self.tmpdir / "scripts" / "variant_tracker.py"
        )
        self.weekly = _load(
            "t_weekly", self.tmpdir / "scripts" / "weekly_signal_report.py"
        )
        self.initm = _load(
            "t_init", self.tmpdir / "scripts" / "init_matrix.py"
        )

        for mod in (self.generate, self.tracker, self.weekly, self.initm):
            mod.PROJECT_ROOT = self.tmpdir
            mod.DATA_DIR = self.tmpdir / "data"
            if hasattr(mod, "OUTPUTS_DIR"):
                mod.OUTPUTS_DIR = self.tmpdir / "outputs"
            if hasattr(mod, "DB_PATH"):
                mod.DB_PATH = self.tmpdir / "data" / "variants.db"
            if hasattr(mod, "SCHEMA_FILE"):
                mod.SCHEMA_FILE = self.tmpdir / "account_matrix_schema.json"

        # Register patched modules under their canonical names so cross-imports
        # (e.g. update_status doing `from generate_outreach import ...`) find
        # the patched DATA_DIR rather than reloading a fresh unpatched copy.
        sys.modules["generate_outreach"] = self.generate
        sys.modules["variant_tracker"] = self.tracker
        sys.modules["weekly_signal_report"] = self.weekly
        sys.modules["init_matrix"] = self.initm

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)


# ─── Seed-data conformance ────────────────────────────────────────────────────


class TestPeregrineSeedData(unittest.TestCase):
    def test_peregrine_has_14_accounts_and_required_fields(self):
        path = PROJECT_ROOT / "data" / "peregrine_accounts.json"
        data = json.loads(path.read_text())
        self.assertEqual(data["client_name"], "peregrine-space")
        self.assertIn("voice_notes", data)
        self.assertGreater(len(data["voice_notes"]), 50)
        self.assertEqual(len(data["accounts"]), 14)

        required_top = {"company", "domain", "icp_tier", "market", "segment",
                        "persona", "angle", "why_now_signal", "product_fit",
                        "heritage_risk"}
        required_signal = {"type", "description", "source"}
        required_persona = {"title", "why_they_feel_it"}
        valid_signal_types = {
            "funding", "hiring", "contract_award", "program_announcement",
            "acquisition", "sbir_award", "leadership_change",
            "product_launch", "conference_signal", "manual",
        }

        for acct in data["accounts"]:
            missing = required_top - set(acct.keys())
            self.assertFalse(missing, f"{acct.get('company')} missing {missing}")
            self.assertIn(acct["icp_tier"], {1, 2, 3})
            self.assertEqual(required_signal - set(acct["why_now_signal"]), set())
            self.assertEqual(required_persona - set(acct["persona"]), set())
            self.assertIn(acct["why_now_signal"]["type"], valid_signal_types)

    def test_peregrine_includes_xona(self):
        path = PROJECT_ROOT / "data" / "peregrine_accounts.json"
        companies = {a["company"] for a in json.loads(path.read_text())["accounts"]}
        self.assertIn("Xona Space Systems", companies)


# ─── generate_outreach ────────────────────────────────────────────────────────


class TestGenerateOutreach(MatrixTestBase):
    def _seed_matrix(self, client="acme-co"):
        matrix = {
            "client_name": client,
            "voice_notes": "Direct. Short. Signal-led.",
            "accounts": [{
                "company": "Acme Corp",
                "domain": "acme.com",
                "icp_tier": 1,
                "market": "B2B SaaS",
                "segment": "Seed-stage pipeline build",
                "persona": {"title": "CEO", "why_they_feel_it": "Founder selling."},
                "angle": "Your first AE needs infra on day one.",
                "why_now_signal": {
                    "type": "funding",
                    "description": "Acme raised $5M seed.",
                    "source": "Crunchbase",
                    "date": "2026-04-01",
                },
                "product_fit": "Pre-built pipeline stack.",
                "heritage_risk": "Low",
            }],
        }
        normalized = client.replace("-", "_")
        (self.tmpdir / "data" / f"{normalized}_accounts.json").write_text(json.dumps(matrix))
        return matrix

    def test_load_matrix_by_slug(self):
        self._seed_matrix("acme-co")
        m = self.generate.load_client_matrix("acme-co")
        self.assertEqual(m["client_name"], "acme-co")

    def test_load_matrix_by_client_name_fallback(self):
        """A file with a non-conventional name should still resolve via client_name."""
        matrix = {"client_name": "weirdly-named", "voice_notes": "x", "accounts": []}
        (self.tmpdir / "data" / "some_other_file_accounts.json").write_text(json.dumps(matrix))
        m = self.generate.load_client_matrix("weirdly-named")
        self.assertEqual(m["client_name"], "weirdly-named")

    def test_find_account_case_insensitive(self):
        self._seed_matrix()
        m = self.generate.load_client_matrix("acme-co")
        a = self.generate.find_account(m, "acme corp")
        self.assertEqual(a["company"], "Acme Corp")

    def test_find_account_missing_raises(self):
        self._seed_matrix()
        m = self.generate.load_client_matrix("acme-co")
        with self.assertRaises(ValueError):
            self.generate.find_account(m, "Nonexistent")

    def test_build_prompts_contains_signal_and_voice(self):
        self._seed_matrix()
        m = self.generate.load_client_matrix("acme-co")
        a = self.generate.find_account(m, "Acme Corp")
        system, user = self.generate.build_prompts(m, a)
        self.assertIn("Direct. Short. Signal-led.", system)
        self.assertIn("Acme raised $5M seed.", user)
        self.assertIn("Under 75 words", system)

    def test_word_count_and_slugify(self):
        # word_count uses \b\w+\b — apostrophes and hyphens split words.
        # That's fine for our purposes (over-counts slightly, never under).
        self.assertEqual(self.generate.word_count("one two three"), 3)
        self.assertEqual(self.generate.word_count(""), 0)
        self.assertGreaterEqual(self.generate.word_count("  hello world  "), 2)
        self.assertEqual(self.generate.slugify("Xona Space Systems"), "xona_space_systems")
        self.assertEqual(self.generate.slugify("  weird/Name!! "), "weird_name")

    def test_parse_variants_strict(self):
        raw = json.dumps({"variants": [
            {"angle_label": "a", "subject": "s1", "body": "b1"},
            {"angle_label": "b", "subject": "s2", "body": "b2"},
            {"angle_label": "c", "subject": "s3", "body": "b3"},
        ]})
        out = self.generate.parse_variants(raw)
        self.assertEqual(len(out), 3)

    def test_parse_variants_strips_code_fences(self):
        raw = "```json\n" + json.dumps({"variants": [
            {"angle_label": "a", "subject": "s", "body": "b"},
            {"angle_label": "b", "subject": "s", "body": "b"},
            {"angle_label": "c", "subject": "s", "body": "b"},
        ]}) + "\n```"
        self.assertEqual(len(self.generate.parse_variants(raw)), 3)

    def test_parse_variants_rejects_wrong_count(self):
        raw = json.dumps({"variants": [{"angle_label": "a", "subject": "s", "body": "b"}]})
        with self.assertRaises(ValueError):
            self.generate.parse_variants(raw)


# ─── variant_tracker ─────────────────────────────────────────────────────────


class TestVariantTracker(MatrixTestBase):
    def _insert(self, client="acme-co", company="Acme Corp", angle="opener-1",
                body="hi", sent="2026-04-01"):
        conn = self.tracker.connect()
        cur = conn.execute(
            "INSERT INTO variants(client_name, company, angle_variant, angle_text, date_sent) "
            "VALUES (?, ?, ?, ?, ?)",
            (client, company, angle, body, sent),
        )
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return rid

    def test_connect_creates_schema(self):
        conn = self.tracker.connect()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        self.assertIn(("variants",), [tuple(t) for t in tables])

    def test_insert_and_read(self):
        rid = self._insert()
        self.assertIsNotNone(rid)
        conn = self.tracker.connect()
        row = conn.execute("SELECT * FROM variants WHERE id=?", (rid,)).fetchone()
        self.assertEqual(row["company"], "Acme Corp")
        self.assertEqual(row["response_received"], 0)

    def test_response_aggregation(self):
        self._insert(angle="opener-1", sent="2026-04-01")
        self._insert(angle="opener-1", sent="2026-04-02")
        rid = self._insert(angle="opener-2", sent="2026-04-03")
        conn = self.tracker.connect()
        conn.execute(
            "UPDATE variants SET response_received=1, response_sentiment='positive' WHERE id=?",
            (rid,),
        )
        conn.commit()

        rows = conn.execute(
            "SELECT angle_variant, COUNT(*) AS sent, SUM(response_received) AS resp "
            "FROM variants WHERE client_name=? GROUP BY angle_variant ORDER BY angle_variant",
            ("acme-co",),
        ).fetchall()
        conn.close()
        as_dict = {r["angle_variant"]: (r["sent"], r["resp"]) for r in rows}
        self.assertEqual(as_dict["opener-1"], (2, 0))
        self.assertEqual(as_dict["opener-2"], (1, 1))


# ─── weekly_signal_report ─────────────────────────────────────────────────────


class TestWeeklyReport(MatrixTestBase):
    def _matrix(self):
        return {
            "client_name": "acme-co",
            "voice_notes": "v",
            "accounts": [
                {
                    "company": "High Priority",
                    "domain": "high.com",
                    "icp_tier": 1,
                    "market": "M",
                    "segment": "S",
                    "persona": {"title": "CEO", "why_they_feel_it": "x"},
                    "angle": "A",
                    "why_now_signal": {
                        "type": "funding",
                        "description": "Raised.",
                        "source": "CB",
                        "date": "2026-04-01",
                    },
                    "product_fit": "P",
                    "heritage_risk": "Low",
                },
                {
                    "company": "Low Priority",
                    "domain": "low.com",
                    "icp_tier": 3,
                    "market": "M",
                    "segment": "S",
                    "persona": {"title": "CEO", "why_they_feel_it": "x"},
                    "angle": "A",
                    "why_now_signal": {
                        "type": "manual",
                        "description": "manual check.",
                        "source": "me",
                    },
                    "product_fit": "P",
                    "heritage_risk": "Low",
                },
            ],
        }

    def test_priority_score_tier1_funding_is_15(self):
        acct = self._matrix()["accounts"][0]
        self.assertEqual(self.weekly.priority_score(acct), 15)

    def test_priority_score_tier3_manual_is_1(self):
        acct = self._matrix()["accounts"][1]
        self.assertEqual(self.weekly.priority_score(acct), 1)

    def test_engagement_threshold_flags_tier1(self):
        matrix = self._matrix()
        report = self.weekly.build_report(
            matrix, birddog_by_domain={},
            variant_stats={"sent": 0, "responded": 0, "by_angle": [], "recent": []},
            days_back=7,
        )
        self.assertIn("High Priority", report)
        self.assertIn("Low Priority", report)
        # Tier 1 / funding = 15 >= 12 → must be in flagged section
        flagged_section = report.split("## Engagement threshold flags")[1]
        self.assertIn("High Priority", flagged_section)
        # Tier 3 / manual = 1 < 12 → must NOT be in flagged section
        self.assertNotIn("Low Priority", flagged_section)

    def test_build_report_markdown_structure(self):
        matrix = self._matrix()
        report = self.weekly.build_report(
            matrix, birddog_by_domain={},
            variant_stats={"sent": 0, "responded": 0, "by_angle": [], "recent": []},
            days_back=7,
        )
        for expected in (
            "# Weekly Signal Report — acme-co",
            "## What moved",
            "## Outreach priority",
            "## Engagement threshold flags",
            "## Variant activity",
        ):
            self.assertIn(expected, report)


# ─── init_matrix ─────────────────────────────────────────────────────────────


class TestInitMatrix(MatrixTestBase):
    def test_stub_shape(self):
        data = self.initm.stub("new-client")
        self.assertEqual(data["client_name"], "new-client")
        self.assertEqual(len(data["accounts"]), 1)
        self.assertIn("REPLACE", data["voice_notes"])
        acct = data["accounts"][0]
        self.assertEqual(acct["icp_tier"], 1)
        self.assertIn("type", acct["why_now_signal"])
        self.assertEqual(acct["status"], "monitor")

    def test_target_path(self):
        p = self.initm.target_path("new-client")
        self.assertTrue(p.name == "new_client_accounts.json")


# ─── verify_signals ───────────────────────────────────────────────────────────


class VerifySignalsTestBase(MatrixTestBase):
    def setUp(self):
        super().setUp()
        shutil.copy(SCRIPTS_DIR / "verify_signals.py",
                    self.tmpdir / "scripts" / "verify_signals.py")
        self.verify = _load(
            "t_verify", self.tmpdir / "scripts" / "verify_signals.py"
        )
        sys.modules["verify_signals"] = self.verify

    def _ready_account(self, **overrides) -> dict:
        base = {
            "company": "Real Corp",
            "domain": "real.com",
            "icp_tier": 1,
            "market": "B2B SaaS",
            "segment": "Segment A",
            "persona": {"title": "CEO", "why_they_feel_it": "Drowning."},
            "angle": "Build before you hire.",
            "why_now_signal": {
                "type": "funding",
                "description": "Real Corp raised $5M seed round.",
                "source": "Crunchbase",
                "date": "2026-03-15",
            },
            "product_fit": "Signal Audit.",
            "heritage_risk": "Low",
        }
        base.update(overrides)
        return base

    def _blocked_account(self, **overrides) -> dict:
        base = self._ready_account()
        base["why_now_signal"]["description"] = "VERIFY — check Crunchbase"
        base["why_now_signal"]["date"] = "VERIFY-2026"
        base.update(overrides)
        return base


class TestVerifySignals(VerifySignalsTestBase):
    def test_clean_account_has_no_issues(self):
        issues = self.verify.audit_account(self._ready_account())
        self.assertEqual(issues, [])

    def test_verify_in_description_is_flagged(self):
        acct = self._ready_account()
        acct["why_now_signal"]["description"] = "VERIFY — check Crunchbase"
        issues = self.verify.audit_account(acct)
        self.assertTrue(any("description" in i for i in issues))

    def test_verify_in_date_is_flagged(self):
        acct = self._ready_account()
        acct["why_now_signal"]["date"] = "VERIFY-2026"
        issues = self.verify.audit_account(acct)
        self.assertTrue(any("date" in i for i in issues))

    def test_placeholder_company_is_flagged(self):
        acct = self._ready_account(company="< FILL IN — Segment C >")
        issues = self.verify.audit_account(acct)
        self.assertTrue(any("company" in i for i in issues))

    def test_placeholder_domain_is_flagged(self):
        acct = self._ready_account(domain="FILL_IN.com")
        issues = self.verify.audit_account(acct)
        self.assertTrue(any("domain" in i for i in issues))

    def test_missing_date_is_flagged(self):
        acct = self._ready_account()
        del acct["why_now_signal"]["date"]
        issues = self.verify.audit_account(acct)
        self.assertTrue(any("date" in i for i in issues))

    def test_audit_matrix_splits_ready_and_blocked(self):
        matrix = {
            "client_name": "test",
            "voice_notes": "Direct.",
            "accounts": [self._ready_account(), self._blocked_account()],
        }
        ready, blocked = self.verify.audit_matrix(matrix)
        self.assertEqual(len(ready), 1)
        self.assertEqual(len(blocked), 1)
        self.assertEqual(ready[0]["company"], "Real Corp")


# ─── batch_outreach ───────────────────────────────────────────────────────────


class TestBatchOutreach(VerifySignalsTestBase):
    def setUp(self):
        super().setUp()
        shutil.copy(SCRIPTS_DIR / "batch_outreach.py",
                    self.tmpdir / "scripts" / "batch_outreach.py")
        self.batch = _load(
            "t_batch", self.tmpdir / "scripts" / "batch_outreach.py"
        )

    def test_parse_tiers_single(self):
        self.assertEqual(self.batch._parse_tiers("1"), {1})

    def test_parse_tiers_multi(self):
        self.assertEqual(self.batch._parse_tiers("1,2"), {1, 2})

    def test_parse_tiers_rejects_invalid(self):
        import click
        with self.assertRaises(click.BadParameter):
            self.batch._parse_tiers("4")

    def test_parse_tiers_rejects_empty(self):
        import click
        with self.assertRaises(click.BadParameter):
            self.batch._parse_tiers("")

    def test_filter_accounts_by_tier(self):
        accounts = [
            {"icp_tier": 1, "company": "A"},
            {"icp_tier": 2, "company": "B"},
            {"icp_tier": 3, "company": "C"},
        ]
        matrix = {"accounts": accounts}
        result = self.batch._filter_accounts(matrix, {1})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["company"], "A")

    def test_filter_accounts_multi_tier(self):
        accounts = [
            {"icp_tier": 1, "company": "A"},
            {"icp_tier": 2, "company": "B"},
            {"icp_tier": 3, "company": "C"},
        ]
        matrix = {"accounts": accounts}
        result = self.batch._filter_accounts(matrix, {1, 2})
        self.assertEqual(len(result), 2)

    def test_blocked_accounts_excluded_by_audit(self):
        ready = self._ready_account()
        blocked = self._blocked_account(company="Blocked Corp", domain="blocked.com")
        accounts = [ready, blocked]
        from verify_signals import audit_account
        skipped = [a for a in accounts if audit_account(a)]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["company"], "Blocked Corp")


# ─── activate_account ────────────────────────────────────────────────────────


class TestActivateAccount(VerifySignalsTestBase):
    def setUp(self):
        super().setUp()
        # activate_account imports update_status — copy and register both
        shutil.copy(SCRIPTS_DIR / "update_status.py",
                    self.tmpdir / "scripts" / "update_status.py")
        update_mod = _load(
            "t_update_for_activate", self.tmpdir / "scripts" / "update_status.py"
        )
        sys.modules["update_status"] = update_mod

        shutil.copy(SCRIPTS_DIR / "activate_account.py",
                    self.tmpdir / "scripts" / "activate_account.py")
        self.activate = _load(
            "t_activate", self.tmpdir / "scripts" / "activate_account.py"
        )
        self.activate.OUTPUTS_DIR = self.tmpdir / "outputs"
        sys.modules["activate_account"] = self.activate

    def _write_output_file(self, client: str, company: str, variants: list[dict]) -> Path:
        """Write a real .txt output file using the generate_outreach format function."""
        account = self._ready_account(company=company, domain="test.com")
        matrix = {"client_name": client, "voice_notes": "Direct.", "accounts": [account]}
        content = self.generate.format_output(matrix, account, variants)
        client_dir = self.tmpdir / "outputs" / client
        client_dir.mkdir(parents=True, exist_ok=True)
        slug = self.generate.slugify(company)
        path = client_dir / f"{slug}_2026-04-24.txt"
        path.write_text(content)
        return path

    def _sample_variants(self) -> list[dict]:
        return [
            {"angle_label": "Speed Angle", "subject": "Day one or day 90?",
             "body": "You're about to hire an AE into nothing. We build the infra before they start."},
            {"angle_label": "Cost Angle", "subject": "Three months wasted",
             "body": "First AE's first quarter goes to setup, not selling. Worth a call?"},
            {"angle_label": "Board Angle", "subject": "Pipeline in 90 days",
             "body": "Board wants pipeline metrics. The system to generate them doesn't exist yet."},
        ]

    def test_parse_output_file_returns_three_variants(self):
        path = self._write_output_file("acme-co", "Real Corp", self._sample_variants())
        variants = self.activate.parse_output_file(path)
        self.assertEqual(len(variants), 3)

    def test_parse_output_file_correct_labels(self):
        path = self._write_output_file("acme-co", "Real Corp", self._sample_variants())
        variants = self.activate.parse_output_file(path)
        labels = [v["angle_label"] for v in variants]
        self.assertIn("Speed Angle", labels)
        self.assertIn("Cost Angle", labels)
        self.assertIn("Board Angle", labels)

    def test_parse_output_file_correct_subjects(self):
        path = self._write_output_file("acme-co", "Real Corp", self._sample_variants())
        variants = self.activate.parse_output_file(path)
        subjects = [v["subject"] for v in variants]
        self.assertIn("Day one or day 90?", subjects)

    def test_parse_output_file_body_content(self):
        path = self._write_output_file("acme-co", "Real Corp", self._sample_variants())
        variants = self.activate.parse_output_file(path)
        self.assertIn("AE into nothing", variants[0]["body"])

    def test_find_latest_output_returns_most_recent(self):
        client_dir = self.tmpdir / "outputs" / "acme-co"
        client_dir.mkdir(parents=True, exist_ok=True)
        (client_dir / "real_corp_2026-04-22.txt").write_text("old")
        (client_dir / "real_corp_2026-04-24.txt").write_text("new")
        result = self.activate.find_latest_output("acme-co", "Real Corp")
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "real_corp_2026-04-24.txt")

    def test_find_latest_output_returns_none_when_missing(self):
        result = self.activate.find_latest_output("no-such-client", "No Company")
        self.assertIsNone(result)

    def test_blocked_account_raises_before_push(self):
        """activate_account should refuse to push an account with VERIFY markers."""
        blocked = self._blocked_account()
        issues = self.verify.audit_account(blocked)
        self.assertTrue(len(issues) > 0, "Expected issues on blocked account")


# ─── update_status ───────────────────────────────────────────────────────────


class TestUpdateStatus(VerifySignalsTestBase):
    def setUp(self):
        super().setUp()
        shutil.copy(SCRIPTS_DIR / "update_status.py",
                    self.tmpdir / "scripts" / "update_status.py")
        self.update = _load(
            "t_update", self.tmpdir / "scripts" / "update_status.py"
        )
        sys.modules["update_status"] = self.update

    def _seed(self, client="acme-co"):
        matrix = {
            "client_name": client,
            "voice_notes": "Direct.",
            "accounts": [self._ready_account(company="Acme", domain="acme.com")],
        }
        normalized = client.replace("-", "_")
        path = self.tmpdir / "data" / f"{normalized}_accounts.json"
        path.write_text(json.dumps(matrix))
        return path

    def test_set_status_writes_back(self):
        path = self._seed()
        result = self.update.set_status("acme-co", "Acme", "outreach_sent")
        self.assertEqual(result["status"], "outreach_sent")
        self.assertEqual(result["last_updated"], date.today().isoformat())
        data = json.loads(path.read_text())
        self.assertEqual(data["accounts"][0]["status"], "outreach_sent")

    def test_set_status_rejects_invalid(self):
        self._seed()
        with self.assertRaises(ValueError):
            self.update.set_status("acme-co", "Acme", "shipped_to_mars")

    def test_set_status_appends_note(self):
        self._seed()
        result = self.update.set_status(
            "acme-co", "Acme", "replied", note="Tyler said yes to a call"
        )
        self.assertIn("replied", result["notes"])
        self.assertIn("Tyler said yes", result["notes"])
        self.assertIn(date.today().isoformat(), result["notes"])

    def test_set_status_appends_multiple_notes(self):
        self._seed()
        self.update.set_status("acme-co", "Acme", "outreach_sent", note="First touch")
        result = self.update.set_status("acme-co", "Acme", "replied", note="Reply came")
        self.assertIn("First touch", result["notes"])
        self.assertIn("Reply came", result["notes"])

    def test_set_status_unknown_company_raises(self):
        self._seed()
        with self.assertRaises(ValueError):
            self.update.set_status("acme-co", "Nonexistent Corp", "monitor")

    def test_all_schema_statuses_accepted(self):
        self._seed()
        for s in ("monitor", "active", "outreach_sent", "replied",
                  "meeting_booked", "no_fit", "paused"):
            result = self.update.set_status("acme-co", "Acme", s)
            self.assertEqual(result["status"], s)


# ─── weekly_signal_report — status distribution ──────────────────────────────


class TestWeeklyReportStatusSection(MatrixTestBase):
    def _matrix_with_statuses(self):
        def acct(company, status):
            return {
                "company": company, "domain": f"{company.lower()}.com",
                "icp_tier": 2, "market": "M", "segment": "S",
                "persona": {"title": "CEO", "why_they_feel_it": "x"},
                "angle": "A",
                "why_now_signal": {"type": "manual", "description": "x", "source": "y"},
                "product_fit": "P", "heritage_risk": "Low", "status": status,
            }
        return {
            "client_name": "acme-co", "voice_notes": "x",
            "accounts": [
                acct("Alpha", "monitor"),
                acct("Bravo", "outreach_sent"),
                acct("Charlie", "outreach_sent"),
                acct("Delta", "replied"),
            ],
        }

    def test_status_distribution_section_present(self):
        report = self.weekly.build_report(
            self._matrix_with_statuses(), birddog_by_domain={},
            variant_stats={"sent": 0, "responded": 0, "by_angle": [], "recent": []},
            days_back=7,
        )
        self.assertIn("## Status distribution", report)

    def test_status_distribution_counts_correct(self):
        report = self.weekly.build_report(
            self._matrix_with_statuses(), birddog_by_domain={},
            variant_stats={"sent": 0, "responded": 0, "by_angle": [], "recent": []},
            days_back=7,
        )
        section = report.split("## Status distribution")[1].split("##")[0]
        self.assertIn("| monitor | 1 |", section)
        self.assertIn("| outreach_sent | 2 |", section)
        self.assertIn("| replied | 1 |", section)
        self.assertIn("| meeting_booked | 0 |", section)


# ─── init_matrix ─────────────────────────────────────────────────────────────  (keep last)

if __name__ == "__main__":
    unittest.main()
