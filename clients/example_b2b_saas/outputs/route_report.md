# Route Report: example_b2b_saas

Generated at: 2026-04-30

## Summary

- Enrich + campaign test: 1
- Hold or monitor: 1

## Accounts

### Northstar CRM Co

- ICP score: `88.0`
- Urgency score: `59.96`
- Route: `Enrich + campaign test`
- Next action: Enrich likely buyers and create a controlled message-market fit test.

Evidence:

- crm_migration: CRM administrator hiring suggests workflow cleanup or migration work is active. (strength 71.39, confidence 0.7)
  Source: https://example.com/northstar/jobs/crm-admin

### Flatfile Ops

- ICP score: `57.0`
- Urgency score: `15.03`
- Route: `Hold or monitor`
- Next action: Hold until more evidence appears.

Evidence:

- sales_hiring: Hiring first account executive suggests early sales process buildout. (strength 30.36, confidence 0.55)
  Source: https://example.com/flatfile/jobs/ae

## Source Notes

- Generated from `clients/example_b2b_saas/outputs/score_snapshots.json`.
- Scoring logic lives in `3_operations/scripts/score_accounts.py`.
- Source context should live in the active client workspace.
