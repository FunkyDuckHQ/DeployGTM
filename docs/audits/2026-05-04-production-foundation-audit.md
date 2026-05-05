# DeployGTM Production Foundation Audit

Date: 2026-05-04

Scope: verified implementation depth in `FunkyDuckHQ/DeployGTM` before adding the production foundation.

## Summary

DeployGTM already has a runnable no-write Signal Audit spine:

```text
intake -> context pack -> ICP strategy -> signal strategy -> account matrix -> CRM push plan -> deliverable
```

The production nervous system is still mostly planned rather than implemented:

```text
durable state -> execution receipts -> verified adapters -> runtime orchestration -> approval queue -> feedback loop -> observability -> governed CRM writes
```

## Existing And Real

- `scripts/platform/intake.py`: creates customer outcome intake and project files.
- `scripts/platform/context_pack.py`: assembles project/brain/transcript context into source-traced principles.
- `scripts/platform/icp_strategy.py`: creates deterministic ICP strategy artifacts from context.
- `scripts/platform/signal_strategy.py`: creates signal strategy and BirdDog-ready manifest.
- `scripts/platform/account_matrix.py`: creates account matrix with ICP, urgency, engagement, confidence, and activation scores.
- `scripts/platform/crm_push_plan.py`: creates dry-run CRM push plan artifacts.
- `scripts/platform/deliverable.py`: compiles Signal Audit deliverable markdown and CSV.
- `scripts/email_sync.py`: ingests SuperSend/email-style events into account scoring; no sending.
- `scripts/transcript.py`: processes pasted/file transcripts with Claude and persists summaries under `projects/<client>/transcripts/`.
- `scripts/hubspot.py`: direct HubSpot script for custom fields, company/contact upsert, deal helpers; write paths require explicit command usage and/or prompts.
- `scripts/platform/adapters/hubspot_adapter.py`: thin wrapper over direct HubSpot functions for company/contact sync.
- `scripts/platform/adapters/clarify_adapter.py`: dry-run shell only; live writes raise.
- Tests exist for platform dry-run flow, adapters, context pack, transcript persistence, email sync, and local API harness.
- `Makefile` exposes the current operator commands.

## Stubbed, Planned, Or Thin

- Durable database/state: planned in docs; runtime state is JSON/Markdown/JSONL files.
- Execution results: documented, but not uniformly emitted by every workflow.
- AdapterRun: not implemented as a universal record.
- Approval queue: documented, but no canonical model or queue table.
- Idempotency keys: documented, not implemented.
- SourceEvidence: context pack has evidence snippets, but no universal canonical model.
- Salesforce adapter: referenced in docs only; no implementation.
- Attio adapter: referenced in docs only; no implementation.
- Clarify CRM: dry-run shell only.
- Sybill/Fathom/meeting intelligence: referenced as transcript/call-adjacent concepts only; no adapters.
- Google Drive: MCP/intake role documented; no canonical GTM context adapter in code.
- Octave: documented as optional brain/content sidecar; no live adapter.
- n8n: specs only; no production workflow implementation.
- Enrichment vendors: Apollo exists as legacy direct script; no general enrichment adapter contract.
- Signal vendors: BirdDog script exists, but API capabilities remain unverified.
- Sequencers: HubSpot sequence templates and email event sync exist; no general sequencer adapter and no sending.

## Unclear Or Needs Verification

- BirdDog API support for creating signal definitions and recommended account fetch.
- Clarify API/MCP access, schema introspection, and write capability.
- HubSpot field mappings for production-safe account/contact/task/note writes beyond current script fields.
- Whether meeting intelligence sources should include Sybill, Fathom, Clarify, manual transcript upload, or all of them.
- Whether Postgres should be self-hosted, Supabase/Neon managed Postgres, or another managed Postgres surface.

## Makefile Commands Reviewed

- Setup and tests: `install`, `env`, `api-test`, `test`
- Current operations: `daily`, `platform-intake`, `context-pack`, `platform-strategy`, `platform-signals`, `platform-matrix`, `platform-crm-plan`, `platform-deliverable`, `signal-audit-dry-run`
- Legacy pipeline: `signals`, `batch`, `push-hubspot`, `followup-*`, `transcript`
- Runtime: n8n is documented but not wired as a Make target for production execution.

## Env Vars Reviewed

- `ANTHROPIC_API_KEY`
- `APOLLO_API_KEY`
- `HUBSPOT_ACCESS_TOKEN`
- `BIRDDOG_API_KEY`
- `OCTAVE_API_KEY`
- `GDRIVE_CREDENTIALS_FILE`
- `GDRIVE_INTAKE_FOLDER_ID`
- Local harness vars including `CRM_PROVIDER`, `CRM_BASE_URL`, `LOCAL_API_ALLOW_WRITE`

## Direction

Add the production foundation without broad feature work:

- ADRs for system-of-record, CRM write policy, execution ledger, conversation intelligence, and GTM context sources.
- Canonical model layer.
- Postgres-compatible migration.
- Adapter contracts and explicit stubs.
- Safe HubSpot skeleton.
- CRM write policy.
- Tests that prove evidence, dry-run, approval, and blocked-field behavior.
