---
title: "Harness Engineering for AI Agents: Why Your Model Isn't the Bottleneck"
slug: harness-engineering-guide
description: "A practitioner's guide to Harness Engineering — the discipline of building feedforward and feedback controls so your coding agents stop repeating the same mistakes."
lang: en
translationOf: harness-engineering-guide
hasEnglish: false
pillar: methodology
priority: P1
publishDate: 2026-04-06
author: content_strategist
keywords:
  - Harness Engineering
  - AI Agent
  - Context Engineering
  - Mitchell Hashimoto
  - Coding Agents
---

In February 2026, Mitchell Hashimoto gave a name to something a lot of us had been quietly building: **Harness Engineering**.

> When an agent makes a mistake, don't just hope it does better next time. Spend the time to design a solution that ensures it never makes the same mistake again.
>
> — Mitchell Hashimoto

If you have been operating a coding agent in anger for more than a few months, that sentence probably lands hard. It certainly did for us. We had been running a multi-agent team inside a working enterprise — codename Synapse-PJ, built on Claude Code — and the failures we kept hitting weren't model failures. They were harness failures.

This guide is what we wish we had read before we built ours.

## The framing: Agent = Model + Harness

Most discussions about agent quality focus on the model. Bigger context. Better reasoning. Newer release. All useful, but missing the point: when your agent ships a regression for the third time, the problem isn't that the model is dumb. The problem is that nothing in the surrounding system caught the regression on attempt one or attempt two.

A reliable agent is a model plus a harness. The harness is the engineered environment around the model — the rules it reads before acting, the sensors it has to read after acting, the hooks that decide what it can even attempt. When operators say "our agent is reliable," they almost always mean "our harness is good." The model is a commodity; the harness is the moat.

Harness Engineering is the discipline of building that moat.

## Two control mechanisms that do most of the work

Any harness worth the name does two things: it shapes behavior **before** the agent acts, and it observes behavior **after** the agent acts. Feedforward and feedback. Open-loop guidance and closed-loop correction.

### Feedforward: get it right the first time

Feedforward is everything you put in front of the agent so the first attempt is closer to good. Done well, it is the cheapest quality intervention you have, because it costs zero retries.

In practice, the feedforward layer is built from three kinds of artifact:

- **AGENTS.md or CLAUDE.md**: a project-level brief that tells the agent the architecture decisions, the coding conventions, the things you want it to never do. Not a wiki. A briefing document the agent reads on every turn.
- **Bootstrap skills**: standardized initialization flows — "set up a new feature branch," "add a new API endpoint" — packaged so the agent doesn't reinvent the workflow each time.
- **Code mods**: deterministic transformations the agent can invoke instead of hand-editing. Anything that can be a deterministic rewrite probably should be.

> **Field note from the Ghostty terminal project**: a tight, well-curated AGENTS.md eliminated almost all of the agent's bad behavior. Not because the model got smarter — because it stopped having to guess.

The trap with feedforward is bloat. Every team eventually overfills its AGENTS.md, the model starts ignoring the lower half, and the harness silently degrades. We hit this in Synapse and ended up imposing a hard 350-line ceiling on the project brief, with timestamped rule entries and a 180-day decay review. The lesson generalizes: feedforward documents are code. They need a budget.

### Feedback: catch it fast when it's wrong

Feedback is what the agent reads **after** it acts to know whether it succeeded. It is the closed loop. Without it, your agent is flying blind and you're the only sensor.

Feedback splits into two types worth distinguishing:

| Type | Cost | Examples |
|---|---|---|
| Computational | Deterministic, milliseconds | Tests, linters, type-checkers, schema validators |
| Reasoning | Non-deterministic, seconds-to-minutes | AI code review, architecture review, behavioral checks |

The split matters because it tells you where a sensor goes in the pipeline. Cheap and deterministic? Run it on every keystroke. Expensive and reasoning-heavy? Save it for the CI gate.

Three sensor patterns we lean on:

- **Custom linters** for project-specific rules a generic linter doesn't catch — things like "no business logic in the controller layer" or "every API handler must declare its idempotency key."
- **Targeted test selection**: run the tests most likely to break given the changed files, not the full suite. The agent gets a signal in seconds instead of waiting on a fifteen-minute CI run.
- **Visual regression**: for any UI change, screenshot before and after. We made screenshot verification a required QA step in our team's harness, and it catches roughly thirty percent of "looks done but isn't" outputs.

## Three layers of harness, in order of investment

When you sit down to build a harness, build it in this order. The earlier layers compound.

### 1. Maintainability harness

Structural checks. Duplicated code, cyclomatic complexity, style violations. Use what already exists — ESLint, Prettier, ruff, gofmt. This layer pays for itself the first week.

### 2. Architecture fitness harness

Fitness functions: programmatic checks that encode your architectural decisions. "Module A may not depend on module B." "All public APIs must have an OpenAPI definition." These are the rules that exist in the heads of your senior engineers; the harness moves them into code so the agent can respect them without anyone having to remember to enforce them.

This is the layer most teams skip and most regret skipping.

### 3. Behavior correctness harness

Specifications as feedforward, AI-generated test suites as feedback. This is the newest and least mature layer — the AI-test-generation tooling is still rough — but it's where the field is heading. Worth tracking. Not yet worth betting the harness on.

## Field-tested guidance

Four rules we have paid for in scar tissue.

**1. Iterate the harness, not the prompt.** The next time the agent repeats a mistake, do not edit the prompt to scold it. Add a sensor that catches the mistake automatically. The prompt is a one-shot intervention; the sensor compounds.

**2. Shift quality left, but not too left.** Cheap deterministic checks belong as close to the agent's keystroke as possible. Expensive reasoning checks belong further down the pipeline. Putting an LLM-based architecture review on every save will burn your budget and your patience.

**3. Monitor the harness itself.** Dead code detection, test coverage trends, runtime SLOs — these tell you whether the harness is still doing its job or has rotted. We run a periodic audit on the harness: any rule that hasn't been re-validated in 180 days is a candidate for deletion.

**4. Use the agent to extend the harness.** Coding agents are good at writing structural tests, drafting fitness function definitions, and proposing new lint rules. Don't write the harness by hand if the agent can draft it. Just review.

## Where Harness Engineering sits relative to Context Engineering

Martin Fowler frames this cleanly: Harness Engineering is the specific shape Context Engineering takes when the agent is a coding agent.

Context Engineering is the broader idea — give the model the right information and the right tools so it can do the job. Harness Engineering is what that looks like when the job is shipping software: feedforward documents, structural sensors, deterministic gates, AI reviewers, all stitched into the development loop.

If you only know one of the two terms, you are probably already doing Harness Engineering and just calling it something else.

## What to take away

Operators who get this right do four things together:

- They stop saying "the model is unreliable" and start asking "what's missing from the harness."
- They build feedforward (AGENTS.md, skills, code mods) and feedback (linters, tests, visual checks) as a single system, not as separate concerns.
- They treat the harness as a living artifact, with a budget, decay rules, and an audit cadence.
- They use the agent itself to grow and maintain the harness over time.

The model gets the headlines. The harness ships the product.

If you are running a multi-agent team and want to see what a working harness looks like in production — including the decision chain, the CEO Guard, and the rule-entropy controls — the Synapse framework that runs our Janus Digital team is open. The patterns travel.
