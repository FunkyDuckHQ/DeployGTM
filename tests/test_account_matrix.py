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


def _load(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── Fixture: fresh temp project root per test so we don't pollute real data ──


class MatrixTestBase(unittest.TestCase):
    """Base class that copies the deploygtm-own project into a tempdir and
    monkeypatches the three scripts to read/write there instead of the repo."""

    def setUp(self):
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


if __name__ == "__main__":
    unittest.main()
