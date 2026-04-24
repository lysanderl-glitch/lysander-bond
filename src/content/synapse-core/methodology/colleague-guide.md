<!-- Auto-generated from synapse@36ab925 on 2026-04-24T17:39:28.209Z; DO NOT EDIT. -->
---
id: colleague-guide
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
audience: [team_partner, technical_builder]
stale_after: 2026-10-24
---

# Synapse 使用指南

> 5 分钟完成初始化，零技术背景可用。

---

## 你将获得什么

- **Synapse** — AI 协作运营体系，37+ AI 专家随时待命
- 说出需求，AI CEO 自动分派给对应专家团队
- 小事直接执行，大事智囊团分析后决策，重大事项才上报
- Obsidian 知识库自动同步 GitHub

---

## 第一步：下载代码

打开浏览器，访问：

```
https://github.com/lysanderl-glitch/synapse
```

点击绿色 **Code** 按钮 → **Download ZIP** → 解压到任意文件夹（如 `桌面/Synapse`）。

---

## 第二步：打开 Claude Code

1. 打开 **Claude Code 桌面应用**
2. 点击 **"Open Folder"**（打开文件夹）
3. 选择刚才解压的 `Synapse` 文件夹
4. 等待 Claude Code 加载完成（看到对话框即可）

> Claude Code 会自动读取 `CLAUDE.md`，AI 团队体系立即生效。

---

## 第三步：发送开场语（复制粘贴）

将以下内容**直接粘贴**到对话框发送：

```
你好，请你按照 CLAUDE.md 中的执行链规范，以 AI CEO 身份问候我，
并告诉我你当前加载的团队成员有哪些。
```

AI CEO 会回复问候语，并列出所有可用的 AI 专家团队。

---

## 第四步：开始工作

直接说出你的需求，系统会自动分派：

| 你说 | 系统行为 |
|------|----------|
| `帮我做一个项目交付方案` | → 交付团队 |
| `帮我分析这个技术架构` | → 智囊团 |
| `帮我写一份项目汇报材料` | → 内容团队 |
| `需要沉淀本次项目经验` | → 知识管理团队 |
| `分析下当前市场竞争态势` | → 增长团队 |

**注意**：每次对话开头带 AI CEO 名称（默认 `Lysander`），系统会识别这是对 AI CEO 发出的指令。

---

## 团队一览

| 团队 | 核心职责 |
|------|----------|
| **Butler** | 项目交付、PMO、UAT测试 |
| **RD 研发** | 系统开发、架构设计、DevOps |
| **OBS 知识管理** | 知识沉淀、检索、质量审核 |
| **Graphify 智囊团** | 战略分析、决策支持、趋势洞察、执行审计 |
| **内容团队** | 文档/报告/提案撰写、视觉呈现 |
| **增长团队** | 客户洞察、GTM策略、竞品分析 |
| **Harness Ops** | 系统工程、配置治理、QA 门禁 |

---

## 常见问题

**Q: Claude Code 怎么下载？**
A: 访问 [claude.ai/download](https://claude.ai/download)，下载桌面版，用 Claude 账号登录。

**Q: 打开文件夹后什么都没有？**
A: 确认选的是 `Synapse` 文件夹本身，而不是它的上级目录。

**Q: 发了消息没有问候语？**
A: 重新打开文件夹，或发送：`请重新加载 CLAUDE.md 并以 AI CEO 身份问候我`

**Q: 想更换 AI 专家的能力怎么做？**
A: 打开 `obs/01-team-knowledge/HR/personnel/` 对应文件，直接编辑 .md 文件即可。

---

## 技术支持

提交 Issue：https://github.com/lysanderl-glitch/synapse/issues
