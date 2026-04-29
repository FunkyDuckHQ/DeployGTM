# DeployGTM Scoring Model

## Purpose

The scoring model decides which accounts deserve enrichment, outreach, monitoring, manual review, or exclusion.

It separates fit from timing.

- `icp_score`: should this account be in the market?
- `urgency_score`: should we act now?
- `engagement_score`: have they shown response or interest?
- `contact_score`: is this the right person?

## ICP Score

Scale: 0 to 100.

Recommended components:

- firmographic fit: 20
- segment / use case fit: 20
- pain hypothesis strength: 15
- ability to buy or implement: 15
- strategic value: 10
- negative indicator adjustment: -20 to 0
- evidence confidence: 20

Example:

```json
{
  "score_type": "icp",
  "score": 84,
  "component_scores": {
    "firmographic_fit": 17,
    "segment_fit": 18,
    "pain_hypothesis": 13,
    "ability_to_buy": 12,
    "strategic_value": 8,
    "negative_adjustment": -2,
    "evidence_confidence": 18
  },
  "recommended_route": "enrich"
}
```

## Urgency Score

Scale: 0 to 100.

Recommended components:

- active trigger strength: 25
- timing window: 20
- willingness to act evidence: 20
- ability to act evidence: 15
- signal freshness: 10
- signal stack strength: 10

Urgency should decay over time unless refreshed by new evidence.

## Decay

Every signal should have:

- `observed_at`
- `expires_at`
- `default_decay_days`
- `decay_half_life_days`
- `current_signal_strength`

Suggested defaults:

- website visit / form engagement: 7 to 14 days
- hiring or job post signal: 30 to 60 days
- funding signal: 60 to 120 days
- procurement or RFP signal: deadline-based
- leadership change: 30 to 90 days
- technical milestone: 30 to 180 days depending on market
- first-party customer behavior: product-cycle specific

Simple decay formula:

```text
current_signal_strength = original_strength * 0.5 ^ (days_since_observed / decay_half_life_days)
```

## Route Logic

Suggested account routing:

| Condition | Route |
| --- | --- |
| ICP >= 80 and urgency >= 70 | manual sales review and enrich |
| ICP >= 80 and urgency 40-69 | enrich and campaign test |
| ICP >= 80 and urgency < 40 | enrich selectively or monitor |
| ICP 65-79 and urgency >= 80 | manual review |
| ICP 65-79 and urgency 50-79 | monitor or test cohort |
| ICP < 65 and urgency >= 85 | human review only |
| ICP < 65 and urgency < 85 | hold or exclude |

## Engagement Feedback

Engagement should update scores, but it should not replace fit.

Positive engagement examples:

- reply
- meeting booked
- forwarded internally
- clicked high-intent asset
- repeated visits from same account
- direct referral

Negative engagement examples:

- unsubscribe
- bounce
- explicit no-fit reply
- competitor lock-in
- timing objection with date

## Source Notes

- DeployGTM Build Spec requires scoring accounts, enriching contacts, monitoring signals, drafting outreach, and returning exception reports: [Build Spec](https://docs.google.com/document/d/13tkqFzql8LsqIZQa0uQijYMlJcTcI9tTPeazTDqWEXg).
- Clay's signal docs support real-time signal detection, frequency/conversion prioritization, enrichment, and action routing: [Intro to Signals](https://university.clay.com/lessons/intro-to-signals-in-clay-signals-abm), [Announcing custom signals](https://www.clay.com/blog/signals), and [Building Custom Signals in Clay](https://university.clay.com/lessons/building-custom-signals-in-clay).
- Josh Whitfield / GTM Engineer School E4 supports alpha signals tied to ability and willingness to act: [Apple Podcasts episode summary](https://podcasts.apple.com/us/podcast/e4-its-creativity-not-prompts-why-gtm-engineers-need/id1833013226?i=1000724738164).
