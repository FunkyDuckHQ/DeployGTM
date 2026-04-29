# Vercel Deployment

This repo now includes a static dashboard at the root.

## Deploy

1. Import `FunkyDuckHQ/DeployGTM` into Vercel.
2. Framework preset: `Other`.
3. Build command: `npm run build`.
4. Output directory: `dist`.

If your host still auto-detects Python, the repo root also includes `app.py`, `main.py`, and `server.py` as dependency-free Python entrypoints that serve the same static dashboard.

## Entry Point

- `/` loads `index.html`.
- The dashboard reads `3_operations/outputs/peregrine_score_snapshots.json`.
- The linked Markdown report is at `3_operations/outputs/peregrine_route_report.md`.

## Current Scope

This is a sandbox UI, not the final app.

It visualizes:

- account scores
- urgency scores
- route decisions
- evidence
- next actions

Next UI iteration should add:

- upload or paste accounts
- run scoring through an API/serverless function
- vendor evaluation view
- message matrix view
- weekly report view
