# DeployGTM — Operating System

GTM engineering practice run by Matthew Stegenga. We build outbound pipeline infrastructure for early-stage B2B SaaS companies — signal detection, enrichment, messaging, CRM automation. Not advice. Not lead lists. A working revenue system.

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Fill in ANTHROPIC_API_KEY at minimum

# 3. Create HubSpot custom properties (run once per account)
python scripts/pipeline.py setup-hubspot

# 4. Run one account through the full pipeline
python scripts/pipeline.py run \
  --company "Acme" --domain "acme.com" \
  --signal funding --signal-date 2026-03-15 \
  --signal-summary "Raised $4M Seed from a16z"

# 5. Review output, then push to HubSpot
python scripts/pipeline.py push --file output/acme_com_2026-03-15.json
```

---

## System architecture

```
Signal detected
    │
    ▼
scripts/pipeline.py run          ← single account
scripts/batch.py run             ← list of accounts from CSV
    │
    ├─ research.py               Claude: company research + pain hypothesis
    ├─ score.py                  ICP Fit (1–5) × Signal Strength (1–3) = Priority
    ├─ apollo.py                 Contact enrichment (titles, emails, LinkedIn)
    └─ outreach.py               Claude: signal-led message + 2 follow-ups
          │
          ▼
      output/                    JSON files, one per account
          │
          ├─ export.py           → HubSpot import CSVs (companies + contacts)
          └─ hubspot.py push     → Direct API push (requires confirmation)

Signal sources:
    BirdDog (continuous)         → birddog.py pull-signals → batch.py run
    Manual intake                → data/signals_intake.csv → batch.py run
    Google Drive transcripts     → transcript.py process   → project files
```

---

## Repository structure

```
DeployGTM/
├── CLAUDE.md                    Master context (read every session)
├── config.yaml                  Tool toggles — on/off without touching code
├── .env.example                 API key template (copy to .env, never commit .env)
├── requirements.txt             Python dependencies
├── .mcp.json                    MCP servers: fetch (web research) + Google Drive (intake)
│
├── brain/                       Octave replacement — free, local, editable
│   ├── icp.md                   Who we target and why
│   ├── personas.md              Founder-Seller, First Sales Leader, RevOps/Growth
│   ├── messaging.md             Message structure, per-persona openers, rules
│   ├── objections.md            7 common objections with positioning
│   └── product.md               What we sell (Signal Audit + Retainer)
│
├── scripts/
│   ├── pipeline.py              Main CLI: run / push / score / setup-hubspot
│   ├── batch.py                 Batch runner: process CSV of accounts
│   ├── export.py                Export output/ JSON → HubSpot import CSVs
│   ├── research.py              Claude account research + pain hypothesis
│   ├── score.py                 ICP × Signal scoring engine
│   ├── apollo.py                Apollo contact enrichment
│   ├── outreach.py              Claude outreach generation (persona-aware)
│   ├── hubspot.py               HubSpot CRM sync + custom property setup
│   ├── birddog.py               BirdDog signal monitoring integration
│   └── transcript.py            Voice memo → structured project updates
│
├── data/
│   ├── batch_template.csv       Template for batch pipeline input
│   ├── signals_intake.csv       Manual signal capture (add rows here)
│   └── yc_w26_targets.csv       YC W26 target list (populate and run)
│
├── output/                      Pipeline outputs (gitignored — may contain prospect data)
│
├── master/
│   ├── field-manual.md          GTM engineering operating principles
│   ├── learnings.md             Promoted patterns (3+ projects to qualify)
│   ├── context-engine.md        How the repo + Drive + AI tools divide labor
│   ├── matthew-working-conditions.md  Per-session operating preferences
│   └── playbooks/
│       ├── enrichment.md        Signal → Research → Enrich → Score → Activate
│       └── signal-audit.md      $3,500 / 2-week engagement playbook
│
└── projects/
    ├── client-template/         Copy this for every new client
    ├── deploygtm-own/           DeployGTM's own outbound (client zero)
    ├── peregrine-space/
    ├── mindra/
    ├── fibinaci/
    ├── sybill/
    ├── rex/
    └── terzo/
```

---

## Core workflow

### Single account
```bash
python scripts/pipeline.py run \
  --company "Name" \
  --domain "domain.com" \
  --signal [funding|hiring|gtm_struggle|agency_churn|tool_adoption|manual] \
  --signal-date YYYY-MM-DD \
  --signal-summary "What you saw"
```
Saves enriched JSON to `output/`. Push separately after reviewing.

### Batch (50+ accounts)
```bash
# 1. Populate data/yc_w26_targets.csv
# 2. Run
python scripts/batch.py run --input data/yc_w26_targets.csv

# 3. Resume if interrupted
python scripts/batch.py run --input data/yc_w26_targets.csv --resume

# 4. Export to HubSpot import CSVs
python scripts/export.py run --min-priority 8

# 5. Or push directly via API
python scripts/export.py run --push-to-hubspot
```

### BirdDog → Pipeline (when enabled)
```bash
python scripts/birddog.py pull-signals --run-pipeline
```

### Voice memo → Project update
```bash
python scripts/transcript.py process --file ~/Desktop/memo.txt --update-project
# or pipe it
cat ~/Desktop/memo.txt | python scripts/transcript.py process --stdin --project mindra
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
