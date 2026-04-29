# Recovery Runbook

Date: 2026-04-28
Scope: `FunkyDuckHQ/DeployGTM` only.

Purpose: establish a trusted, repeatable, no-write test loop before additional feature work or branch merges.

## Golden Rules

- GitHub Cloud is source of truth.
- No CRM writes during recovery.
- No branch deletion during recovery.
- No force pushes.
- No large branch merges until subsystem review is complete.
- Every command below should either pass or produce a documented failure.

## DeployGTM Trusted Loop

Run from a fresh clone, GitHub Codespace, or other GitHub-backed dev environment.

```bash
git clone https://github.com/FunkyDuckHQ/DeployGTM.git
cd DeployGTM
git switch recovery/signal-audit-build
```

### 1. Inspect Repo State

```bash
git status --short --branch
git branch --all --verbose --no-abbrev
```

Expected:

- On `recovery/signal-audit-build`.
- No unexpected tracked-file changes.

### 2. Install Dependencies

Current declared command:

```bash
make install
```

If tests fail because `pytest` is missing, the first code fix should be to declare test dependencies explicitly. Do not rely on a globally installed `pytest`.

### 3. Run Offline Unit Tests

```bash
python -m pytest tests -q
```

Expected:

- Tests do not require live API credentials.
- Tests do not perform CRM writes.
- Network calls are mocked.

Known audit concern:

- `pytest` may not be declared in `requirements.txt` yet. That should be fixed before any feature merge.

### 4. Run Daily Briefing

```bash
make daily
```

Expected:

- Command runs without API credentials.
- It reports project/open-loop state.
- It should not write to CRM or external systems.

### 5. Run Read-Only API Harness Validation

```bash
cp .env.local.example .env.local
# Fill only read credentials if available.
python scripts/local_api_harness.py validate-env
```

Expected:

- Missing credentials should produce a clear failure.
- The harness should not require write permissions.
- The harness should not fail solely because diagnostic logging cannot write.

### 6. Run One No-Write Workflow

Preferred first target after tests are fixed:

```bash
python scripts/pipeline.py score \
  --company "Acme" \
  --domain "acme.com" \
  --signal funding \
  --signal-date 2026-03-15 \
  --signal-summary "Raised a seed round"
```

If `pipeline.py score` is not the correct CLI shape, document the actual no-write equivalent and update this runbook. The goal is one deterministic workflow that does not require live enrichment APIs or CRM writes.

### 7. Run Signal Audit Dry-Run

```bash
make signal-audit-dry-run
```

Expected artifacts:

- `projects/sample-signal-audit/platform/intake.json`
- `projects/sample-signal-audit/platform/context_pack.json`
- `projects/sample-signal-audit/platform/icp_strategy.json`
- `projects/sample-signal-audit/platform/signal_strategy.json`
- `projects/sample-signal-audit/platform/birddog_signal_manifest.json`
- `projects/sample-signal-audit/platform/accounts.json`
- `projects/sample-signal-audit/platform/crm_push_plan.json`
- `projects/sample-signal-audit/deliverable/signal_audit_summary.md`
- `projects/sample-signal-audit/deliverable/target_accounts.csv`

Safety checks:

- CRM plan has `dry_run: true`.
- CRM plan has `writes_enabled: false`.
- Email sequencing remains `draft_only`.
- No production CRM write or email send occurs.

### 8. Run Email Engagement Dry-Run

Create a local sample payload:

```json
{"events":[{"event":"opened","email":"buyer@acmeanalytics.example"},{"event":"replied","email":"buyer@acmeanalytics.example"}]}
```

Then run:

```bash
python scripts/email_sync.py ingest \
  --client sample-signal-audit \
  --payload /path/to/sample_payload.json \
  --dry-run
```

Expected:

- Events are matched by email domain.
- Engagement and activation scores are recomputed in memory.
- Matrix is not written when `--dry-run` is present.

## Claude Master Files Check

After porting Claude master files, verify they are present and scoped honestly:

```bash
ls master/architecture-roadmap.md
ls master/playbooks/market-map.md
ls master/playbooks/inbox-warmup.md
ls brain/segments.md
```

Check:

- No doc claims a workflow is production-ready unless it passes this runbook.
- Planned nodes are labeled planned/pre-activation.
- Segment guidance aligns with `brain/icp.md`, `brain/personas.md`, and `brain/messaging.md`.

## External Tooling Smoke Checks

External repos should be evaluated without spending API credits.

### research-process-builder

Use as process reference first:

```bash
ls processes
```

Check for relevant process files:

- `find-hiring.md`
- `find-growth-signals.md`
- `find-competitors.md`
- `find-news.md`
- `find-negativity.md`

### ai-ark-cli

Use dry-run mode before any paid/export flow:

```bash
bun run src/index.ts people search \
  --title "VP of Sales" \
  --industry "SaaS" \
  --employees 50-500 \
  --seniority vp director \
  --dry-run
```

Expected:

- Produces review URL and request payload.
- Does not spend credits.

### claude-workspace-template

Use as operating model reference:

- continuity ledgers
- handoffs
- orchestration discipline
- MCP runtime patterns

Do not copy template files blindly into DeployGTM.

## Recovery Exit Criteria

The recovery phase is complete when:

- `AUDIT.md`, `BRANCH_DISPOSITION.md`, `DUPLICATE_WORK.md`, `RUNBOOK.md`, `EXTERNAL_REPOS.md`, `CLEANUP_PLAN.md`, and `CLAUDE_MASTER_FILES.md` are present in GitHub Cloud.
- Claude master files are ported or have an explicit reason for deferral.
- DeployGTM offline tests pass from declared dependencies.
- `make daily` passes.
- One no-write workflow passes.
- `make signal-audit-dry-run` passes.
- `scripts/email_sync.py ingest --dry-run` accepts a sample SuperSend payload.
- PR #6 has a clear merge/close decision.
- Stale branches have documented archive/delete recommendations.
