# SDR Automation Coverage Model

## Purpose

This file turns the SDR automation context dump into DeployGTM product direction.

The core idea:

- most outbound SDR work is mechanical, repeatable, and software-addressable
- the human seller should spend time on live discovery, hard objections, multi-stakeholder navigation, executive trust, and recovery from misfires
- DeployGTM should become the operating layer that automates or assists the mechanical work while routing the human work with better context

This is not a claim that every sales motion should be fully autonomous. It is a coverage model for deciding what DeployGTM should automate, assist, route, or leave human.

## Six Automatable Workstreams

| Workstream | Jobs To Automate | DeployGTM Owner | Candidate Tools / Adapters |
| --- | --- | --- | --- |
| Research and targeting | Lookalikes from closed-won accounts, ICP fit scoring, champion/job-change tracking, intent/topic detection | Context pack, ICP strategy, signal strategy, account matrix, signal adapter | BirdDog, Clay, Apollo, UserGems, 6sense, Bombora |
| Enrichment and data | Email/phone waterfalls, account/contact/domain dedupe, stale data refresh, account routing | Enrichment adapter, CRM adapter, account/contact schema, CRM push plan | Clay, Apollo, ZoomInfo, Cognism, Amplemarket, Clarify |
| Personalization and copy | Research-backed first lines, copy variants, subject/body scoring, tone adaptation | Content adapter, message matrix, persona strategy, source-traced copy | Claude, Octave, Lavender, Regie, Apollo AI |
| Sending and deliverability | Domain/inbox rotation, warmup pools, sequence orchestration, A/B send tests, inbox pausing | Deferred managed-sending module; V1 drafts tasks and sequence-ready copy only | Clarify Campaigns, Smartlead, Instantly, Outreach, Salesloft, lemlist, SuperSend |
| Inbound and routing | Form qualification, meeting routing, traffic de-anonymization, high-intent chat | Future inbound/routing adapter; urgency and SLA workflow input | Chili Piper, Default, RB2B, Warmly, Qualified, Clarify |
| Pipeline and coaching | Activity logging, call summaries, pre-meeting briefs, objection practice, rep coaching moments | Transcript adapter, precall workflow, daily briefing, engagement feedback loop | Gong, Granola, Avoma, Hyperbound, Clarify meetings |

## Human Boundary

Automate or assist:

- finding accounts
- cleaning and enriching records
- generating signal hypotheses
- monitoring account changes
- scoring fit, urgency, engagement, and confidence
- drafting copy and variants
- compiling pre-call/account briefs
- creating CRM tasks and write plans
- summarizing calls and replies
- updating reports

Keep human:

- live discovery
- hard objections
- multi-stakeholder navigation
- executive trust
- negotiation and commercial judgment
- recovery from misfires
- final approval on sensitive CRM writes, bulk updates, and outbound sends

DeployGTM should use automation to remove low-value effort from the rep, not to pretend human sales judgment is obsolete.

## Signal Audit Implication

Signal Audit should become an SDR automation coverage assessment as well as a signal/account deliverable.

The audit should answer:

- Which of the six workstreams are already covered?
- Which are broken, manual, duplicated, or vendor-dependent?
- Where does the client have enough context/data to automate safely?
- Where is the risk too high for automation yet?
- Which workflows should be automated first?
- Which human review gates must stay in place?
- What account, signal, copy, task, and CRM artifacts can be produced immediately?

Recommended new audit artifact:

```text
projects/<client>/platform/automation_coverage.json
```

Suggested fields:

- `workstream`
- `current_state`
- `manual_tasks_found`
- `software_better_tasks`
- `required_context`
- `required_adapters`
- `quick_win_score`
- `risk_score`
- `human_review_required`
- `recommended_next_action`
- `source_traces`

## Retainer Implication

The retainer should be framed as operating the automatable SDR workload so the client's reps spend effort on the human 20%.

The retainer operates:

- research and account discovery
- enrichment and data hygiene
- signal monitoring
- scoring and routing
- copy drafting and test design
- CRM task/writeback planning
- engagement and signal feedback loops
- weekly reporting and learning capture

The rep owns:

- live conversations
- judgment-heavy follow-up
- relationship building
- executive navigation
- closing motions

## Guarantee Posture

The context dump included a strong offer idea:

```text
90-day profitable pipeline guarantee; if the agreed sales-qualified meeting target is missed, work continues for free until the target is hit.
```

Do not publish or operationalize this as the default promise until it has guardrails.

Required guardrails before using guarantee language:

- define sales-qualified meeting criteria in writing
- define the target, time window, and measurement source
- require client approval SLAs for copy, account lists, CRM access, and tool access
- exclude tool spend, ad spend, data spend, and inbox/domain setup from free-work obligations
- require deliverability prerequisites before any sending responsibility
- define what counts as client-caused delay
- cap the free-work period or scope
- distinguish meeting target from revenue, close rate, or reply-rate guarantees
- reserve disqualification rights if ICP, TAM, or offer evidence is weak
- include a postmortem mechanism before guarantee extension activates

Safer default positioning:

```text
We guarantee the operating system and proof loop: real accounts, real scores, real signals, real profiles, real copy, real CRM tasks, and a measurable path to qualified meetings. Performance guarantees only apply after the motion and client obligations are defined.
```

## Build Priorities

1. Add `automation_coverage.json` to the Signal Audit deliverable.
2. Score each of the six workstreams during intake and deliverable generation.
3. Keep managed sending deferred until deliverability controls exist.
4. Add inbound/routing and pipeline/coaching as later adapter categories.
5. Make Clarify the preferred workspace for rep-facing tasks, lists, campaigns, meetings, and feedback where access is confirmed.
6. Keep HubSpot compatibility, but do not design the product around HubSpot-specific workflows.

## Source Notes

- Source context: user-provided SDR automation map and image, May 4, 2026.
- This file is a product interpretation of that context, not a wholesale copy of the public image.
