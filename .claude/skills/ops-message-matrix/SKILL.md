---
name: ops-message-matrix
trigger: message matrix, write copy, outreach copy, campaign copy, Octave playbook
---

## When To Use

Use this skill when turning ICP, personas, value props, and signals into high-quality message variants.

## Steps

1. Load persona, playbook, value prop, signal definitions, and voice traits.
2. Identify the account or segment route: automated test, manual sales review, nurture, or hold.
3. Define allowed claims and blocked claims.
4. Map pain hypothesis, signal basis, proof point, objection, CTA, and channel.
5. Generate matrix rows before drafting copy.
6. Draft channel-specific variants from approved rows.
7. Mark every claim with proof or review status.
8. Save the matrix before saving individual copy.
9. If Octave is available, use it as a ContentAdapter implementation only.

## Output

Write to:

- `1_brand/message-matrices/{client}-{segment}-{persona}.md`
- `2_acquisition/outbound/{client}-{campaign}-drafts.md`

## Epilogue

After each message batch, capture:

- which signal basis produced the strongest copy
- which objections require better proof
- which claims need customer validation
- whether the account should route to a human instead of automation

## Source Notes

Connects DeployGTM ContentAdapter architecture with the Growth Engine creative angle matrix and Josh Whitfield's institutional-knowledge moat principle.
