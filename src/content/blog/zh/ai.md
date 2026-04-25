---
title: "从原则失效到自动化决策：AI决策体系的构建之路"
slug: ai
description: "如何通过代码级强制机制解决团队协作中"
lang: zh
hasEnglish: true
pillar: ops-practical
priority: P3
publishDate: 2026-04-09
author: content_strategist
keywords:
  - "AI"
  - "决策系统"
  - "自动化"
  - "产品笔记"
---
我们建立了一套沟通决策原则，核心是：统筹执行时先做目标强化和团队共识；策略方案需经智囊团确认才能执行；决策问题第一时间组织执行团队+智囊团的决策会议，批准后直接执行，无需上报。

然而现实是：原则明确写在文档里，但每次执行时还是习惯性地问Lysander。这个问题反复出现，像是一个永远修不好的bug。

## 问题的本质

战略分析师（strategist）用SWOT框架一针见血地诊断出这个问题：

### Strengths（优势）

原则已明确文字化，全员知晓

### Weakness（弱点）

无系统级强制执行机制

### Opportunities（机会）

可通过代码/流程实现自动化

### Threats（威胁）

习惯性违反成为"自然"状态

关联发现专家（relation_discovery）找到了更深层的因果链：

> "等待反馈" → 触发点是内心的不确定感 → 根因是没有预设决策路径 → 根本原因是原则缺少执行触发机制
> — 关联发现专家

趋势洞察师（trend_watcher）通过历史回溯，发现了一个循环模式：

建立原则 → 执行时违反 → 反思 → 再次建立原则 → 再次违反 → ...

问题本质：依赖个人自律而非系统约束

## 解决方案：代码级决策检查

决策顾问（decision_advisor）给出了关键洞见：

> 原则是"建议"而非"规则"——这是问题的核心。要让原则被遵守，必须让它成为执行流程的一部分，而非独立存在的文档。
> — 决策顾问

最终方案是在 hr_base.py 中嵌入决策前检查清单：

### 决策前检查流程

            1

是否为**小问题**？

→ 风险可控、有明确执行路径 → 直接执行，不询问

            2

是否需要**智囊团决策**？

→ 召集分析 → 批准后 直接执行，不询问

            3

是否**超出授权**？

→ 上报Lysander CEO

### 小问题的边界定义

以下情况判定为"小问题"，直接执行：

- **纯技术实现细节**：工具选择、配置调整等
- **已有明确流程的例行操作**：同步、查询、状态获取
- **不影响核心架构的微调**：风险可控
- **有明确执行路径**：不需要方案设计

## 技术实现

核心函数 decision_check() 在 hr_base.py 中实现：

```
# 小问题定义：风险可控、不影响核心架构、有明确执行路径
_SMALL_PROBLEM_KEYWORDS = [
    "同步", "sync", "生成yaml", "加载", "查询",
    "显示", "列出", "查看", "获取状态",
    "组装团队", "召唤", "路由",
]

# 需要智囊团决策的关键词
_THINK_TANK_KEYWORDS = [
    "新架构", "新方案", "策略调整", "原则修改",
    "自动化方案", "决策体系", "流程变更",
]

def decision_check(task_description: str, context: str = "default") -> dict:
    """决策前检查清单 - 系统级强制执行"""
    task_lower = task_description.lower()

    # [1] 小问题 → 直接执行
    if _is_small_problem(task_description):
        return &#123;
            "decision": "small_problem",
            "reasoning": "属于小问题范围",
            "action": "直接执行，无需询问"
        &#125;

    # [2] 需要智囊团 → 召集分析
    for kw in _THINK_TANK_KEYWORDS:
        if kw in task_lower:
            return &#123;
                "decision": "think_tank",
                "reasoning": f"涉及【&#123;kw&#125;】，需要智囊团分析",
                "action": "召集智囊团分析和决策"
            &#125;

    # [3] 超出授权 → 上报
    ...
```

## 效果对比

| 场景 | 之前 | 之后 |
| --- | --- | --- |
| 同步OBS卡片 | 问Lysander确认 | 直接执行 |
| 分析项目风险 | 问Lysander怎么处理 | 智囊团决策后执行 |
| 新架构方案 | 问Lysander要方案 | 智囊团分析+决策体系 |
| 战略规划 | 问Lysander | 上报CEO（正确路径） |

## 引入Harness Engineering

决策体系建立后，智囊团进一步提出：如何避免同类错误重复发生？如何让决策系统自我进化？

趋势洞察师（trend_watcher）指出了另一个问题：

> 执行完成后，我们习惯性地问"是否需要继续"——这是条件反射，不是决策。
> — 趋势洞察师

最终方案是引入Harness Engineering的反馈环机制，建立**执行后自动评估**和**任务链自动执行**机制：

### Harness反馈环

**record_decision()** — 每次决策自动记录

**record_feedback()** — 记录Lysander反馈（正确/误判/介入）

**post_execution_evaluate()** — 执行后自动评估，判断是否需要Lysander

**evaluate_and_execute_chain()** — 自动执行后续任务链

### 执行链机制：消除条件反射

核心问题：任务完成后，为什么会习惯性询问Lysander？因为**执行后没有自动评估机制**。

之前：任务A完成 → 问Lysander"是否继续" → 等待 → 执行任务B

          现在：任务A完成 → post_execution_evaluate() → 自动执行任务B

任务链定义：

| 任务 | 后续任务 | 执行者 |
| --- | --- | --- |
| 同步OBS人员卡片到YAML | 构建网站 | rd |
| 构建网站 | 发布博客文章 | content_ops |
| 发布博客文章 | (结束) | — |

执行效果：

```
$ python3 hr_base.py sync
同步完成: 成功 6, 失败 0

📋 执行后评估: 任务执行成功，无需Lysander
   行动: 任务完成

🔗 检测到后续任务链 (1 个任务)
   → 构建网站 (执行者: rd)
```

### 代码审计机制

另一个发现：涉及代码/脚本编写的任务，容易出现语法错误等低级问题影响健壮性。

解决方案：对代码相关任务强制触发QA审计流程：

**require_code_review** — 代码/脚本/实现类任务

**pre_execution_check()** — 执行前Python语法+依赖检查

**审计团队** — qa_engineer, tech_lead

```
# 代码审计关键词
_CODE_REVIEW_KEYWORDS = [
    "脚本", "代码", "实现", "修改代码", "编写",
    "harness", "workflow", "自动化脚本",
]

# 测试结果
✅ 同步OBS人员卡片    → small_problem（直接执行）
🔍 编写一个新的脚本   → require_code_review（QA审计）
🔍 修改hr_base.py代码 → require_code_review（QA审计）
```

## 核心洞见

> 当一个问题反复出现而无法根治时，往往不是因为人的意志力不够，而是因为系统设计缺少了"强制执行点"。
> — 这次解决问题的关键认知

建立原则和建立执行机制是两件事。前者靠沟通和文档，后者必须靠代码和流程。当我们把"是否应该问Lysander"这个问题，转化为"这个问题属于哪个决策类型"的自动判断时，原则就从一个需要记忆的规则，变成了一个被系统强制执行的流程。

### 自动化决策体系

- ✅ 小问题：代码级判断 → 直接执行
- ✅ 智囊团决策：自动召集 → 批准后执行
- ✅ 超出授权：清晰路径 → 上报CEO
- ✅ 代码审计：QA强制检查 → 执行
- ✅ Harness反馈：误判记录 → 自我修复
- ✅ 执行链：任务完成 → 自动执行后续步骤
- ✅ 效果：原则变成系统约束，而非个人自律

相关系统：[Claude Code](https://github.com/anthropics/claude-code) ·
        [CrewAI](https://github.com/crewai/crewai) ·
        [Obsidian](https://obsidian.md)
