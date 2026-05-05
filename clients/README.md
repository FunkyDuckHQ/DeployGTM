# DeployGTM Client Workspaces

Client workspaces live under:

```text
clients/{client_id}/
```

Each client should use this convention:

```text
clients/{client_id}/
+-- config/
|   +-- scoring.json
|   +-- signal_definitions.json
|   +-- vendors.json
|   +-- workflows.json
+-- inputs/
|   +-- accounts.json
+-- outputs/
|   +-- route_report.md
|   +-- score_snapshots.json
+-- runs/
    +-- {execution_id}.json
    +-- {execution_id}.validation.json
```

## Bootstrap

Create a new client workspace from the template:

```text
python 3_operations/scripts/bootstrap_client.py --client acme
```

## Validate

Validate a client workspace before scoring or delivery work:

```text
python 3_operations/scripts/validate_client.py --client acme --write-report
```

Validation reports are written to `clients/{client_id}/runs/`.

## Run

Run the current file-based scoring workflow:

```text
python 3_operations/scripts/run_client_workflow.py --client acme
```

The engine should load client configuration from this folder instead of hardcoding client-specific paths in scripts.

## Active Workspaces

| Client | Purpose | Status |
| --- | --- | --- |
| `peregrine_space` | Space/hardware demo client used to prove the multi-client scoring spine. | Demo workspace. |
| `example_b2b_saas` | Generic second-client fixture used to prove the engine is not Peregrine-specific. | Test fixture. |
| `flashpoint` | Flashpoint GTM pilot prep: revenue map, agency research, signal definitions, scoring, and copy-packet workflow. | Onboarding workspace; no live vendor integrations. |
