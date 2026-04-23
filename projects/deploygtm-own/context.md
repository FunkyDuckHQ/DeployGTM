# DeployGTM Own Outbound — Project Context

## Status: Week 1 — System built, ready to run

## Objective
Build the full pipeline engine for DeployGTM's own outbound. This serves three purposes:
1. Generate revenue (Signal Audit clients) within 30 days
2. Prove the system works with real data and real results
3. Create the case study that sells the service to future clients

## Target for this project
- 50 enriched prospect accounts
- Personalized outreach for each
- All prospects in HubSpot with proper fields and lifecycle stages
- BirdDog monitoring active on top 30 accounts
- Octave brain configured with DeployGTM context
- First outreach sent by end of Week 1

## ICP for this project
B2B SaaS companies, Seed to Series A, US-based, 5-30 employees, selling to technical or enterprise buyers, recently raised funding OR recently posted sales hiring roles.

**Priority targets:**
- YC W26 batch (Demo Day was March 24, 2026 — these founders just raised and need GTM infrastructure NOW)
- Recent Seed/A raises tracked through Crunchbase, Fundraise Insider, Growth List
- Companies in GTM Cafe and GTME communities where founders are actively discussing pipeline challenges

## Signals we're monitoring
- Raised Seed or Series A in last 90 days
- Posted job for SDR/BDR/AE
- Founder posting about pipeline struggles on LinkedIn
- Using Clay/Apollo but complaining about results
- Recently churned an agency or fractional CRO

## Messaging angle
Lead with: "You just raised. You need pipeline. You probably don't have the infrastructure to support it yet. I build the system — signals, enrichment, CRM, outreach — so your team can focus on closing."

## Success metrics
- Outreach sent to 50 prospects
- 10%+ reply rate
- 5+ discovery conversations booked
- 2+ Signal Audits sold within 30 days
- Full system documented as case study

## System status (as of 2026-04-17)

**Built and ready:**
- Pipeline scripts: research, score, Apollo enrichment, outreach generation, HubSpot sync
- Batch runner: process 50 accounts from CSV in one command
- Signal detection: Apollo hiring + funding search (scripts/signals.py)
- Export: HubSpot import CSVs from output/ files
- Sequence enrollment: auto-enroll contacts into HubSpot sequences by persona
- Brain: ICP, personas, messaging, objections, product docs fully populated
- BirdDog: integration built, activate when API key is set
- Report: weekly signal report generator

**Immediate next actions:**
1. Run `python scripts/signals.py all --output data/signals_intake.csv` to find first 50 accounts
2. For YC W26: manually pull from ycombinator.com/companies?batch=W26, add to data/yc_w26_targets.csv
3. Run `python scripts/batch.py run --input data/signals_intake.csv`
4. Review output/, push priority accounts to HubSpot
5. Set HUBSPOT_ACCESS_TOKEN in .env and run `make setup-hubspot`
6. Configure HubSpot sequences, add IDs to config.yaml
7. Run `make push-hubspot` for all priority accounts (≥8 priority score)
8. Send outreach

**Time to first outreach from a standing start:** ~2 hours with API keys set.

## Tracking
| Date | Action | Result | Learning |
|------|--------|--------|----------|
| 2026-04-17 | Built full pipeline system | All scripts live on GitHub | System is complete — bottleneck is now API keys + account list |
| 2026-04-23 | Shipped 4-artifact account matrix system | Schema + 14 Peregrine seed accounts, outreach generator, SQLite variant tracker, weekly report — all client-agnostic | The matrix is the single source of truth per client; every script reads from it. Adding a new client = drop a JSON file in `data/`. |

## Account Matrix System (client-agnostic, lives in this project)

All four artifacts are parameterized by `--client <slug>`. To onboard a new client, drop a `data/<slug>_accounts.json` file that conforms to `account_matrix_schema.json`, then every command below works unchanged.

**The workflow:**

```bash
# 1. Generate 3 outreach variants for one account, auto-log variant #2 as sent
make outreach-variants CLIENT=peregrine-space COMPANY="Xona Space Systems" LOG=2

# 2. When a response comes in, record it (use ID from `make variant-list`)
make variant-respond ID=3 SENTIMENT=positive

# 3. Weekly: see which angles actually work
make variant-report CLIENT=peregrine-space

# 4. Weekly: full signal + priority report (writes markdown to outputs/<client>/)
make weekly-report CLIENT=peregrine-space
```

**File map:**
- `account_matrix_schema.json` — JSON Schema for the matrix (reusable across every client).
- `data/<client>_accounts.json` — per-client account list with voice_notes, why_now_signal, angle per account.
- `data/variants.db` — SQLite tracker (git-ignored — local state).
- `outputs/<client>/` — generated variants and weekly reports (git-ignored).
- `scripts/generate_outreach.py` — Artifact 2.
- `scripts/variant_tracker.py` — Artifact 3.
- `scripts/weekly_signal_report.py` — Artifact 4.
