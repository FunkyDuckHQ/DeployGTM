[README.md](https://github.com/user-attachments/files/26416216/README.md)
# DeployGTM — GTM Engineering Practice

## What this is
This repo is the operating system for DeployGTM. It contains the master playbooks, client project templates, and tooling configuration for running GTM engineering engagements.

## Repo Structure

```
deploygtm/
├── CLAUDE.md                    ← Master context (Claude Code reads this every session)
├── master/
│   ├── field-manual.md          ← GTME operating principles and architecture
│   ├── playbooks/
│   │   ├── signal-audit.md      ← How to run a Signal Audit engagement
│   │   └── enrichment.md        ← How to run the enrichment pipeline
│   ├── templates/
│   │   ├── outreach/            ← Message templates by persona
│   │   └── deliverables/        ← Client-facing report templates
│   └── learnings.md             ← Promoted insights (proven patterns only)
├── projects/
│   ├── deploygtm-own/           ← Our own outbound (client zero)
│   │   ├── context.md           ← Project-specific ICP, targets, goals
│   │   ├── prospects.csv        ← Raw prospect list
│   │   └── enriched.csv         ← Enriched + scored prospects
│   └── client-template/         ← Clone this for each new client
├── scripts/                     ← Automation scripts
├── .env.template                ← Copy to .env, fill in API keys
└── .gitignore                   ← Keeps secrets and sensitive data out of git
```

## Build Order (Week 1)

### Day 1: Foundation ✅
- [x] Define ICP, personas, positioning
- [x] Create CLAUDE.md
- [x] Set up repo structure
- [x] Write Signal Audit playbook
- [x] Write Enrichment playbook

### Day 2-3: Prospect List
- [ ] Research 50 target accounts (YC W26 B2B SaaS + recent Seed/A raises)
- [ ] Enrich each account with Claude
- [ ] Score for ICP fit and signal strength
- [ ] Draft personalized outreach for priority accounts

### Day 3-4: HubSpot Setup
- [ ] Create HubSpot free account (or configure existing)
- [ ] Set up custom properties (Signal Source, Pain Hypothesis, ICP Score, Signal Strength)
- [ ] Create deal pipeline stages
- [ ] Import enriched prospects
- [ ] Build one workflow (signal source → task creation)

### Day 4-5: BirdDog + Octave
- [ ] Set up BirdDog monitoring on top 30 target accounts
- [ ] Configure Octave brain with DeployGTM context
- [ ] Test messaging generation through Octave

### Day 5-6: Connect the Loop
- [ ] BirdDog signal → Claude research → Octave messaging → HubSpot → outreach
- [ ] Run the full workflow end-to-end on 5 test accounts
- [ ] Document the workflow with screenshots

### Day 7: Launch
- [ ] Send first outreach batch
- [ ] Document the system as case study
- [ ] Architecture diagram for client-facing use

## Rules
- Never hard-code API keys
- Never write to production CRM without confirmation
- Learnings promote to master only when patterns repeat across 3+ projects
- Every workflow must answer: what signal triggers it, what action it takes, what it writes back, how we know it worked
