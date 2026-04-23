# Playbook — Market Mapping

How to turn an ICP into segments an SDR can actually work. Not industry categories. Not Gartner quadrants. The groupings a rep would build a day's worklist around.

## Why this exists

An ICP is a filter. A market map is a terrain. Reps can't prospect against a filter — they need terrain: "today I'm working X segment, here's how these companies are alike, here's the opening they respond to, here's the objection I'll hear."

Every Signal Audit and Retainer engagement produces a market map. It becomes the backbone of the account matrix (see `projects/deploygtm-own/account_matrix_schema.json`), the voice of the outreach generator, and the rubric the weekly report ranks against.

## Inputs

1. The client's product and buyer (from `brain/clients/<client>/icp.md`)
2. 3–5 reference customers — who they already sell to, in the client's words
3. Recent wins and recent losses — patterns in both
4. Public signals the market already broadcasts (funding rounds, hiring posts, contract awards, program announcements, SBIRs, product launches)

## The 5-step method

### 1. Cluster, don't categorize

Start with 20–40 candidate accounts. Group them by _how they buy_, not by what SIC code they share. Useful clustering axes, pick 2–3:

- **Buying motion:** bottoms-up product-led vs top-down sales-led vs procurement-led
- **Program vs product:** are they buying for a specific program/mission or a general capability?
- **Timing pressure:** contract deadline, launch window, fundraise-burn horizon
- **Integration surface:** where your product has to slot in (their bus, their CRM, their data warehouse, their GTM stack)
- **Heritage / risk tolerance:** how much qualification proof is required before they will buy

A segment is useful when you can finish this sentence for it: "Companies in this segment are all buying _because_ ___ and they are all blocked by ___."

### 2. Name segments in the rep's voice

Not "Small B2B SaaS with sales-led motion" — a rep won't remember that. Name it for the plot.

Bad: "Commercial EO companies"
Good: "Next-gen EO constellations who need flight-proven optical payloads by Q2 2025 or their manifest slips"

The name should imply the signal, the timing, and the angle in one line. If your segment name doesn't imply why-now, rework it.

### 3. Map the 4 fields per segment

Every segment gets these four fields. Carry them into `segments.md` in the brain.

| Field | What it captures |
|-------|------------------|
| **Buying trigger** | The event that makes them willing to take a call |
| **Persona-who-feels-it** | Title + the frame in their head, not yours |
| **Angle** | One-sentence directional argument |
| **Objection pattern** | The #1 thing that kills these deals, named honestly |

If you cannot fill all four with a specific sentence, the segment is not real yet. Go back to step 1.

### 4. Rank by serveability, not TAM

For each segment, score on three axes, 1–3:

- **Deal velocity** — how fast the first close can realistically happen
- **Product fit density** — are 1 in 3 accounts a fit, or 1 in 30?
- **Signal legibility** — is the why-now signal public and grep-able, or do we have to guess?

Pick the top 2–3 segments. Deprioritize everything else. A client with 6 "target segments" actually has zero — you cannot run 6 motions at once.

### 5. Wire segments to the matrix

Every account in `data/<client>_accounts.json` must specify `market` and `segment`. Those fields are not cosmetic — the weekly report ranks by them, and the outreach generator uses them to frame the angle.

Rule: no account goes in the matrix without a segment. If you cannot place an account in a segment, it is not a target account yet — it is a lead.

## Anti-patterns

- **"Enterprise" as a segment.** It is not. Pick the motion inside "enterprise" that actually matches.
- **Segments defined by firmographics only.** A segment that fits "B2B SaaS, 50–200 employees, Series B" tells the rep nothing about how to open.
- **Every account in Tier 1.** If everything is tier 1, nothing is. Discipline the tiering.
- **Rebuilding segments every quarter.** Segments should be durable for 6–12 months. Update signals and angles; don't churn the map itself.

## Deliverable shape

A market map for one engagement is ~1 page per segment:

```
## Segment: [Rep-voice name]

**Buying trigger:** [the event]
**Persona:** [title] — [frame]
**Angle:** [one sentence]
**Objection pattern:** [the honest blocker]
**Signal sources:** [SAM.gov / Crunchbase / LinkedIn / SpaceNews / etc.]
**Ranking:** velocity=X, fit=Y, signal=Z (total N)
**Representative accounts (3–5):** Name, Name, Name
```

Top 2–3 segments get loaded into the account matrix. The rest go into `brain/clients/<client>/segments.md` as a parking lot — visible, but not being worked this cycle.

## Checklist — is the map done?

- [ ] 4–8 candidate segments described
- [ ] Top 2–3 segments ranked and chosen
- [ ] Every chosen segment has buying trigger, persona, angle, objection
- [ ] Every account in the matrix has `market` + `segment` set
- [ ] Client can read the map aloud and nod — it sounds like their world, not ours
