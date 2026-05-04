# Qualification Playbook

*How to run a discovery call, qualify live, and move to next step or gracefully disqualify.*

---

## Before the call

Run the pre-call brief:
```bash
make precall DOMAIN=acme.ai CONTACT="Evan Park"
```

Have the output in front of you. Know the signal, the pain hypothesis, and your 5 questions.

---

## The 5 qualification criteria

A deal is qualified when you have YES on all five:

| Criterion | What to listen for | Disqualify if |
|-----------|-------------------|---------------|
| **Pain is real** | They describe a specific operational problem, not a theoretical one | "We're doing fine, just exploring options" |
| **They have budget authority** | Founder or VP-level, can approve $3,500 without committee | "I'll have to run it by [CEO, board, finance]" |
| **Timing is now** | Immediate trigger — AE starting, pipeline down, just raised | "Maybe in Q3" without a concrete reason |
| **ICP fit** | B2B SaaS, Seed–A, 5–30 people, selling to technical/enterprise buyers | Consumer, pre-product, or enterprise-only motion |
| **They want infrastructure** | Open to HubSpot + BirdDog as part of the system | "We just need more leads" / "we don't want new tools" |

---

## Call structure (30 minutes)

### 0–3 min: Set the agenda
> "Thanks for making time. I want to understand what's actually going on with your pipeline — the real situation, not the polished version. Then I'll tell you whether what I do is relevant. Fair?"

This signals you're not there to pitch. It opens them up.

### 3–15 min: Discovery
Don't rush. Ask one question, listen fully, ask a follow-up.

**Starting question (pick one based on signal):**
- Funding signal: *"You just raised — what does the GTM pressure look like from here? Where's the gap?"*
- Hiring signal: *"You're building out sales. What does your pipeline infrastructure look like today — what do they inherit when they start?"*
- GTM struggle signal: *"You mentioned [the post/thing you saw]. What's the actual situation?"*
- Agency churn signal: *"What did the [fractional CRO / agency] get right, and where did they leave you hanging?"*
- Inbound: *"What made you reach out? What's the problem you're trying to solve?"*

**Follow-up probes:**
- "How much time are you personally spending on this right now?"
- "What have you already tried?"
- "What does good look like in 90 days?"
- "Is this a 'nice to have' or is it costing you real pipeline right now?"
- "Who else would be involved in a decision like this?"

### 15–22 min: Position (only if discovery reveals a fit)
Do NOT pitch until you've heard the pain. Then:

> "Here's what I'm hearing: [restate their pain in their language]. That's exactly the problem I solve. I build the infrastructure layer — [specific things they said they're missing]. Two weeks, $3,500 for the Signal Audit, and you walk away with [the thing they said they wanted]."

Keep it tight. Reference what they told you, not what your pitch deck says.

### 22–28 min: Handle objections
See `brain/objections.md` for the 7 common objections with responses.

Key principle: **don't over-justify**. One clear response and move on. Over-explaining signals insecurity.

### 28–30 min: Close (or disqualify gracefully)

**If qualified — hard close:**
> "Based on what you've told me, this is a fit. The Signal Audit is two weeks, $3,500, and I can start [next Monday / next week]. Want to get that on the calendar?"

Don't offer a "let me think about it" escape hatch. Ask for the next concrete step.

**If needs more information:**
> "I want to make sure this is the right move before we commit either direction. Can we do [specific next step — send contract, review scope doc, quick follow-up call]?"

**If disqualified:**
> "Honestly, based on what you've told me, I don't think I'm the right fit right now. [Specific reason.] When [the timing trigger / the situation] changes, reach back out — I'm usually booked 2–4 weeks out so don't wait too long."

Disqualifying cleanly builds more credibility than a weak close.

---

## Signals to listen for

**Hot signals (qualified immediately):**
- Describes a specific pain point without prompting
- Has tried something and it failed
- Founder is personally spending hours/week on the thing I solve
- "Our AE starts [specific date]" / "We need this before [specific event]"
- Already has a modern CRM/workspace or is willing to adopt one

**Warm signals (qualified with clarification):**
- "We've been thinking about this" — ask what they've tried and why it didn't work
- "Our pipeline is inconsistent" — ask what they've done to address it
- "We're hiring for this" — ask what they need to set up before the hire

**Red flags (soft disqualifiers — probe before deciding):**
- "We just want more leads" — ask if they mean a system for finding leads, or just a list
- "We don't want to add tools" — ask what they're currently using; may be fine
- "We have someone internal working on it" — ask what's blocked; may still need a system build

**Hard disqualifiers:**
- Pre-product (nothing to sell)
- Consumer / B2C
- Expecting guaranteed reply rates or meeting counts before ICP, offer, client obligations, and deliverability prerequisites are defined
- Budget under $3,500 (don't negotiate down)
- Wants to hire in-house and just needs a job description (not our problem)

---

## After the call

**If they verbally committed:**
1. Send contract within 2 hours — don't let the momentum cool
2. Create a deal in HubSpot: `make deal COMPANY="Name" STAGE=meeting_booked AMOUNT=3500`
3. Advance it to `proposal_sent` when contract goes out: `make advance-deal COMPANY="Name" STAGE=proposal_sent`
4. Create client project: `make new-client CLIENT=name DOMAIN=domain.com`

**If they need to think:**
1. Log the follow-up: `python scripts/follow_up.py log --file output/name.json --email email@co.com --touch 0`
2. Set a specific follow-up date — "When should I check back in?" Get a concrete answer
3. Note the specific objection so the follow-up addresses it

**If disqualified:**
1. Update follow-up status: `python scripts/follow_up.py log ... --status paused`
2. Note in output JSON why — useful if their situation changes

---

## Pricing anchor

Signal Audit: **$3,500 / 2 weeks.** This is non-negotiable.

Pipeline Engine Retainer: **$7,500/month.** Usually discussed after Signal Audit is done.

Don't offer discounts. Don't suggest payment plans unless they ask. The price is part of the signal — it filters for founders who have budget and are serious.

If they push back on price:
> "The price reflects the time it takes to do this right. It's two weeks of focused work, not a template. If the budget isn't there right now, the Signal Audit might not be the right timing — but it's the lowest-risk way to see what the system looks like before committing to the retainer."

---

## Update the deal after the call

| Outcome | Stage | Command |
|---------|-------|---------|
| Sent contract | proposal_sent | `make advance-deal COMPANY="X" STAGE=proposal_sent` |
| Signed | closed_won | `make advance-deal COMPANY="X" STAGE=closed_won AMOUNT=3500` |
| Not now | closed_lost | `make advance-deal COMPANY="X" STAGE=closed_lost` |
| Needs follow-up | meeting_booked | stays in place |
