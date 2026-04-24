# DeployGTM — Build Log & Progress

*Single source of truth for what's been built, what's activated, and what's next.*
*Updated: 2026-04-24*

---

## Status: ACTIVE — ACCOUNT MATRIX LIVE, SIGNALS UNVERIFIED

System is fully constructed. Account matrix operational for Peregrine (14/14 accounts ready) and DeployGTM own (12 accounts, 0 verified — signals need Crunchbase/LinkedIn update before batch outreach can run).

Immediate blocker: verify signals for Loops, Orb, Mintlify, Plain, Campsite, Koala in `projects/deploygtm-own/data/deploygtm_accounts.json`, then run `make batch-outreach CLIENT=deploygtm`.

---

## Build timeline

### April 1 — Repo initialized
- GitHub repo created: `FunkyDuckHQ/DeployGTM`
- Initial folder structure: `master/`, `projects/`, `brain/`
- Uploaded `deploygtm_context_build.zip` with project context files

### April 15 — Context files loaded
- Project files extracted: peregrine-space, mindra, fibinaci, sybill, rex, terzo
- Each with `context.md`, `handoff.md`, `open-loops.md`
- `master/context-engine.md` — operating architecture doc

### April 16 — Core pipeline built (Claude)
**Infrastructure:**
- `config.yaml` — tool toggles (Apollo, BirdDog, HubSpot, Octave, all on/off)
- `.env.example` — all API keys documented
- `.mcp.json` — fetch + Google Drive MCP servers
- `requirements.txt` — anthropic, requests, click, pyyaml, python-dotenv

**Brain (Octave replacement, free + local):**
- `brain/icp.md` — ICP definition, trigger signals, hard disqualifiers
- `brain/personas.md` — Founder-Seller, First Sales Leader, RevOps/Growth
- `brain/messaging.md` — message structure, per-persona openers
- `brain/objections.md` — 8 objections with positioning + responses
- `brain/product.md` — Signal Audit + Retainer specs, pricing

**Core scripts:**
- `scripts/score.py` — ICP Fit (1–5) × Signal Strength (1–3) → Priority
- `scripts/research.py` — Claude account research with prompt caching
- `scripts/apollo.py` — Apollo v1 contact search + company enrichment (with retry/backoff)
- `scripts/outreach.py` — Claude message gen: primary + 2 follow-ups + LinkedIn note
- `scripts/hubspot.py` — HubSpot v3: upsert company + contact + deal creation
- `scripts/pipeline.py` — main CLI: run / push / score / setup-hubspot / new-client
- `scripts/batch.py` — batch runner from CSV with resume support
- `scripts/export.py` — output/ → HubSpot import CSVs
- `scripts/birddog.py` — BirdDog signal monitoring integration
- `scripts/transcript.py` — voice memo → project update

**Active project artifacts:**
- `projects/peregrine-space/` — GTM OS proof-point for Tyler + send message
- `projects/mindra/` — 30/60/90 plan for Deniz
- `projects/fibinaci/` — advisory response posture + red lines
- `projects/sybill/` — prep questions for next conversation
- `projects/rex/` — discovery prep notes
- `projects/terzo/` — scheduling note for Brodie
- `projects/deploygtm-own/context.md` — own pipeline status

### April 17 — Signal layer, engagement tooling, playbooks (Claude)
- `scripts/signals.py` — Apollo hiring/funding + YC batch signal detection
- `scripts/report.py` — weekly signal + pipeline report
- `scripts/signal_audit.py` — full Signal Audit engagement CLI (new/week1/week2/deliverable)
- `scripts/follow_up.py` — full cadence: due/generate/log/respond/create-tasks
- `scripts/qualify.py` — inbound ICP qualifier
- `scripts/daily.py` — morning briefing (no API needed)
- `brain/clients/` — per-client brain override for Signal Audit engagements
- `Makefile` — 40+ targets covering all workflow commands
- `master/playbooks/enrichment.md` — signal → research → enrich → score → activate
- `master/playbooks/signal-audit.md` — $3,500 / 2-week engagement playbook
- `master/playbooks/outreach-ops.md` — full outreach loop: signal to close
- `master/playbooks/hubspot-setup.md` — one-time HubSpot configuration guide

### April 18 — UI, quality gates, advanced tooling (Claude)
- `scripts/crm_audit.py` — data quality scanner before every HubSpot push
- `scripts/sequence_builder.py` — generates HubSpot sequence step templates
- `scripts/precall.py` — pre-call brief generator for discovery/close calls
- `scripts/hubspot.py` — extended: deal creation + create-deal / advance-deal CLI
- `ui/app.py` — Streamlit dashboard (Dashboard / Accounts / Follow-ups / Outreach tabs)
- `ui/sample_data.py` — realistic preview data when output/ is empty
- `master/playbooks/qualification.md` — 5 criteria, call structure, close language
- `master/playbooks/retainer-ops.md` — monthly rhythm, renewal, offboarding
- Bug fix: `daily.py` / `crm_audit.py` / `ui/app.py` now read from `output/[client]/` subdirs
- Apollo retry logic: 4 retries with 2/4/8/16s backoff on 429/5xx

### April 21 — API test harness, design principles (Codex/GPT)
- `scripts/local_api_harness.py` — validates HubSpot + external API connections
- `tests/test_local_api_harness.py` — offline unit tests with mocks
- `.env.local.example` — separate env file for local API testing
- `master/design-principles.md` — 7 principles: local-first, safe by default, observable, testable
- `master/local-api-testing-plan.md` — harness runbook
- `logs/` directory — structured JSONL run logs
- README — added local API harness section

### April 23–24 — Account matrix system + DeployGTM own outbound (Claude Code)
**Schema and seed data:**
- `projects/deploygtm-own/account_matrix_schema.json` — JSON Schema draft-07 for client-agnostic account intelligence; all required fields, valid enums for signal types, icp_tier 1–3
- `projects/deploygtm-own/data/peregrine_accounts.json` — 14 accounts across 4 NewSpace segments, all signals verified, 14/14 ready
- `projects/deploygtm-own/data/deploygtm_accounts.json` — 12 accounts across all 5 DeployGTM segments (A–E); tier-1: Loops, Orb, Plain, Campsite; tier-2: Mintlify, Koala + 6 archetype slots. Signals unverified — update VERIFY fields before outreach.

**Scripts (client-agnostic, all parameterized by `--client <slug>`):**
- `projects/deploygtm-own/scripts/init_matrix.py` — scaffold schema-valid stub for a new client
- `projects/deploygtm-own/scripts/generate_outreach.py` — generate 3 angle variants for one account; prompt caching on system prompt; model `claude-sonnet-4-6`
- `projects/deploygtm-own/scripts/batch_outreach.py` — run generate across all tier-filtered accounts; auto-skips accounts with unresolved VERIFY/FILL_IN markers; prints cache hit stats; `--force` to override
- `projects/deploygtm-own/scripts/verify_signals.py` — audit matrix for blocked accounts (VERIFY/FILL_IN in signal description, date, company, or domain); `--strict` exits 1 if any blocked; imported by batch_outreach for auto-skip
- `projects/deploygtm-own/scripts/variant_tracker.py` — SQLite tracker for variant performance; records angle, sentiment, date; aggregates response rate by angle_variant
- `projects/deploygtm-own/scripts/weekly_signal_report.py` — markdown weekly report: signal changes, priority table, engagement threshold flags (≥12), variant activity; optional BirdDog integration

**Supporting artifacts:**
- `brain/segments.md` — 5 DeployGTM segments (A–E) with triggers, frames, angles, openers, objections, avoid-list
- `master/playbooks/market-map.md` — 5-step method for constructing segment maps for any client
- `master/playbooks/inbox-warmup.md` — dedicated outbound domain, SPF/DKIM/DMARC, volume ramp table, seed testing, daily reality checks
- `master/matthew-working-conditions.md` — fully filled in: working hours, comms style, decision authority, things that waste time, standing rules, current focus, projects in flight

**Makefile targets added:** `init-matrix`, `outreach-variants`, `batch-outreach`, `verify-signals`, `variant-respond`, `variant-list`, `variant-report`, `weekly-report`

**Tests:** `tests/test_account_matrix.py` — 34 tests covering all 6 scripts; uses `importlib.util` + tempdir isolation so no real data is touched; classes: TestPeregrineSeedData, TestGenerateOutreach, TestVariantTracker, TestWeeklyReport, TestInitMatrix, TestVerifySignals, TestBatchOutreach

---

## Current system inventory

### Scripts (20)
| Script | Purpose | Status |
|--------|---------|--------|
| `daily.py` | Morning briefing | ✅ Ready (no API needed) |
| `pipeline.py` | Main orchestration | ✅ Ready |
| `batch.py` | Batch runner | ✅ Ready |
| `signals.py` | Signal detection (Apollo + YC) | ✅ Ready — needs `APOLLO_API_KEY` |
| `research.py` | Claude research | ✅ Ready — needs `ANTHROPIC_API_KEY` |
| `score.py` | ICP scoring | ✅ Ready (no API needed) |
| `apollo.py` | Contact enrichment | ✅ Ready — needs `APOLLO_API_KEY` |
| `outreach.py` | Message generation | ✅ Ready — needs `ANTHROPIC_API_KEY` |
| `follow_up.py` | Follow-up cadence | ✅ Ready |
| `qualify.py` | Inbound qualifier | ✅ Ready — needs `ANTHROPIC_API_KEY` |
| `crm_audit.py` | Data quality gate | ✅ Ready (no API needed) |
| `sequence_builder.py` | HubSpot sequence templates | ✅ Ready — needs `ANTHROPIC_API_KEY` |
| `precall.py` | Pre-call brief | ✅ Ready — needs `ANTHROPIC_API_KEY` |
| `hubspot.py` | CRM sync + deals | ✅ Ready — needs `HUBSPOT_ACCESS_TOKEN` |
| `export.py` | CSV export | ✅ Ready (no API needed) |
| `birddog.py` | Signal monitoring | ✅ Ready — needs `BIRDDOG_API_KEY` |
| `report.py` | Weekly report | ✅ Ready |
| `signal_audit.py` | Client engagement | ✅ Ready |
| `transcript.py` | Voice memo processing | ✅ Ready — needs `ANTHROPIC_API_KEY` |
| `local_api_harness.py` | API connection tests | ✅ Ready — needs `HUBSPOT_ACCESS_TOKEN` |

### Playbooks (8)
- enrichment.md, signal-audit.md, outreach-ops.md, hubspot-setup.md, qualification.md, retainer-ops.md, market-map.md, inbox-warmup.md

### Account matrix system (projects/deploygtm-own/)
| Script | Purpose | Status |
|--------|---------|--------|
| `init_matrix.py` | Scaffold new client stub | ✅ Ready |
| `generate_outreach.py` | Single-account variant gen (prompt cached) | ✅ Ready — needs `ANTHROPIC_API_KEY` |
| `batch_outreach.py` | Batch run across tier filter; auto-skips blocked | ✅ Ready — needs `ANTHROPIC_API_KEY` |
| `verify_signals.py` | Audit matrix for VERIFY/FILL_IN blockers | ✅ Ready (no API needed) |
| `variant_tracker.py` | SQLite angle performance tracker | ✅ Ready (no API needed) |
| `weekly_signal_report.py` | Markdown weekly report with priority scores | ✅ Ready — optional `BIRDDOG_API_KEY` |

### Client matrices
| Client | Accounts | Status |
|--------|---------|--------|
| peregrine-space | 14 | 14/14 ready — all signals verified |
| deploygtm | 12 | 0/12 ready — VERIFY fields need Crunchbase/LinkedIn update |

### UI
- `ui/app.py` — Streamlit dashboard with sample data fallback

### Tests (34 total)
- `tests/test_local_api_harness.py` — 5 tests for API harness
- `tests/test_account_matrix.py` — 29 tests: seed data conformance, generate_outreach, variant_tracker, weekly_signal_report, init_matrix, verify_signals, batch_outreach

---

## Activation checklist

**Step 1: Confirm API keys** (~15 min)
- [ ] `cp .env.example .env` and fill in `ANTHROPIC_API_KEY`
- [ ] Add `HUBSPOT_ACCESS_TOKEN` (create private app in HubSpot)
- [ ] Add `APOLLO_API_KEY`
- [ ] Run: `python scripts/local_api_harness.py validate-env`
- [ ] Run: `python scripts/local_api_harness.py hubspot-read`

**Step 2: Configure HubSpot** (~30 min)
- [ ] `make setup-hubspot` — creates custom properties (run once)
- [ ] Create 3 sequences in HubSpot (see `master/playbooks/hubspot-setup.md`)
- [ ] Add sequence IDs to `config.yaml`
- [ ] `make generate-sequences` — generates step content to paste in

**Step 3: First batch** (~1 hour)
- [ ] `make signals` — pull Apollo hiring + funding signals
- [ ] Review `data/signals_intake.csv` — remove obvious misfits
- [ ] `make batch` — run pipeline on all signals
- [ ] `make ui` — review accounts, outreach, scores in dashboard
- [ ] `make audit` — data quality check
- [ ] `make push-hubspot` — push priority accounts (≥8)

**Step 4: Send first outreach**
- [ ] Review outreach copy in UI (Outreach tab)
- [ ] Enroll contacts in sequences or send manually
- [ ] Log first touch: `python scripts/follow_up.py log ...`

**Step 5: Daily operation**
- [ ] `make daily` every morning
- [ ] `make followup-due` to see what's due
- [ ] `make report` weekly

---

## Active project status (as of April 21)

| Project | Status | Next action |
|---------|--------|-------------|
| deploygtm-own | System built, not activated | Complete activation steps above |
| peregrine-space | Send message ready | Send to Tyler — `projects/peregrine-space/follow_up_message.md` |
| mindra | 30/60/90 plan built | Present to Deniz |
| fibinaci | Response posture built | Send warm follow-up — NDA + demo request |
| sybill | Prep questions built | Show up to next conversation |
| rex | Prep notes built | Run discovery call |
| terzo | Scheduling note drafted | Send to Brodie |

---

## What still needs to happen in Drive / GPT

*Update this section as work from other sessions is captured here.*

Items referenced but not yet in GitHub:
- [ ] Files created in Drive during GPT sessions — pull relevant content into `projects/` or `brain/`
- [ ] "One second" / Deepline API context — what is this tool and how does it fit the stack?
- [ ] Any client intake notes or transcripts from voice memos

---

## Key commands (quick reference)

```bash
make daily                    # Morning briefing
make api-test                 # Validate API connections
make signals                  # Find new accounts
make batch                    # Run pipeline on signals_intake.csv
make ui                       # Launch dashboard → http://localhost:8501
make audit                    # Data quality check before pushing
make push-hubspot              # Push to HubSpot CRM
make followup-due             # Follow-up queue
make precall DOMAIN=acme.ai   # Pre-call brief
make report                   # Weekly signal report
```
