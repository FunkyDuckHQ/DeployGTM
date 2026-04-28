# Internal Testing and Deliverables Plan

## Purpose
This document defines how to test DeployGTM's service offerings internally and how to store, package, and hand deliverables to clients.

The immediate problem:

- The service offers are now defined.
- The architecture is mostly defined.
- The build state may be partially complete across Codex, Claude Code, and GitHub.
- I still need a way to test the system for myself before selling it.
- I need a mechanism to store outputs and give clients useful artifacts.

This document turns the services into testable internal workflows.

## First Principle
Every service offering must be testable internally before it is sold.

A service is not real until I can run a dry test and produce the same type of artifact a client would receive.

## Source of Truth Split

### GitHub
Use GitHub for canonical system assets:

- service playbooks
- templates
- scripts
- schemas
- scoring profiles
- internal test fixtures
- generated markdown outputs that should be versioned

### Google Drive
Use Drive for shareable client-facing artifacts:

- memos
- reports
- scored account exports
- PDFs
- working docs
- client folders

### CRM
Use CRM for operational account/contact/task state:

- companies
- contacts
- fit score
- urgency score
- tier
- signal summary
- tasks
- next actions

### Local / SQLite / Logs
Use local storage for execution state and testing:

- event logs
- touch logs
- email event sync
- dry-run outputs
- execution results

## Recommended Project Folder Structure
Every client or internal test client should follow this structure:

```text
projects/<client>/
  context.md
  handoff.md
  open-loops.md

  data/
    icp_profile.json
    account_matrix.json
    contacts.json
    signals.json
    monitored_accounts.json
    campaign_matrix.json
    response_events.jsonl
    execution_log.jsonl

  outputs/
    audit/
      YYYY-MM-DD_signal-audit.md
      YYYY-MM-DD_scored-accounts.csv
      YYYY-MM-DD_signal-coverage.csv

    message-market-fit/
      YYYY-MM-DD_test-cells.md
      YYYY-MM-DD_variant-matrix.md
      YYYY-MM-DD_results.md

    action-queues/
      YYYY-MM-DD_weekly-action-queue.md

    client-facing/
      YYYY-MM-DD_client-memo.md
      YYYY-MM-DD_report.pdf
      YYYY-MM-DD_accounts.csv
```

## Execution Result Standard
Every script or workflow should emit an execution result.

Minimum fields:

```json
{
  "execution_id": "uuid",
  "client": "client-slug",
  "workflow": "audit | sprint | os-pilot | email-sync | crm-sync",
  "mode": "dry_run | live",
  "started_at": "timestamp",
  "finished_at": "timestamp",
  "status": "success | partial_success | failed | needs_review",
  "created_count": 0,
  "updated_count": 0,
  "skipped_count": 0,
  "failed_count": 0,
  "outputs": [],
  "exceptions": []
}
```

Append execution results to:

```text
projects/<client>/data/execution_log.jsonl
```

## Internal Test Clients
Use internal test clients before selling.

### deploygtm-own
Purpose:
- test DeployGTM's own ICP, scoring, and service model
- good for GTM maturity / sales infra / founder-led sales logic

### peregrine-space
Purpose:
- test client-specific ICP scoring where GTM maturity is not the scoring dimension
- good for deep tech / aerospace / signal-account intelligence

### synthetic-client
Purpose:
- safe fake test case where no external data or client claims matter
- useful for testing scripts and deliverable generation

## Offer Test 1: GTM Signal Audit

### Goal
Prove I can create a client-ready diagnostic artifact.

### Dry Run Command Shape

```text
make test-audit CLIENT=peregrine-space MODE=dry-run
```

or manually:

```text
python scripts/run_signal_audit.py --client peregrine-space --sample-size 25 --dry-run
```

### Required Inputs

```text
projects/<client>/context.md
projects/<client>/data/icp_profile.json
```

Optional:

```text
projects/<client>/data/account_matrix.json
projects/<client>/data/signals.json
```

### Workflow
1. Load context.
2. Load or derive ICP profile.
3. Build or load 25-50 sample accounts.
4. Check BirdDog signal coverage if available.
5. Score accounts.
6. Generate signal coverage summary.
7. Generate audit memo.
8. Export scored accounts CSV.
9. Write execution result.

### Required Outputs

```text
projects/<client>/outputs/audit/YYYY-MM-DD_signal-audit.md
projects/<client>/outputs/audit/YYYY-MM-DD_scored-accounts.csv
projects/<client>/outputs/audit/YYYY-MM-DD_signal-coverage.csv
```

### Success Criteria
The audit test passes if it produces:

- a readable memo
- a scored account sample
- a BirdDog recommendation category: core / supplemental / not central
- a next-motion recommendation
- no unhandled errors

### Client-Facing Artifact
The client should receive:

- Signal Audit Memo
- scored accounts CSV
- signal coverage summary

## Offer Test 2: Signal + Message-Market Fit Sprint

### Goal
Prove I can define and run message-market-fit experiments using the market -> segment -> persona -> angle unit.

### Dry Run Command Shape

```text
make test-sprint CLIENT=peregrine-space MODE=dry-run
```

or manually:

```text
python scripts/run_mmf_sprint.py --client peregrine-space --cells 5 --dry-run
```

### Required Inputs

```text
projects/<client>/context.md
projects/<client>/data/icp_profile.json
projects/<client>/data/account_matrix.json
```

Optional:

```text
projects/<client>/data/contacts.json
projects/<client>/data/signals.json
```

### Workflow
1. Load ICP profile.
2. Define 3-5 test cells.
3. Each cell must include market, segment, persona, angle.
4. Assign accounts/contacts to cells.
5. Generate 2-4 step sequence draft per cell.
6. Create human review queue.
7. If live, route approved contacts to sequencer.
8. Track replies and sentiment.
9. Generate results report.

### Required Outputs

```text
projects/<client>/outputs/message-market-fit/YYYY-MM-DD_test-cells.md
projects/<client>/outputs/message-market-fit/YYYY-MM-DD_variant-matrix.md
projects/<client>/outputs/message-market-fit/YYYY-MM-DD_results.md
projects/<client>/data/campaign_matrix.json
```

### Success Criteria
The sprint test passes if it produces:

- 3-5 test cells
- account/contact assignment logic
- draft messaging by cell
- review queue
- testable performance tracking structure

### Client-Facing Artifact
The client should receive:

- test cell map
- message hypotheses
- results report when live data exists
- recommendation: keep / kill / iterate by cell

## Offer Test 3: GTM OS Pilot

### Goal
Prove I can run the full account intelligence loop.

### Dry Run Command Shape

```text
make test-os-pilot CLIENT=peregrine-space MODE=dry-run
```

or manually:

```text
python scripts/run_os_pilot.py --client peregrine-space --dry-run
```

### Required Inputs

```text
projects/<client>/context.md
projects/<client>/data/icp_profile.json
projects/<client>/data/account_matrix.json
```

Optional:

```text
projects/<client>/data/signals.json
projects/<client>/data/contacts.json
projects/<client>/data/monitored_accounts.json
```

### Workflow
1. Load client context.
2. Load ICP profile.
3. Load or discover account universe.
4. Score accounts.
5. Select active monitored accounts.
6. Pull or simulate BirdDog signals.
7. Compute urgency and priority scores.
8. Generate CRM writeback payload.
9. Generate weekly action queue.
10. Generate messaging ideas for top accounts.
11. Write execution result.

### Required Outputs

```text
projects/<client>/outputs/action-queues/YYYY-MM-DD_weekly-action-queue.md
projects/<client>/data/account_matrix.json
projects/<client>/data/monitored_accounts.json
projects/<client>/data/execution_log.jsonl
```

Optional live output:

```text
projects/<client>/outputs/client-facing/YYYY-MM-DD_crm-update-summary.md
```

### Success Criteria
The OS pilot test passes if it produces:

- scored account list
- monitored account recommendation
- CRM writeback preview
- weekly action queue
- next actions by account
- messaging ideas for top accounts

### Client-Facing Artifact
The client should receive:

- weekly action queue
- CRM update summary
- signal report
- top accounts to work
- message ideas

## Offer Test 4: Operated GTM Command Layer

### Goal
Prove the recurring operating cadence.

### Dry Run Command Shape

```text
make test-command-layer CLIENT=peregrine-space MODE=dry-run
```

### Workflow
This is the OS Pilot repeated on a cadence.

1. New signals checked.
2. Urgency scores updated.
3. CRM writeback preview generated.
4. Action queue generated.
5. Reply/sentiment events incorporated.
6. Monthly calibration generated.

### Required Outputs

```text
projects/<client>/outputs/action-queues/YYYY-MM-DD_weekly-action-queue.md
projects/<client>/outputs/client-facing/YYYY-MM-DD_monthly-command-report.md
projects/<client>/data/execution_log.jsonl
```

### Success Criteria
The command layer test passes if the system can run the workflow more than once and preserve state between runs.

## Offer Test 5: Company Brain / Warehouse Layer

### Goal
Prove repeated cross-system questions deserve a query layer.

### Dry Run Command Shape

```text
make test-company-brain CLIENT=peregrine-space MODE=dry-run
```

### Workflow
1. Start with one recurring business question.
2. Identify required sources.
3. Load sample data locally.
4. Query across sources.
5. Generate answer artifact.
6. Decide whether warehouse/query layer is justified.

### Required Outputs

```text
projects/<client>/outputs/client-facing/YYYY-MM-DD_company-brain-poc.md
```

## How to Give Anyone Anything

Do not give clients raw internal files by default.

Use this packaging path:

1. Generate markdown report from canonical data.
2. Export CSVs where useful.
3. Copy or render client-facing docs into Google Drive.
4. Share Drive links or PDFs.
5. Keep internal JSON/logs in GitHub/local storage.

### Client-Facing Deliverables

Audit:
- memo
- scored accounts CSV
- signal coverage CSV

Sprint:
- test cell map
- variant matrix
- results memo

OS Pilot:
- weekly action queue
- signal report
- CRM update summary
- top account briefs

Command Layer:
- weekly command report
- monthly calibration report
- executive summary

Company Brain:
- question-answer memo
- query/report examples
- dashboard or MCP proof of concept

## Client-Facing Report Template
Every report should follow this structure:

```text
# [Client] - [Report Type]

## Executive Summary
What changed, what matters, and what decision should be made.

## What We Analyzed
Inputs, account sample, signals, CRM data, or campaign data.

## Findings
The important observations.

## Recommended Actions
What should happen next.

## Supporting Data
Tables, scores, signal coverage, campaign results.

## Open Questions
Anything still uncertain.
```

## Build Gaps to Close
The current build needs these mechanisms if they do not already exist:

1. `scripts/run_signal_audit.py`
2. `scripts/run_mmf_sprint.py`
3. `scripts/run_os_pilot.py`
4. `scripts/generate_client_report.py`
5. `scripts/export_outputs_to_drive.py` or manual Drive export step
6. execution logging standard
7. project output folder creation
8. dry-run mode for every workflow
9. CRM writeback preview before live writes
10. test fixtures for internal clients

## Codex / Claude Code Recovery Step
Before building new features, verify repo state.

Run:

```bash
git status
git branch --show-current
git log --oneline --decorate --all -n 20
find . -name "derive_icp.py" -o -name "email_sync.py"
find . -name "score_engine.py" -o -name "research_accounts.py" -o -name "enrich_matrix.py"
git diff --name-only
git stash list
pytest
```

Then answer:

1. Is the ICP refactor present locally?
2. Is it committed?
3. Is it pushed?
4. Is `email_sync.py` present?
5. Is `email_sync.py` complete or half-built?
6. What tests pass/fail?
7. What is the safest next implementation step?

## Implementation Priority

### First
Recover current repo state and confirm the ICP refactor.

### Second
Finish local testability:
- output folder creation
- execution logs
- dry-run audit workflow

### Third
Finish feedback loop:
- email_sync.py
- response events
- score updates

### Fourth
Add live integrations:
- HubSpot writeback
- BirdDog adapter
- enrichment adapter

### Fifth
Add client packaging:
- markdown reports
- CSV exports
- Drive export/share workflow

## Summary
The service model becomes practical only when each offer produces a concrete artifact.

The rule:

> Every workflow must end in a client-facing output and an internal execution log.

If it cannot produce an artifact, it is not ready to sell.
