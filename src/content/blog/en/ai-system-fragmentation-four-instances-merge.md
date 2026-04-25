---
title: "Notes from the Field: Merging Four Drifted Copies of My AI System"
slug: ai-system-fragmentation-four-instances-merge
description: "An abstract of a Chinese case study on consolidating four parallel Synapse instances (Mini, Work, Lab, Archive) that had drifted apart over two months, and the dimension-by-dimension merge strategy used."
lang: en
translationOf: ai-system-fragmentation-four-instances-merge
hasEnglish: true
pillar: multi-agent-case
priority: P3
publishDate: 2026-04-17
author: content_strategist
keywords:
  - "AI-engineering"
  - "configuration-management"
  - "Synapse"
---

# Notes from the Field: Merging Four Drifted Copies of My AI System

This is an abstract of a Chinese-language Synapse case study. I opened the file manager to add a new rule and froze: there were four Synapse directories on my desktop — `Mini`, `Work`, `Lab`, `Archive` — each with a recently modified `CLAUDE.md`, each independently evolved. My AI automation system had silently fractured into four diverging species. The full Chinese article walks through how the drift happened (legitimate-feeling clones with no merge-back path), the three signals that revealed it, and the dimension-by-dimension merge strategy used to consolidate everything back into a single authoritative repo. Useful for any team where a single operator runs multiple environments of the same AI tooling.

## Key Takeaways

- **Pick the authoritative version, not the newest**: no single instance led on every dimension. Mini had the cleanest hooks, Lab had the richest skill experiments, Work had the deepest knowledge base, Archive had a deleted methodology doc no one else had. Merge by dimension, not by timestamp.
- **Three drift signals**: behavior inconsistency (same prompt triggers different agents in different copies), broken cross-references (SOP links resolve only in some instances), and memory amnesia (the AI keeps asking you to "re-establish context" because the conversation history lives in another copy).
- **Branches, not clones, for experiments**: 90% of "let me try a new idea without breaking main" cases are git branches in disguise. Physical copies are the root cause of drift.
- **Audit drift on a 7-day cycle**: linear cost to fix at one week, exponential cost at two months. Run a `audit_harness()` diff against any local copies on a recurring schedule.

## Why This Matters

This is a configuration-management problem dressed up as an AI problem. The same drift happens with shell dotfiles, with Kubernetes manifests, with Terraform state — but it bites harder for AI systems because the configuration *is* the agent's behavior. A drifted `CLAUDE.md` is not just a stale config file; it's a different employee with a different set of instructions, running in parallel with no reconciliation. The Synapse framework now enforces a single canonical directory naming rule (`Synapse` is the only allowed name; experimental copies must carry suffixes and expiry dates) and ships with an `audit_harness()` skill specifically for catching this class of fragmentation. The certainty that comes from "exactly one authoritative version" is worth more than any new feature.

---

*This is an abstract. Read the full article in Chinese →* [AI 自动化体系碎片化：四实例合并实录](/blog/ai-system-fragmentation-four-instances-merge)
