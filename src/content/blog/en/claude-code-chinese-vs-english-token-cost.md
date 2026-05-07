---
title: "Chinese Token Optimization in Multi-Agent Systems"
description: "Chinese Token Optimization in Multi-Agent Systems"
date: 2026-05-07
publishDate: 2026-05-07T00:00:00.000Z
slug: claude-code-chinese-vs-english-token-cost
lang: en
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

## TL;DR
- Chinese text consumes ~1.7x more tokens than English for identical meaning
- Translation middleware cuts costs by 40%+ in long task scenarios
- Claude Code system prompts with high Chinese ratio need optimization focus
- Translation layer must sit between Agents, not at user interaction layer
- Structured instructions stay in English; content layers get selective translation

## The Problem

Last Friday, Synapse's multi-Agent scheduling system ran a batch of long tasks and the billing number made me stare at my screen for 3 seconds—68% over budget. We built an automated testing Agent pipeline with Claude Code: 20 tasks averaging 150 conversation turns each. The final token consumption was 70% higher than our English-only benchmark.

Where did this 68% excess come from? We initially suspected verbose prompt engineering. But after careful auditing, the truth emerged: system prompts, Agent collaboration instructions, and task descriptions were 90%+ Chinese-written. Claude's tokenization encodes Chinese significantly less efficiently than English, causing identical semantic content to consume substantially more tokens.

This isn't a simple fix. Our team works in Chinese for task descriptions, business rules, and test cases. Simply converting everything to English would spike collaboration costs—an unacceptable trade-off. The real challenge is balancing token efficiency against team coordination efficiency.

## The Solution

I designed a translation middleware architecture that intercepts Agent-to-Agent communication rather than user interactions. This preserves our team's Chinese collaboration environment while optimizing token consumption at critical points.

In Synapse's production deployment, Agents split into two categories: user-facing Agents maintain Chinese for smooth team collaboration, while task-execution Agents receive translated instructions through the middleware layer. The `TranslationGateway` class handles this translation, converting Chinese prompts to English before Claude processes them. With English system prompts around 30 tokens versus Chinese at ~52 tokens for the same meaning (1.73x ratio), the savings compound across hundreds of interactions.

The 40%+ cost reduction came from targeting the highest-frequency communication path: Agent internals rather than user interfaces.

## Key Takeaways

- If you run multi-Agent pipelines with international teams, deploy translation at the communication layer between Agents, not at user interaction points.
- If you process high-volume task queues with repeated prompts, convert Agent-to-Agent instructions to English while keeping user interfaces in the team's native language.
- If you notice token costs exceeding estimates by 50%+, audit your prompt language distribution—Chinese-heavy prompts compound inefficiencies.
- If you want consistent token optimization across models, keep structured system instructions in English regardless of content language.
- If you maintain team collaboration efficiency as a priority, translate only at machine-to-machine boundaries, preserving human-facing communication.

## Read the Full Article (Chinese)

This is an abstract. The full technical walkthrough with code examples is available in the original Chinese article.
