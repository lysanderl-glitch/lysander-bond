---
title: "Notes from the Field: Personal Task Management with Claude Code as the Hub"
slug: personal-task-management-claude-code-workflow
description: "An abstract of a Chinese article on collapsing capture, organize, and execute into a single Claude Code session, using a YAML active_tasks file as the only state store."
lang: en
translationOf: personal-task-management-claude-code-workflow
hasEnglish: true
pillar: ops-practical
priority: P3
publishDate: 2026-04-12
author: content_strategist
keywords:
  - "personal-productivity"
  - "Claude-Code"
  - "Synapse"
---

# Notes from the Field: Personal Task Management with Claude Code as the Hub

This is an abstract of a Chinese-language article inspired by the *How I AI* podcast's observation that the biggest productivity drag for knowledge workers is the friction *between* capturing and executing — every transfer (paper → inbox → Notion → editor) costs information and attention. Since most of my real work already happens inside Claude Code, why not collapse capture, organize, and execute into the same session? The full Chinese article describes the three-layer workflow built around a single `active_tasks.yaml` file, and the deliberate decision to *not* let AI classify tasks (because category systems are themselves a maintenance burden).

## Key Takeaways

- **Capture happens where execution happens**: tasks are spoken into Claude Code in natural language. Claude appends them to `active_tasks.yaml`. No format decisions, no foldering, no tagging.
- **AI does structural judgment, human does value judgment**: priority, dependencies, context loading — AI handles these mechanically using full task history. "Is this worth doing?" stays with the human.
- **No daily review ritual**: traditional GTD demands periodic review; here, review is automatic — every new session begins with Claude reading `active_tasks.yaml` and reporting in-progress items.
- **YAML, not Markdown, not Notion**: YAML has structure (so the AI doesn't drift into format errors) and is human-checkable. Notion / Linear / Asana all live outside the execution environment, costing context switches.

## Why This Matters

Most "AI task management" products try to be Notion with an LLM bolted on. This article inverts: the AI session *is* the task manager, and persistence is just a YAML file. The deeper insight — that capture and execution should share an environment to eliminate transfer friction — is the same principle that drove the Synapse decision to treat Obsidian as the SSOT for everything else. Not for everyone (if your work isn't text or code, this won't help), but transformative if your day already lives in a CLI plus AI conversation.

---

*This is an abstract. Read the full article in Chinese →* [个人任务管理的 AI 化](/blog/personal-task-management-claude-code-workflow)
