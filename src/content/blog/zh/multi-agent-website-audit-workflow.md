---
title: "AI驱动的网站运维：如何让多智能体团队完成一次全站内容审计"
description: "产品委员会、内容团队、市场团队、智囊团协同完成网站审计的实际流程拆解"
date: 2026-04-29
publishDate: 2026-04-29T00:00:00.000Z
slug: multi-agent-website-audit-workflow
lang: zh
hasEnglish: true
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

<div class="tl-dr"><ul>
  <li>多智能体协作网站审计，4个角色分工明确才能跑通</li>
  <li>产品委员会负责裁决，内容/市场/智囊团各司其职</li>
  <li>最难的不是写agent，是设计"谁拍板"的权限边界</li>
  <li>没有结构化输出约定，跨agent信息传递会静默腐化</li>
  <li>真实跑完一次审计暴露了三个我们没预料到的问题</li>
</ul></div>

<h2>问题背景</h2>

<p>三个月前，我们接到一个内部需求：对 Synapse 官网做一次全站内容审计。网站当时共有 47 个页面，包括产品介绍、案例库、博客、文档入口。问题是，没有一个人记得所有页面的内容状态——有些页面的 CTA 按钮指向已下线的功能，有些案例的数据是 2022 年的，还有几个定价页面在不同入口展示了不一致的描述。手动审计的话，保守估计需要两个人花三到四天。</p>

<p>我们决定用这个场景做一次多智能体系统的实战练习。目标很具体：让 AI 智能体团队完成从"抓取页面"到"输出改稿建议"的完整链路，同时记录下整个流程里哪些环节是真正卡住我们的。这篇文章是那次实验的问题日志，不是成功案例展示。</p>

<h2>为什么这个系统比预想的难搭</h2>

<p>我们一开始以为，这是一个标准的"分工 + 汇总"问题——给每个 agent 分配一块内容，最后汇总到一个地方就行。所以最初的设计是线性的：一个 crawler agent 抓页面，一个 review agent 分析，输出报告。我们大概花了两天把这个版本跑通了，然后发现它没什么用。</p>

<p>实际上，网站内容审计根本不是一个单一维度的判断任务。同一段产品描述，从产品角度看是"准确的"，从市场角度看可能是"太技术化、不适合转化"，从内容角度看可能是"和上个月发的博客逻辑矛盾"。这三个判断都是对的，但优先级谁高谁低，需要有人做裁决。没有裁决机制的多 agent 系统，输出的结果就是一堆互相矛盾的建议，没有人知道下一步该做什么。这是我们真正卡住的地方：不是技术实现，是组织逻辑。</p>

<h2>根因：缺少"产品委员会"这个裁决层</h2>

<p>我们重新设计了整个系统架构，核心变化是引入了四个角色，并明确了它们的权限边界：</p>

<ul>
  <li><strong>产品委员会（Product Committee Agent）</strong>：最终裁决者，持有"接受/拒绝/搁置"三种决策权，负责整合各方意见后输出最终改稿优先级列表</li>
  <li><strong>内容团队（Content Team Agent）</strong>：负责判断表达一致性、品牌语气、与其他内容的逻辑冲突</li>
  <li><strong>市场团队（Marketing Team Agent）</strong>：负责评估转化路径、CTA 有效性、目标受众匹配度</li>
  <li><strong>智囊团（Think Tank Agent）</strong>：负责提出挑战性问题，专门扮演"反对派"，防止另外三个角色陷入一致性偏差</li>
</ul>

<p>关键设计点是：内容团队、市场团队、智囊团的输出全部是"建议"，只有产品委员会的输出才是"决策"。这个权限边界写进了每个 agent 的 system prompt，也体现在结构化输出的字段设计里：</p>

<pre><code class="language-yaml"># agent output schema (simplified)
content_team_output:
  page_id: string
  issues_found:
    - type: "consistency" | "tone" | "logic_conflict"
      description: string
      severity: "low" | "medium" | "high"
      suggestion: string
  recommendation_only: true   # 标记：此输出无决策权

product_committee_input:
  collects_from:
    - content_team_output
    - marketing_team_output
    - think_tank_output
  decision_fields:
    final_action: "accept_as_is" | "revise" | "defer" | "remove"
    priority: 1 | 2 | 3
    assigned_to: string
    rationale: string
</code></pre>

<p>这个 schema 的作用不只是格式约定，它强制每个 agent 在输出时明确自己的"角色身份"。我们在早期版本里没有 <code>recommendation_only: true</code> 这个字段，结果产品委员会 agent 在处理输入时，会把内容团队的"建议"当成"已决策项"直接跳过，静默地丢掉了大量信息。</p>

<p>智囊团的设计是整个系统里最有意思的部分。它的 system prompt 里有一条强制指令：</p>

<pre><code class="language-python"># think_tank_agent system prompt fragment
SYSTEM_PROMPT = """
你是网站审计团队的智囊团成员。你的唯一职责是质疑。

对于每一条来自内容团队或市场团队的建议，你必须：
1. 找出至少一个该建议可能适得其反的场景
2. 提出一个产品委员会在做决策前应该先回答的问题
3. 如果你认为某个问题根本不该被修改，明确说出来并给出理由

你不需要提供解决方案。你的价值在于让其他人慢下来想清楚。
"""
</code></pre>

<p>在实际跑完 47 个页面的审计后，智囊团共产生了 23 个"反对意见"，其中 9 个被产品委员会采纳，最终阻止了 4 处"表面上正确但实际上会损害 SEO 结构"的改动。</p>

<h2>可移植的原则</h2>

<div class="callout callout-insight"><p>如果你在设计多 agent 协作系统，先画出"谁有决策权"的权限图，再写第一行代码。没有裁决层的多 agent 系统，输出结果的噪音会随 agent 数量线性增长。</p></div>

<ol>
  <li>如果你在让多个 agent 评估同一个对象，给每个 agent 的输出 schema 加一个「角色标记」字段，明确区分"建议"和"决策"，防止下游 agent 混淆权限。</li>
  <li>如果你的任务有多维度判断需求（比如质量 vs 转化 vs 一致性），专门设计一个"反对派 agent"，它的 KPI 是找矛盾，不是给答案。这比单纯增加审查步骤更有效。</li>
  <li>如果你在用 n8n 或类似工具编排这类工作流，把"产品委员会"这样的裁决节点单独做成一个子流程，而不是嵌入在某个 agent 的 prompt 里。裁决逻辑需要可见、可审计、可替换。</li>
  <li>如果你的 agent 团队需要处理超过 20 个页面或任务单元，先在 5 个样本上跑完整链路，验证结构化输出没有静默腐化，再放量。我们就是在第 6 个页面发现了 schema 字段被 agent 自作主张修改的问题。</li>
  <li>如果你发现多 agent 系统的输出"看起来都对但没法执行"，问题几乎一定不在 prompt 质量，而在缺少一个能说"最终就这么办"的节点。</li>
</ol>

<h2>下一步</h2>

<p>这次审计跑完之后，我们遗留了一个没有解决的问题：产品委员会 agent 在面对"智囊团反对 + 内容团队支持 + 市场团队中立"这种三方分裂的场景时，它的裁决质量明显下降，倾向于输出"defer"来回避决策。这其实是一个很典型的 agent 在面对高不确定性时的退缩模式。如果你在自己的系统里也遇到了类似的"agent 裁决回避"问题，欢迎在评论里聊聊你的处理方式——我们下篇文章打算专门拆解这个问题。</p>
