---
title: "Notes from the Field: An Asana + Slack + n8n PMO Pipeline"
slug: asana-slack-n8n-automation
description: "An abstract of a Chinese case study describing a project-management automation that auto-generates task chains from a CSV process table and notifies the right person on completion."
lang: en
translationOf: asana-slack-n8n-automation
hasEnglish: true
pillar: ops-practical
priority: P3
publishDate: 2026-04-03
author: content_strategist
keywords:
  - "Asana"
  - "Slack"
  - "n8n"
---

# Notes from the Field: An Asana + Slack + n8n PMO Pipeline

This is an abstract of a Chinese-language case study. The goal: when a project kicks off in Asana, automatically create the full chain of process tasks (with assignees, durations, dependencies), provision a project-specific Slack channel, and as each step completes, notify the next owner. The full Chinese article includes the CSV process-table schema, the two-workflow design (kickoff + notification), and the concrete n8n configurations needed to wire dependencies and Slack channel routing.

## Key Takeaways

- **CSV is the source of truth, not Asana**: process tables (step number, assignee email, duration, predecessors, Slack channel) live in the knowledge base in Git. Asana receives a generated copy on project kickoff. This decouples process design from project execution.
- **Two-workflow split**: Workflow A (kickoff) listens for the "project start" task, parses the CSV, batch-creates tasks with `executeOnce: false`, sets dependencies via `POST /tasks/{gid}/addDependencies`, and provisions a Slack channel. Workflow B (notification) listens on `completed=true` and notifies downstream owners via Slack Block Kit.
- **`executeOnce` discipline matters**: looping task creation needs `false`; user-ID lookup for the project lead needs `true`. Mixing them up either creates duplicate tasks or skips users.
- **Slack channel naming convention**: `#proj-{slug}` stored in Asana task notes as `SLACK_CHANNEL` metadata, so notification logic can pull the channel without a separate lookup table.

## Why This Matters

This is the canonical "PMO automation in 100 lines of n8n config" pattern. It's the simplest project-management automation that delivers real value: humans only create one Asana task to start a project; everything else (task tree, channel, notifications) materializes automatically. The Chinese article includes the actual CSV schema and the snippet for setting Asana dependencies — copy these directly if you need a similar pipeline. The Synapse Multi-Agent system uses an evolved version of this same pattern internally for its own task graph.

---

*This is an abstract. Read the full article in Chinese →* [Asana + Slack + n8n 自动化](/blog/asana-slack-n8n-automation)
