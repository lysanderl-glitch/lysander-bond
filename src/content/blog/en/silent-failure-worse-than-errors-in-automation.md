---
title: "When Automation Fails Silently 23 Times: Why Zero Logs Are More Dangerous Than Errors"
slug: silent-failure-worse-than-errors-in-automation
description: "23 consecutive zero-message triggers from pmo-wbs-trigger exposed a counterintuitive truth: 'fake success' is harder to debug than 'real errors.'"
lang: en
translationOf: silent-failure-worse-than-errors-in-automation
pillar: ops-practical
priority: P2
publishDate: 2026-04-18
author: content_strategist
keywords:
  - Incident Log
  - AI Engineering
  - Synapse
---

## When Automation Fails Silently 23 Times: Why Zero Logs Are More Dangerous Than Errors

Last Wednesday around midnight, while cleaning up n8n workflow logs, I found a number that made my back tense. The `pmo-wbs-trigger` — a scheduled task that fires every 30 minutes — had **zero errors, zero alerts, zero business logs** across 23 consecutive trigger records. On the Grafana dashboard it was a flat green line, because it had never "failed." It just hadn't done anything.

That moment crystallized something for me: the monitoring system I'd spent three months building could only catch "errors," not "fake successes." And in automation systems, the latter is the real killer.

### Background: A Trigger That Should Have Been Working

The job of pmo-wbs-trigger is straightforward — every 30 minutes, scan `active_tasks.yaml` and re-dispatch any tasks whose blockers have cleared back to the executing agents. It's the most unglamorous link in our execution chain, but it underwrites our cross-session task-resumption guarantee.

Its health check was written this way: HTTP 200 = healthy. The n8n webhook was returning 200, so the monitor never alarmed. The problem was that the handler logic behind that webhook contained a `try/except Exception: pass` — originally added by a previous engineer "to prevent task interruption." The result: YAML parse failures, agent dispatch failures, Slack notification failures — all swallowed, returning 200.

### Why Silent Failure Is Harder to Debug Than Errors

When the team did the post-mortem, I drew a matrix.

One class of failure is "real errors": stack traces, 500s, timeouts. These have high signal strength, complete alerting paths, and MTTR typically measured in minutes. The other class is "fake success": HTTP 200, exit code 0, "task triggered" log lines — but nothing happened downstream. These have no signal at all. The only path to detection is reasoning backward from "business outcome looks wrong," and MTTR is measured in days.

Our 23 silent failures came from a downstream agent's check-in file being accidentally deleted, which made the dispatch routing unable to find the receiver. The whole call chain was idling at the second hop, but the first hop (the trigger itself) believed it was working fine.

The counterintuitive part: **the more reliable the system, the more dangerous silent failure becomes**. Teams equate "no alerts" with "everything is fine," and shift attention elsewhere. By the time we noticed, 11 PMO tasks had been rotting in `active_tasks.yaml` for two full days.

### The Fix: From "Monitoring Errors" to "Monitoring Outcomes"

I had harness_engineer make three changes.

First, **ban bare excepts**. A repo-wide grep for `except Exception: pass` turned up 37 spots. Every single one was rewritten to do explicit handling with structured logging — exception type, context, trace_id all required to land in logs. The "prevent interruption" tolerance logic was, in practice, "prevent you from knowing the system is broken."

Second, **add semantic health checks**. The trigger's health is no longer defined as "HTTP 200" but as "completed at least 1 valid task dispatch in the past 2 hours." Zero dispatches counts as sick, even if the webhook returns 200. We added this as an `absent_over_time` rule in Prometheus.

Third, **make heartbeat logs routine**. Every automation task, every execution, regardless of whether there was business activity, must emit a structured heartbeat: `{task_id, trigger_time, scanned_items, dispatched_items, skipped_reason}`. Three consecutive `dispatched_items=0` events trigger an immediate alert — because "did nothing" is itself an alert-worthy state.

### Three Reusable Principles

**1. Health checks must be business-semantic, not technical-signal.** HTTP 200, process alive, normal CPU — these only prove "the server is breathing," not "the service is creating value." When you define health, ask: if this service was completely slacking off but kept its heartbeat, would the monitor catch it?

**2. Zero output is an anomaly, not a default.** A task that should produce data, producing zero data multiple times in a row, deserves an alert at the same severity as "produced wrong data." Most teams' alert rules cover "value too high" but not "value is zero."

**3. Tolerance does not equal swallowing exceptions.** Real fault tolerance is "fail, degrade, log explicitly, notify a human" — not pretending everything is fine. The moment you write `except: pass`, you're planting a delayed bomb for your future self.

Looking back, those 23 silent failures didn't cause catastrophic loss — that's luck. But they recalibrated a judgment for me: **in automation systems, "everything is fine" is a conclusion that has to be proven, not a default state.**

If you're building an AI engineering team, take a look at our open-source Synapse framework. It includes the full execution-chain audit, silent-failure detection, and cross-session task resumption mechanisms — hopefully it spares you a few of the pits we fell into.
