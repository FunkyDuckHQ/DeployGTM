# Cleanup Execution Plan

Date: 2026-04-28
Scope: `FunkyDuckHQ/DeployGTM` only.

This is the execution sequence after the audit pack is reviewed.

## Phase 1: Port Claude Master Files

Goal: preserve the useful Claude strategic/master files before touching runtime code.

Source branch: `claude/read-master-files-wWR6f`

Include first:

- `master/playbooks/market-map.md`
- `master/playbooks/inbox-warmup.md`
- `brain/segments.md`
- `master/architecture-roadmap.md`, edited so readiness claims match verified commands

Include carefully:

- selected `CLAUDE.md` sections
- selected `master/matthew-working-conditions.md` sections
- selected `master/progress.md` sections only after reconciling with actual test results

Rule: include the Claude master files; do not import unverified duplicate runtime systems just because they live on the same branch.

## Phase 2: Prove The Base Repo

Goal: make `main`/recovery branch testable before merging feature branches.

Tasks:

1. Declare test dependencies explicitly.
   - Add `pytest` to the appropriate dependency file.
   - If dev dependencies are split later, document that split.

2. Run offline tests.
   - Command: `python -m pytest tests -q`
   - Expected: pass without API keys.

3. Run `make daily`.
   - Expected: pass without API keys.

4. Identify one no-write workflow and make it pass.
   - Prefer a deterministic score/dry-run path.
   - If none exists, add the smallest one.

Exit criteria:

- Fresh cloud/dev clone can run the trusted loop from `RUNBOOK.md`.

## Phase 3: Decide PR #6

Goal: resolve the open DeployGTM PR without blending unrelated branch work.

Tasks:

1. Review PR #6 changed files.
2. Run tests including `tests/test_email_sync.py` and `tests/platform/*`.
3. Confirm `scripts/email_sync.py` has no default write-to-CRM behavior.
4. Merge if green; otherwise close with notes and port selected tests/fixes manually.

Exit criteria:

- PR #6 is merged or closed with a written reason.

## Phase 4: Salvage Claude Runtime Work

Target branch: `claude/read-master-files-wWR6f`

Do not merge wholesale. Review in this order:

1. Tests:
   - `tests/test_account_matrix.py`
   - `tests/test_derive_icp.py`
   - `tests/test_engage_and_scoring.py`
   - `tests/test_research_and_enrich.py`
   - `tests/test_new_scripts.py`

2. Reusable platform concepts:
   - account matrix lifecycle
   - signal verification
   - variant tracking
   - derived ICP
   - engagement scoring

3. Runtime modules:
   - `scripts/derive_icp.py`
   - `scripts/engage.py`
   - `scripts/signals_to_matrix.py`
   - `scripts/sync_client_context.py`
   - `scripts/crm_adapter.py`

Rules:

- Port tests before implementation where possible.
- Prefer shared `scripts/platform/` modules over per-project scripts.
- Reject generated code that cannot be exercised by a command.

## Phase 5: External Repo Adoption

Do after Phases 1-3.

Tasks:

1. Use `research-process-builder` process files to rewrite the research runbook.
2. Test `ai-ark-cli` dry-run review URL flow without spending credits.
3. Decide whether to add submodules under `external/`.
4. Defer `auto-prompt-creator`, `discolike-cli`, and `techsight-cli` until the base system is green.

## Phase 6: Branch Archive

Only after recovery branch is merged.

Archive/delete candidates:

- `Test`
- `codex/apply-updated-files-and-set-up-api-tests`
- `codex/check-progress-on-deploygtm-artifacts`

Potentially archive after diff confirmation:

- `codex/apply-updated-files-and-set-up-api-tests-uzmqm8`
- `codex/check-progress-on-deploygtm-artifacts-u4uyba` if PR #6 is merged/closed

Never delete before:

- branch disposition is reviewed
- recovery branch is merged
- any salvage decisions are complete
