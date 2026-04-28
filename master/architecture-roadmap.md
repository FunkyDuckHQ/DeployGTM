# DeployGTM — Architecture Roadmap

*Last updated: 2026-04-27*

---

## What's Built (Current State)

### Core Infrastructure
| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/engage.py` | Research-first engagement intake | ✅ Built |
| `scripts/sync_client_context.py` | Google Drive → context.md sync | ✅ Built |
| `scripts/signals_to_matrix.py` | Signals CSV → account matrix bridge | ✅ Built |
| `scripts/derive_icp.py` | context.md → per-client ICP scoring profile (Claude-derived) | ✅ Built |
| `scripts/crm_adapter.py` | CRM-agnostic routing layer | ✅ Built |
| `scripts/hubspot.py` | HubSpot v3 adapter (full) | ✅ Built |
| `scripts/pipeline.py` | Single-account enrichment pipeline | ✅ Built |
| `scripts/batch.py` | Batch pipeline runner | ✅ Built |
| `scripts/signals.py` | Signal detection via Apollo | ✅ Built |
| `scripts/birddog.py` | BirdDog signal pull | ✅ Built |
| `scripts/qualify.py` | ICP qualification check | ✅ Built |
| `scripts/follow_up.py` | Cadence manager + HubSpot tasks with copy | ✅ Built |
| `scripts/export.py` | HubSpot import CSV export | ✅ Built |
| `scripts/report.py` | Weekly signal report | ✅ Built |
| `scripts/daily.py` | Morning briefing | ✅ Built |
| `scripts/research.py` | Claude + web enrichment | ✅ Built |
| `scripts/score.py` | Static ICP × signal priority score | ✅ Built |
| `scripts/transcript.py` | Voice memo → CRM note | ✅ Built |

### Account Matrix System
| Script | Purpose | Status |
|--------|---------|--------|
| `projects/*/scripts/generate_outreach.py` | 3-variant outreach generation (prompt caching) | ✅ Built |
| `projects/*/scripts/batch_outreach.py` | Batch outreach across tier filter | ✅ Built |
| `projects/*/scripts/verify_signals.py` | Signal completeness check (gates outreach) | ✅ Built |
| `projects/*/scripts/activate_account.py` | Matrix → CRM push | ✅ Built |
| `projects/*/scripts/update_status.py` | Account status lifecycle | ✅ Built |
| `projects/*/scripts/variant_tracker.py` | SQLite variant performance tracker | ✅ Built |
| `projects/*/scripts/weekly_signal_report.py` | Signal + status + variant report | ✅ Built |
| `projects/*/scripts/score_engine.py` | Fit-first dynamic scoring (fit_score + signal_bonus decay + interaction delta) | ✅ Built |
| `projects/*/scripts/research_accounts.py` | Apollo + web + Claude company research → sets fit_score | ✅ Built |
| `projects/*/scripts/enrich_matrix.py` | Apollo contact find + Claude individual profiling | ✅ Built |
| `projects/*/scripts/init_matrix.py` | New client matrix scaffold | ✅ Built |

### CRM Adapters
| Adapter | Status |
|---------|--------|
| HubSpot | ✅ Full |
| CSV export | ✅ Full |
| None (no-op) | ✅ Full |
| Salesforce | 🔲 Stub — raises NotImplementedError |
| Attio | 🔲 Stub — raises NotImplementedError |
| Pipedrive | 🔲 Stub — raises NotImplementedError |

---

## Near-Term Nodes (Next 3–5 Builds)

### Node: ICP-Driven Signal Search
**File:** `scripts/signals.py` (update existing)
**Problem:** Current `signals.py` is hardcoded for DeployGTM's own ICP (hiring SDR/AE/BDR, recently funded B2B SaaS). When running for a client (e.g., Peregrine targeting NewSpace primes), the queries are wrong.
**What needs to change:**
- Add `--client <slug>` flag to `signals.py`
- Read client's ICP from `projects/<slug>/context.md`
- Have Claude derive the right Apollo search parameters from the ICP
- Generate a client-specific signals CSV, not a generic one
**Make target:** `make signals CLIENT=peregrine-space` (parameterized)

---

### Node: BirdDog Enrollment from Matrix
**File:** `projects/*/scripts/birddog_enroll.py` (new)
**Trigger:** After scoring, before weekly monitoring
**What it does:**
- Read tier 1 + 2 accounts from accounts.json
- Push their domains to BirdDog monitoring list via API
- Mark accounts as enrolled in the matrix (`birddog_enrolled: true`)
- Verify BirdDog confirms enrollment
**Dependency:** Need to confirm BirdDog API has an "add account to monitoring list" endpoint (check API docs).
**Make target:** `make birddog-enroll CLIENT=slug [TIER=1,2]`

---

### Node: Salesforce Adapter
**File:** `scripts/crm_adapter.py` — implement `SalesforceAdapter`
**Trigger:** When first client uses Salesforce
**What needs to happen:**
- Auth: OAuth2 client credentials flow, `SFDC_CLIENT_ID` + `SFDC_CLIENT_SECRET` + `SFDC_INSTANCE_URL` in .env
- SFDC is building headless APIs — confirm REST endpoint shape when ready
- Key objects: Account (company), Opportunity (deal), Task, Note
- `upsert_company` → SFDC Account with domain as external ID
- `create_deal` → SFDC Opportunity linked to Account
- `create_note` → SFDC Note on Account
- `create_task` → SFDC Task on Contact/Account

---

### Node: Slack Delivery Adapter
**File:** `scripts/notify_slack.py` (new)
**Trigger:** After weekly signal report generates, or when a hot signal fires
**What it does:**
- Post formatted weekly report to a client Slack channel
- Post real-time alert when BirdDog fires a new signal on a tier-1 account
- Auth: `SLACK_BOT_TOKEN` per client, stored in `.env` or per-client config
**Why this matters:** Several clients will want reports delivered to Slack rather than email or a PDF. "Weekly Slack digest" was the delivery mechanism requested for Peregrine.
**Make target:** `make slack-report CLIENT=slug CHANNEL=#channel`

---

## Future Nodes (Longer Horizon)

### Node: Attio Adapter
**File:** `scripts/crm_adapter.py` — implement `AttioAdapter`
**API:** `api.attio.com/v2`, key auth
**Priority:** Medium — Attio is gaining traction with early-stage companies. First Attio client triggers this build.

---

### Node: Meeting Auto-Brief
**What it does:**
When a meeting transcript lands in Drive (from Otter, Fireflies, Fathom, or any recorder):
1. MCP reads it automatically (no manual step)
2. Agent identifies: which client/company is this about?
3. New relationship → begins scaffolding context.md
4. Existing relationship → runs stats check (deal stage, last touch, pipeline activity)
5. Surfaces a brief immediately — key people, decisions, action items, pain signals
6. No manual trigger required
**Dependency:** Needs the recording service to write to Drive automatically, or an MCP for the recorder directly (e.g., Otter MCP, Fireflies webhook → Drive).
**Current state:** `transcript.py` exists but requires manual `--file` argument. The auto-detect step is missing.

---

### Node: Self-Improving Signal Weights
**What it does:**
After enough data accumulates in `variants.db` and account score histories:
- Analyze which signal types (funding, hiring, etc.) actually led to replies and meetings
- Adjust `SIGNAL_WEIGHT` in `score_engine.py` based on observed conversion rates
- Minimum threshold: 30+ activated accounts with reply data before adjusting
**Current state:** `score_engine.py` uses static weights. The feedback loop isn't closed yet.

---

### Node: Client-Facing Dashboard
**What it does:**
A read-only web view clients can access to see:
- Their monitored account list and scores
- Signal activity timeline
- Outreach status by account
- Pipeline progress
**Options:**
- Extend `ui/app.py` (Streamlit) to support multi-client with auth
- Or build a static weekly HTML report instead of a live dashboard
**Current state:** `ui/app.py` exists but is DeployGTM-internal only.

---

### Node: Multi-Channel Outreach
**What it does:**
Current system generates email copy only. Expand to:
- LinkedIn DM templates (character-limited, different tone)
- Cold call talking points (3-bullet framework, not a script)
- Re-engagement sequences after 90-day pause
**Dependency:** `generate_outreach.py` needs channel parameter. Brain/messaging.md needs channel-specific voice notes.

---

### Node: Pipedrive Adapter
**File:** `scripts/crm_adapter.py` — implement `PipedriveAdapter`
**API:** `api.pipedrive.com/v1`, token auth
**Priority:** Low — implement when first Pipedrive client appears.

---

## Architectural Principles (Non-Negotiable)

1. **CRM-agnostic from day one.** All CRM operations route through `crm_adapter.py`. No script outside `hubspot.py` imports HubSpot directly.

2. **ICP-agnostic scoring.** Fit dimensions, signal weights, decay rates, and personas are NOT hardcoded. They live in `projects/deploygtm-own/data/<client>_icp_profile.json`, generated by `derive_icp.py` from the client's context.md. GTM maturity matters for DeployGTM's own ICP; SBIR awards matter for Peregrine's ICP. The scoring engine doesn't care — it loads the right profile per client.

3. **Research layer is always AI-first.** `engage.py` researches before asking. Context.md is populated by the system, not by forms Matthew fills in.

4. **Drive is supplementary, not required.** Every workflow degrades gracefully when Drive isn't configured.

5. **Confidence markers on all AI inferences.** context.md always labels `[confirmed]`, `[researched]`, `[inferred]`. Never present assumptions as facts.

6. **Scores are live, not frozen.** `score_engine.py` recomputes on every weekly refresh. Scores decay with signal age (per-signal half-life) and rise with engagement events.

7. **Outreach gates on verified signals.** `verify_signals.py` blocks outreach on any account with VERIFY markers. This is not optional.

8. **No CRM writes without explicit confirmation.** `activate_account.py` requires `click.confirm()` for live pushes. Dry-run is always available.

9. **Every new client engagement starts with `make engage` then `make derive-icp`.** Research-first intake produces context.md; ICP profile derivation produces the scoring framework. Both are required before research-accounts can run meaningfully.
