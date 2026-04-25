---
title: "Notes from the Field: Understanding n8n's executeOnce Setting"
slug: n8n-node-execution-strategy
description: "An abstract of a Chinese tutorial on n8n's item-based execution model and the executeOnce flag, with examples for chained Asana/Slack workflows."
lang: en
translationOf: n8n-node-execution-strategy
hasEnglish: true
pillar: ops-practical
priority: P3
publishDate: 2026-04-04
author: content_strategist
keywords:
  - "n8n"
  - "workflow"
---

# Notes from the Field: Understanding n8n's executeOnce Setting

This is an abstract of a Chinese-language n8n tutorial. n8n's execution model differs from traditional programming: data flows between nodes as **items**, and downstream nodes execute once per item by default. Misunderstanding this leads to either accidental fan-out (10 users → 10 task creations when you wanted one) or missed iterations (one summary call where you wanted 10 details). The full Chinese article walks through `executeOnce`, expression syntax for referencing prior nodes, and a concrete Asana + Slack workflow that mixes both modes.

## Key Takeaways

- **Default behavior is per-item iteration**: a node receiving 10 items executes 10 times. This is fan-out by default, which surprises engineers used to "function called once per pipeline run."
- **`executeOnce: true` collapses to a single run**: useful when you only need the first item or an aggregate, regardless of upstream count.
- **Three expression patterns matter**: `$('Node').first().json.field` (first item), `$('Node').item.json.field` (current item), `$('Node').all()` (full array). Picking the wrong one is the most common silent-data-bug source.
- **Mixed mode is normal**: a real Asana workflow uses `executeOnce: false` for "create one task per role" but `executeOnce: true` for "look up the project lead's user ID once."

## Why This Matters

n8n is a foundational tool in the Synapse stack and most user-facing pipeline failures trace back to the item-iteration model. The Chinese article's debugging tips — double-clicking nodes to inspect input/output, using Code nodes to log intermediate variables, stepping through Test workflow runs — are the same patterns we use across all our workflows. If you've ever wondered why your n8n flow either created 47 duplicate tasks or quietly created none, this is the article that explains why.

---

*This is an abstract. Read the full article in Chinese →* [n8n 节点执行策略](/blog/n8n-node-execution-strategy)
