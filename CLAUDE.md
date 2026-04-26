# DeployGTM — Master Context

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
- HubSpot CRM setup/optimization, workflows, lead scoring
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
- Using HubSpot or willing to adopt it
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
| CRM | HubSpot | System of record, automation, sequences, pipeline management |
| Outreach | HubSpot Sequences / Apollo | Email sequences, follow-up automation |
| Data Providers | Apollo, web search, niche APIs | Contact finding, email verification, firmographic data |

## Client Session Protocol

When Matthew mentions a client by name (e.g. "I'm working with Peregrine" or "let's look at the Peregrine engagement"), do the following automatically — do not wait to be asked:

1. **Load client context** — Read `projects/<client-slug>/context.md` in full.
2. **Check for unsynced Drive docs** — Run `make sync-client CLIENT=<slug>` (or call the script directly) to pull any new files from Google Drive. If `GDRIVE_INTAKE_FOLDER_ID` is not set, skip and note it.
3. **State what you know** — Briefly summarize the client's current status: engagement type, week, last action, and what's next. One paragraph max.
4. **Ask what to do next** — Unless Matthew has already stated the objective.

Known client slugs and their project directories:

| Client slug | Directory | Engagement |
|---|---|---|
| deploygtm-own | projects/deploygtm-own/ | Client zero — DeployGTM's own outbound |
| peregrine-space | projects/peregrine-space/ | NewSpace outbound — 14 accounts |
| mindra | projects/mindra/ | TBD |
| fibinaci | projects/fibinaci/ | TBD |
| sybill | projects/sybill/ | TBD |
| rex | projects/rex/ | TBD |
| terzo | projects/terzo/ | TBD |

When a new client is mentioned that has no project directory yet:
1. Run `python scripts/pipeline.py new-client --client <slug> --domain <domain>`
2. Run `make sync-client CLIENT=<slug>` to pull any existing Drive docs
3. Populate `projects/<slug>/context.md` from whatever Drive docs and conversation context exist

## Meeting Transcript Protocol

When a meeting transcript lands (from Fireflies, Otter, Fathom, or any recorder writing to Drive):

1. Run `make sync-client CLIENT=<slug>` — the transcript is processed by `sync_client_context.py`, synthesized, and written to context.md automatically.
2. After sync, read the updated context.md.
3. Surface immediately:
   - Which company this meeting was about
   - Key people mentioned (name, title, company)
   - Pain points or buying signals revealed
   - Decisions made
   - Action items (who, what, when)
   - If new client: begin scaffolding context.md — company overview, ICP notes, initial signal map
   - If existing client: check pipeline stats and surface: deal stage, last touch, next scheduled follow-up
4. Send Matthew a brief (Slack or terminal output) — do not wait for him to ask.

## Rules for Claude Code

- Never hard-code API keys. Always use .env files.
- Never write to a client's production CRM without explicit confirmation.
- When enriching data, always include a confidence level and source.
- Outreach drafts should lead with pain hypothesis, not product features.
- Keep messaging conversational and direct. No AI-sounding language. No "I hope this email finds you well." No "leveraging synergies."
- When in doubt about ICP fit, disqualify. We'd rather work with 5 right clients than 20 wrong ones.
- Every workflow should answer: what signal triggers this, what action does it take, what data does it write back, and how do we know it worked.
- When new signals come in (from Apollo, BirdDog, or manual entry), run `make signals-to-matrix CLIENT=<slug>` to bridge them into the client's account matrix before any outreach decisions.

## About Matthew Stegenga

10+ years B2B SaaS sales. Founding AE at PlayerZero ($0 to $500K ARR, $1M+ TCV). Enterprise AE at Twilio (APIs), ngrok (developer infrastructure), PGI (communications SaaS). Background in financial services (E*TRADE, Wells Fargo Advisors). Deep experience selling to technical buyers — engineers, architects, CTOs. Built GTM from scratch at multiple companies. Based in Atlanta metro (Cumming, GA). Remote.

Core differentiator: understands both the business (how companies buy, how revenue works, where friction lives) AND the technical layer (how tools connect, how data flows, how systems break). Most GTMEs have one or the other. Matthew has both.