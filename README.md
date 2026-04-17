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
    ├─ score.py               ICP Fit (1–5) × Signal Strength (1–3) = Priority
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
├── requirements.txt              Python dependencies
├── .mcp.json                     MCP servers: fetch (web) + Google Drive (intake)
│
├── brain/                        Messaging + ICP intelligence (Octave replacement)
│   ├── icp.md                    Who we target and why
│   ├── personas.md               Founder-Seller, First Sales Leader, RevOps/Growth
│   ├── messaging.md              Message structure, per-persona openers, rules
│   ├── objections.md             7 common objections with positioning
│   ├── product.md                What we sell (Signal Audit + Retainer)
│   └── clients/                  Per-client brain overrides (Signal Audit engagements)
│
├── scripts/
│   ├── daily.py                  Morning briefing — follow-ups, projects, activity
│   ├── pipeline.py               Main CLI: run / push / score / setup-hubspot
│   ├── batch.py                  Batch runner: process CSV of accounts (with resume)
│   ├── signals.py                Signal detection: Apollo hiring/funding + YC batch
│   ├── research.py               Claude account research + pain hypothesis
│   ├── score.py                  ICP × Signal scoring engine
│   ├── apollo.py                 Apollo contact enrichment
│   ├── outreach.py               Claude outreach generation (persona-aware)
│   ├── follow_up.py              Follow-up cadence: due/generate/log/respond/create-tasks
│   ├── qualify.py                Inbound qualifier for replies and bookings
│   ├── crm_audit.py              Data quality scanner — run before every HubSpot push
│   ├── sequence_builder.py       Generate HubSpot sequence step templates from brain/
│   ├── hubspot.py                HubSpot CRM sync, custom properties, sequence enrollment
│   ├── export.py                 Export output/ JSON → HubSpot import CSVs
│   ├── birddog.py                BirdDog signal monitoring integration
│   ├── report.py                 Weekly signal report generator
│   ├── signal_audit.py           Signal Audit engagement workflow ($3,500 / 2 weeks)
│   └── transcript.py             Voice memo → structured project updates
│
├── data/
│   ├── batch_template.csv        Template for batch pipeline input
│   ├── signals_intake.csv        Manual signal capture (add rows here)
│   └── yc_w26_targets.csv        YC W26 target list (populate and run)
│
├── output/                       Pipeline outputs (gitignored)
│
├── master/
│   ├── field-manual.md           GTM engineering operating principles
│   ├── learnings.md              Promoted patterns (3+ projects to qualify)
│   ├── context-engine.md         How repo + Drive + AI tools divide labor
│   ├── matthew-working-conditions.md  Per-session operating preferences
│   └── playbooks/
│       ├── enrichment.md         Signal → Research → Enrich → Score → Activate
│       ├── signal-audit.md       $3,500 / 2-week engagement playbook
│       ├── outreach-ops.md       Full outreach loop: signal to close (incl. audit gate)
│       └── hubspot-setup.md      One-time HubSpot configuration guide
│
└── projects/
    ├── client-template/          Copy this for every new client
    ├── deploygtm-own/            DeployGTM's own outbound (client zero)
    ├── peregrine-space/          Space GTM proof-point
    ├── mindra/                   30/60/90 plan built
    ├── fibinaci/                 Advisory engagement decision pending
    ├── sybill/                   Job process — active
    ├── rex/                      Intro call — discovery
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

Priority = ICP Fit (1–5) × Signal Strength (1–3)

| Priority | Action |
|----------|--------|
| ≥ 12 | Reach out immediately |
| 8–11 | Reach out this week |
| 5–7 | Nurture / monitor |
| < 5 | Skip |

Thresholds configurable in `config.yaml`.

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
