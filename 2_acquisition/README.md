# 2 Acquisition

This folder turns research and messaging into controlled acquisition tests.

## Job

Plan and operate outbound, paid, CRM, nurture, and SLA workflows without writing to production systems until a human approves.

## Inputs

- ICP definitions
- scored account lists
- signal definitions
- personas
- value props
- message matrices
- campaign specs
- CRM attribution rules

## Core Outputs

- `outbound/`: cold email, LinkedIn, and manual sales plays
- `paid/`: Meta, LinkedIn, and future paid channel specs
- `crm/`: attribution rules, lifecycle stages, lead scoring, and writeback plans
- `nurture/`: stage-based nurture flows with eject conditions
- `sla/`: high-value lead routing and response-time workflows
- `experiments/`: campaign and message-market fit tests

## Operating Rules

- Drafts, not sends.
- Never write to production CRM, ad platforms, or outbound tools without explicit approval.
- Campaign specs must include budget ceilings, graduation criteria, and pause criteria.
- Never delete campaigns by default; pause or archive.
- Attribute contacts before scaling spend.
- Route high-urgency accounts to humans, not fully automated outbound.

## First Pass Checklist

1. Pick one channel for the first controlled test.
2. Define the campaign or outbound hypothesis.
3. Attach ICP and urgency thresholds.
4. Build channel-specific copy from message matrices.
5. Define approval, pause, and graduation criteria.
6. Define CRM writeback and attribution rules.
7. Launch only after human review.

## Source Notes

- Based on the Growth Engine acquisition stack: Meta, LinkedIn, CRM attribution, nurture flows, 5-minute SLA, and cold outreach.
- Maps to DeployGTM CampaignSpec, CampaignTest, AttributionRule, NurtureFlow, SLAWorkflow, and ExecutionResult objects.
