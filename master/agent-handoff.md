# DeployGTM Agent Handoff

Updated: 2026-04-29

Purpose: give the next Claude/Codex session the current operating truth without relying on a standalone desktop chat.

## Current State

PR #7, `Recover DeployGTM Signal Audit system`, has been merged into `main`.

The repo now includes:

- Recovery audit docs:
  - `AUDIT.md`
  - `BRANCH_DISPOSITION.md`
  - `DUPLICATE_WORK.md`
  - `RUNBOOK.md`
  - `EXTERNAL_REPOS.md`
  - `CLEANUP_PLAN.md`
  - `CLAUDE_MASTER_FILES.md`
- Signal Audit recovery spine:
  - `scripts/platform/intake.py`
  - `scripts/platform/icp_strategy.py`
  - `scripts/platform/signal_strategy.py`
  - `scripts/platform/account_matrix.py`
  - `scripts/platform/crm_push_plan.py`
  - `scripts/platform/deliverable.py`
  - `scripts/email_sync.py`
  - `n8n/README.md`
  - `n8n/workflows/signal-audit-runtime.json`

## Product Direction

DeployGTM is an end-to-end GTM operating system.

Signal Audit is the wedge offer: a paid test that leaves the client with real accounts, real ICP/urgency scores, real signal definitions, real enriched target profiles, real copy, and a CRM push plan. The audit proves whether the system should continue into an operated retainer.

The intended flow is:

```text
Customer + desired outcome
  -> context pack
  -> ICP strategy
  -> 20 BirdDog-ready signals
  -> account discovery / target list
  -> account matrix
  -> separate ICP fit + urgency + engagement + confidence scores
  -> activation priority
  -> CRM push plan
  -> rep tasks / copy / profiles
  -> feedback from BirdDog + email engagement
```

## Architecture Boundaries

- GitHub Cloud is the source of truth.
- Python scripts are the deterministic business logic.
- Claude/Codex/OpenAI are the reasoning, generation, review, and code-change layer.
- n8n is only the durable runtime for schedules, webhooks, retries, approvals, and notifications.
- BirdDog is the signal monitoring layer.
- HubSpot is the first CRM adapter.
- SuperSend/email engagement is a feedback signal only until managed sending controls exist.

## What To Do Next

1. Keep the repo green:
   - `python3 -m pytest tests -q`
   - `make daily`
   - `make signal-audit-dry-run`

2. Prove one real no-write Signal Audit:
   - Run `platform-intake` for a real customer/outcome.
   - Fill or import `projects/<client>/targets.csv`.
   - Run `context-pack`, `platform-strategy`, `platform-signals`, `platform-matrix`, `platform-crm-plan`, and `platform-deliverable`.
   - Confirm the output is useful before adding automation.

3. Verify BirdDog API reality:
   - Confirm whether BirdDog supports custom signal definitions and recommended accounts via API.
   - Until confirmed, keep `birddog_signal_manifest.json` as manual-review/export artifact.

4. Keep CRM safe:
   - `crm_push_plan.json` is dry-run by default.
   - Push only DeployGTM-found accounts, contacts, notes, tasks, and deals.
   - Do not ingest or mutate the entire client CRM yet.

5. Defer managed sending:
   - Generate copy and sequence-ready drafts.
   - Do not own sending until domain warming, suppression, unsubscribe, bounce handling, deliverability reporting, and approval controls exist.

6. Only then wire n8n:
   - Use the specs in `n8n/`.
   - n8n should call tested scripts; it should not become the business logic.

## Branch Cleanup Guidance

Do not delete branches yet.

Use `BRANCH_DISPOSITION.md` and `DUPLICATE_WORK.md` for branch decisions. The Claude branch contains useful master files but should not be wholesale-merged. The SuperSend/email feedback concept has been ported into `scripts/email_sync.py`; review PR/branch duplicates before closing anything.

## Guardrails

- No production CRM write without explicit confirmation.
- No email sends during recovery.
- No force pushes.
- No branch deletion until the cleanup pass.
- No broad refactor unless it directly improves the trusted Signal Audit loop.
- No local-only deliverables; commit durable state to GitHub Cloud.
