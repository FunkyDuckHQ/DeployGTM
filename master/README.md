# DeployGTM Master Architecture

## Current State

This folder defines the durable operating architecture for DeployGTM: a headless, adapter-based GTM operating layer that turns natural-language business goals into sourced research, account scoring, signal monitoring, enrichment, messaging, routing, acquisition operations, and reporting.

## Files

- [design-principles.md](design-principles.md): operating beliefs, Josh Whitfield / GTM Engineer School E4 principles, Clay alpha signal principles, and the adapter-first posture.
- [build-spec.md](build-spec.md): end-to-end build spec, including the Peregrine 3-month engagement language and workflow.
- [adapter-contracts.md](adapter-contracts.md): contracts for CRM, Signal, Enrichment, Content, Memory, Scoring, Planner, and Validation adapters.
- [canonical-schema.md](canonical-schema.md): canonical objects used across the system, including ICP, SignalDefinition, ScoreSnapshot, Persona, Playbook, ValueProp, MessageMatrix, and CampaignTest.
- [scoring-model.md](scoring-model.md): ICP score, urgency score, decay, routing thresholds, and engagement feedback.
- [client-workflow.md](client-workflow.md): practical workflow from intake command through prep, customer docs, account scoring, enrichment, copy, testing, manual routing, and success tracking.
- [growth-engine-integration.md](growth-engine-integration.md): integration of the Ascend-style Growth Engine pattern: ICP research, data-driven brand/message alignment, acquisition execution, CRM attribution, nurture, SLA, and operations.
- [sdr-automation-map.md](sdr-automation-map.md): six-workstream SDR automation coverage model, human boundary, Signal Audit impact, and guarantee guardrails.
- [vendor-strategy.md](vendor-strategy.md): vendor evaluation strategy for Mantis-style providers, uncommon data access, adapter fit, and cost per useful signal.
- [../docs/clarify-api-cli-strategy.md](../docs/clarify-api-cli-strategy.md): Clarify-first CRM/workspace posture plus API/CLI control-plane rules.

Related contracts and templates:

- [../docs/content-adapter-contract.md](../docs/content-adapter-contract.md): deeper standalone contract for messaging adapters such as ClaudeMarkdownContentAdapter or OctaveContentAdapter.
- [../templates/vendor-evaluation.yaml](../templates/vendor-evaluation.yaml): reusable template for deciding whether a vendor should be piloted, integrated, rejected, or held.

## Build Priorities

1. Add Growth Engine and vendor objects/contracts into `canonical-schema.md` and `adapter-contracts.md`.
2. Convert the canonical schema into machine-readable YAML or JSON schema.
3. Create example client fixtures for Peregrine Space.
4. Create an ICP scoring worksheet or script using the scoring model.
5. Create validated research process templates modeled on Mitchell Keller's research-process-builder.
6. Create a SignalDefinition template that can be translated into BirdDog monitoring setup.
7. Create a MessageMatrix template for Claude/Octave-backed content generation.
8. Create a weekly growth report template that reads from canonical scoring and execution objects.
9. Add `automation_coverage.json` to Signal Audit output using the six-workstream SDR automation coverage model.
10. Run vendor evaluations for MANTIS Group, Mantis Solutions, Firecrawl, People Data Labs, Apollo, Clay, Bombora, Demandbase, and any niche vertical data sources relevant to the client.

## Source Spine

Primary internal sources:

- DeployGTM Drive Build Spec
- DeployGTM Drive Adapter Contracts
- DeployGTM Drive Canonical Schema
- DeployGTM Drive Context Engine Spec
- Peregrine Space Working Brief
- User-provided Growth Engine idea file based on the Ascend/FlyFlat growth system
- User guidance: data is context, context is everything

External concept sources:

- Josh Whitfield / GTM Engineer School E4 for creativity over prompts, institutional knowledge, alpha signals, demo-quality builds, and agency positioning.
- Clay GTM alpha and custom signal materials for signal-based GTM, custom signal design, enrichment, and action routing.
- Mitchell Keller's research-process-builder for validated web research processes, ground-truth testing, quality/consistency scoring, kill lists, extraction specs, and stop conditions.
- Mantis and other vendor categories for uncommon data, contextual targeting, owned-data activation, vertical intelligence, and differentiated context access.
