# Growth Engine Integration

## Purpose

This file integrates the user-provided Growth Engine idea file into DeployGTM.

The Growth Engine pattern adds an operating sequence that DeployGTM needs: research first, brand/message alignment second, acquisition execution third, operations/reporting always on.

DeployGTM should not become only an outbound engine. It should become the command layer for building and operating a full growth system.

## What This Adds To DeployGTM

The Growth Engine file contributes four concrete ideas that were under-modeled in the first DeployGTM architecture pass:

1. ICP work must start from existing customer economics when available.
2. Brand and message-market fit should be derived from customer language, not invented positioning.
3. Acquisition is multi-channel: paid ads, outbound, CRM attribution, nurture, and SLA routing.
4. Operational scripts and skills should be scaffolded as repeatable moves, not a monolithic app.

## Architecture Shape

DeployGTM should support a markdown-first client workspace with these folders:

```text
client-growth-engine/
├── 0_research/
├── 1_brand/
├── 2_acquisition/
├── 3_operations/
├── .claude/
│   ├── skills/
│   └── settings.json
├── .env.example
└── CLAUDE.md
```

DeployGTM's canonical repo remains the system-level brain. Client workspaces become implementation environments for a specific business.

## Stage 1: ICP Research

Purpose: find the real customers, not the assumed customers.

Required operations:

- analyze customer records by profitability, not just volume
- find revenue concentration and margin sweet spots
- enrich top customers and accounts
- extract personas from sales/support/customer transcripts
- use Jobs to Be Done and Four Forces of Progress for persona extraction
- build segmented prospect lists by persona and segment

DeployGTM mapping:

- `ClientBrief`
- `ICPDefinition`
- `Persona`
- `Account`
- `Contact`
- `ResearchRun`
- `ScoreSnapshot`

Important operating principle:

If customer data exists, use it before building audiences, ICPs, or campaigns. Data before creative.

## Stage 2: Brand and Message Alignment

Purpose: align public-facing messaging with the customer reality revealed by research.

Required operations:

- diagnose brand-reality gap
- extract voice from customer language
- cluster quotes by theme
- derive voice traits
- build creative angle matrix
- codify publishable brand principles

DeployGTM mapping:

- `VoiceTrait`
- `CreativeAngle`
- `MessageMatrix`
- `ValueProp`
- `Playbook`
- `ContentFinding`

Important operating principle:

Customer language is the brand voice. Do not invent a voice before extracting actual language from calls, transcripts, and customer evidence.

## Stage 3: Acquisition Execution

Purpose: turn ICP, positioning, and messaging into measurable acquisition loops.

Required operations:

- Meta campaign specs
- LinkedIn campaign specs
- CRM attribution waterfall
- nurture flows
- 5-minute SLA alerts for high-value leads
- cold outreach sequences
- daily ad review
- weekly growth report

DeployGTM mapping:

- `CampaignSpec`
- `CampaignTest`
- `AttributionRule`
- `NurtureFlow`
- `SLAWorkflow`
- `OutreachDraft`
- `ExecutionResult`

Important operating principle:

Drafts, not sends. Ad changes, CRM edits, outbound messages, and bulk updates require human approval before production writes.

## Research Process Builder Integration

Mitchell Keller's `research-process-builder` should be treated as a method for building reliable research workflows, not as a replacement for DeployGTM.

DeployGTM should absorb the following concepts:

- define the research goal in one sentence
- define what a good result looks like
- test search patterns against sample companies
- include multiple company tiers
- score pattern quality and consistency
- use ground truth examples when available
- keep kill lists for bad searches
- add stop conditions and extraction specs
- assemble validated process files

DeployGTM mapping:

- `ResearchProcess`
- `ResearchPattern`
- `ResearchRun`
- `ResearchFinding`
- `ResearchKillPattern`

Recommended stance:

Mitchell's process builder is better than DeployGTM today at validated web research. DeployGTM is broader: it should use that method as its `ResearchAdapter` layer, then route findings into ICP scoring, signal definitions, account selection, enrichment, messaging, and acquisition operations.

## New Canonical Objects To Add

### ResearchProcess

Fields:

- `research_process_id`
- `name`
- `goal`
- `good_result_definition`
- `inputs`
- `sample_companies`
- `ground_truth_examples`
- `patterns`
- `kill_patterns`
- `accuracy_target`
- `validated_accuracy`
- `output_template`
- `source_refs`

### ResearchPattern

Fields:

- `research_pattern_id`
- `research_process_id`
- `query_template`
- `pattern_type`
- `intended_signal`
- `quality_score`
- `consistency_score`
- `freshness_score`
- `accuracy_score`
- `classification`
- `failure_modes`
- `extract_instructions`
- `stop_condition`

### ResearchRun

Fields:

- `research_run_id`
- `research_process_id`
- `target_account_id`
- `inputs_used`
- `patterns_run`
- `findings`
- `sources`
- `confidence`
- `execution_result_id`
- `created_at`

### VoiceTrait

Fields:

- `voice_trait_id`
- `client_id`
- `name`
- `meaning`
- `sounds_like`
- `does_not_sound_like`
- `customer_quotes`
- `source_refs`

### CreativeAngle

Fields:

- `creative_angle_id`
- `client_id`
- `persona_id`
- `psychological_hook`
- `segment`
- `concept`
- `proof_basis`
- `channel_fit`
- `claims_allowed`
- `claims_blocked`
- `source_refs`

### CampaignSpec

Fields:

- `campaign_spec_id`
- `client_id`
- `platform`
- `stage`
- `objective`
- `budget`
- `audiences`
- `creative_concepts`
- `graduation_criteria`
- `pause_criteria`
- `approval_status`
- `source_refs`

### AttributionRule

Fields:

- `attribution_rule_id`
- `client_id`
- `priority_order`
- `match_type`
- `source_field`
- `target_channel`
- `propagation_rules`
- `audit_notes`

### NurtureFlow

Fields:

- `nurture_flow_id`
- `client_id`
- `name`
- `trigger`
- `steps`
- `eject_conditions`
- `owner`
- `approval_status`

### SLAWorkflow

Fields:

- `sla_workflow_id`
- `client_id`
- `trigger`
- `qualification_rules`
- `business_hours_response_target_minutes`
- `after_hours_response_target_minutes`
- `alert_destination`
- `owner_rotation`
- `status`

## Starter Skills To Scaffold Later

DeployGTM should eventually scaffold these as local Claude/Codex skills or command workflows:

- `ops-icp-analysis`
- `ops-enrichment`
- `ops-persona-extraction`
- `ops-voice-extraction`
- `ops-angle-matrix`
- `ops-campaign-spec`
- `ops-ad-review`
- `ops-weekly-growth-report`
- `ops-attribution-audit`
- `ops-nurture-builder`
- `ops-cold-outreach`
- `write-copy`

## Guardrails

Required write safety:

- external API writes require explicit approval
- bulk CRM updates require preview and confirmation
- Slack/SMS writes default to read-only or draft mode
- campaign specs require budgets, graduation criteria, and pause criteria
- every copy claim needs evidence
- never delete campaigns or CRM records by default; pause/archive instead

## First Implementation Sequence

1. Add the new canonical objects to `master/canonical-schema.md`.
2. Add `ResearchAdapter`, `PaidAdsAdapter`, `AttributionAdapter`, `NurtureAdapter`, and `SLAAdapter` to `master/adapter-contracts.md`.
3. Create machine-readable templates for persona cards, voice traits, campaign specs, research processes, and message matrices.
4. Create Peregrine-specific research processes for space/deep-tech account discovery.
5. Create a scoring script or worksheet that consumes research findings and emits `ScoreSnapshot` objects.
6. Create a weekly growth report template.

## Source Notes

- User-provided Growth Engine idea file in chat, based on the Ascend/FlyFlat growth engine: ICP research, data-driven rebrand, acquisition stack, CRM attribution, nurture flows, SLA routing, and Claude Code operations.
- Mitchell Keller's `research-process-builder` provides the validation loop for reliable web research processes: [GitHub repo](https://github.com/MitchellkellerLG/research-process-builder).
- DeployGTM's existing architecture files define the adapter-first system these ideas should plug into: [build-spec.md](build-spec.md), [adapter-contracts.md](adapter-contracts.md), [canonical-schema.md](canonical-schema.md), and [client-workflow.md](client-workflow.md).
