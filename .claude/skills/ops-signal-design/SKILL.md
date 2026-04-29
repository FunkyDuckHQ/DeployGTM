---
name: ops-signal-design
trigger: design signals, alpha signals, BirdDog signals, urgency score, why now
---

## When To Use

Use this skill when converting client-specific knowledge into monitorable signals and urgency scoring logic.

## Steps

1. Load the client brief, ICP definition, personas, and existing signal notes.
2. Ask what the client knows that competitors cannot easily buy.
3. Identify events that indicate ability to act, willingness to act, timing, pain, budget, risk, or strategic fit.
4. Separate generic signals from client-specific alpha signals.
5. Define source systems and detection methods.
6. Create signal decay assumptions.
7. Define ICP and urgency scoring impact.
8. Draft BirdDog setup notes or equivalent SignalAdapter instructions.
9. Validate with known positive and negative accounts.
10. Save signal definitions and research processes.

## Output

Write to:

- `0_research/signal-definitions/{client}-{signal}.yaml`
- `0_research/research-processes/{client}-{signal}-research.md`

## Epilogue

After signal design, update:

- urgency scoring weights
- BirdDog monitoring recommendations
- target account list criteria
- manual sales review triggers

## Source Notes

Uses Josh Whitfield / GTM Engineer School E4 principles and Clay-style alpha signal thinking: data is context, context is leverage, and the best signals are client-specific and actionable.
