---
title: "给 AI 工作流设计输出路径规则：为什么临时修复是系统债务"
description: "从「文件写错目录」这个小事故出发，讲清楚 AI Agent 输出治理应该以规则驱动而非事后补救"
date: 2026-04-30
publishDate: 2026-04-30T00:00:00.000Z
slug: ai-workflow-output-path-governance
lang: zh
hasEnglish: true
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

<div class="tl-dr"><ul>
  <li>一次文件写错目录的小事故，暴露了 AI 输出路径缺乏规则治理的深层问题</li>
  <li>事后打补丁 ≠ 修复，每次临时修复都在积累系统债务</li>
  <li>输出路径应该由显式规则驱动，而非靠 AI 自行"猜"</li>
  <li>规则设计的核心：约束优先于自由，声明优先于纠错</li>
  <li>本文给出一套可直接套用的输出路径规则设计思路</li>
</ul></div>

<h2>从一个文件写错目录说起</h2>

<p>三周前，我们的一个 AI Agent 工作流在处理客户报告时，把生成的 PDF 文件写进了 <code>/tmp/output/</code> 而不是约定的 <code>/reports/client/</code>。这件事本身不大——文件没丢，手动移过去就行了。但当我去查日志时，发现这不是第一次：过去 47 天里，同类路径写错的情况发生了 9 次，其中 3 次被用户发现，另外 6 次是在例行审计时才找到的。</p>

<p>9 次里面，我们内部的处置方式是：移文件、在 Slack 里提一句"记得检查路径"、然后继续。没有人系统性地问过：为什么 AI Agent 每隔几天就会在这里出错？我们只是在不断地做同一件事——事后补救。这让我意识到，我们在做的不是修复，是在给系统喂债务。</p>

<h2>为什么这个问题比看起来难排查</h2>

<p>我们一开始以为这是 Prompt 写得不够精确的问题——只要把输出路径写进系统提示，Agent 就会老老实实地执行。但实际上，问题根本不在 Prompt 的措辞上。</p>

<p>真正的问题是：Agent 的输出路径决策发生在执行链的哪个环节，完全不透明。当工作流触发时，Agent 会基于上下文、任务类型、甚至当前对话历史来"推断"应该写到哪里。在大多数情况下，这个推断是对的。但在以下几种情况下，它会偏移：</p>

<ul>
  <li>任务描述里包含了模糊的"临时"、"草稿"等词，Agent 倾向于写临时目录</li>
  <li>前一个任务的输出路径作为上下文被带入，导致路径"继承"了错误</li>
  <li>工作流并发执行时，不同实例之间路径参数没有严格隔离</li>
</ul>

<p>每次出错后我们的修复方式——在 Prompt 里加一行"请确保输出到正确目录"——实际上是在用自然语言约束来对抗一个结构性问题。自然语言约束本质上是软约束，Agent 可以遵守，也可以在某些条件下绕过。这就是为什么补丁永远修不干净：你修的是表面，根没有动。</p>

<div class="callout callout-insight"><p>每一次「手动移文件+口头提醒」的处置，都是在用人力成本掩盖系统设计的缺口。这个缺口不会因为你移了文件而消失，它只是在等待下一次触发。</p></div>

<h2>根因：输出路径没有被当作一等公民来设计</h2>

<p>根因很清晰：我们把输出路径的决策权交给了 Agent，但没有给它配套的硬约束机制。这在设计上是一个错误——不是 Agent 的错，是我们的错。</p>

<p>正确的做法是：输出路径应该由工作流层的规则来声明和强制，Agent 只负责内容生成，不负责路径决策。用一个类比来说：你不会让一个实习生自己决定把文件归档到哪个客户文件夹，你会给他一张明确的归档规则表。</p>

<p>下面是我们重新设计后的输出路径规则配置片段，用 YAML 声明，在工作流初始化时加载：</p>

<pre><code class="language-yaml">output_routing:
  default_base: "/reports"
  rules:
    - condition: task_type == "client_report"
      destination: "/reports/client/{client_id}/{YYYY-MM}/"
      filename_pattern: "{task_id}_report.pdf"
      on_conflict: "version_suffix"

    - condition: task_type == "internal_draft"
      destination: "/reports/internal/drafts/"
      filename_pattern: "{task_id}_draft_{timestamp}.md"
      on_conflict: "overwrite"

    - condition: task_type == "temp_processing"
      destination: "/tmp/agent_workspace/{session_id}/"
      ttl_hours: 24
      auto_cleanup: true

  fallback:
    destination: "/reports/unclassified/"
    alert: true
    notify_channel: "ops-alerts"
</code></pre>

<p>这个配置做了几件关键的事：</p>

<ol>
  <li><strong>路径决策与内容生成解耦</strong>：Agent 只返回内容和 <code>task_type</code>，路径由规则引擎计算，Agent 无法覆盖</li>
  <li><strong>fallback 带告警</strong>：当没有规则匹配时，文件不会神秘地消失，而是写入 <code>/reports/unclassified/</code> 并触发 <code>ops-alerts</code> 通知</li>
  <li><strong>临时目录有生命周期</strong>：<code>ttl_hours: 24</code> 和 <code>auto_cleanup: true</code> 确保临时文件不会在 <code>/tmp</code> 里永久堆积</li>
  <li><strong>冲突策略显式声明</strong>：<code>on_conflict</code> 字段避免了静默覆盖或静默失败这两种最难调试的情况</li>
</ol>

<p>在 n8n 工作流的实现里，这对应于在 Agent 节点的下游加一个专门的"路径解析"函数节点，而不是把路径逻辑塞进 Agent 的系统提示里。两者在日常运行中看起来效果差不多，但在出错时，前者给你一个清晰的错误栈，后者给你一个困惑的 AI 输出。</p>

<h2>可移植的原则</h2>

<div class="callout callout-insight"><p>如果你在设计 AI Agent 的任何输出行为，把「输出目标」当作配置，而不是当作指令。配置是代码，指令是期望——你能 review 代码，但你没法 review 期望。</p></div>

<ol>
  <li>
    <strong>如果你在给 Agent 写系统提示时提到了具体路径</strong>，把它移出 Prompt，改为在工作流层通过变量或配置文件注入。Prompt 里的路径是软约束，配置里的路径是硬约束。
  </li>
  <li>
    <strong>如果你的工作流出现过「文件找不到」或「文件写错地方」</strong>，在修复之前先问：这个路径决策是在哪一层做的？如果答案是"在 Agent 的推理里"，那你需要的不是更好的 Prompt，而是一个路径路由层。
  </li>
  <li>
    <strong>如果你在用 n8n 或类似工具构建 AI 工作流</strong>，给每一种输出类型设计一个显式的 fallback 路径，并配上告警。没有 fallback 的输出路由就像没有 catch 的 try 块——它在大多数时候没问题，但它出问题的时候你不会知道。
  </li>
  <li>
    <strong>如果你的团队已经有过临时补丁</strong>（比如"记得手动检查"、"每周例行审计"），把这些补丁的人力成本加起来。通常这个数字足以说服你把规则系统做进去，而不是继续靠人力兜底。
  </li>
  <li>
    <strong>如果你的 AI 工作流跑在并发场景下</strong>，路径规则里必须包含 session 或 task 级别的隔离变量（比如上面配置里的 <code>{session_id}</code> 和 <code>{task_id}</code>）。并发场景下的路径冲突是最难复现的一类 bug。
  </li>
</ol>

<h2>后记</h2>

<p>我们那 9 次写错目录的事故，在引入路径路由层之后，过去三周归零了。但我更在意的是另一件事：以前每次出错，我们的反应是"谁来移一下文件"；现在出错，<code>ops-alerts</code> 会告诉我们具体是哪条规则没有匹配到，原因是什么。这个变化不只是减少了人力，它让系统变得可以被推理——你知道问题出在哪，你知道怎么修，你知道修完之后会发生什么。如果你的 AI 工作流里也有类似的"靠人眼定期检查"的环节，我很想知道你们是怎么处理的，欢迎在评论里聊。</p>
