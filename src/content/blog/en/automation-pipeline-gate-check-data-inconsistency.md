---
title: "Notes from the Field: Phantom Data in Automation Pipelines"
slug: automation-pipeline-gate-check-data-inconsistency
description: "An abstract of a Chinese case study where 111 records were written to Asana but only 19 were visible to the gate check, exposing a structural data-consistency trap in multi-stage pipelines."
lang: en
translationOf: automation-pipeline-gate-check-data-inconsistency
hasEnglish: true
pillar: ops-practical
priority: P3
publishDate: 2026-04-20
author: content_strategist
keywords:
  - "incident-log"
  - "AI-engineering"
  - "Synapse"
---

# Notes from the Field: Phantom Data in Automation Pipelines

This is an abstract of a Chinese-language Synapse case study. Our WBS-to-Asana pipeline wrote 111 tasks successfully, the Asana UI showed all 111, but the downstream "completeness gate" only ever counted 19. No errors, no exceptions, no network anomalies — the data was simply invisible to one stage of the pipeline. The full Chinese article walks through the diagnosis, root cause, and the three reusable principles we extracted for any multi-stage automation system. It is most useful for AI engineers building Asana / WBS / Notion integrations and for anyone designing gate-check logic in event-driven pipelines.

## Key Takeaways

- **Write path and read path used different filters**: the sync module created tasks via `projects/{gid}/tasks` (no section), while the gate queried `sections/{gid}/tasks` (section-only). Same data, two different WHERE clauses, 92 invisible records.
- **Unit tests cannot catch this class of bug**: the writer's test verified successful POST, the reader's test verified non-empty response. Both passed. Only end-to-end runs surfaced the mismatch.
- **The fix is a single shared "valid record" definition**: extract "what counts as one valid task" into a single function or constant, and reference it from both writer and reader. Never let two pieces of code each invent their own filter.
- **Every pipeline needs a conservation-law assertion**: if you write N records, downstream visibility must equal N. Print the set difference on mismatch. Ten minutes of code; saves a full day of debugging.

## Why This Matters

Phantom data is a silent failure pattern unique to multi-stage automation, and it gets more common as AI agents start writing and reading from the same systems on different schedules. The bug is structural — it lives in the gap between two reasonable definitions of "a valid record" — so no amount of monitoring at either endpoint will surface it. The Chinese article generalizes this into three reusable principles: shared data-view definitions, broadest-possible reads in gate checks, and explicit conservation assertions. These principles are baked into the Synapse Harness Engineering methodology and apply equally to CI/CD pipelines, ETL flows, and multi-agent execution chains.

---

*This is an abstract. Read the full article in Chinese →* [自动化流水线的幽灵数据](/blog/automation-pipeline-gate-check-data-inconsistency)
