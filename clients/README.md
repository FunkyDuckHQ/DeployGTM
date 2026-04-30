# DeployGTM Client Workspaces

Client workspaces live under:

```text
clients/{client_id}/
```

Each client should use this convention:

```text
clients/{client_id}/
├── config/
│   ├── scoring.json
│   ├── signal_definitions.json
│   ├── vendors.json
│   └── workflows.json
├── inputs/
│   └── accounts.json
├── outputs/
│   └── score_snapshots.json
└── runs/
    └── {execution_id}.json
```

The engine should load client configuration from this folder instead of hardcoding client-specific paths in scripts.
