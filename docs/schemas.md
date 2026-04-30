# DeployGTM Schema Draft

## Purpose

This document extends the canonical schema into a modular service-led product model. It is intentionally broader than the Peregrine sandbox so the system can support space, software, hardware, services, PLG, enterprise expansion, and other GTM motions.

## Schema Rules

- Internal objects first, vendor objects second.
- Every important field should preserve source, confidence, and timestamp when possible.
- Fit, urgency, engagement, and learning are separate concepts.
- Scores must explain why they changed.
- Workflows must define trigger, action, writeback, success condition, and exception path.

## Objects

### Client

- `client_id`
- `name`
- `business_model`
- `market`
- `current_gtm_motion`
- `desired_outcomes`
- `constraints`
- `tools`
- `data_sources`
- `approval_rules`
- `source_refs`

### ProductService

- `product_service_id`
- `client_id`
- `name`
- `category`
- `buyer_problem`
- `primary_value`
- `proof_points`
- `qualification_notes`
- `risk_notes`
- `source_refs`

### Account

- `account_id`
- `client_id`
- `company_name`
- `domain`
- `firmographics`
- `technographics`
- `strategic_notes`
- `icp_score`
- `urgency_score`
- `engagement_score`
- `recommended_route`
- `source_refs`

### Contact

- `contact_id`
- `account_id`
- `full_name`
- `title`
- `persona_id`
- `email`
- `linkedin_url`
- `contact_score`
- `profile_summary`
- `likely_pains`
- `likely_objections`
- `recommended_angle`
- `source_refs`

### ICPCriteria

- `icp_criteria_id`
- `client_id`
- `segment`
- `must_have_conditions`
- `nice_to_have_conditions`
- `negative_indicators`
- `scoring_weights`
- `confidence`
- `source_refs`

### SignalDefinition

- `signal_definition_id`
- `client_id`
- `name`
- `category`
- `detection_method`
- `source_system`
- `ability_to_act_indicator`
- `willingness_to_act_indicator`
- `timing_indicator`
- `default_decay_days`
- `recommended_action`
- `confidence`
- `source_refs`

### Signal

- `signal_id`
- `signal_definition_id`
- `account_id`
- `contact_id`
- `observed_at`
- `expires_at`
- `summary`
- `evidence`
- `confidence`
- `current_strength`
- `why_it_matters`
- `next_action_hint`
- `source_refs`

### Score

- `score_id`
- `object_type`
- `object_id`
- `score_type`
- `score`
- `component_scores`
- `weights`
- `confidence`
- `evidence`
- `decay_applied`
- `explanation`
- `recommended_route`
- `calculated_at`
- `source_refs`

### Play

- `play_id`
- `client_id`
- `name`
- `trigger`
- `target_segment`
- `required_context`
- `action`
- `writeback`
- `success_condition`
- `exception_path`
- `source_refs`

### Workflow

- `workflow_id`
- `client_id`
- `name`
- `phase`
- `trigger`
- `steps`
- `owner`
- `systems_touched`
- `writeback_rules`
- `success_metrics`
- `human_review_rules`
- `source_refs`

### VendorAdapter

- `adapter_id`
- `vendor`
- `adapter_type`
- `supported_methods`
- `auth_requirements`
- `read_capabilities`
- `write_capabilities`
- `field_mappings`
- `limitations`
- `source_refs`

### Experiment

- `experiment_id`
- `client_id`
- `hypothesis`
- `segment`
- `message_matrix_id`
- `channels`
- `sequence_count`
- `start_date`
- `end_date`
- `success_metrics`
- `results`
- `learnings`
- `next_iteration`
- `source_refs`

### Report

- `report_id`
- `client_id`
- `period`
- `experiments_run`
- `sequence_count`
- `reply_rates`
- `meetings`
- `score_changes`
- `workflow_changes`
- `learnings`
- `next_actions`
- `source_refs`

### Assumption

- `assumption_id`
- `client_id`
- `statement`
- `category`
- `confidence`
- `test_plan`
- `status`
- `source_refs`

### Learning

- `learning_id`
- `client_id`
- `source`
- `summary`
- `implication`
- `objects_to_update`
- `created_at`
- `source_refs`

## Source Notes

- Strategy source: user-provided DeployGTM Strategy / Product / Architecture Condensed Brief, shared April 30, 2026.
- Existing schema source: [master/canonical-schema.md](../master/canonical-schema.md).
- Supporting architecture sources: [docs/architecture.md](architecture.md), [master/build-spec.md](../master/build-spec.md), and [master/adapter-contracts.md](../master/adapter-contracts.md).
