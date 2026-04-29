# 3 Operations

This folder is for scripts, logs, reports, and audit trails.

## Job

Run the growth engine in a way that is observable, reversible, and safe.

## Inputs

- platform API exports
- CRM exports
- outbound performance data
- signal events
- score snapshots
- execution results
- manual review decisions

## Core Outputs

- `scripts/`: simple Python scripts for pull, audit, scoring, reporting, and dry-run writes
- `logs/`: JSONL run logs
- `reports/`: daily reviews, weekly growth reports, and monthly learning reports
- `audits/`: source classification, CRM hygiene, claim evidence, and campaign safety audits

## Operating Rules

- Scripts should be small and independent.
- One platform outage should not break the rest of the engine.
- Pull and report before write.
- Every write-capable script must support dry-run mode.
- Logs should be line-delimited JSON when possible.
- Reports should separate market learning, execution learning, and business outcomes.

## Starter Scripts To Build

- `icp_score.py`
- `signal_decay.py`
- `crm_attribution.py`
- `crm_source_audit.py`
- `weekly_growth_report.py`
- `ad_daily_review.py`
- `birddog_signal_export.py`
- `message_matrix_export.py`

## Source Notes

- Based on the Growth Engine operations model: Python scripts, JSONL logs, weekly reports, attribution audits, and guarded API writes.
- Connects to DeployGTM ExecutionResult and ScoreSnapshot objects.
