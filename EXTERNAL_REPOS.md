# External Repo Integration Review

Date: 2026-04-28

Purpose: decide how Mitchell Keller's repos should inform DeployGTM without creating more untracked local-only state.

## Update: 2026-05-05 Flashpoint Readiness Pass

Mitchell Keller's public GitHub profile now shows 15 public repos. The useful DeployGTM move is still selective adoption, not wholesale import.

What changed for Flashpoint:

- Added a full deep-dive at `docs/mitchell-keller-github-deep-dive.md`.
- Added `clients/flashpoint/` as a client workspace.
- Added `workflows/flashpoint-gtm-pilot.md`.
- Adopted the `research-process-builder` method into Flashpoint agency research:
  - define the research goal
  - state what a good result looks like
  - use tested search patterns
  - keep kill patterns
  - stop when evidence is sufficient
  - capture a source trace
- Added Flashpoint-specific signals for:
  - AI/self-serve research pressure
  - survey ops or programming need
  - bank/CPG/product innovation proof fit
  - tracker or monitoring repeat potential
  - RFP differentiation pressure
  - research ops hiring signal
- Adopted paid-data guardrails from AI Ark and DiscoLike:
  - count or dry-run first
  - review URL when available
  - 10-record validation before full export
  - client approval before paid data export

What did not change:

- No external repo code was vendored.
- No submodules were added.
- No real vendor integrations were enabled.
- No MCP/n8n/social-signal runtime was made core to DeployGTM.

Operational decision:

Use Mitchell's repos as a free workflow library and vendor watchlist. DeployGTM should keep the core engine file/API/function-first and client-configurable.

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

## Additional CLI And Agent Tooling Watchlist

Source: https://github.com/stars/elviskahoro/lists/cli

Use this list as a research backlog only. Do not add tools to DeployGTM just because they are interesting. Any candidate must either improve the trusted Signal Audit loop, make agent work more observable, or reduce operational risk.

Relevant candidates to evaluate later:

| Tool | URL | Possible Role | Decision |
|---|---|---|---|
| `agentsview` | https://github.com/wesm/agentsview | Local-first session intelligence for Claude/Codex and other coding agents; could help Matthew understand what happened across machines. | Evaluate after one real no-write Signal Audit. |
| `agor` | https://github.com/preset-io/agor | Multiplayer canvas for Claude Code, Codex, Gemini, git worktrees, and agent conversation tracking. | Reference only until agent workflow is stable. |
| `CodeBoarding` | https://github.com/CodeBoarding/CodeBoarding | Interactive architecture diagrams for codebases; useful for understanding AI-built code visually. | Evaluate as documentation aid, not runtime dependency. |
| `noodles` | https://github.com/unslop-xyz/noodles | Interactive diagrams for understanding AI-generated codebases. | Evaluate as a repo-understanding aid. |
| `contextai` | https://github.com/madeburo/contextai | Generates `AGENTS.md`, `CLAUDE.md`, `.cursorrules` from one context config. | Reference for future context hygiene; do not replace current handoff files yet. |
| `openai/codex-plugin-cc` | https://github.com/openai/codex-plugin-cc | Lets Claude Code delegate review/work to Codex. | Reference only; use native Codex/GitHub workflow first. |
| `googleworkspace/cli` | https://github.com/googleworkspace/cli | CLI access to Drive, Gmail, Calendar, Sheets, Docs, and Chat; may help Google Drive intake later. | Evaluate only when Drive intake becomes the blocker. |
| `Doppler CLI` | https://github.com/DopplerHQ/cli | Secrets/config management. | Defer; `.env` plus current guardrails are enough for recovery. |
| `Infisical agent-vault` | https://github.com/Infisical/agent-vault | Credential proxy/vault for AI agents. | Defer until multi-agent automation needs stronger secret isolation. |
| `inngest` | https://github.com/inngest/inngest | Durable workflow orchestration for step functions and AI workflows. | Compare against n8n only after Python scripts are proven. |
| `openai-agents-python` | https://github.com/openai/openai-agents-python | Multi-agent framework. | Reference only; do not rebuild DeployGTM around agent frameworks. |
| `pydantic/logfire` | https://github.com/pydantic/logfire | Observability for LLM/agent systems. | Consider when runtime workflows exist and need monitoring. |

Evaluation rule:

1. Read README and license.
2. Confirm active maintenance and security posture.
3. Run only local/no-write smoke checks.
4. Document the exact problem it solves.
5. Add to DeployGTM only through a small PR with tests/runbook updates.

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
