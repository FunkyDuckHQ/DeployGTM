# DeployGTM Design Principles

## Operating Thesis

DeployGTM is a headless GTM command layer. The operator describes the desired business outcome; the system plans the work, pulls context, routes through adapters, writes back to systems of record, and returns an execution report.

The durable asset is not a prompt library. The durable asset is the client's institutional knowledge translated into reusable objects, scoring models, signal definitions, message strategy, and execution loops.

## Principles

### 1. Creativity and institutional knowledge are the moat

The system should not compete on generic prompt engineering. It should compete on the ability to understand a client's business, identify non-obvious buying signals, and turn that knowledge into repeatable workflows.

Operator rule:

- Ask what the client knows that competitors cannot easily buy.
- Extract the language, objections, deal patterns, constraints, and weird buying moments from founder calls, customer docs, CRM notes, and sales conversations.
- Convert that knowledge into canonical objects, not one-off prompts.

### 2. Alpha signals must be specific, weird, and actionable

Good signals are not just funding announcements, job changes, or generic intent. Those are useful context, but they are crowded. Alpha signals should be tied to a client's specific market truth.

A signal is worth monitoring when it answers:

- Does this account look like a fit?
- Is there evidence of a problem or trigger?
- Is there evidence they can act?
- Is there evidence they may act now?
- What would we do differently because this signal exists?

### 3. Messaging brain is an adapter, not the operating system

Octave, Claude, Clay, HubSpot AI, or any other messaging tool can help generate copy. None of them should become the operating system.

DeployGTM owns:

- canonical account, contact, signal, persona, playbook, value prop, and message objects
- scoring logic
- routing logic
- writeback logic
- source provenance

Messaging tools implement the `ContentAdapter` contract. They can be swapped without changing the system.

### 4. Demo-quality builds can sell before full onboarding

The system should produce a credible proof artifact before a heavy onboarding motion. For a sales conversation, that means:

- a tight ICP hypothesis
- a small target account sample
- 3 to 5 alpha signal ideas
- a scoring preview
- a sample account profile
- a sample message matrix
- a clear 30/60/90-day operating plan

This proves the advisor role before the client commits to full operational depth.

### 5. Agency positioning shifts from email sender to AI/GTM advisor

DeployGTM should not be positioned as "we send emails for you." It should be positioned as the operator of a signal-based revenue system.

The offer is:

- identify where revenue is hiding
- define the signals that reveal timing
- build the account and contact engine
- test ICP and message-market fit
- route urgent opportunities to humans
- automate the repetitive work
- report on what is learning, improving, and converting

### 6. Canonical schema first, vendor APIs second

Every external platform maps into and out of DeployGTM's canonical schema. HubSpot, BirdDog, Clay, Octave, Apollo, Drive, GitHub, and future systems are adapters.

No vendor-native object should define the core model.

### 7. Drive is raw intake; GitHub is durable context

Drive holds messy client material: transcripts, decks, notes, screenshots, uploaded docs, and rough briefs.

GitHub holds durable system artifacts: master specs, canonical schema, reusable playbooks, scoring logic, handoffs, and client-ready operating models.

### 8. Human review is for judgment, not clerical work

The system should automate low-risk work and reserve human judgment for:

- ambiguous fit
- high-urgency accounts
- risky claims
- executive outreach
- complex objections
- strategic pivots

### 9. Every workflow needs trigger, action, writeback, and success condition

No workflow is real until it defines:

- trigger: what starts it
- context: what must be pulled
- action: what the system does
- writeback: where results go
- success condition: how we know it worked
- exception path: what needs review

## Source Notes

- DeployGTM Drive specs define the headless command layer, canonical schema, adapter pattern, Drive/GitHub memory split, and execution reporting model: [Build Spec](https://docs.google.com/document/d/13tkqFzql8LsqIZQa0uQijYMlJcTcI9tTPeazTDqWEXg), [Adapter Contracts](https://docs.google.com/document/d/1qQnyu108BUv-LdXJsfM4Syp4TcH3cwBaVuiBQJHZZdA), [Canonical Schema](https://docs.google.com/document/d/1EWaXmVvE5D5n68xSQqqTTynFLXge5BVTDvkkhdSwi_g), and [Context Engine Spec](https://docs.google.com/document/d/1Yrg-AK8YlDnVxi9Eqk7kqZmXtbnCR4amtmqVNBRElXw).
- Josh Whitfield / GTM Engineer School E4 is the source for creativity over prompts, institutional knowledge, alpha signals, demo-quality builds before onboarding, and agency positioning as AI/GTM advisor: [Apple Podcasts episode summary](https://podcasts.apple.com/us/podcast/e4-its-creativity-not-prompts-why-gtm-engineers-need/id1833013226?i=1000724738164).
- Clay's GTM alpha and custom signal material supports the principle that advantage comes from unique data, custom plays, and signals competitors do not monitor: [Finding GTM alpha](https://www.clay.com/blog/gtm-alpha), [Announcing custom signals](https://www.clay.com/blog/signals), and [Building Custom Signals in Clay](https://university.clay.com/lessons/building-custom-signals-in-clay).
