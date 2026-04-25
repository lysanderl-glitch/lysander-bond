---
title: "AI自动化任务悄悄发消息到公司群：我是怎么发现并堵住这个漏洞的"
slug: ai-automation-slack-channel-boundary-violation
description: "从一次定时任务配置审查意外发现AI助手在向全公司频道广播消息，引出AI自动化权限边界设计的核心问题"
lang: zh
hasEnglish: false
pillar: multi-agent-case
priority: P3
publishDate: 2026-04-22
author: content_strategist
keywords:
  - "问题日志"
  - "AI工程"
  - "Synapse"
---
## 那天我差点没发现：AI 助手正在向全公司广播




上周三下午，我在做一次再普通不过的例行工作——审查我们团队配置的定时任务（Scheduled Agents）。起因只是想优化一下日报生成的时间窗口，顺手点开了一个叫 `daily-intel-digest` 的任务日志。日志第三行让我愣住了：`channel: #general, recipients: 287`。




这是一个面向全公司的 287 人频道。而这个任务，是三周前我自己配置的"AI 情报日报"——我以为它只会发送到 `#bot-sandbox`。过去三周，我们的 AI 助手每天早上 8 点准时向全公司广播了 21 条它自己筛选的"AI 行业动态"。没有人投诉，但也没有人应该收到这些。




### 是怎么走到这一步的




复盘发现问题出在三层叠加。第一层，Webhook URL 是我复制自官方示例的，示例里默认填的是 `#general`，我当时只改了 token 没改 channel。第二层，Slack App 的 OAuth scope 我申请的是 `chat:write`——它允许写入所有公开频道，而不是我以为的"只能写入被邀请的频道"。第三层也是最关键的：AI Agent 在生成发送指令时，被我写了一句看似无害的 prompt："select the most relevant channel for this content"。模型看到 `#general` 在频道列表里、名字最"通用"，于是每天自信地把它选为目标。




三个小缺陷，单独看都不足以触发事故。但在 AI 自动化链路里，它们叠加成了一次持续三周的静默广播。传统 DevOps 里的"最小权限原则"在这里完全没落地——我给 AI 的权限是"可以发消息"，但真正该给的是"可以向某个特定频道发送某类消息"。




### 我是怎么堵住的




修复用了大约两个小时，但设计原则比代码更重要。




第一步，把 `chat:write` 降级为 `chat:write.public` 加上显式的 `channel allowlist`——配置文件里写死三个可发送频道，Agent 选择范围被物理限制在白名单内。第二步，引入"Dry-Run 默认"：所有新注册的定时任务首次运行时只打印 payload 不实际发送，必须我手动 approve 后才切换成真实投递。第三步，加了一个"受众阈值门禁"：任何目标频道超过 50 人的消息，必须经过 `integration_qa` 二次确认，阈值外自动阻断。




### 更深的问题：AI 自动化的"爆炸半径"




这次事故让我重新思考了一个概念：每一个 AI 自动化动作，都有自己的"爆炸半径"（Blast Radius）。传统脚本的爆炸半径是静态可审的——代码里写死了收件人、频道、API endpoint。但 AI Agent 的爆炸半径是动态的——它会根据上下文"智能选择"对象。一个看似无害的 prompt，加上一个过宽的权限 scope，就能把爆炸半径从"一个测试频道"放大到"整个公司"。




我们团队现在给所有 AI 自动化任务强制加了三个元数据字段：`max_recipients`（最大受众数）、`allowed_targets`（白名单目标列表）、`approval_tier`（审批等级）。任何超出阈值的动作自动进入人工审批队列。这套机制上线后，又抓到了两个类似的潜在误发——一个是要把内部财务摘要发到外部客户群的邮件任务，另一个是误把 staging 数据推送到 production dashboard 的同步任务。




## 可复用的四条原则




**1. 默认私密，显式公开。**所有新建的 AI 自动化目标默认是私有频道或个人 DM，要扩大受众必须显式配置并审批。




**2. 分离"起草"和"发送"能力。**让 AI 能生成内容，但发送动作由独立的、权限最小化的 runner 执行——这样 prompt injection 也无法越权。




**3. 把"受众规模"当成一级安全信号。**受众数量跨过某个阈值，就该触发人工门禁，和"调用外部 API 支付金额"同等级处理。




**4. 所有 outbound 动作必须写审计日志。**定期 review 日志中的 `recipients` 和 `target` 字段，比任何 alerting 都更容易提前发现偏移。




AI 自动化的威力在于它能替你做决定，但这正是它需要被约束的原因。我们习惯给人类员工"够用就好"的权限，却经常给 AI Agent 一个全公司 workspace 级别的 admin token——只因为"这样配置起来简单"。这次三周的静默广播提醒我：AI 工程里最危险的 bug，不是崩溃，而是它默默地按错误的语义"正常工作"。




*如果你在构建 AI 工程团队，欢迎参考我们开源的 Synapse 框架——里面沉淀了我们在 AI 自动化权限边界、执行链审计、多 Agent 协作这些具体场景下踩过的坑和对应的治理机制。*
