---
title: "Notes from the Field: How to Build a Second Brain with Claude Code (Slides)"
slug: ai-second-brain-presentation
description: "An abstract of a Chinese presentation deck on building a Software 2.0 second brain that auto-extracts decisions, concepts, problems, learnings, and projects from Claude Code conversations."
lang: en
translationOf: ai-second-brain-presentation
hasEnglish: true
pillar: multi-agent-case
priority: P3
publishDate: 2026-04-11
author: content_strategist
---

# Notes from the Field: How to Build a Second Brain with Claude Code (Slides)

This is an abstract of a Chinese-language presentation deck (13 slides) covering the Software 2.0 second-brain system. It frames the problem (every conversation contains valuable knowledge that vanishes), the architecture (extraction → classification → storage → continuous learning), the five-category intent classifier (decisions / concepts / problems / learnings / projects), the daily 23:00 automation loop, and the agent-butler decision tiers (L1/L2/L3). The deck pairs with the longer technical write-up "Building a Second Brain from Claude Code Conversations." Useful as a 10-minute orientation for someone new to the Synapse knowledge-management philosophy.

## Key Takeaways

- **Software 1.0 vs Software 2.0**: Software 1.0 relies on human-defined tags and manual links; Software 2.0 lets AI learn implicit rules from usage patterns and discover associations automatically.
- **100% conversation coverage** vs the 0.2% achieved by manual daily-record habits. The system pulls directly from Claude Code's `.jsonl` files, leaving nothing on the table.
- **Real numbers from one day (April 8)**: 526 high-value knowledge items extracted from 1,272 messages across 72 sessions. Scale is non-trivial.
- **Three-tier decision routing**: L1 routine operations auto-execute; L2 plans need butler approval; L3 complex/irreversible actions escalate to human.

## Why This Matters

Most "AI knowledge management" pitches miss the cycle: capture → classify → retrieve → *re-train*. The Software 2.0 framing matters because it inverts the assumption: instead of humans maintaining a tag taxonomy, the AI maintains it from observed patterns. The closing line of the deck — "every conversation is a learning event; every day makes the second brain smarter" — is the mission statement of the Synapse OBS layer. This deck is the cleanest 13-slide summary we have.

---

*This is an abstract. Read the full article in Chinese →* [如何用 AI 打造第二大脑 - Claude Code 实战分享](/blog/ai-second-brain-presentation)
