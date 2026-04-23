# DeployGTM — Segment-Aware Messaging

Our ICP (B2B SaaS, Seed–Series A) is the filter. Segments are the terrain. Within the ICP, buyers do not all feel the same pain, and they do not respond to the same opener. This file is the segment-by-segment guide for calibrating the outreach generator, voice in calls, and objection framing.

When the outreach generator runs against our own accounts, the `segment` field on each account in the matrix pulls from the segments below.

---

## Segment A — Just Raised, No Pipeline Infrastructure

**Trigger:** Seed or Series A announcement in the last 90 days. Usually accompanied by a hiring post for SDR/BDR/AE within 30 days of the raise.

**Who feels it:** The founder, usually CEO/CTO. Hiring partner is about to light $120K/year on fire without the infrastructure to make them productive.

**Frame in their head:** "We have to show the board pipeline progress in 90 days. I don't have time to build the tech stack, and I don't want to hire a RevOps person before we hit $2M ARR."

**Angle:** You are about to hire a rep into nothing. The first 60 days of any AE's tenure is wasted unless the CRM, signal detection, and sequences are already running. We build that before they start.

**Opener pattern:** "Saw the Series A — congrats. When does the first AE start?" (works because it is specific, not salesy, and anchors on the real constraint)

**Objection pattern we hear:** "We'll figure it out internally." Counter: "You will — and it'll cost you three months. Here's what two weeks looks like."

**Avoid:** Decks. Strategy language. "Let me walk you through our approach." These founders have seen 20 decks this week.

---

## Segment B — First Sales Leader Just Started

**Trigger:** New VP Sales, Head of Sales, Founding AE, or Head of Revenue posted on LinkedIn within the last 60 days at a Seed–A company.

**Who feels it:** The new leader — hired to close, but inherited nothing. Onboarding week was a CRM audit and they realized what "nothing" means.

**Frame in their head:** "Quota attainment in Q1 is make-or-break for my credibility. I need to show pipeline motion in 30 days. Building the stack takes 90."

**Angle:** You were hired to close, not to be a RevOps admin. We build the engine under you in 2 weeks so your first quarter is about selling, not about configuring HubSpot workflows.

**Opener pattern:** "Saw you joined [company] — what's the CRM situation look like?" (invites them to vent, which they will)

**Objection pattern we hear:** "I want to understand the motion myself before handing pieces to an outsider." Respect the instinct — counter with: "Fine. Let's do a 20-minute GTM audit, free. If it's useful, we talk. If not, you have a clean diagnostic document."

**Avoid:** Tool-dumping. They already know the tool names. They want the operator, not the vendor list.

---

## Segment C — Using Clay/Apollo but Not Getting Results

**Trigger:** Public LinkedIn posts from founders or growth leads complaining about cold outbound, reply rates, or tool bloat. Often mentions the tool by name.

**Who feels it:** Founder, Head of Growth, or solo RevOps. They bought the tools because the playbook said to. Now the tools are running and the pipeline isn't.

**Frame in their head:** "We did what the gurus said. The tools are set up. Why isn't it working?"

**Angle:** The tools are fine. The orchestration is missing. Nobody sold them the layer that connects signals to messages to CRM to measurement. That's what we build.

**Opener pattern:** "Your Clay setup is probably fine — the problem is usually the layer around it. What signal are you leading with?" (flatters them by not attacking their choice, redirects to the actual gap)

**Objection pattern we hear:** "Can you just run our Clay table?" Counter: "No, and that's why this works. A better table isn't what you're missing. I'll show you what is on a call."

**Avoid:** Tool comparisons. Don't bash Clay, don't bash Apollo. Those are not the problem.

---

## Segment D — Recently Churned an Agency or Fractional CRO

**Trigger:** LinkedIn post describing frustration with "our last agency," "tried a fractional," or "ran an outsourced SDR play." Often with a hiring post for an internal role 30 days later.

**Who feels it:** Founder, burned by strategy-without-execution. The fractional produced a deck. The agency produced a list. Neither produced pipeline.

**Frame in their head:** "I don't want another consultant. I want someone who builds the thing and walks me through how it works."

**Angle:** We don't advise. We build. You will finish our engagement with a working system running inside your CRM — not a strategy document in a Drive folder.

**Opener pattern:** "Saw the post about [the agency/fractional situation]. What does 'working' actually look like to you?" (invites them to define the finish line in their own words)

**Objection pattern we hear:** "How is this different from what we just had?" Counter with the Signal Audit deliverable checklist — every item is a thing in their CRM, not a slide.

**Avoid:** The word "strategy." The word "transformation." Anything that smells like a deck. They just paid for one.

---

## Segment E — Solo RevOps / Growth Person Overwhelmed

**Trigger:** RevOps or Growth person at a Seed–A company posting about tool sprawl, integration debt, or "spending 80% of my time on plumbing."

**Who feels it:** Solo ops hire, wants to do strategy work, stuck on plumbing. CEO expects both.

**Frame in their head:** "I was hired to be strategic. I'm spending all week in Zapier and HubSpot workflows. Nobody is going to promote me for fixing pipelines I didn't break."

**Angle:** We take the plumbing. You take the credit for the system working. We operate quietly inside their CRM and your CEO sees you shipping.

**Opener pattern:** "How much time this week went to workflows vs. actual strategy?" (specific, validates their pain, invites a number)

**Objection pattern we hear:** "My CEO would want this done internally." Counter: "Sure — want us to train you or bring you up as the system owner? Your call. Either way you get the credit."

**Avoid:** Treating them like the decision maker in a vacuum. They usually need ammunition to sell the engagement to the founder. Give it to them.

---

## Cross-segment rules

**On every segment:**
- Lead with the signal, never the product.
- Under 75 words for first touch (outreach generator enforces this).
- One verifiable reference. One simple question.
- No feature dumping. No "leveraging." No "exciting opportunity."
- Close with "20 minutes?" or "Worth a call?" — that is the ask.

**What changes per segment:**
- The _opening fact_ (the signal-specific reference)
- The _frame_ (how we describe the problem in their terms)
- The _ask_ stays the same — short, low-commitment, specific

**What does not change, ever:**
- We don't sell the tools. We sell the system. Tools are implementation detail.
- We don't guarantee reply rates or meeting counts. We build systems, not guarantees.
- Pre-product, B2C, or budget-under-$3,500 — disqualify, politely.

---

## How this file is used

- **Outreach generator** (`projects/deploygtm-own/scripts/generate_outreach.py`): the account's `segment` field narrows the angle the LLM is writing from.
- **Account matrix schema** (`projects/deploygtm-own/account_matrix_schema.json`): every account's `segment` field should map to one of A–E above for DeployGTM's own accounts, or to a client-specific segment in `brain/clients/<client>/segments.md`.
- **Voice & tone**: the client's `voice_notes` in the matrix stacks on top of the segment. Segment controls the argument; voice_notes controls the delivery.
- **Weekly report** (`projects/deploygtm-own/scripts/weekly_signal_report.py`): groups priority by segment to show where the motion is hot.

When adding a new segment, update both this file and the client's segment table. Segments should change rarely — signals and angles per segment iterate more often.
