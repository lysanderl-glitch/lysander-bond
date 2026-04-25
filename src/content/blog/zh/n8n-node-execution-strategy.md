---
title: "n8n 节点执行策略"
slug: n8n-node-execution-strategy
description: "深入理解 n8n 的 executeOnce 配置"
lang: zh
hasEnglish: true
pillar: ops-practical
priority: P3
publishDate: 2026-04-04
author: content_strategist
keywords:
  - "n8n"
  - "工作流"
---
n8n 的节点执行逻辑和传统编程不同。理解 `executeOnce` 是掌握 n8n 工作流开发的关键。

## 核心概念：节点执行次数

n8n 的数据在节点间传递时以 **items** 为单位。当上游节点输出多个 items 时，
       下游节点默认会对每个 item 执行一次。

示例

"Get All Users" 节点返回 10 个用户 → 下游的 "Create Task" 节点会执行 10 次

## executeOnce 的作用

当你设置 `executeOnce: true` 时，节点只执行一次，不管上游传来多少 items。
        这在你只需要"第一个"或"汇总"数据时非常有用。

配置示例

在节点设置中勾选 "Execute Once" 选项即可

## 数据引用语法

在 n8n 表达式中引用上游节点数据：

| 语法 | 含义 |
| --- | --- |
| $('NodeName').first().json.field | 取第一个 item 的字段 |
| $('NodeName').item.json.field | 取当前 item 的字段 |
| $('NodeName').all() | 获取所有 items |

## 链式连接

使用 `.to()` 方法链式连接节点，让代码更简洁。

## 实际工作流示例

创建一个 Asana 任务并通知 Slack：

1. Get All Users (executeOnce: false) → 返回所有用户
2. Extract Lysander ID (executeOnce: true) → 只取 Lysander
3. Create Asana Task → 使用提取的 User ID 创建任务
4. Send Slack Notification → 发送完成通知

## 调试技巧

- 双击节点查看输入/输出数据
- 使用 `Code` 节点打印中间变量
- 开启 "Test workflow" 逐步执行，观察每个节点的数据变化
