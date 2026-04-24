# Matthew — Working Conditions

*This file is read at the start of every Claude Code session. It tells Claude how to work with you — not around you.*

## Status
**ACTIVE** — account matrix system built and live; deploygtm own matrix verified; peregrine matrix 14/14 ready.

See `master/progress.md` for full build log. See `projects/deploygtm-own/data/deploygtm_accounts.json` for current outbound targets.

Immediate next action: verify signals in deploygtm matrix → `make verify-signals CLIENT=deploygtm` → update VERIFY fields from Crunchbase/LinkedIn → run `make batch-outreach CLIENT=deploygtm`

---

## Working hours / availability
Eastern time (Atlanta metro, Cumming GA). Remote.

Work happens in focused sessions — not always sequential. Claude should be ready to pick up mid-workflow from a cold start each session, because sessions do not carry forward.

No timezone constraints for generating content or running offline scripts. For anything that sends outreach, creates HubSpot records, or touches external APIs — only do it during an active session where Matthew is present and confirmed.

---

## Communication style
Short. Direct. Lead with what changed or what needs to happen — not what you did or why.

**Response format:**
- One sentence status, then action items if any
- Bullet points for lists of things; prose for reasoning
- Code blocks for commands
- No headers for short answers

**Things that never belong in a response:**
- "Great question!" or any affirmation opener
- Lengthy preambles before the actual answer
- Explaining what you're about to do before doing it
- Re-summarizing what was just discussed
- "I hope this helps" or similar closers
- Asking for clarification when the task is clear from context

When the task is ambiguous, state the interpretation and proceed — do not ask unless a wrong assumption would cause significant rework.

---

## Decision authority

**Claude can decide without asking:**
- Code edits, new scripts, file creation/deletion within the project
- Generating outreach drafts (these are drafts, not sends)
- Running `make test`, `make audit`, `make verify-signals`, any offline command
- Committing and pushing to the current feature branch
- Updating documentation files (CLAUDE.md, progress.md, this file)
- Creating new matrix accounts, playbooks, brain files
- Reading any file in the repo
- Scaffolding new client projects from the template

**Always confirm before:**
- Writing to a production HubSpot (any `--push-to-hubspot` flag)
- Spending API credits on a large batch run (>10 accounts at once)
- Pushing to `main` branch
- Creating a pull request
- Sending any actual outreach or email
- Deleting data files (`data/`, `output/`, `projects/*/data/`)
- Enrolling contacts in HubSpot sequences

---

## Things that waste time
- Asking whether to proceed when the task has been explicitly stated
- Over-explaining decisions — state the decision, then act
- Writing multi-paragraph responses to simple questions
- Using the word "strategy," "leverage," "synergy," "exciting," or "innovative" anywhere
- Adding error handling for scenarios that cannot happen
- Commenting code that explains what the code does (the code already does that)
- Building abstractions before there are 3+ real use cases
- Creating placeholder files, README files, or documentation unless explicitly asked
- Summarizing what was just done at the end of every response — just say what's next

---

## Things that are always true

**Code:**
- Never hard-code API keys. Always `.env`. If a key is missing, fail loudly at startup.
- Never write to a production CRM without explicit confirmation in the current session.
- Every enrichment record includes confidence level and source.
- Offline tests always pass before a commit lands. `make test` is the gate.
- The branch is `claude/read-master-files-wWR6f`. Push there, not to main.

**Outreach:**
- Always leads with the verifiable signal, never with a product description.
- Never sounds like AI. No "leveraging," no "I hope this email finds you well."
- Under 75 words for first touch. Subject under 6 words.
- The close is "20 minutes?" or "Worth a call?" — nothing else.
- When in doubt about ICP fit: disqualify.

**Client work:**
- Peregrine is the proof-point. Quality of that artifact matters above everything.
- Every client project stays in `projects/<client>/`. Nothing leaks across clients.
- Learnings only promote to `master/learnings.md` after 3+ validated instances.

**System:**
- Every workflow answers: trigger → action → data write-back → success metric.
- Never build an isolated automation. Everything closes the loop.
- The seven-layer build order (field-manual.md) is the architecture standard.

---

## Current focus / priority
DeployGTM's own outbound is the immediate priority. Goal: 2+ Signal Audits sold in 30 days.

1. Verify deploygtm matrix signals → update 6 named accounts (Loops, Orb, Mintlify, Plain, Campsite, Koala) from Crunchbase/LinkedIn
2. Run batch outreach → generate variants for all verified tier-1 accounts
3. Populate Segment C/D/E archetype slots as LinkedIn signals fire
4. Send first outreach to tier-1 accounts
5. Peregrine follow-up is live → waiting on Tyler's reply

Top-of-mind: do not over-build tooling when the constraint is unverified signals and unsent outreach. Ship the outreach before adding another feature.

---

## Projects in flight

| Project | Status | Next action |
|---------|--------|-------------|
| deploygtm-own | Matrix built; signals unverified | Verify 6 accounts → run batch-outreach |
| peregrine-space | Outreach ready; proof-point complete | Send message to Tyler; update status when reply comes |
| mindra | 30/60/90 plan built | Present to Deniz |
| fibinaci | Response posture built | Send warm follow-up: NDA + demo. Don't start work until economics are clear. |
| sybill | Prep questions built | Show up curious, reference prior product use |
| rex | Prep notes built | Light discovery, 30-45 min, just detect signal |
| terzo | Scheduling note drafted | Send when Brodie context is clear |

*Update this table when project status changes. Do not let it go stale.*
