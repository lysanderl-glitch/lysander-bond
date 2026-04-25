---
title: "Harness Engineering 入门：AI 代理的控制框架"
slug: harness-engineering-guide
description: "深入理解 Harness Engineering——让 AI 代理不再犯同一个错误的工程化方法"
lang: zh
hasEnglish: true
pillar: methodology
priority: P1
publishDate: 2026-04-06
author: content_strategist
keywords:
  - Harness Engineering
  - 约束工程
  - AI Agent
  - Context Engineering
  - Mitchell Hashimoto
---

Mitchell Hashimoto 在 2026 年 2 月提出了一个概念，让 AI 开发者终于有了名字来形容我们一直在做的事——**Harness Engineering**（控制框架工程）。

> 每当代理（Agent）犯错误时，不要只是希望它下次做得更好，而是花时间设计一个解决方案，确保它永远不再犯同样的错误。
>
> — Mitchell Hashimoto

## 为什么需要 Harness Engineering？

当 AI 编码代理承担越来越多软件生命周期的任务时，如何确保它们可靠、可预测、不会反复犯同样的错误？

传统的做法是反复提示（"再试一次"、"注意这个错误"），但这效率低下且不可扩展。Harness Engineering 提供了一种系统化的工程方法：

- **前馈（Feedforward）**：行动前的引导和控制，提高首次成功率
- **反馈（Feedback）**：行动后的观察和修正，支持自我纠错

## 两大控制机制

### 前馈：让代理第一次就做对

前馈控制是在代理行动之前就给予指导，增加首次成功的概率：

- **AGENTS.md**：项目级文档，告诉代理编码规范、架构决策
- **项目引导（Bootstrap Skills）**：标准化的项目初始化流程
- **代码规范（Code Mods）**：自动化的代码转换规则

> **案例：** Ghostty 终端项目通过 AGENTS.md，几乎完全消除了代理的不良行为。

### 反馈：快速修正错误

反馈控制是在代理行动后立即观察结果，支持自动修正：

- **自定义 Linter**：针对项目特定规则的检查
- **定向测试**：筛选特定场景的测试用例
- **截图校验**：视觉回归测试

## 两种执行类型

| 类型 | 特点 | 示例 |
|------|------|------|
| 计算型 | 确定性、毫秒级 | 测试、Linter、类型检查 |
| 推理型 | 非确定性、语义分析 | AI 代码审查、架构检查 |

## 三层调节架构

### 1. 可维护性调节（Maintainability Harness）

结构性检查：重复代码、圈复杂度、风格违规。使用现有工具（ESLint、Prettier）。

### 2. 架构适应性调节（Architecture Fitness Harness）

定义和检查架构特征的 Fitness Functions，确保代码结构符合预期。

### 3. 行为正确性调节（Behavior Harness）

功能规范作为前馈，AI 生成测试套件作为反馈（仍在成熟中）。

## 实战建议

1. **迭代 Harness**：每次问题重复出现时，改进前馈/反馈控制
2. **质量左移**：快速检查放在集成前，昂贵的传感器放在 CI 管道后期
3. **持续监控**：死代码检测、测试覆盖率、运行时 SLO
4. **用 AI 构建 Harness**：代理可以编写结构性测试、生成规则草稿

## 与 Context Engineering 的关系

Martin Fowler 指出：Harness Engineering 是 Context Engineering 在编码代理领域的具体形式。

Context Engineering 提供了让指南和传感器对代理可用的手段，而 Harness Engineering 则是针对编码代理的特定实现。

## 核心要点

- 不要只是"再试一次"——要工程化解决方案
- 好的 Harness 将人类输入引导到最重要的地方
- 前馈 + 反馈 = 快速、高质量的结果
- 用 AI 代理来构建和维护 Harness 本身
