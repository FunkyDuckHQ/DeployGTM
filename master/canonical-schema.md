# DeployGTM Canonical Schema

## Purpose

This schema is the internal data model for the GTM operating layer. External systems map into and out of these objects.

## Schema Rules

- Internal schema first, external adapters second.
- Preserve external IDs without letting them define internal shape.
- Preserve source refs, evidence, confidence, and timestamps.
- Separate fit, urgency, and engagement.
- Every workflow emits `ExecutionResult`.

## Core Objects

### ProjectContext

Fields:

- `project_id`
- `project_name`
- `project_type`
- `objective`
- `current_state`
- `key_facts`
- `decisions_made`
- `open_loops`
- `next_actions`
- `tone_constraints`
- `updated_at`
- `source_refs`

### ClientBrief

Fields:

- `client_id`
- `client_name`
- `desired_outcome`
- `engagement_window`
- `success_metrics`
- `business_model`
- `products`
- `market_context`
- `known_constraints`
- `institutional_knowledge`
- `customer_docs_refs`
- `source_refs`

### Account

Fields:

- `account_id`
- `company_name`
- `domain`
- `website`
- `industry`
- `subindustry`
- `employee_count`
- `funding_stage`
- `headquarters`
- `description`
- `icp_score`
- `urgency_score`
- `engagement_score`
- `icp_tier`
- `product_fit`
- `why_now`
- `pain_hypothesis`
- `risk_notes`
- `signal_summary`
- `recommended_route`
- `owner`
- `status`
- `tags`
- `external_refs`
- `created_at`
- `updated_at`
- `source_refs`

### Contact

Fields:

- `contact_id`
- `account_id`
- `full_name`
- `first_name`
- `last_name`
- `title`
- `seniority`
- `department`
- `persona_id`
- `linkedin_url`
- `email`
- `email_status`
- `phone`
- `contact_score`
- `confidence`
- `contact_source`
- `profile_summary`
- `likely_pains`
- `likely_objections`
- `recommended_angle`
- `owner`
- `status`
- `external_refs`
- `created_at`
- `updated_at`
- `source_refs`

### SignalDefinition

Fields:

- `signal_definition_id`
- `client_id`
- `name`
- `description`
- `signal_category`
- `alpha_signal_type`
- `data_source`
- `detection_method`
- `fit_component`
- `urgency_component`
- `ability_to_act_indicator`
- `willingness_to_act_indicator`
- `expected_frequency`
- `expected_conversion_potential`
- `default_decay_days`
- `recommended_action`
- `bird_dog_setup_notes`
- `confidence`
- `source_refs`

### Signal

Fields:

- `signal_id`
- `signal_definition_id`
- `account_id`
- `contact_id`
- `signal_type`
- `source_system`
- `source_url`
- `source_text`
- `summary`
- `importance`
- `confidence`
- `observed_at`
- `expires_at`
- `decay_model`
- `decay_half_life_days`
- `current_signal_strength`
- `product_relevance`
- `why_it_matters`
- `ability_to_act_evidence`
- `willingness_to_act_evidence`
- `next_action_hint`
- `created_at`
- `source_refs`

### ICPDefinition

Fields:

- `icp_definition_id`
- `client_id`
- `name`
- `segment`
- `firmographic_rules`
- `technographic_rules`
- `behavioral_rules`
- `exclusion_rules`
- `must_have_conditions`
- `nice_to_have_conditions`
- `negative_indicators`
- `scoring_weights`
- `created_at`
- `updated_at`
- `source_refs`

### ScoreSnapshot

Fields:

- `score_snapshot_id`
- `object_type`
- `object_id`
- `score_type`
- `score`
- `tier`
- `component_scores`
- `weights`
- `evidence`
- `confidence`
- `decay_applied`
- `decay_notes`
- `recommended_route`
- `human_override`
- `override_reason`
- `calculated_at`
- `expires_at`
- `source_refs`

### Persona

Fields:

- `persona_id`
- `name`
- `role_family`
- `seniority`
- `goals`
- `pains`
- `objections`
- `buying_triggers`
- `preferred_language`
- `avoid_language`
- `source_refs`

### Playbook

Fields:

- `playbook_id`
- `client_id`
- `name`
- `motion`
- `target_segments`
- `primary_offer`
- `qualification_rules`
- `message_angles`
- `proof_points`
- `cta_options`
- `disqualification_rules`
- `source_refs`

### ValueProp

Fields:

- `value_prop_id`
- `client_id`
- `name`
- `target_personas`
- `pain`
- `promise`
- `mechanism`
- `proof`
- `differentiators`
- `risk_reversal`
- `source_refs`

### MessageMatrix

Fields:

- `message_matrix_id`
- `client_id`
- `playbook_id`
- `persona_id`
- `segment`
- `signal_definition_ids`
- `angles`
- `objections`
- `proof_points`
- `claims_allowed`
- `claims_blocked`
- `cta_options`
- `channel_variants`
- `test_plan`
- `source_refs`

### OutreachDraft

Fields:

- `draft_id`
- `account_id`
- `contact_id`
- `playbook_id`
- `persona_id`
- `message_matrix_id`
- `channel`
- `subject`
- `body`
- `call_script`
- `personalization_basis`
- `signal_basis`
- `tone_profile`
- `claims_used`
- `compliance_notes`
- `approval_status`
- `created_at`
- `updated_at`
- `source_refs`

### CampaignTest

Fields:

- `campaign_test_id`
- `client_id`
- `hypothesis`
- `target_segment`
- `message_matrix_id`
- `account_ids`
- `contact_ids`
- `channels`
- `start_date`
- `end_date`
- `success_metrics`
- `status`
- `results_summary`
- `learnings`
- `next_iteration`
- `source_refs`

### AutomationCoverage

Fields:

- `automation_coverage_id`
- `client_id`
- `workstream`
- `current_state`
- `manual_tasks_found`
- `software_better_tasks`
- `required_context`
- `required_adapters`
- `candidate_tools`
- `quick_win_score`
- `risk_score`
- `human_review_required`
- `recommended_next_action`
- `source_refs`

### Task

Fields:

- `task_id`
- `related_object_type`
- `related_object_id`
- `task_type`
- `title`
- `description`
- `reason`
- `priority`
- `due_at`
- `owner`
- `status`
- `external_refs`
- `created_at`
- `updated_at`

### ExecutionResult

Fields:

- `execution_id`
- `workflow_type`
- `command_text`
- `target_system`
- `action`
- `result_status`
- `created_count`
- `updated_count`
- `skipped_count`
- `failed_count`
- `needs_review_count`
- `exception_summary`
- `raw_log_ref`
- `started_at`
- `finished_at`
- `source_refs`

## Required Enums

### `recommended_route`

- `enrich`
- `monitor`
- `automated_test`
- `manual_sales_review`
- `nurture`
- `hold`
- `exclude`

### `score_type`

- `icp`
- `urgency`
- `engagement`
- `contact`
- `campaign_fit`

### `signal_category`

- `intent`
- `growth`
- `change`
- `distress`
- `custom`
- `first_party`
- `relationship`

### `alpha_signal_type`

- `ability_to_act`
- `willingness_to_act`
- `timing`
- `pain`
- `risk`
- `budget`
- `strategic_fit`

### `automation_workstream`

- `research_and_targeting`
- `enrichment_and_data`
- `personalization_and_copy`
- `sending_and_deliverability`
- `inbound_and_routing`
- `pipeline_and_coaching`

## Source Notes

- Existing schema source: [DeployGTM - Canonical Schema](https://docs.google.com/document/d/1EWaXmVvE5D5n68xSQqqTTynFLXge5BVTDvkkhdSwi_g).
- Existing build and context specs define ProjectContext, Account, Contact, Signal, Task, Opportunity, OutreachDraft, and ExecutionResult as core objects: [Build Spec](https://docs.google.com/document/d/13tkqFzql8LsqIZQa0uQijYMlJcTcI9tTPeazTDqWEXg) and [Context Engine Spec](https://docs.google.com/document/d/1Yrg-AK8YlDnVxi9Eqk7kqZmXtbnCR4amtmqVNBRElXw).
- Clay signal materials support fields for custom signals, actionability, timing, signal categories, frequency, and conversion potential: [Intro to Signals](https://university.clay.com/lessons/intro-to-signals-in-clay-signals-abm), [Announcing custom signals](https://www.clay.com/blog/signals), and [Building Custom Signals in Clay](https://university.clay.com/lessons/building-custom-signals-in-clay).
- SDR automation coverage source: [sdr-automation-map.md](sdr-automation-map.md).
