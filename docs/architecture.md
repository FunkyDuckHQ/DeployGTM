# DeployGTM Architecture

## Position

DeployGTM is a callable GTM engine for service-led delivery. It helps an operator turn messy GTM context into scored accounts, explainable signals, CRM-ready plays, message tests, and reporting loops.

It is not a narrow SaaS app, Clay clone, outbound agency workflow, or MCP-first system.

The core loop is:

```text
ingest -> normalize -> score -> explain -> activate -> learn
```

## Architecture Layers

### 1. Core Data Model

The canonical model owns the internal truth:

- clients
- accounts
- contacts
- opportunities
- personas
- products and services
- ICP criteria
- signals
- scores
- plays
- playbooks
- workflows
- experiments
- CRM field mappings
- reports
- assumptions
- learnings

External systems map into this model through adapters. They do not define it.

### 2. Connector And Vendor Layer

Vendor adapters translate between DeployGTM objects and external systems:

- Clarify, HubSpot, Salesforce, Attio
- Google Drive, Docs, Sheets, Gmail
- Apollo, Clay, BirdDog, Mantis, SuperSend, Octave
- call transcript systems
- public web and research providers

The adapter contract is more important than any single vendor. Vendors should be swappable underneath the workflow. Clarify is the preferred CRM/workspace candidate for DeployGTM-operated work once access is confirmed; HubSpot is compatibility support for clients already living there.

### 3. Deterministic Function Layer

Deterministic functions handle repeatable operations:

- `ingest_company()`
- `normalize_account()`
- `calculate_icp_score()`
- `calculate_urgency_score()`
- `write_to_crm()`
- `create_task()`
- `fetch_transcript()`
- `create_playbook()`
- `run_sequence_test()`
- `log_learning()`

This layer should be boring, inspectable, testable, and source-aware.

### 4. Reasoning Layer

LLMs are used where judgment is required:

- summarize calls
- extract pains and objections
- infer buying committee
- explain scores
- recommend plays
- draft outreach
- classify replies
- update assumptions

LLMs do not own the data model, execution state, or writeback rules.

### 5. Interface Layer

Interfaces sit around the engine:

- API for product and integration use
- CLI for operator and Codex/Claude workflows
- webhooks for event-driven automation
- MCP for AI workspace access
- lightweight UI for visibility and review

The API should be the backbone. MCP can expose capabilities later, but it should not become the operating system.

Every API/CLI integration should support the same execution pattern: validate environment, describe capabilities, read, plan, dry-run, write with confirmation, sync events, and save receipts.

### 6. Observability And Memory Layer

Every run should leave behind enough context to trust and improve the system:

- logs
- traces
- score changes
- signal changes
- assumptions
- client preferences
- failed jobs
- artifacts
- learnings
- human overrides

Drive remains raw intake. GitHub remains durable canonical context. CRM remains the client-facing system of record when appropriate.

## Event Pattern

```text
Event happens
-> webhook received
-> data validated
-> deterministic worker runs
-> LLM used only where reasoning is required
-> output written to CRM, Drive, docs, or vendor system
-> trace logged
-> learning captured
```

## Operator Rules

- Diagnose before automating.
- Use tools to support the GTM motion, not define it.
- Make scores explainable or do not use them.
- Treat signals as action triggers, not decorations.
- Keep outbound as a feedback loop.
- Separate what is known, assumed, testable, and learned.
- Preserve human approval gates for judgment-heavy work.

## Source Notes

- Strategy source: user-provided DeployGTM Strategy / Product / Architecture Condensed Brief, shared April 30, 2026.
- Existing repo sources: [master/build-spec.md](../master/build-spec.md), [master/adapter-contracts.md](../master/adapter-contracts.md), [master/canonical-schema.md](../master/canonical-schema.md), and [master/design-principles.md](../master/design-principles.md).
- Clarify/API/CLI strategy source: [docs/clarify-api-cli-strategy.md](clarify-api-cli-strategy.md).
- Prior external concepts referenced in the brief: Josh Whitfield / GTM Engineer School E4 principles, Clay's GTM alpha and custom signal concepts, and Kellen's service-business positioning feedback.
