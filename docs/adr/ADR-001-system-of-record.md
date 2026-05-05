# ADR-001: System Of Record Boundaries

Status: Accepted

Date: 2026-05-04

## Context

DeployGTM is becoming a modular GTM operating system. It needs multiple memory and execution surfaces without letting any vendor become the hidden source of truth.

## Decision

- GitHub is the canonical human-readable engineering and process context. It owns code, schemas, ADRs, playbooks, templates, durable project artifacts, and implementation history.
- Google Drive is the raw client intake and collaboration layer. It owns messy documents, transcripts, screenshots, working docs, and client-shareable materials before canonical promotion.
- Postgres is the transactional source of truth for production state. It owns tenants/workspaces, canonical objects, execution receipts, adapter runs, approvals, idempotency keys, source evidence, and audit logs.
- CRM systems are external customer business-system projections. They receive approved account/contact/task/note/deal projections; they do not own DeployGTM execution state.
- n8n and Mindra are workflow/orchestration glue, not sources of truth. n8n may schedule, route webhooks, trigger commands, handle approvals, and notify humans. Mindra may be evaluated for adaptive or agentic orchestration where workflows need judgment, self-healing, or multi-step coordination. Neither owns canonical execution state.
- Clay, RevyOps, Airtable, Octave, and similar tools are optional sidecars. They may hold useful data, GTM primitives, enrichment context, or workspace views, but they do not own canonical execution state.

## Consequences

- Every production workflow must write its authoritative execution record to Postgres.
- Vendor IDs are preserved as external references, not primary identity.
- File artifacts can remain useful and versioned, but production truth cannot depend on local-only files.
- Sidecars can accelerate workflows without dictating the schema.

## Non-Goals

- This does not choose a managed Postgres provider.
- This does not make DeployGTM a CRM replacement.
