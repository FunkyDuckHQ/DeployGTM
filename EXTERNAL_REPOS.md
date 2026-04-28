# External Repo Integration Review

Date: 2026-04-28

Purpose: decide how Mitchell Keller's repos should inform DeployGTM without creating more untracked local-only state.

## Principle

External repos must be visible from GitHub Cloud if they are part of the operating plan. Local clones are not enough.

Recommended cloud-visible options:

1. Documentation links only: lowest risk, no vendored code.
2. Git submodules under `external/`: visible in GitHub Cloud/Desktop while preserving upstream history.
3. Selective port: copy/adapt only specific patterns into DeployGTM after review.
4. Full dependency: only after smoke tests and clear runtime need.

For this recovery phase, prefer documentation links plus selective port. Add submodules only after the audit docs are reviewed, because submodules require a real gitlink commit and should not be added casually.

## Adoption Matrix

| Repo | URL | Proposed Status | Why It Matters | Immediate Action |
|---|---|---|---|---|
| `research-process-builder` | https://github.com/MitchellkellerLG/research-process-builder | use now as reference | Validated research processes for competitors, hiring, news, reviews, growth signals, negativity | Map DeployGTM research scripts to these process files before adding more custom research logic. |
| `ai-ark-cli` | https://github.com/MitchellkellerLG/ai-ark-cli | evaluate now | People/company search, dry-run review URLs, verified email exports; possible Apollo complement/replacement | Test only `--dry-run` review URL flows first; no credit-spending export during audit. |
| `claude-workspace-template` | https://github.com/MitchellkellerLG/claude-workspace-template | reference now | Continuity, handoffs, orchestration discipline, MCP/runtime patterns | Adopt concepts in docs/runbooks, not template files wholesale. |
| `auto-prompt-creator` | https://github.com/MitchellkellerLG/auto-prompt-creator | defer but important | Ground-truth prompt evaluation and annealing | Use later to evaluate ICP scoring/research/outreach prompts against known-good examples. |
| `discolike-cli` | https://github.com/MitchellkellerLG/discolike-cli | defer | B2B company discovery, lookalikes, market sizing/enrichment | Evaluate after base pipeline works; could support account discovery. |
| `techsight-cli` | https://github.com/MitchellkellerLG/techsight-cli | defer | Free tech-stack detection via HTTP/DNS/TLS fingerprinting | Evaluate as low-cost signal source after no-write pipeline is green. |

## Proposed Role In DeployGTM Architecture

### Research Layer

Use `research-process-builder` as the standard for web research instructions. DeployGTM should not keep inventing ad hoc company research prompts when validated process files already exist.

Candidate mappings:

- DeployGTM `research.py` -> `find-profiles.md`, `find-news.md`, `find-competitors.md`
- DeployGTM `signals.py` -> `find-hiring.md`, `find-growth-signals.md`
- DeployGTM disqualification/risk checks -> `find-negativity.md`, `find-reviews.md`

### Enrichment Layer

Use `ai-ark-cli` as a possible enrichment lane, especially where dry-run review URLs help validate filter logic before spending credits.

Candidate workflow:

1. Generate target account list in DeployGTM.
2. Run AI Ark dry-run URL for people filters.
3. Review list manually in AI Ark UI.
4. Only then export/enrich if approved.

### Operating Model Layer

Use `claude-workspace-template` to improve process discipline:

- durable handoffs
- continuity/state files
- clear worker/orchestrator split
- explicit end-of-session summaries

DeployGTM already has `master/context-engine.md`; the template should strengthen that, not replace it.

### Prompt Evaluation Layer

Use `auto-prompt-creator` later to stop trusting subjective prompt quality. Build tiny ground-truth sets for:

- ICP scoring
- company research summaries
- outreach copy quality
- disqualification decisions

### Discovery And Signal Expansion

Use `discolike-cli` and `techsight-cli` only after the base system can run. These are expansion inputs, not recovery blockers.

## Submodule Decision

Submodules should be added only if the team wants the external repos visible in GitHub Desktop/Cloud under DeployGTM. If approved, use paths:

```text
external/research-process-builder
external/ai-ark-cli
external/claude-workspace-template
```

Submodule follow-up command set:

```bash
git submodule add https://github.com/MitchellkellerLG/research-process-builder.git external/research-process-builder
git submodule add https://github.com/MitchellkellerLG/ai-ark-cli.git external/ai-ark-cli
git submodule add https://github.com/MitchellkellerLG/claude-workspace-template.git external/claude-workspace-template
git commit -m "Add external reference repos as submodules"
```

Do this after the audit PR is reviewed, not before, unless visibility is the immediate blocker.

## Do Not Do Yet

- Do not copy entire external repos into DeployGTM.
- Do not make AI Ark or other paid APIs part of the first green test loop.
- Do not add n8n or workflow orchestration until the code-first loop is proven.
- Do not replace existing scripts before mapping the behavior they currently provide.
