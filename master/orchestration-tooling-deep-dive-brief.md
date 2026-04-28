# Orchestration Tooling Deep Dive Brief

## Purpose
This brief exists because orchestration was treated too casually in the architecture discussions.

The desired workflow is not theoretical:

> I should be able to communicate through Codex, Claude Code, GPT, Claude, or a command surface and say: "I am working with XYZ company." From there, the system should automate the buildout: pull company data, derive ICP strategies, score accounts, attach signals, push/update CRM records, generate alerts, and produce messaging ideas for a human rep to review and personally send.

This requires a serious tooling decision.

The question is not simply whether to use n8n, Mindra, Codex, Claude Code, or custom scripts. The question is which layer each tool should own.

## Current North Star
DeployGTM is a headless GTM command layer with persistent context and CRM-agnostic execution adapters.

The system must support:

1. Client bootstrap
2. Multi-segment ICP profile derivation
3. Account discovery
4. Account scoring
5. BirdDog account recommendations
6. BirdDog active account monitoring
7. Signal ingestion and urgency scoring
8. Contact enrichment
9. CRM writeback / preview
10. Message-market-fit test cell generation
11. Prompt asset ingestion from MD/JSON
12. Human-reviewed message suggestions
13. Sequencer / send handoff
14. Email reply/event sync
15. LinkedIn engagement-triggered tasks
16. Weekly action queues
17. Client-facing reports
18. Internal execution logs
19. Error handling / retries
20. Eventually warehouse / company brain / MCP layer

## Key Correction: One Client Does Not Mean One ICP
A client should not have one flat ICP.

Correct model:

```text
one client
  -> one ICP profile
    -> many ICP segments
    -> many personas
    -> many market/segment/persona/angle test cells
```

The tooling layer must support segment-level scoring and experiments, not a single monolithic ICP.

## Key Correction: BirdDog Is More Than Signal Enrichment
BirdDog can participate upstream and downstream.

BirdDog roles:

- account discovery / recommendations
- active monitored account list
- signal source
- urgency scoring input
- signal coverage assessment
- CRM update trigger

BirdDog daily updates may arrive directly through API/webhook/feed. If so, n8n should not be used just to poll BirdDog daily unless there is a specific routing reason.

## Execution Model Concern
n8n pricing is based on workflow executions. If n8n is used incorrectly, cost and complexity explode.

Correct idea:

```text
n8n/Mindra/top-level orchestrator executes workflow boundary
DeployGTM engine loops through accounts internally
```

Wrong idea:

```text
one n8n/Mindra execution per account per day
one n8n/Mindra execution per send/open/click event
```

For 1K accounts per client, expected orchestration usage should be modeled explicitly.

Planning hypothesis:

- if n8n is only a control plane: 75-200 executions/client/month/1K accounts
- if workflows are per account/event: 10K-300K+ executions/client/month

This needs verification.

## Tools To Evaluate

### Codex / Claude Code
Likely role:
- build and maintain deterministic engine
- local scripts
- schema
- adapters
- tests
- logs
- deliverable generation

Questions:
- Can the repo engine alone power production runs through scheduled CLI/API calls?
- What is the minimum wrapper needed around the scripts?
- How do we expose a command surface without overbuilding a UI?

### n8n
Potential role:
- boring scheduler
- webhook router
- retry wrapper
- notifications
- manual approval routing
- calling DeployGTM engine endpoints/scripts

Questions:
- What workflows should n8n own?
- What should never be done in n8n?
- What is execution count per 1K accounts/client/month under a sane design?
- Does the $20/2.5K execution plan support early production or only testing?
- How do we design this so n8n does not become the product?

### Mindra
Potential role:
- adaptive agent orchestration
- self-healing workflows
- multi-agent DAGs
- human-in-the-loop review
- anomaly detection/retry
- orchestrating repo engine components

Questions:
- Is Mindra better than n8n for GTM OS workflows?
- Which workflows need agent judgment vs deterministic scheduling?
- What is Mindra's cost/execution model for 1K accounts/client/month?
- Should Mindra orchestrate per client run, per segment, or per workflow type?
- How do we prevent one orchestration per account?

### Custom DeployGTM Engine
Likely role:
- core IP
- account loops
- scoring
- batching
- state
- CRM adapters
- BirdDog adapters
- report generation
- execution logs

Questions:
- Should the engine expose a CLI, local API server, or both?
- What jobs should exist as commands?
- What state store is needed first: JSONL, SQLite, Postgres?
- How does the engine preserve client state between runs?

### Warehouse / dlt / Redash / MCP Later
Potential role:
- Stage 2/3 once repeated cross-system joins justify it

Questions:
- When does local JSON/SQLite stop being enough?
- Does dltHub help with CRM/BirdDog/SuperSend data ingestion?
- When should Postgres enter?
- When should MCP expose a company brain?

## Required Analysis From Codex / Claude Code
Perform a deep dive and produce a written recommendation.

### Part 1: Current Repo State
Inspect current repo and answer:

- What scripts exist?
- What workflows are already implemented?
- Is the ICP refactor present?
- Is email_sync.py present and complete?
- What Makefile targets exist?
- What test commands pass/fail?
- Where is state currently stored?
- Where are outputs generated?

### Part 2: Workflow Inventory
List every workflow the product needs.

For each workflow, identify:

- trigger type: manual / scheduled / webhook / API / agent command
- frequency
- per-client or global
- account volume touched
- needs LLM judgment? yes/no
- needs deterministic code? yes/no
- needs human approval? yes/no
- should be handled by engine, n8n, Mindra, or later warehouse/MCP
- expected execution count if using n8n or Mindra

### Part 3: Execution Count Model
Build a realistic execution model for:

- 1 client / 1K accounts
- 7 clients / 10K accounts total
- 20 clients / 25K accounts total

Scenarios:

1. n8n as control plane only
2. n8n handling per-account loops
3. Mindra as client-run orchestrator
4. Mindra as per-segment orchestrator
5. custom engine with only notifications in n8n

Output should include monthly executions, likely cost tier, and risk.

### Part 4: Recommended Architecture
Recommend the tool ownership model.

Example output format:

```text
Codex/Claude Code builds:
- ...

DeployGTM engine owns:
- ...

n8n owns:
- ...

Mindra owns:
- ...

BirdDog owns:
- ...

CRM owns:
- ...

Do not use X for Y because...
```

### Part 5: Build Roadmap
Recommend an implementation sequence.

Must include:

- what to build locally first
- when to introduce n8n
- when to introduce Mindra
- when to introduce Postgres/warehouse
- when to introduce MCP
- how to test each service offer internally

## Non-Negotiables

- Do not make the orchestration tool the core IP.
- The DeployGTM engine must own scoring, schemas, batching, logs, and deliverables.
- The system must support multiple ICP segments per client.
- The system must work across CRMs.
- Dry-run mode must exist before live writes.
- Live CRM writes must have preview/approval path.
- Client-facing artifacts must be generated from the same state used internally.
- Human review remains required for high-priority outreach.

## Expected Final Answer
Codex/Claude should produce:

1. current repo state summary
2. workflow inventory table
3. execution count model
4. recommended tool ownership architecture
5. implementation roadmap
6. specific next command/build step

The immediate goal is not to pick the flashiest tool. The goal is to know what powers what, how often it runs, what it costs, and how it gets tested.
