---
name: research-process-builder
trigger: build a research process, validate research, create search patterns, find alpha signals
---

## When To Use

Use this skill when the operator needs a repeatable research process instead of one-off browsing.

Examples:

- find alpha signals for a client
- build a research process for a specific buying trigger
- validate whether a web signal can be detected reliably
- create account research instructions for Claude, Clay, BirdDog, or browser agents

## Steps

1. State the research goal in one sentence.
2. Define what a good result looks like.
3. Gather 3 to 5 known positive and negative examples if available.
4. Draft search patterns and source types.
5. Test patterns across multiple account tiers.
6. Score each pattern for quality, consistency, freshness, and actionability.
7. Create kill patterns for bad or misleading results.
8. Define extraction rules and stop conditions.
9. Save the process using `templates/research-process.md`.
10. Route validated findings into SignalDefinition, Signal, and ScoreSnapshot objects.

## Output

Write to:

- `0_research/research-processes/{client}-{process-name}.md`
- `0_research/signal-definitions/{client}-{signal-name}.yaml` when a signal becomes monitorable

## Epilogue

After each run, ask:

- Did this process find evidence that changes a GTM action?
- Which patterns failed?
- Which signal definitions should be created or updated?
- Should BirdDog monitor this signal?

## Source Notes

Modeled on Mitchell Keller's research-process-builder method: ground truth, tested patterns, quality/consistency scoring, kill lists, extraction rules, and stop conditions.
