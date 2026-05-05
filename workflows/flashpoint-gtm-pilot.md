# Flashpoint GTM Pilot Workflow

## Purpose

Turn the Flashpoint "contract SDR" conversation into a 6-month GTM test pilot that builds the motion while testing it.

This is not a meeting-volume workflow. It is a learning system for finding the agency wedge, proving what messages work, and turning early GTM chaos into a source-of-truth pipeline.

## Operating Thesis

Flashpoint likely needs:

- a lightweight source of truth
- current revenue mapping
- one or two usable proof stories
- a narrower agency ICP
- target-account research
- controlled messaging tests
- live discovery capture
- pricing/packaging feedback
- founder-led deal support where trust matters

## Phase 0: Commercial Scope Guardrail

Before tooling:

- define whether Flashpoint means meeting setting, discovery, opportunity creation, deal support, or full GTM pilot
- define hours per week
- define who closes
- define whether tool costs are reimbursed
- define whether success comp attaches to meetings, opportunities, closed revenue, cash collected, or materially influenced revenue
- define post-contract tail

Do not start paid-data work until tool reimbursement and approval rules are clear.

## Phase 1: Source Of Truth

Start with Google Sheet only if needed, but set up these fields from day one:

| Field | Why It Exists |
| --- | --- |
| account | Agency or target account name |
| domain | Entity resolution and enrichment |
| contact | Buyer/contact name |
| title | Buyer/persona mapping |
| segment | Agency segment or enterprise segment |
| use_case | Survey programming, tracking, behavioral testing, AI research assist, etc. |
| source | Where the account came from |
| stage | Pipeline stage |
| next_step | What happens next |
| owner | Matthew / founder / Flashpoint owner |
| last_touch | Activity recency |
| next_touch | Follow-up discipline |
| objection | Market learning |
| repeat_potential | One-off vs recurring potential |
| project_type | Research project type |
| estimated_value | Deal size or project value |
| founder_involvement_needed | Whether Christian/Stephen/Ben is needed |
| proof_asset_fit | Which story supports outreach |

CRM decision:

- Week 1-2: Google Sheet is acceptable for controlled testing.
- After week 2: move into HubSpot, Attio, Pipedrive, Airtable, or another agreed source of truth.
- Do not let CRM implementation become the project.

## Phase 2: Revenue Map

Tag current revenue by:

- one-off
- repeat
- tracking
- usage
- true subscription
- agency
- bank
- enterprise
- project type
- margin
- repeat potential
- proof/case-study potential

Output:

- "what to sell first"
- "what not to sell yet"
- "best proof asset candidate"
- "pricing/packaging unknowns"

## Phase 3: Proof Asset

Build one practical proof story before scaling outreach.

Minimum proof asset:

- customer type
- problem
- old way
- Flashpoint way
- result/speed/cost/confidence
- why they came back
- what this proves
- claims that are safe vs risky

No proof asset, no scaled outreach.

## Phase 4: Agency Universe And Research

Use Mitchell-style validated research processes:

```text
company profile
  -> growth/marketing signals
  -> hiring/activity signals
  -> job-role insights where relevant
  -> competitive positioning
  -> Flashpoint signal stack
  -> ICP/urgency score
```

First target universe should be narrow:

- small/midsized research agencies
- agencies doing survey programming
- agencies serving banks, CPG, product/innovation, or emerging markets
- agencies under AI/self-serve pressure
- agencies needing RFP differentiation

Vendor guardrail:

- AI Ark: dry-run and review URL before export.
- DiscoLike: count -> 10-record validation -> confirmation before full pull.
- TechSight: free technographic enrichment only.
- Clay/Apollo: enrichment after segment and signal logic are approved.

## Phase 5: Scoring And Routing

Use `clients/flashpoint/config/scoring.json`.

Core scoring dimensions:

- agency fit
- research ops pain
- vertical relevance
- repeat revenue potential
- proof asset fit
- ability to buy
- evidence confidence

Urgency comes from signals:

- AI/self-serve pressure
- survey ops/programming need
- bank/CPG/product innovation client work
- tracking or monitoring recurrence
- RFP differentiation pressure
- hiring or role evidence tied to research operations

Routes:

- founder_assisted_discovery
- enrich_and_test_sequence
- monitor_for_signal
- exclude_or_revisit_later

## Phase 6: Copy And Discovery

Use the DeployGTM Prospect Copy Workflow.

Rules:

- entity resolution first
- source trace required
- copy packet required
- copy quality score must be 85+
- no unsupported claims
- no "we help companies like yours"

Discovery should capture:

- does the agency understand Flashpoint?
- which pain resonates?
- which use case is easiest to buy?
- do they fear replacement?
- do they see delivery leverage?
- preferred pricing model
- objections
- next step

## Phase 7: Weekly Learning Loop

Weekly report should include:

- accounts researched
- accounts scored
- sequences/messages tested
- positive replies
- negative replies
- neutral/curious replies
- meetings
- qualified opportunities
- objections by segment
- proof asset performance
- pricing/packaging feedback
- CRM hygiene issues
- next week's hypothesis

## 30/60/90 Checkpoints

### Day 30

- source of truth live
- revenue map completed
- first proof asset drafted
- first 100-250 agency accounts identified or scoped
- first signal definitions tested manually
- first message tests launched or ready

### Day 60

- top responding segments identified
- objections categorized
- qualified opportunity definition tightened
- packaging/pricing feedback summarized
- CRM/pipeline stages stable
- founder involvement rules defined

### Day 90

- clear recommendation: continue, narrow, pivot, or stop
- best agency wedge documented
- repeatable research and scoring process
- proof-backed outreach angle
- forecastable next-quarter pilot plan

## Source Notes

- Engagement-shape source: user-provided Flashpoint GTM pilot context, shared May 5, 2026.
- Research workflow source: https://github.com/MitchellkellerLG/research-process-builder
- Dry-run/cost guardrail sources: https://github.com/MitchellkellerLG/ai-ark-cli and https://github.com/MitchellkellerLG/discolike-cli
- Free technographic enrichment source: https://github.com/MitchellkellerLG/techsight-cli
