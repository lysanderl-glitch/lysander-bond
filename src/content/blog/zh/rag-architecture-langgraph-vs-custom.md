---
title: "从零思考RAG选型：LangGraph还是自研？"
description: "不因已有投入而拒绝评估，从第一性原理分析LangGraph与自研RAG的技术取舍"
publishDate: 2026-06-09T00:00:00.000Z
slug: rag-architecture-langgraph-vs-custom
lang: zh
hasEnglish: true
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

<h2>TL;DR</h2>
<div class="tl-dr">
  <ul>
    <li>LangGraph擅长流程编排，但检索性能需自研补强</li>
    <li>自研不等于更可控，框架学习曲线和自研维护成本要一起算</li>
    <li>先用最小闭环验证核心假设，再决定架构选型</li>
    <li>性能瓶颈通常出在数据流而非流程控制层</li>
    <li>混合架构可能是中小团队的最优解</li>
  </ul>
</div>

<h2>问题背景</h2>
<p>去年Q3，我们接到了一个需求：为一个内部知识库系统构建RAG能力。文档规模50万份，涵盖产品手册、技术文档、客服FAQ三类内容。用户场景是自然语言查询，需要返回精准答案而非整篇文档。</p>
<p>团队当时对LangGraph有过小范围试用经历，直觉上想复用这套经验。但另一个声音是：从零自研RAG Pipeline，理论上更可控，毕竟我们熟悉自己的数据特征和查询模式。</p>
<p>两种声音拉扯了将近三周，期间做了两轮POC，踩了几个坑才逐渐清晰。</p>

<h2>为什么这个决策难做</h2>
<p>我们一开始以为LangGraph能解决流程编排问题就够了，检索层用哪家向量数据库都行。但实际上，当我们用LangGraph跑完第一个可用的RAG Chain后，P95延迟直接飙到800ms，用户体验完全不可接受。</p>
<p>更关键的认知翻转在于：<strong>我们一开始以为"自研"意味着更强的可控性，但实际上</strong>，当真正去实现Query理解、意图分类、查询改写、检索、重排序这一整套流程时，光是调试各环节的串接逻辑就消耗了预计工时的两倍。自研方案的开发周期从预估的2周膨胀到6周。</p>
<p>这不是选择LangGraph还是自研的问题，而是<strong>我们在没有拆解清楚RAG系统各层性能特征的情况下，就做了技术选型</strong>。</p>

<h2>根因/核心设计决策</h2>
<p>真正让我们走出困境的，是一个关键认知：RAG系统的性能瓶颈不在流程编排层，而在数据流层。</p>
<p>LangGraph擅长的是有状态的工作流管理，它让流程节点之间的状态传递变得可追溯、可调试。但当我们把大量时间花在"如何让LangGraph高效处理批量检索"时，发现这本身就是用错了工具。</p>
<p>最终我们采用了混合架构：LangGraph负责Query理解 → 意图路由 → 生成这整条链路，而向量检索和重排序模块独立出来，用底层库直接实现。</p>

<h3>LangGraph负责的流程编排</h3>
<pre><code class="language-python">from langgraph.graph import StateGraph, END
from typing import TypedDict

class RAGState(TypedDict):
    query: str
    intent: str
    retrieval_result: list
    reranked_result: list
    answer: str

def intent_classifier(state: RAGState) -> RAGState:
    """意图识别节点"""
    query = state["query"]
    # 简单规则匹配，生产环境可用fine-tuned model
    if any(k in query for k in ["如何", "怎么", "步骤"]):
        state["intent"] = "instructional"
    elif any(k in query for k in ["为什么", "原因", "原理"]):
        state["intent"] = "explanatory"
    else:
        state["intent"] = "factual"
    return state

def route_by_intent(state: RAGState) -> str:
    """条件路由"""
    return state["intent"]

# 构建图
workflow = StateGraph(RAGState)
workflow.add_node("classify", intent_classifier)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)
workflow.set_entry_point("classify")
workflow.add_conditional_edges("classify", route_by_intent, {
    "instructional": "retrieve",
    "explanatory": "retrieve", 
    "factual": "retrieve"
})
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

app = workflow.compile()</code></pre>

<h3>自研的检索层关键实现</h3>
<pre><code class="language-python">class HybridRetriever:
    def __init__(self, vector_store, bm25_index):
        self.vector_store = vector_store  # FAISS或Milvus
        self.bm25_index = bm25_index      # Pyserini构建
        self.reranker = CrossEncoderReranker()
    
    def retrieve(self, query: str, top_k: int = 20) -> list[Document]:
        # 并行向量检索 + BM25
        vector_results = self.vector_store.similarity_search(query, k=top_k)
        bm25_results = self.bm25_index.search(query, k=top_k)
        
        # Reciprocal Rank Fusion合并结果
        fused_scores = self._reciprocal_rank_fusion(
            [vector_results, bm25_results],
            k=60
        )
        
        # 重排序，取top 5
        reranked = self.reranker.rerank(query, fused_scores[:top_k], top_n=5)
        return reranked
    
    def _reciprocal_rank_fusion(self, result_lists: list, k: int = 60) -> list:
        scores = {}
        for results in result_lists:
            for rank, doc in enumerate(results):
                doc_id = doc.id
                scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)</code></pre>

<p>调优后的混合方案，P95延迟稳定在180ms左右，比纯LangGraph方案快了4倍，同时保留了LangGraph在流程编排上的灵活性。</p>

<h2>可移植的原则</h2>

<div class="callout callout-insight"><p>如果你在构建RAG系统，<strong>先用最小闭环验证核心假设</strong>，再决定框架选型。不要被工具束缚问题定义本身。</p></div>

<ol>
<li>如果你在评估复杂查询场景，先用LangGraph快速构建原型验证流程正确性，再评估性能瓶颈点</li>
<li>如果你发现框架的性能墙出现在数据流环节而非流程控制，那么自研该模块是正确的选择</li>
<li>如果你需要支持多种检索策略（向量+关键词+知识图谱），确保检索层是可插拔架构</li>
<li>如果你担心自研的长期维护成本，为核心模块编写完整的单元测试和集成测试</li>
<li>如果你在团队内部推广新技术，先在非关键路径上试点，用真实数据验证效果后再决定是否全量</li>
</ol>

<h2>结尾</h2>
<p>RAG选型没有银弹。LangGraph和自研不是非此即彼的选择，而是不同抽象层次上的工具。关键在于识别你的系统真正卡在哪里——是流程编排的复杂度，还是检索性能的天花板。如果是前者，LangGraph值得投入；如果是后者，别犹豫，把那块独立出来优化。</p>
