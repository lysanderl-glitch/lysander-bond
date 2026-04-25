---
title: "Notes from the Field: GA Validation and Version-Locking for AI Products"
slug: ai-product-ga-validation-version-lock
description: "An abstract of a Chinese case study on the full GA acceptance flow for PMO Auto V2.0 — structured requirements pool, layered test suites, and the mandatory five-step version lock."
lang: en
translationOf: ai-product-ga-validation-version-lock
hasEnglish: true
pillar: multi-agent-case
priority: P3
publishDate: 2026-04-24
author: content_strategist
keywords:
  - "AI-engineering"
  - "release-management"
  - "Synapse"
---

# Notes from the Field: GA Validation and Version-Locking for AI Products

This is an abstract of a Chinese-language Synapse case study using PMO Auto V2.0/V2.1 as the worked example. The opening realization: this product had never gone through real GA acceptance — meaning explicit acceptance criteria, end-to-end tests across critical paths, traceable requirement-to-version chain, and a P0 rollback plan that doesn't depend on memory at 3am. Traditional software has mature practices for this; AI products almost universally don't. The full Chinese article documents how we built that infrastructure from scratch, including a near-miss WF-05 OOM bug caught only because Suite D existed.

## Key Takeaways

- **Start from a structured requirements pool, not from code**: `requirements_pool.yaml` with RICE scoring, machine-verifiable Acceptance Criteria, and evidence links. No AC = no acceptance baseline. Each shipped REQ writes back `shipped_at`, `release_tag`, `evidence` for full traceability.
- **Layered test suites (A/B/C/D)** beat one-suite-fits-all: V2.1's Suite D specifically covered the new WBS chain. Version upgrades re-run only the new suite plus regression — not everything from scratch.
- **TC-D04 caught a production-critical OOM**: WF-05 Assignee distribution crashed on 44/111 of a Test Copy project because Node.js default heap size was too small. Fix: `N8N_RUNNERS_MAX_OLD_SPACE_SIZE=4096`. This bug would have been catastrophic on a real 200-task project; demos rarely use enough data to trip OOM.
- **Five-step version lock, all mandatory**: (1) update requirements_pool.yaml, (2) update VERSION file with one-line summary, (3) write CHANGELOG entry in problem→discovery→fix→verification→evidence format, (4) commit with REQ ID reference, (5) git tag with `product-prefix-semver`. Skip any one and it's not a GA, it's just a commit on main.
- **PARTIAL judgment beats green-or-fail**: TC-D02's premise expired due to a Phase G architecture change. Marking it PARTIAL (with a P3 follow-up to update the test title) preserves both honesty and shipping velocity, instead of either green-washing or blocking GA.

## Why This Matters

GA discipline is the difference between an AI product you can iterate on safely and an AI product that becomes load-bearing without any of the engineering hardening that load-bearing systems require. This article is the cleanest description we have of what "engineering rigor" looks like *for an AI workflow product specifically*, including the failure modes (OOM under real data, expired test premises, requirement drift) that don't show up in generic SWE GA guides. The Synapse framework ships with a `requirements_pool.yaml` template, the multi-agent dispatch flow for acceptance, and the version-lock SOP — borrow them as starting points.

---

*This is an abstract. Read the full article in Chinese →* [如何给 AI 产品做 GA 验收](/blog/ai-product-ga-validation-version-lock)
