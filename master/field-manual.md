# GTM Engineering Field Manual — Operating Reference

## One sentence to remember
Build a system that notices what matters, knows what to do next, acts in the right channel, and writes the result back so the next action gets smarter.

## The Seven Layers (build in this order)

1. **Source of truth** — CRM, product events, account/contact data. Nothing works if this is dirty.
2. **Signal layer** — Hiring changes, funding, content engagement, competitor gaps, intent signals, alpha signals.
3. **Scoring + intelligence** — ICP fit, research, pain hypothesis, objection extraction, summarization.
4. **Activation layer** — Sequences, outbound tasks, inbound routing, nurture flows.
5. **Recapture loop** — Website revisit, email reply, meeting booked, score increase.
6. **Memory + measurement** — CRM updates, dashboards, experiment results, revenue attribution.
7. **Ops reliability** — Error handling, logs, ownership, data QA, manual review thresholds.

## Design Rule
Do not build isolated automations. Build a revenue operating system: signal in, decision made, action taken, feedback captured, system improved.

## Anti-Patterns (never do these)
- Treating GTM engineering as "lead gen but with better software"
- Optimizing reply rate as the only truth metric
- Buying tools before defining the constraint, ICP, or business outcome
- Spamming a huge TAM when the better move is to shrink TAM and improve fit
- Building workflows on top of bad source-of-truth data
- Assuming AI output is trustworthy because the prompt feels smart

## Default Problem-Solving Prompt
Given this GTM problem, identify the bottleneck, map the data flow, propose the smallest closed-loop system that could improve revenue, name the exact signals and fields required, specify what gets human review, and define how success will be measured.
