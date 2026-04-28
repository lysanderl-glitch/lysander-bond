---
title: "[EN] Replacing a 15-Person Outsourced Team with AI: A Financial Leasing Company's Synapse Transition"
description: "From a real client scenario: how 'product manager + AI' can absorb work that previously required a 15-person outsourced development team"
date: 2026-04-26
publishDate: 2026-04-26T00:00:00.000Z
slug: ai-replacing-outsourcing-financial-leasing-synapse
lang: en
tags:
  - AI Engineering
  - Synapse
  - Case Study
author: lysander
---

## TL;DR

- Client: financial equipment leasing company, 15-person outsourced dev team, ~¥300K/month
- After 3 months: team reduced to 1 PM + 2 part-time engineers, monthly delivery up 15→23 features
- Monthly cost dropped from ¥250K to ~¥60K (including engineer salaries and AI tools)
- Key insight: 80% of outsourced work was mechanical execution; AI targets exactly that 20/80 split
- Non-replicable preconditions: standard tech stack (Spring Boot + Vue), PM with dev background, no legacy debt

## The Problem

Three months ago, a client in equipment financing leasing came to me with a direct question: they maintained a 15-person outsourced dev team, nearly ¥3M annually, inconsistent delivery quality, 2-week average requirement response time, and core business logic scattered across contractors' personal computers with no institutional knowledge retained. Could AI replace this?

My first response wasn't "yes" — it was "let's figure out what these 15 people actually do."

The breakdown: 2 people on requirements and documentation, 4 on frontend, 6 on backend and APIs, 3 on testing and operations. The core system — leasing contract management, repayment schedule generation, asset ledger, risk rules engine — isn't architecturally complex. The work that actually requires business judgment concentrated in requirements understanding and rules design. Everything else was mechanical CRUD development, API integration, and regression testing. Roughly 20% requiring humans, 80% repeating labor.

## What Synapse Did in This Context

The solution wasn't "AI writes code, humans review." We redefined what a product manager does.

**Layer 1: Requirements structuring.** Financial leasing has many rule-type requirements: "interest rate calculation differs by lease category — financing leases use IRR, operating leases use calendar-day method." This kind of requirement, when thrown to outsourcers, would come back wrong two weeks later. Now the PM uses Synapse's requirement decomposition template to write business rules as structured decision tree descriptions. AI generates code frameworks and test cases from these. Critically: rule definition authority stays with the PM; AI handles translation and execution. This compressed the requirement-to-code cycle from 2 weeks to 2 days.

**Layer 2: Code quality control for financial domain.** A real pitfall worth documenting: AI-generated financial calculation code frequently produces floating-point precision errors in repayment schedules — accumulated rounding errors in lease payments. Our fix was injecting domain constraints into Synapse's code generation node, forcing all monetary calculations to use Decimal types, with automatic boundary-value testing post-generation.

<pre><code class="language-python"># Injected into Synapse code generation system prompt
FINANCIAL_CONSTRAINTS = """
- All monetary calculations: use Python Decimal, never float
- Repayment schedules: validate that sum(payments) == principal + total_interest ± 0.01
- IRR calculation: use scipy.optimize with tolerance 1e-8
"""
</code></pre>

**Layer 3: Knowledge retention loop.** The biggest outsourcing risk is knowledge walking out the door. Synapse auto-generates a "decision record" after each requirement — why designed this way, which alternatives were rejected, which business rules apply. Three months in: 200+ business decision records, more institutional knowledge than 5 years of prior outsourcing produced.

## Real Numbers and Unsolved Problems

After 3 months: outsourced team reduced to 1 full-time PM + 2 part-time engineers (deployment and security audit only). Monthly delivery: 8 → 23 requirements. Monthly cost: ¥250K → ~¥60K.

Prerequisites that made this work: standard tech stack (Spring Boot + Vue), PM with 3 years of development background, no legacy system complexity.

Two problems we haven't solved: requirement accuracy still depends on the PM's individual capability ceiling — AI can't find business gaps you didn't think to describe. And regulatory compliance requirements (5-tier asset classification, ABS disclosure) still need manual line-by-line verification.

<div class="callout callout-insight"><p>If you're evaluating this path, do the work breakdown first — don't talk about replacement ratios. Find out what percentage of your outsourced work is rule-clear mechanical execution versus genuine business judgment. AI targets the mechanical portion. If it's less than 60%, the math doesn't work.</p></div>

## Key Takeaways

<ol>
<li>If you're considering AI to replace outsourcing, decompose the work first — identify what's mechanical execution vs. what requires business judgment.</li>
<li>If you use AI for domain-specific code, inject domain knowledge explicitly — AI won't automatically know the difference between IRR and calendar-day interest calculations.</li>
<li>If you go fully AI-driven development, keep one engineer who can read code — not to write it, but to identify when AI output is technically correct but domain-wrong.</li>
</ol>

## Read the Full Article (Chinese)

This is an abstract. The full case study — including the complete 3-month implementation timeline, Synapse decision record format, and the specific financial domain constraints injected into prompts — is in Chinese at [lysander.bond/blog/ai-replacing-outsourcing-financial-leasing-synapse](https://lysander.bond/blog/ai-replacing-outsourcing-financial-leasing-synapse).
