---
title: "Notes from the Field: When Principles Fail, Encode Them in Code"
slug: ai
description: "An abstract of a Chinese article on transforming team decision principles from documentation into code-level enforcement, eliminating the 'everyone knows the rule, everyone breaks the rule' anti-pattern."
lang: en
translationOf: ai
hasEnglish: true
pillar: ops-practical
priority: P3
publishDate: 2026-04-09
author: content_strategist
keywords:
  - "AI"
  - "decision-systems"
  - "automation"
---

# Notes from the Field: When Principles Fail, Encode Them in Code

This is an abstract of a Chinese-language Synapse case study. Our team had clear decision principles written down: small problems execute directly, strategy proposals go through the think tank, only true escalations reach the CEO. Everyone knew the rules. Everyone defaulted to "let me ask Lysander first" anyway. The full Chinese article diagnoses why principles-as-documentation fail, walks through the SWOT analysis from our strategist agent, and lands on the solution: encode the decision tree directly into `hr_base.py` as a `decision_check()` function that classifies tasks at runtime. Once principles became code, the violation pattern stopped — because there was no longer a step where a human could choose to violate.

## Key Takeaways

- **The bug is the ask, not the asker**: "wait for confirmation" is triggered by internal uncertainty, which exists because the principle has no execution trigger. Documentation cannot fix this; only a system-level enforcement point can.
- **Three-branch decision tree**: keyword-driven classifier routes tasks to (a) `small_problem` → execute directly, (b) `think_tank` → convene experts then execute, (c) escalate to CEO. Each branch has explicit keyword lists making the classification auditable.
- **Code-review keywords trigger mandatory QA**: any task containing `脚本/代码/实现/harness/workflow` triggers `pre_execution_check()` (Python syntax + dependency check) before execution. Prevents low-level errors from shipping.
- **Execution chains eliminate "what's next?" reflex**: `TASK_EXECUTION_CHAIN` declares post-task successors (sync OBS → build site → publish blog). Completion automatically triggers the next link instead of waiting for human prompt.

## Why This Matters

This article articulates the core philosophy behind Synapse Harness Engineering: when a problem keeps recurring, it's not a willpower failure, it's a missing system enforcement point. Building principles is one job; building enforcement mechanisms is a different job — the first relies on documentation, the second on code and process. The Synapse `hr_base.py` `decision_check()` function is the canonical example, and the Harness feedback loop (`record_decision`, `record_feedback`, `post_execution_evaluate`) closes the system into a self-correcting machine. Anyone tired of writing the same retrospective twice should read this.

---

*This is an abstract. Read the full article in Chinese →* [从原则失效到自动化决策](/blog/ai)
