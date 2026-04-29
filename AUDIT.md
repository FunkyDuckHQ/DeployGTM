# DeployGTM Recovery Audit

Date: 2026-04-28
Branch: `recovery/full-audit-cleanup`
Scope: `FunkyDuckHQ/DeployGTM` only, plus selected Mitchell Keller external repos as reference/tooling inputs.

## Executive Summary

DeployGTM needs a stabilization pass before more feature work. The current state is not hopeless, but it is split across AI-generated branches, overlapping implementations, and documentation that sometimes claims readiness before the GitHub-cloud test loop is proven.

The immediate priority is trust recovery:

1. Keep GitHub Cloud as the source of truth.
2. Focus only on the DeployGTM build.
3. Do not merge old branches wholesale.
4. Preserve and port useful Claude master files intentionally.
5. Reconcile duplicated work by subsystem.
6. Establish one green, no-write cloud/local test loop.
7. Only then decide what belongs in code, external tooling, or a workflow orchestrator.

## Source Of Truth

GitHub Cloud is canonical. Local clones are useful for inspection, but they are not the durable record because the operator works across computers and phone.

Canonical repo for this recovery:

- `FunkyDuckHQ/DeployGTM`

Local clones observed during audit:

- `/Users/matthew/Documents/DeployGTM`
- `/Users/matthew/external/research-process-builder`
- `/Users/matthew/external/ai-ark-cli`
- `/Users/matthew/external/claude-workspace-template`

`yourfinancialguru` is explicitly out of scope for this recovery branch.

## Key Findings

### DeployGTM

- `main` is the current cloud source of truth.
- `Test`, `codex/apply-updated-files-and-set-up-api-tests`, and `codex/check-progress-on-deploygtm-artifacts` are behind `main` with zero ahead commits; they are archive candidates after recovery is merged.
- `codex/apply-updated-files-and-set-up-api-tests-uzmqm8` is a small diverged Codex branch for the local API harness. Its core work appears already represented in `main`; treat as superseded unless a file-level diff proves otherwise.
- `codex/check-progress-on-deploygtm-artifacts-u4uyba` is open PR #6. It contains one commit on top of already-merged PR #5 and adds SuperSend/email-sync hardening plus platform artifacts. It is a merge candidate only after dependency/test verification.
- `claude/read-master-files-wWR6f` is a large divergent branch with 21 commits ahead and 13 behind. It contains both valuable master files and substantial runtime code. The master/docs content should be included intentionally; the runtime code should be evaluated by subsystem before porting.

## Claude Master Files

We should include the Claude master files. The concern is only about merging the entire divergent Claude branch wholesale.

Priority Claude files to port/reconcile:

- `master/architecture-roadmap.md`
- `master/playbooks/market-map.md`
- `master/playbooks/inbox-warmup.md`
- `brain/segments.md`
- selected sections of `CLAUDE.md`, `master/matthew-working-conditions.md`, and `master/progress.md`

See `CLAUDE_MASTER_FILES.md` for the detailed salvage plan.

## Current Risk Register

| Risk | Severity | Evidence | Recommendation |
|---|---:|---|---|
| Branch split-brain | High | Multiple Claude/Codex branches with overlapping scripts/docs | Freeze feature work until branch disposition is approved |
| Unproven runnable loop | High | Tests previously failed locally because `pytest` was not declared/available | Make dependency/test fix the first recovery change |
| Docs ahead of reality | High | `progress.md` says built/pre-activation, while pipeline output is absent | Reconcile docs against verified commands |
| Duplicate implementations | High | Account matrix/scoring/email sync exist in both PR #6 and Claude branch variants | Choose winners by subsystem |
| AI as runtime engine | Medium | Claude/Codex generated many workflow steps but scheduling/event runtime is unresolved | Code-first for MVP; consider n8n only after green loop |
| External repo ambiguity | Medium | Mitchell repos exist locally but not in GitHub Cloud under DeployGTM | Add explicit external repo integration strategy before copying code |

## Recovery Principle

Do not optimize for a big merge. Optimize for a small green recovery branch that proves the system can be tested and operated. Include useful Claude master files deliberately; do not import unverified duplicate runtime systems just because they share the same branch.
