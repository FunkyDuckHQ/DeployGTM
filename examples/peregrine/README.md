# Peregrine Sandbox

This is a runnable sandbox for the DeployGTM scoring loop.

It is not production research. It uses a small example dataset to make the ICP, urgency, decay, and routing logic inspectable.

## Run

```powershell
python 3_operations\scripts\score_accounts.py --as-of 2026-04-29
```

If `python` is not on PATH in Codex Desktop, use the bundled runtime path shown by workspace dependencies.

## Current Example Result

As of 2026-04-29:

- Xona Space Systems: `icp_score=92.0`, `urgency_score=55.4`, route `enrich_and_campaign_test`
- Kepler Communications: `icp_score=80.0`, `urgency_score=19.34`, route `enrich_selectively_or_monitor`
- Generic Aerospace Prime: `icp_score=43.0`, `urgency_score=0`, route `exclude`

## Source Notes

- Peregrine Space working brief in Drive: https://docs.google.com/document/d/1zz47YzPlD7Mz_BQOutgwNDWkgujtRgE609xICAag2Ws
- DeployGTM scoring model: `master/scoring-model.md`
- DeployGTM canonical schema: `master/canonical-schema.md`
