---
title: "构建AI团队协作体系：让Obsidian成为第二大脑"
slug: aiobsidian
description: "分享如何用Obsidian构建AI团队协作体系，实现HR知识库自动化、决策体系代码级强制执行、Harness Engineering错误自愈。附完整开源体系和实施指南。"
lang: zh
hasEnglish: true
pillar: ops-practical
priority: P3
publishDate: 2026-04-09
author: content_strategist
keywords:
  - "AI"
  - "团队协作"
  - "Obsidian"
  - "自动化"
---
当我把Obsidian作为第二大脑后，一直在思考一个问题：如何让这个"大脑"不仅管理知识，还能管理团队？
        如何让AI Agent团队像真实团队一样协作，而不是一堆分散的工具？

经过半年的演进，我构建了一套完整的AI团队协作体系。本文将完整分享这套体系的架构、实现和使用方法。

## 核心理念：Obsidian作为唯一数据源

传统做法是维护多份数据：OBSidian一份、YAML配置一份、代码里又一份。问题是：改了一处，其他地方就过时了。

我采用的方案是：**Obsidian作为唯一数据源（SSOT）**，所有配置从这个源头自动派生。

核心架构：

```
OBSidian人员卡片（.md）
        ↓
    hr_watcher.py（inotify监控）
        ↓
    hr_base.py（同步引擎）
        ↓
    *_experts.yaml（Agent配置）
        ↓
    CrewAI（多Agent执行）
```

## 角色层级：清晰的决策边界

```
┌─────────────────────────────────────┐
│         总裁（用户）— 最高决策者        │
└─────────────────────────────────────┘
                    ↑
                    │ 战略/重大决策
                    │
┌─────────────────────────────────────┐
│      Lysander CEO — AI分身/CEO        │
│      （日常管理 + 决策执行）          │
└─────────────────────────────────────┘
                    ↑
                    │ 分析/方案
                    │
┌─────────────────────────────────────┐
│        Graphify 智囊团                │
│   战略分析师 | 关联发现 | 趋势洞察   │
└─────────────────────────────────────┘
                    ↑
                    │ 执行
                    │
┌─────────────────────────────────────┐
│   Butler | RD | OBS | Content_ops    │
│       5个执行团队，共29个AI专家      │
└─────────────────────────────────────┘
```

**关键设计**：总裁只做"重大决策"，日常管理全部由Lysander+智囊团完成。
        决策通过代码级强制执行，而非依赖个人自律。

## 决策体系：代码级强制执行

传统的原则是"写在文档里让人遵守"，结果是所有人都知道原则，但所有人都违反。
        我的解决方案是：把决策原则写成代码。

### 决策检查流程

            1

**小问题** → 直接执行，无需询问

            2

**需智囊团** → 召集分析，批准后执行

            3

**代码审计** → QA检查后才能执行

            4

**超出授权** → 上报总裁

## 技术实现

### HR知识库

人员卡片存在Obsidian中：

```
obs/01-team-knowledge/HR/personnel/rd/tech_lead.md

---
title: 研发团队技术负责人
specialist_id: tech_lead
team: rd
role: 研发团队技术负责人
domains:
  - 技术架构
  - 系统设计
capabilities:
  - 系统架构设计
  - AI Agent系统设计
availability: available
召唤关键词: [研发, 技术, 架构]
---
```

### 自动化同步

hr_watcher.py 监控文件变化，自动同步：

```
# 监控OBS变化 → 自动同步到YAML
python3 hr_base.py sync

# 结果：
✓ butler: 7 agents
✓ rd: 5 agents
✓ obs: 4 agents
✓ graphify: 4 agents
✓ stock: 5 agents
```

### 执行链机制

任务完成后自动执行后续步骤：

```
TASK_EXECUTION_CHAIN = &#123;
    "同步OBS人员卡片到YAML": ["构建网站"],
    "构建网站": ["发布博客文章"],
    "发布博客文章": [],
&#125;

# 执行效果：
$ python3 hr_base.py sync
同步完成: 成功 6, 失败 0
🔗 检测到后续任务链: 构建网站
```

## Harness Engineering：错误自动修复

同类错误不能出现两次。每次犯错，都要花时间设计解决方案确保永远不再犯。

| 错误 | 原因 | 固化方案 |
| --- | --- | --- |
| 直接cp导致编码错误 | 未用发布脚本 | 强制使用harness-daily-publish.sh |
| Python语法错误 | pre_execution_check未执行 | 代码审计关键词触发检查 |
| 原则失效 | 无系统级强制执行 | decision_check()代码级判断 |

## 团队配置：29个AI专家

| 团队 | 专家数 | 职责 |
| --- | --- | --- |
| Graphify | 4 | 第二大脑/深度分析 |
| Butler | 7 | 项目交付/IoT |
| RD | 5 | 技术研发 |
| OBS | 4 | 知识管理 |
| Content_ops | 4 | 内容运营 |
| Stock | 5 | 股票交易系统 |

## 开源体系：可分享的完整方案

我把这套体系打包分享，放在GitHub上。新同事clone后即可使用。

仓库地址：

```
https://github.com/lysanderl-glitch/synapse
```

快速开始：

```
# 1. Clone
git clone https://github.com/lysanderl-glitch/synapse.git
cd synapse

# 2. 安装
cd agent-butler/scripts
bash setup.sh

# 3. 启动Claude Code
claude

# 4. 开始使用
lysander 查看RD团队状态
lysander 同步HR知识库
```

### 体系结构

```
agent-butler/
├── scripts/              ← 一键安装脚本
│   ├── setup.sh          ← 核心安装脚本
│   └── sync-claude-memory.sh
│
├── agent-butler/         ← Agent核心
│   ├── hr_base.py        ← HR知识库+决策体系
│   ├── hr_watcher.py     ← 文件监控
│   └── config/           ← 配置文件
│       ├── organization.yaml
│       └── *_experts.yaml
│
└── docs/                 ← 文档
    ├── ARCHITECTURE.md
    ├── DECISION_SYSTEM.md
    └── CLAUDE_CODE.md
```

## 核心价值

### 知识自动化

OBSidian修改 → 自动同步到所有配置，无需手动维护多份数据

### 决策强制执行

原则变成代码，而非写在文档里靠人自觉遵守

### 错误自愈

Harness Engineering：同类错误永不重复

### 可分享

新同事clone即可使用，无需复杂配置

## 总结

这套体系的核心是：**把管理原则写成代码**，让AI自动遵守，而非依赖人的自觉。

当Obsidian成为第二大脑，当AI Agent团队像真实团队一样协作，当"原则"变成"代码"——
        我们不是在用工具，我们是在构建一个真正能自我运转的组织。

### 体系核心文件

- **hr_base.py** — HR知识库 + 决策体系核心
- **hr_watcher.py** — 文件监控自动同步
- **decision_check()** — 代码级决策检查
- **TASK_EXECUTION_CHAIN** — 执行链自动执行

仓库：[lysanderl-glitch/synapse](https://github.com/lysanderl-glitch/synapse)
