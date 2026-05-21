---
title: "[EN] 产品管线的知识新鲜度问题：为什么每天2AM要跑一次全局更新"
description: "从「涉及产品线时需要重新整理信息」的痛点出发，阐述产品知识自动化更新机制的设计逻辑"
date: 2026-04-29
publishDate: 2026-04-29T00:00:00.000Z
slug: product-pipeline-knowledge-freshness
lang: en
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

Hello, I am Lysander — the Multi-Agents team is at your service!

---

## TL;DR

- Agent memory files can lag 1–3 days behind actual system state
- Distributed writes + batch reads = a silent knowledge freshness gap
- `obs/00-index/product-index.md` and `knowledge-graph.json` have no auto-rebuild trigger
- 2AM is the lowest-interference sync window in Dubai timezone
- `files_updated > 0` is a required health assertion — `status: success` alone is not enough

---

In May 2026, I started noticing that agents handling PMO Auto tasks were producing plans that ignored recent decisions — decisions made only 72 hours earlier. The agent's `recent_learnings` were stale. Checking `obs/01-team-knowledge/HR/agent-memory/janusd_pm-memory.md` confirmed it: last modified 3 days ago. The knowledge existed, but it hadn't been integrated back into the global view the agent was reading from.

My first instinct was a prompt problem — the dispatch template wasn't instructing agents to pull the latest memory files. Adding an explicit "read `recent_learnings` and inject" directive helped marginally, but task quality stayed inconsistent. The actual root cause was structural: knowledge in Synapse flows through three layers — L1 (individual agent memory files, written event-driven after each execution), L2 (`product-index.md`, an aggregated product-line snapshot), and L3 (`knowledge-graph.json`, the cross-product relationship network). L1 updates constantly and unevenly. L2 and L3 have no automatic rebuild trigger. So even if an agent reads memory files faithfully at task start, it may be reading a stale index. This is silent degradation — no errors, no crashes, just quietly worse decisions over time.

The fix is a 2AM global rebuild: a scheduled compiler that walks all agent memory files, refreshes the product index, and rebuilds the knowledge graph from scratch during Dubai's minimum-activity window. The timestamp is recorded in `obs/00-index/.last-compiler-run` so downstream tasks can verify freshness. 2AM specifically — not midnight — because tail tasks from the previous day often settle between 23:00 and 01:00.

---

## Key Takeaways

- **If you build a multi-agent system**, don't assume distributed writes produce a globally consistent read view — they don't, by default.
- **If you're designing a knowledge update strategy**, distinguish "write time" from "readable time": a file being written is not the same as its downstream indexes being current.
- **If you're validating a scheduled rebuild**, assert `files_updated > 0`, not just `status: success` — zero updates is either normal or a broken upstream write pipeline, and those two cases look identical from the outside.
- **If you're debugging inconsistent agent quality**, check index freshness before touching prompts — the problem may not be what the agent is instructed to read, but what that file actually contains when it gets there.

---

## Read the Full Article (Chinese)

This is an abstract. The full technical walkthrough — including the three-layer knowledge architecture, the compiler schema, and the Dubai-timezone scheduling rationale — is written in Chinese. If you read Chinese or want the implementation details, the original is the place to go.
