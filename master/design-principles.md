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

---

## 9) The moat is institutional knowledge, not prompts
Prompts are replicable. The ability to identify non-obvious signals for a specific client, know which ones actually predict buying behavior, and build a system that surfaces them continuously — that is not replicable from a prompt library.

Every client engagement should produce artifacts that encode client-specific insight: which signals matter for their ICP, which accounts acted on what, what messaging angles held up, what was wrong in the first week. These artifacts are the institutional knowledge layer. They live in `projects/<client>/` and in `brain/`. They compound across engagements. Generic signal templates and generic message scaffolds do not.

Codex and Claude are execution tools. They operate on the knowledge we bring. If the knowledge layer is shallow, the output will be shallow regardless of model quality.

## 10) Alpha signals are client-specific, weird, and tied to ability and willingness to act
The 20 generic signal templates are a starting point, not the product. A funding announcement is not an alpha signal — everyone is watching it. The alpha is what most operators miss.

A real alpha signal for a given client might be: their target buyers consistently post about a specific workflow pain on LinkedIn the week after a board meeting; or a downstream customer segment is consolidating in a way that forces their ICP to re-evaluate tooling; or a niche job title is appearing at accounts two quarters before they go to market with a new product line.

Alpha signals have two required properties:
- **Ability to act**: the account has the budget, headcount, or decision cycle to actually buy in the near term.
- **Willingness to act**: something in their external behavior signals that the problem is live and has urgency.

Generic signals (hiring SDRs, closing a round) are weak because they confirm ability without confirming willingness. The strongest signals confirm both at once.

Signal fields in `accounts.json` and `signal_strategy.json` must support `alpha: bool`, `ability_indicator: bool`, and `willingness_indicator: bool`. These are first-class fields, not metadata.

## 11) The messaging brain is an adapter, not the operating system
The `brain/` directory holds ICP definitions, persona descriptions, tone guidelines, and objection maps. It is a data source. It is not the orchestration layer.

Octave, Clay tables, a custom Claude system prompt, a HubSpot property — any of these can serve as the messaging intelligence source for a given client. The system should not assume `brain/` is the only or canonical source. `MessagingAdapter` is the abstraction. Implementations include `LocalBrainAdapter` (reads `brain/`), `OctaveAdapter`, and anything else that satisfies the contract.

A pipeline that can only generate messaging from a local brain/ directory is not portable to clients who have their own intelligence layer already.

## 12) Demo-quality builds prove value before full onboarding
Do not gate value delivery on completing the full platform spine. A working account matrix with five real scored accounts, a CRM push plan, and two outreach drafts is a proof of concept that closes the next engagement. Ship that first.

The Signal Audit is the demo. It is designed to work before BirdDog is fully configured, before HubSpot is wired, and before n8n is running. The demo-quality build must be independently executable: `make signal-audit-dry-run` should always produce a complete, deliverable-ready output.

Design every new feature to have a demo-quality path that produces visible output before the full integration path is needed. Stub adapters, dry-run modes, and sample data should be first-class concerns, not afterthoughts.

## 13) The agency is an AI/GTM advisor, not an email sender
DeployGTM builds systems. The differentiation is the architecture, the signal intelligence, and the compounding institutional knowledge — not the ability to run a sequence.

Positioning as an email sender creates a race to the bottom: deliverability metrics, open rates, reply rates, volume. Positioning as an AI/GTM advisor creates a different conversation: what signals should we be watching, what does our ICP actually look like, why isn't the pipeline working, and what does the system need to do differently.

The practical implication for the codebase: email sending is a deferred, gated capability. The value the system delivers before sending is turned on — scored accounts, signal map, ICP strategy, outreach drafts, CRM plan — should be substantial enough to justify the engagement fee. If it is not, the sending capability will not save it.

This also means: never own sending until deliverability controls, suppression lists, unsubscribe handling, bounce management, and approval workflows are built. Owning sending without controls destroys the advisor positioning.
