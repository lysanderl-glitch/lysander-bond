---
title: "产品管线的知识新鲜度问题：为什么每天2AM要跑一次全局更新"
description: "从「涉及产品线时需要重新整理信息」的痛点出发，阐述产品知识自动化更新机制的设计逻辑"
date: 2026-04-29
publishDate: 2026-04-29T00:00:00.000Z
slug: product-pipeline-knowledge-freshness
lang: zh
hasEnglish: true
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

```html
<div class="tl-dr"><ul>
  <li>Agent 读取产品知识时，文件可能已过时 1-3 天</li>
  <li>2AM 全局更新是对"知识衰减"的主动防御机制</li>
  <li>Agent Memory 不自动追踪变更，需显式重建索引</li>
  <li>根因：知识写入分散在各 Agent，读取却集中于全局视图</li>
  <li>未更新的代价：每次涉产品线任务都要人工重整背景信息</li>
</ul></div>

<h2>问题背景</h2>

<p>Synapse 是一套多智能体操作系统，核心设计是把产品知识、决策历史、执行结果沉淀到一个二脑知识库（OBS）里，让所有 Agent 在执行任务前读取上下文再行动。系统目前跑着 4 条并行产品管线，每天平均产生 8-12 条决策记录、若干任务状态变更、以及各 Agent 的执行学习笔记。乍看起来，这是一套设计良好的"知识自增长"系统——写的人多、写的频繁，知识库应该越来越饱满。</p>

<p>问题在 2026 年 5 月初集中暴露。在处理一个 PMO Auto 产品线任务时，Agent 给出的方案明显滞后——它引用的"近期学习"里没有三天前刚刚处理过的同类问题的经验，最终走了一段弯路。翻查日志，<code>obs/01-team-knowledge/HR/agent-memory/janusd_pm-memory.md</code> 的最后修改时间是 72 小时前。知识在增长，但分布在各处的片段没有被重新整合成可用的全局视图。</p>

<h2>为什么这个问题难发现</h2>

<p>我们一开始以为是 Agent prompt 的问题——Agent 没有被明确指示去读最新的 memory 文件。于是调整了 dispatch 模板，加了"读取 <code>recent_learnings</code> 并注入"的硬性要求。效果有一些改善，但任务质量依然时好时坏，找不到规律。又猜是 Agent 读文件的顺序不对，调整了读取链路，还是无法稳定复现。</p>

<p>实际上问题根本不在 prompt 层。即使 Agent 每次都忠实地读取了 memory 文件，读到的也可能是过时内容。核心矛盾是：<strong>知识的写入是事件驱动的（每个 Agent 执行后更新自己的 memory），但知识的读取是批量的（一次任务要拿到所有相关产品线的全局视图）</strong>。两个时序不同步，中间的窗口就是知识的"灰色地带"。更麻烦的是，这类问题不报错、不崩溃，只是让 Agent 的决策质量悄悄变差——典型的 silent degradation，和代码 bug 的排查路径完全不一样。</p>

<h2>根因与 2AM 更新的设计逻辑</h2>

<p>最终把问题定位在三层知识结构的同步断层上：</p>

<ul>
  <li><strong>L1 原始记录</strong>：各 Agent memory 文件（<code>obs/01-team-knowledge/HR/agent-memory/</code>），由各 Agent 在执行后自行写入，更新频率不一</li>
  <li><strong>L2 产品索引</strong>：<code>obs/00-index/product-index.md</code>，汇总各产品线当前状态，依赖 L1 数据</li>
  <li><strong>L3 全局知识图谱</strong>：<code>obs/00-index/knowledge-graph.json</code>，跨产品线关系网络，依赖 L2 数据</li>
</ul>

<p>L1 是分散写入的，L2 和 L3 却没有自动重建的触发器。每次涉产品线的任务进来，系统需要在 [0.5] 阶段读取对应的产品上下文并注入 dispatch prompt，但如果 L2/L3 没有被刷新，这个注入的上下文就是陈旧的。2AM 全局更新是一个"强制同步点"：在业务低谷期重建整个知识索引，保证当天第一个任务拿到的是昨日完整结算后的知识状态。</p>

<pre><code class="language-yaml"># obs/00-index/.last-compiler-run (schema fragment)
last_run: "2026-05-21T02:00:00+04:00"   # Dubai timezone
targets_refreshed:
  - obs/00-index/master-index.md
  - obs/00-index/product-index.md
  - obs/00-index/knowledge-graph.json
  - obs/01-team-knowledge/HR/agent-memory/   # all files under dir
log_ref: logs/obs-compiler.log
status: success
files_updated: 24
files_skipped: 3   # no change detected since last run
</code></pre>

<p>选 2AM 而非凌晨 12 点，原因很具体：Dubai 时区的 Agent 任务高峰在 8-22 点，23:00 以后仍有尾单在结算。2AM 是所有活跃任务基本完成、新一天任务尚未启动的最小干扰窗口。过早跑会漏掉当天最后一批写入，过晚跑会压缩次日第一个任务的准备时间。更新日志落到 <code>logs/obs-compiler.log</code>，<code>obs/00-index/.last-compiler-run</code> 记录最后一次成功运行时间戳，供后续任务判断知识新鲜度。</p>

<div class="callout callout-insight"><p>设计陷阱：健康度检查不能只看 <code>status: success</code>，必须同时验证 <code>files_updated &gt; 0</code>。如果某次跑了 0 更新，可能是数据确实没变（正常），也可能是上游写入链路断了（告警）。两种情况在外观上完全一致，但处理方式截然相反——这是 silent fail 的经典变体。</p></div>

<h2>可移植的原则</h2>

<div class="callout callout-insight"><p>如果你在构建多 Agent 系统，<strong>不要假设分散写入会自动产生全局一致的读视图</strong>。写入是本地的、事件驱动的；读取是全局的、批量的。这之间必须有一个显式的"重建"步骤，无论是触发式还是定时式，都需要被明确设计出来，而不是期待它自然发生。</p></div>

<ol>
  <li>如果你在设计知识库更新策略，<strong>区分"写入时间"和"可读时间"</strong>：一个文件被写入不等于其下游索引已更新；可读时间是下游重建完成后才生效的，两者之间的时间差就是知识的"灰色窗口"。</li>
  <li>如果你遇到 Agent 决策质量随机波动，<strong>先查知识文件的修改时间，再查 prompt</strong>：silent degradation 比报错更难追踪，而知识新鲜度是最常见的沉默根因之一，通常比 prompt 问题更容易被忽视。</li>
  <li>如果你选择定时更新而非触发更新，<strong>把更新窗口选在业务低谷且尾单结算完毕之后</strong>：太早跑会遗漏当天最后一批写入，太晚跑会影响次日第一个任务的上下文质量，两个边界都要明确测量，不能靠直觉拍时间。</li>
  <li>如果你的知识更新是批处理的，<strong>让日志区分"无变化跳过"和"上游断链导致 0 更新"</strong>：两种情况都输出相同的计数，但只有在日志字段上加以区分，监控告警才能真正生效，否则断链会以"一切正常"的形态存在很久。</li>
</ol>

<p>这个问题在系统运行几周后才暴露，因为早期只有 2 条产品管线、知识的"陈旧窗口"不超过 4 小时，任务能容忍。随着管线扩展到 4 条、agent-memory 文件超过 20 个，窗口拉长到 24-72 小时，问题才变得不可接受。如果你正在搭建类似的多产品线 Agent 系统，并且在 <code>logs/obs-compiler.log</code> 里发现了连续多日 <code>files_updated: 0</code> 的记录，那大概率不是系统太稳定，而是写入链路某个环节悄悄断了。</p>
```
