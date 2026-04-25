---
title: "Notes from the Field: When Your AI Quietly Broadcasts to the Whole Company"
slug: ai-automation-slack-channel-boundary-violation
description: "An abstract of a Chinese incident report on discovering an AI scheduled task had been posting daily intel digests to #general (287 people) for three weeks, and the four governance rules we instituted afterward."
lang: en
translationOf: ai-automation-slack-channel-boundary-violation
hasEnglish: true
pillar: multi-agent-case
priority: P3
publishDate: 2026-04-22
author: content_strategist
keywords:
  - "AI-safety"
  - "AI-engineering"
  - "Synapse"
---

# Notes from the Field: When Your AI Quietly Broadcasts to the Whole Company

This is an abstract of a Chinese-language Synapse incident report. While reviewing scheduled-task configs, I opened the log for `daily-intel-digest` and froze on line three: `channel: #general, recipients: 287`. The task had been posting AI-generated industry digests to a 287-person company channel for three weeks. No one complained, but no one should have been receiving them. The full Chinese article unpacks the three layered defects that produced this — a copy-pasted webhook URL, an over-broad OAuth scope, and an LLM prompt that confidently picked `#general` as "the most relevant channel" — plus the four-rule governance framework we now apply to every AI outbound action. Recommended for anyone integrating AI agents with Slack, email, or any messaging system that has a "send to public" capability.

## Key Takeaways

- **Default private, explicitly public**: every new AI automation target starts as a private channel or DM. Broadening recipients requires an explicit config change and approval, never an LLM decision.
- **Separate drafting from sending**: the AI generates content; a separate, minimum-privilege runner performs the actual send. Prompt injection cannot escalate what it never had.
- **Treat audience size as a first-class safety signal**: any target above N recipients triggers human review, the same way an outbound payment above a threshold would.
- **Audit every outbound action**: periodic review of `recipients` and `target` fields catches drift earlier than any alerting rule. We caught two more near-misses this way (an internal financial summary almost going to a customer list; staging data nearly pushed to a production dashboard).

## Why This Matters

Traditional scripts have a static blast radius — recipients are hardcoded and reviewable. AI agents have a *dynamic* blast radius: they choose targets at runtime based on prompts. A friendly-sounding prompt ("pick the most relevant channel") plus an over-permissioned token can expand that radius from "test channel" to "everyone in the company" without any code change. The Synapse Harness layer now requires three metadata fields on every automation task — `max_recipients`, `allowed_targets`, `approval_tier` — and the four rules in the Chinese article have become company-wide policy. The most dangerous bug in AI engineering isn't a crash; it's the system working "correctly" against the wrong semantics.

---

*This is an abstract. Read the full article in Chinese →* [AI 自动化任务悄悄发消息到公司群](/blog/ai-automation-slack-channel-boundary-violation)
