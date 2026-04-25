---
title: "Notes from the Field: AI Tools Talk — A Tour of My Personal AI Stack"
slug: ai-application-sharing
description: "An abstract of a Chinese presentation deck covering cc-connect WeChat integration, Obsidian second brain, Harness Engineering, the 29-agent Synapse team, and a stock trading system."
lang: en
translationOf: ai-application-sharing
hasEnglish: true
pillar: multi-agent-case
priority: P3
publishDate: 2026-04-11
author: content_strategist
---

# Notes from the Field: AI Tools Talk — A Tour of My Personal AI Stack

This is an abstract of a Chinese-language presentation deck given at an internal AI application sharing session. It walks through my personal AI work-and-life stack across four pillars: personal productivity (cc-connect WeChat bridge, voice diary, Obsidian second brain), AI automation (Harness Engineering self-healing, Agent butler system, autonomous decision tiers), business projects (stock trading system, automated publish pipeline, team collaboration architecture), and AI team management (Graphify think tank, multi-agent coordination, knowledge management). The full Chinese version is presentation-style with diagrams; useful as a high-level introduction to the Synapse approach.

## Key Takeaways

- **cc-connect bridges WeChat to the AI stack**: receive messages and images, send notifications, trigger n8n webhooks. The mobile-side capture surface for an AI workflow that otherwise lives in a terminal.
- **Voice → Whisper → daily-record automation**: voice notes flow through Groq Whisper transcription into Obsidian markdown automatically. Zero-friction capture.
- **29 specialists across 6 teams**: Lysander (CEO) → Graphify (4) / Butler (7) / RD (5) / OBS (4) / Stock (5) / Content (4). Each team has a clear domain, a roster file, and a routing keyword set.
- **Three decision tiers (L1/L2/L3)**: routine ops execute autonomously; medium-risk plans get butler approval; high-risk or irreversible actions escalate to the human user.
- **Publishing pipeline**: Markdown → `harness-daily-publish.sh` → Astro build → n8n → WeChat draft, scheduled at 22:30/22:45 Dubai time. Fully automated.

## Why This Matters

The deck is the closest thing to a "Synapse executive summary" we publish — it shows the entire system at a glance rather than diving into any one component. If you've read individual case studies and wondered how everything fits together, this is the orientation map. The closing principle — "AI doesn't replace humans, it amplifies them; let AI handle the repetitive, focus humans on the creative" — captures the philosophy that runs through every Synapse design choice.

---

*This is an abstract. Read the full article in Chinese →* [AI 应用实战分享](/blog/ai-application-sharing)
