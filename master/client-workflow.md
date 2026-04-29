# DeployGTM Client Workflow

## Purpose

This is the end-to-end workflow for using DeployGTM with your own prospecting and with clients across different niches, including space, software, hardware, deep tech, and services.

## Intake Command

Example:

```text
Working with Peregrine Space Co, with a desired outcome of 10 qualified meetings per month over a 3 month span. Client understands the first 2-4 weeks will be spent testing ICP assumptions and signal hypotheses, with the final 2 months focused on optimizing the engine.
```

The system should convert that into:

- client-facing engagement language
- prep research plan
- build plan
- scoring plan
- signal plan
- account plan
- enrichment plan
- messaging plan
- testing plan
- reporting plan

## Meeting Prep Workflow

Before the client call:

1. Pull Drive working brief and raw docs.
2. Pull canonical GitHub context.
3. Pull prior transcripts and open loops.
4. Pull Octave context if API access exists.
5. Research the company, category, competitors, and likely buying moments.
6. Identify 3 to 5 alpha signal hypotheses.
7. Identify what the client likely knows that is not in public data.
8. Prepare questions that extract institutional knowledge.
9. Generate a demo-quality preview artifact.

## Client Call Questions

Use the call to extract the moat:

- Which customers bought fastest and why?
- Which accounts looked good but wasted time?
- What happens inside a customer right before they need you?
- Who feels the pain first?
- Who owns the budget?
- What makes buyers hesitate?
- What internal event creates urgency?
- What public or digital trace might reveal that event?
- Which claims are safe to make?
- Which claims need proof or review?

## Build-With-Customer Workflow

After docs are in Drive, schedule working time to build:

- ICP definition
- persona map
- value props
- objection handling
- playbooks
- Octave messaging library if the client uses Octave
- BirdDog signal definitions
- message matrix
- first campaign test

The client should participate in the institutional knowledge layer, not the mechanical tooling layer.

## Target Account Workflow

1. Generate initial account universe.
2. Pull BirdDog recommended companies based on selected signals.
3. Add accounts already named by client.
4. Deduplicate by domain.
5. Score for ICP.
6. Score for urgency.
7. Apply decay to existing signals.
8. Route accounts based on score.
9. Enrich accounts above threshold.
10. Create exception list for high-urgency or ambiguous accounts.

## Contact and Messaging Workflow

For enriched accounts:

1. Identify likely buying committee.
2. Find contacts by persona and role hints.
3. Verify email and source confidence.
4. Build shareable contact profile.
5. Generate message matrix.
6. Generate first-touch copy.
7. Mark copy for automated test or manual review.

## Message Matrix Requirements

Every message matrix should include:

- target segment
- persona
- signal basis
- pain hypothesis
- opening angle
- proof point
- objection handled
- CTA
- claims used
- claims blocked
- channel
- test hypothesis
- approval status

## Account Expansion Logic

Additional leads should be added only when one of these is true:

- account score is above enrichment threshold
- new urgency signal appears
- engagement suggests buying committee expansion
- a manual seller requests more contacts
- an account enters a named-account campaign
- a contact changes role or refers another stakeholder

Do not add contacts just because a data vendor can find them.

## Success Tracking

Track:

- accounts reviewed
- accounts enriched
- accounts monitored
- ICP score distribution
- urgency score distribution
- contacts found
- contacts verified
- messages generated
- messages approved
- campaign tests launched
- replies
- meetings booked
- qualified meetings
- opportunities created
- learnings added to playbooks

V1 can live in Markdown and Sheets. Later, a Lovable, Codex-built, or Claude-built UI can sit on top of the canonical data.

## Source Notes

- Peregrine-specific context comes from the Drive working brief: [Peregrine Space - Working Brief](https://docs.google.com/document/d/1zz47YzPlD7Mz_BQOutgwNDWkgujtRgE609xICAag2Ws).
- DeployGTM source architecture comes from the Drive specs: [Build Spec](https://docs.google.com/document/d/13tkqFzql8LsqIZQa0uQijYMlJcTcI9tTPeazTDqWEXg), [Adapter Contracts](https://docs.google.com/document/d/1qQnyu108BUv-LdXJsfM4Syp4TcH3cwBaVuiBQJHZZdA), [Canonical Schema](https://docs.google.com/document/d/1EWaXmVvE5D5n68xSQqqTTynFLXge5BVTDvkkhdSwi_g), and [Context Engine Spec](https://docs.google.com/document/d/1Yrg-AK8YlDnVxi9Eqk7kqZmXtbnCR4amtmqVNBRElXw).
- Clay sources support custom signals, signal enrichment, proactive opportunity capture, and routing signal-driven action to automation or humans: [Finding GTM alpha](https://www.clay.com/blog/gtm-alpha), [Announcing custom signals](https://www.clay.com/blog/signals), and [Intro to Signals](https://university.clay.com/lessons/intro-to-signals-in-clay-signals-abm).
- Josh Whitfield / GTM Engineer School E4 supports creativity over prompts, institutional knowledge, alpha signals, demo-quality builds, and agency positioning as AI/GTM advisor: [Apple Podcasts episode summary](https://podcasts.apple.com/us/podcast/e4-its-creativity-not-prompts-why-gtm-engineers-need/id1833013226?i=1000724738164).
