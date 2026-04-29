---
name: ops-weekly-growth-report
trigger: weekly growth report, report performance, summarize growth, investor update
---

## When To Use

Use this skill when summarizing market learning, execution learning, and business outcomes for a client or internal review.

## Steps

1. Pull latest score snapshots, execution results, campaign tests, CRM attribution notes, and engagement metrics.
2. Separate signal/account learning from channel performance.
3. Report ICP score movement and urgency score movement.
4. Report accounts enriched, contacts verified, messages approved, tests launched, replies, meetings, and opportunities.
5. Identify what changed in the ICP, signal model, message matrix, or route thresholds.
6. Call out manual review items and blocked decisions.
7. Recommend next week's operating moves.
8. Save report and update open loops.

## Output

Write to:

- `3_operations/reports/{client}-weekly-growth-report-YYYY-MM-DD.md`
- `3_operations/logs/` for structured execution notes when scripts exist

## Epilogue

After the report, update:

- client brief
- campaign test learnings
- signal definitions
- score thresholds
- next actions

## Source Notes

Based on DeployGTM reporting loop and the Growth Engine weekly growth report pattern.
