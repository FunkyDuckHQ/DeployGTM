# DeployGTM Agent Handoff

Updated: 2026-05-05

Purpose: give the next Claude/Codex session the current operating truth without relying on a standalone desktop chat.

## Current State

PR #7, `Recover DeployGTM Signal Audit system`, has been merged into `main`.

The repo now includes the recovery spine plus the multi-client workflow spine and Flashpoint onboarding prep.

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
- Clarify/API/CLI and SDR automation strategy:
  - `docs/clarify-api-cli-strategy.md`
  - `master/sdr-automation-map.md`
- Multi-client workflow spine:
  - `clients/_template/`
  - `clients/peregrine_space/`
  - `clients/example_b2b_saas/`
  - `3_operations/scripts/bootstrap_client.py`
  - `3_operations/scripts/validate_client.py`
  - `3_operations/scripts/score_accounts.py`
  - `3_operations/scripts/run_client_workflow.py`
- Copy quality infrastructure:
  - `workflows/deploygtm-prospect-copy.md`
  - `templates/copy-packet.schema.json`
  - `templates/copy-quality-rubric.json`
  - `3_operations/scripts/validate_copy_packet.py`
- Flashpoint onboarding prep:
  - `clients/flashpoint/`
  - `clients/flashpoint/research/agency-research-processes.md`
  - `clients/flashpoint/research/revenue-map.md`
  - `workflows/flashpoint-gtm-pilot.md`
  - `docs/mitchell-keller-github-deep-dive.md`

## Product Direction

DeployGTM is an end-to-end GTM operating system.

Signal Audit is the wedge offer: a paid test that leaves the client with real accounts, real ICP/urgency scores, real signal definitions, real enriched target profiles, real copy, and a CRM push plan. The audit proves whether the system should continue into an operated retainer.

Signal Audit should also assess SDR automation coverage across six workstreams: research/targeting, enrichment/data, personalization/copy, sending/deliverability, inbound/routing, and pipeline/coaching. See `master/sdr-automation-map.md`.

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
- Clarify is the preferred CRM/workspace candidate once API/MCP access and field mapping are confirmed.
- HubSpot is a compatibility adapter for clients already on HubSpot, not the default center of gravity.
- SuperSend/email engagement is a feedback signal only until managed sending controls exist.
- Complex APIs/CLIs must be wrapped in the DeployGTM control-plane lifecycle: validate, describe, read, plan, dry-run, write with confirmation, sync events, and save receipts.

## What To Do Next

1. Keep the repo green:
   - `python -m pytest tests -q`
   - `make daily`
   - `make signal-audit-dry-run`

2. Prepare Flashpoint with the file-based client workspace:
   - Validate `clients/flashpoint/`.
   - Complete `clients/flashpoint/research/revenue-map.md` with real revenue/project rows.
   - Replace seed segment rows in `clients/flashpoint/inputs/accounts.json` with researched agency accounts.
   - Run Mitchell-style agency research from `clients/flashpoint/research/agency-research-processes.md`.
   - Score accounts with `3_operations/scripts/score_accounts.py --client flashpoint`.
   - Use the copy packet workflow only after account evidence and proof asset fit are attached.

3. Prove one real no-write Signal Audit:
   - Run `platform-intake` for a real customer/outcome.
   - Fill or import `projects/<client>/targets.csv`.
   - Run `context-pack`, `platform-strategy`, `platform-signals`, `platform-matrix`, `platform-crm-plan`, and `platform-deliverable`.
   - Confirm the output is useful before adding automation.

4. Verify BirdDog API reality:
   - Confirm whether BirdDog supports custom signal definitions and recommended accounts via API.
   - Until confirmed, keep `birddog_signal_manifest.json` as manual-review/export artifact.

5. Keep CRM safe:
   - `crm_push_plan.json` is dry-run by default.
   - Push only DeployGTM-found accounts, contacts, notes, tasks, and deals.
   - Do not ingest or mutate the entire client CRM yet.
   - Prefer Clarify for new DeployGTM-operated workflows after API/MCP access is confirmed.
   - Keep HubSpot adapter support for client compatibility.

6. Defer managed sending:
   - Generate copy and sequence-ready drafts.
   - Do not own sending until domain warming, suppression, unsubscribe, bounce handling, deliverability reporting, and approval controls exist.

7. Only then wire n8n:
   - Use the specs in `n8n/`.
   - n8n should call tested scripts; it should not become the business logic.

8. Evaluate CLI/agent tooling carefully:
   - Matthew flagged https://github.com/stars/elviskahoro/lists/cli as a useful research source.
   - Matthew also flagged https://github.com/MitchellkellerLG for free workflows and vendor ideas.
   - The likely value is agent observability, codebase visualization, context hygiene, and workflow/runtime tooling.
   - Do not add these tools directly to the system. Use the watchlist and evaluation rules in `EXTERNAL_REPOS.md`.

9. Follow the Clarify/API/CLI strategy:
   - Read `docs/clarify-api-cli-strategy.md`.
   - Treat Clarify as a first-class CRM/workspace target, not a place to hide business logic.
   - Do not enable live Clarify writes until the adapter can prove schema, dry-run payloads, approval, and receipt logging.

10. Follow the SDR automation map:
   - Read `master/sdr-automation-map.md`.
   - Build toward automating the mechanical SDR workload while routing live discovery, hard objections, multi-stakeholder navigation, executive trust, and recovery from misfires to humans.
   - Treat 90-day profitable pipeline guarantee language as an offer hypothesis until qualification, economics, client obligations, deliverability, and scope guardrails are defined.

## Branch Cleanup Guidance

Branch cleanup has been completed. `main` is the source of truth. Keep `origin/claude/read-master-files-wWR6f` only as a low-cost salvage/reference branch until its master-file value is fully extracted.

## Guardrails

- No production CRM write without explicit confirmation.
- No email sends during recovery.
- No force pushes.
- No branch deletion unless branch disposition has been checked.
- No broad refactor unless it directly improves the trusted Signal Audit loop.
- No local-only deliverables; commit durable state to GitHub Cloud.
