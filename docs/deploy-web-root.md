# Deploying The Web Dashboard

The repository contains Python scripts for scoring and operations, so some hosts auto-detect the repo root as a Python app.

Deploy the dashboard from the isolated `web/` folder instead.

## Vercel Settings

- Root Directory: `web`
- Framework Preset: `Other`
- Build Command: `npm run build`
- Output Directory: `dist`

## Why

The `web/` folder has its own `package.json`, `vercel.json`, static assets, and copied demo data. It does not include the repo's Python scripts, so Vercel should not look for `app.py`, `main.py`, or other Python entrypoints.
