# DeployGTM Build Specification

This document defines what the system must do, in what order, and at what quality bar. It is the contract between design decisions and implementation.

---

## Guiding constraint

Every build decision should be answerable with: "Can we run the Signal Audit dry-run with this change and produce a deliverable-ready output?" If no, it is not ready to merge.

---

## System layers (in order of trust)

### L0 — Source of truth
GitHub Cloud: `FunkyDuckHQ/DeployGTM`

Nothing is durable until it is committed here. Local-only artifacts are not deliverables.

### L1 — State and artifacts
```
projects/<client>/platform/intake.json
projects/<client>/platform/context_pack.json
projects/<client>/platform/icp_strategy.json
projects/<client>/platform/signal_strategy.json
projects/<client>/platform/accounts.json
projects/<client>/platform/crm_push_plan.json
projects/<client>/platform/birddog_signal_manifest.json
projects/<client>/deliverable/signal_audit_summary.md
projects/<client>/deliverable/target_accounts.csv
brain/                   (ICP, personas, tone, objections — first-class data source)
config.yaml              (tool toggles, scoring thresholds)
```

Artifacts at L1 are the contract between pipeline stages. Stage N reads the output of Stage N-1. No stage should read from another stage's internal state directly.

### L2 — Adapters
CRM, messaging, enrichment, and signal adapters. All must satisfy provider-agnostic abstract base classes. No business logic lives here.

```
scripts/platform/adapters/base.py        (CRMAdapter ABC)
scripts/platform/adapters/types.py       (CompanyRecord, ContactRecord, CRMContext, SyncResult)
scripts/platform/adapters/messaging.py   (MessagingAdapter ABC — see adapter-contracts.md)
scripts/platform/adapters/signal.py      (SignalAdapter ABC — see adapter-contracts.md)
```

### L3 — Business logic
Python scripts in `scripts/platform/`. Deterministic. No side effects unless explicitly invoked. Runnable offline in dry-run mode.

```
intake.py          → intake.json
context_pack.py    → context_pack.json
icp_strategy.py    → icp_strategy.json
signal_strategy.py → signal_strategy.json + birddog_signal_manifest.json
account_matrix.py  → accounts.json
crm_push_plan.py   → crm_push_plan.json
deliverable.py     → signal_audit_summary.md + target_accounts.csv
email_sync.py      → mutates accounts.json engagement block (webhook)
```

### L4 — Entry points
`scripts/platform/cli.py` (Click CLI group). `Makefile` targets. All commands must have a `--dry-run` flag where they touch external systems.

### L5 — Runtime
n8n. Calls L4 entry points via subprocess or HTTP. Contains no business logic. Not activated until the trusted loop passes.

---

## Signal Audit pipeline — required behavior

### Stage 1: Intake
- Input: client name, domain, target outcome, offer, constraints, current tools, CRM provider
- Output: `intake.json` with governance fields (`sequencing_mode: draft_only`, `crm_scope: deploygtm_found_leads_tasks_only`, `managed_sending: deferred`)
- Required: schema version, engagement type, client slug

### Stage 2: Context Pack
- Input: `brain/` + `intake.json` + `projects/<client>/transcripts/`
- Output: `context_pack.json` with Evidence objects tracing every principle to a source file and line
- Required: no principle without a source trace

### Stage 3: ICP Strategy
- Input: `context_pack.json` + `intake.json`
- Output: `icp_strategy.json` with exactly 2 ICP objects
- Each ICP requires: name, description, fit_criteria (4 items), personas (with problem_ownership_reason), disqualifiers, source_trace
- Required: no ICP without disqualifiers; do not create a third ICP to avoid disqualification

### Stage 4: Signal Strategy
- Input: `icp_strategy.json` + `intake.json`
- Output: `signal_strategy.json` + `birddog_signal_manifest.json`
- Required: each signal must declare `alpha: bool`, `ability_indicator: bool`, `willingness_indicator: bool`
- Non-alpha signals (generic: funding, hiring) should be clearly marked; alpha signals are client-specific derivations
- Minimum 2 alpha signals per ICP before audit is considered complete

### Stage 5: Account Matrix
- Input: `projects/<client>/targets.csv` + ICP/signal strategy
- Output: `accounts.json`
- Four required scores per account: `icp_fit_score`, `urgency_score`, `engagement_score`, `confidence_score`
- Derived field: `activation_priority = 0.45*icp_fit + 0.35*urgency + 0.10*engagement + 0.10*confidence`
- Do not collapse the four scores into one. They are independently useful.

### Stage 6a: CRM Push Plan
- Input: `accounts.json` + `intake.json`
- Output: `crm_push_plan.json`
- Required: `dry_run: true`, `writes_enabled: false`, `requires_explicit_approval: true`
- Only include accounts above `min_activation_priority` (default: 60)
- Only scope to DeployGTM-found records; do not plan to ingest or modify existing CRM state

### Stage 6b: Email Sync (async, webhook-triggered)
- Input: SuperSend engagement events
- Output: mutated `accounts.json` engagement block
- Required: `--dry-run` flag; no CRM writes; idempotent on repeated events

### Stage 7: Deliverable
- Input: all platform artifacts
- Output: `signal_audit_summary.md` + `target_accounts.csv`
- Required: top 10 accounts by activation_priority; ICP summary; signal map summary; architecture recommendation

---

## Scoring contract

Do not change scoring weights without updating this spec and the `canonical-schema.md`.

```
icp_fit_score        ∈ [1, 100]   weighted ICP criteria match
urgency_score        ∈ [1, 100]   signal_type + freshness decay + birddog_score
engagement_score     ∈ [0, 100]   opens×4 (cap 20) + clicks×10 (cap 25)
                                  + replies×30 (cap 45) − bounces×25 − unsub×60
confidence_score     ∈ [1, 100]   source quality: birddog=80, full=65,
                                  domain-only=45, incomplete=25

activation_priority = 0.45×icp_fit + 0.35×urgency + 0.10×engagement + 0.10×confidence
```

---

## Demo-quality build criteria

The following must work before any other feature ships:

```bash
python -m pytest tests -q                      # all pass, no keys
make daily                                     # no keys
make signal-audit-dry-run                      # produces all 7 stage artifacts
python scripts/email_sync.py ingest \
  --client sample --payload sample.json --dry-run
python scripts/local_api_harness.py validate-env
```

If any of these fail, do not proceed to n8n, BirdDog API, or HubSpot write activation.

---

## What is not in scope until demo-quality build passes

- n8n workflow activation
- BirdDog API write capability
- HubSpot production writes
- SuperSend managed sending
- Octave adapter implementation
- Branch cleanup of PR #2 (claude/read-master-files-wWR6f)

---

## Deferred until deliverability controls exist

Email sending is not a feature until these are built and tested:
- Domain warming tracking
- Suppression list management
- Unsubscribe handling with CRM writeback
- Bounce handling (hard and soft)
- Deliverability reporting per domain
- Approval workflow before any sequence activates

Building these half-way destroys the advisor positioning. Either own it fully or defer it.

---

## Messaging intelligence

Messaging generation must use a `MessagingAdapter` interface, not direct `brain/` file reads. The local brain is one implementation. The system must be wirable to Octave or a client-owned intelligence layer without rewriting the pipeline.

See `adapter-contracts.md` for the `MessagingAdapter` ABC.

---

## Alpha signal requirement

At minimum, every client Signal Audit must produce at least 2 alpha signals per ICP. An alpha signal must satisfy:
- `alpha: true`
- At least one of `ability_indicator: true` or `willingness_indicator: true`
- A `rationale` field explaining why it is client-specific and non-generic
- A `detection_hint` that is not a copy of the signal name

If the signal strategy produces only generic signals from `SIGNAL_TEMPLATES`, the audit is incomplete.
