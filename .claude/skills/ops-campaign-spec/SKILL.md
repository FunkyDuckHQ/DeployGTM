---
name: ops-campaign-spec
trigger: new campaign, campaign spec, paid test, outbound test, launch campaign
---

## When To Use

Use this skill when preparing a campaign, outbound test, nurture flow, or acquisition experiment.

## Steps

1. Load the ICP definition, score thresholds, message matrix, and channel constraints.
2. State the campaign hypothesis.
3. Define audience, budget or volume ceiling, and exclusions.
4. Attach graduation criteria and pause criteria.
5. Define CRM attribution and writeback rules.
6. Keep production status as draft or paused until a human approves.
7. Save the campaign spec using `templates/campaign-spec.md`.
8. Produce an execution checklist and exception risks.

## Output

Write to:

- `2_acquisition/experiments/{client}-{campaign}.md`
- channel-specific folders such as `2_acquisition/paid/` or `2_acquisition/outbound/`

## Epilogue

After campaign review, update:

- campaign test status
- message matrix learnings
- score thresholds
- attribution assumptions

## Guardrails

Do not activate campaigns, increase budgets, launch sequences, or update CRM workflows without explicit human approval.

## Source Notes

Based on the Growth Engine campaign spec and DeployGTM drafts-not-sends operating rule.
