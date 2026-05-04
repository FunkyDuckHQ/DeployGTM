# DeployGTM — Master Context

## Current Recovery State — Read First

As of 2026-05-04, PR #7 (`Recover DeployGTM Signal Audit system`) has been merged into `main`, and the repo now treats Clarify as the preferred CRM/workspace candidate while keeping HubSpot as a compatibility adapter.

The repo has been re-centered around Signal Audit as the entry offer and DeployGTM as the end-to-end operated GTM system. Future Claude/Codex sessions should read `master/agent-handoff.md`, `docs/clarify-api-cli-strategy.md`, `RUNBOOK.md`, `AUDIT.md`, `BRANCH_DISPOSITION.md`, `DUPLICATE_WORK.md`, `EXTERNAL_REPOS.md`, `CLAUDE_MASTER_FILES.md`, and `CLEANUP_PLAN.md` before making architectural changes.

Important operating constraints:
- GitHub Cloud `FunkyDuckHQ/DeployGTM` is the source of truth.
- Do not work from local-only clones as the final artifact.
- Do not touch `yourfinancialguru` for this recovery work.
- Do not delete old branches, force push, write to production CRM, or send email during recovery.
- Use `make signal-audit-dry-run`, `python3 -m pytest tests -q`, and `make daily` as the first trust loop.
- n8n is the workflow runtime after scripts are proven; Python remains the business logic layer.
- Complex APIs and CLIs must go through the DeployGTM lifecycle: validate, describe capabilities, read, plan, dry-run, write with confirmation, sync events, and save receipts.

## Who We Are

DeployGTM is a GTM engineering practice run by Matthew Stegenga. We build outbound pipeline infrastructure for early-stage B2B SaaS companies. We don't advise — we build. The client walks away with a working revenue system, not a strategy deck.

## What We Do

We design, build, and operate the systems that turn signals into pipeline. Signal detection, enrichment, messaging intelligence, CRM automation, outreach sequencing — the full stack, connected and running.

### Service Architecture

**Signal Audit ($3,500 | 2-week engagement)**
- Diagnostic of the client's current GTM motion
- ICP validation and TAM construction
- Signal mapping: which signals indicate buying intent for their specific product
- Enrichment of target accounts with pain hypotheses
- Deliverable: prioritized account list, signal report, outreach templates, architecture recommendation
- Goal: show them what they're missing and what the system should look like

**Pipeline Engine Retainer ($7,500/month)**
- Full build and operation of the outbound pipeline system
- BirdDog signal monitoring on target accounts
- Ongoing enrichment and outreach generation
- CRM/workspace setup, workflows, field mapping, lead scoring, and writeback planning
- Octave brain configuration for messaging intelligence
- Weekly signal reports, pipeline analysis, outreach iteration
- Goal: working revenue system that generates qualified meetings

**Embedded tools (included in every engagement):**
- BirdDog (signal monitoring) — we are an authorized reseller partner earning 30% recurring commission
- Octave (messaging intelligence) — integrated for ICP/persona/messaging context
- Both become sticky infrastructure the client continues using after engagement

## Who We Serve

### Ideal Client Profile (ICP)

**Primary:** B2B SaaS founders, Seed to Series A
- 5-30 employees
- Have a product with early traction (some customers, some revenue)
- Selling to technical or enterprise buyers
- Founder is still doing sales OR just hired first 1-2 AEs
- No repeatable pipeline infrastructure exists
- Using a modern CRM/workspace or willing to adopt one; Clarify is preferred when it fits, HubSpot is supported for compatibility
- Based in US (no timezone constraint for us — we're remote)

**Trigger signals that indicate readiness to buy:**
- Just raised a round (Seed or A) — have money to spend on GTM
- Posted a job for SDR, BDR, or AE — investing in sales but may not have the infrastructure to support them
- Founder posting on LinkedIn about pipeline struggles, outbound challenges, or hiring sales
- Recently churned a fractional CRO or agency — tried the advice route, now needs the build route
- Using Clay or Apollo but not getting results — have the tools but not the system

**Disqualifiers:**
- Pre-product (nothing to sell yet)
- Consumer/B2C (not our motion)
- Wants only "more leads" without willingness to build infrastructure
- Budget under $3,500 for any engagement
- Expects guaranteed reply rates or meeting counts (we build systems, not guarantees)

### Personas We Sell To

**Persona 1: The Founder-Seller**
- CEO/CTO who is doing sales themselves
- Pain: drowning in product + sales + fundraising, no time to build outbound properly
- What they want: someone to build the pipeline engine so they can focus on product and closing
- How we talk to them: "You shouldn't be spending 3 hours a day on prospecting. Let me build the system that does it."

**Persona 2: The First Sales Leader**
- VP Sales, Head of Sales, or Founding AE at a seed/A company
- Pain: inherited nothing — no CRM hygiene, no sequences, no signal detection, no playbook
- What they want: infrastructure underneath them so they can actually sell
- How we talk to them: "You were hired to close deals, not build a tech stack from scratch. I'll build the engine, you drive it."

**Persona 3: The Overwhelmed RevOps/Growth Person**
- Solo ops person trying to manage CRM, tools, data, and enablement
- Pain: too many disconnected tools, no time to architect the system properly
- What they want: someone who understands the full stack and can wire it up correctly
- How we talk to them: "I'll build the orchestration layer so your tools actually talk to each other."

## How We Position Against Alternatives

**vs. Fractional CRO:** They give you strategy. We give you infrastructure. You walk away with a working system, not a deck.

**vs. Clay Agency:** They optimize one piece of the funnel (usually cold email). We build the full closed-loop system — signals to pipeline to CRM to measurement. And we don't get fired when reply rates fluctuate because we're not hired for reply rates.

**vs. Hiring an in-house GTME:** We're faster to deploy (no recruiting, no ramp), we come with pre-built playbooks, and we cost less than a full-time hire. If they outgrow us, that's a win — we helped them build the system their in-house person inherits.

**vs. Doing nothing:** Every month without pipeline infrastructure is a month of founder time burned on manual prospecting, missed signals, and inconsistent outreach. The cost of inaction is measurable.

## Our Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Intelligence & Orchestration | Claude (claude.ai + Claude Code) | Research, enrichment, analysis, automation, thought partnership |
| Signal Detection | BirdDog | Continuous monitoring of target accounts for buying signals |
| Messaging Intelligence | Octave | ICP/persona context brain for calibrated messaging across channels |
| Enrichment | Clay + Claude | Contact/company data enrichment, waterfall lookups |
| CRM / Workspace | Clarify first; HubSpot compatibility | Rep-facing system of record, tasks, lists, deals, field mapping, writeback |
| Outreach | Clarify Campaigns / HubSpot Sequences / Apollo | Sequence-ready drafts, controlled testing, engagement feedback |
| Data Providers | Apollo, web search, niche APIs | Contact finding, email verification, firmographic data |

## Rules for Claude Code

- Never hard-code API keys. Always use .env files.
- Never write to a client's production CRM without explicit confirmation.
- When enriching data, always include a confidence level and source.
- Outreach drafts should lead with pain hypothesis, not product features.
- Keep messaging conversational and direct. No AI-sounding language. No "I hope this email finds you well." No "leveraging synergies."
- When in doubt about ICP fit, disqualify. We'd rather work with 5 right clients than 20 wrong ones.
- Every workflow should answer: what signal triggers this, what action does it take, what data does it write back, and how do we know it worked.

## About Matthew Stegenga

10+ years B2B SaaS sales. Founding AE at PlayerZero ($0 to $500K ARR, $1M+ TCV). Enterprise AE at Twilio (APIs), ngrok (developer infrastructure), PGI (communications SaaS). Background in financial services (E*TRADE, Wells Fargo Advisors). Deep experience selling to technical buyers — engineers, architects, CTOs. Built GTM from scratch at multiple companies. Based in Atlanta metro (Cumming, GA). Remote.

Core differentiator: understands both the business (how companies buy, how revenue works, where friction lives) AND the technical layer (how tools connect, how data flows, how systems break). Most GTMEs have one or the other. Matthew has both.
