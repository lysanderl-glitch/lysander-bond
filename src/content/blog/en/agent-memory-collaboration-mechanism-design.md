---
title: "[EN] Agent记忆协作机制设计：让AI在下一次会话中'记得'上一次做了什么决策"
description: "通过产品管线信息归档实现跨会话知识传递，分析这种'外置记忆+委员会调用'模式的架构设计与适用场景"
date: 2026-04-28
publishDate: 2026-04-28T00:00:00.000Z
slug: agent-memory-collaboration-mechanism-design
lang: en
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

## TL;DR

- Cross-session amnesia in agents stems from the stateless nature of context windows
- Appending raw chat history inflates token costs 6× by session five
- RAG retrieval finds semantic similarity, not decision-relevant conclusions
- The fix: structured decision logs with role-based injection, not full history
- Write-time compression disciplines the architecture; read-time filtering controls noise

We run a product pipeline review process at Synapse where a committee of AI agents — playing product manager, tech lead, and market analyst — evaluate feature proposals across multiple sessions. Each session runs about 40 minutes and produces 12–18 decision records. The problem surfaced clearly at our fourth review meeting: the tech lead agent recommended an approach it had explicitly rejected two sessions earlier. It wasn't a model failure — it was an engineering reality. Every LLM call is stateless, and no retrieval shortcut changes that fundamental constraint.

Our first attempt was naive: append the previous session transcript to the system prompt. By session five, token cost had grown to roughly 6× session one's baseline. Worse, models reading 3,000-word histories conflated rejected options with accepted conclusions about 30% of the time in our tests. We then tried RAG, vectorizing conversation history and retrieving semantically similar chunks. That failed more subtly. Semantic similarity does not equal decision relevance. A critical tech lead judgment — "this approach's latency is unacceptable" — ranked outside the top-5 results when the current session's question was about caching strategy. We retrieved plenty about caching. We retrieved nothing useful.

The real problem was that we wanted **decision continuity**, not content retrieval. Those require entirely different storage and recall mechanisms. We built a pipeline memory archive where a dedicated archiving agent compresses each session into structured decision logs after the session ends. Every entry enforces three fields: `decision`, `rationale` (capped at 50 words), and `owner` (which role made the call), plus a `status` field marking entries as `closed`, `open`, or `revisable`. At the start of the next session, `memory_injector.py` filters the archive by `owner` and injects only role-relevant entries into each agent's system prompt — typically under 400 tokens, but with extremely high signal-to-noise ratio. One non-obvious design choice: `status: open` entries are deliberately excluded from injection. Pending decisions cause agents to prematurely resolve them rather than focus on the current agenda.

## Key Takeaways

- If you run multi-agent review workflows, add a dedicated archiving step after each session — never let the generating agent archive its own output
- If you're tempted to use RAG for agent memory, ask first whether you need content retrieval or decision continuity — they are not the same problem
- If token cost is growing across sessions, the fix is write-time compression with a strict schema, not better retrieval
- If you inject historical context, filter by role — role-irrelevant history is noise, not grounding
- If you have unresolved items, manage them separately at the coordination layer rather than embedding them in individual agent prompts

## Read the Full Article (Chinese)

This is an abstract. The full technical walkthrough — including the complete YAML schema, annotated pseudocode, and the specific failure modes we encountered — is in Chinese.
