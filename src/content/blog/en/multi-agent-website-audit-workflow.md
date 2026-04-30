---
title: "How a 4-Agent Team Audited 47 Pages — and Why Authority Design Is the Hard Part"
description: "A live test of multi-agent website auditing: how we structured committee authority, role-based output schemas, and a dedicated opposition agent that blocked 4 SEO-damaging changes."
date: 2026-04-29
publishDate: 2026-04-29T00:00:00.000Z
slug: multi-agent-website-audit-workflow
lang: en
keywords:
  - AI Engineering
  - multi-agent
  - Synapse
author: lysander
---

## TL;DR

- Multi-agent website audits need explicit decision authority, not just task division
- Four roles (committee, content, marketing, think tank) each serve distinct functions
- Without structured output schemas, inter-agent data silently corrupts
- A dedicated "opposition agent" blocked 4 SEO-damaging changes across 47 pages
- The hard problem was organizational logic, not technical implementation

We ran a full-site content audit on the Synapse website — 47 pages covering product descriptions, case studies, blog posts, and documentation. The immediate problem was obvious: CTA buttons pointing to deprecated features, case study data from 2022, and pricing descriptions that contradicted each other across different entry points. Manual review would cost two people three to four days. We used this as a live test for a multi-agent system, and what we ended up documenting was mostly what broke.

Our first instinct was a simple linear pipeline: one crawler agent, one review agent, one output. We got it running in about two days. It was useless. The real issue is that website content audits aren't single-dimension judgments. The same product description can be "technically accurate" from a product perspective, "too jargon-heavy to convert" from a marketing perspective, and "logically inconsistent with last month's blog post" from a content perspective. All three are valid. Without a mechanism to arbitrate between them, the system outputs a pile of contradictory suggestions with no clear next action.

The fix was architectural: we introduced four agents with hard-coded authority boundaries. The **Product Committee Agent** holds the only decision-making power — accept, revise, defer, or remove. The **Content Team Agent** and **Marketing Team Agent** produce recommendations only. The **Think Tank Agent** does one thing: challenge every recommendation from the other two. Its system prompt contains a hard instruction to identify at least one scenario where a proposed change could backfire, and to surface a question the committee must answer before deciding. It is explicitly not allowed to propose solutions.

The authority boundary was enforced through output schema design. We added a `recommendation_only: true` field to content and marketing agent outputs. Without it, the Product Committee Agent was silently treating content team suggestions as already-decided items and skipping them entirely — a data loss bug with no error message. Across the full 47-page run, the Think Tank generated 23 objections, 9 of which the committee adopted, ultimately preventing 4 changes that would have damaged the site's SEO structure.

## Key Takeaways

- If you're building a multi-agent evaluation system, draw the authority map before writing any code — noise scales linearly with agent count when no one has final say.
- If multiple agents assess the same object, add a role-marker field to each output schema that explicitly distinguishes "recommendation" from "decision."
- If your task involves competing evaluation dimensions, design a dedicated opposition agent whose KPI is finding contradictions, not providing answers.
- If agents pass structured data between layers, treat missing schema fields as silent failure modes — validate authority markers at ingestion, not just at output.

## Read the Full Article (Chinese)

This is an abstract. The full technical walkthrough — including system prompt fragments, the complete output schema, and a breakdown of all 23 think tank objections — is in Chinese.
