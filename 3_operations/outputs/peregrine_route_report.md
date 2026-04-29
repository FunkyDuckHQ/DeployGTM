# Route Report: peregrine_space

Generated at: 2026-04-29

## Summary

- Enrich + campaign test: 1
- Selective enrichment or monitor: 1
- Exclude: 1

## Accounts

### Xona Space Systems

- ICP score: `92.0`
- Urgency score: `55.4`
- Route: `Enrich + campaign test`
- Next action: Enrich likely buyers and create a controlled message-market fit test.

Evidence:

- active_build_cycle: Active NewSpace build cycle likely creates demand for precision payload and timing/navigation components. (strength 74.87, confidence 0.74)
  Source: https://docs.google.com/document/d/1zz47YzPlD7Mz_BQOutgwNDWkgujtRgE609xICAag2Ws

### Kepler Communications

- ICP score: `80.0`
- Urgency score: `19.34`
- Route: `Selective enrichment or monitor`
- Next action: Monitor for urgency signals and enrich only if a timing event appears.

Evidence:

- product_fit: Satellite communications focus may align with optical communications components. (strength 59.55, confidence 0.58)
  Source: https://kepler.space

### Generic Aerospace Prime

- ICP score: `43.0`
- Urgency score: `0`
- Route: `Exclude`
- Next action: Exclude from current motion.

Evidence:

- procurement_risk: Large prime likely has high flight-heritage barrier and slower vendor approval. (strength 23.33, confidence 0.65)
  Source: https://docs.google.com/document/d/1zz47YzPlD7Mz_BQOutgwNDWkgujtRgE609xICAag2Ws

## Source Notes

- Generated from `3_operations/outputs/peregrine_score_snapshots.json`.
- Scoring logic lives in `3_operations/scripts/score_accounts.py`.
- Sandbox source context references the Peregrine Space working brief in Drive.
