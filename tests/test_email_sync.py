from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.email_sync import apply_events


def test_email_events_update_engagement_and_activation_score():
    matrix = {
        "accounts": [
            {
                "company": "Acme",
                "domain": "acme.com",
                "scores": {
                    "icp_fit_score": 80,
                    "urgency_score": 70,
                    "engagement_score": 0,
                    "confidence_score": 65,
                    "activation_priority": 67,
                },
            }
        ]
    }

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
    assert account["scores"]["engagement_score"] > 0
    assert account["scores"]["activation_priority"] > 67
