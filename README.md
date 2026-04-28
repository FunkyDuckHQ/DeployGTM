# DeployGTM — Operating System

GTM engineering practice run by Matthew Stegenga. We build outbound pipeline infrastructure for early-stage B2B SaaS companies — signal detection, enrichment, messaging, CRM automation. Not advice. Not lead lists. A working revenue system.

---

## Quick start

```bash
# 1. Install dependencies
make install

# 2. Create .env from template
make env
# Fill in ANTHROPIC_API_KEY at minimum — everything else is optional

# 3. Run morning briefing (no API keys needed)
make daily

# 4. Find accounts to target
make signals

# 5. Run full pipeline on a batch
make batch

# 6. Push priority accounts to HubSpot (≥8 priority)
make push-hubspot
```

One account at a time:
```bash
python scripts/pipeline.py run \
  --company "Acme" --domain "acme.com" \
  --signal funding --signal-date 2026-03-15 \
  --signal-summary "Raised $4M Seed from a16z"
```

Platform vNext (client bootstrap + context + strategy):
```bash
make platform-bootstrap CLIENT_NAME="Acme Space" DOMAIN=acme.space CLIENT=acme-space
make platform-intake CLIENT_NAME="Acme Space" DOMAIN=acme.space CLIENT=acme-space OUTCOME="create qualified pipeline" OFFER="workflow automation platform"
make context-pack CLIENT=acme-space
make platform-strategy CLIENT=acme-space
make platform-signals CLIENT=acme-space
make platform-matrix CLIENT=acme-space
make platform-crm-plan CLIENT=acme-space
make platform-deliverable CLIENT=acme-space
```

No-write Signal Audit smoke test:
```bash
make signal-audit-dry-run
```

---

## Local API test harness

Validate your API connections before running the first batch.

```bash
cp .env.local.example .env.local
# fill in HUBSPOT_ACCESS_TOKEN (and optionally ONE_SECOND_API_URL)

python scripts/local_api_harness.py validate-env
python scripts/local_api_harness.py crm-read
python scripts/local_api_harness.py one-second-read
```

Write tests are gated by `LOCAL_API_ALLOW_WRITE=1`. CRM provider is selected by `CRM_PROVIDER=hubspot|generic` in `.env.local`. HubSpot aliases (`hubspot-read`, `hubspot-upsert-company`) also work. See `master/local-api-testing-plan.md` for the full runbook.

---

## System architecture

```
Signal detected
    │
    ▼
scripts/signals.py           ← find accounts (Apollo hiring/funding, YC batch)
    │
    ▼
scripts/pipeline.py run      ← single account
scripts/batch.py run         ← list of accounts from CSV
    │
    ├─ research.py            Claude: company research + pain hypothesis
    ├─ score.py               ICP Fit + Urgency + Engagement + Confidence = Activation Priority
    ├─ apollo.py              Contact enrichment (titles, emails, LinkedIn)
    └─ outreach.py            Claude: signal-led message + follow-up variants
          │
          ▼
      output/                 JSON files, one per account
          │
          ├─ export.py        → HubSpot import CSVs
          ├─ hubspot.py push  → Direct API push (requires confirmation)
          └─ hubspot.py enroll→ Sequence enrollment by persona
                │
                ▼
          follow_up.py        Track cadence: due / generate / log / respond
          qualify.py          Inbound qualification on replies/bookings
          daily.py            Morning briefing — status across all activity
          report.py           Weekly signal report

Signal sources:
    BirdDog (continuous)      → birddog.py pull-signals → batch.py run
    Apollo hiring/funding     → signals.py all          → batch.py run
    YC batch companies        → signals.py yc-batch     → batch.py run
    Manual intake             → data/signals_intake.csv → batch.py run
    Voice memos               → transcript.py process   → project files

Client engagements:
    Signal Audit ($3,500)     → signal_audit.py new/week1/week2/deliverable
```

---

## Repository structure

```
DeployGTM/
├── CLAUDE.md                     Master context (read every session)
├── config.yaml                   Tool toggles — on/off without touching code
├── .env.example                  API key template (copy to .env, never commit .env)
├── .env.local.example            Local API test harness template (copy to .env.local)
├── requirements.txt              Python dependencies
├── .mcp.json                     MCP servers: fetch (web) + Google Drive (intake)
│
├── brain/                        Messaging + ICP intelligence (Octave replacement)
│   ├── icp.md                    Who we target and why
│   ├── personas.md               Founder-Seller, First Sales Leader, RevOps/Growth
│   ├── messaging.md              Message structure, per-persona openers, rules
│   ├── objections.md             8 objections with positioning + responses
│   ├── product.md                What we sell (Signal Audit + Retainer)
│   └── clients/                  Per-client brain overrides (Signal Audit engagements)
│
├── scripts/
│   ├── daily.py                  Morning briefing — follow-ups, projects, activity
│   ├── pipeline.py               Main CLI: run / push / score / setup-hubspot / new-client
│   ├── batch.py                  Batch runner: process CSV of accounts (with resume)
│   ├── signals.py                Signal detection: Apollo hiring/funding + YC batch
│   ├── research.py               Claude account research + pain hypothesis
│   ├── score.py                  ICP × Signal scoring engine
│   ├── apollo.py                 Apollo contact enrichment (with retry/backoff)
│   ├── outreach.py               Claude outreach generation (persona-aware + LinkedIn)
│   ├── follow_up.py              Follow-up cadence: due/generate/log/respond/create-tasks
│   ├── qualify.py                Inbound qualifier for replies and bookings
│   ├── precall.py                Pre-call brief for discovery/close calls
│   ├── crm_audit.py              Data quality scanner — run before every HubSpot push
│   ├── sequence_builder.py       Generate HubSpot sequence step templates from brain/
│   ├── hubspot.py                HubSpot CRM: contacts, companies, deals, sequences
│   ├── export.py                 Export output/ JSON → HubSpot import CSVs
│   ├── birddog.py                BirdDog signal monitoring integration
│   ├── report.py                 Weekly signal report generator
│   ├── signal_audit.py           Signal Audit engagement workflow ($3,500 / 2 weeks)
│   ├── transcript.py             Voice memo → structured project updates
│   └── local_api_harness.py      Validate API connections before first run
│
├── tests/
│   └── test_local_api_harness.py Unit tests (offline, no API keys needed)
│
├── ui/
│   ├── app.py                    Streamlit dashboard (run: make ui)
│   └── sample_data.py            Preview data when output/ is empty
│
├── data/
│   ├── batch_template.csv        Template for batch pipeline input
│   ├── signals_intake.csv        Manual signal capture (add rows here)
│   └── yc_w26_targets.csv        YC W26 target list (populate and run)
│
├── output/                       Pipeline outputs (gitignored)
│
├── logs/                         API harness run logs (JSONL format, gitignored)
│
├── master/
│   ├── progress.md               Build log + activation checklist ← START HERE
│   ├── field-manual.md           GTM engineering operating principles
│   ├── learnings.md              Promoted patterns (3+ projects to qualify)
│   ├── context-engine.md         How repo + Drive + AI tools divide labor
│   ├── design-principles.md      7 design principles for the system
│   ├── local-api-testing-plan.md API harness runbook
│   ├── matthew-working-conditions.md  Per-session operating preferences
│   └── playbooks/
│       ├── enrichment.md         Signal → Research → Enrich → Score → Activate
│       ├── signal-audit.md       $3,500 / 2-week engagement playbook
│       ├── outreach-ops.md       Full outreach loop: signal to close
│       ├── hubspot-setup.md      One-time HubSpot configuration guide
│       ├── qualification.md      Discovery call structure + close language
│       └── retainer-ops.md       Monthly rhythm for Pipeline Engine retainer
│
└── projects/
    ├── client-template/          Copy this for every new client
    ├── deploygtm-own/            DeployGTM's own outbound (client zero)
    ├── peregrine-space/          Send message ready for Tyler
    ├── mindra/                   30/60/90 plan built for Deniz
    ├── fibinaci/                 Advisory response posture built
    ├── sybill/                   Prep questions built
    ├── rex/                      Discovery prep notes built
    └── terzo/                    Scheduling note drafted
```

---

## Daily workflow

```bash
make daily               # Morning briefing — where everything stands
make followup-due        # Full follow-up queue with generate commands
make signals             # Find new accounts via Apollo + YC
make batch               # Run pipeline on signals_intake.csv
make push-hubspot        # Push priority accounts (≥8) to HubSpot
make report              # Weekly signal report from output/
make birddog-pull        # Pull fresh signals from BirdDog
```

---

## Follow-up cadence

```bash
# See what's due
make followup-due

# Generate and review touch
make followup-generate FILE=output/acme_com.json EMAIL=ceo@acme.com TOUCH=1

# Log it as sent
python scripts/follow_up.py log --file output/acme_com.json --email ceo@acme.com --touch 1

# Someone replied — generate a response
make followup-respond FILE=output/acme_com.json EMAIL=ceo@acme.com REPLY="asked about pricing"

# Qualify an inbound lead
make qualify COMPANY="Acme" DOMAIN=acme.com
make qualify-context COMPANY="Acme" DOMAIN=acme.com CONTEXT="replied asking about pricing"
```

Cadence: Touch 1 (day 3) → Touch 2 (day 7) → Touch 3 (day 14) → pause, wait for next signal.

---

## Signal detection

```bash
make signals             # All sources → signals_intake.csv
make signals-hiring      # Companies posting sales roles via Apollo
make signals-funded      # Recently funded B2B SaaS via Apollo
make signals-yc          # YC W26 batch → yc_w26_targets.csv
```

---

## Signal Audit engagements ($3,500 / 2 weeks)

```bash
make new-client CLIENT=acme DOMAIN=acme.com     # Create project + brain stubs
make audit-week1 CLIENT=acme                    # BirdDog setup + prerequisite check
make audit-week2 CLIENT=acme                    # Batch enrichment with client brain
make audit-deliverable CLIENT=acme              # Compile final deliverable package
make audit-status CLIENT=acme                   # Show enrichment progress
```

---

## Scoring system

Legacy pipeline outputs still include `icp_fit`, `signal_strength`, and `priority` for backwards compatibility.

Signal Audit vNext keeps the scores separate:

| Score | Meaning |
|-------|---------|
| `icp_fit_score` | How well the account matches the customer-specific ICP |
| `urgency_score` | How timely the account is right now, including BirdDog/manual signal decay |
| `engagement_score` | Email/CRM engagement once tests begin; defaults to 0 during audit |
| `confidence_score` | Source quality and completeness of enrichment |
| `activation_priority` | Weighted action ordering score |

Default activation priority formula:

```text
45% ICP fit + 35% urgency + 10% engagement + 10% confidence
```

CRM writes stay behind `crm_push_plan.json` and explicit approval.

---

## Tool toggles (`config.yaml`)

| Tool | Default | When disabled |
|------|---------|---------------|
| `apollo.enabled` | `true` | Skip contact enrichment |
| `octave.enabled` | `false` | Use `brain/` folder (free local replacement) |
| `birddog.enabled` | `false` | Use `data/signals_intake.csv` manually |
| `hubspot.require_confirmation` | `true` | Always prompt before CRM write |
| `hubspot.sandbox` | `false` | Set `true` for HubSpot sandbox |

---

## MCP servers (`.mcp.json`)

- **`fetch`** — fetches web pages for account research
- **`google-drive`** — reads from Google Drive Transcript Inbox

For Google Drive, set in `.env`:
```
GDRIVE_CREDENTIALS_FILE=~/.config/gdrive-credentials.json
GDRIVE_INTAKE_FOLDER_ID=your_folder_id_here
```

---

## Hard rules

1. No API keys hardcoded — always `.env`
2. No production CRM writes without explicit confirmation
3. Every enrichment includes confidence level + source
4. Outreach leads with signal and pain — never product features
5. No AI-sounding language in any outreach
6. When in doubt about ICP fit, disqualify
7. Every workflow defines: trigger → action → write-back → success metric
8. Learnings only promote to `master/learnings.md` after 3+ projects confirm the pattern
