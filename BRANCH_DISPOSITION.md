# Branch Disposition Audit

Date: 2026-04-28

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
| `claude/read-master-files-wWR6f` | 21 ahead / 13 behind | PR #2 plus direct merges | account matrix, CRM adapter, derive ICP, email sync, engage/scoring, tests, docs/playbooks | cherry-pick candidate | Large divergent branch. Contains valuable work but overlaps with PR #5/#6 and main. Do not merge wholesale. |

## FunkyDuckHQ/yourfinancialguru

Base: `claude/design-financial-guru-mvp-e3lBM`

| Branch | Status vs default | PR | Changed Surface | Disposition | Rationale |
|---|---:|---|---|---|---|
| `claude/design-financial-guru-mvp-e3lBM` | source | n/a | Current Next app | keep as mainline | Current default branch. Unusual branch name but canonical unless renamed later. |
| `claude/add-bulk-enrichment-api-JsHIK` | 1 ahead / 0 behind | none observed | `app/api/people/bulk_match/route.ts` | cherry-pick candidate | Small API addition; review for product relevance and security. |
| `claude/behavioral-first-rebuild-e3lBM` | 17 ahead / 0 behind | none observed | broad product/UI, checkins, insights, quiz/results/accounts | cherry-pick candidate | Large and possibly valuable, but too broad for wholesale merge without UX/build validation. |
| `claude/continue-design-thread-uwAEV` | 1 ahead / 0 behind | none observed | `app/data/types.ts`, `app/globals.css` | superseded duplicate | Small design/type tweaks likely included in broader branches. Diff before archive. |
| `claude/review-session-code-muhw8` | 9 ahead / 1 behind | none observed | account data, home, quiz, dependency versions | cherry-pick candidate | Diverged and touches core flows/package metadata. Needs build test before any adoption. |
| `codex/analyze-your-financial-guru` | 2 ahead / 13 behind | PR #1 draft open | mock-memory, connect, memory, quiz, layout, nav, home | cherry-pick candidate | Draft PR is unmergeable/diverged. Salvage ideas only after build and flow validation. |

## Cleanup Order

1. Keep all branches untouched while recovery branch is reviewed.
2. Merge or close PR #6 only after tests are green.
3. Salvage unique work from `claude/read-master-files-wWR6f` by subsystem.
4. For `yourfinancialguru`, create a separate recovery audit branch before merging any UI work.
5. Archive/delete zero-ahead branches only after the recovery PR is merged.
