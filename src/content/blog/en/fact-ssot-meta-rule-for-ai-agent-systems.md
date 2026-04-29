---
title: "Fact-SSOT: The Meta-Rule for Eliminating Number Drift in AI Agent Systems"
description: "When the same AI system had agent counts of 44, 46, and 50 in three files simultaneously — root cause analysis and the Fact-SSOT meta-rule as a systematic fix"
date: 2026-04-25
publishDate: 2026-04-25T00:00:00.000Z
slug: fact-ssot-meta-rule-for-ai-agent-systems
lang: en
tags:
  - AI Engineering
  - Synapse
  - Meta-Rules
author: lysander
---

## TL;DR

- Discovered 44/46/50 simultaneously as "correct" agent counts in CLAUDE.md, team docs, and Notion
- All three numbers written by me, all independently updated, all became contradictory
- Root cause: same fact stored in multiple locations with no single authority (SSOT)
- Fix: Fact-SSOT meta-rule — designate authority file, reference don't duplicate, make modifications deliberate
- 20 minutes to fix existing drift; 0 new drift events across 2 subsequent team changes

## The Problem

Last week I reviewed our documentation and found an embarrassing problem: the same AI collaboration system had agent team member counts of 44, 46, and 50 — in three different files, all claiming to be accurate.

All three numbers were written by me.

This is textbook number drift (Number Drift): one fact, multiple copies in a system, each independently updated, eventually contradicting each other. Worse, this type of contradiction usually triggers no errors. The system runs normally — until someone puts all the files side by side and notices the problem.

## Root Cause: Copies Are the Problem

Tracing each number's origin took about an hour. 44 was a stale value left from a configuration rewrite that didn't sync to other files. 46 was the actual count during a documentation cleanup. 50 was a "planned target" from an external demo that somehow got written as current status.

<pre><code class="language-yaml"># The problem: same fact in 3 places
# CLAUDE.md
team_description: "Multi-Agent team (44 members)"  # stale

# obs/01-team-knowledge/team-overview.md
current_headcount: 46  # from last cleanup

# Notion public page
"50 AI agents across 13 teams"  # from roadmap, never updated
</code></pre>

Root cause is clear: **the same fact has no single authoritative source (SSOT — Single Source of Truth), dispersed across multiple locations with independent maintenance.** This isn't a new problem in software engineering — databases use primary key constraints for uniqueness, code uses variables to avoid scattered magic numbers — but AI system knowledge bases and configuration documents usually rely on "someone remembers to sync," and humans (and AIs) forget.

## The Fact-SSOT Meta-Rule

<pre><code class="language-yaml"># agent-CEO/config/organization.yaml — THE authority for agent counts
# All other files must reference this file, not maintain their own copy
team:
  total_agents: 58
  core_agents: 58
  optional_modules: [Janus, Stock]
  last_updated: 2026-04-25
  ssot_maintainer: harness_engineer

# Usage in CLAUDE.md: "Multi-Agent team (58 core / all 69 enabled)"
# Source: organization.yaml — DO NOT update this number elsewhere
</code></pre>

We introduced a meta-rule called Fact-SSOT, with simple core logic: **for any quantitative fact referenced in multiple places, designate a single authoritative file (SSOT); all other references must cite the source; forbid hard-coding values in non-SSOT files.**

Three implementation steps:

**Step 1: Identify drift-high-risk numbers.** Not every number needs SSOT management. Drift-high-risk characteristics: changes over time, referenced by multiple files, no automatic notification on change. Team headcount, version numbers, prices, configuration parameters — all under management.

**Step 2: Designate an SSOT file for each fact category.** Our rule: team headcount authority is `agent-CEO/config/organization.yaml`; other files can only reference this value. Version number authority is the project root `VERSION` file.

**Step 3: Write constraints into AI instructions.** Add to CLAUDE.md: "When any number is referenced in more than one file, the SSOT source must be cited in the proposal phase; when modifying fact numbers, update the SSOT first, then check and update all reference locations."

<div class="callout callout-insight"><p>Meta-rules (rules that govern other rules) are how you manage consistency at scale. When your system is complex enough that no one can track every detail from memory, you need the system architecture itself to carry consistency guarantees — not reminders and personal discipline.</p></div>

## Fixing Existing Drift and Prevention

The existing fix took about 20 minutes: open `organization.yaml`, confirm the actual current count, uniformly replace all reference locations, annotate each with "source: organization.yaml."

For prevention, we added a checkpoint to the code commit process: any commit involving SSOT file changes automatically prompts checking associated reference locations. Not a hard block — a reminder, preserving process flexibility while handling special cases.

Three weeks later: two team composition changes, both successfully completed full-file synchronization, no new drift. More importantly, team members (including AI agents) instinctively ask "where is this number's SSOT?" when discussing figures — that habit itself is the best anti-drift mechanism.

## Key Takeaways

<ol>
<li>If you maintain multi-file AI systems, ask "where is each fact's authority source?" before the first drift incident — answering this takes an hour; fixing drift aftermath takes much longer.</li>
<li>If you find number inconsistency, fix the architecture, not just the values — patching numbers without SSOT designation means they'll drift again within weeks.</li>
<li>If you're building AI agent context files, treat quantitative facts (counts, versions, thresholds) as a separate category from narrative description — they have different maintenance requirements.</li>
</ol>

## Read the Full Article (Chinese)

This is an abstract. The full technical walkthrough — including the complete SSOT file structure, the AI meta-instruction syntax, and the commit hook implementation for drift prevention — is in Chinese at [lysander.bond/blog/fact-ssot-meta-rule-for-ai-agent-systems](https://lysander.bond/blog/fact-ssot-meta-rule-for-ai-agent-systems).
