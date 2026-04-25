---
title: "Notes from the Field: Obsidian as the Single Source of Truth for an AI Team"
slug: aiobsidian
description: "An abstract of a Chinese article on using Obsidian as the SSOT for an AI multi-agent team — HR knowledge, decision rules, and Harness Engineering all derive from Obsidian markdown cards."
lang: en
translationOf: aiobsidian
hasEnglish: true
pillar: ops-practical
priority: P3
publishDate: 2026-04-09
author: content_strategist
keywords:
  - "AI"
  - "team-collaboration"
  - "Obsidian"
  - "automation"
---

# Notes from the Field: Obsidian as the Single Source of Truth for an AI Team

This is an abstract of a Chinese-language Synapse architecture write-up. The premise: don't maintain agent definitions in three places (Obsidian, YAML configs, code). Pick one as the source of truth and derive the rest. We chose Obsidian markdown personnel cards as the SSOT — `hr_watcher.py` watches for changes, `hr_base.py` syncs them into `*_experts.yaml`, and CrewAI loads the YAML at runtime. The full Chinese article includes the full architecture diagram, the role hierarchy (President → CEO → Think Tank → 5 execution teams / 29 specialists), the `decision_check()` enforcement layer, and the Harness Engineering error-recovery patterns.

## Key Takeaways

- **Obsidian is the source of truth, everything else is derived**: change a `.md` card; `inotify` triggers sync; YAML configs regenerate; agents load updated capabilities. No drift between three copies of the same data.
- **Personnel cards have structured frontmatter**: `specialist_id`, `team`, `role`, `domains`, `capabilities`, `availability`, summon-keywords. The same fields make humans browse-able in Obsidian and machines parse-able as YAML.
- **Error recovery hardens by case**: each past error becomes a permanent guard — `cp` instead of release script → forced use of `harness-daily-publish.sh`; Python syntax errors → keyword-triggered code review; principle drift → `decision_check()` code-level enforcement. Errors don't repeat, by construction.
- **29 specialists across 6 teams**: Graphify (think tank, 4) / Butler (delivery, 7) / RD (engineering, 5) / OBS (knowledge, 4) / Content_ops (content, 4) / Stock (trading, 5). Each team's roster auto-syncs from Obsidian.

## Why This Matters

Every AI multi-agent system eventually faces the same structural question: where do agent definitions live? Most projects answer "in code" or "in YAML" — both lock the team into engineering changes for any HR adjustment. Synapse picks Obsidian because it's already the human knowledge base, and personnel changes feel like editing knowledge rather than editing config. The "principles become code" idea that runs through this article is the Synapse signature: management rules don't live in documents to be remembered; they live in `decision_check()` to be enforced. Anyone considering a multi-agent team architecture should read the Chinese version, especially the architecture diagram and the error-recovery table.

---

*This is an abstract. Read the full article in Chinese →* [构建 AI 团队协作体系：让 Obsidian 成为第二大脑](/blog/aiobsidian)
