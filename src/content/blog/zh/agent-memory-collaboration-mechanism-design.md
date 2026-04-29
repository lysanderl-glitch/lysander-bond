---
title: "Agent记忆协作机制设计：让AI在下一次会话中'记得'上一次做了什么决策"
description: "通过产品管线信息归档实现跨会话知识传递，分析这种'外置记忆+委员会调用'模式的架构设计与适用场景"
date: 2026-04-28
publishDate: 2026-04-28T00:00:00.000Z
slug: agent-memory-collaboration-mechanism-design
lang: zh
hasEnglish: true
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

<div class="tl-dr"><ul>
  <li>Agent跨会话失忆，根因是上下文窗口天然无状态</li>
  <li>解法：产品管线归档 + 外置记忆 + 委员会召回</li>
  <li>不是RAG检索，而是结构化决策日志的定向注入</li>
  <li>架构核心：写入时严格，读取时按角色筛选</li>
  <li>适用场景有限，盲目推广反而引入噪声</li>
</ul></div>

<h2>问题背景</h2>

<p>我们在 Synapse 内部跑着一个产品管线评审流程：多个 AI Agent 组成一个"委员会"，分别扮演产品经理、技术负责人、市场分析师的角色，对某个功能提案进行轮流评审。每轮会话平均持续 40 分钟，产出 12–18 条决策记录。问题在于：当下一次会话开始，你想让"技术负责人 Agent"接着上次说——它完全不记得任何事情。</p>

<p>这不是玄学问题，是 LLM 的工程现实：每次调用都是无状态的。上下文窗口塞不下三次以上的完整会话历史，而且即便你强行塞进去，模型的注意力会被稀释，靠后的信息实际上被"遗忘"的概率很高。我们第一次正式遇到这个问题，是在推进某个功能的第 4 次评审会议时，技术负责人 Agent 给出了一个建议——和第 2 次会议里它自己否定过的方案几乎一模一样。</p>

<h2>为什么这个决策难做</h2>

<p>我们一开始以为，把上一次会话的聊天记录直接附在 system prompt 里就够了。实际上这带来了两个真实问题：第一，token 成本在第 5 次会话时已经是第 1 次的 6 倍；第二，更隐蔽的问题是，模型在阅读一段长达 3000 字的历史记录时，会混淆"哪些是已经拍板的决策"和"哪些是当时被否定的讨论方向"。我们测试过，把一段包含正反两面讨论的历史记录喂给 Agent，它有将近 30% 的概率会把曾经被否定的选项当成"上次的结论"来继承。</p>

<p>然后我们换了一个方向：用 RAG，把历史对话向量化，每次召回最相关的几段。这在概念上很美，但实际上失败得很彻底。相关性检索找到的是"语义相似的内容"，而不是"对当前决策有影响力的结论"。举个例子：技术负责人在第 2 次会议里说过"这个方案的延迟不可接受"，但如果第 5 次会议的问题是"我们要不要重新考虑缓存策略"，这条关键结论的向量距离可能根本排不进 Top-5。你检索到的，是一堆关于"缓存"的泛泛讨论。</p>

<h2>根因与核心设计决策</h2>

<p>问题的根因是：我们想解决的是"决策连续性"，而不是"内容检索"。这两件事要求完全不同的存储和召回机制。</p>

<p>最终我们设计了一套"产品管线信息归档"结构。每次会话结束后，有一个专门的归档 Agent 负责把本次会话的输出压缩成结构化的决策日志，而不是保留原始对话。格式强制要求三个字段：<code>decision</code>（拍板的结论）、<code>rationale</code>（核心理由，限 50 字以内）、<code>owner</code>（哪个角色做出的判断）。</p>

<pre><code class="language-yaml"># pipeline_memory_entry.yaml
session_id: "review_session_004"
timestamp: "2024-11-12T14:32:00Z"
entries:
  - decision: "放弃方案A的同步写入设计"
    rationale: "P99延迟在压测中超过800ms，超出SLA上限"
    owner: "tech_lead_agent"
    status: "closed"   # closed / open / revisable

  - decision: "缓存策略延后到第6次会议决定"
    rationale: "依赖基础设施评估结果，当前信息不足"
    owner: "committee"
    status: "open"

  - decision: "优先级排序：稳定性 > 性能 > 新特性"
    rationale: "市场分析显示当前用户流失主因是稳定性"
    owner: "pm_agent"
    status: "closed"
</code></pre>

<p>下一次会话开始时，系统不是把整个历史记录扔进去，而是按 <code>owner</code> 字段做定向注入：技术负责人 Agent 只收到 <code>owner: tech_lead_agent</code> 和 <code>owner: committee</code> 的条目，产品经理 Agent 只收到属于自己角色的部分。这样每个 Agent 的 system prompt 里的历史记忆部分通常不超过 400 tokens，但信噪比极高。</p>

<pre><code class="language-python"># memory_injector.py（伪代码）
def build_agent_context(agent_role: str, pipeline_archive: list[dict]) -> str:
    relevant = [
        e for e in pipeline_archive
        if e["owner"] in (agent_role, "committee")
        and e["status"] in ("closed", "revisable")
    ]

    memory_block = "## 历史决策（请在本次发言前先确认是否与以下结论冲突）\n"
    for entry in relevant:
        flag = "✅ 已定案" if entry["status"] == "closed" else "🔄 可复议"
        memory_block += f"- [{flag}] {entry['decision']}（理由：{entry['rationale']}）\n"

    return memory_block
</code></pre>

<p>这里有一个反直觉的设计选择：我们没有把 <code>status: open</code> 的条目注入进去。原因是"未决事项"会让 Agent 在本轮提前发散去解决它，而不是聚焦当前议题。未决事项由会议协调层单独管理，在正确的时机才会触发。</p>

<h2>可移植的原则</h2>

<div class="callout callout-insight"><p>外置记忆的价值不在于"存得多"，在于"写入时强制压缩"。如果归档这一步本身没有结构约束，所有下游召回机制都是在放大噪声。</p></div>

<ol>
  <li>
    <strong>如果你在设计多 Agent 协作流程</strong>，在每次会话结束时加一个专门的归档步骤，不要让生成 Agent 自己归档自己的输出——角色分离能显著提高归档质量。
  </li>
  <li>
    <strong>如果你在考虑用 RAG 解决跨会话记忆问题</strong>，先问自己：你要检索的是"相关内容"还是"有约束力的结论"？如果是后者，RAG 是错误的工具，结构化日志 + 定向注入更合适。
  </li>
  <li>
    <strong>如果你的 Agent 系统有多个角色</strong>，按角色过滤历史记忆，而不是全量广播。每个 Agent 只需要知道"和自己相关的已拍板结论"，全量历史是认知负担，不是信息资产。
  </li>
  <li>
    <strong>如果你在设计 status 字段</strong>，至少区分"已定案"和"可复议"两种状态。完全封闭的记忆系统会让 Agent 在遇到新信息时无法正常更新判断，这比遗忘更危险。
  </li>
  <li>
    <strong>如果你遇到 token 成本随会话次数线性增长的问题</strong>，根因几乎必然是你在用"历史记录堆叠"而不是"决策摘要替换"——两者达到同样的连续性效果，成本差距是数量级的。
  </li>
</ol>

<h2>还没解决的问题</h2>

<p>这套机制现在的真实短板是：归档 Agent 本身的压缩质量不稳定——遇到有歧义的讨论时，它有时候会把一个"倾向性意见"错误归类为 <code>status: closed</code>。我们在想的方向是加一个置信度字段，或者引入人工确认节点作为兜底。如果你在自己的系统里也跑着类似的多 Agent 评审管线，很想知道你们是怎么处理"半决策"这类边界情况的——欢迎在评论区或直接联系我讨论。</p>
