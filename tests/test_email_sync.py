"""
Tests for scripts/email_sync.py — covers both the original apply_events
contract (from main) and the enhanced features: idempotent dedupe,
contact-email matching, reply sentiment, unsubscribe/bounce status,
and extended event-type aliases.
"""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.email_sync import (
    apply_events,
    record_event,
    _normalize_event_type,
    _classify_reply_sentiment,
    _extract_domain,
    _ensure_engagement,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _account(domain: str, **kwargs) -> dict:
    base = {
        "company": domain.split(".")[0].title(),
        "domain": domain,
        "scores": {
            "icp_fit_score": 80,
            "urgency_score": 70,
            "engagement_score": 0,
            "confidence_score": 65,
            "activation_priority": 67,
        },
    }
    base.update(kwargs)
    return base


def _matrix(*domains: str, **kwargs) -> dict:
    return {"accounts": [_account(d, **kwargs) for d in domains]}


# ─── _normalize_event_type ───────────────────────────────────────────────────


def test_normalize_dot_notation():
    assert _normalize_event_type("email.opened") == "open"
    assert _normalize_event_type("email.replied") == "reply"
    assert _normalize_event_type("email.bounced") == "bounce"
    assert _normalize_event_type("email.unsubscribed") == "unsubscribe"
    assert _normalize_event_type("email.clicked") == "click"
    assert _normalize_event_type("email.sent") == "sent"


def test_normalize_flat_aliases():
    assert _normalize_event_type("opened") == "open"
    assert _normalize_event_type("clicked") == "click"
    assert _normalize_event_type("replied") == "reply"
    assert _normalize_event_type("bounced") == "bounce"


def test_normalize_passthrough():
    assert _normalize_event_type("open") == "open"
    assert _normalize_event_type("REPLY") == "reply"


def test_normalize_unknown():
    # Unknown types pass through; apply_events will skip them
    result = _normalize_event_type("some_weird_type")
    assert result == "some_weird_type"


# ─── _classify_reply_sentiment ───────────────────────────────────────────────


def test_sentiment_positive():
    assert _classify_reply_sentiment("Worth a call. 20 minutes?") == "positive"
    assert _classify_reply_sentiment("Interested, tell me more") == "positive"
    assert _classify_reply_sentiment("Happy to talk. Send a calendar link.") == "positive"


def test_sentiment_negative():
    assert _classify_reply_sentiment("Please unsubscribe me") == "negative"
    assert _classify_reply_sentiment("Not interested, thanks") == "negative"
    assert _classify_reply_sentiment("wrong person — remove me") == "negative"


def test_sentiment_neutral():
    assert _classify_reply_sentiment("ok") == "neutral"
    assert _classify_reply_sentiment("") == "neutral"


# ─── Original apply_events contract (from main) ──────────────────────────────


def test_email_events_update_engagement_and_activation_score():
    matrix = _matrix("acme.com")
    counts = apply_events(
        matrix,
        [
            {"event": "opened", "email": "buyer@acme.com"},
            {"event": "clicked", "email": "buyer@acme.com"},
            {"event": "replied", "email": "buyer@acme.com"},
        ],
    )
    account = matrix["accounts"][0]
    assert counts["applied"] == 3
    assert account["engagement"]["reply_count"] == 1
    assert account["engagement"]["open_count"] == 1
    assert account["engagement"]["click_count"] == 1
    assert account["scores"]["engagement_score"] > 0
    assert account["scores"]["activation_priority"] > 67


def test_unmatched_events_skipped():
    matrix = _matrix("acme.com")
    counts = apply_events(matrix, [{"event": "opened", "email": "buyer@unknown.com"}])
    assert counts.get("skipped_no_match", 0) == 1
    assert counts.get("applied", 0) == 0


# ─── Enhanced: contact-email matching ────────────────────────────────────────


def test_match_by_contact_email_takes_priority_over_domain():
    acme = _account("acme.com", contacts=[{"email": "tyler@acme.com"}])
    other = _account("other.com")
    matrix = {"accounts": [acme, other]}

    apply_events(matrix, [{"event": "replied", "email": "tyler@acme.com"}])
    # acme got the reply, not other
    assert acme["engagement"]["reply_count"] == 1
    assert other.get("engagement", {}).get("reply_count", 0) == 0


# ─── Enhanced: idempotent dedupe ─────────────────────────────────────────────


def test_duplicate_event_id_not_applied_twice():
    matrix = _matrix("acme.com")
    event = {"id": "evt_abc", "event": "clicked", "email": "x@acme.com"}
    apply_events(matrix, [event])
    apply_events(matrix, [event])
    assert matrix["accounts"][0]["engagement"]["click_count"] == 1


def test_events_without_id_are_applied_each_time():
    # No 'id' field — cannot dedupe, applied on every call
    matrix = _matrix("acme.com")
    event = {"event": "opened", "email": "x@acme.com"}
    apply_events(matrix, [event])
    apply_events(matrix, [event])
    assert matrix["accounts"][0]["engagement"]["open_count"] == 2


# ─── Enhanced: reply sentiment ────────────────────────────────────────────────


def test_positive_reply_sets_replied_status():
    matrix = _matrix("acme.com")
    apply_events(matrix, [{
        "event": "replied",
        "email": "x@acme.com",
        "body": "Worth a call. 20 minutes?",
    }])
    eng = matrix["accounts"][0]["engagement"]
    assert eng["status"] == "replied"
    assert eng.get("last_reply_sentiment") == "positive"


def test_negative_reply_disqualifies():
    matrix = _matrix("acme.com")
    apply_events(matrix, [{
        "event": "replied",
        "email": "x@acme.com",
        "body": "Please unsubscribe me, not interested",
    }])
    eng = matrix["accounts"][0]["engagement"]
    assert eng["status"] == "disqualified"
    assert eng.get("last_reply_sentiment") == "negative"


# ─── Enhanced: bounce + unsubscribe status ───────────────────────────────────


def test_bounce_sets_delivery_issue():
    matrix = _matrix("acme.com")
    apply_events(matrix, [{"event": "bounced", "email": "x@acme.com"}])
    assert matrix["accounts"][0]["engagement"]["status"] == "delivery_issue"
    assert matrix["accounts"][0]["engagement"]["bounce_count"] == 1


def test_unsubscribe_disqualifies():
    matrix = _matrix("acme.com")
    apply_events(matrix, [{"event": "unsubscribed", "email": "x@acme.com"}])
    assert matrix["accounts"][0]["engagement"]["status"] == "disqualified"


# ─── Enhanced: dot-notation aliases ─────────────────────────────────────────


def test_dot_notation_aliases_work_in_apply_events():
    matrix = _matrix("acme.com")
    counts = apply_events(matrix, [
        {"type": "email.opened", "recipient": "x@acme.com"},
        {"type": "email.clicked", "recipient": "x@acme.com"},
    ])
    assert counts["applied"] == 2
    eng = matrix["accounts"][0]["engagement"]
    assert eng["open_count"] == 1
    assert eng["click_count"] == 1
