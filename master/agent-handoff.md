# DeployGTM Agent Handoff

Updated: 2026-05-07

Purpose: give the next Claude/Codex session the current operating truth without relying on a standalone desktop chat.

## Current State

Branch `claude/fix-skeleton-builds-UE36D` is ahead of `main` with the skeleton-fix work (commits `e70ed33` through `f90c5f1`). This branch has NOT been merged to main yet — it is the active development branch.

**Do not push to main directly.** When this work is ready to merge, open a PR from `claude/fix-skeleton-builds-UE36D` into `main`.

### What changed on this branch (2026-05-04 to 2026-05-07)

The entire platform pipeline was skeleton code — string substitution and keyword matching with no real LLM reasoning. Every account scored identically. Signals were hardcoded B2B SaaS templates. ICPs were generic. Copy was never generated. This has been fully replaced.

**Platform pipeline now has real LLM reasoning at every step:**

| Step | File | What it does now |
|------|------|-----------------|
| ICP Strategy | `scripts/platform/icp_strategy.py` | Claude generates market-specific ICPs with `must_have`, `nice_to_have`, `disqualifiers`, `scoring_weights`, `why_now_signals` (with source/urgency), `angle_template`, and a 5-band `scoring_rubric` specific to the client's market |
| Signal Strategy | `scripts/platform/signal_strategy.py` | Claude generates 20 client-specific signals; assigns `mapped_icps` by relevance (not round-robin index); BirdDog query hints reference all mapped ICP names |
| Account Matrix | `scripts/platform/account_matrix.py` | GPT-4o (Claude fallback) scores each account against full ICP criteria text including rubric and disqualifiers; returns `matched_icp`, `recommended_persona`, `recommended_angle` per account |
| Messaging | `scripts/platform/messaging.py` | **NEW** — reads `brain/messaging.md` + `brain/personas.md`; Claude generates sub-100-word first-touch copy, email subject line, and LinkedIn version per account in Matthew's voice; writes back to `accounts.json` under `copy` |
| Brief | `scripts/platform/brief.py` | **NEW** — reads `brain/personas.md` + `brain/objections.md`; Claude generates per-account call-prep brief (snapshot, why_now, talking points, objections with responses from the real playbook, recommended ask); writes `account_briefs.json` |
| Deliverable | `scripts/platform/deliverable.py` | Updated CSV includes Matched ICP, Recommended Persona, First Touch Subject, First Touch Copy; summary shows messaging/brief step completion status |

**LLM provider routing** (`scripts/platform/llm.py`):
- `icp_strategy` → Claude
- `signal_strategy` → Claude
- `account_scoring` → GPT-4o (falls back to Claude if no `OPENAI_API_KEY`)
- `messaging` → Claude
- `brief` → Claude
- Set `LLM_SKIP=true` to run fully offline (deterministic fallbacks, no API calls)

**CLI** (`scripts/platform/cli.py`): `messaging` and `briefs` commands added; both included in `signal-audit-dry-run` sequence.

**Makefile**: `platform-messaging` and `platform-briefs` targets added.

**Tests**: 55 tests pass. 2 new tests cover messaging schema and brief structure. Run: `python3 -m pytest tests/ -q`

### Complete platform pipeline order (as of 2026-05-07)

```text
intake → context-pack → strategy (ICP) → signal-strategy → account-matrix
  → messaging → briefs → crm-plan → deliverable
```

Or via CLI:
```bash
python3 -m scripts.platform.cli signal-audit-dry-run   # runs all steps on sample data
```

Or per step:
```bash
python3 -m scripts.platform.cli intake --client-name "..." --domain ... --target-outcome "..." --offer "..."
python3 -m scripts.platform.cli strategy --client <slug>
python3 -m scripts.platform.cli signal-strategy --client <slug>
python3 -m scripts.platform.cli account-matrix --client <slug>
python3 -m scripts.platform.cli messaging --client <slug>
python3 -m scripts.platform.cli briefs --client <slug>
python3 -m scripts.platform.cli crm-plan --client <slug>
python3 -m scripts.platform.cli deliverable --client <slug>
```

## What Is NOT Yet Built (next priorities)

### 1. Follow-up sequence generation
`accounts.json` has `copy.followups: []` — it's seeded but never filled.
The messaging step only generates the first touch. Follow-ups #1 (day 3), #2 (day 7), #3 (day 14) need a separate pass.
Reference: `brain/messaging.md` — "Channel guidance" section has the cadence and tone rules.
File to create: `scripts/platform/followups.py` — same pattern as `messaging.py`, extend `copy.followups` list.

### 2. Living Brain — ingestion layer
Roadmapped in session (2026-05-07). The brain/ folder is static markdown. It needs to become a self-updating system that pulls from calls, emails, meetings, and deals.
Phase 1 schema is designed; implementation not started.
Key files to create:
- `brain/schema/brain_update.json` — structured format for new intelligence units
- `scripts/brain/ingest.py` — ingestion from transcripts, email threads, deal notes
- `scripts/brain/pattern_extract.py` — extract ICP signals, objections, messaging wins/losses
- `scripts/brain/approval_queue.py` — human-approval before brain updates go live
See session notes for the full 5-phase roadmap.

### 3. Peregrine Space re-run with real LLM
The `projects/peregrine-space/` artifacts were generated with the old skeleton code (all 8 accounts scored ICP:60, urgency:16, generic ICPs, wrong signals). These need to be regenerated with real LLM calls to show what the fixed system produces.
Run: `make platform-strategy CLIENT=peregrine-space` etc. with a live `ANTHROPIC_API_KEY`.

### 4. BirdDog API verification
`birddog_signal_manifest.json` is generated but write mode is `manual_review_required`.
BirdDog's API support for custom signal definitions and recommended accounts via API is unconfirmed.
Until confirmed, the manifest is a manual-review/export artifact only.

### 5. Merge branch to main
`claude/fix-skeleton-builds-UE36D` → PR → review → merge to `main`.

## Key Files to Read Before Making Changes

1. `master/agent-handoff.md` (this file)
2. `CLAUDE.md` — operating constraints and product context
3. `RUNBOOK.md` — operational procedures
4. `docs/clarify-api-cli-strategy.md` — CRM strategy
5. `master/sdr-automation-map.md` — SDR automation coverage map
6. `brain/messaging.md` — messaging rules (non-negotiable, do not override)
7. `brain/personas.md` — buyer personas
8. `brain/objections.md` — objection handling playbook

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

## Guardrails

- No production CRM write without explicit confirmation.
- No email sends.
- No force pushes.
- No branch deletion until the cleanup pass in `BRANCH_DISPOSITION.md`.
- No broad refactor unless it directly improves the trusted Signal Audit loop.
- No local-only deliverables; commit durable state to GitHub Cloud.
- `handoff.md` and `open-loops.md` inside any `projects/<client>/` directory are human-maintained — never overwrite them (the `--force` flag on intake deliberately skips these files).
- `LLM_SKIP=true` must keep all 55 tests passing — every LLM call needs a deterministic fallback.

## Branch Cleanup Guidance

Do not delete branches yet.
Use `BRANCH_DISPOSITION.md` and `DUPLICATE_WORK.md` for branch decisions.

