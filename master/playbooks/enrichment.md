# Enrichment Workflow Playbook

## The Pipeline: Signal → Research → Enrich → Score → Activate

### Step 1: Signal Detection
**Source:** BirdDog (continuous) + manual research (periodic)
**Signals to capture:**
- Funding announcement (Seed/A in last 90 days)
- Sales hiring post (SDR/BDR/AE/VP Sales)
- Leadership change (new CRO, VP Sales, Head of Growth)
- Product launch or expansion announcement
- Founder posting about GTM challenges on LinkedIn/Twitter
- Agency/consultant churn (mentions of switching or disappointment)
- Tech stack changes (adopted Clay, Apollo, HubSpot recently)

**Output:** Company name, domain, signal type, signal date, signal source, signal summary

### Step 2: Account Research (Claude)
**For each signaled account, research:**
- What does the company do? (one sentence)
- Who are the founders? Background?
- How big are they? (employees, funding amount, stage)
- What do they sell and to whom?
- What's their likely GTM pain given their stage and signal?
- Are they ICP? (yes/no/maybe with reason)

**Prompt pattern:**
"Research [company]. They're a [signal context]. I want to know: what they do, founder names, team size, funding, who they sell to, their likely GTM pain, and whether they match our ICP (B2B SaaS, Seed-A, 5-30 employees, selling to technical or enterprise buyers, need pipeline infrastructure). Draft a pain hypothesis and a 3-sentence outreach email."

**Output:** Enriched account record with all fields populated

### Step 3: Contact Enrichment (Clay or Apollo)
**For each ICP-qualified account, find:**
- Founder/CEO — name, email, LinkedIn
- VP Sales / Head of Sales / First AE (if they exist) — name, email, LinkedIn
- Head of Growth / RevOps (if they exist) — name, email, LinkedIn

**Waterfall logic:**
1. Apollo (free tier first)
2. Clay enrichment (if Apollo misses)
3. LinkedIn manual lookup (last resort)

**Output:** Contact records with name, title, verified email, LinkedIn URL, associated company

### Step 4: Scoring
**ICP Fit Score (1-5):**
- 5 = Perfect fit (B2B SaaS, Seed-A, 5-30 employees, technical buyer, active signal, founder-led sales)
- 4 = Strong fit (meets most criteria, one minor gap)
- 3 = Possible fit (meets some criteria, needs more research)
- 2 = Weak fit (misses key criteria)
- 1 = Not ICP (disqualify)

**Signal Strength (1-3):**
- 3 = Active signal in last 30 days (just raised, just posted sales role)
- 2 = Recent signal in last 90 days
- 1 = No active signal but matches ICP

**Priority = ICP Fit × Signal Strength**
- 12+ = Reach out immediately
- 8-11 = Reach out this week
- 5-7 = Add to nurture / monitor
- Below 5 = Don't pursue

### Step 5: Messaging (Octave + Claude)
**Generate outreach for each priority contact:**
- Lead with the specific signal ("Congrats on the raise" / "Saw you're hiring your first SDR")
- Bridge to the pain hypothesis ("Most founders at your stage are drowning in manual prospecting while trying to close deals")
- Offer the next step ("I do a 2-week Signal Audit — basically a diagnostic on your pipeline infrastructure. $3,500, you walk away with a working system. Worth a conversation?")
- Keep it under 100 words
- No AI language. Write like a human who gives a shit.

### Step 6: Activate
- Push contacts to HubSpot with all enrichment data
- Enroll in appropriate sequence
- Set follow-up tasks
- Log signal source and pain hypothesis in HubSpot contact properties

### Step 7: Feedback Loop
- Track: sent, opened, replied, meeting booked, audit sold
- Weekly review: which signals converted best? Which messaging angles got replies?
- Update ICP definition and signal criteria based on real data
- Promote learnings to master playbook when patterns repeat across 3+ accounts
