# Playbook — Inbox Warmup & Deliverability

Cold outreach is only cold if it gets delivered. A freshly-configured sending domain with zero reputation will land in spam, and nothing above the filter matters. This is the playbook for standing up a clean sending infrastructure before we touch a target account.

## TL;DR checklist

- [ ] Dedicated outbound domain separate from primary (e.g. `peregrineglobal.com` sends, `peregrinespace.com` stays protected)
- [ ] SPF, DKIM, DMARC published and passing
- [ ] Custom tracking domain set up if using any tracker (prefer no trackers on cold)
- [ ] Inbox warmup running for 2–4 weeks before first real send
- [ ] Daily send volume ramped incrementally (see table below)
- [ ] Reply rate > send rate during warmup
- [ ] First cold send only after warmup mailbox shows healthy placement in seed tests

## Why a separate sending domain

If cold sends go out on your primary domain and a complaint spike happens, every transactional email and every real customer conversation degrades with it. A separate domain isolates risk. Rule: never warm a cold-send motion on the domain that carries your customer communications.

Pattern:
- **Primary (protected):** `clientname.com` — used for product, support, customer replies.
- **Outbound (sacrificial):** `clientname.co`, `clientnamehq.com`, `getclientname.com`. Two-pronged redirect back to primary site.
- SPF/DKIM on the outbound domain sign cold sends. If it ever burns, you rotate it, not your business.

## DNS records — non-negotiable

Before a single cold email is sent:

1. **SPF** — one `TXT` record on the outbound domain listing authorized senders (e.g. Google Workspace, SendGrid, the provider in use). Only one SPF record per domain. Merge if you have multiples — more than one and everything fails silently.
2. **DKIM** — signing keys from the sending provider, published as `TXT` under `selector._domainkey.domain.com`.
3. **DMARC** — start with `p=none; rua=mailto:dmarc@clientname.com` so you get reports without breaking delivery. Once you see clean pass rates for 2+ weeks, move to `p=quarantine`. Don't skip to `p=reject` until you have reports showing no legitimate failures.

Validate using `dig TXT` and a DMARC validator before trusting it. "I think I set it up" is not the same as "it passes."

## Warmup protocol

Warmup means sending low volumes of _real-looking_ emails to seed mailboxes (or a warmup service's network) that reply, open, and move mail out of spam. The point is to build a reputation signal: this sender sends mail people want.

### Volume ramp

Start low. The numbers matter because ramp speed is itself a signal:

| Week | Daily sends per mailbox | Notes |
|------|-------------------------|-------|
| 1    | 5–10                    | Warmup only, no real prospects |
| 2    | 15–25                   | Warmup only |
| 3    | 30–50                   | Begin real cold sends, mixed with warmup |
| 4    | 50–80                   | Real cold sends dominate; warmup continues at 10–20/day |
| 5+   | 80–150 max per mailbox  | Never blast past ~150/day from one mailbox |

If volume needs to exceed ~150/day for the motion, add mailboxes on the same domain (john@, jane@, matt@) rather than blasting from one. Rotate load across them.

### Warmup service or manual?

Warmup services (Mailwarm, Warmup Inbox, Instantly warmup, Smartlead warmup) automate this. They are fine. Do not trust them to do the entire job — still run manual seed tests weekly (send to your own Gmail/Outlook/Yahoo and verify inbox placement).

Manual warmup also works: a small group of real humans replying to a handful of real sender messages daily for 2–3 weeks. More defensible, but higher ops cost.

## Content rules during warmup and first sends

The warmup period teaches filters what you send looks like. Do not warm up with emoji-heavy marketing blasts and then switch to text-only cold — the filters have already categorized you.

During warmup, send:
- Short plain-text messages (the same format cold sends will use)
- Minimal links (one at most)
- No tracking pixels
- No HTML signatures with logos, banners, unsubscribe-style boilerplate
- Varied subject lines — never the same subject to 50 people

During first real sends:
- Same plain-text format
- No open tracking. Open tracking costs ~30% of inbox placement on some providers. Skip it.
- No link tracking unless the link is required; use the raw URL.
- Under 100 words. Subject under 6 words. (Our standard — see the outreach generator.)

## Seed testing

Before declaring warmup done, run a seed test:

1. Send your actual first-touch template to ~10 mailboxes you control: Gmail personal, Gmail workspace, Outlook personal, Outlook work, Yahoo, iCloud.
2. Check each inbox — primary? Promotions? Spam?
3. If more than 1 lands in spam, you are not ready. Extend warmup a week and fix the template (remove unsubscribe language, shorten, strip links).

Tools like GlockApps do this at scale. Useful for retainer clients with higher stakes.

## Daily reality checks once live

- **Reply rate dropping below 5% while volume is steady** → deliverability problem, not copy problem. Audit placement before iterating on message.
- **Bounce rate above 3%** → list quality issue. Pause and re-verify the list. Sustained bounces above 3% will tank your sender reputation within days.
- **Spam complaints above 0.1%** → stop the sequence immediately. Fix the list or the opener. One complaint per 1000 sends is the ceiling before providers start throttling you.

## When to rotate or rebuild

- Sustained placement degradation over 2 weeks → rotate to a second outbound domain that has been warming in parallel. Always keep a backup warming.
- Bounce spike from a single import → pause, clean the list, do not unpause until placement recovers.
- Provider blacklist hit (Spamhaus, Barracuda) → halt, diagnose, delist, do not resume on the affected domain.

## Deliverables for a retainer client

By end of Week 1 of a Pipeline Engine Retainer, the client should have:

1. Outbound domain registered, redirecting to primary
2. SPF/DKIM/DMARC passing on the outbound domain
3. 1–3 sending mailboxes created on the outbound domain
4. Warmup service running on each mailbox
5. Seed-test schedule on the calendar (weekly during warmup, then monthly)
6. A documented ramp plan with the volume-per-week target above

Only after that does the first cold send go out. This is the bottleneck to hit every time, and it is faster to get right than to fix once it's broken.

## Related

- `master/playbooks/enrichment.md` — how we build the list that gets warmed-up mailboxes send to
- `master/playbooks/outreach-ops.md` — cadence, reply-handling, and sequence ops
- `projects/deploygtm-own/scripts/generate_outreach.py` — message format expectations this playbook assumes
