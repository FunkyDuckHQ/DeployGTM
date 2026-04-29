# DeployGTM Growth Engine Operating Guide

## What This Is

This is the practical operating layer for DeployGTM.

The goal is to turn client context and proprietary data into a repeatable growth engine:

1. Research the real ICP.
2. Extract the client's institutional knowledge.
3. Define client-specific alpha signals.
4. Score accounts for fit and urgency.
5. Build buyer profiles and message matrices.
6. Route accounts to automation, manual sales review, nurture, or hold.
7. Track learning through reports and score updates.

## Core Belief

Data is context, and context is everything.

The advantage is not a prompt. The advantage is the data a client has, the signals competitors do not monitor, the vendors that expose uncommon data, and the operator's ability to turn that context into action.

## Workspace Flow

Use these folders in order:

1. `0_research/`: ICP, personas, signals, research processes, account scoring.
2. `1_brand/`: voice traits, value props, creative angles, message matrices.
3. `2_acquisition/`: outbound, paid, CRM, nurture, SLA, campaign tests.
4. `3_operations/`: scripts, logs, audits, reports.

Use `master/` for architecture and durable system decisions.

Use `templates/` for repeatable file shapes.

Use `.claude/skills/` for repeatable operating moves.

## First Client Build Sequence

1. Create or update the client working brief.
2. Run `research-process-builder` for 3 to 5 alpha signal hypotheses.
3. Run `ops-icp-analysis` to create ICP definitions and first score snapshots.
4. Run `ops-signal-design` to define BirdDog-ready signal definitions.
5. Run `ops-message-matrix` to create persona/signal-specific copy systems.
6. Run `ops-campaign-spec` to define the first controlled test.
7. Run `ops-weekly-growth-report` after execution data exists.

## Approval Rules

Drafts, not sends.

Human approval is required before:

- production CRM writes
- bulk contact updates
- ad campaign activation
- budget increases
- outbound sequence launch
- Slack/SMS notifications to live teams
- delete/archive operations

## Source Notes

- User-provided Growth Engine idea file based on Ascend/FlyFlat.
- Josh Whitfield / GTM Engineer School E4 principles: creativity and institutional knowledge are the moat; alpha signals should be client-specific and actionable; agency positioning shifts toward AI/GTM advisor.
- Clay GTM alpha and custom signal materials: vendor/data access and custom signals can create practical GTM advantage.
- Mitchell Keller research-process-builder: validated research processes, ground truth, kill lists, quality/consistency scoring, extraction rules, and stop conditions.
