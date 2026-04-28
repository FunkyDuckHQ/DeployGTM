# DeployGTM Recovery Audit

Date: 2026-04-28
Branch: `recovery/full-audit-cleanup`
Scope: `FunkyDuckHQ/DeployGTM`, `FunkyDuckHQ/yourfinancialguru`, and selected Mitchell Keller external repos.

## Executive Summary

This repository needs a stabilization pass before more feature work. The current state is not hopeless, but it is split across AI-generated branches, overlapping implementations, and documentation that sometimes claims readiness before the local/cloud test loop is proven.

The immediate priority is trust recovery:

1. Keep GitHub Cloud as the source of truth.
2. Do not merge old branches wholesale.
3. Reconcile duplicated work by subsystem.
4. Establish one green, no-write local/cloud test loop.
5. Only then decide what belongs in code, external tooling, or a workflow orchestrator.

## Source Of Truth

GitHub Cloud is canonical. Local clones are useful for inspection, but they are not the durable record because the operator works across computers and phone.

Canonical repos:

- `FunkyDuckHQ/DeployGTM`
- `FunkyDuckHQ/yourfinancialguru`

Local clones observed during audit:

- `/Users/matthew/Documents/DeployGTM`
- `/Users/matthew/yourfinancialguru`
- `/Users/matthew/external/research-process-builder`
- `/Users/matthew/external/ai-ark-cli`
- `/Users/matthew/external/claude-workspace-template`

## Key Findings

### DeployGTM

- `main` is the current cloud source of truth.
- `Test`, `codex/apply-updated-files-and-set-up-api-tests`, and `codex/check-progress-on-deploygtm-artifacts` are behind `main` with zero ahead commits; they are archive candidates.
- `codex/apply-updated-files-and-set-up-api-tests-uzmqm8` is a small diverged Codex branch for the local API harness. Its core work appears already represented in `main`; treat as superseded unless a file-level diff proves otherwise.
- `codex/check-progress-on-deploygtm-artifacts-u4uyba` is open PR #6. It contains one commit on top of already-merged PR #5 and adds SuperSend/email-sync hardening plus platform artifacts. It is a merge candidate only after dependency/test verification.
- `claude/read-master-files-wWR6f` is a large divergent branch with 21 commits ahead and 13 behind. It contains substantial work: account matrix scripts, CRM adapter, derive ICP, email sync, engagement/scoring, tests, and docs. This is not a safe wholesale merge. It is a salvage/cherry-pick candidate by subsystem.

### yourfinancialguru

- Default branch is `claude/design-financial-guru-mvp-e3lBM`, which is unusual but currently canonical for the repo.
- Several Claude branches are ahead of default and contain product/UI work.
- `codex/analyze-your-financial-guru` is open draft PR #1 and is diverged; it should not be merged until build and flow tests prove it.
- `claude/behavioral-first-rebuild-e3lBM` is the largest ahead branch and likely contains meaningful product direction, but it touches broad UI/product surfaces and must be reviewed by behavior, not merged wholesale.

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

Do not optimize for a big merge. Optimize for a small green recovery branch that proves the system can be tested and operated. Old branch cleanup should happen after the recovery branch is reviewed and green.
