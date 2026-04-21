# Local API Testing Plan

## Goal
Stand up a minimal local harness for three first checks:
1. HubSpot read test
2. HubSpot upsert company test
3. one second API read test

## Folder conventions
- `.env.local`: local credentials and endpoints (never committed)
- `scripts/local_api_harness.py`: executable harness
- `tests/test_local_api_harness.py`: offline unit tests with mocks
- `logs/local_api_tests.jsonl`: structured run log output

## Environment variables
Add these to `.env.local`:

```bash
HUBSPOT_ACCESS_TOKEN=...
LOCAL_API_ALLOW_WRITE=0
ONE_SECOND_API_URL=http://localhost:8080/health
ONE_SECOND_API_KEY=
BIRDDOG_API_KEY=...
DEEPLINE_BASE_URL=...
DEEPLINE_API_KEY=...
```

## Env setup notes
- `.env.local.example` is a template. Copy it to `.env.local` and fill values locally.
- For the current first harness, only `HUBSPOT_ACCESS_TOKEN` and one-second endpoint/key are needed.
- BirdDog and Deepline keys are included so you can expand tests next without changing file shape.

## Beyond local (team/staging/prod)
- Local dev: keep secrets in `.env.local` (gitignored).
- Shared environments: store secrets in your secrets manager (e.g., 1Password, Doppler, AWS/GCP/Azure Secret Manager, GitHub Actions Secrets).
- CI/staging/prod should inject environment variables directly; no `.env.local` required there.
- Harness supports additional env profiles via `--env-file` (for example, `.env.staging`).

## Runbook

```bash
# Validate env first
python scripts/local_api_harness.py validate-env

# Optional: load an additional profile
python scripts/local_api_harness.py --env-file .env.staging validate-env

# HubSpot read (safe)
python scripts/local_api_harness.py hubspot-read

# HubSpot upsert (requires LOCAL_API_ALLOW_WRITE=1)
python scripts/local_api_harness.py hubspot-upsert-company --domain example.com --name "DeployGTM API Harness"

# one second API read
python scripts/local_api_harness.py one-second-read

# all three
python scripts/local_api_harness.py run-all --domain example.com --name "DeployGTM API Harness"
```

## Safety checks
- Keep `LOCAL_API_ALLOW_WRITE=0` during normal development.
- Use dedicated sandbox/test records when write-testing HubSpot.
- Review `logs/local_api_tests.jsonl` after each run.

## Next expansion (after first harness)
- Add retry/backoff wrappers for transient 429/5xx responses.
- Add a `make api-test` shortcut.
- Add optional schema assertions for API response bodies.
