---
title: "Asana + Slack + n8n 自动化"
slug: asana-slack-n8n-automation
description: "完整的项目管理自动化方案"
lang: zh
hasEnglish: false
pillar: ops-practical
priority: P3
publishDate: 2026-04-03
author: content_strategist
keywords:
  - "Asana"
  - "Slack"
  - "n8n"
---
分享我搭建的项目管理自动化方案：项目启动时自动创建工序任务，前置完成后自动通知下一步负责人。

## 整体架构

```
┌──────────────┐     ┌─────────────────┐     ┌────────────────┐
│  知识库 Git   │────▶│  工作流 A        │────▶│     Asana      │
│  工序表文件   │     │  项目启动        │     │  创建工序任务   │
└──────────────┘     └────────┬────────┘     └────────────────┘
                              │ Asana Webhook
                              ▼
                       ┌─────────────────┐     ┌────────────────┐
                       │  工作流 B        │────▶│     Slack      │
                       │  工序完成提醒    │     │  项目专用频道   │
                       └─────────────────┘     └────────────────┘
```

## 核心组件

### Asana

任务管理、负责人分配、依赖关系

### Slack

实时通知、项目频道沟通

### n8n

工作流引擎、自动化编排

## 工序表设计

工序表存储在知识库中（CSV 格式），包含：

```
序号,工序名称,负责人邮箱,持续时间(天),前置工序序号,Slack频道
1,需求确认,lysander@janusd.com,1,,#proj-alpha
2,UI设计,andrey@janusd.com,3,1,#proj-alpha
3,前端开发,wissame@janusd.com,5,2,#proj-alpha
4,后端开发,michaelb@janusd.com,5,2,#proj-alpha
5,系统集成,lysander@janusd.com,2,"3,4",#proj-alpha
6,测试验收,andrey@janusd.com,3,5,#proj-alpha
7,部署上线,lysander@janusd.com,1,6,#proj-alpha
```

## 工作流 A：项目启动

触发时机：Asana 中「项目启动」任务被创建

```
Asana Trigger
  → 解析任务信息
  → 读取工序表（HTTP Request）
  → 解析CSV
  → 批量查询用户ID（转换为 Asana User ID）
  → 循环创建任务（executeOnce: false）
  → 批量设置依赖（Code 节点 + HTTP Request）
  → 创建Slack频道
```

## 工作流 B：工序完成提醒

触发时机：Asana 任务 completed 字段变为 true

```
Asana Trigger（监听任务更新）
  → IF(完成 && 是工序任务)
  → 获取任务详情
  → 查询下游依赖任务
  → 获取负责人
  → 发送 Slack 通知（Block Kit 格式）
```

## 关键配置要点

### 1. executeOnce 的使用

循环创建任务时，executeOnce 必须设为 false。

          而查询 Lysander 的 User ID 时，executeOnce 设为 true。

### 2. 依赖设置

通过 Code 节点构建依赖映射，然后调用 Asana API：

          `POST /tasks/&#123;gid&#125;/addDependencies`

### 3. Slack 频道命名

格式：#proj-&#123;项目标识&#125;

          在 Asana 任务的 notes 字段存储 SLACK_CHANNEL 映射

## 效果

- 项目启动只需在 Asana 创建一个任务
- 所有工序自动创建、分配负责人
- 工序完成自动通知下一步负责人
- Slack 频道记录完整项目沟通历史
