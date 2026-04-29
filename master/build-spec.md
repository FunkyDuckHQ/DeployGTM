# DeployGTM Build Spec

## What We Are Building

DeployGTM is a GTM operating layer that turns a natural-language business objective into a planned, cited, scored, and executed revenue workflow.

The operator should be able to write:

> Working with Peregrine Space Co. Desired outcome: 10 qualified meetings per month over 3 months. First 2 to 4 weeks are for ICP and signal testing. Final 2 months are for optimization and scaling.

The system should turn that into:

- client-facing engagement language
- prep research checklist
- ICP hypotheses
- alpha signal hypotheses
- scoring model
- target account list
- BirdDog monitoring recommendations
- enrichment plan
- contact profiles
- message matrix
- campaign testing plan
- manual escalation path
- reporting loop

## Client-Facing Offer Language

Use this as the default polished version of the engagement promise:

> We will build Peregrine a signal-based GTM engine designed to create 10 qualified meetings per month over a 3-month engagement. The first 2 to 4 weeks are intentionally treated as a learning sprint: we will pressure-test ICP assumptions, identify the accounts most likely to buy before traditional flight heritage exists, define the alpha signals that reveal timing and budget, and validate which messaging earns real engagement. The final 2 months are focused on optimization: scaling the account engine, tightening signal scoring, enriching the right buyers, routing urgent opportunities to the team, and improving message-market fit until the system is producing repeatable qualified conversations instead of one-off outbound activity.

Shorter version:

> We are not selling a list or an email campaign. We are building the revenue intelligence loop that shows Peregrine which accounts are worth pursuing now, why they are likely to care, who to engage, what to say, and when a human should step in.

## 3-Month Engagement Shape

### Phase 1: Discovery and Demo-Quality Build

Goal: prove the operating logic before heavy onboarding.

Duration: week 0 to week 1.

Outputs:

- client working brief
- current state summary
- initial ICP hypotheses
- first-pass value proposition map
- 3 to 5 alpha signal concepts
- sample account profile
- sample message matrix
- "what we would monitor" BirdDog recommendation list

### Phase 2: ICP and Signal Testing

Goal: learn which accounts, signals, and messages create real response.

Duration: weeks 1 to 4.

Outputs:

- ICP scoring matrix
- urgency scoring matrix
- target account source list
- BirdDog signal setup recommendations
- scored account list
- enrichment threshold
- first contact profiles
- controlled message-market fit tests
- exception report for accounts needing manual review

### Phase 3: Engine Optimization

Goal: improve conversion, scoring accuracy, and routing.

Duration: months 2 and 3.

Outputs:

- refreshed ICP and urgency scores
- signal decay updates
- engagement feedback loop
- message matrix iteration
- account expansion logic
- urgent-opportunity routing
- weekly operating report
- monthly learning report

## Core Workflow

1. Receive natural-language objective.
2. Pull client context from Drive, GitHub, Octave if available, CRM, transcripts, and uploaded materials.
3. Build or update `ClientBrief`, `ICPDefinition`, `Persona`, `Playbook`, `ValueProp`, and `SignalDefinition`.
4. Generate alpha signal hypotheses tied to ability and willingness to act.
5. Recommend BirdDog monitoring setup.
6. Build target account list from client context, research, and BirdDog-recommended companies.
7. Score accounts for ICP fit and urgency.
8. Enrich accounts above threshold.
9. Find and score contacts.
10. Build contact profiles and message matrices.
11. Decide route:
    - automated campaign test
    - manual sales alert
    - nurture or monitor
    - discard or hold
12. Capture engagement and signal updates.
13. Re-score accounts and contacts.
14. Report learnings and next actions.

## Context Pull Order

1. Canonical GitHub files.
2. Client working brief in Drive.
3. Raw client docs in Drive.
4. Transcript inbox and meeting notes.
5. Octave library if API access exists.
6. CRM records.
7. BirdDog monitored signals and recommended companies.
8. Enrichment providers.
9. Public web research when needed.

## Scoring Overview

Every account should receive at least two scores:

- `icp_score`: how closely the account matches the target customer profile
- `urgency_score`: whether something suggests action should happen now

Scores should include:

- source provenance
- evidence
- confidence
- decay
- last recalculated timestamp
- recommended route

Suggested route thresholds:

- `80+`: enrich and prepare outreach
- `65-79`: monitor, enrich selectively, or use for test cohorts
- `40-64`: hold unless urgency score is high
- `<40`: exclude unless a human overrides

Urgency can override ICP only with strong evidence. A mediocre-fit account with a major urgent trigger should route to human review, not fully automated outreach.

## Campaign Testing Crossroads

After profiles and copy exist, the system must choose between automated testing and manual routing.

Automated testing is appropriate when:

- ICP score is high
- urgency is moderate
- claims are low risk
- message variation is controlled
- contacts are verified

Manual routing is required when:

- urgency score is high
- account is strategic
- signal is sensitive or unusual
- executive buyer is involved
- product claims need founder judgment
- there is a procurement or risk objection

## Reporting Loop

The system should track success across three layers:

- market learning: ICP, signals, objections, buyer roles, account patterns
- execution learning: contact quality, deliverability, reply rate, meeting conversion, route accuracy
- business learning: meetings booked, qualified opportunities, pipeline created, client decisions

UI can come later. V1 reporting can be Markdown, Sheets, or a lightweight dashboard. The important part is that every report is generated from canonical execution and scoring objects rather than manual narrative.

## Source Notes

- Existing DeployGTM Build Spec defines the natural-language command layer, batch/event workflows, adapter layer, memory layer, validation layer, and V1 stack direction: [Build Spec](https://docs.google.com/document/d/13tkqFzql8LsqIZQa0uQijYMlJcTcI9tTPeazTDqWEXg).
- Existing Context Engine Spec defines Drive as raw intake and GitHub as canonical durable context: [Context Engine Spec](https://docs.google.com/document/d/1Yrg-AK8YlDnVxi9Eqk7kqZmXtbnCR4amtmqVNBRElXw).
- Peregrine working brief supplies the specific ICP problem, flight heritage objection, NewSpace wedge, Xona signal, and tone constraints: [Peregrine Space - Working Brief](https://docs.google.com/document/d/1zz47YzPlD7Mz_BQOutgwNDWkgujtRgE609xICAag2Ws).
- Clay supports signal-based GTM as proactive opportunity capture and emphasizes that signals must be acted on after enrichment: [Intro to Signals](https://university.clay.com/lessons/intro-to-signals-in-clay-signals-abm) and [Announcing custom signals](https://www.clay.com/blog/signals).
- Josh Whitfield / GTM Engineer School E4 supports the demo-quality build before onboarding and agency shift from sender to advisor: [Apple Podcasts episode summary](https://podcasts.apple.com/us/podcast/e4-its-creativity-not-prompts-why-gtm-engineers-need/id1833013226?i=1000724738164).
