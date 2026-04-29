---
name: ops-icp-analysis
trigger: analyze ICP, find best customers, segment accounts, score ICP
---

## When To Use

Use this skill when building or revising the ideal customer profile for a client.

## Steps

1. Load the client brief and current ICP assumptions.
2. Pull available customer economics: revenue, gross profit, retention, deal size, sales cycle, discounts, and support burden.
3. Segment by profitability and strategic value, not only volume.
4. Identify top accounts, mid-tier profitable clusters, and false positives.
5. Enrich top accounts with web, LinkedIn, CRM, and client-provided context.
6. Extract common firmographic, technographic, behavioral, and psychographic patterns.
7. Create or update persona cards from transcripts and customer language.
8. Create `ICPDefinition` objects and initial scoring weights.
9. Score a sample account list and mark unknowns.
10. Write open questions back to the client workflow or handoff.

## Output

Write to:

- `0_research/icp-definitions/{client}-{segment}.yaml`
- `0_research/personas/{client}-{persona}.md`
- `0_research/score-snapshots/{client}-{date}.yaml`

## Epilogue

After analysis, update:

- account enrichment criteria
- exclusion rules
- signal definition hypotheses
- message matrix assumptions

## Source Notes

Based on DeployGTM scoring architecture and the Growth Engine ICP research stage: analyze existing data, enrich top accounts, extract personas, and build segmented prospect lists.
