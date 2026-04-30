---
title: "[EN] 给 AI 工作流设计输出路径规则：为什么临时修复是系统债务"
description: "从「文件写错目录」这个小事故出发，讲清楚 AI Agent 输出治理应该以规则驱动而非事后补救"
date: 2026-04-30
publishDate: 2026-04-30T00:00:00.000Z
slug: ai-workflow-output-path-governance
lang: en
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

## TL;DR

- A misfiled PDF revealed 9 path errors over 47 days, mostly undetected
- Prompt-based fixes are soft constraints — they don't solve structural problems
- Output path decisions belong to the workflow layer, not the AI agent
- Declare routing rules explicitly in config; agents own content, not destinations
- A fallback with alerting beats silent failures every time

Three weeks ago, an AI agent in our workflow wrote a generated PDF to `/tmp/output/` instead of the designated `/reports/client/` directory. The fix took two minutes — move the file, mention it in Slack, move on. But when I pulled the logs, I found this had happened 9 times in 47 days. Six of those instances were only caught during routine audits. Our internal response each time was identical: move the file, remind the team to check paths, repeat. We weren't fixing anything. We were accumulating system debt and calling it maintenance.

The instinct was to blame the prompt — tighten the wording, add a line like "always write to the correct directory." That's the wrong diagnosis. The real issue is that output path decisions were happening somewhere inside the agent's reasoning chain, opaque and context-sensitive. Ambiguous words like "draft" or "temp" in task descriptions pushed the agent toward temporary directories. Path parameters leaked between concurrent workflow instances. Previous task context got inherited incorrectly. Natural language instructions are soft constraints: the agent *usually* follows them, until it doesn't. Patching a structural problem with another instruction is not a fix — it's a delay.

The solution we implemented was to remove path decision-making from the agent entirely. We defined an explicit `output_routing` config block in YAML, loaded at workflow initialization. Each `task_type` maps to a hard-coded destination pattern, a filename template, and a conflict resolution strategy (`version_suffix` or `overwrite`). Temporary paths get a `ttl_hours: 24` and `auto_cleanup: true`. Critically, the fallback rule routes unmatched files to `/reports/unclassified/` and fires an `ops-alerts` notification — no silent failures, no mystery disappearances. In our n8n implementation, this lives in a dedicated "path resolver" function node downstream of the agent, not inside the system prompt. When something breaks, you get a clean error stack instead of a confused model output.

## Key Takeaways

- If you're adding path instructions to a system prompt, move that logic to a config file instead — configuration is reviewable code, instructions are unverifiable expectations
- If your agent outputs different file types or serves different task categories, declare explicit routing rules per `task_type` before you hit your first misfiled document
- If you're manually correcting AI output errors more than once, treat the third occurrence as a signal to audit the structural design, not the prompt wording
- If you define any temporary output path, attach a TTL and auto-cleanup policy at declaration time — not as a follow-up task
- If no routing rule matches, always write to a known fallback location and alert — unclassified beats missing

## Read the Full Article (Chinese)

This is an abstract. The full technical walkthrough — including the complete YAML routing config, n8n implementation details, and root cause analysis — is available in the original Chinese article.
