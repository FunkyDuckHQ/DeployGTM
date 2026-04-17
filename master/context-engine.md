# Context Engine — Operating Architecture

## What this is
DeployGTM runs on a context engine, not on chat history.

The repo is the canonical brain.
Google Drive is the raw intake and live working layer.
The transcript inbox is where rough material lands.
Project context files are where that material becomes usable.
Handoff files are what move work cleanly between ChatGPT, Claude, Gemini, or any other model.

## System design

### 1. Raw intake
Raw material lives in Google Drive:
- voice memo transcripts
- pasted call notes
- decks
- screenshots
- PDFs
- rough founder material

Do not over-organize raw material before it exists. Dump first, distill second.

### 2. Canonical project context
Every active project gets three files in the repo:
- `context.md` — current truth about the project
- `handoff.md` — model-agnostic summary for starting fresh anywhere
- `open-loops.md` — unresolved questions, blockers, next actions

### 3. Durable learning
Only promote a learning to `master/learnings.md` when it repeats across 3+ projects.
One-off observations stay inside the project.

### 4. Session discipline
Before closing any conversation that produced real work, compress it into four bullets:
- what changed
- what matters now
- open loops
- next move

That compression updates `handoff.md` or `open-loops.md`.

## Tool roles

### GitHub repo
Use for:
- canonical project context
- reusable playbooks
- outputs worth keeping
- templates
- repeatable learnings

### Google Drive
Use for:
- transcript inbox
- raw files
- working docs
- quick operating notes

### ChatGPT
Use as:
- control tower across projects
- prioritization layer
- packaging layer
- rewriting layer
- operator for turning raw material into briefs

### Claude
Use as:
- deep project worker
- long-doc synthesizer
- one-project reasoning engine

## File rules

### `context.md`
Should answer:
- what this project is
- objective
- current state
- key facts
- decisions already made
- what success looks like

### `handoff.md`
Should be safe to paste into any model cold.
Use this structure:
- Project
- Objective
- Current state
- What changed in the last session
- Decisions already made
- Open loops
- Next 3 actions
- Tone / writing constraints
- Start by helping with: [task]

### `open-loops.md`
Should only contain:
- waiting on
- need to decide
- need to build
- blocked by

## Standard workflow
1. Raw material lands in the Google Drive Transcript Inbox.
2. Matthew says in chat: "I uploaded one."
3. ChatGPT reads the latest section and returns:
   - one-line summary
   - what matters
   - risks / open questions
   - best next move
   - reusable language
4. Important outputs get promoted into the project files in GitHub.
5. Repeated patterns get promoted to master.

## Non-negotiables
- Do not rely on chat memory.
- Do not create admin work for the sake of admin work.
- Keep raw and canonical layers separate.
- Use the smallest amount of structure that preserves clarity.
- When in doubt, simplify.
