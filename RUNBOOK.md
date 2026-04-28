# Recovery Runbook

Date: 2026-04-28

Purpose: establish a trusted, repeatable, no-write test loop before additional feature work or branch merges.

## Golden Rules

- GitHub Cloud is source of truth.
- No CRM writes during recovery.
- No branch deletion during recovery.
- No force pushes.
- No large branch merges until subsystem review is complete.
- Every command below should either pass or produce a documented failure.

## DeployGTM Trusted Loop

Run from a fresh clone or GitHub Codespace/dev environment.

```bash
git clone https://github.com/FunkyDuckHQ/DeployGTM.git
cd DeployGTM
git switch recovery/full-audit-cleanup
```

### 1. Inspect Repo State

```bash
git status --short --branch
git branch --all --verbose --no-abbrev
```

Expected:

- On `recovery/full-audit-cleanup`.
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

## yourfinancialguru Trusted Loop

Run separately in the `yourfinancialguru` repo.

```bash
git clone https://github.com/FunkyDuckHQ/yourfinancialguru.git
cd yourfinancialguru
```

### 1. Install

```bash
npm install
```

### 2. Verify Static Quality

```bash
npm run lint
npm run build
```

Expected:

- No TypeScript/build failures.
- If lint/build scripts are insufficient, add explicit typecheck or test script before merging UI branches.

### 3. Smoke Test App

```bash
npm run dev
```

Manual smoke paths:

- Home page loads.
- Quiz/pulse flow runs.
- Connect flow persists localStorage as expected.
- Results page handles both pulse-only and full profile states.

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

- `AUDIT.md`, `BRANCH_DISPOSITION.md`, `DUPLICATE_WORK.md`, `RUNBOOK.md`, and `EXTERNAL_REPOS.md` are present in GitHub Cloud.
- DeployGTM offline tests pass from declared dependencies.
- `make daily` passes.
- One no-write workflow passes.
- PR #6 has a clear merge/close decision.
- Stale branches have documented archive/delete recommendations.
