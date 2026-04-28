"""
Offline tests for scripts/email_sync.py — engagement sync from email
platforms (Supersend / generic) into the client's account matrix.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
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


def _matrix_with(accounts: list[dict]) -> dict:
    return {
        "client_name": "testclient",
        "voice_notes": "test",
        "accounts": accounts,
    }


def _account(company: str, domain: str, **kwargs) -> dict:
    base = {
        "company": company,
        "domain": domain,
        "icp_tier": 2,
        "status": "monitor",
        "fit_score": 5.0,
        "current_score": 5.0,
        "score_history": [],
    }
    base.update(kwargs)
    return base


class EmailSyncBase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="dgtm-emailsync-"))
        (self.tmpdir / "data").mkdir()

        # Load score_engine, generate_outreach, derive_icp, then email_sync —
        # each gets its DATA_DIR redirected into the tempdir.
        self.gen = _load("eg_generate", MATRIX_SCRIPTS_DIR / "generate_outreach.py")
        self.gen.DATA_DIR = self.tmpdir / "data"
        sys.modules["generate_outreach"] = self.gen

        self.derive = _load("eg_derive", SCRIPTS_DIR / "derive_icp.py")
        self.derive.MATRIX_DATA_DIR = self.tmpdir / "data"
        sys.modules["derive_icp"] = self.derive

        self.score = _load("eg_score", MATRIX_SCRIPTS_DIR / "score_engine.py")
        sys.modules["score_engine"] = self.score

        self.sync = _load("eg_sync", SCRIPTS_DIR / "email_sync.py")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        for mod in ("eg_generate", "eg_derive", "eg_score", "eg_sync",
                    "generate_outreach", "derive_icp", "score_engine"):
            sys.modules.pop(mod, None)

    def _write_matrix(self, accounts: list[dict]) -> Path:
        path = self.tmpdir / "data" / "testclient_accounts.json"
        path.write_text(json.dumps(_matrix_with(accounts), indent=2) + "\n")
        return path


# ─── Pure helpers (no I/O) ────────────────────────────────────────────────────


class TestNormaliseEvent(EmailSyncBase):
    def test_known_supersend_aliases(self):
        self.assertEqual(self.sync._normalise_event("email.opened"), "open")
        self.assertEqual(self.sync._normalise_event("email.replied"), "reply")
        self.assertEqual(self.sync._normalise_event("email.bounced"), "bounce")
        self.assertEqual(self.sync._normalise_event("email.unsubscribed"), "unsubscribe")

    def test_already_normalised(self):
        self.assertEqual(self.sync._normalise_event("send"), "send")
        self.assertEqual(self.sync._normalise_event("REPLY"), "reply")

    def test_unknown_returns_none(self):
        self.assertIsNone(self.sync._normalise_event("email.weird_thing"))
        self.assertIsNone(self.sync._normalise_event(""))
        self.assertIsNone(self.sync._normalise_event(None))


class TestClassifySentiment(EmailSyncBase):
    def test_negative_phrases(self):
        self.assertEqual(self.sync._classify_reply_sentiment("Please unsubscribe me"), "negative")
        self.assertEqual(self.sync._classify_reply_sentiment("Not interested, thanks"), "negative")
        self.assertEqual(self.sync._classify_reply_sentiment("wrong person — remove me"), "negative")

    def test_positive_phrases(self):
        self.assertEqual(self.sync._classify_reply_sentiment("Sure, send a calendar link"), "positive")
        self.assertEqual(self.sync._classify_reply_sentiment("Worth a call. 20 minutes?"), "positive")
        self.assertEqual(self.sync._classify_reply_sentiment("Tell me more"), "positive")

    def test_neutral_default(self):
        self.assertEqual(self.sync._classify_reply_sentiment("ok"), "neutral")
        self.assertEqual(self.sync._classify_reply_sentiment(""), "neutral")


class TestCoerceEvent(EmailSyncBase):
    def test_extracts_supersend_shape(self):
        raw = {
            "id": "evt_123",
            "type": "email.replied",
            "recipient": "tyler@loops.so",
            "timestamp": "2026-04-27T12:00:00Z",
            "body": "Worth a call",
        }
        e = self.sync._coerce_event(raw)
        self.assertEqual(e["type"], "reply")
        self.assertEqual(e["id"], "evt_123")
        self.assertEqual(e["recipient"], "tyler@loops.so")

    def test_skips_unknown_type(self):
        self.assertIsNone(self.sync._coerce_event({"type": "weird", "recipient": "a@b.com"}))

    def test_skips_missing_recipient(self):
        self.assertIsNone(self.sync._coerce_event({"type": "email.opened"}))

    def test_falls_back_to_to_field(self):
        e = self.sync._coerce_event({"event": "email.opened", "to": "x@y.com"})
        self.assertEqual(e["recipient"], "x@y.com")
        self.assertEqual(e["type"], "open")

    def test_synthetic_id_when_missing(self):
        e = self.sync._coerce_event({"type": "email.click", "recipient": "a@b.com",
                                     "timestamp": "2026-04-27"})
        self.assertIn("click", e["id"])
        self.assertIn("a@b.com", e["id"])


# ─── Account matching ────────────────────────────────────────────────────────


class TestAccountMatching(EmailSyncBase):
    def test_match_by_contact_email(self):
        acct = _account("Loops", "loops.so", contacts=[
            {"email": "tyler@loops.so", "name": "Tyler"},
        ])
        matrix = _matrix_with([acct])
        email_idx, domain_idx = self.sync._index_accounts(matrix)
        m = self.sync._match_account("tyler@loops.so", email_idx, domain_idx)
        self.assertIs(m, acct)

    def test_match_by_domain_fallback(self):
        acct = _account("Loops", "loops.so")
        matrix = _matrix_with([acct])
        email_idx, domain_idx = self.sync._index_accounts(matrix)
        m = self.sync._match_account("someone-new@loops.so", email_idx, domain_idx)
        self.assertIs(m, acct)

    def test_no_match_returns_none(self):
        matrix = _matrix_with([_account("Loops", "loops.so")])
        email_idx, domain_idx = self.sync._index_accounts(matrix)
        self.assertIsNone(self.sync._match_account("a@unknown.com", email_idx, domain_idx))

    def test_email_index_case_insensitive(self):
        acct = _account("Loops", "loops.so", contacts=[
            {"email": "Tyler@Loops.So"},
        ])
        matrix = _matrix_with([acct])
        email_idx, domain_idx = self.sync._index_accounts(matrix)
        m = self.sync._match_account("TYLER@loops.so", email_idx, domain_idx)
        self.assertIs(m, acct)


# ─── Apply event ─────────────────────────────────────────────────────────────


class TestApplyEvent(EmailSyncBase):
    def test_send_promotes_monitor_to_outreach_sent(self):
        acct = _account("Loops", "loops.so", status="monitor")
        event = {"id": "e1", "type": "send", "recipient": "tyler@loops.so",
                 "timestamp": "2026-04-27"}
        self.sync._apply_event(acct, event, profile=None)
        self.assertEqual(acct["status"], "outreach_sent")

    def test_send_does_not_downgrade_replied(self):
        acct = _account("Loops", "loops.so", status="replied")
        event = {"id": "e1", "type": "send", "recipient": "tyler@loops.so",
                 "timestamp": "2026-04-27"}
        self.sync._apply_event(acct, event, profile=None)
        self.assertEqual(acct["status"], "replied")

    def test_reply_positive_sets_replied_status(self):
        acct = _account("Loops", "loops.so", status="outreach_sent")
        event = {"id": "e1", "type": "reply", "recipient": "tyler@loops.so",
                 "timestamp": "2026-04-27", "body": "Worth a call. 20 minutes?",
                 "sentiment": None}
        self.sync._apply_event(acct, event, profile=None)
        self.assertEqual(acct["status"], "replied")
        # Sentiment event recorded
        sentiments = [e for e in acct["score_history"] if e.get("type") == "sentiment"]
        self.assertEqual(sentiments[-1]["value"], "positive")

    def test_reply_negative_sets_no_fit(self):
        acct = _account("Loops", "loops.so", status="outreach_sent")
        event = {"id": "e1", "type": "reply", "recipient": "tyler@loops.so",
                 "timestamp": "2026-04-27", "body": "not interested, remove me"}
        self.sync._apply_event(acct, event, profile=None)
        self.assertEqual(acct["status"], "no_fit")

    def test_bounce_sets_no_fit_and_negative_sentiment(self):
        acct = _account("Loops", "loops.so", status="outreach_sent")
        event = {"id": "e1", "type": "bounce", "recipient": "tyler@loops.so",
                 "timestamp": "2026-04-27"}
        self.sync._apply_event(acct, event, profile=None)
        self.assertEqual(acct["status"], "no_fit")
        sentiments = [e for e in acct["score_history"] if e.get("type") == "sentiment"]
        self.assertEqual(sentiments[-1]["value"], "negative")

    def test_unsubscribe_sets_no_fit(self):
        acct = _account("Loops", "loops.so", status="outreach_sent")
        event = {"id": "e1", "type": "unsubscribe", "recipient": "tyler@loops.so",
                 "timestamp": "2026-04-27"}
        self.sync._apply_event(acct, event, profile=None)
        self.assertEqual(acct["status"], "no_fit")

    def test_open_below_threshold_no_score_event(self):
        acct = _account("Loops", "loops.so")
        event = {"id": "e1", "type": "open", "recipient": "tyler@loops.so",
                 "timestamp": "2026-04-27"}
        self.sync._apply_event(acct, event, profile=None)
        # No birddog_signal recorded yet (count = 1)
        signals = [e for e in acct["score_history"] if e.get("type") == "birddog_signal"]
        self.assertEqual(len(signals), 0)

    def test_open_at_threshold_records_engaged(self):
        acct = _account("Loops", "loops.so")
        for i in range(self.sync.OPEN_ENGAGEMENT_THRESHOLD):
            self.sync._apply_event(acct, {
                "id": f"open_{i}",
                "type": "open",
                "recipient": "tyler@loops.so",
                "timestamp": "2026-04-27",
            }, profile=None)
        signals = [e for e in acct["score_history"] if e.get("type") == "birddog_signal"]
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["value"], "engaged")

    def test_click_records_engaged(self):
        acct = _account("Loops", "loops.so")
        event = {"id": "e1", "type": "click", "recipient": "tyler@loops.so",
                 "timestamp": "2026-04-27"}
        self.sync._apply_event(acct, event, profile=None)
        signals = [e for e in acct["score_history"] if e.get("type") == "birddog_signal"]
        self.assertEqual(len(signals), 1)

    def test_idempotent_dedupe_by_event_id(self):
        acct = _account("Loops", "loops.so")
        event = {"id": "evt_dupe", "type": "click", "recipient": "tyler@loops.so",
                 "timestamp": "2026-04-27"}
        first = self.sync._apply_event(acct, event, profile=None)
        second = self.sync._apply_event(acct, event, profile=None)
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        # Only one engaged signal recorded
        signals = [e for e in acct["score_history"] if e.get("type") == "birddog_signal"]
        self.assertEqual(len(signals), 1)


# ─── End-to-end sync ─────────────────────────────────────────────────────────


class TestSyncEvents(EmailSyncBase):
    def test_full_sync_writes_matrix_and_summary(self):
        acct = _account("Loops", "loops.so", status="monitor", contacts=[
            {"email": "tyler@loops.so"},
        ])
        path = self._write_matrix([acct])

        events = [
            {"id": "e1", "type": "email.sent", "recipient": "tyler@loops.so",
             "timestamp": "2026-04-27T10:00:00Z"},
            {"id": "e2", "type": "email.replied", "recipient": "tyler@loops.so",
             "timestamp": "2026-04-27T11:00:00Z", "body": "Tell me more"},
            {"id": "e3", "type": "email.opened", "recipient": "ghost@nowhere.com",
             "timestamp": "2026-04-27T12:00:00Z"},
        ]

        summary = self.sync.sync_events("testclient", events, dry_run=False)

        self.assertEqual(summary["matched"], 2)
        self.assertEqual(summary["unmatched"], 1)
        self.assertEqual(summary["applied"], 2)

        # Reload matrix and verify status was promoted to replied
        reloaded = json.loads(path.read_text())
        self.assertEqual(reloaded["accounts"][0]["status"], "replied")

    def test_dry_run_does_not_write(self):
        acct = _account("Loops", "loops.so", status="monitor")
        path = self._write_matrix([acct])
        original = path.read_text()

        events = [{"id": "e1", "type": "email.sent", "recipient": "tyler@loops.so"}]
        self.sync.sync_events("testclient", events, dry_run=True)

        # File untouched
        self.assertEqual(path.read_text(), original)

    def test_unmatched_event_skipped_no_error(self):
        self._write_matrix([_account("Loops", "loops.so")])
        events = [{"id": "e1", "type": "email.sent",
                   "recipient": "anyone@unknown-domain.com"}]
        summary = self.sync.sync_events("testclient", events)
        self.assertEqual(summary["unmatched"], 1)
        self.assertEqual(summary["applied"], 0)


# ─── Provider: generic events file ───────────────────────────────────────────


class TestLoadEventsFile(EmailSyncBase):
    def test_list_format(self):
        f = self.tmpdir / "events.json"
        f.write_text(json.dumps([
            {"type": "email.opened", "recipient": "a@b.com"},
        ]))
        events = self.sync.load_events_file(f)
        self.assertEqual(len(events), 1)

    def test_envelope_format(self):
        f = self.tmpdir / "events.json"
        f.write_text(json.dumps({"events": [
            {"type": "email.click", "recipient": "a@b.com"},
        ]}))
        events = self.sync.load_events_file(f)
        self.assertEqual(len(events), 1)


# ─── Provider: Supersend (mocked) ────────────────────────────────────────────


class TestFetchSupersend(EmailSyncBase):
    def test_fetches_and_paginates(self):
        page1 = MagicMock()
        page1.status_code = 200
        page1.json.return_value = {
            "events": [{"id": "e1", "type": "email.opened", "recipient": "a@b.com"}],
            "next_cursor": "cur_2",
        }
        page2 = MagicMock()
        page2.status_code = 200
        page2.json.return_value = {
            "events": [{"id": "e2", "type": "email.click", "recipient": "c@d.com"}],
            "next_cursor": None,
        }

        with patch.dict("os.environ", {"SUPERSEND_API_KEY": "test-key"}):
            with patch("requests.get", side_effect=[page1, page2]) as get:
                events = self.sync.fetch_supersend_events(
                    datetime(2026, 4, 1),
                )
        self.assertEqual(len(events), 2)
        self.assertEqual(get.call_count, 2)

    def test_raises_on_missing_key(self):
        import click as _click
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(_click.ClickException):
                self.sync.fetch_supersend_events(datetime(2026, 4, 1))

    def test_raises_on_401(self):
        import click as _click
        bad = MagicMock()
        bad.status_code = 401
        bad.text = "unauthorized"
        with patch.dict("os.environ", {"SUPERSEND_API_KEY": "test-key"}):
            with patch("requests.get", return_value=bad):
                with self.assertRaises(_click.ClickException):
                    self.sync.fetch_supersend_events(datetime(2026, 4, 1))


if __name__ == "__main__":
    unittest.main()
