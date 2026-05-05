# Mitchell Keller GitHub Deep Dive

Date: 2026-05-05

Purpose: decide which Mitchell Keller / LeadGrow public repos should shape DeployGTM as Flashpoint onboarding approaches.

## Bottom Line

Adopt the workflow ideas now. Do not vendor the code yet.

The strongest immediate value is Mitchell's research-process-builder pattern: define a research goal, generate/test search patterns, score quality and consistency, keep kill lists, stop early when evidence is sufficient, and output source-backed findings. That maps directly into DeployGTM's Signal Audit, account scoring, and copy packet workflow.

For Flashpoint, this means the first GTM pilot should not start with generic agency lead lists. It should start with validated research processes for:

- current revenue mapping
- agency universe discovery
- agency proof fit
- AI/self-serve pressure
- survey ops and programming pain
- bank/CPG/product innovation vertical fit
- repeat/tracker potential
- buyer/contact mapping

## Repo Inventory

Source: public GitHub API inventory of `MitchellkellerLG`, run 2026-05-05.

| Repo | What It Is | DeployGTM Decision |
| --- | --- | --- |
| `research-process-builder` | Validated web research processes with tested search patterns, kill lists, stop conditions, and output templates. | Adopt now as methodology. |
| `ai-ark-cli` | Company/person search, verified email export, dry-run review URLs, domain include helper. | Evaluate as Apollo/Clay complement; dry-run only first. |
| `discolike-cli` | B2B company discovery, lookalike search, market sizing, profile/append workflows. | Evaluate for target universe building after ICP is narrowed. |
| `techsight-cli` | Free technographic detection from HTTP/DNS/TLS/HTML signals, no API key. | Adopt as optional low-cost enrichment pattern. |
| `attio-cli` | Agent-friendly Attio CRM CLI with JSON output and CRUD coverage. | Reference if Flashpoint wants Attio as the light CRM. |
| `claude-workspace-template` | Claude Code continuity, handoffs, orchestration, MCP runtime patterns. | Reference for operating discipline; do not copy wholesale. |
| `auto-prompt-creator` | Prompt evaluation and annealing with train/validation/holdout, rubrics, and graduation. | Defer; use later for copy/research prompt evals. |
| `system-comparison` | Gap assessment skill for comparing two systems and producing a ranked steal list. | Reference later for vendor/process comparisons. |
| `trigify-cli` | Social listening and signal intelligence CLI/MCP. | Defer until social signals are proven useful for Flashpoint. |
| `n8n-agent-cli` | n8n agent CLI/MCP wrapper. | Defer; our n8n stance is scripts first, orchestration later. |
| `mcp-cli` | Lightweight MCP interaction CLI. | Defer. |
| `Agent-Skills-for-Context-Engineering` | Context engineering skills. | Reference for context hygiene only. |
| `Continuous-Claude-v2` | Session continuity through ledgers/handoffs. | Reference only; DeployGTM already has handoff docs. |
| `List-processing-project-v1` | Claude Code list-processing baseblocks. | Defer. |
| `clawdbot` | General assistant project. | Ignore for DeployGTM. |

## What Is Working

### 1. Validated research processes beat ad hoc prompting

`research-process-builder` describes a six-phase method: define the goal, generate candidate search patterns, test against sample companies, score quality and consistency, iterate until 90%+, then assemble a portable process file with extraction rules, stop conditions, kill lists, and output templates.

DeployGTM should mirror that shape for Flashpoint. Every repeatable research workflow should have:

- goal
- good result definition
- inputs
- search patterns
- kill patterns
- extraction rules
- stop conditions
- output shape
- source trace

### 2. Search kill lists save money and time

The research-process-builder README calls out that kill lists avoid wasting 30-40% of search budget. For Flashpoint, this matters because agency research can get noisy fast: "market research AI" returns industry think pieces, not target-account evidence.

DeployGTM should force every Flashpoint research process to include `do_not_search` patterns.

### 3. Research should be process-chained

Mitchell's hiring process explicitly points to job-role-insights as a companion process after finding roles. That pattern generalizes:

```text
profile -> growth signals -> hiring/activity -> role insights -> competitor/positioning -> account score -> copy packet
```

For Flashpoint, this becomes:

```text
agency profile -> vertical/client proof -> AI pressure -> survey ops pain -> buyer map -> urgency score -> discovery/copy
```

### 4. Dry-run and review URLs are the right paid-data guardrail

AI Ark's CLI emphasizes review URLs and `--dry-run` before spending credits. DiscoLike similarly supports `count`, `--dry-run`, max record caps, budget guardrails, and a count -> validate -> confirm workflow.

DeployGTM should make this a vendor rule:

- count or dry-run first
- review in vendor UI if available
- cap returned records
- store the review URL or estimate
- only spend/export after approval

### 5. Free technographics are useful, but only as a secondary signal

TechSight claims no API key is required and scans HTTP headers, DNS TXT, cookies, meta tags, scripts, HTML patterns, and TLS certs. For Flashpoint, tech stack is not the core buying signal, but it can help detect whether an agency runs modern marketing/research ops infrastructure.

Use it as enrichment, not as the basis for ICP.

### 6. Attio is a credible lightweight CRM candidate if Flashpoint wants modern CRM

The Attio CLI is built around JSON output and object/note/task control. That fits agent-assisted workflows. Still, HubSpot may be easier for client acceptance. The decision should be made on Flashpoint's team behavior, not tooling taste.

## Flashpoint Adoption

### Adopt Now

- `research-process-builder` methodology.
- Flashpoint-specific research process stack.
- Dry-run/cost-safe vendor workflow rules.
- Source-traced agency scoring and copy packet requirements.
- Light CRM/source-of-truth field list from day one.

### Evaluate During First Two Weeks

- AI Ark dry-run review URLs for buyer/contact filters.
- DiscoLike count/dry-run for research agency universe sizing.
- TechSight for free enrichment of agency domains.
- Attio vs HubSpot as the lightweight CRM.

### Defer

- Trigify social listening until social signals prove useful.
- n8n agent CLI until deterministic scripts are stable.
- Auto-prompt optimization until we have real Flashpoint outcomes and failures.
- Any MCP-first integration.

## Source Notes

- Mitchell Keller GitHub profile lists 15 public repositories and popular repos including `research-process-builder`, `auto-prompt-creator`, `discolike-cli`, `ai-ark-cli`, `system-comparison`, and `techsight-cli`: https://github.com/MitchellkellerLG
- `research-process-builder` README describes the six-phase methodology, nine process files, 90%+ target reliability, and key discoveries around kill lists, year variables, domain-qualified queries, ATS searches, and community signals: https://github.com/MitchellkellerLG/research-process-builder
- `find-growth-signals.md` defines growth signal research across website infrastructure, content, social/community, lead capture, third-party buzz, events, and fallback sources: https://github.com/MitchellkellerLG/research-process-builder/blob/master/processes/find-growth-signals.md
- `find-hiring.md` uses careers, ATS, direct careers pages, year-filtered hiring, and fallback searches, with LinkedIn jobs as direct-visit only: https://github.com/MitchellkellerLG/research-process-builder/blob/master/processes/find-hiring.md
- `find-job-role-insights.md` extracts role basics, tech stack, pain points, team context, and strategic signals from job descriptions: https://github.com/MitchellkellerLG/research-process-builder/blob/master/processes/find-job-role-insights.md
- `find-competitors.md` uses alternatives/competitors/vs patterns, category market maps, structured sources, and practitioner opinions: https://github.com/MitchellkellerLG/research-process-builder/blob/master/processes/find-competitors.md
- `find-profiles.md` starts company research with structured profiles, funding data, LinkedIn, ZoomInfo, and RocketReach: https://github.com/MitchellkellerLG/research-process-builder/blob/master/processes/find-profiles.md
- `ai-ark-cli` README documents people/company search, export, batch CSV input, dry-run review URLs, and domain-list paste helper: https://github.com/MitchellkellerLG/ai-ark-cli
- `discolike-cli` README documents domain similarity, ICP text, phrase match, `auto-icp`, count-first, dry-run, max-record caps, budget guardrails, and count -> validate -> confirm workflow: https://github.com/MitchellkellerLG/discolike-cli
- `techsight-cli` README documents no-key tech detection using HTTP/DNS/TLS/HTML vectors: https://github.com/MitchellkellerLG/techsight-cli
- `attio-cli` README documents agent-friendly JSON output and object/note/task commands for Attio: https://github.com/MitchellkellerLG/attio-cli
- `claude-workspace-template` README documents orchestration, continuity ledgers, handoffs, hooks, and MCP runtime concepts: https://github.com/MitchellkellerLG/claude-workspace-template
