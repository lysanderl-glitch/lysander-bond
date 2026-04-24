<!-- Auto-generated from synapse@36ab925 on 2026-04-24T13:38:21.253Z; DO NOT EDIT. -->
---
id: harness-engineering-methodology
type: core
status: published
lang: zh
version: 1.0
source_commit: af25f02cbd24fc44d0610c7a5841b21c24242c85
synapse_version: 3.0.0
published_at: 2026-04-24
updated_at: 2026-04-24
author: knowledge_engineer
review_by: [execution_auditor]
audience: [all]
stale_after: 2026-10-24
---

# Synapse 方法论 — Harness Engineering 实践指南

> **Synapse** 是一套 AI 协作运营体系。
> 命名源自"突触"— 神经元之间传递信号的关键节点，
> 象征知识、决策、执行之间的信息流转枢纽。

## 什么是 Harness Engineering

**核心定义**：Harness Engineering 是设计 **环境、约束、反馈循环和基础设施** 以使 AI Agent 在规模化运行中保持可靠性的工程实践。

**核心公式**：

```
Agent = Model + Harness
```

- **Model**：AI 大模型本身（如 Claude Opus/Sonnet）
- **Harness**：模型之外的一切 — 配置、规则、流程、约束、状态管理、反馈机制

**行业背景**：

- 2026 年被 Martin Fowler、Red Hat 等权威确认为 AI 工程新范式
- 竞争优势不在于谁的模型最大，而在于谁的 Harness 最有效
- 核心转变：从 Prompt Engineering → **Context Engineering** → **Harness Engineering**

---

## Harness 的两大核心机制

### Guides（前馈控制）

**定义**：在 Agent 行动之前，预先引导其行为方向。

| Synapse 实践 | Harness 概念 | 作用 |
|-----------|-------------|------|
| `CLAUDE.md` | Configuration Guide | 定义角色、规则、流程、约束 |
| `organization.yaml` | Organization Context | 团队架构、路由规则、能力矩阵 |
| `decision_rules.yaml` | Constraint System | 四级决策规则、权限边界 |
| `*_experts.yaml` | Agent Backstory | 专家角色定义、能力描述 |
| `HR/personnel/*.md` | Capability Registry | 每个 Agent 的能力档案 |
| `daily-intelligence-prompt.md` | Task Guide | 任务级执行指南 |

### Sensors（反馈控制）

**定义**：在 Agent 行动之后，观察结果并帮助其自我修正。

| Synapse 实践 | Harness 概念 | 作用 |
|-----------|-------------|------|
| QA + 智囊团审查 | Evaluation Sensor | 质量门禁、目标达成检查 |
| `execution_chain_check()` | Process Sensor | 执行链完整性检查 |
| `decision_log.json` | Decision Sensor | 决策日志、误判追踪 |
| `active_tasks.yaml` | State Sensor | 跨会话状态恢复 |
| `_analyze_and_adjust()` | Feedback Loop | 误判分析、关键词自动调整 |
| 情报行动管线评审 | Expert Review Panel | 多专家评分制评审 |

---

## Synapse 架构全景

```
┌─────────────────────────────────────────────────────────────┐
│                    Synapse Architecture                       │
│                                                              │
│  ┌──────────── Guides (前馈) ────────────┐                  │
│  │                                        │                  │
│  │  CLAUDE.md          角色/规则/流程      │                  │
│  │  organization.yaml  团队/路由/能力      │                  │
│  │  decision_rules.yaml 决策约束          │                  │
│  │  *_experts.yaml     Agent定义          │                  │
│  │  HR/personnel/      能力档案           │                  │
│  │                                        │                  │
│  └────────────────────────────────────────┘                  │
│                          ↓                                   │
│              ┌─────────────────────┐                         │
│              │   Model (Claude)    │                         │
│              │   + AI CEO          │                         │
│              └─────────────────────┘                         │
│                          ↓                                   │
│  ┌──────────── Sensors (反馈) ───────────┐                  │
│  │                                        │                  │
│  │  QA审查              质量门禁          │                  │
│  │  execution_chain_check 流程检查        │                  │
│  │  decision_log.json    决策追踪         │                  │
│  │  active_tasks.yaml    状态管理         │                  │
│  │  评审评分制           专家共识          │                  │
│  │                                        │                  │
│  └────────────────────────────────────────┘                  │
│                                                              │
│  ┌──────────── Automation (自动化) ──────┐                  │
│  │                                        │                  │
│  │  每日情报日报         定时Agent         │                  │
│  │  情报行动管线         评估→执行→报告    │                  │
│  │  跨会话恢复           状态持久化        │                  │
│  │                                        │                  │
│  └────────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 与 Anthropic "三 Agent 架构" 的对照

Anthropic 发布的标准三 Agent Harness 架构：

| Anthropic 架构 | Synapse 对应 | 增强点 |
|---------------|--------------|--------|
| Planning Agent | Graphify 智囊团 | 多视角分析，非单一规划 |
| Generation Agent | 执行团队（多团队） | 按领域专业化分工 |
| Evaluation Agent | QA + 智囊团审查 | 量化评分制（85/100 通过线） |
| — | 执行审计师 | **增强**：流程合规守护 |
| — | 四级决策体系 | **增强**：权限分级管控 |
| — | 情报行动管线 | **增强**：自动化闭环执行 |

---

## Context Engineering 实践

**核心理念**：把仓库本身作为单一事实来源。

Synapse 的上下文生态：

```
项目级上下文    → CLAUDE.md（Harness 配置）
组织级上下文    → organization.yaml（团队架构）
决策级上下文    → decision_rules.yaml（规则约束）
角色级上下文    → HR/personnel/*.md（能力档案）
任务级上下文    → active_tasks.yaml（当前状态）
知识级上下文    → obs/（知识库完整体系）
情报级上下文    → daily-intelligence/（每日技术动态）
```

**关键原则**：所有决策知识沉淀到仓库，而非记在人脑子里。

---

## 适用场景

本方法论适用于：

1. 使用 Claude Code + Multi-Agent 管理工作的团队
2. 需要 AI Agent 可靠、可预测运行的场景
3. 希望从"AI 助手"升级为"AI 团队"的组织
4. 需要将 AI 工作流程制度化、可复制的企业

---

## 参考资料

- [Martin Fowler - Harness Engineering](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html)
- [Red Hat - Structured Workflows for AI-Assisted Development](https://developers.redhat.com/articles/2026/04/07/harness-engineering-structured-workflows-ai-assisted-development)
- [InfoQ - Anthropic Three-Agent Harness](https://www.infoq.com/news/2026/04/anthropic-three-agent-harness-ai/)
- [Epsilla - Harness Engineering: Shift from Models to Agent Control Systems](https://www.epsilla.com/blogs/2026-03-12-harness-engineering)
