# DeployGTM Copy Quality Standard

## Purpose

Copy is the last mile of the GTM system. If it is wrong, generic, overconfident, or awkward, every upstream component looks fake.

This standard defines what good looks like before a prospect-facing message can be trusted.

## Quality Bar

Good DeployGTM copy is:

- Correct about the company, person, role, and context.
- Specific because the context supports specificity, not because the writer invented detail.
- Built from a clear message strategy before drafting starts.
- Useful to the buyer in the first read.
- Direct, practical, and restrained.
- Honest about uncertainty.
- Easy to reply to.
- Traceable back to source material.

Bad DeployGTM copy is:

- Generic agency copy with the prospect name swapped in.
- Confident about unsupported facts.
- Built around a vendor, tool, or internal DeployGTM concept instead of the buyer's problem.
- Overwritten, breathless, or jargon-heavy.
- Too clever to be useful.
- A sequence of claims without a reason to act.

## Scoring Rubric

Every copy packet should be scored out of 100.

| Dimension | Points | What It Measures |
| --- | ---: | --- |
| Entity correctness | 20 | The company/person/role are resolved and not guessed. |
| Source-grounded specificity | 20 | Specific claims trace to trusted sources. |
| Pain and trigger relevance | 15 | The message maps to a real business problem, signal, or timing reason. |
| Message strategy fit | 15 | The copy follows the approved hypothesis, angle, CTA, and blocked claims. |
| Voice fit | 10 | It sounds direct, operator-led, and practical. |
| CTA quality | 10 | The ask is low-friction, relevant, and easy to answer. |
| Brevity and readability | 5 | The message is tight enough for a busy buyer. |
| Risk control | 5 | The copy avoids fake certainty, sensitive claims, and unsafe personalization. |

## Decision Thresholds

- `pass`: 85-100
- `rewrite`: 70-84
- `fail`: 0-69

A copy packet can score above 85 and still fail if it triggers a hard fail condition.

## Hard Fail Conditions

Reject the packet if any of these are true:

- Wrong company or person.
- Entity identity is unresolved or ambiguous.
- Any factual claim lacks a source reference.
- The message invents a pain, trigger, funding event, technology stack, hiring plan, or business initiative.
- Octave or another content adapter was used for entity resolution.
- The copy includes sensitive personalization that requires human review.
- The copy uses a banned phrase from the workflow or client context.
- The message is generic enough that it could be sent to any company in the segment.
- The CTA asks for a meeting before the message earns it.

## Matthew Voice Standard

The default operator voice is:

- Direct without being blunt for sport.
- Specific without being creepy.
- Practical instead of grand.
- Curious, not performative.
- Confident about the process, careful about the prospect's facts.

It should avoid:

- "At DeployGTM" brand-tag sentences.
- SaaS launch copy.
- AI jargon as the lead.
- Unexplained "signals" language.
- Fake familiarity.
- Long setup before the actual point.

## Required Copy Packet

Prospect-facing copy should be delivered as a copy packet, not just text.

The packet must include:

- target company and person
- context bundle reference
- message strategy
- final copy
- claims used
- source trace
- QA score
- hard fail status
- reviewer notes

Use `templates/copy-packet.schema.json` for structure and `templates/copy-quality-rubric.json` for scoring.

## Human Review Triggers

Require human review when:

- The score is below 85.
- The packet includes a hard fail flag.
- The target is a senior executive, investor, partner, journalist, or sensitive account.
- The message references legal, financial, medical, employment, security, defense, or regulated-market claims.
- The source trace includes unverified or low-confidence evidence.
- The message would be sent at scale.

## Operating Rule

Do not trust final copy because it "sounds good."

Trust it only when it is entity-correct, source-grounded, strategically coherent, and passes QA.
