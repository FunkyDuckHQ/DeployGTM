# ADR-004: Conversation Intelligence Layer

Status: Accepted

Date: 2026-05-04

## Context

Meeting and call tools can capture transcripts, summaries, recordings, and action items. DeployGTM needs this context but must not let recorder tools directly mutate high-risk CRM fields.

## Decision

- Meeting/call tools are capture sources, not the DeployGTM source of truth.
- Postgres owns normalized meeting intelligence.
- CRM owns customer business records.
- DeployGTM creates CRM update proposals from meeting intelligence.
- Recorder tools must not directly write high-risk CRM fields through DeployGTM.
- All extracted insights require transcript/source evidence.

## Allowed Flow

```text
meeting source
-> transcript/recording/summary capture
-> normalized meeting intelligence in Postgres
-> source-evidenced insight/action extraction
-> CRM update proposal
-> approval
-> CRM task/note/next-step write
```

## Blocked Flow

```text
meeting source -> autonomous deal stage/owner/amount/forecast write
```

## Consequences

- Meeting intelligence adapters must expose reads and proposals, not unsafe writes.
- CRM update proposals require approval.
- Extracted insights without source evidence are invalid.
