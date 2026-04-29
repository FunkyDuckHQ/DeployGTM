# Content Adapter Contract

## Purpose

The Content Adapter turns canonical GTM context into usable messaging artifacts.

It lets DeployGTM use different messaging engines without changing the core system. V1 can be Claude reading markdown playbooks from GitHub. Later implementations can use Octave, Clay, HubSpot AI, or a client-owned content system.

The core system should never call a vendor content API directly. It should call this contract and receive canonical output.

## Design Principle

DeployGTM owns the schema. Vendors own execution details. Adapters translate between the two.

This keeps Octave optional. If Octave is useful, it becomes an implementation of this contract. If it is too expensive, unavailable, or client-specific, the same contract can be backed by Drive/GitHub docs and Claude-generated output.

## Canonical Inputs

### Account

Expected fields:

- `id`
- `name`
- `domain`
- `industry`
- `segment`
- `size`
- `geo`
- `source`
- `signals`
- `crm_refs`

### Contact

Expected fields:

- `id`
- `account_id`
- `first_name`
- `last_name`
- `title`
- `role`
- `seniority`
- `email`
- `linkedin_url`
- `source`
- `crm_refs`

### Signal

Expected fields:

- `id`
- `account_id`
- `contact_id`
- `type`
- `summary`
- `source_url`
- `observed_at`
- `confidence`
- `evidence`

### Persona

Expected fields:

- `id`
- `name`
- `role_family`
- `seniority`
- `goals`
- `pains`
- `objections`
- `buying_triggers`
- `preferred_language`
- `avoid_language`

### Playbook

Expected fields:

- `id`
- `name`
- `motion`
- `target_segments`
- `primary_offer`
- `qualification_rules`
- `message_angles`
- `proof_points`
- `cta_options`
- `disqualification_rules`

### ValueProp

Expected fields:

- `id`
- `name`
- `target_personas`
- `pain`
- `promise`
- `mechanism`
- `proof`
- `differentiators`
- `risk_reversal`

## Canonical Outputs

### OutreachDraft

Expected fields:

- `id`
- `account_id`
- `contact_id`
- `playbook_id`
- `persona_id`
- `channel`
- `subject`
- `body`
- `cta`
- `personalization_basis`
- `signal_basis`
- `tone_profile`
- `claims_used`
- `compliance_notes`
- `confidence`
- `created_at`
- `adapter_metadata`

### CallPrep

Expected fields:

- `id`
- `account_id`
- `contact_id`
- `playbook_id`
- `persona_id`
- `meeting_goal`
- `opening_context`
- `likely_pains`
- `discovery_questions`
- `objections_to_prepare_for`
- `proof_points_to_use`
- `recommended_cta`
- `adapter_metadata`

### ContentFinding

Expected fields:

- `id`
- `source_type`
- `source_ref`
- `finding_type`
- `summary`
- `evidence`
- `impacted_personas`
- `impacted_playbooks`
- `recommended_update`
- `confidence`
- `observed_at`
- `adapter_metadata`

## Required Methods

### `generate_outreach_draft`

Creates a canonical outreach draft from account, contact, signal, persona, playbook, and value prop context.

Input:

```json
{
  "account": "Account",
  "contact": "Contact",
  "signals": ["Signal"],
  "persona": "Persona",
  "playbook": "Playbook",
  "value_props": ["ValueProp"],
  "channel": "email | linkedin | call_script | other",
  "constraints": {
    "max_words": 120,
    "tone": "direct",
    "required_cta": "optional string",
    "blocked_claims": ["string"]
  }
}
```

Output:

```json
{
  "draft": "OutreachDraft"
}
```

### `generate_call_prep`

Creates call prep for a target contact and account.

### `generate_message_matrix`

Creates channel, persona, signal, objection, proof, CTA, and test variants from canonical strategy objects.

### `extract_content_findings`

Extracts reusable messaging learnings from call transcripts, email replies, notes, or CRM activity.

## Optional Methods

### `qualify_messaging_fit`

Scores whether a target account/contact fits a playbook before drafting.

### `suggest_library_updates`

Turns `ContentFinding` records into proposed changes to personas, playbooks, or value props.

## Adapter Implementations

### `ClaudeMarkdownContentAdapter`

Recommended V1.

Source of truth:

- GitHub markdown files
- Drive intake docs exported or synced into canonical objects
- local canonical schema

Strengths:

- lowest vendor lock-in
- works without Octave API access
- easy to inspect and version
- best match for the current adapter-first architecture

Limitations:

- requires discipline around file structure and schema validation
- does not automatically learn from calls unless transcripts are routed into the system

### `OctaveContentAdapter`

Possible later implementation.

Source of truth:

- Octave personas
- Octave products
- Octave segments
- Octave playbooks
- Octave value props
- Octave findings and events

Strengths:

- purpose-built messaging library
- useful if clients already manage messaging in Octave
- potentially strong feedback loop from calls and emails

Limitations:

- requires paid API access
- uses a vendor object model that must be mapped into DeployGTM canonical objects
- should not become the source of truth for the whole GTM system

## Mapping Notes For Octave

Suggested translation:

- Octave persona -> `Persona`
- Octave playbook -> `Playbook`
- Octave value proposition -> `ValueProp`
- Octave generated email -> `OutreachDraft`
- Octave call prep -> `CallPrep`
- Octave findings/events -> `ContentFinding`

The adapter should preserve raw Octave IDs in `adapter_metadata`, while core workflows continue using DeployGTM canonical IDs.

## Validation Rules

An adapter response is valid only if:

- it returns canonical objects, not vendor-native payloads
- it cites the signals and value props used to generate the message
- it does not invent evidence, customer names, metrics, or claims
- it includes confidence and compliance notes when claims are uncertain
- it keeps vendor IDs inside `adapter_metadata`
- it can fail gracefully with a structured error

## Error Shape

```json
{
  "error": {
    "code": "CONTENT_ADAPTER_UNAVAILABLE",
    "message": "Octave API access is not available for this workspace.",
    "retryable": false,
    "vendor": "octave",
    "raw_ref": "optional log or request id"
  }
}
```

Suggested error codes:

- `CONTENT_ADAPTER_UNAVAILABLE`
- `CONTENT_ADAPTER_AUTH_FAILED`
- `CONTENT_ADAPTER_RATE_LIMITED`
- `CONTENT_ADAPTER_INVALID_INPUT`
- `CONTENT_ADAPTER_LOW_CONFIDENCE`
- `CONTENT_ADAPTER_VENDOR_ERROR`

## Recommended Build Sequence

1. Add `Persona`, `Playbook`, and `ValueProp` to the canonical schema.
2. Store V1 messaging library files in GitHub as markdown or YAML.
3. Implement `ClaudeMarkdownContentAdapter`.
4. Generate `OutreachDraft` from canonical account, contact, signal, persona, playbook, and value prop inputs.
5. Add transcript/reply ingestion later and emit `ContentFinding`.
6. Only build `OctaveContentAdapter` after API access exists and Octave is a client-required messaging system.

## Decision

Do not treat Octave as the system of record.

Treat Octave as a possible content adapter implementation.

The durable product decision is to model messaging as canonical DeployGTM objects first. That preserves interchangeable APIs, keeps Drive/GitHub useful as the low-cost implementation, and allows Octave to slot in later without reshaping the architecture.
