# Outbound Feedback Loop

## Purpose

Outbound is not just a meeting-generation machine. It is a structured feedback loop for testing ICP, message-market fit, buying triggers, objections, and urgency.

The operator should be able to say:

> We are not just buying outbound volume. We are building the feedback loop that tells us what the market actually responds to.

## Loop

```text
hypothesis -> sequence -> reply -> classify -> learn -> update -> retest
```

## Required Metrics

- unique sequences tested
- segments tested
- accounts targeted
- contacts enrolled
- verified contact rate
- positive reply rate
- negative reply rate
- neutral or curious reply rate
- meeting conversion rate
- quality of responses
- objection frequency
- signal quality by segment
- account score movement
- CRM action completion
- iteration cycles completed

## Reply Categories

- `positive`: clear interest, referral, meeting intent, or useful buying motion.
- `neutral_curious`: asks a question, requests more context, or shows weak curiosity.
- `negative`: no interest, bad fit, timing rejection, vendor rejection, or unsubscribe.
- `objection`: concern about proof, timing, budget, authority, risk, or switching cost.
- `referral`: points to another stakeholder.
- `manual_review`: strategic or sensitive response requiring human judgment.

## Experiment Shape

Every outbound test should define:

- hypothesis
- segment
- persona
- signal basis
- message angle
- proof point
- claims allowed
- claims blocked
- channel
- sequence count
- success metric
- stop condition
- learning owner

## Human Review Rules

Route to manual review when:

- urgency score is high
- account is strategic
- signal is unusual or sensitive
- executive buyer is involved
- product claim needs founder judgment
- reply implies procurement, risk, or partnership complexity

## Source Notes

- Strategy source: user-provided DeployGTM Strategy / Product / Architecture Condensed Brief, shared April 30, 2026.
- Existing scoring and routing sources: [master/scoring-model.md](../master/scoring-model.md), [master/client-workflow.md](../master/client-workflow.md), and [3_operations/scripts/score_accounts.py](../3_operations/scripts/score_accounts.py).
