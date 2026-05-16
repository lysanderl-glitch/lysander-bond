---
title: "AI Agent工作流设计：会议纪要从录音到知识库的自动化处理"
description: "如何设计一个能够调用多个AI agent协同处理会议纪要的端到端工作流"
publishDate: 2026-05-16T00:00:00.000Z
slug: ai-agent-workflow-meeting-notes-knowledge-base
lang: zh
hasEnglish: true
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

<div class="tl-dr">
  <ul>
    <li>多Agent管道中错误会级联放大，需在每个节点加Schema验证</li>
    <li>上下文窗口不是简单切分，要按语义块累积</li>
    <li>状态机模式比回调地狱更可控</li>
    <li>会议纪要要用结构化Schema而非纯文本</li>
    <li>失败重试要设熔断阈值，避免无限循环</li>
  </ul>
</div>

<h2>问题背景：每周200页的会议记录，我们团队是怎么被拖垮的</h2>

<p>上个月我们团队统计了一个数据：每周平均40场会议，总时长超过25小时。假设每场会议的纪要整理需要30分钟，光是这一个环节就占用了20个人·小时。更要命的是，这些纪要在整理完后大部分都躺在文档库里，从来没人再去看第二遍。</p>

<p>问题的本质不是会议太多，而是从录音到可执行知识的转化链路太慢了。一场关键的产品评审会结束后，决策者需要立刻知道"结论是什么"、"谁负责什么"、"下周要看什么"。但传统的处理流程是：录音→人工听写→手动整理→上传文档。这条链路最快也要2-3小时，而且依赖人工注意力，整理质量参差不齐。</p>

<p>我开始想，能不能用多个AI Agent串联起来，把这个过程自动化？录音上传后，Agent自动转写、智能摘要、提取行动项、关联到已有的知识库。但当我真正开始设计这条管道时，发现事情远没有想象中简单。</p>

<h2>为什么这个决策难做：多Agent编排不是拼积木</h2>

<p>我们一开始以为，设计多Agent工作流就是"把任务拆解，每个Agent负责一步，然后用消息队列串起来"。理论上这个思路没问题，但实际跑起来遇到了三个没想到的坑。</p>

<p>第一个坑是错误级联。我们以为只要每个Agent正确处理自己的输入就行，但实际上上游Agent的一个小错误会在下游被放大。比如转录Agent偶尔会把一个词识别错，虽然不影响人类理解，但摘要Agent拿到这个错误片段时，会把它当成正确信息继续加工，最终输出的摘要可能偏离原意。更糟糕的是，这种错误很难追溯——你看到的是最终结论错了，但不知道根因在哪一步。</p>

<p>第二个坑是上下文窗口管理。我们以为"每场会议单独处理"就能解决问题，但现实是，同一个项目往往有多场连续会议，决策是逐步形成的。如果只看单场会议的纪要，很多上下文会丢失。但要把多场会议的转录文本累积起来处理，很快就触及模型的上下文窗口限制。我们一开始尝试简单截断，后来发现这样会切掉关键的决策结论部分。</p>

<p>第三个坑是状态同步。多个Agent并行处理不同会议时，状态管理变得极其复杂。哪个会议处理到哪一步了？失败了要不要重试？重试多少次？这些问题交织在一起，用传统的回调模式很快就变成了"回调地狱"。</p>

<h2>根因分析：用一个状态机模式重构工作流</h2>

<p>经过三个版本的迭代，我们决定放弃简单的消息队列模式，改用状态机（State Machine）来编排整个工作流。核心思路是：每个会议的处理状态是明确且可追溯的，状态转换由明确的规则触发，失败处理统一在一个地方管理。</p>

<p>这是我们的核心配置结构：</p>

<pre><code class="language-python">import asyncio
from typing import TypedDict
from enum import Enum

class ProcessingState(str, Enum):
    PENDING = "pending"
    TRANSCRIBING = "transcribing"
    SUMMARIZING = "summarizing"
    EXTRACTING_ACTIONS = "extracting_actions"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"

class MeetingState(TypedDict):
    meeting_id: str
    audio_path: str
    state: ProcessingState
    transcript: str | None
    summary: str | None
    action_items: list[dict]
    topics: list[str]
    retry_count: int
    error_message: str | None

async def process_meeting(meeting: MeetingState) -> MeetingState:
    """会议处理主流程"""
    handlers = {
        ProcessingState.TRANSCRIBING: transcribe_agent,
        ProcessingState.SUMMARIZING: summarize_agent,
        ProcessingState.EXTRACTING_ACTIONS: action_extractor_agent,
        ProcessingState.UPLOADING: knowledge_base_uploader,
    }

    while meeting["state"] != ProcessingState.COMPLETED:
        if meeting["state"] == ProcessingState.FAILED:
            break

        handler = handlers.get(meeting["state"])
        if not handler:
            break

        try:
            meeting = await handler(meeting)
            meeting["state"] = get_next_state(meeting["state"])
        except Exception as e:
            meeting["retry_count"] += 1
            if meeting["retry_count"] >= 3:
                meeting["state"] = ProcessingState.FAILED
                meeting["error_message"] = str(e)
            else:
                await asyncio.sleep(2 ** meeting["retry_count"])

    return meeting
</code></pre>

<p>这个设计解决了我们之前遇到的三个问题。首先，每个Agent处理完后都要验证输出，不合格就立即重试，不会把错误传递到下游。</p>

<pre><code class="language-python">from pydantic import BaseModel, field_validator

class ActionItem(BaseModel):
    assignee: str
    task: str
    deadline: str | None
    priority: str

    @field_validator("task")
    @classmethod
    def task_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 10:
            raise ValueError("行动项描述不能少于10个字符")
        return v

async def action_extractor_agent(meeting: MeetingState) -> MeetingState:
    prompt = f"从以下会议记录中提取行动项：\n{meeting['summary']}"
    raw_output = await llm_client.generate(prompt)

    try:
        parsed = json.loads(raw_output)
        meeting["action_items"] = [ActionItem(**item) for item in parsed]
    except (json.JSONDecodeError, ValidationError) as e:
        raise RuntimeError(f"行动项解析失败: {e}")

    return meeting
</code></pre>

<p>其次，上下文窗口的问题我们通过语义块累积解决：不是按固定长度切分，而是按段落语义切分，确保每个块都是完整的语义单元。</p>

<pre><code class="language-python">from dataclasses import dataclass

@dataclass
class ContextWindow:
    max_tokens: int = 128000
    accumulated_texts: list[str]

    def add(self, text: str, estimated_tokens: int) -> bool:
        if self.current_tokens + estimated_tokens > self.max_tokens:
            return False
        self.accumulated_texts.append(text)
        return True

    def get_context_for_summary(self) -> str:
        return "\n---\n".join(self.accumulated_texts[-3:])

# 多场会议关联处理
async def process_project_meetings(project_id: str):
    meetings = await db.get_meetings_by_project(project_id)
    context_window = ContextWindow()

    for meeting in sorted(meetings, key=lambda m: m["timestamp"]):
        if context_window.add(meeting["transcript"], estimate_tokens(meeting["transcript"])):
            continue
        await summarize_cumulative_context(context_window)
        context_window = ContextWindow()
        context_window.add(meeting["transcript"], estimate_tokens(meeting["transcript"]))
</code></pre>

<h2>可移植的原则</h2>

<div class="callout callout-insight">
  <p>如果你在设计多Agent工作流，在每个Agent输出端加Schema验证。不要假设上游的输出一定正确，不要让错误级联到下游。</p>
</div>

<ol>
  <li>如果你在设计多Agent工作流，用状态机模式替代回调模式。状态是可追溯的，转换规则是明确的，失败处理是统一的。</li>
  <li>如果你在处理长文本累积，不要简单截断。按语义块累积，确保每个块是完整的表达单元，累积上限设到上下文窗口的80%。</li>
  <li>如果你在定义Agent输出格式，用结构化Schema而不是自由文本。Schema是自文档化的，验证是自动化的，下游解析是无歧义的。</li>
  <li>如果你在实现重试逻辑，设置熔断阈值和指数退避。盲目重试不仅浪费资源，还可能把系统推向更不稳定的状态。</li>
</ol>

<h2>结尾</h2>

<p>这条工作流目前已经稳定运行了六周，处理了超过300场会议。但我们清楚，目前的设计还有优化空间——比如多Agent之间的上下文共享机制，比如如何让LLM更好地理解跨会议的决策演变链条。如果你也在做类似的事情，或者遇到了我们还没解决的问题，欢迎来交流。我们把具体的Agent编排代码和状态机实现细节整理了一份文档，可以在评论里留下邮箱，我会发给需要的人。</p>
