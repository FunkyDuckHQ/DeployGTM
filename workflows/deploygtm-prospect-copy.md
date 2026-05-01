# DeployGTM Prospect Copy Workflow

## 1. Purpose

The DeployGTM Prospect Copy Workflow turns a target account/person into prospect-ready copy with a source trace and QA pass.

This workflow exists because copy is the visible output of the GTM system. If entity resolution, source loading, message strategy, or voice QA is loose, the final copy will feel generic or wrong even when upstream scoring is useful.

This is not an Octave workflow. Octave is an optional content adapter inside the workflow.

## 2. Trigger Phrases

Run this workflow when the operator says any of the following:

- `Run workflow: DeployGTM Prospect Copy`
- `write prospect copy`
- `build outreach for this account`
- `draft sequence for this person`
- `turn this account brief into copy`
- `use Octave to help with messaging`

## 3. Required Inputs

Minimum required inputs:

- target company
- target person or target persona
- canonical sources to use
- output format requested

Preferred inputs:

- company domain
- person title
- client ID
- relevant account score
- relevant urgency signal
- relevant source refs
- explicit `Use Octave for`
- explicit `Do not use Octave for`

## 4. Source Priority

Use sources in this order:

1. User-provided notes in the current request
2. Client working brief or Drive notes
3. Repo/client workspace files
4. Company website, LinkedIn, or public web
5. Octave enrichment after entity confirmation

Rules:

- Never let Octave be the first source of truth for entity identity.
- Octave can enrich or interpret context after the entity is confirmed.
- Do not let a vendor guess which company/person the operator means.
- If entity identity is ambiguous, stop and ask for clarification.

## 5. Workflow Stages

### Stage 1: Entity Resolution

Confirm:

- company name
- company domain or canonical account ID
- target person
- target title or role
- duplicate-name risk
- source proving the entity is correct

Pass condition:

- The company/person is tied to at least one trusted source.

Fail condition:

- The company/person could refer to multiple entities and no source resolves it.

### Stage 2: Canonical Context Loading

Load:

- client workspace context
- relevant account/person notes
- scoring output
- signal evidence
- Drive or repo working brief
- any user-provided notes

Pass condition:

- The context bundle includes enough source-backed facts to write without guessing.

Fail condition:

- The copy would require inventing the pain, person, signal, or why-now.

### Stage 3: Account/Person Brief

Create a brief before writing copy:

- Company
- Person
- Role
- Persona
- Current GTM situation
- Likely business problem
- Relevant signal
- Why now
- DeployGTM angle
- What not to overclaim
- Confidence
- Source refs

Pass condition:

- The brief states what is known, assumed, and not safe to claim.

### Stage 4: Message Strategy

Create the copy strategy:

- Primary hypothesis
- Pain angle
- Timing angle
- Credibility angle
- CTA
- Tone
- Banned framing
- Best offer fit
- Claims allowed
- Claims blocked

Pass condition:

- The strategy explains why this message should exist before drafting begins.

### Stage 5: Draft Generation

Use the selected content adapter only after Stages 1-4 pass.

If using Octave, provide tight instructions:

- Use this company/person brief.
- Use this message strategy.
- Use only the supplied facts.
- Draft the requested format.
- Do not introduce new facts.
- Do not resolve entities.
- Do not use brand-tag phrasing like `at DeployGTM`.
- Do not over-index on CRM unless CRM pain is actually supported.

Pass condition:

- Drafts are specific, source-grounded, and match the requested format.

### Stage 6: QA And Rewrite

Run QA after drafting:

- Is the company correct?
- Is the person correct?
- Is the pain specific?
- Is the copy too generic?
- Is there fake certainty?
- Is the subject usable?
- Does it sound like Matthew?
- Does it awkwardly mention DeployGTM?
- Does the CTA feel natural?
- Does every claim trace back to context?

Pass condition:

- Final copy passes QA or includes clear notes on what needs human review.

## 6. Context Bundle Schema

Use `templates/context-bundle.schema.json`.

Required sections:

- `workflow`
- `client`
- `target_company`
- `target_person`
- `entity_resolution`
- `canonical_sources`
- `account_person_brief`
- `message_strategy`
- `adapter_instructions`
- `qa`
- `source_trace`

## 7. Message Strategy Template

Use `templates/message-strategy.md`.

Do not draft copy until the strategy exists.

## 8. Octave Usage Rules

Use Octave for:

- persona interpretation
- message angle suggestions
- sequence drafting
- playbook/value prop inspiration
- content findings if the client already has Octave context

Do not use Octave for:

- entity resolution
- factual guessing
- choosing source of truth
- inventing signals
- overriding client workspace context
- final QA in Matthew's voice

If Octave conflicts with canonical context, canonical context wins.

## 9. Copy Output Formats

Supported outputs:

- one-off email
- 3-email sequence
- LinkedIn connection note
- LinkedIn follow-up
- call opener
- call prep
- message matrix
- source trace and QA notes only

Every output must include:

- final recommended version
- alternates if requested
- source trace
- QA notes
- claims used
- claims blocked

## 10. Voice QA Checklist

Use `templates/copy-qa-checklist.md`.

The QA pass should be separate from draft generation.

## 11. Banned Phrases

Default banned phrases:

- `at DeployGTM`
- `I hope this finds you well`
- `just checking in`
- `quick question`
- `revolutionize`
- `game-changing`
- `cutting-edge`
- `AI-powered GTM engine`
- `signal layer` as unexplained jargon
- `unlock growth`
- `supercharge your pipeline`
- `we help companies like yours`
- fake familiarity such as `I noticed` without a source

Client-specific banned phrases can be added in the context bundle.

## 12. Final Response Format

Return:

```text
Entity Resolution
- Company:
- Person:
- Confidence:
- Source:

Brief
- Current situation:
- Likely problem:
- Relevant signal:
- Why now:
- What not to overclaim:

Message Strategy
- Primary hypothesis:
- Pain angle:
- Timing angle:
- Credibility angle:
- CTA:

Final Copy
...

QA Notes
- Passed:
- Rewritten:
- Needs human review:

Source Trace
- ...
```

## Operator Command Format

Use this exact command shape:

```text
Run workflow: DeployGTM Prospect Copy

Target company:
Target person:
Canonical sources:
Use Octave for:
Do not use Octave for:
Output:
```

Example:

```text
Run workflow: DeployGTM Prospect Copy

Target company: Peregrine Space
Target person: Tyler Ritz
Canonical sources: Drive working brief + repo notes
Use Octave for: persona interpretation, message angles, sequence drafting
Do not use Octave for: entity resolution or factual guessing
Output: 3-email sequence, source trace, QA notes, final recommended version
```

## Source Notes

- Strategy source: user-provided Copy Workflow Orchestrator context, shared April 30, 2026.
- Architecture dependency: copy workflow sits after client workspace, validation, scoring, and context loading.
- Adapter principle: Octave is an optional content adapter, not the operating system.
