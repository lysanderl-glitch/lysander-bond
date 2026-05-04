---
title: "Agent Memory Collaboration Autonomous Decision Making"
description: "How externalized memory with active_wbs fields reduced task recovery from 5 minutes to 30 seconds, enabling 85% of decisions to run autonomously."
date: 2026-05-03
publishDate: 2026-05-03T00:00:00.000Z
slug: agent-memory-collaboration-autonomous-decision-making
lang: en
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

TITLE: Agent Memory Collaboration Replaces Manual Approval

## TL;DR
- Manual approval became single point of failure in multi-agent workflow
- Agents lacked persistent context to resume interrupted tasks
- Static product descriptions insufficient without active task identifiers
- Active_wbs field in product-profile frontmatter enabled 30-second recovery
- 85% of tasks now resolved autonomously in L1-L2 range without escalation

In our Synapse system at week three, the CEO agent was processing up to seventeen pending confirmation requests every morning—each product line coordinator was blocking on manual approval before proceeding. This contradicted our goal of offloading repetitive decisions to machines. The core problem: multi-agent collaboration requires agents to know task context, current deadlock points, and next handoff targets, but LLMs themselves are stateless. Without externalized memory, agents either depended on humans repeatedly explaining background (inefficient and error-prone) or made unauthorized decisions (unacceptable risk).

We initially assumed that providing each agent with a product background document would solve state sharing. However, obs/02-product-knowledge/PMO-Auto-Monday/product-profile.md only contained static product descriptions—features, tech stack, team contacts. Agents could retrieve context but could not locate execution breakpoints. When Lysander attempted morning recovery, discovering twelve in-progress tasks across agent-CEO/config/active_tasks.yaml without knowing which step each had stopped at caused recovery cycles to exceed five minutes. The root cause: product-profile.md lacked the active_wbs field in frontmatter, preventing agents from directly positioning to resume points.

The fix involved adding active_wbs to frontmatter metadata, enabling direct jump to task state. Recovery time dropped from approximately five minutes to thirty seconds. With the decision framework in .claude/harness/product-routing.md classifying 85% of tasks into L1-L2 range, most now complete autonomously without human intervention.

## Key Takeaways
- If your agents repeatedly ask for background context, externalize state into structured documents instead of relying on conversation memory
- If your task graphs take over five minutes to rebuild, the metadata schema lacks active positioning fields
- If your approval bottleneck grows linearly with team size, implement stateless decision routing rather than centralized review
- If your agents make out-of-scope decisions, the product-profile is storing descriptive content instead of state-relative identifiers
- If your recovery procedures require human intervention, add active_wbs equivalent fields to frontmatter

## Read the Full Article (Chinese)
This is an abstract. The full technical walkthrough is in Chinese.
