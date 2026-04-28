---
title: "[EN] AI Team Decision Boundaries: When Should You Let the Agent Decide?"
description: "From 'ask me every 5 minutes' to 'professional decisions by professionals' — how we evolved Claude Code delegation in a real engineering team"
date: 2026-04-27
lang: en
tags:
  - AI Engineering
  - Synapse
  - Problem Log
author: lysander
---

## TL;DR

- Over-restricting agents creates as many problems as under-restricting them
- Key framework: classify decisions by reversibility × impact scope
- Boundary declarations outperform permission restrictions for agent autonomy
- Replacing approval gates with decision logs reduced interruptions ~60%
- Building the delegation framework forced us to make implicit engineering norms explicit

## The Problem

Three months ago, our Claude Code sessions looked like this: every few minutes, someone would say "it stopped again asking if it can continue." The agent would write mid-task, pause for confirmation, we'd confirm, it would write a few more lines, pause again. We'd paid for a highly capable agent but were getting the efficiency of a junior developer who needs a signature every 5 minutes.

The root cause wasn't the AI. It was that we hadn't thought clearly about which decisions belonged to humans and which could be delegated.

We went through two failure modes. First: too much autonomy. The agent refactored a shared library interface, downstream services broke, and nobody caught it until integration — the code was correct, but the blast radius exceeded the codebase. Then we over-corrected: added confirmation checkpoints everywhere and returned to the constant-pause pattern.

## The Classification Framework

Two months of iteration produced a framework based on two dimensions: **reversibility** and **impact scope**.

<pre><code class="language-yaml"># Decision classification in task briefing
decision_boundaries:
  auto_approve:
    - function naming and comments
    - unit test structure
    - code formatting
  human_required:
    - database schema changes
    - breaking API interface changes
    - major version dependency upgrades
  async_log_and_proceed:
    - medium-risk refactors within module scope
    - new internal utility functions
    - performance optimizations with no interface change
</code></pre>

High reversibility + small scope → delegate fully. Low reversibility + large scope → mandatory human approval. The middle ground — medium reversibility, uncertain scope — gets an "impact statement" from the agent before proceeding. Not "can I continue?" but "I'm about to do X, which will affect modules Y and Z."

<div class="callout callout-insight"><p>If you want to reduce agent interruptions, stop asking "how much can I trust the AI?" and start asking "which specific decisions are low-risk enough to delegate?" The answer is more than you think — if you've defined the boundaries explicitly.</p></div>

## Three Practices That Actually Worked

**Explicit task boundary declarations.** We add a "do not auto-decide" list to every task description: don't modify anything under `config/production/`, don't delete code blocks over 50 lines, don't add external dependencies. Giving Claude clear boundaries made it *more* autonomous within those bounds — it stopped guessing at the edges.

**Separate confirmation needs from information needs.** Agent pauses fall into two categories: "approve this action" vs. "I need information X to continue." We require the agent to declare which type before stopping, and information requests must specify exactly what's needed and why. This reduced invalid interruption requests by approximately 60%.

**Decision logs instead of approval gates.** For medium-risk decisions, the agent proceeds, logs the decision rationale, and humans review asynchronously. The log includes: action taken, reasoning, expected impact, actual impact (filled in after). This keeps the agent moving and gives humans pattern visibility across decisions — instead of drowning in individual approvals.

## Key Takeaways

<ol>
<li>If your agent keeps asking permission, the bottleneck is usually unclear boundaries, not the AI's capability.</li>
<li>If you're defining delegation scope, start with reversibility — that single dimension eliminates most ambiguous cases.</li>
<li>If you build decision logs, you'll discover something useful: the pattern of what agents decide reveals your implicit engineering norms. Document them.</li>
</ol>

## Read the Full Article (Chinese)

This is an abstract. The full technical walkthrough — including the two-month iteration history, specific CLAUDE.md constraint syntax, and decision log format — is in Chinese at [lysander.bond/blog/ai-agent-decision-boundary-delegation](https://lysander.bond/blog/ai-agent-decision-boundary-delegation).
