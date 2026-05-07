---
title: "从四级到五级：如何设计AI Agent的决策分级体系"
description: "将非技术价值判断纳入决策框架的实操方法论"
publishDate: 2026-05-05T00:00:00.000Z
slug: decision-hierarchy-design-4-to-5-levels
lang: zh
hasEnglish: true
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

<div class="tl-dr"><ul>
  <li>L5需要处理非技术价值判断，L4只需确定性规则</li>
  <li>决策分级本质是边界条件而非层级数量</li>
  <li>业务方需提供"价值偏好函数"而非仅流程图</li>
  <li>每个决策点必须标注可回滚范围</li>
  <li>反馈机制设计比初期分类更重要</li>
</ul></div>

<h2>问题背景</h2>

<p>上周三凌晨2点，我们的物流调度Agent（L4→L5升级灰度测试）做出了一个让整个团队陷入争议的决策：接受了一条利润率只有3%的订单，理由是"距离仓库15公里内优先级更高"。业务方质问为什么Agent放弃了隔壁城市利润率12%的订单，运维团队查了3小时日志才发现原因是某条规则在凌晨被意外激活。</p>

<p>这不是个例。过去两个月，我们的Agent在L4升级L5的过程中，决策失误率从0.3%飙升到2.1%，影响单量超过4700单，涉及金额超过180万元。问题不在于模型能力不足，而在于我们根本没有为"非技术价值判断"设计可执行的决策框架。</p>

<h2>为什么难排查</h2>

<p>我们一开始以为L4到L5的差距只是"多了一层判断逻辑"，参照现有分级标准增加规则数量就行。但实际上，L4处理的是确定性环境（成本最低、时间最短），L5要处理的是价值判断环境（成本与时效的权重、风险与收益的取舍）。这两个问题的本质完全不同。</p>

<p>更重要的是，我们发现业务方在提需求时普遍使用"优先级"这个模糊概念，但Agent执行时需要的是可量化的"价值函数"。业务方说"优先考虑大客户"，实际意思是"利润率高于8%的客户权重+50%"，但这个换算过程在过去完全缺失。结果就是业务方觉得Agent"不听话"，Agent其实在按字面意思执行一条从未被精确定义过的规则。</p>

<h2>根因/核心设计决策</h2>

<p>问题的根因在于：L5的决策框架需要同时处理技术约束和非技术价值判断，但我们沿用了L4时代的纯规则引擎架构。</p>

<p>真正的解决方案是引入"价值偏好层"，让业务方的价值判断变成可配置参数，而非硬编码规则。以下是我们重构后的决策框架核心代码：</p>

<pre><code class="language-python"># decision_framework.py
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

class DecisionLevel(IntEnum):
    L1_EXECUTE = 1   # 完全按指令执行
    L2_VALIDATE = 2  # 执行前校验
    L3_OPTIMIZE = 3  # 同目标内优化
    L4_BOUNDED = 4   # 边界内自主决策
    L5_VALUED = 5    # 价值判断决策

@dataclass
class ValuePreference:
    """业务价值偏好函数"""
    metric: str                    # 指标名称
    weight: float                  # 权重 (0.0-1.0)
    threshold: Optional[float] = None  # 阈值
    direction: str = "higher"      # 优化方向
    
    def evaluate(self, value: float) -> float:
        if self.threshold:
            return self.weight * (1.0 if value >= self.threshold else 0.0)
        return self.weight * value if self.direction == "higher" else self.weight * (1 - value)

class DecisionContext:
    """决策上下文"""
    level: DecisionLevel
    action: str
    options: List[Dict[str, Any]]
    value_preferences: List[ValuePreference]
    rollback_range: Optional[Dict[str, Any]] = None

def evaluate_option(option: Dict[str, Any], 
                   preferences: List[ValuePreference]) -> float:
    """计算单个选项的价值得分"""
    score = 0.0
    for pref in preferences:
        if pref.metric in option:
            score += pref.evaluate(option[pref.metric])
    return score

def make_decision(ctx: DecisionContext) -> Dict[str, Any]:
    """核心决策函数"""
    if ctx.level < DecisionLevel.L5_VALUED:
        # L1-L4: 使用确定性规则（保持原有逻辑）
        return deterministic_select(ctx)
    
    # L5: 价值驱动的决策
    scored_options = []
    for opt in ctx.options:
        score = evaluate_option(opt, ctx.value_preferences)
        scored_options.append((opt, score))
    
    # 按价值得分排序，选择最高分
    best = max(scored_options, key=lambda x: x[1])
    
    # 记录决策轨迹供回滚使用
    return {
        "selected": best[0],
        "score": best[1],
        "alternative": [opt for opt, _ in scored_options if opt != best[0]],
        "rollback_range": ctx.rollback_range
    }</code></pre>

<div class="callout callout-insight"><p>业务方的需求不应该是一张流程图，而是一组ValuePreference对象：metric定义要什么、weight定义多重要、threshold定义可接受的底线。这才是将"模糊的优先级"变成"可执行的价值函数"的正确方式。</p></div>

<h2>可移植的原则</h2>

<ol>
<li>如果你在设计L5级别Agent，请先问业务方"这个决策的失败成本是多少"，而不是"这个决策的优先级是什么"。失败成本决定了rollback_range的宽度。</li>
<li>如果你在定义决策边界，请确保每个边界条件都有对应的可量化测试用例。边界不是"客户重要性高"，而是"利润率≥8%且近30天订单数≥5"。</li>
<li>如果你在处理多目标冲突，请使用加权和模型而非if-else链。10个if-else覆盖不了10个指标的组合，但加权和可以。</li>
<li>如果你在写决策日志，请记录每个选项的"未选中原因"。这对事后复盘至关重要，我们就是因为缺少这个字段才查了3小时。</li>
</ol>

<h2>结尾</h2>

<p>物流调度Agent的问题在重新定义ValuePreference后72小时内解决：业务方将"优先考虑大客户"表述为"利润率权重0.6、订单量权重0.3、服务时效权重0.1"，Agent现在能正确地在不同业务场景下动态调整决策权重。如果你正在经历类似的L4→L5升级困境，建议先从决策日志格式改起——让Agent记录每个选项的未选中原因，比任何架构重构都更直接地暴露问题所在。</p>
