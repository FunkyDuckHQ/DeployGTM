# DeployGTM Service Delivery Playbooks

## Purpose
This document turns the service catalog into practical delivery workflows.

The question is not only what DeployGTM sells. The question is how each offer is delivered through the architecture:

- client context intake
- ICP profile derivation
- account discovery
- BirdDog signal assessment
- scoring and prioritization
- CRM writeback
- message-market-fit testing
- human-reviewed execution
- reporting and decision-making

## Core Delivery Principle
Do not sell a vague test of the platform.

Sell a business decision artifact:

- Is this market reachable?
- Which accounts should be worked first?
- Where is there signal coverage?
- Which personas and angles are worth testing?
- What should the team do next?

The platform is how the work gets done. The client buys the answer, the operating layer, and the action queue.

## SDR Automation Coverage Lens

Use the SDR automation map as a diagnostic layer for every Signal Audit and retainer plan.

The six workstreams:

- research and targeting
- enrichment and data
- personalization and copy
- sending and deliverability
- inbound and routing
- pipeline and coaching

The Signal Audit should identify which workstreams are manual, which are already handled by tooling, which are broken or duplicated, and which should be automated first.

The retainer should operate the automatable workload while preserving human attention for live discovery, hard objections, multi-stakeholder navigation, executive trust, and recovery from misfires.

See [sdr-automation-map.md](sdr-automation-map.md).

## Architecture Components Used

### Context Engine
Used to ingest and maintain:
- client context
- product description
- ICP assumptions
- buyer personas
- past wins/losses
- open questions

### ICP Engine
Used to derive product-specific scoring dimensions from the client context.

Examples:
- DeployGTM: GTM maturity, sales infrastructure gaps, founder-led sales, messy tools
- Peregrine: mission alignment, program activity, procurement readiness, contract paths, aerospace buyer structure

### Account Discovery Layer
Used to build or expand the account universe.

Sources can include:
- client-provided account list
- CRM export
- BirdDog account recommendations
- Deepline / DiscoLike / other account discovery tools
- manual research

### BirdDog Layer
Used for:
- signal coverage assessment
- active account monitoring
- account recommendations
- signal summary
- urgency scoring

### CRM Adapter
Used for:
- company creation/update
- contact creation/update
- custom fields
- tasks
- notes
- account tiering
- signal summaries

### Message-Market-Fit Layer
Used to test:
- market
- segment
- persona
- angle
- message variants
- reply/sentiment outcomes

### Execution Layer
Used for:
- manual review queues
- assisted sends
- sequencer handoff
- LinkedIn DM tasks
- email events and reply tracking

---

# Offer 1: GTM Signal Audit

## What This Is
A diagnostic and decision artifact, not a generic platform test.

The audit answers:

> Is there enough account fit, signal coverage, and GTM clarity to justify building or operating a GTM OS for this company?

## What the Client Buys
The client is buying:

- external analysis of their market and account universe
- signal coverage assessment
- ICP scoring profile
- sample scored account set
- practical recommendation on what motion to run next
- SDR automation coverage map across the six workstreams

They are not buying a promise that the platform will magically work.

## Suggested Price
- $2.5K-$5K one-time

For more complex markets or where the client expects CRM/BirdDog setup, price at the higher end.

## Inputs Needed
Minimum:
- company website
- product description
- target customer description
- 5-10 best-fit customers or examples
- 5-10 bad-fit customers or examples, if available
- any existing target list
- CRM export if available
- current outbound messaging, if available

Optional:
- call transcripts
- founder notes
- sales decks
- closed-won/lost notes
- existing CRM fields
- BirdDog access

## Delivery Workflow

### Step 1: Intake
Create or update project context.

Architecture:
- Context Engine
- ProjectContext object

Output:
- `projects/<client>/context.md`
- initial assumptions
- open questions

### Step 2: Derive ICP Scoring Profile
Use the client's context to derive product-specific fit dimensions.

Architecture:
- ICP Engine
- `derive_icp.py`
- `icp_profile.json`

Output:
- 3-5 product-specific fit dimensions
- universal dimensions
- disqualifiers
- buyer personas
- signal categories

### Step 3: Build Sample Account Universe
Create a sample set of 25-50 accounts.

Sources:
- client list
- CRM export
- BirdDog recommendations
- account discovery tools
- manual curation

Architecture:
- Account Discovery Adapter
- Account object

Output:
- sample account matrix

### Step 4: BirdDog Fit and Signal Coverage Assessment
Assess whether BirdDog is useful for this client based on who they sell to.

Questions:
- Are target accounts usually 300+ employees?
- Are target accounts ideally 1,000+ employees?
- Are there public/commercial signals for this market?
- Does BirdDog return meaningful account recommendations?
- Are signals fresh, stale, or absent?
- Do signals explain why now, or are they weak trivia?

Architecture:
- BirdDog Adapter
- Signal Coverage Model

Output:
- expected coverage by account size
- actual coverage on sample accounts
- signal quality notes
- recommendation: BirdDog core / BirdDog supplemental / BirdDog not needed

### Step 5: Score Accounts
Score each sample account using:
- universal structural fit
- product-specific ICP fit
- signal presence
- signal freshness
- disqualifiers

Architecture:
- Score Engine
- Account object
- Signal object

Output:
- ICP fit score
- urgency score
- priority score
- tier recommendation

### Step 6: Produce Recommendation
The audit should end with a decision, not just data.

Possible outcomes:

1. Strong fit for GTM OS Pilot
2. Better fit for Message-Market-Fit Sprint first
3. Need cleaner ICP before outbound
4. Not a good fit for DeployGTM
5. BirdDog is valuable
6. BirdDog is not central yet

## Deliverables
Client-facing:

- Signal Audit Memo
- ICP Scoring Profile summary
- 25-50 scored account sample
- BirdDog signal coverage assessment
- recommended motion
- next 30-day plan

Internal:

- context.md
- icp_profile.json
- account matrix
- open loops

## What the Client Gets at the End
They should receive useful data and a decision artifact.

Minimum end package:
- scored sample accounts
- top account list
- why each top account matters
- signal coverage summary
- recommended next motion

This is what makes the audit worth paying for.

## How to Position It

> This is a diagnostic to see where your market has account-level signal, which accounts look worth working, and what motion makes sense before you spend money on outbound volume.

or:

> Before building a full GTM OS, I run a signal audit to determine whether your target market has enough data, timing, and account fit to justify an operated motion.

---

# Offer 2: Signal + Message-Market Fit Sprint

## What This Is
A structured outbound learning sprint.

It is similar to Kellen's message-market-fit offer, but powered by DeployGTM's account scoring and signal layer.

The sprint answers:

> Which market / segment / persona / angle combinations create real replies and movement?

## Suggested Price
- $5K/month
- 60-90 day minimum

## Inputs Needed
- ICP scoring profile
- target account universe
- persona hypotheses
- offer/messaging assumptions
- sending infrastructure or agreed send mode
- CRM or simple tracking layer

## Delivery Workflow

### Step 1: Define Experiment Grid
Use Kellen's core unit:

- market
- segment
- persona
- angle

Architecture:
- Campaign object
- Experiment object

Output:
- 3-5 test cells

Example:
- Market: funded NewSpace companies
- Segment: companies building navigation/timing infrastructure
- Persona: mission/program leader
- Angle: reduce payload risk before flight heritage exists

### Step 2: Build Target List
For each test cell:
- define account criteria
- find accounts
- find contacts
- score fit
- exclude disqualified accounts

Architecture:
- Account Discovery Adapter
- Enrichment Adapter
- Score Engine

Output:
- target list by cell

### Step 3: Check Signals
For each account:
- signal present?
- signal age?
- signal relevance?
- urgency score?

Architecture:
- BirdDog Adapter
- Signal object

Output:
- priority order inside each cell

### Step 4: Write Message Variants
For each cell:
- 1-2 primary messages
- 2-4 step sequence
- simple CTA
- human-readable proof point
- uncertainty language where needed

Architecture:
- PromptAsset
- OutreachDraft
- Message Variant object

Output:
- sequence copy
- variant matrix

### Step 5: Human Review
Review:
- account list
- segment logic
- copy quality
- claims
- risk
- send mode

Architecture:
- ApprovalItem

Output:
- approved campaign cells

### Step 6: Send or Assist Send
Execution mode depends on tier:

- S-tier: manual review / manual send
- A-tier: assisted send
- B-tier: sequenced send
- C-tier: generalized or no action

Architecture:
- Sequencer Adapter
- Touch object
- CampaignMembership

Output:
- sends completed or queued

### Step 7: Track Replies and Sentiment
Track:
- replies
- positive replies
- negative replies
- meetings
- objections
- sentiment
- next action

Architecture:
- Email Sync
- Response Event
- ExecutionResult

Output:
- learning loop

### Step 8: Decide Next Iteration
Do not blindly double down on what worked historically.

Assess:
- did the cell produce movement?
- did it surface objections?
- is the segment valuable?
- is the angle worth another attempt?
- should the next cell target a hidden gem?

Output:
- keep / kill / iterate decision

## Deliverables
Weekly:
- test cells launched
- replies and sentiment
- top learnings
- underperformers
- next iteration

End of sprint:
- winning / losing cells
- segment/persona/angle findings
- next campaign map
- recommendation for OS Pilot or continued testing

## How to Position It

> This sprint is not about blasting a list. It is about finding which market, segment, persona, and angle combinations create movement so we know what is worth scaling.

---

# Offer 3: GTM OS Pilot

## What This Is
The core DeployGTM build/operate offer.

The pilot creates a working version of the account intelligence and action system for one client.

The pilot answers:

> Can we turn ICP, signals, and CRM data into a weekly action queue that tells the team who to work, why now, and what to do next?

## Suggested Price
- $7.5K-$12K/month
- 90 day minimum

## Inputs Needed
- client context
- ICP profile
- target account universe or criteria
- CRM access
- BirdDog access or workflow
- enrichment source
- agreed execution mode
- stakeholder review cadence

## Delivery Workflow

### Step 1: Client Bootstrap
Command:

```text
I'm working with [client].
```

System creates:
- project folder/files
- context.md
- handoff.md
- open-loops.md
- account matrix scaffold
- ICP profile scaffold

Architecture:
- Context Engine
- Memory Adapter

### Step 2: ICP Profile Derivation
Read context and derive:
- ICP dimensions
- personas
- disqualifiers
- signal categories
- fit scoring rules

Architecture:
- ICP Engine

### Step 3: Account Universe Creation
Build initial account universe from:
- client list
- CRM
- BirdDog recommendations
- discovery tools
- manual strategic picks

Architecture:
- Account Discovery Adapter
- BirdDog Account Recommendation flow

### Step 4: Account Scoring
Compute:
- ICP fit score
- urgency score
- engagement score
- priority score
- tier

Architecture:
- Score Engine

### Step 5: BirdDog Monitoring Setup
Choose active monitored accounts.

Inputs:
- tier
- account size
- signal coverage expectations
- strategic importance

Architecture:
- BirdDog Adapter
- MonitoredAccount object

Output:
- active account list
- signal coverage status

### Step 6: CRM Writeback
Push/update:
- company record
- fit score
- urgency score
- tier
- signal summary
- next action
- owner
- tasks

Architecture:
- CRM Adapter

Output:
- CRM becomes useful, not just archival

### Step 7: Alert and Action Queue
Generate weekly or daily queue:
- new signal accounts
- high-priority S/A accounts
- stale but important accounts
- engagement-triggered contacts
- recommended next action
- messaging ideas

Architecture:
- Alert Engine
- Task object
- OutreachDraft

### Step 8: Human Review and Send
The rep/founder reviews:
- account context
- why now
- suggested message
- recommended channel

Human sends manually or approves assisted send.

Architecture:
- ApprovalItem
- Sequencer Adapter
- Touch object

### Step 9: Feedback Loop
Sync outcomes:
- sent
- reply
- positive/negative sentiment
- meeting
- no response
- disqualified

Architecture:
- Email Sync
- CRM Adapter
- Score Engine

Scores update on next run or immediately where possible.

## Deliverables
Weekly:
- action queue
- signal report
- CRM updates made
- top accounts to work
- messaging recommendations
- replies / outcomes
- open questions

Monthly:
- account movement report
- scoring calibration
- signal coverage review
- message-market-fit findings
- next month plan

## How to Position It

> This pilot builds the operating layer that tells your team who deserves attention, why now, and what to do next. It connects ICP, signals, CRM state, and messaging into one workflow.

---

# Offer 4: Operated GTM Command Layer

## What This Is
The ongoing managed version of the GTM OS.

DeployGTM is not just building the system. DeployGTM is operating the command layer.

## Suggested Price
- $12K-$20K+/month
- 6 month minimum where possible

## Delivery Workflow
Same as GTM OS Pilot, but expanded across:
- more active monitored accounts
- more workflows
- more stakeholders
- recurring tuning
- larger reporting cadence
- deeper CRM integration

## Ongoing Operating Rhythm

### Daily / Near-Daily
- check new signals
- update urgency scores
- create review queue
- surface hot accounts

### Weekly
- signal report
- action queue
- campaign/message learnings
- CRM updates
- account recommendation review

### Monthly
- ICP profile calibration
- signal weight review
- segment/persona/angle performance
- monitored account allocation review
- executive summary

## How to Position It

> This is the ongoing command layer for your account motion. We keep the account universe current, monitor timing, update CRM, and tell the team where to focus.

---

# Offer 5: Company Brain / Warehouse Layer

## What This Is
A later-stage data and query layer for more mature teams.

Do not sell this first unless the client already has repeated cross-system reporting pain.

## Trigger for This Offer
Sell this when:
- CSV/direct workflows stop scaling
- multiple systems need to be joined repeatedly
- leadership asks recurring cross-system questions
- CRM reporting is insufficient
- there is enough data volume to justify a warehouse/query layer

## Delivery Workflow

### Stage 1: One Source
Start with one source and one recurring business question.

### Stage 2: Warehouse / Query Layer
Move repeated source data into an owned store.

### Stage 3: MCP / Company Brain
Expose narrow tools for querying and action.

## Example Questions
- Which target accounts had fresh signals this week and no open task?
- Which high-fit accounts have contacts but no outreach?
- Which message-market-fit cells are producing positive replies?
- Which reps are working the highest-priority accounts?

## How to Position It

> Once the operating motion works, we can centralize the data so your team can ask questions across CRM, signal, enrichment, and engagement systems.

---

# How to Assess BirdDog Fit

## Inputs
- target account size distribution
- target industries
- sample account list
- client's ICP definition
- BirdDog account recommendation output
- signal samples

## Evaluation Questions

### Coverage
- What percent of sample accounts have any signal?
- What percent have fresh signals?
- What percent have product-relevant signals?
- Is signal absence meaningful at this account size?

### Quality
- Are signals specific enough to guide action?
- Do signals support urgency?
- Are signals just trivia?
- Can the signal be translated into a credible why now?

### Discovery Value
- Can BirdDog recommend accounts the client would not have named?
- Do recommendations match the ICP profile?
- Are recommendations explainable?

### Operational Value
- Can BirdDog active accounts be monitored economically?
- Does BirdDog scoring improve priority order?
- Can BirdDog events update CRM or task queues?

## BirdDog Recommendation Categories

### Core Layer
Use BirdDog as a central part of the system when:
- target accounts are mostly 1,000+ employees
- signal coverage is high
- signals are relevant and recent enough
- account recommendations are strong

### Supplemental Layer
Use BirdDog as one input when:
- target accounts are mostly 300-1,000 employees
- coverage is mixed
- signals help but do not define the whole motion

### Not Central Yet
Do not make BirdDog central when:
- targets are mostly under 100-300 employees
- signals are sparse or stale
- the market is better tested through message-market-fit first

---

# How to Test Message-Market Fit

## Core Unit
Use the Kellen unit:

```text
market -> segment -> persona -> angle
```

Do not test copy alone.

## Test Cell Definition
Each cell should define:
- market
- segment
- persona
- angle
- account criteria
- contact criteria
- message hypothesis
- success metric

## Sample Cell

```text
Market: NewSpace companies
Segment: funded companies building mission-critical satellite infrastructure
Persona: program / mission owner
Angle: reduce risk before flight heritage exists
Hypothesis: buyers under program pressure will engage if we frame Peregrine as a way to move faster despite heritage gaps
```

## Metrics
Prioritize:
- replies
- positive replies
- meetings
- explicit objections
- sentiment
- next-action value

Do not overfocus early on:
- opens
- clicks
- small subject-line differences

## Learning Rules
A test should teach something even when it fails.

Specific message to specific segment:
- reply = signal
- positive reply = stronger signal
- objection = learning
- silence = weak evidence against that exact hypothesis

Generic message to broad market:
- silence teaches very little

---

# How to Run the Sprint

## Sprint Timeline

### Week 0: Intake and Setup
- collect context
- derive ICP profile
- define account universe
- choose test cells
- prepare sending/review workflow

### Week 1: Launch First Cells
- launch 2-3 cells
- keep volume controlled
- inspect early replies
- verify deliverability / routing

### Week 2: Launch Remaining Cells
- launch remaining cells
- refine weak copy
- watch for objections
- start sentiment tracking

### Week 3: Analyze and Iterate
- compare cells
- identify standout segments/angles
- kill weak cells
- refine promising cells

### Week 4: Report and Decide
- produce sprint report
- recommend continue / expand / change ICP / stop

For 90-day sprint, repeat this rhythm monthly with stronger hypotheses each cycle.

## End Deliverable
The sprint should produce:
- tested market/segment/persona/angle map
- campaign performance summary
- reply/sentiment analysis
- winning or promising hypotheses
- rejected hypotheses
- account learnings
- recommendation for next motion

---

# What the Client Is Paying For

They are not paying for a test of an unproven tool.

They are paying for:

- structured market learning
- account intelligence
- signal coverage assessment
- a prioritized account queue
- tested messaging hypotheses
- CRM-ready data
- practical next actions

The platform is the operating system behind the service.

## The Core Buyer Promise

> I will help you figure out which accounts deserve attention, what signal exists, what angle is worth testing, and what your team should do next.

## The Proof Artifact
Every offer should end in an artifact the client can understand:

- Audit Memo
- Scored Account Matrix
- Signal Coverage Report
- Message-Market-Fit Report
- Weekly Action Queue
- CRM Update Summary

Do not end with vague activity.
End with decisions.
