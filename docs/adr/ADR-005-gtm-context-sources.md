# ADR-005: GTM Context Sources

Status: Accepted

Date: 2026-05-04

## Context

DeployGTM needs context from Google Drive, GitHub, CRM, transcripts, manual inputs, vendors, and potentially Octave.

## Decision

- Google Drive is the raw messy memory, intake, and collaboration layer.
- Octave is an optional structured GTM brain/context sidecar.
- When enabled, Octave may own reusable GTM primitives such as ICPs, personas, use cases, proof points, competitors, playbooks, and messaging concepts.
- Octave does not own execution receipts, approvals, CRM mappings, tenant data, or audit logs.
- DeployGTM/Postgres owns canonical operational truth.

## Supported Source Types

```text
google_drive | octave | github | crm | manual | transcript | vendor
```

## Consequences

- GTM context adapters extract primitives and preserve source refs.
- Context sidecars can be swapped without changing execution state.
- Google Drive content can be raw/collaborative without becoming canonical execution state.
- Octave can improve content quality without owning execution.
