# ADR-002: CRM Write Policy

Status: Accepted

Date: 2026-05-04

## Context

DeployGTM must project useful GTM intelligence into CRMs without creating unsafe autonomous writes.

## Decision

- HubSpot is the first real CRM adapter target because the repo already contains HubSpot scripts and tests.
- Salesforce is accepted only as read-only, constrained, or admin-partner-required in v1. No autonomous Salesforce writes in MVP.
- Attio is a likely second modern CRM adapter candidate after HubSpot because it fits modern CRM workflows and should share the same adapter contract.
- Clarify is an internal CRM and early-client CRM experiment. It is not a universal source of truth.
- No autonomous deletes.
- No autonomous owner, stage, amount, close date, forecast category, lifecycle stage, or lead-status changes in MVP.
- Every write path must support dry-run and approval-required modes before execution.
- Bulk writes require explicit approval and a generated write plan.

## Allowed By Default

- Meeting notes
- Summaries
- Action items
- Follow-up tasks
- Next-step text
- Non-destructive account/contact enrichment proposals

## Blocked In MVP

- Deal stage
- Owner
- Amount
- Close date
- Forecast category
- Lifecycle stage
- Lead status
- Destructive overwrites
- Delete/archive operations
- Bulk writes without approval

## Consequences

- CRM adapters must validate mappings and blocked fields before writing.
- `needs_review` mode creates approval items rather than writing.
- `execute` mode requires approval evidence and idempotency keys.
- Failed validation must create an error event.
