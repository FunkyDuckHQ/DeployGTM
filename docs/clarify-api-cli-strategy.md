# Clarify And API/CLI Control Plane Strategy

## Decision

Clarify is the preferred modern CRM/workspace candidate for DeployGTM, but it should not become the operating system.

DeployGTM owns the canonical GTM intelligence layer:

- client outcome intake
- context packs
- ICP and persona strategy
- signal definitions
- account, contact, and opportunity scoring
- source traces and rationale
- CRM push plans
- copy, tasks, and rep-ready action
- learning from signal and engagement feedback

Clarify can become the preferred place where that intelligence shows up for operators and reps. HubSpot should be treated as a compatibility adapter for clients already using it, not the default center of gravity.

## Why This Matters

GTM tools are consolidating. CRMs, enrichment tools, sequencers, call tools, workflow tools, and AI assistants are all trying to own more of the workflow.

DeployGTM should win by owning context, interpretation, and action logic across vendors:

- what the client is trying to achieve
- which accounts fit
- why now is urgent
- which people matter
- what evidence supports the play
- what the rep should do next
- what happened after action was taken

The vendor UI can change. The DeployGTM decision layer should survive.

## Clarify-First, Adapter-Safe

Clarify should be evaluated and implemented as a first-class CRM adapter because its public direction matches the desired workflow:

- flexible CRM objects and fields
- companies, people, deals, tasks, meetings, campaigns, and lists
- AI field automation and meeting/deal intelligence
- Lead Finder for company and people discovery
- Campaigns for sequence-ready execution
- MCP access for AI assistants
- API access for approved early-access integrations

The adapter rule remains: no Clarify-specific business logic outside a Clarify adapter.

DeployGTM artifacts under `projects/<client>/platform/` remain the source of what should happen. Clarify receives an approved projection of those artifacts.

## API And CLI Management Pattern

Every complex API or CLI integration should expose the same internal lifecycle:

1. `validate-env`
   - Confirm credentials, scopes, base URLs, account IDs, and sandbox/write flags.

2. `describe-capabilities`
   - Report what this integration can currently read, plan, dry-run, write, and sync.

3. `read`
   - Pull records or events into normalized canonical objects.

4. `plan`
   - Produce a write plan without changing external systems.

5. `dry-run`
   - Validate payload shape and idempotency assumptions without writing.

6. `write --confirm`
   - Perform approved external writes only after an explicit human approval path.

7. `sync-events`
   - Pull engagement, signal, or CRM activity back into scoring and learning loops.

8. `receipt`
   - Store a machine-readable execution result with timestamps, inputs, IDs, skipped rows, failures, retries, and next action.

This makes complex APIs manageable because Codex/Claude operate against stable internal commands, not every vendor's raw surface area.

## Runtime Boundary

Codex, Claude, and GPT can design, review, repair, and operate the system. They should not be the durable runtime.

Use this split:

- Python: business logic, adapters, validation, scoring, artifact compilation.
- CLI: stable operator interface for humans and AI agents.
- Local API: callable surface for dashboards, browser tests, and future services.
- n8n/Inngest/Temporal-style runtime: schedules, webhooks, retries, logs, notifications, and approvals after scripts are proven.
- Clarify MCP: useful AI-assistant access to Clarify data, but not the source of truth for DeployGTM's canonical logic.

## Clarify Implementation Sequence

1. Confirm API/MCP access for the workspace.
2. Pull the Clarify schema before writing fields.
3. Map DeployGTM canonical objects to Clarify companies, people, deals, tasks, lists, campaigns, meetings, and custom fields.
4. Build read-only adapter functions first.
5. Build `crm_push_plan.json` to Clarify dry-run output.
6. Add explicit approval gates for create/update records.
7. Add engagement/event sync from campaigns, replies, meetings, tasks, and deal changes.
8. Keep HubSpot adapter working for client compatibility, but stop designing around HubSpot-specific assumptions.

## V1 Clarify Field Mapping

| DeployGTM Field | Clarify Target |
| --- | --- |
| `icp_fit_score` | Company custom field |
| `urgency_score` | Company custom field |
| `engagement_score` | Company or person custom field |
| `confidence_score` | Company custom field |
| `activation_priority` | Company custom field or list view |
| `signal_summary` | Company note/comment or custom field |
| `source_traces` | Note/comment with links and timestamps |
| `next_action` | Task |
| `recommended_copy` | Task/comment/campaign draft |
| `buyer_profile` | Person note/comment or custom field |
| `deploygtm_project_id` | Custom field |
| `deploygtm_last_scored_at` | Custom field |

## Guardrails

- No direct external writes without a generated plan.
- No production CRM write without explicit approval.
- No managed sending until suppression, unsubscribe, deliverability, bounce, and account-warming controls exist.
- No vendor-specific logic in scoring, research, or signal modules.
- No assumption that Clarify API access is generally available; treat it as early access until confirmed in the target workspace.
- Use MCP for assistant access and schema exploration, but prefer API/adapter code for repeatable production workflows.

## Source Notes

- Clarify API help center notes that API access is through an Early Access Program and asks applicants to identify read/write needs and objects/fields: https://docs.clarify.ai/en/articles/12503528-clarify-api
- Clarify MCP exposes assistant-readable and assistant-writable CRM tools including schema, query, records, lists, campaigns, lead finder, record creation/update, tasks, custom objects, and fields: https://docs.clarify.ai/en/articles/13367278-clarify-mcp
- Clarify automation/product docs describe real-time data, workflow automation, product signals, APIs, and webhooks: https://www.clarify.ai/product/automation
- Clarify CSV import supports companies, people, and deals with field mapping, validation, update matching, failed-row reporting, and import-created lists: https://docs.clarify.ai/en/articles/13493132-import-your-data-csv
- Clarify Campaigns support multi-step email sequences, variables, stop conditions, connected email requirements, and engagement metrics: https://docs.clarify.ai/en/articles/13415130-campaigns
- Clarify Lead Finder supports company/people discovery and imported leads update existing records when matches are found: https://docs.clarify.ai/en/articles/14219316-lead-finder
