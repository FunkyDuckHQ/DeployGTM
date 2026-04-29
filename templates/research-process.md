---
type: research_process
name: ___
client: ___
last_updated: YYYY-MM-DD
---

# Research Process: ___

## Goal

One sentence describing what this process must discover.

## Good Result Definition

A good result includes:

- ___
- ___
- ___

A bad result looks like:

- generic market facts
- unsourced claims
- stale or irrelevant signals
- results that do not change an action

## Inputs

- target account: ___
- domain: ___
- segment: ___
- hypothesis: ___
- known ground truth examples: ___

## Search Patterns To Test

| Pattern | Query Template | Intended Signal | Quality Score | Consistency Score | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | `___` | ___ | _/5 | _/5 | ___ |
| 2 | `___` | ___ | _/5 | _/5 | ___ |
| 3 | `___` | ___ | _/5 | _/5 | ___ |

## Kill Patterns

Do not use results when:

- ___
- ___
- ___

## Extraction Rules

Extract:

- signal summary
- source URL
- source date
- exact evidence snippet or paraphrased evidence note
- why it matters
- ability-to-act evidence
- willingness-to-act evidence
- confidence
- recommended next action

## Stop Conditions

Stop when:

- a high-confidence signal is found
- 3 independent weak signals form a signal stack
- all validated patterns fail
- source quality is too low

## Output Shape

```yaml
research_run_id: ___
account_id: ___
research_process_id: ___
findings:
  - signal_type: ___
    summary: ___
    source_url: ___
    observed_at: YYYY-MM-DD
    confidence: 0.0
    ability_to_act_evidence: ___
    willingness_to_act_evidence: ___
    recommended_action: ___
```

## Source Notes

- Modeled on Mitchell Keller-style research process validation: ground truth examples, tested search patterns, kill lists, extraction specs, and stop conditions.
- Designed to feed DeployGTM SignalDefinition, Signal, ResearchRun, and ScoreSnapshot objects.
