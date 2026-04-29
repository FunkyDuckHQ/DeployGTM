# Claude Master Files Salvage Plan

Date: 2026-04-28
Source branch: `claude/read-master-files-wWR6f`
Target scope: `FunkyDuckHQ/DeployGTM` only

## Position

The Claude master files should be included in the DeployGTM recovery. The caution is not about the docs themselves; it is about not merging the entire divergent Claude branch blindly just to get them.

The Claude branch contains two different categories of work:

1. Strategic/docs work that can be reviewed and ported quickly.
2. Runtime code/tests that overlap with `main`, PR #6, and newer platform work.

This document makes the strategic/docs work a first-class salvage track.

## Include First

These files should be reviewed for direct inclusion or near-direct port into `main`/the recovery branch:

| Source File | Recommended Destination | Disposition | Why |
|---|---|---|---|
| `master/architecture-roadmap.md` | `master/architecture-roadmap.md` | include after wording audit | Strong system map: current state, next nodes, CRM-agnostic principles, ICP-driven signal search, feedback loops. |
| `master/playbooks/market-map.md` | `master/playbooks/market-map.md` | include | Clear playbook for converting ICP into workable segments. This strengthens account-matrix discipline. |
| `master/playbooks/inbox-warmup.md` | `master/playbooks/inbox-warmup.md` | include | Deliverability is operationally critical and missing from current mainline playbooks. |
| `brain/segments.md` | `brain/segments.md` | include, then reconcile with `brain/icp.md` and `brain/messaging.md` | Segment-aware messaging is directly relevant to DeployGTM's own outbound engine. |

## Include Carefully

These files have useful sections but may conflict with current recovery docs or overstate readiness:

| Source File | Disposition | Notes |
|---|---|---|
| `CLAUDE.md` | selective merge | Useful operating instructions, but must not override the recovery audit or claim unverified workflows are ready. |
| `master/matthew-working-conditions.md` | selective merge | Preserve operator preferences; remove stale status claims. |
| `master/progress.md` | selective merge only | Progress docs are valuable but must be reconciled against actual passing commands. |

## Do Not Include Blindly

These are valuable but should be treated as implementation candidates, not docs to merge immediately:

- `projects/deploygtm-own/scripts/*`
- `scripts/crm_adapter.py`
- `scripts/derive_icp.py`
- `scripts/engage.py`
- `scripts/signals_to_matrix.py`
- `scripts/sync_client_context.py`
- `scripts/email_sync.py`
- `tests/test_account_matrix.py`
- `tests/test_derive_icp.py`
- `tests/test_engage_and_scoring.py`
- `tests/test_research_and_enrich.py`

Reason: these overlap with current platform code and PR #6. They should be evaluated by subsystem and ported only with passing tests.

## Porting Order

1. Add the three low-risk strategic docs:
   - `master/playbooks/market-map.md`
   - `master/playbooks/inbox-warmup.md`
   - `brain/segments.md`

2. Add `master/architecture-roadmap.md`, but edit language that says everything is built unless the runbook proves it.

3. Reconcile `brain/segments.md` with current `brain/icp.md`, `brain/personas.md`, and `brain/messaging.md`.

4. After test dependencies are fixed, review the Claude branch tests to identify missing coverage worth porting.

5. Only after tests pass, decide whether any Claude runtime code should be manually ported.

## Rule

Include the Claude master files. Do not include unverified duplicate runtime systems just because they live on the same branch.
