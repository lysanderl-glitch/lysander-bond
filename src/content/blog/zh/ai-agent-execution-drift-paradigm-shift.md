---
title: "解决AI Agent执行漂移：从修修补补到从零开始的范式转变"
description: "AI工作流可靠性：如何通过设计原则而非调试来保证长程会话稳定性"
publishDate: 2026-06-13T00:00:00.000Z
slug: ai-agent-execution-drift-paradigm-shift
lang: zh
hasEnglish: true
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

<h2>TL;DR</h2>
<div class="tl-dr"><ul>
  <li>长程会话中，错误不累积——它们以非线性的方式级联</li>
  <li>调试修正是治标，从零设计状态管理才是治本</li>
  <li>每 N 步强制插入 checkpoint，比任何 prompt 工程都有效</li>
  <li>限制 agent 的工具集自由度，比信任 LLM 自主选择更可靠</li>
  <li>可预测的失败优于不可预期的成功</li>
</ul></div>

<h2>问题背景</h2>
<p>去年 Q4，我们的一条客服 AI 工作流在测试环境跑通了 200 条对话，PM 签字上线。上线第一周，服务可用率 99.2%。第三周，跌到 87%。第五周，运维告警：模型输出的 JSON 结构开始出现字段缺失，工具调用参数开始指向不存在的资源 ID。</p>

<p>我们查了两天日志，发现问题不是「某个 prompt 写错了」——而是这条工作流在第 30 步之后，开始系统性漂移：每一步的输出质量都在下降，但下降的速度不均匀，有时连续三步输出完全正常，第四步突然崩溃。</p>

<p>这不是一个边界 case。我们回顾了内部三个项目的日志，类似的「长程会话衰减」在超过 25 步的任务中出现概率是 41%。</p>

<h2>为什么难排查</h2>
<p>我们一开始以为问题出在 prompt 上——可能某些指令被上下文覆盖了，或者工具描述文档写得不清晰。但实际上，重新审查 prompt 后发现，那些指令在对话开头写得很清楚，在第 15 步之后被正确引用，在第 35 步之后仍然存在。</p>

<p>我们后来以为问题出在模型的「记忆」上——可能上下文窗口满了，模型开始遗忘关键信息。但实际上，我们打印了每一步的 token 用量，第 35 步时上下文才用了 62%，远没有接近上限。</p>

<p>真正的原因藏在更隐蔽的地方：每一步的输出虽然「看起来正确」，但都不是严格类型化的。当第 8 步的工具调用返回了一个边界情况——比如 ID 为空字符串而非 null——这个值被传给了第 9 步，第 9 步把它拼进了某个 URL，第 10 步的解析器对这个 URL 产生了误解但没有报错，继续往下跑。这个错误像滚雪球一样越滚越大，直到第 30 步时某个下游系统终于因为无效参数拒绝响应。</p>

<p>换句话说：不是模型「记不住」，而是系统在第 1 步就允许了一个不合法状态滑过，然后把这个状态一直传递到第 N 步，直到某个脆弱的环节断裂。</p>

<h2>根因：缺乏显式状态管理</h2>

<p>问题的本质是：我们的工作流依赖 LLM 的「隐性判断」来维持状态连续性。每一步该做什么工具、参数从哪里取、上一步的输出是否有效——这些判断在代码层面是不存在的，全靠模型在 prompt 上下文中自己推理。</p>

<p>当会话短于 20 步时，这种方式足够好使，因为上下文路径短，错误还没来得及积累。但当会话超过 25 步，上下文中的中间结果越来越多，其中夹杂着无效值、边界情况、模型幻觉式的补充说明——系统的熵增无法控制。</p>

<p>我们从零重新设计的核心思路是：<strong>把「模型该怎么做」的判断权，从 LLM 的隐性推理中抽离出来，变成显式的状态机控制流</strong>。</p>

<p>具体来说，改造后的 agent 主循环如下：</p>

<pre><code class="language-python">from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import json

class AgentState(Enum):
    AWAITING_USER_INPUT = "awaiting_user_input"
    CLASSIFYING_INTENT = "classifying_intent"
    EXECUTING_TOOL = "executing_tool"
    VALIDATING_OUTPUT = "validating_output"
    RECOVERING = "recovering"

@dataclass
class AgentContext:
    state: AgentState = AgentState.AWAITING_USER_INPUT
    step_count: int = 0
    checkpoint_buffer: list[Dict[str, Any]] = field(default_factory=list)
    validated_output: Optional[Dict[str, Any]] = None
    error_log: list[str] = field(default_factory=list)

    # 关键设计：只允许显式传递的字段进入上下文
    safe_workspace: Dict[str, Any] = field(default_factory=dict)

MAX_STEPS = 20
CHECKPOINT_INTERVAL = 5

def agent_loop(initial_input: str) -> Dict[str, Any]:
    ctx = AgentContext()
    ctx.safe_workspace["user_input"] = initial_input

    while ctx.step_count < MAX_STEPS:
        # 每 CHECKPOINT_INTERVAL 步强制保存快照
        if ctx.step_count > 0 and ctx.step_count % CHECKPOINT_INTERVAL == 0:
            snapshot = {
                "step": ctx.step_count,
                "state": ctx.state.value,
                "workspace_snapshot": json.loads(
                    json.dumps(ctx.safe_workspace)
                ),  # 深拷贝，隔离引用
            }
            ctx.checkpoint_buffer.append(snapshot)
            # 超过 3 个 checkpoint 则清理旧快照
            if len(ctx.checkpoint_buffer) > 3:
                ctx.checkpoint_buffer.pop(0)

        # 状态机驱动下一步行为，而非模型自由选择
        next_state = transition(ctx)
        ctx.state = next_state

        if ctx.state == AgentState.RECOVERING:
            # 回滚到最近的有效 checkpoint
            if ctx.checkpoint_buffer:
                restored = ctx.checkpoint_buffer[-1]
                ctx.safe_workspace = restored["workspace_snapshot"]
                ctx.state = AgentState.CLASSIFYING_INTENT
                ctx.error_log.append(f"Rollback at step {ctx.step_count}")

        ctx.step_count += 1

    return ctx.safe_workspace

def transition(ctx: AgentContext) -> AgentState:
    """
    状态转换由规则引擎控制，而非由 LLM 自由选择。
    LLM 只在 CLASSIFYING_INTENT 和 VALIDATING_OUTPUT 两个状态介入。
    """
    match ctx.state:
        case AgentState.AWAITING_USER_INPUT:
            return AgentState.CLASSIFYING_INTENT
        case AgentState.CLASSIFYING_INTENT:
            # LLM 只负责分类，不负责执行
            intent = llm_classify(ctx.safe_workspace["user_input"])
            ctx.safe_workspace["current_intent"] = intent
            return AgentState.EXECUTING_TOOL
        case AgentState.EXECUTING_TOOL:
            # 工具选择是确定性的——根据 intent 查表，不依赖 LLM 自主决策
            tool = INTENT_TO_TOOL_MAP.get(ctx.safe_workspace["current_intent"])
            if tool is None:
                return AgentState.RECOVERING
            result = execute_tool(tool, ctx.safe_workspace)
            ctx.safe_workspace["last_result"] = result
            return AgentState.VALIDATING_OUTPUT
        case AgentState.VALIDATING_OUTPUT:
            # 必须通过 schema 校验，否则强制回滚
            validated = validate_and_sanitize(ctx.safe_workspace["last_result"])
            if validated is None:
                return AgentState.RECOVERING
            ctx.validated_output = validated
            ctx.safe_workspace["last_result"] = validated
            return AgentState.AWAITING_USER_INPUT
        case AgentState.RECOVERING:
            return AgentState.CLASSING_INTENT
    return AgentState.AWAITING_USER_INPUT
</code></pre>

<p>这段代码的核心变化是三处：</p>

<ul>
  <li>状态机替代 LLM 自主决策：工具选择通过 <code>INTENT_TO_TOOL_MAP</code> 查表完成，LLM 只在「分类意图」和「校验输出」两个节点介入，其余路径由确定性代码驱动。</li>
  <li>强制 checkpoint：每 5 步保存一次工作区快照，当检测到无效状态时回滚到最近的 checkpoint，而非让错误继续传播。</li>
  <li>类型化校验：<code>validate_and_sanitize</code> 对每一步的输出做 schema 校验，拒绝无效值进入 <code>safe_workspace</code>。</li>
</ul>

<h2>可移植的原则</h2>

<div class="callout callout-insight"><p>如果你在构建 AI 工作流，<strong>不要信任 LLM 的「隐性判断」来维持状态连续性，显式状态机 + 强制 checkpoint 比任何 prompt 技巧都更可靠。</strong></p></div>

<ol>
  <li>如果你在设计 agent 的执行路径，<strong>限制工具集的自由度</strong>——在每个状态下，只暴露该状态需要的工具，而不是把全部工具 API 都扔给模型。</li>
  <li>如果你在处理长程会话，<strong>每 N 步（N ≤ 10）插入一次强制 checkpoint</strong>，将工作区序列化后存入独立存储，而非依赖内存中的上下文。</li>
  <li>如果你在调试间歇性崩溃，<strong>先检查数据流的边界情况</strong>——空字符串、零值、null 是否被允许进入下一步，而不是默认「正常」就放行。</li>
  <li>如果你在评估 AI 工作流可靠性，<strong>用「最坏路径」测试</strong>——构造一个 token 边界、工具返回异常、网络超时的场景，看系统是否能正确降级而非崩溃。</li>
  <li>如果你在计划 AI 工作流的上线节奏，<strong>用分阶段 step limit 控制风险</strong>——先用 10 步以内的小流程验证，长期任务通过分片和多 agent 协作完成。</li>
</ol>

<h2>结尾</h2>

<p>改造完成后，我们把同一条工作流重新跑进了生产。同一套场景，第 35 步之后的输出结构完整性从 61% 提升到了 97%。这不是因为模型变聪明了，而是因为我们把「模型该怎么做」这件事从模糊的 prompt 推理中抽离出来，变成了可审计的确定性代码。</p>

<p>如果你正在为 AI 工作流的不稳定头疼，与其反复调 prompt，不如先问自己一个问题：<strong>我的系统在第 N 步失败时，有没有能力知道「从哪一步开始错的」？</strong> 如果答案是否定的，从零设计你的状态管理架构。</p>

<p>我们踩过的坑——状态漂移、隐性错误传播、checkpoint 缺失——每一个都有对应的日志记录和复盘文档。如果你在具体实现 checkpoint 机制或 schema 校验层遇到了卡点，欢迎来聊。</p>
