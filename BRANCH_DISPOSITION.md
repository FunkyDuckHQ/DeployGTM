# Branch Disposition Audit

Date: 2026-04-28
Scope: `FunkyDuckHQ/DeployGTM` only.

Disposition labels:

- `keep as mainline`: current source of truth.
- `merge candidate`: can be merged after tests/review.
- `cherry-pick candidate`: salvage specific files/ideas only.
- `superseded duplicate`: work appears already represented elsewhere.
- `archive/delete later`: no ahead work relative to main/default.

## FunkyDuckHQ/DeployGTM

Base: `main` (`d10fc26c0482405ecaa59cc5692d65c3e800947b` at audit time)

| Branch | Status vs `main` | PR | Changed Surface | Disposition | Rationale |
|---|---:|---|---|---|---|
| `main` | source | n/a | Current repo | keep as mainline | GitHub Cloud source of truth. |
| `Test` | 0 ahead / 43 behind | PR #1 | none vs main | archive/delete later | No ahead commits; old upload/test branch. |
| `codex/apply-updated-files-and-set-up-api-tests` | 0 ahead / 18 behind | PR #3 | none vs main | archive/delete later | Merged/superseded by later harness work. |
| `codex/apply-updated-files-and-set-up-api-tests-uzmqm8` | 1 ahead / 19 behind | PR #4 | `.env.local.example`, README, logs, design principles, local API harness, tests | superseded duplicate | PR #4 body says resolved via direct merge. Confirm no unique harness fixes before archiving. |
| `codex/check-progress-on-deploygtm-artifacts` | 0 ahead / 4 behind | PR #5 merged | none vs main | archive/delete later | PR #5 merged into main. |
| `codex/check-progress-on-deploygtm-artifacts-u4uyba` | 1 ahead / 5 behind | PR #6 open | email sync, platform schemas, context pack, ICP strategy, transcript persistence, tests | merge candidate | Small focused follow-on to PR #5. Requires dependency/test verification before merge. |
| `claude/read-master-files-wWR6f` | 21 ahead / 13 behind | PR #2 plus direct merges | master files, account matrix, CRM adapter, derive ICP, email sync, engage/scoring, tests | split disposition | Include master/docs intentionally; do not merge runtime code wholesale. |

## Claude Branch Split

`claude/read-master-files-wWR6f` should be split into two tracks:

| Track | Files | Disposition |
|---|---|---|
| Claude master files | `master/architecture-roadmap.md`, `master/playbooks/market-map.md`, `master/playbooks/inbox-warmup.md`, `brain/segments.md`, selected `CLAUDE.md`/progress/working-conditions sections | include after wording/reality audit |
| Claude runtime/code | `scripts/*`, `projects/deploygtm-own/scripts/*`, `tests/test_*` | cherry-pick candidate by subsystem after tests are fixed |

See `CLAUDE_MASTER_FILES.md` for the specific include plan.

## Cleanup Order

1. Keep all branches untouched while recovery branch is reviewed.
2. Port/reconcile Claude master files into the recovery branch.
3. Fix test dependencies and prove the trusted loop.
4. Merge or close PR #6 only after tests are green.
5. Salvage unique runtime work from `claude/read-master-files-wWR6f` by subsystem.
6. Archive/delete zero-ahead branches only after the recovery PR is merged.
