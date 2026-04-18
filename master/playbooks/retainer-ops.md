# Retainer Operations Playbook

*How to run a Pipeline Engine Retainer engagement ($7,500/month). What you deliver, when, and how.*

---

## What the retainer is

A fully operated outbound pipeline system. The client doesn't manage it — they just show up to the weekly briefing and close the deals that come out of the system.

**What's included:**
- BirdDog signal monitoring on their target accounts (continuous)
- Weekly signal batch: 10–15 new accounts enriched and scored
- Outreach generation: personalized first emails + follow-up sequence
- HubSpot updates: new contacts, score updates, sequence enrollment
- Follow-up cadence management: track touches, generate follow-ups, log responses
- Inbound qualification: reply handling and meeting routing
- Weekly signal report + pipeline review call (30 min)
- Ongoing ICP refinement as signals tell us what's working

**What's NOT included:**
- Sending emails (client sends from their own inbox or sequences)
- Closing deals (that's the client)
- Managing their AE's calendar
- Content marketing / SEO

---

## Monthly rhythm

### Week 1 — Batch + activation
- Pull 15–20 new accounts from BirdDog + Apollo signals
- Run through full pipeline: research, score, enrich, outreach
- Push to HubSpot, enroll in sequences
- Send client the weekly signal report (Monday morning)
- 30-min review call: review the batch, discuss who to prioritize

### Week 2 — Follow-up cadence
- Run `make followup-due` — generate and send follow-up touches for Week 1 batch
- Monitor sequence replies and route inbound interest to client
- Qualify any inbound leads: `make qualify`
- Update deal stages for anything that moved

### Week 3 — New batch + measurement
- Pull next 15–20 accounts
- Review Week 1 reply rates — are we hitting the right signals?
- Adjust ICP/persona if needed based on response patterns
- Report to client: what moved, what didn't, what we're changing

### Week 4 — Close the month
- Full pipeline summary: accounts added, touches sent, replies, meetings
- Update `master/learnings.md` if a pattern emerged this month
- Identify next month's primary signal sources based on what worked

---

## Weekly signal report

Generated with:
```bash
make report
```

The report includes:
- New accounts added this week
- Priority breakdown (by action tier)
- Signals detected (by type)
- Follow-up activity (touches sent, replies, meetings)
- Top 3 accounts to prioritize this week

Send to the client every Monday morning. Keep it to one page.

---

## Weekly call agenda (30 minutes)

1. **5 min:** What happened last week — deals moved, replies received, anything notable
2. **10 min:** Review this week's batch — who are the top 3-5 accounts? Any context the client has that I don't?
3. **10 min:** Pipeline hygiene — anything stuck? Deal stages accurate? Sequences performing?
4. **5 min:** What to adjust — is the ICP right? Are the signals we're monitoring the right ones?

**Run it async when there's nothing urgent.** If it was a quiet week, send the report and skip the call.

---

## Signals we monitor (standard stack)

Adjust per client based on Signal Audit findings.

| Signal | Tool | Cadence |
|--------|------|---------|
| Funding events | BirdDog / Apollo | Daily |
| Sales hiring | BirdDog / Apollo | Daily |
| LinkedIn GTM posts by founder | BirdDog | Weekly |
| Tool adoption (Clay, Apollo, HubSpot) | BirdDog | Weekly |
| Fractional CRO churn | LinkedIn + manual | Weekly |
| YC batch launches | Manual (seasonal) | Per batch |

---

## Managing the brain during a retainer

The `brain/` folder reflects DeployGTM's messaging framework. If a specific client has different buyer personas or messaging, use a client brain override:

```
brain/clients/[client-slug]/
  icp.md        ← their ICP override (who they sell to, not who we sell to)
  personas.md   ← their buyer personas
  messaging.md  ← messaging rules specific to their product
```

The pipeline auto-loads client brain when present. Set `CLIENT_SLUG` env var or pass `--client` flag.

---

## When the retainer is going well

Signs that it's working:
- 2–3 qualified replies per week from outreach
- At least 1 meeting booked per month from the system (not warm intros)
- Client is running sequences and updating HubSpot consistently
- ICP definition is getting sharper over time (fewer disqualified accounts in the batch)

---

## When it's not working

If reply rates are consistently < 2%, investigate in order:
1. **Signal quality** — are we finding accounts with real buying intent, or just ICP-fit accounts?
2. **ICP definition** — is the scoring correct? Are low-priority accounts sneaking into outreach?
3. **Messaging** — run `python scripts/qualify.py` on a few accounts and see if the pain hypothesis resonates
4. **Email deliverability** — check bounce rates in HubSpot sequences
5. **Timing** — did a competitor or market event change the buying context?

Don't change everything at once. Isolate one variable per week.

---

## Renewal conversation

Start the renewal conversation at Week 3, not Week 4.

At Week 3 check-in: *"We've got one week left in the month. Here's where things stand — [results]. I think [X] is working well and [Y] is what we'd focus on in month 2. Want to keep going?"*

If they're happy and seeing pipeline activity, renewal is a formality. If they're uncertain, get specific about what would make month 2 feel worth it — then deliver that thing in the final week.

---

## Month-end handoff / offboarding

If a client churns or pauses:
1. Export current HubSpot data to CSV
2. Generate a final pipeline report with all accounts + status
3. Document what we learned about their ICP in `brain/clients/[slug]/`
4. Deliver a "system handoff" doc: what was built, how to operate it, what worked
5. Promote any confirmed patterns to `master/learnings.md`

The goal: they leave with a system that runs without us. If they re-engage, we pick up where we left off.
