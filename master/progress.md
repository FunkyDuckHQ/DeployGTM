# DeployGTM — Build Log & Progress

*Single source of truth for what's been built, what's activated, and what's next.*
*Updated: 2026-04-23*

---

## Status: BUILT / PRE-ACTIVATION

The system is fully constructed. Zero accounts have run through it. Activation is blocked only by API key configuration.

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

### April 23 — Platform vNext foundation + hardening (Codex/GPT)
- `projects/deploygtm-own/artifacts/client-account-matrix/client_account_matrix.schema.json` — client-agnostic account matrix schema
- `projects/deploygtm-own/artifacts/client-account-matrix/peregrine_accounts.json` — 14-account seed dataset for Peregrine
- `projects/deploygtm-own/platform/schema/canonical.schema.json` — canonical platform payload contract
- `projects/deploygtm-own/platform/schema/icp_strategy.schema.json` — ICP strategy output schema
- `scripts/platform/adapters/base.py` — CRM adapter contract
- `scripts/platform/adapters/types.py` — typed records (`CompanyRecord`, `ContactRecord`, `CRMContext`, `SyncResult`)
- `scripts/platform/adapters/hubspot_adapter.py` — HubSpot-first adapter implementation
- `scripts/platform/crm_sync.py` — provider-agnostic company/contact sync primitive
- `scripts/platform/context_pack.py` — phase-2 context pack assembly from project context + transcripts + brain priors
- `scripts/platform/bootstrap_client.py` — client workspace bootstrap helper
- `scripts/platform/icp_strategy.py` — context-grounded ICP strategy generation
- `scripts/platform/cli.py` — unified CLI for bootstrap/context-pack/strategy
- `scripts/transcript.py` — now persists transcript summaries to `projects/<client>/transcripts/` by default when project is known
- `Makefile` — new targets: `context-pack`, `platform-bootstrap`, `platform-strategy`
- New tests:
  - `tests/platform/test_platform_contracts.py`
  - `tests/platform/test_context_pack.py`
  - `tests/platform/test_bootstrap_and_strategy.py`
  - `tests/platform/test_transcript_summary_persistence.py`

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

### Playbooks (6)
- enrichment.md, signal-audit.md, outreach-ops.md, hubspot-setup.md, qualification.md, retainer-ops.md

### UI
- `ui/app.py` — Streamlit dashboard with sample data fallback

### Tests
- `tests/test_local_api_harness.py` — unit tests for API harness

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
