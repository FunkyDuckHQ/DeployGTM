# DeployGTM Adapter Contracts

## Purpose

Adapters translate between DeployGTM canonical objects and external systems. The core system should think in canonical objects, not in Clarify, HubSpot, BirdDog, Clay, Octave, Apollo, Drive, or CSV shapes.

## General Rules

- Inputs are canonical objects or normalized command arguments.
- Outputs are canonical objects plus `ExecutionResult`.
- Adapters preserve external IDs in `external_refs` or `adapter_metadata`.
- Adapters are idempotent where possible.
- Adapters return structured exceptions.
- Adapters do not become the system of record.

## CRM Adapter

Purpose: create, update, fetch, and associate CRM records.

Required methods:

- `upsert_account(account)`
- `upsert_contact(contact)`
- `associate_contact_to_account(contact_id, account_id)`
- `create_task(task)`
- `update_task(task)`
- `fetch_account_by_domain(domain)`
- `fetch_contact_by_email(email)`
- `fetch_open_tasks(object_ref)`
- `write_score(account_id, score_snapshot)`
- `write_signal_summary(account_id, signal_summary)`

Required behaviors:

- detect duplicates by domain and email
- preserve CRM IDs
- map custom properties per CRM
- write back score, urgency, status, and next action fields

Preferred implementation priority:

- Clarify first for DeployGTM-operated workflows once API/MCP access and field mappings are confirmed.
- HubSpot remains the compatibility adapter for clients already on HubSpot.
- Other CRMs should follow the same contract.

### API / CLI Tool Adapter

Purpose: manage complex external APIs and CLIs through a stable DeployGTM lifecycle.

Required methods:

- `validate_env()`
- `describe_capabilities()`
- `read(args)`
- `plan_write(args)`
- `dry_run_write(plan)`
- `write_with_confirmation(plan, approval_ref)`
- `sync_events(args)`
- `write_receipt(result)`

Required behaviors:

- dry-run is the default
- live writes require explicit approval
- credentials and scopes are validated before execution
- every external ID is preserved
- every run returns a structured execution receipt
- raw vendor API shapes stay inside the adapter
- failures include retryability and human next action

## Signal Adapter

Purpose: define, create, monitor, fetch, and normalize account-level signals.

BirdDog is the first target implementation.

Required methods:

- `suggest_signal_definitions(client_brief, icp_definition, playbooks)`
- `create_signal_definition(signal_definition)`
- `monitor_account(account, signal_definitions)`
- `unmonitor_account(account_id)`
- `fetch_latest_signals(account_id)`
- `fetch_recommended_accounts(signal_definition)`
- `sync_signal_summary_to_account(account_id)`

Required behaviors:

- preserve source URLs and timestamps
- attach confidence and evidence
- support signal decay
- distinguish generic signals from alpha signals
- return empty lists cleanly

## Enrichment Adapter

Purpose: enrich accounts and find likely buyers without making a data vendor the source of truth.

Required methods:

- `enrich_account(account)`
- `find_contacts(account, role_hints, persona_hints)`
- `verify_email(email)`
- `enrich_contact(contact)`
- `build_contact_profile(contact, account, signals)`

Required behaviors:

- support waterfall providers
- separate found data from verified data
- preserve source for every field
- return confidence per field
- do not enrich below threshold unless manually requested

## Content Adapter

Purpose: generate messaging artifacts from canonical GTM context.

The messaging brain is an adapter, not the operating system.

Candidate implementations:

- `ClaudeMarkdownContentAdapter`
- `OctaveContentAdapter`
- `ClayContentAdapter`
- `HubSpotAIContentAdapter`

Required methods:

- `generate_outreach_draft(account, contact, signals, persona, playbook, value_props, constraints)`
- `generate_call_prep(account, contact, signals, persona, playbook, value_props, meeting_context)`
- `generate_message_matrix(account_segment, persona, playbook, value_props, signal_definitions)`
- `extract_content_findings(source_type, source_ref, content, known_playbooks, known_personas)`

Required behaviors:

- cite signal and claim basis
- avoid invented evidence
- preserve tone constraints
- output canonical `OutreachDraft`, `CallPrep`, `MessageMatrix`, or `ContentFinding`
- mark risky claims for review

## Memory Adapter

Purpose: read and write raw, working, canonical, and compact context.

Required methods:

- `read_project_brief(project_id)`
- `write_project_brief(project_id, content)`
- `read_handoff(project_id)`
- `write_handoff(project_id, content)`
- `append_open_loop(project_id, item)`
- `build_compact_context(project_id)`
- `read_client_docs(project_id)`
- `sync_drive_to_repo(project_id)`

Required behaviors:

- preserve Drive as raw intake
- preserve GitHub as canonical layer
- do not overwrite durable context without intent
- attach source refs to every important update

## Scoring Adapter

Purpose: calculate ICP, urgency, contact, and campaign-route scores in a consistent way.

Required methods:

- `calculate_icp_score(account, icp_definition, signals, firmographics)`
- `calculate_urgency_score(account, signals, engagement, timing_context)`
- `calculate_contact_score(contact, account, persona, buying_committee)`
- `apply_decay(score_snapshot, current_time)`
- `explain_score(score_snapshot)`
- `recommend_route(score_snapshot)`

Required behaviors:

- expose component weights
- include evidence and confidence
- apply decay by signal type
- separate fit from urgency
- allow manual override with reason

## Planner / Router

Purpose: turn natural-language requests into workflows.

Required methods:

- `classify_workflow(command)`
- `plan_steps(command, context)`
- `execute_plan(plan)`
- `summarize_execution(result)`
- `route_account(account, score_snapshot)`
- `route_contact(contact, account, score_snapshot)`

Workflow classes:

- `prep`
- `batch`
- `event_driven`
- `mixed`
- `reporting`

## Validation / Exception Adapter

Purpose: keep headless execution trustworthy.

Required methods:

- `validate_required_fields(object)`
- `detect_partial_failures(result)`
- `format_exception_report(result)`
- `flag_claim_risk(content)`
- `flag_missing_sources(object)`

Exception report fields:

- succeeded
- failed
- skipped
- needs_review
- retryable
- human_owner
- next_action

## Source Notes

- Existing adapter contract source: [DeployGTM - Adapter Contracts](https://docs.google.com/document/d/1qQnyu108BUv-LdXJsfM4Syp4TcH3cwBaVuiBQJHZZdA).
- Existing build and context specs define command routing, memory, adapters, workflow types, and execution results: [Build Spec](https://docs.google.com/document/d/13tkqFzql8LsqIZQa0uQijYMlJcTcI9tTPeazTDqWEXg) and [Context Engine Spec](https://docs.google.com/document/d/1Yrg-AK8YlDnVxi9Eqk7kqZmXtbnCR4amtmqVNBRElXw).
- The prior local content adapter artifact defines the messaging adapter shape: [content-adapter-contract.md](../docs/content-adapter-contract.md).
- Clay's custom signal docs support signal definitions, enrichment, and action routing: [Announcing custom signals](https://www.clay.com/blog/signals) and [Building Custom Signals in Clay](https://university.clay.com/lessons/building-custom-signals-in-clay).
- Clarify control-plane source: [clarify-api-cli-strategy.md](../docs/clarify-api-cli-strategy.md).
