from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.email_sync import apply_events, maybe_flag_profile_update, log_execution


def _base_matrix():
    return {
        "schema_version": "v1.0",
        "client": {"client_name": "Acme", "domain": "acme.com", "voice_notes": "test"},
        "accounts": [
            {"company": "Xona", "domain": "xona.com", "score": {"priority": 10}},
            {"company": "Umbra", "domain": "umbra.space", "score": {"priority": 8}},
        ],
    }


def test_apply_events_reply_and_open_nudge():
    matrix = _base_matrix()

    events = [
        {"type": "open", "contact": {"email": "a@xona.com"}},
        {"type": "open", "contact": {"email": "a@xona.com"}},
        {"type": "open", "contact": {"email": "a@xona.com"}},
        {"type": "reply", "contact": {"email": "a@xona.com"}},
    ]

    counts = apply_events(matrix, events)
    account = matrix["accounts"][0]

    assert counts["applied"] == 4
    assert account["engagement"]["open_count"] == 3
    assert account["engagement"]["reply_count"] == 1
    assert account["engagement"]["sentiment"] == "positive"
    assert account["engagement"]["sentiment_mod"] == 2
    assert account["score"]["priority_adjusted"] == 12


def test_apply_events_hard_bounce_disqualifies():
    matrix = _base_matrix()
    events = [
        {
            "type": "bounce",
            "contact": {"email": "ops@umbra.space"},
            "bounce_category": "invalid_recipient",
        }
    ]

    counts = apply_events(matrix, events)
    account = matrix["accounts"][1]

    assert counts["event_bounce"] == 1
    assert account["engagement"]["status"] == "disqualified"
    assert account["engagement"]["sentiment"] == "negative"
    assert account["score"]["priority_adjusted"] == 6


def test_profile_update_flag_written_when_threshold_reached(tmp_path: Path):
    from scripts import email_sync

    email_sync.PROJECTS_DIR = tmp_path
    matrix = _base_matrix()
    # simulate sufficient replies for profile re-derivation gate
    matrix["accounts"][0]["engagement"] = {"reply_count": 31}

    status = maybe_flag_profile_update("acme-space", matrix, threshold=30)
    flag_file = tmp_path / "acme-space" / "platform" / "profile_update_needed.json"

    assert status == "flagged"
    assert flag_file.exists()
    payload = json.loads(flag_file.read_text())
    assert payload["reply_count"] == 31


def test_execution_log_appends_jsonl(tmp_path: Path):
    from scripts import email_sync

    email_sync.LOGS_DIR = tmp_path
    log_path = log_execution(
        client_slug="acme-space",
        mode="poll",
        counts={"applied": 2},
        events_fetched=2,
        dry_run=True,
        update_profile=False,
        profile_update_status="not_requested",
    )

    assert log_path.exists()
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["client_slug"] == "acme-space"
    assert row["dry_run"] is True
