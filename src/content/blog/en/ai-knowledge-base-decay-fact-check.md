---
title: "[EN] Why Your AI Knowledge Base Decays: Lessons from CLAUDE.md Fact Accuracy Failures"
description: "The moment I discovered all the agent count data was wrong — how config file decay makes every AI analysis rest on sand"
date: 2026-04-27
lang: en
tags:
  - AI Engineering
  - Synapse
  - Problem Log
author: lysander
---

## TL;DR

- Found "12 agents deployed" in an AI-generated report — actual count was 7
- CLAUDE.md had not been updated through multiple architecture changes over 4 months
- AI analysis built on outdated context produces confident-sounding wrong conclusions
- Fix: separate stable facts from dynamic state, bind updates to change events not calendar reviews
- Using AI to describe its own context against reality is a low-cost accuracy probe

## The Problem

Three weeks ago, reviewing an AI-generated system analysis report, I noticed a detail that made me stop: "the system currently has 12 specialized agents deployed." I stared at that number — the actual count was 7. Nearly double.

The problem was in CLAUDE.md. This is the context file we give to AI, describing system architecture, agent responsibilities, data flows, and other baseline information. That "12 agents" figure was written four months earlier when it was accurate. We'd done a round of consolidation and cleanup since then, but nobody remembered to update this file. The AI used this outdated "fact," confidently analyzed the situation, and every inference, recommendation, and optimization direction was built on a false premise.

## How Decay Happens

We ran a systematic audit — listed every quantifiable or verifiable claim in CLAUDE.md and checked each against reality. The results were uncomfortable: agent count wrong, a module's latency data was a six-month-old benchmark, two deprecated interfaces still labeled as "core dependencies," even the team size description was outdated.

The root cause is a hidden trust mechanism: we tend to believe "things that have been written down." Completing CLAUDE.md creates a sense of closure — "that's done, the AI can use it now." But "writing good documentation" and "maintaining documentation accuracy" are completely different tasks. The first is one-time work; the second is ongoing operational burden — and the second is almost always neglected.

<div class="callout callout-insight"><p>If you maintain AI context files, treat "are these facts still true?" as a recurring engineering obligation, not a one-time documentation task. The feedback delay on stale context is long — you won't know it's wrong until the AI's confident analysis leads you somewhere wrong.</p></div>

## The Structural Fix

<pre><code class="language-yaml"># CLAUDE.md fact classification pattern
stable_facts:
  - System design philosophy (rarely changes)
  - Core architectural principles
  - Team decision-making framework

dynamic_state:
  - agent_count: 7  # last_verified: 2026-04-27, source: organization.yaml
  - p95_latency_ms: 340  # last_verified: 2026-04-15, benchmark: load-test-0415
  - active_integrations: [slack, notion, n8n]  # last_verified: 2026-04-27
</code></pre>

Three concrete changes we made:

**Separate stable from dynamic.** Stable facts (design philosophy, architectural principles) change rarely and need infrequent review. Dynamic state (current agent count, performance metrics, active integrations) needs timestamps and source citations — or ideally, references to authoritative source files rather than hard-coded values.

**Bind updates to change events, not calendar reviews.** Adding "update CLAUDE.md" to the system change checklist is more reliable than scheduled reviews. Calendar-based reviews get skipped; event-bound updates happen because the system change is already in progress.

**Use AI as an accuracy probe.** Occasionally ask the AI to describe the system based on CLAUDE.md, then compare with reality. Discrepancies reveal exactly what needs correction — a low-cost verification technique that doesn't require building new tooling.

## Key Takeaways

<ol>
<li>If you use CLAUDE.md or equivalent context files, audit them against reality at least once — you'll likely find multiple stale facts you didn't know existed.</li>
<li>If you write numbers or status descriptions in AI context, add a timestamp — any sentence containing "currently X" should include when that was measured.</li>
<li>If you rely on AI analysis for system decisions, the quality ceiling is the accuracy of its context. Garbage in, confident garbage out.</li>
</ol>

## Read the Full Article (Chinese)

This is an abstract. The full technical walkthrough — including the audit process, specific CLAUDE.md restructuring format, and the change-event binding implementation — is in Chinese at [lysander.bond/blog/ai-knowledge-base-decay-fact-check](https://lysander.bond/blog/ai-knowledge-base-decay-fact-check).
