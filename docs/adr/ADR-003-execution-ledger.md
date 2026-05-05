# ADR-003: Execution Ledger

Status: Accepted

Date: 2026-05-04

## Context

Headless execution is not trustworthy unless every workflow, adapter call, write, and exception leaves a durable receipt.

## Decision

- Every workflow emits an `ExecutionResult`.
- Every adapter call emits an `AdapterRun`.
- Every write uses an `IdempotencyKey`.
- Every source fact has `SourceEvidence`.
- Partial failures produce exception reports.
- Silent writes are prohibited.

## Ledger Objects

- `ExecutionResult`: workflow-level result.
- `AdapterRun`: single adapter operation result.
- `ApprovalItem`: human review record for risky or pending actions.
- `IdempotencyKey`: write dedupe and retry safety.
- `ErrorEvent`: structured failure record.
- `SourceEvidence`: source refs for facts and extracted claims.

## Consequences

- A workflow can succeed partially only if exceptions are explicit.
- Adapter methods return ledger-linked results.
- Production reports and client deliverables must be generated from the same state used by execution.
- Runtime tools such as n8n may trigger workflows, but Postgres owns the receipts.
