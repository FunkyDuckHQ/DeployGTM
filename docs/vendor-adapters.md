# Vendor Adapter Strategy

## Purpose

DeployGTM should be vendor-aware without becoming vendor-dependent. The system can use Clay, BirdDog, Mantis, SuperSend, Octave, HubSpot, Salesforce, Apollo, Drive, Gmail, and future providers, but none of them should define the core workflow.

## Adapter Types

### CRM Adapter

Examples:

- HubSpot
- Salesforce
- Attio
- Clarify

Responsibilities:

- upsert accounts and contacts
- write scores and next actions
- create tasks
- sync source attribution
- preserve CRM IDs
- map custom fields
- respect writeback approval rules

### Sequencer Adapter

Examples:

- SuperSend
- Instantly
- Smartlead
- Outreach
- Salesloft

Responsibilities:

- create draft sequences
- push approved contacts
- preserve campaign and sequence IDs
- fetch engagement
- classify reply outcomes
- avoid owning deliverability logic internally

### Enrichment Adapter

Examples:

- Apollo
- Clay
- Clearbit-style providers
- public web research
- Mantis if useful for differentiated data

Responsibilities:

- enrich accounts
- find contacts
- verify emails
- preserve source and confidence
- support waterfall logic
- avoid enriching accounts that do not meet threshold

### Signal Adapter

Examples:

- BirdDog
- Clay signals
- Mantis
- custom web monitors
- first-party product/customer data

Responsibilities:

- create signal definitions
- monitor accounts
- fetch recommended companies
- normalize signal evidence
- apply confidence and decay
- map signal to action

### Transcript Adapter

Examples:

- Fireflies
- Gong
- Fathom
- Zoom recordings
- call notes in Drive

Responsibilities:

- fetch transcripts
- preserve speaker/source metadata
- extract pains, objections, language, and buying moments
- route learning back into personas and playbooks

### Doc Adapter

Examples:

- Google Drive
- Google Docs
- Google Sheets
- GitHub

Responsibilities:

- ingest raw customer docs
- preserve canonical specs
- sync durable artifacts
- cite sources
- avoid overwriting durable context without intent

### Content Adapter

Examples:

- Claude
- Octave
- Clay
- HubSpot AI

Responsibilities:

- generate message matrices
- draft outreach
- create call prep
- extract content findings
- cite signal and claim basis
- output reviewable artifacts

## Vendor Selection Rules

- Choose vendors for data advantage, not novelty.
- Prefer vendors that expose APIs, exports, webhooks, or reliable operator surfaces.
- Treat unusual client-specific data as a moat.
- Keep vendor-specific logic inside adapters.
- Do not build proprietary versions of commodity infrastructure like inbox warming unless it becomes a paid strategic requirement.

## Build Vs Buy Defaults

- Use SuperSend or similar tools for inbox setup, rotation, warming, and sequencing.
- Use BirdDog, Clay, Mantis, or custom monitors for signal discovery depending on data edge.
- Use CRM-native objects for client-facing action where possible.
- Build internal scoring, routing, explanation, and learning logic because that is the differentiated layer.

## Source Notes

- Strategy source: user-provided DeployGTM Strategy / Product / Architecture Condensed Brief, shared April 30, 2026.
- Existing adapter source: [master/adapter-contracts.md](../master/adapter-contracts.md).
- Supporting architecture source: [docs/architecture.md](architecture.md).
