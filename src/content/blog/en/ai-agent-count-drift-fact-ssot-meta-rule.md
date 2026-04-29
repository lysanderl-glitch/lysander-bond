---
title: "When Your AI Team Has 3 Different Headcounts: Fixing Number Drift with Fact-SSOT"
description: "From a real incident where 44/46/50 coexisted as the 'correct' agent count — root cause analysis of number drift in multi-file AI systems and the Fact-SSOT meta-rule solution"
date: 2026-04-26
publishDate: 2026-04-26T00:00:00.000Z
slug: ai-agent-count-drift-fact-ssot-meta-rule
lang: en
tags:
  - AI Engineering
  - Synapse
  - Problem Log
author: lysander
---

## TL;DR

- Our system had 3 simultaneous "correct" agent counts: 44, 46, and 50 across different files
- AI silently chose one number to proceed — no error, just unpredictable drift
- Root cause: facts spread across multiple files with no single authority
- Fix: Fact-SSOT meta-rule — designate one file as truth, all others reference it
- Implementation took half a day; 0 new drift incidents in 2 weeks after

## The Problem

Last week our AI agent system had three simultaneous "correct" answers: 44, 46, and 50 — all claiming to be the current team member count, each from a different document. Nobody intentionally created this inconsistency. Each update was well-intentioned, each had a reason, but the end result was a system that had lost consensus on its own basic facts.

When an AI task pulled all three files into the same context window, it didn't report a conflict. It quietly picked one number and continued. We reproduced it several times — sometimes 46, sometimes 50, depending on document order in context. That's the hallmark of number drift: not a one-time error, but continuous, unpredictable deviation.

## Why This Is Hard to Catch

We initially assumed AI would flag contradictions. It didn't. LLMs process contradictory facts using internal weighting, not explicit conflict detection. The more dangerous failure mode is silent selection — the AI appears to function correctly while operating on a false premise.

The structural cause: AI knowledge bases encourage writing complete context in each file, which means the same fact gets restated multiple times. Each restatement is a drift opportunity. Unlike human readers who pause when numbers disagree, AI quietly resolves contradictions and keeps moving.

<div class="callout callout-insight"><p>If you build AI systems that read multiple files, treat fact consistency as an engineering problem — not a documentation problem. Documentation relies on memory; engineering relies on constraints.</p></div>

## The Fact-SSOT Meta-Rule

We introduced three rules:

<pre><code class="language-yaml"># fact-registry.yaml — the ONLY place to update team headcount
team:
  agent_count: 58  # SSOT: all other files must reference this value
  last_updated: 2026-04-26
  source_file: agent-CEO/config/organization.yaml
</code></pre>

**Rule 1 — Fact isolation.** Extract all quantitative facts that change over time (headcount, version numbers, thresholds) from narrative documents. Store them in a dedicated Fact Registry — pure key-value, no prose. All other documents reference this registry rather than hard-coding values.

**Rule 2 — Narrow write permissions.** The Fact Registry has explicit write rules: who can modify it, which downstream documents need sync notification, and what change records must be kept. A version-controlled YAML file plus Git commit conventions is sufficient — the goal is making "modifying a fact" feel deliberate, not incidental.

**Rule 3 — Conflict detection in AI instructions.** Add a meta-instruction to the system prompt: when the AI detects inconsistent quantitative descriptions of the same entity in context, it must stop, output a conflict report, and wait for human confirmation. This turns "silent selection" into "explicit error."

## Key Takeaways

<ol>
<li>If you maintain multi-file AI knowledge bases, treat "which file is the authority?" as a first-class architectural question — answer it before you need it.</li>
<li>If you find number drift, spend 20 minutes fixing the architecture, not just the numbers — patching values without a SSOT means they'll drift again.</li>
<li>If your AI seems to "work" despite inconsistent inputs, verify it isn't silently choosing — reproduce with different document orderings to check stability.</li>
</ol>

## Read the Full Article (Chinese)

This is an abstract. The full technical walkthrough — including the step-by-step implementation, conflict detection prompt engineering, and two-week incident log — is in Chinese at [lysander.bond/blog/ai-agent-count-drift-fact-ssot-meta-rule](https://lysander.bond/blog/ai-agent-count-drift-fact-ssot-meta-rule).
