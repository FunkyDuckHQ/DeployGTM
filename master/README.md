# DeployGTM Master Architecture

## Current State

This folder defines the durable operating architecture for DeployGTM: a headless, adapter-based GTM operating layer that turns natural-language business goals into sourced research, account scoring, signal monitoring, enrichment, messaging, routing, and reporting.

## Files

- [design-principles.md](design-principles.md): operating beliefs, Josh Whitfield / GTM Engineer School E4 principles, Clay alpha signal principles, and the adapter-first posture.
- [build-spec.md](build-spec.md): end-to-end build spec, including the Peregrine 3-month engagement language and workflow.
- [adapter-contracts.md](adapter-contracts.md): contracts for CRM, Signal, Enrichment, Content, Memory, Scoring, Planner, and Validation adapters.
- [canonical-schema.md](canonical-schema.md): canonical objects used across the system, including ICP, SignalDefinition, ScoreSnapshot, Persona, Playbook, ValueProp, MessageMatrix, and CampaignTest.
- [scoring-model.md](scoring-model.md): ICP score, urgency score, decay, routing thresholds, and engagement feedback.
- [client-workflow.md](client-workflow.md): practical workflow from intake command through prep, customer docs, account scoring, enrichment, copy, testing, manual routing, and success tracking.

Related contract:

- [../docs/content-adapter-contract.md](../docs/content-adapter-contract.md): deeper standalone contract for messaging adapters such as ClaudeMarkdownContentAdapter or OctaveContentAdapter.

## Build Priorities

1. Convert the canonical schema into machine-readable YAML or JSON schema.
2. Create example client fixtures for Peregrine Space.
3. Create an ICP scoring worksheet or script using the scoring model.
4. Create a SignalDefinition template that can be translated into BirdDog monitoring setup.
5. Create a MessageMatrix template for Claude/Octave-backed content generation.
6. Create a weekly engagement report template that reads from canonical scoring and execution objects.

## Source Spine

Primary internal sources:

- DeployGTM Drive Build Spec
- DeployGTM Drive Adapter Contracts
- DeployGTM Drive Canonical Schema
- DeployGTM Drive Context Engine Spec
- Peregrine Space Working Brief

External concept sources:

- Josh Whitfield / GTM Engineer School E4 for creativity over prompts, institutional knowledge, alpha signals, demo-quality builds, and agency positioning.
- Clay GTM alpha and custom signal materials for signal-based GTM, custom signal design, enrichment, and action routing.
