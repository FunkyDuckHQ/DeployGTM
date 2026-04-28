# n8n Runtime Specs

DeployGTM keeps the business logic in Python and GitHub. n8n is the durable runtime for schedules, webhooks, retries, approval gates, and notifications after the scripts pass the trusted local loop.

## Runtime Boundary

- n8n triggers commands and records execution state.
- Python scripts generate artifacts and make deterministic decisions.
- Claude/Codex/OpenAI generate or review strategy, research, and copy.
- CRM writes require an explicit approval step.
- Managed email sending is deferred until deliverability, suppression, warmup, and approval controls exist.

## Workflows

| Workflow | Trigger | Python command | Write behavior |
|---|---|---|---|
| Signal Audit intake | Form/webhook | `python -m scripts.platform.cli intake ...` | Writes repo artifacts only |
| Daily BirdDog pull | Schedule | `python scripts/birddog.py pull-signals` | Reads BirdDog, writes CSV/artifacts |
| Signal strategy refresh | Manual/schedule | `python -m scripts.platform.cli signal-strategy --client <client>` | Writes signal manifest only |
| Account matrix scoring | Manual/schedule | `python -m scripts.platform.cli account-matrix --client <client>` | Writes `accounts.json` |
| CRM push approval | Manual approval | `python -m scripts.platform.cli crm-plan --client <client>` | Dry-run plan by default |
| Email engagement sync | SuperSend webhook | `python scripts/email_sync.py ingest --client <client> --payload <payload>` | Updates matrix only |
| Weekly client report | Schedule | `python -m scripts.platform.cli deliverable --client <client>` | Writes deliverable artifacts |

## Activation Rule

Do not import these specs into production n8n until:

- `python -m pytest tests -q` passes.
- `make daily` passes.
- `make signal-audit-dry-run` passes.
- CRM push plans remain dry-run by default.
- BirdDog API write capabilities are confirmed.
