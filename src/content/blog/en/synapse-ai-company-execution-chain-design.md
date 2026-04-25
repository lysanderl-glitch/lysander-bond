---
title: "Building an AI Company With an Actual Execution Chain"
slug: synapse-ai-company-execution-chain-design
description: "Not 'AI helps me do work' — 'an AI company that operates.' The design notes behind Synapse: CEO role, decision chain, dispatch protocol, and QA gates."
lang: en
translationOf: synapse-ai-company-execution-chain-design
hasEnglish: false
pillar: methodology
priority: P1
publishDate: 2026-04-12
author: content_strategist
keywords:
  - Synapse
  - Execution Chain
  - AI Engineering
  - Claude Code
  - Multi-Agent
---

## I'm not using AI to do work — I'm running an AI company

Late last year I started taking a question seriously: why does almost everyone use Claude Code as "the AI that helps me write code"? Nothing wrong with that, but it always felt like a layer was missing. What I actually wanted was a continuously operating execution system — not a one-shot assistant, but a real organization with role boundaries, decision chains, and quality gates.

So I spent a few months building Synapse on top of Claude Code: an engineering framework that organizes AI collaboration into something that runs like a company. This piece is not a tour of impressive AI capabilities. It is a record of the failures the design hit, and the structures that finally stabilized.

The team this powers — Janus Digital, codename Synapse-PJ internally — runs around fifty agents across product, ops, growth, and engineering. The patterns below are what made that survivable.

## The core failure: AI without execution boundaries

The earliest version had a textbook problem. I would hand Claude a task, and it would execute end-to-end — edit files, run commands, produce output, all in one go. Sounds great. Two symptoms emerged fast:

First, what the AI did kept drifting subtly from what I wanted, and I noticed too late. Second, the same kind of task would produce wildly different output quality across sessions, because every session started from scratch. There was no organizational memory.

The realization: a single-AI execution model isn't fundamentally a capability problem, it's a **role-boundary** problem. A human who simultaneously owns requirements, architecture decisions, and code implementation will make mistakes. Human companies solved this a century ago — CEOs don't write code, engineers don't make strategy, QA doesn't make business calls. There's no reason to make the AI team an exception.

## The execution chain: turn conversation into process

The core of Synapse is a mandatory execution chain. Any task that comes in must pass through fixed nodes. Skipping is not allowed.

**【0.5 Acknowledgement】** — The CEO (Lysander, our AI CEO) restates the user's goal in their own words, confirms understanding, and judges the decision tier. This step sounds redundant. In practice it's the most important interceptor we have. It forces the vague "do X for me" into the explicit "I understand you want X, specifically Y, correct?" The cost paid here saves enormous rework downstream.

**【① Tiered routing】** — Tasks split into S, M, L tiers. S-tier (under five minutes, negligible risk) goes straight to dispatch and execute. M-tier requires a quick plan confirmation. L-tier requires deep advisory analysis and expert review. Tiering isn't ceremony — it's resource allocation. If every task runs the full process, the system drowns under low-value work.

**【② Mandatory dispatch table】** — This is a hard constraint I added later, and it turned out to be the single most important pattern I discovered. Before the CEO calls any execution tool, it must output a dispatch table in a fixed format: work item, executor, deliverable. No exceptions. I initially thought it was bureaucratic overhead. It solved a real problem: CEO/executor role confusion. The moment you require "declare who does what before doing anything," you discover that many tasks should not, in fact, be done by the CEO at all. The format itself is a thinking checkpoint.

**【③ QA gate】** — After execution, mandatory quality review. Auto-scored anything below 3.5 cannot ship. UI changes carry an additional mandatory screenshot verification step — no passing screenshot, no completion. In production this rule alone catches roughly thirty percent of the "looks done but isn't" outputs that would otherwise have shipped.

This four-node chain is enforced for every task. The friction is intentional. It is the friction that makes the difference between "AI did something" and "AI executed a controlled process I can audit."

## CEO Guard: turning rules into technical constraints

Writing rules in a document is not enough. Under load, the AI will "forget" them. What actually keeps Synapse stable is moving the core rules from document layer to runtime layer.

The mechanism is Claude Code's PreToolUse hook. Before any tool call, the hook fires, injects an audit record, and checks whether the call violates the CEO execution boundary. The CEO (main conversation) is explicitly limited to `Read / Skill / Agent / Glob / Grep`. `Bash / Edit / Write / WebSearch / WebFetch` are forbidden in the main conversation — they may only run inside subagent contexts. Violations are logged into the audit log and trigger alerts.

The philosophy: **don't rely on the AI's memory or self-discipline; embed the constraint in the execution environment itself.** This is the heart of Harness Engineering — Agent = Model + Harness, where the model defines the ceiling and the harness defines the consistency. If a rule matters, it lives in a hook, not a prompt.

## Cross-session state: giving the organization a memory

Another problem that kept recurring: session breaks. Every new Claude Code session starts blank. Whatever was "in progress" at the end of last session disappears.

The fix is forced state persistence. Before every session ends, Lysander must write in-progress tasks to `active_tasks.yaml` — current chain node, blockers, next step. At the start of every new session, the first action is to read that file and restore context. The mechanism gives the *organization* a memory, even when the underlying AI instances are fresh. Behavioral continuity decouples from model continuity.

## Three reusable design principles

**1. Role boundaries must be technical, not descriptive.** Writing "the CEO should not execute directly" in a prompt and using a hook to physically block the CEO from invoking Bash are two completely different interventions. The more important the rule, the more it needs to be in the execution environment, not the instruction text.

**2. Mandatory front-loaded steps are the highest-ROI quality lever you have.** Acknowledgement, dispatch tables, tier judgment — these look like process overhead. They are actually the cheapest quality gate available. Ten seconds of alignment before execution is ten times cheaper than discovering drift after execution.

**3. Treat organizational design and technical design as the same problem.** Synapse's four-tier decision system, HR management, dispatch routing — these are not "AI roleplay." They are solutions to real engineering problems: task routing, resource allocation, quality assurance. Human organizations have spent a century solving these. Borrow directly. Do not reinvent.

If you are building an AI engineering team, the Synapse framework — execution chain design, harness configuration spec, CEO Guard implementation — is available as reusable templates. The patterns are open; the scar tissue is documented.
