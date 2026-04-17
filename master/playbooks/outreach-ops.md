# DeployGTM — Outreach Operations Playbook

*How to run the full outreach loop from signal to close, using the DeployGTM pipeline stack.*

---

## The Loop

```
Signal fires → Research + Score → Enrich → Generate outreach → Send
    → Day 3: Follow-up #1 → Day 7: Follow-up #2 → Day 14: Follow-up #3
    → Reply: Generate response → Book call → Qualify → Close or pause
```

No step is optional. Skipping any break in the loop means deals fall through.

---

## Step 1: Signal to pipeline output

**Command:** `python scripts/pipeline.py run` or `make batch`

**Input:** Company + domain + signal type + signal date  
**Output:** `output/<domain>.json` with research, score, contacts, outreach

**Quality gates:**
- Priority score ≥ 8 before activating (ICP Fit × Signal Strength)
- If `icp_verdict` is "disqualified" → skip, don't send
- If `confidence` is "low" → review manually before sending
- Every outreach contact must have a verified or likely email

**What good output looks like:**
```
ICP Fit:         4/5
Signal Strength: 3/3
Priority:        12/15  →  Activate immediately
ICP verdict:     qualified — B2B SaaS, Series A, 18 employees, technical buyers
Pain hypothesis: Founder is still closing every deal while trying to hire first AEs
Confidence:      high
```

---

## Step 2: Review before sending

**Never send without reading the outreach draft.** The system generates it — you own it.

Check:
- [ ] Correct signal referenced (not a generic "I saw your company")
- [ ] Pain hypothesis matches what you actually know about them
- [ ] Under 100 words for the primary message
- [ ] No AI language, no filler phrases
- [ ] Subject line is specific, not clickbait
- [ ] Contact name and title are correct

If any of these fail → regenerate or edit manually before sending.

---

## Step 2.5: Audit before sending

Run before any push to catch data quality problems:
```bash
make audit
```
Fix any errors before proceeding. Warnings can be accepted with context.

```bash
make audit-summary     # high-level view across all accounts
```

---

## Step 3: Send via HubSpot or manual

**Option A (HubSpot sequence enrollment — preferred):**
```bash
python scripts/hubspot.py enroll --file output/<domain>.json --dry-run
python scripts/hubspot.py enroll --file output/<domain>.json
```
Requires: `HUBSPOT_ACCESS_TOKEN` in `.env` + sequence IDs in `config.yaml`

**Option B (manual send):**
- Copy subject + body from `output/<domain>.json`
- Send from your email client or Apollo sequences
- Log it immediately after:
```bash
python scripts/follow_up.py log --file output/<domain>.json --email <email> --touch 0
```

---

## Step 4: Follow-up cadence

Run every morning to see what's due:
```bash
make followup-due
```

**Touch 1 (day 3):** Add one new piece of value. Reference original.
```bash
make followup-generate FILE=output/<domain>.json EMAIL=<email> TOUCH=1
```
Review the generated message → send → log:
```bash
python scripts/follow_up.py log --file output/<domain>.json --email <email> --touch 1
```

**Touch 2 (day 7):** One or two sentences. "Still relevant?"
**Touch 3 (day 14):** Breakup. "Happy to park this."

After touch 3 with no reply → set status to paused:
```bash
python scripts/follow_up.py log --file output/<domain>.json --email <email> --touch 3 --status paused
```

---

## Step 5: Reply comes in

Someone replies. Log it and generate a response immediately while the context is fresh:
```bash
make followup-respond FILE=output/<domain>.json EMAIL=<email> REPLY="they asked about pricing and timing"
```

The `--save` flag (included in `make followup-respond`) will:
- Set status to "replied" in the follow_up_log
- Log the reply summary with timestamp
- Save the suggested response to reply_log in the output file

**Review the suggested response before sending.** Then send and log the booking:
```bash
python scripts/follow_up.py log --file output/<domain>.json --email <email> --touch 0 --status booked --notes "Call booked for 2026-04-22"
```

---

## Step 6: Pre-call qualification

Before any discovery call, run the qualifier with the reply context:
```bash
python scripts/qualify.py requalify --file output/<domain>.json --context "replied asking about pricing, CEO at 15-person team"
```

This surfaces: recommended service (Signal Audit vs Retainer), questions to ask, red flags to watch.

---

## Step 7: Call → close or nurture

**If it's a qualified close:**
- Recommend Signal Audit ($3,500) if they need a diagnostic
- Recommend Retainer ($7,500/month) if they know the problem and need the system
- Get a signed SOW or credit card before starting any work

**If they need more time:**
- Set a specific follow-up date in HubSpot
- Tag with "nurture" status
- Let BirdDog surface the next signal before re-engaging

**If they're not a fit:**
- Disqualify cleanly. Be direct.
- `python scripts/follow_up.py log --file output/<domain>.json --email <email> --touch 0 --status closed --notes "disqualified — B2C, not ICP fit"`

---

## Tracking across all accounts

**Daily check (2 minutes):**
```bash
make followup-due      # what follow-ups are due today
make report            # weekly signal report (if running a batch)
```

**Weekly check:**
```bash
make report            # accounts by priority, outreach status, HubSpot pipeline
make birddog-pull      # new signals from monitored accounts
```

---

## Outreach metrics to watch

Track these per batch of 50 accounts:

| Metric | Target | Warning |
|--------|--------|---------|
| Reply rate (touch 1) | ≥ 15% | < 8% |
| Reply rate (full sequence) | ≥ 25% | < 15% |
| Call booked rate | ≥ 10% | < 5% |
| IQ-qualified rate | ≥ 50% of calls | < 30% |
| Close rate (qualified calls) | ≥ 30% | < 15% |

If reply rate is low: the signal or message angle is wrong — try a different signal type or persona.  
If call-booked rate is low: the follow-up cadence or response quality is the problem.  
If close rate is low: the wrong ICP is getting to the call stage — tighten qualification earlier.

---

## Red lines

- Never send to a contact without a verified or likely email
- Never send if ICP verdict is "disqualified"
- Never send if the outreach draft contains AI language or filler
- Never skip logging sends — follow-up cadence breaks without accurate sent dates
- Never skip the pre-call qualifier for inbound conversations

---

## Files referenced

| File | Purpose |
|------|---------|
| `scripts/pipeline.py` | Run full pipeline for one account |
| `scripts/batch.py` | Run pipeline on a CSV of accounts |
| `scripts/follow_up.py` | Track and generate follow-up cadence |
| `scripts/qualify.py` | Quick ICP qualification for inbound |
| `scripts/hubspot.py` | Push to CRM, enroll in sequences |
| `scripts/report.py` | Weekly signal report |
| `output/<domain>.json` | All pipeline data for one account |
| `brain/messaging.md` | Outreach rules and persona openers |
