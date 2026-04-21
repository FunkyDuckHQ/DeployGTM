# DeployGTM Design Principles

## 1) Local-first execution
- Every workflow should run from a local terminal with predictable commands.
- External APIs are optional integrations, not required for development loops.

## 2) Safe by default
- Read operations should be the default path.
- Write operations must require explicit opt-in via environment flags.

## 3) Small, composable scripts
- Keep scripts focused on one job.
- Prefer plain Python + environment variables over framework-heavy setups.

## 4) Observable runs
- Every API harness run should write structured logs to `logs/`.
- Keep logs line-delimited JSON so they can be grepped and parsed quickly.

## 5) Testable without network
- Unit tests should mock network calls.
- CI/local checks should pass without live API credentials.

## 6) Convention over configuration
- Use `.env.local` for local credentials.
- Keep canonical folders stable: `scripts/`, `tests/`, `logs/`.

## 7) Minimal onboarding cost
- New contributors should be able to run first tests in minutes.
- Commands and environment expectations should be documented next to code.


## 8) Provider-agnostic interfaces
- Avoid hard-coding one CRM vendor into test harnesses and adapters.
- Use a provider switch and stable command surface so teams can migrate without rewiring runbooks.
