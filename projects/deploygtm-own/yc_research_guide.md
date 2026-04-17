# DeployGTM Own — YC W26 Research Guide

*How to build the target list from the YC W26 batch. Demo Day was March 24, 2026.*

---

## Why YC W26 is the priority target

These founders just raised. They have money to spend on GTM infrastructure. Most of them are still doing sales themselves — exactly the Founder-Seller persona. Many have never hired a sales rep. They need pipeline infrastructure NOW, before they burn through their runway trying to figure out outbound manually.

The signal is: **just raised** + **no GTM infrastructure** + **need pipeline immediately**.

---

## How to pull the W26 company list

### Method 1: YC directory (fastest)

1. Go to: `https://www.ycombinator.com/companies?batch=W26`
2. Filter by: **Status = Active**, **Type = B2B**
3. Export or manually copy the list
4. For each company, note: company name, website, one-line description, industry tag

Or use the built-in command (may require manual extraction if the page returns HTML):
```bash
make signals-yc
```

### Method 2: LinkedIn

1. Search: `"YC W26" OR "Y Combinator W26" site:linkedin.com/company`
2. Filter by: Employee count 1–50, Industry = Software
3. Note founders' LinkedIn profiles for later outreach

### Method 3: Twitter/X

Search: `"YC W26" OR "W26" "demo day" -RT`  
Founders announce their companies around Demo Day (March 24, 2026).

---

## ICP filtering criteria

Keep only companies that match ALL of:
- [ ] B2B (selling to businesses, not consumers)
- [ ] Software/SaaS product (not hardware, not services-only)
- [ ] Has a product users can actually buy today (not purely pre-launch)
- [ ] US-based founders (or selling to US market)

Likely good fits (higher priority):
- Developer tools, API products, AI/ML infrastructure — these founders think in systems
- Sales/RevOps tooling — they understand the GTM problem by living it
- Vertical SaaS for SMB — typically needs outbound infrastructure quickly
- B2B marketplaces — need demand-side pipeline

Likely weak fits (lower priority or skip):
- Consumer apps with B2B pivot potential (too early)
- Deep biotech/hardware (long sales cycles, wrong buyers)
- Already well-funded growth-stage companies (have a sales team, don't need us)
- International-only focus (our motion is US market-first)

---

## Research each company (10 minutes per account)

For each filtered company, answer:
1. **What do they sell?** One sentence, in buyer language not founder language
2. **Who buys it?** Title + company type + company size
3. **Signal strength:** Did they announce funding? Are they posting about hiring? Founder on LinkedIn talking about GTM?
4. **Quick ICP check:** Does this look like a B2B SaaS company, Seed–Series A, 5–30 employees, technical or enterprise buyer?

Then run them through the pipeline:
```bash
python scripts/pipeline.py run \
  --company "Company Name" \
  --domain "companydomain.com" \
  --signal funding \
  --signal-date 2026-03-24 \
  --signal-summary "YC W26 company — raised at Demo Day, founding team doing sales"
```

Or batch them:
```bash
# Add to data/yc_w26_targets.csv first, then:
make batch-yc
```

---

## CSV format for batch runner

File: `data/yc_w26_targets.csv`

```
company,domain,signal_type,signal_date,signal_source,signal_summary
Acme AI,acme.ai,funding,2026-03-24,YC W26,"YC W26 — building AI agent infrastructure for sales teams. Founder doing all sales."
```

Add each company as a row. Run `make batch-yc` when ready.

---

## Outreach angle for YC W26 founders

The signal is public and known — use it directly.

**Don't say:** "I saw you recently raised funding..."  
**Do say:** "YC W26 — congrats. Most founders at your stage are still doing outbound manually while trying to close and ship. I build the pipeline engine. [offer]."

The pitch is tight because the situation is universal for YC founders at Demo Day stage:
- They just raised
- They're fielding inbound interest from the Demo Day announcement
- They know they need to build outbound but haven't had time
- They're probably 2–6 weeks away from hiring their first sales rep and wondering what to set up first

That's our exact buyer, at the exact right moment.

---

## Priority tiers within the batch

**Tier 1 (reach out immediately):**
- Founder has posted about pipeline, sales, or hiring on LinkedIn in last 30 days
- Posted a sales or RevOps role on LinkedIn or YC Jobs
- Product is explicitly "for sales teams" or "for GTM" — they live in the problem

**Tier 2 (reach out this week):**
- B2B SaaS, technical product, founding team still selling
- No obvious sales infrastructure visible

**Tier 3 (nurture):**
- B2B but selling to large enterprise (longer sales cycle, different motion)
- Team is 2–3 people still building the product (not ready for outbound)

---

## Target count

Aim for 50 companies in the batch. From a typical YC batch of ~200 companies:
- ~60–70% are B2B
- ~40–50% are software/SaaS
- ~30–40% are ICP-qualified after filtering
- ~50 should be activatable within the first 30 days

---

## Tracking

Add each company to the tracking table in `context.md` as you research them.

| Company | Domain | Tier | Status | Notes |
|---------|--------|------|--------|-------|
| | | | | |

---

*Run `make daily` after adding companies to see follow-up status and pipeline activity.*
