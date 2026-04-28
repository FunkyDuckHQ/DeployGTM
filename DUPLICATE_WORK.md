# Duplicate Work And Conflict Analysis

Date: 2026-04-28
Scope: `FunkyDuckHQ/DeployGTM` only.

This document groups overlapping work by subsystem. It is intentionally behavior-first rather than branch-first, because the same concept appears in multiple Claude/Codex DeployGTM branches.

## Summary Table

| Subsystem | Main / Current State | Duplicate Or Competing Work | Recommended Winner | Action |
|---|---|---|---|---|
| Local API harness | Present on `main` via Codex PR #3/#4 lineage | `codex/apply-updated-files-and-set-up-api-tests-uzmqm8` has older/similar harness files | `main` | Keep main; only salvage missing test/dependency fixes. |
| Platform vNext/context packs | PR #5 merged into `main` | PR #6 adds hardening; Claude branch adds broader account matrix/client scripts | `main` + reviewed PR #6 | Merge PR #6 only after tests; salvage Claude account matrix ideas separately. |
| Email sync/SuperSend | PR #6 adds `scripts/email_sync.py` with dry-run/log/profile gates | Claude branch has a larger `scripts/email_sync.py` plus tests | PR #6 for near-term | Use smaller PR #6 implementation first; compare Claude test cases for coverage. |
| Account matrix/scoring | `main` has platform schemas and seed artifacts | Claude branch has `projects/deploygtm-own/scripts/*`, `score_engine.py`, `variant_tracker.py`, `verify_signals.py`, many tests | Hybrid, not wholesale | Promote concepts after tests; avoid nested per-project script sprawl unless justified. |
| Research/enrichment | `main` has `research.py`, `apollo.py`, `signals.py`, `score.py` | Claude branch adds `derive_icp.py`, `signals_to_matrix.py`, `sync_client_context.py`; Mitchell repos add validated research/enrichment tooling | Main code + Mitchell patterns | Keep main as base; adopt Mitchell processes before expanding custom scripts. |
| CRM/HubSpot | `main` has `hubspot.py`, local API harness, provider switch concepts | Claude branch adds `crm_adapter.py`; PR #6 adds platform CRM adapter contract | PR #6 adapter direction | Favor provider-agnostic adapter contract; avoid duplicate CRM wrappers. |
| Docs/playbooks | `main` has extensive playbooks and progress docs | Claude branch adds architecture roadmap, market-map, inbox-warmup, segments | Main + Claude master files | Include Claude master files intentionally; reconcile readiness claims against tests. |

## Detailed Notes

### API Harness

The API harness work appears to have gone through at least two Codex branches and was then resolved into `main`. The open risk is not feature absence; it is trust. The harness must be verified with declared dependencies and a read-only/no-write path.

Required fixes before calling it stable:

- Ensure test runner is declared in repo dependencies or dev dependencies.
- Ensure harness can run diagnostics without failing solely because log writing fails.
- Ensure all write operations remain gated by explicit env flags.

### Platform vNext And Context Packs

PR #5 already merged the platform foundation. PR #6 is a follow-on with email sync and schema/test additions. The Claude branch has an older/larger version of similar ideas, including account-matrix scripts and engagement tooling.

Recommendation:

- Treat `main` + PR #6 as the canonical platform path.
- Use the Claude branch as a source of test cases and possible missing workflow concepts.
- Do not merge per-project scripts wholesale until the repo proves it needs that structure.

### Email Sync

Two email-sync paths exist:

- PR #6: smaller SuperSend event ingestion/polling with dry-run, logging, profile-update marker.
- Claude branch: larger email sync and engagement system intertwined with account matrix scripts.

Recommendation:

- Prefer PR #6 for near-term because it is smaller and tied to the current platform package.
- Pull over only missing tests or event cases from the Claude branch after file-level review.

### Account Matrix And Scoring

This is the largest runtime overlap. `main` contains schemas and seed artifacts; the Claude branch contains a full account-matrix operating layer under `projects/deploygtm-own/scripts/`.

Recommendation:

- Do not accept nested per-client scripts as the default pattern yet.
- Promote reusable logic to `scripts/platform/` only when it serves all clients.
- Keep client-specific data under `projects/<client>/`, not client-specific code unless absolutely necessary.

### Claude Master Files

The Claude master files are strategically useful and should be included. They are not the risky part of the Claude branch.

Priority include list:

- `master/architecture-roadmap.md`
- `master/playbooks/market-map.md`
- `master/playbooks/inbox-warmup.md`
- `brain/segments.md`

The only caution is that readiness language must be made honest. If a doc says a workflow is built, that workflow must either pass the runbook or be labeled as planned/pre-activation.

### Research And Enrichment

DeployGTM currently has custom scripts for signals, Apollo enrichment, Claude research, and scoring. Mitchell Keller's repos provide more mature patterns for research process validation and enrichment workflow design.

Recommendation:

- Use `research-process-builder` to standardize company research steps before adding more custom web research code.
- Use `ai-ark-cli` as an evaluated Apollo complement/replacement, starting with dry-run review URLs to avoid spend.
- Evaluate `discolike-cli` and `techsight-cli` as Phase 2 sources after the trusted loop is green.

### CRM And HubSpot

The repo has both direct HubSpot scripting and newer provider-agnostic adapter work. This can become messy fast.

Recommendation:

- Keep direct HubSpot scripts only as concrete implementations.
- Make provider-agnostic interfaces the public/internal contract.
- No CRM writes during audit.

## Merge Rules From This Analysis

1. Never merge a divergent branch wholesale.
2. Include Claude master files deliberately.
3. Prefer smaller, tested implementations over larger generated systems.
4. Promote reusable logic to shared platform modules.
5. Keep docs honest: document only workflows that have a passing command or clearly label them pre-activation.
6. Treat Mitchell repos as pattern sources first, dependencies second.
