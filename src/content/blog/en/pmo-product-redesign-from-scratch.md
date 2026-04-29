---
title: "[EN] 从还原到重塑：我们如何用'浴火重生'方式重新设计PMO产品"
description: "当迁移工具的成本高于重新思考产品本身时，回到原点才是最快的路"
date: 2026-04-29
publishDate: 2026-04-29T00:00:00.000Z
slug: pmo-product-redesign-from-scratch
lang: en
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

## TL;DR

- Migrating a legacy PMO system cost more than redesigning it from scratch
- We abandoned restoration in favor of a full "phoenix" rebuild of product logic
- 40% of old features existed to manage the system's own complexity, not user needs
- Deleting features proved harder—and more important—than adding new ones
- This decision saved us at least three months of compounding misdirection

---

At week 14 of the project, we hit a wall most engineering teams recognize too late: we were migrating a PMO system with nearly 200 workflow nodes, three mismatched design language versions, and less than 30% documentation coverage. We'd allocated 6 weeks for migration. By the end of week 3, we'd migrated 17 nodes—each one revealing an average of 2.3 hidden dependencies. Full completion at that rate would take 27 weeks, not 6. We weren't doing engineering. We were repainting a building with a cracked foundation.

The harder problem wasn't technical debt in the code—it was self-referential complexity in the product logic itself. When we stopped and re-examined the system's core requirements, we found that roughly 40% of existing features existed solely to manage problems created by the system itself, not to solve any original user need. The clearest example: an 800-line "task status sync module" whose entire purpose was reconciling three separate copies of the same task state across three modules. That module only needed to exist because of a flawed early design decision. Migrating those 800 lines versus deleting them entirely were two completely different roads. We deleted them, replaced the distributed state with a single `TaskStateManager` class as the sole source of truth, and eliminated the sync problem at its root rather than wrapping it in yet another abstraction layer.

The real friction in making this call wasn't technical—it was psychological. Abandoning restoration meant admitting that months of prior architectural decisions had been structurally invalid. That required a specific kind of honesty: not the kind used in status reports, but the kind you say out loud in a Friday afternoon team meeting before you've fully convinced yourself.

---

## Key Takeaways

- **If your migration velocity hasn't improved by week 3**, stop and ask whether you're solving user problems or problems the system created for itself.
- **If you're considering abandoning existing work**, run a "difficulty-avoidance test"—list your reasons and check how many are engineering judgments versus accumulated fatigue. They're not the same thing.
- **If you find features that exist to manage complexity**, treat it as an architecture signal, not a requirements signal. Trace back and delete; don't keep encapsulating.
- **If you're redesigning product logic**, start by listing features you would never add if building from zero. That list is more valuable than any requirements document.
- **If you're building agent workflows in tools like n8n**, the single-source-of-truth principle applies: never let two nodes independently maintain state judgments about the same entity.

---

## Read the Full Article (Chinese)

This is an abstract. The full technical walkthrough—including the complete state management pseudocode, the week-by-week migration breakdown, and the internal decision framework—is written in Chinese.
