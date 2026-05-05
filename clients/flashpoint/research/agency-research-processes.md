# Flashpoint Agency Research Processes

## Purpose

Adapt Mitchell Keller's validated research-process pattern to Flashpoint's agency wedge.

The goal is not to research "market research agencies" broadly. The goal is to find agencies where Flashpoint has a plausible wedge, proof story, and reason to act now.

## Process Stack

Run in this order:

1. Agency profile.
2. Vertical and proof fit.
3. Growth and marketing signals.
4. Hiring/activity signals.
5. Job-role insights if hiring reveals research ops or delivery roles.
6. Competitive/positioning context.
7. Flashpoint signal stack.
8. ICP/urgency score.
9. Copy packet.

## Process 1: Agency Profile

Goal: confirm what the agency does, who they serve, size/stage, and whether they are a real target.

Mitchell source process:

- `find-profiles.md`

Search patterns:

- `{{company_name}} {{category}} company overview`
- `site:linkedin.com/company {{company_name}}`
- `site:rocketreach.co {{company_name}}`
- `{{company_name}} official website about`

Extract:

- agency category
- services offered
- employee count
- HQ / geography
- verticals served
- key people
- source URLs
- confidence

Kill patterns:

- results about generic market research statistics
- broad industry analyst reports
- unrelated agencies with similar names
- profile pages that do not resolve the domain

## Process 2: Vertical And Proof Fit

Goal: determine whether a target agency maps to Flashpoint proof or likely use cases.

Search patterns:

- `site:{{domain}} bank OR banking OR "financial services" OR fintech`
- `site:{{domain}} CPG OR consumer OR "product innovation" OR "concept testing"`
- `site:{{domain}} "emerging markets" OR "tracking study" OR tracker`
- `site:{{domain}} case study OR clients OR work OR industries`

Extract:

- named verticals
- relevant client categories
- case studies
- repeat/tracker language
- proof asset match
- safe claim / risky claim notes

Stop when:

- one strong vertical match is found with source URL, or
- no vertical proof appears after owned-site and profile checks.

## Process 3: Growth And Marketing Signals

Goal: determine whether the agency is investing in growth or likely receptive to differentiation.

Mitchell source process:

- `find-growth-signals.md`

Search patterns:

- `site:{{domain}} blog OR pricing OR newsletter OR demo OR "book a call"`
- `site:{{domain}}/blog`
- `{{company_name}} {{category}} site:twitter.com OR site:x.com OR site:instagram.com OR site:linkedin.com`
- `{{company_name}} {{category}} podcast OR webinar OR event OR conference`

Extract:

- content recency
- lead capture mechanisms
- events/webinars
- social/community proof
- marketing maturity

Kill patterns:

- generic "how to market research" articles
- search results about the target's clients rather than the agency itself
- YouTube site searches

## Process 4: Hiring And Research Ops Signals

Goal: find active operational needs through hiring.

Mitchell source processes:

- `find-hiring.md`
- `find-job-role-insights.md`

Search patterns:

- `{{company_name}} {{category}} careers`
- `{{company_name}} site:boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com OR site:wellfound.com`
- `site:{{domain}}/careers`
- `{{company_name}} "we're hiring" OR "join our team" OR "open positions"`

Role titles to inspect if found:

- Research Operations
- Survey Programmer
- Insights Manager
- Data Collection Manager
- Project Manager
- Client Delivery
- Quantitative Researcher
- Behavioral Scientist

Extract:

- ATS platform
- role titles
- departments hiring
- seniority
- role pain implied by job descriptions
- budget/ability signals
- urgency/willingness signals

Do not search:

- `site:linkedin.com/jobs {{company_name}}`
- generic salary searches unless compensation data is specifically needed

## Process 5: Competitive And Positioning Context

Goal: understand whether Flashpoint should be positioned as replacement risk, delivery leverage, or RFP differentiation.

Mitchell source process:

- `find-competitors.md`

Search patterns:

- `{{company_name}} {{category}} alternatives OR competitors OR "vs" OR "compared to"`
- `{{company_name}} {{category}} competitors`
- `best {{category}} agencies`
- `{{company_name}} vs {{top_competitor_from_above}}`

Extract:

- competitors
- positioning angle
- where the agency wins
- where they may feel pressure
- whether Flashpoint should be framed as leverage or differentiation

## Flashpoint Output Shape

```yaml
account_id: ___
company_name: ___
domain: ___
agency_profile:
  services: ___
  verticals: ___
  size_stage: ___
proof_fit:
  matching_story: ___
  safe_claims:
    - ___
  risky_claims:
    - ___
signals:
  - signal_definition_id: ___
    summary: ___
    source_url: ___
    confidence: 0.0
    ability_to_act_evidence: ___
    willingness_to_act_evidence: ___
recommended_route: ___
copy_angle: ___
sources:
  - ___
```

## Source Notes

- Research methodology source: https://github.com/MitchellkellerLG/research-process-builder
- Profile process source: https://github.com/MitchellkellerLG/research-process-builder/blob/master/processes/find-profiles.md
- Growth process source: https://github.com/MitchellkellerLG/research-process-builder/blob/master/processes/find-growth-signals.md
- Hiring process source: https://github.com/MitchellkellerLG/research-process-builder/blob/master/processes/find-hiring.md
- Job role process source: https://github.com/MitchellkellerLG/research-process-builder/blob/master/processes/find-job-role-insights.md
- Competitor process source: https://github.com/MitchellkellerLG/research-process-builder/blob/master/processes/find-competitors.md
