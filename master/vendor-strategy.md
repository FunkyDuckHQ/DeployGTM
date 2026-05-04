# Vendor Strategy

## Purpose

DeployGTM should stay ahead by finding vendors that expose data, context, or execution access other teams do not have.

Vendors are not the operating system. Vendors are context sources, execution surfaces, or workflow accelerators. DeployGTM owns the canonical schema, scoring logic, routing logic, and client-specific GTM intelligence.

Clarify is currently the preferred CRM/workspace candidate for the DeployGTM operating surface. That preference should shape adapter priority, not core lock-in. HubSpot remains useful as a compatibility adapter for clients that already run on HubSpot.

## Core Thesis

Data is context, and context is everything.

The winner is not the team with the best prompt. The winner is the team with better context, better access, better interpretation, and faster action.

A vendor is valuable when it gives DeployGTM at least one of these advantages:

- data competitors cannot easily access
- faster signal detection
- better source provenance
- better enrichment accuracy
- better audience targeting
- better workflow execution
- better evidence for sales action
- better client-specific learning loops

## Vendor Evaluation Criteria

Score every vendor against these dimensions before integrating it:

| Dimension | Question |
| --- | --- |
| Data uniqueness | Does this vendor expose data or context that is hard to get elsewhere? |
| Client specificity | Can the vendor support weird, client-specific alpha signals? |
| API access | Can DeployGTM read/write programmatically without manual UI work? |
| Provenance | Does the vendor preserve source, timestamp, and evidence? |
| Freshness | How current is the data? Can freshness be measured? |
| Compliance | Is the data source defensible, consented, and client-appropriate? |
| Cost per useful signal | How much does it cost to produce an action-worthy signal? |
| Workflow fit | Does it map cleanly into an existing adapter? |
| Lock-in risk | Can we swap it without changing the core system? |
| Human leverage | Does it save expert time or create insight experts would miss? |

## Adapter Categories

### CRM / Workspace Adapter

Projects DeployGTM intelligence into the system reps actually use.

Preferred candidate:

- Clarify, if API/MCP access, schema control, campaign/list/task support, and write approvals are available for the workspace

Compatibility candidates:

- HubSpot
- Salesforce
- Attio

Canonical outputs:

- `Account`
- `Contact`
- `Opportunity`
- `Task`
- `CRMWritePlan`
- `EngagementEvent`
- `ScoreSnapshot`

Decision rule:

- Build against DeployGTM canonical objects first.
- Use Clarify as the preferred operator workspace when it can support the flow.
- Do not place scoring, routing, or research logic inside Clarify-specific code.

### Research Adapter

Finds and validates client-specific evidence from public or semi-public sources.

Candidate vendors/tools:

- Firecrawl for clean web data and site extraction
- Brave Search or similar search APIs
- Mitchell Keller-style validated research processes as methodology

Canonical outputs:

- `ResearchProcess`
- `ResearchRun`
- `ResearchFinding`
- `Signal`

### Company Data Adapter

Enriches accounts with firmographics, funding, headcount, social profiles, hierarchy, and other company context.

Candidate vendors/tools:

- People Data Labs
- Apollo
- Clay data waterfalls
- Demandbase account intelligence

Canonical outputs:

- `Account`
- `ScoreSnapshot`
- `ResearchFinding`

### People Data Adapter

Finds and enriches buyer contacts, job changes, employment history, contact data, and role fit.

Candidate vendors/tools:

- People Data Labs
- Apollo
- Clay
- LinkedIn-derived providers where compliant

Canonical outputs:

- `Contact`
- `ContactProfile`
- `ScoreSnapshot`

### Intent Data Adapter

Detects account-level buying intent, topic research, competitive interest, and category movement.

Candidate vendors/tools:

- Bombora Company Surge
- Demandbase Intent
- G2 Buyer Intent where available
- 6sense or similar ABM intent platforms

Canonical outputs:

- `Signal`
- `ScoreSnapshot`
- `recommended_route`

### Technographic Adapter

Detects technologies, infrastructure, integrations, and stack patterns that reveal fit or urgency.

Candidate vendors/tools:

- BuiltWith
- Wappalyzer
- Demandbase technographics
- Clay waterfalls

Canonical outputs:

- `Account`
- `Signal`
- `ICPDefinition`

### Contextual Audience Adapter

Builds or activates audience segments based on content context, publisher data, or contextual targeting logic.

Candidate vendors/tools:

- Mantis Solutions, which positions itself around contextual targeting, brand safety, and audience segmentation
- Demandbase or Bombora audience activation partners
- paid media platform audiences

Canonical outputs:

- `CampaignSpec`
- `CreativeAngle`
- `AudienceSegment`

### First-Party Data Adapter

Turns client-owned data into segmentation, audience, retention, expansion, and signal logic.

Candidate vendors/tools:

- MANTIS Group, which positions around data appraisal, readiness, productization, and GTM/data brokerage
- warehouse or reverse ETL tooling
- client CRM/product data

Canonical outputs:

- `ClientBrief`
- `ICPDefinition`
- `AttributionRule`
- `SignalDefinition`
- `CampaignSpec`

### Vertical Intelligence Adapter

Uses niche vendor data for a specific market where generic GTM data is weak.

Examples:

- Mantis AI for media/video intelligence contexts such as sponsorship exposure, semantic video search, and content archives
- MantisCore for security intelligence contexts if targeting cybersecurity teams or using verified security posture signals
- space, defense, healthcare, construction, logistics, or procurement-specific data vendors as discovered

Canonical outputs:

- `ResearchFinding`
- `Signal`
- `ICPDefinition`
- `ScoreSnapshot`

## Mantis Notes

The word "Mantis" maps to multiple vendors. Do not assume one integration.

Known candidates found so far:

1. MANTIS Group: data and marketing transformation, data appraisal/readiness/productization, and GTM/data brokerage.
2. Mantis Solutions: contextual targeting, brand safety, and audience segmentation for advertising.
3. Mantis AI: video intelligence for media workflows, including semantic video search and brand exposure analytics.
4. MantisCore: autonomous security intelligence, attack surface mapping, exploitability reasoning, and evidence-based findings.

DeployGTM should evaluate each only against the client use case. For most B2B GTM work, MANTIS Group is a strategic/commercial data partner, Mantis Solutions is a paid media/contextual targeting candidate, and Mantis AI or MantisCore are vertical-specific intelligence candidates.

## Vendor Decision Rule

Integrate a vendor only if it improves one of these loops:

- better ICP discovery
- better alpha signal detection
- better urgency scoring
- better contact/buying committee identification
- better message evidence
- better campaign targeting
- better attribution
- better reporting or learning

If a vendor only duplicates existing data at higher cost, treat it as optional.

## Vendor Integration Workflow

1. Define the vendor's possible advantage.
2. Map it to an adapter category.
3. Run a sample against 10 known accounts.
4. Score useful signal rate.
5. Score source quality and freshness.
6. Calculate cost per useful signal.
7. Decide read-only, draft-write, or production-write mode.
8. Add environment variables only after the vendor passes evaluation.
9. Create a small adapter or workflow before expanding use.

## API And CLI Management Rule

Every vendor integration should be exposed through a stable internal API/CLI control plane before it becomes production automation.

Minimum lifecycle:

- validate credentials and scopes
- describe read/write capabilities
- read normalized objects
- generate a write plan
- dry-run payloads
- write only with explicit approval
- sync events back into DeployGTM
- store an execution receipt

This is how Codex, Claude, and future agents should manage complex APIs without becoming the runtime themselves.

## Source Notes

- User guidance: data is context, context is everything; vendor access and uncommon data should become a differentiator.
- MANTIS Group positions around data appraisal, readiness, productization, and GTM/data brokerage: https://www.mantisgroup.ai/
- Mantis Solutions positions around contextual targeting, brand safety, and audience segmentation: https://www.mantissolutions.com/
- Mantis AI positions around video intelligence, semantic video search, smart archives, and brand exposure analytics: https://mantis-ai.com/
- MantisCore positions around autonomous security intelligence with discovery, reasoning, testing, and evidence loops: https://mantiscore.ai/
- People Data Labs offers person and company enrichment/search APIs and data feeds: https://www.peopledatalabs.com/
- Firecrawl provides an API to search, scrape, and interact with the web for AI applications: https://www.firecrawl.dev/
- Demandbase and Bombora provide B2B intent/account intelligence data: https://www.demandbase.com/products/account-intelligence/intent/ and https://bombora.com/intent/
- Clarify API/MCP/product notes are summarized in [../docs/clarify-api-cli-strategy.md](../docs/clarify-api-cli-strategy.md).
