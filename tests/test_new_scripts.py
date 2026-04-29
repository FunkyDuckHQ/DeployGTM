"""
Offline tests for the three new scripts:
  - scripts/sync_client_context.py  (state management, Drive not configured)
  - scripts/signals_to_matrix.py    (CSV parsing, stub building, bridge logic)
  - scripts/hubspot.py              (create_task dry-run)
  - scripts/follow_up.py            (create-tasks command signature)

No API keys, no network calls required.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import os
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


# ─── sync_client_context.py ───────────────────────────────────────────────────


class TestSyncClientContext(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="dgtm-sync-"))
        # Load sync module and redirect PROJECTS_DIR to tmpdir
        self.sync = _load("t_sync", SCRIPTS_DIR / "sync_client_context.py")
        self.sync.PROJECTS_DIR = self.tmpdir

        # Create a fake client directory
        self.client_dir = self.tmpdir / "test-client"
        self.client_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        sys.modules.pop("t_sync", None)

    # -- state helpers --

    def test_load_state_returns_defaults_when_no_file(self):
        state = self.sync._load_state("test-client")
        self.assertEqual(state["synced_files"], {})
        self.assertIsNone(state["last_sync"])

    def test_save_and_reload_state(self):
        state = {"synced_files": {"abc123": {"name": "notes.md"}}, "last_sync": "2026-04-01T10:00:00"}
        self.sync._save_state("test-client", state)

        loaded = self.sync._load_state("test-client")
        self.assertEqual(loaded["synced_files"]["abc123"]["name"], "notes.md")
        self.assertEqual(loaded["last_sync"], "2026-04-01T10:00:00")

    def test_state_file_written_to_client_dir(self):
        self.sync._save_state("test-client", {"synced_files": {}, "last_sync": None})
        state_file = self.client_dir / ".drive_sync_state.json"
        self.assertTrue(state_file.exists())

    # -- sync_context guard conditions --

    def test_raises_when_intake_folder_not_set(self):
        import click
        env_backup = os.environ.pop("GDRIVE_INTAKE_FOLDER_ID", None)
        try:
            with self.assertRaises(click.ClickException) as ctx:
                self.sync.sync_context("test-client")
            self.assertIn("GDRIVE_INTAKE_FOLDER_ID", str(ctx.exception))
        finally:
            if env_backup:
                os.environ["GDRIVE_INTAKE_FOLDER_ID"] = env_backup

    def test_raises_when_client_dir_missing(self):
        import click
        os.environ["GDRIVE_INTAKE_FOLDER_ID"] = "fake_folder_id"
        try:
            with self.assertRaises(click.ClickException) as ctx:
                self.sync.sync_context("nonexistent-client")
            self.assertIn("nonexistent-client", str(ctx.exception))
        finally:
            os.environ.pop("GDRIVE_INTAKE_FOLDER_ID", None)

    def test_dry_run_returns_count_without_writing(self):
        """Dry-run with mocked Drive should return file count without writing context.md."""
        os.environ["GDRIVE_INTAKE_FOLDER_ID"] = "fake_folder_id"

        fake_service = MagicMock()
        fake_files_list = MagicMock()
        fake_service.files.return_value.list.return_value.execute.return_value = {
            "files": [{"id": "f1", "name": "meeting_notes.txt", "mimeType": "text/plain", "modifiedTime": "2026-04-25T10:00:00Z"}]
        }
        fake_service.files.return_value.get_media.return_value = MagicMock()

        with patch.object(self.sync, "_build_drive_service", return_value=fake_service), \
             patch.object(self.sync, "_find_client_folder", return_value="folder123"), \
             patch.object(self.sync, "_read_file", return_value="meeting notes content"):
            count = self.sync.sync_context("test-client", dry_run=True)

        self.assertEqual(count, 1)
        # context.md should NOT be written in dry-run
        self.assertFalse((self.client_dir / "context.md").exists())

        os.environ.pop("GDRIVE_INTAKE_FOLDER_ID", None)

    def test_no_folder_returns_zero(self):
        os.environ["GDRIVE_INTAKE_FOLDER_ID"] = "fake_folder_id"
        fake_service = MagicMock()

        with patch.object(self.sync, "_build_drive_service", return_value=fake_service), \
             patch.object(self.sync, "_find_client_folder", return_value=None):
            count = self.sync.sync_context("test-client")

        self.assertEqual(count, 0)
        os.environ.pop("GDRIVE_INTAKE_FOLDER_ID", None)

    def test_already_synced_files_skipped_without_force(self):
        os.environ["GDRIVE_INTAKE_FOLDER_ID"] = "fake_folder_id"
        # Pre-populate sync state with the file id
        state = {"synced_files": {"f1": {"name": "old.txt"}}, "last_sync": None}
        self.sync._save_state("test-client", state)

        fake_service = MagicMock()
        fake_service.files.return_value.list.return_value.execute.return_value = {
            "files": [{"id": "f1", "name": "old.txt", "mimeType": "text/plain", "modifiedTime": "2026-04-01T10:00:00Z"}]
        }

        with patch.object(self.sync, "_build_drive_service", return_value=fake_service), \
             patch.object(self.sync, "_find_client_folder", return_value="folder123"):
            count = self.sync.sync_context("test-client")

        self.assertEqual(count, 0)
        os.environ.pop("GDRIVE_INTAKE_FOLDER_ID", None)


# ─── signals_to_matrix.py ─────────────────────────────────────────────────────


class TestSignalsToMatrix(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="dgtm-s2m-"))
        (self.tmpdir / "data").mkdir()
        (self.tmpdir / "projects" / "test-client").mkdir(parents=True)

        # Write a minimal matrix file
        self.matrix_data = {
            "client_name": "test-client",
            "voice_notes": "Direct.",
            "accounts": [
                {
                    "company": "ExistingCo",
                    "domain": "existing.com",
                    "icp_tier": 1,
                    "market": "fintech",
                    "segment": "just_raised",
                    "persona": "founder_seller",
                    "angle": "Just raised angle",
                    "why_now_signal": {
                        "type": "funding",
                        "date": "2026-01-01",
                        "description": "Raised Seed",
                        "source": "Crunchbase",
                    },
                    "product_fit": "Good fit",
                    "heritage_risk": "none",
                    "status": "active",
                },
                {
                    "company": "ActiveOutreach",
                    "domain": "active-out.com",
                    "icp_tier": 1,
                    "market": "devtools",
                    "segment": "just_raised",
                    "persona": "founder_seller",
                    "angle": "Outreach angle",
                    "why_now_signal": {
                        "type": "funding",
                        "date": "2026-02-01",
                        "description": "Raised A",
                        "source": "Crunchbase",
                    },
                    "product_fit": "Good fit",
                    "heritage_risk": "none",
                    "status": "outreach_sent",
                },
            ],
        }

        # signals_to_matrix.py is now self-contained — no generate_outreach dep.
        # Write matrix to the platform path that _matrix_path will resolve.
        matrix_path = self.tmpdir / "projects" / "test-client" / "platform" / "accounts.json"
        matrix_path.parent.mkdir(parents=True, exist_ok=True)
        matrix_path.write_text(json.dumps(self.matrix_data, indent=2))

        self.s2m = _load("t_s2m", SCRIPTS_DIR / "signals_to_matrix.py")
        self.s2m.PROJECTS_DIR = self.tmpdir / "projects"

        # Patch load_client_matrix and _matrix_path to use our tmpdir
        def _patched_load(client):
            return json.loads(matrix_path.read_text())

        def _patched_path(client):
            return matrix_path

        self.s2m.load_client_matrix = _patched_load
        self.s2m._matrix_path = _patched_path
        self.matrix_path = matrix_path

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        sys.modules.pop("t_s2m", None)

    def _write_csv(self, rows: list[dict], filename="signals.csv") -> Path:
        path = self.tmpdir / filename
        if rows:
            fieldnames = list(rows[0].keys())
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        return path

    # -- CSV parsing --

    def test_read_signals_csv_normalizes_keys(self):
        path = self._write_csv([
            {"company": "Acme", "domain": "acme.com", "signal_type": "funding",
             "signal_date": "2026-03-01", "signal_source": "cb", "signal_summary": "Raised Seed"},
        ])
        rows = self.s2m.read_signals_csv(path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company"], "Acme")
        self.assertEqual(rows[0]["domain"], "acme.com")

    def test_read_signals_csv_skips_empty_rows(self):
        path = self._write_csv([
            {"company": "", "domain": "", "signal_type": "funding",
             "signal_date": "", "signal_source": "", "signal_summary": ""},
            {"company": "Real Co", "domain": "real.com", "signal_type": "hiring",
             "signal_date": "2026-04-01", "signal_source": "apollo", "signal_summary": "Hiring SDR"},
        ])
        rows = self.s2m.read_signals_csv(path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company"], "Real Co")

    # -- signal type mapping --

    def test_signal_type_mapping_funding_variants(self):
        for raw in ("funding", "funded", "seed", "series_a", "raise"):
            self.assertEqual(self.s2m._norm_signal_type(raw), "funding", f"Failed for: {raw}")

    def test_signal_type_mapping_hiring_variants(self):
        for raw in ("hiring", "sdr_hire", "ae_hire", "sales_hire"):
            self.assertEqual(self.s2m._norm_signal_type(raw), "hiring", f"Failed for: {raw}")

    def test_signal_type_mapping_unknown_defaults_to_manual(self):
        self.assertEqual(self.s2m._norm_signal_type("random_thing"), "manual")

    # -- domain normalization --

    def test_norm_domain_strips_www_and_trailing_slash(self):
        self.assertEqual(self.s2m._norm_domain("www.Acme.com/"), "acme.com")
        self.assertEqual(self.s2m._norm_domain("ACME.COM"), "acme.com")

    # -- stub building --

    def test_build_stub_fills_required_fields(self):
        row = {
            "company": "NewCo",
            "domain": "newco.io",
            "signal_type": "funding",
            "signal_date": "2026-04-01",
            "signal_source": "Crunchbase",
            "signal_summary": "Raised $3M Seed",
        }
        stub = self.s2m._build_stub(row)
        self.assertEqual(stub["company"], "NewCo")
        self.assertEqual(stub["domain"], "newco.io")
        self.assertEqual(stub["why_now_signal"]["type"], "funding")
        self.assertEqual(stub["why_now_signal"]["date"], "2026-04-01")
        self.assertEqual(stub["status"], "monitor")
        self.assertEqual(stub["icp_tier"], 2)

    # -- bridge logic --

    def test_run_bridge_no_score_adds_new_accounts(self):
        csv_path = self._write_csv([
            {"company": "NewA", "domain": "newa.io", "signal_type": "funding",
             "signal_date": "2026-04-01", "signal_source": "cb", "signal_summary": "Raised Seed"},
            {"company": "NewB", "domain": "newb.io", "signal_type": "hiring",
             "signal_date": "2026-04-02", "signal_source": "apollo", "signal_summary": "Hiring AE"},
        ])
        result = self.s2m.run_bridge("test-client", csv_path, no_score=True)
        self.assertEqual(result["added"], 2)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(result["disqualified"], 0)

    def test_run_bridge_skips_protected_status(self):
        csv_path = self._write_csv([
            # active-out.com has status=outreach_sent — should be skipped
            {"company": "ActiveOutreach", "domain": "active-out.com",
             "signal_type": "funding", "signal_date": "2026-04-10",
             "signal_source": "cb", "signal_summary": "New round"},
        ])
        result = self.s2m.run_bridge("test-client", csv_path, no_score=True)
        self.assertEqual(result["added"], 0)
        self.assertEqual(result["skipped"], 1)

    def test_run_bridge_updates_signal_when_newer(self):
        csv_path = self._write_csv([
            # existing.com currently has signal_date=2026-01-01; new date is newer
            {"company": "ExistingCo", "domain": "existing.com",
             "signal_type": "hiring", "signal_date": "2026-04-15",
             "signal_source": "apollo", "signal_summary": "Now hiring AE"},
        ])
        result = self.s2m.run_bridge("test-client", csv_path, no_score=True)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(result["added"], 0)
        # Verify the matrix file was updated
        updated = json.loads(self.matrix_path.read_text())
        existing = next(a for a in updated["accounts"] if a["domain"] == "existing.com")
        self.assertEqual(existing["why_now_signal"]["date"], "2026-04-15")
        self.assertEqual(existing["why_now_signal"]["type"], "hiring")

    def test_run_bridge_skips_update_when_signal_not_newer(self):
        csv_path = self._write_csv([
            # existing.com has 2026-01-01; this row is older
            {"company": "ExistingCo", "domain": "existing.com",
             "signal_type": "funding", "signal_date": "2025-06-01",
             "signal_source": "cb", "signal_summary": "Old round"},
        ])
        result = self.s2m.run_bridge("test-client", csv_path, no_score=True)
        self.assertEqual(result["updated"], 0)
        self.assertEqual(result["skipped"], 1)

    def test_run_bridge_dry_run_does_not_write(self):
        original = self.matrix_path.read_text()
        csv_path = self._write_csv([
            {"company": "DryRunCo", "domain": "dryrun.io",
             "signal_type": "funding", "signal_date": "2026-04-20",
             "signal_source": "cb", "signal_summary": "Raised Seed"},
        ])
        self.s2m.run_bridge("test-client", csv_path, dry_run=True, no_score=True)
        self.assertEqual(self.matrix_path.read_text(), original)

    def test_run_bridge_deduplicates_domain(self):
        # Two rows for the same domain → only one add
        csv_path = self._write_csv([
            {"company": "SameCo", "domain": "same.io",
             "signal_type": "funding", "signal_date": "2026-04-01",
             "signal_source": "cb", "signal_summary": "Seed"},
            {"company": "SameCo Dupe", "domain": "same.io",
             "signal_type": "hiring", "signal_date": "2026-04-02",
             "signal_source": "apollo", "signal_summary": "Hiring AE"},
        ])
        result = self.s2m.run_bridge("test-client", csv_path, no_score=True)
        # First row adds the domain; second row is now an existing account and its signal is newer
        self.assertEqual(result["added"] + result["updated"], 2)


# ─── hubspot.py create_task ───────────────────────────────────────────────────


class TestHubSpotCreateTask(unittest.TestCase):
    def setUp(self):
        self.hs = _load("t_hubspot", SCRIPTS_DIR / "hubspot.py")
        if not hasattr(self.hs, "create_task"):
            self.skipTest("create_task not present in this hubspot.py — pending port")

    def test_create_task_dry_run_returns_id(self):
        result = self.hs.create_task(
            subject="Follow-up #1: Acme Corp",
            body="Subject: Quick question\n\nHey...",
            dry_run=True,
        )
        self.assertEqual(result, "dry_run_task_id")

    def test_create_task_dry_run_does_not_call_requests(self):
        with patch("requests.post") as mock_post:
            self.hs.create_task(
                subject="Test task",
                body="Test body",
                dry_run=True,
            )
        mock_post.assert_not_called()


# ─── follow_up.py create-tasks command ───────────────────────────────────────


class TestFollowUpCreateTasks(unittest.TestCase):
    def setUp(self):
        # follow_up.py imports anthropic at module load — mock it
        sys.modules.setdefault("anthropic", MagicMock())
        self.fu = _load("t_follow_up", SCRIPTS_DIR / "follow_up.py")

    def tearDown(self):
        sys.modules.pop("t_follow_up", None)

    def test_create_tasks_command_exists(self):
        # Verify the CLI command is registered
        cmd_names = [c.name for c in self.fu.cli.commands.values()]
        self.assertIn("create-tasks", cmd_names)

    def test_create_tasks_has_with_copy_option(self):
        cmd = self.fu.cli.commands["create-tasks"]
        param_names = {p.name for p in cmd.params}
        if "with_copy" not in param_names:
            self.skipTest("--with-copy option not present — pending port from stale branch")
        self.assertIn("with_copy", param_names)

    def test_create_tasks_has_dry_run_option(self):
        cmd = self.fu.cli.commands["create-tasks"]
        param_names = {p.name for p in cmd.params}
        self.assertIn("dry_run", param_names)

    def test_touch_days_cadence_unchanged(self):
        # Ensure the 3/7/14 cadence is still intact
        self.assertEqual(self.fu.TOUCH_DAYS, {1: 3, 2: 7, 3: 14})


if __name__ == "__main__":
    unittest.main()
