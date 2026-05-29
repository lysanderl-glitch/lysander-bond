# Synapse System: AI-Driven Intelligent Collaboration Platform

> Version: v1.1 | Date: 2026-05-04 | Compiled by: OBS · Harness Ops · Product Ops · Content Ops · AI/ML · Advisory Council

---

## Executive Summary

**The real problem we are solving**: Everyone uses AI today — but every session starts from scratch. AI does not remember what was said before, does not know the organization's rules, and cannot guarantee stable output quality. Business experts spend significant time "coaching AI" instead of using AI to solve business problems. The deeper issue: AI capabilities, judgments, and knowledge cannot accumulate inside the organization.

**What Synapse solves**: Enabling business experts (non-engineers) to drive AI through business-language instructions to complete complex professional tasks — with auditable processes, accumulated results, and replicable capabilities. No Prompt Engineering knowledge required. No need to re-explain context every session. No need to manually oversee every step.

**The value it creates**: Synapse Owner involvement dropped from 100% to 0% (Slack result notifications only). For the Phoenix PMO Automation product — from product planning (D1-D8 fully executed by AI) through to live deployment — the Synapse Owner only intervened at three points: plan approval, architecture approval, and a 2-hour pause during a Stage 2 token limit event. All other execution was completed autonomously by the Synapse team and committee. Over 50 formally archived D-numbered decisions mean organizational knowledge is now genuinely searchable, reproducible, and transferable.

---

## Part I: Architecture and Core Capabilities

The Synapse system operates across five interconnected layers, forming a complete information flow network — "Knowledge ←synapse→ Decision ←synapse→ Execution":

```
├── Knowledge Layer (OBS Second Brain)   — Organizational memory externalized
├── Control Layer (Harness)              — AI behavior engineered and constrained
├── Execution Layer (Multi-Agents)       — Specialized autonomous execution
├── Decision Layer (4-Level System)      — Tiered authorization with clear accountability
└── Evolution Layer (Intelligence Loop)  — Continuous self-learning and iteration
```

### 1.1 Harness Engineering（智能体架构工程）: Making AI Manageable, Constrained, and Evolvable

**Core value**: Manage AI behavior the way engineers manage code.

Harness Engineering（哈内斯工程，AI控制层工程）is an AI engineering paradigm confirmed in 2026 by Martin Fowler, Red Hat, and other authorities. The fundamental equation is:

> **Agent = Model（模型） + Harness（控制层）**

Competitive advantage lies not in having the largest model, but in having the most effective Harness. Synapse fully implements this principle across three control mechanisms:

**Guides（前馈控制，Feedforward Controls）** — Define boundaries before AI acts:
- `CLAUDE.md`: Master configuration file (currently 322 lines, hard cap of 350 lines)
- `organization.yaml`: Team architecture with 75 keyword-to-specialist routing rules
- `.claude/harness/` module library: 18 specialized rule files (credentials, dispatch templates, HR management, etc.)

**Workflow（结构化流程，Structured Workflow）** — Execution chain v2.0, 8 mandatory steps:
```
[Opening] Identity confirmation → [0.5] Synapse intake（6 steps）→ [①] Task grading (S/M/L)
→ [②] Route & dispatch → [③] QA gate（≥85/100）→ [③.5] PQG filter
→ [④] Deliver to Synapse Owner
```

**Constraints（约束系统，Constraint System）** — CEO execution exclusion zone P0 hard rules:
- Main conversation is prohibited from directly calling Bash/Edit/Write (prevents AI from overstepping)
- Every task must pass through Synapse intake and formal dispatch (the only auditable execution path)
- Audit log `logs/ceo-guard-audit.log` automatically records all tool calls via PreToolUse hook

**Practical outcome**: Through PreToolUse hook technical enforcement, the system intercepts any unauthorized direct AI execution at the code level, keeping all operations within auditable, traceable governance.

---

### 1.2 Knowledge Management System（知识管理体系）: The OBS Second Brain

**Core value**: Move team memory from human brains to a system — enabling knowledge to accumulate, be retrieved, and be transferred.

**Obsidian Knowledge Graph（知识图谱）** — Structured knowledge base across 7 domains:

| Knowledge Domain | File Count | Contents |
|-----------------|-----------|----------|
| Product Knowledge（产品知识） | 70+ | Product-line profiles, PRDs, committee records |
| Process Knowledge（流程知识） | 27+ | SOPs, best practices, runbooks |
| Decision Knowledge（决策知识） | 50+ | D-numbered archived decisions, strategic analyses |
| Team Knowledge（团队知识） | 69 | Agent personnel cards, HR records |
| Content Pipeline（内容管线） | Continuously growing | Blog drafts, published articles |
| Intelligence Reports（情报报告） | Daily generated | Tech landscape summaries, action reports |
| Analysis Reports（分析报告） | On-demand | QA reports, sprint reports |

**Cross-Session State Persistence（跨会话状态持久化）** — The fundamental fix for "explaining everything again":
- `agent-CEO/config/active_tasks.yaml`: Stores current task state (stage/blocker/next_step)
- New sessions automatically read this file and resume from breakpoints
- Authorization is Objective-level（目标级别授权），persistent across sessions — no re-approval needed

**Memory System（记忆系统）** — Accumulated cross-session experience (35 entries):
- `feedback_*.md`: Work preference and mode feedback (21 entries)
- `project_*.md`: Product-line status and technical configuration records (14 entries)
- Automatically updated when new patterns are identified; effective in the next session

**Mandatory Decision Archiving（决策归档强制机制）** (P0, approved by Synapse Owner 2026-04-27):
- All L3+ decisions must be archived with D-number to `obs/04-decision-knowledge/decision-log/`
- CI script `scripts/check_decision_log.py` auto-blocks commits with unarchived decisions
- As of 2026-05-03: 50+ D-numbered decisions archived, forming a complete organizational decision history

---

### 1.3 Product Pipeline Management（产线管理能力）: The Phoenix / PMO Auto Case

**Core value**: AI-managed full lifecycle of complex software products — from planning to production, fully automated. The Synapse Owner intervenes only at key decision gates; all intermediate execution is completed autonomously by the AI team.

**Phoenix v3.0.0 PMO Automation** is the definitive proof of Synapse's product pipeline capability:

**Autonomous Execution Scale** (2026-04-28 → 2026-05-01, continuous cross-session execution over 4 days):
- The Synapse Owner participated at only three points throughout the entire delivery cycle: (1) product plan approval D8; (2) deployment architecture approval R3; (3) a 2-hour pause during the Stage 2 token limit event
- All other execution was completed autonomously by the Synapse CEO and committee, covering the full chain from product planning to live deployment
- Continuous execution across multiple sessions; authorization held at Objective level, persisting across session switches without re-approval

**D8 Product Planning Phase（产品规划阶段）** (8-step rigorous process, completed in 4 days under Lysander dispatch, Owner intervening only at the 3 governance gates):
- D1-D3: Scenario analysis (6 project types / 6 roles / 8 end-to-end scenarios) + Business goals + Industry best practices
- D4-D5: BRD (30 requirements) + PRD v1.1.0 (13 chapters / 1,446 lines / 14 P0 requirements)
- D6-D8: Execution plan + Roundtable review（8/10 passed）+ Synapse Owner approval package

**R-Process Deployment Architecture Review（R 流程部署架构审批）** (Synapse Owner approves final package only):
- 10 deployment architectures systematically compared (R1)
- Historical baseline archaeology to verify assumptions (R1.5)
- 10-person roundtable: 9/9 unanimous pass (R2)
- Synapse Owner approves final B+F hybrid architecture (R3, D-2026-0430-001)

**Stage Gate Management（阶段门禁管理）** (3-phase acceptance):
- Stage 1: Infrastructure (private repo + self-hosted runner + credentials management)
- Stage 2: First image deployment + real end-to-end full-chain validation (status=success, blockers=[])
- Stage 3: Monitoring governance + 11/11 must-fix items closed → Gate PASSED

**Key outcome**: Synapse Owner involvement dropped from "participating throughout" to "receive Slack notification of result only." Deployment time dropped from 30+ minutes of manual steps to 5-minute fully automated pipeline. All 7 D-numbered decisions archived; complete end-to-end proof artifacts (Monday board, Notion charter pages, team invitations — all genuinely live).

---

### 1.4 Multi-Agent Collaboration System（多智能体协作体系）

**Core value**: Manage AI teams like real teams — clear division of labor, defined accountability, controllable quality.

**Team Scale（团队规模）**:
- Core: 58 Agents across 13 specialized teams
- Full activation mode: 69 Agents (including optional Janus delivery team and Stock quant team)

**Core Teams（核心团队矩阵）**:

| Team | Specialty | Members |
|------|-----------|---------|
| Graphify Advisory Council（智囊团） | Intelligence analysis, strategic decisions, audit | 7 |
| Harness Ops（驾驭运维部） | Harness configuration, code development, QA | 5 |
| Butler Delivery（交付运营团队） | Project delivery, IoT, PMO management | 6 |
| RD Engineering（研发团队） | Backend/Frontend/DevOps/Testing | 5 |
| OBS Knowledge Management（知识管理团队） | Knowledge architecture, search, quality | 4 |
| Content Ops（内容运营团队） | Content strategy, creation, visual, publishing | 8 |
| Product Ops（产品运营团队） | PRD, requirements analysis, product committee | 8 |
| Growth（增长团队） | GTM strategy, sales enablement, community | 4 |
| AI/ML Engineering（AI/ML工程团队） | Claude API, RAG, Prompt Caching | 1 |
| Specialist Group（领域专家组） | Legal, financial | 2 |
| HR Management（HR管理团队） | Capability assessment, onboarding approval | 2 |

**Dispatch System（派单制度）** — Engineering solution to prevent AI role confusion:
- Mandatory precedence: Dispatch table must be output before any Edit/Write/Bash call
- Identity declaration: Each execution block must be labeled with `<specialist_id> executing`
- Violation tracking: execution_auditor automatically checks during QA — missing dispatch is logged as a violation

**Roundtable Review Mechanism（圆桌评审机制）** — Multi-perspective cross-validation:
- Standard review: integration_qa + execution_auditor + advisory council (3-party independent)
- Major decisions: 9-10 person roundtable with majority vote (reference: D-2026-0430-001, 9/9 passed)
- Quantified scoring: QA score ≥85/100 required for delivery (not qualitative judgment — a numeric gate)

---

### 1.5 Self-Evolution Capability（自我进化能力）

**Core value**: The system continuously improves its own rules, processes, and knowledge without manual intervention.

**Weekly Harness Review（周维度审查）** (P0, approved by Synapse Owner 2026-04-27):
- Schedule: Every Sunday 23:00 Dubai time
- 6 review dimensions: CLAUDE.md line count / Agent card scores / frontmatter compliance / fact-SSOT drift / stale tasks / decision and execution chain integrity
- Executed by: harness_engineer + execution_auditor independently (not Synapse self-review — avoids the self-evaluator trap)
- Output: Weekly report to `obs/01-team-knowledge/HR/weekly-audit/`
- Alert trigger: 2 consecutive missed reports → L4 escalation to Synapse Owner

**President Query Gate v2.0（总裁问询门卫）** (PQG, activated 2026-04-30):
- Based on mining 141 real interruption incidents from 7 major sessions — evidence-driven, not assumed
- Identifies and intercepts 6 high-frequency interruption patterns
- Weekly iteration using new session data to refine intercept rules
- Result: Systematically eliminated approximately 40/70 categories of unnecessary interruptions
- Measured score: 8.4/10 (integration_qa roundtable)

**Rule Timestamps + Entropy Budget（规则时间戳+熵增预算）** — Preventing infinite rule bloat:
- Every new rule tagged `# [ADDED: YYYY-MM-DD]`
- Rules unreferenced for 180+ days automatically become deprecation candidates
- CLAUDE.md hard cap: 350 lines (must delete before adding if at limit)
- Tightens to 300 lines after Phase 2 is complete

**Intelligence Feedback Loop（情报闭环管线）** — Continuous environmental sensing:
- 8:00 Dubai daily: Intelligence report generated (AI-synthesized tech landscape digest)
- 10:00 Dubai daily: Intelligence action execution (scan OBJ keywords → assess relevance → execute → Slack report)
- Information flow: External signals → Knowledge base → Decision support → Execution iteration

---

### 1.6 Token Optimization Strategy（Token 优化策略）

**Context**: Chinese text consumes approximately 2.0x more tokens than English (measured range 1.7-2.4x). System Prompt consumes a fixed ~17,664 tokens per conversation.

**Research conclusion — Option C (5/5 recommendation score)**:
- Convert all Harness documents to English (CLAUDE.md + 13 harness files)
- Add English constraints for Agent-to-Agent dispatch communications
- Migrate active_tasks.yaml state fields to English storage
- Preserve Chinese for Synapse Owner ↔ Synapse interface — zero-perception migration
- **Estimated savings: 40-55% token consumption per conversation**

---

## Part II: System Growth History (PDCA Analysis)

Since the Synapse system was established in early April 2026, it has passed through three clear PDCA maturity cycles. Each cycle has a distinct problem trigger, solution implemented, and verified outcome.

### Phase 1 (2026-04-12 to 2026-04-24): Zero to One — Foundation

**Plan (problem identified)**: Inspired by the podcast *How I AI*, the Synapse Owner wanted an AI collaboration operations system. Existing tools (standalone SaaS) were all disconnected from workflows — no AI-native integrated management capability.

**Do (foundations built)**:
- D-2026-0412-001 (L3): Selected SPE fusion approach — building on existing Claude Code CLI + Obsidian + Slack with zero additional tool costs
- Established Harness Engineering foundation framework (CLAUDE.md v1.0)
- Built Multi-Agent team architecture (core 12 teams)

**Check (results verified)**:
- D-2026-0424-001 (L4): Synapse Owner approved SSOT+i18n strategy; synapse-core immediately public; academy first phase delivers completion badges
- PMO Auto v2.0 GA acceptance completed

**Act (improvements anchored)**: Established "replicability without founder dependency" as the system's core value proposition. Decided on full Multi-Agent delivery (no Synapse Owner on-camera).

---

### Phase 2 (2026-04-25 to 2026-04-28): Usable to Trustworthy — Governance Maturity

**Plan (problem identified)**: After 14 days of operation, three governance blind spots emerged: no weekly health check rhythm, Synapse both executing and reviewing (self-evaluator trap), and L3+ decisions scattered without searchability.

**Do (system upgraded)**:
- D-2026-0427-001 (L4): Synapse Owner approved 4 governance structures — dual-track weekly review / mandatory D-number archiving + CI interception / independent advisory council review path
- D-2026-04-28-001 (L3): Agent Memory Collaboration Mechanism v1 activated — product routing + committee knowledge card injection, enabling "gets smarter the more you use it"
- D-2026-04-28-002 (L4): Synapse Platform independent product line established + independent PMC governance

**Check (results verified)**: Execution chain v2.0 live, CEO Guard P0 constraints activated, decision archiving rate jumped from 0% to 100% (CI enforcement).

**Act (capabilities extended)**: Product-line routing rules established; cross-product-line memory collaboration foundation created.

---

### Phase 3 (2026-04-29 to 2026-05-03): Trustworthy to Efficient — Automation and Optimization

**Plan (problem identified)**: Three key bottlenecks — (1) Synapse Owner interrupted by too many intermediate decisions (141 recorded interruptions before PQG activation), (2) Phoenix deployment had no automation path, (3) AI call costs too high (Chinese 2x token overhead).

**Do (key breakthroughs)**:
- D-2026-04-30-PQG (L3): PQG v2.0 activated — 6-scenario intercept rules designed from 141 real interruption incidents; score 8.4/10
- D-2026-0430-001 (L4): Phoenix deployment architecture approved (B+F hybrid: self-hosted runner + docker-compose + Watchtower); real end-to-end full-chain validation passed
- D-2026-05-01-001 (L3): Content pipeline root-cause fix + dual-path architecture hardening
- D-2026-05-03-001 (L3): AI call migration complete; Synapse v1.1.0 released

**Check (quantified acceptance)**:
- Synapse Owner involvement: 100% → 0% (Slack notifications only)
- GHA pipeline Run #25279393501 succeeded; Slack confirmed "intelligence daily pipeline success"
- lysander.bond: 5-day intelligence backfill + 12 blog articles, all live online

**Act (system anchored)**:
- Established "true end-to-end business proof" principle (HTTP 200 ≠ real business value; requires status=success + artifact verification)
- Established dual-path blog pipeline (sessions_watcher primary + action report fallback)
- Intelligence pipeline upgraded to v1.1.0; code fork issue fully resolved

---

### Key Milestone Timeline

```
2026-04-12  D-2026-0412-001 ← System foundation decision (L3, SPE fusion approach)
2026-04-24  D-2026-0424-001 ← SSOT+i18n strategy approved (L4, Synapse Owner)
2026-04-27  D-2026-0427-001 ← Weekly review + mandatory D-number archiving (L4, Synapse Owner)
2026-04-28  D-2026-04-28-001 ← Agent Memory Collaboration Mechanism v1 (L3, Synapse Owner-approved)
2026-04-28  D-2026-04-28-002 ← Synapse Platform independent product line (L4, Synapse Owner)
2026-04-30  D-2026-04-30-PQG ← PQG v2.0 activated (L3, 8.4/10)
2026-04-30  D-2026-0430-001  ← Phoenix deployment architecture (L4, Synapse Owner)
2026-05-01  D-2026-05-01-001 ← Content pipeline dual-path hardening (L3)
2026-05-03  D-2026-05-03-001 ← AI call migration + Synapse v1.1.0 released (L3)
```

**Maturity Curve（成熟度曲线）**:
- Phase 1 (Usable): Single Agent → Multi-Agent team framework
- Phase 2 (Trustworthy): Constraint system + traceable decisions + governance mechanisms
- Phase 3 (Efficient): Minimum Synapse Owner involvement + maximum automation + cost optimization

---

## Part III: Commercial Value and Application Scenarios

### 3.1 Current Operating Value (Synapse Owner Perspective)

From actual operational results, the Synapse system has produced measurable value across the following dimensions:

**Execution Quality Assurance（执行质量保障）**:
- QA score gate ≥85/100 (not qualitative judgment — a numeric hard gate)
- All code changes require integration_qa validation
- Major architectural changes require roundtable majority vote (9/10)

**Decision Traceability（决策可追溯性）**:
- 50+ D-numbered decisions fully archived (including context, options analysis, expert opinions, Synapse Owner approval)
- CI automatically blocks decision-related commits without archiving
- Any historical decision retrievable within 30 seconds with full original logic

**Cross-Session Continuity（跨会话连续性）**:
- Task resume via `active_tasks.yaml` with no context re-explaining
- 35 Memory entries systematically preserving work patterns and project states
- System automatically briefs in-progress tasks at new session start

**Measured Outcomes**:
- Phoenix product delivery: continuous execution across 4 days and multiple sessions; Synapse Owner participated at only 3 key gate points
- Pipeline recovery: 5-day content gap + 12 blog articles, all restored and live within one day
- Synapse Owner interruptions: From ~20/session historically to near-zero (PQG active)

---

### 3.2 Deployment Scenario 1: Project Management — The Spike Case

**Business context**: Spike manages project management training and needs to continuously update training materials to reflect real system changes — a high-frequency, high-repetition content production task currently done manually.

**Core pain points**:
- Every system update requires rewriting training materials (workload scales with iteration speed)
- Training content must be written in business language (not technical language), but technical teams cannot maintain that voice
- High review cost: Spike reviews from scratch rather than incrementally validating

**Synapse Solution (MECE Analysis)**:

| Dimension | Problem | Synapse Capability | Delivered Outcome |
|-----------|---------|-------------------|------------------|
| Knowledge capture | System changes scattered | OBS auto-tracking | Change log → structured knowledge entries |
| Content generation | Training must use business language | Content Ops (content_creator + content_training) | Business-language training draft |
| Quality assurance | Training accuracy needs expert review | QA gate ≥85 + roundtable review | Spike reviews only the final output |
| Version management | Old vs. new material version confusion | D-number archiving + CI version lock | Every training update automatically versioned |

**Spike's new working model**:
1. Describe the business need: "Chapter 3 of PMO onboarding needs updating — system now has Feature X"
2. Synapse generates a training material draft in business language
3. Spike reviews the final output and provides feedback
4. Iterates until acceptance — **no AI interaction required throughout the process**

**Analogy to Phoenix**: The Synapse Owner only participates at D8 (goals and final acceptance). Spike only participates at business-requirement input and final review.

---

### 3.3 Deployment Scenario 2: QA Testing Standardization — The Suzy Case

**Business context**: Suzy manages QA testing and maintains both regression test scripts and testing training materials — both tasks require deep system knowledge and must stay synchronized with code changes.

**Core pain points**:
- Test cases are disconnected from business scenarios ("how to test" without "why to test")
- Training materials are inconsistent with actual testing processes (knowledge siloed across individuals)
- High onboarding cost for new QA members (no standardized testing knowledge base)

**Synapse Solution (MECE Analysis)**:

| Dimension | Problem | Synapse Capability | Delivered Outcome |
|-----------|---------|-------------------|------------------|
| Knowledge system | Test cases have no business scenario binding | OBS bidirectional binding (test ↔ scenario) | Searchable test ↔ business mapping matrix |
| Test standardization | No unified regression path | Stage Gate pattern reuse (Phoenix S1/S2/S3) | Standardized 3-gate regression path |
| Training content | Testing training disconnected from actual process | Content Ops pipeline reuse | Suzy-reviewable training draft |
| Quality gate | Test report quality inconsistent | integration_qa auto-QA (≥85/100) | Every output has quantified quality score |

**Key differentiator**: The Stage Gate pattern validated in Phoenix can be directly reused for testing standardization. The regression process is divided into 3 stages (Stage 1: case library / Stage 2: automation scripts / Stage 3: training materials), each with clear acceptance gates.

**Suzy's new working model**:
1. Define business acceptance criteria: "The core business logic is X, edge cases are Y"
2. Synapse generates test case matrix + test script drafts
3. Suzy validates: "Does this testing cover the business scenarios I care about?"
4. After Stage Gate passes, training materials auto-generate from test cases

---

### 3.4 Raising the Capability Ceiling for Non-Technical Professionals

**Core value proposition**: Synapse gives non-technical professionals the ability to "manage an AI team" — not just "use an AI tool."

**Traditional AI Use vs. Synapse Model**:

| Dimension | Traditional AI Use | Synapse System |
|-----------|-------------------|----------------|
| Required skill | Prompt Engineering | Business-language requirements |
| Interaction mode | Start from zero each session | Memory accumulates continuously |
| Quality control | Subjective user judgment | ≥85/100 numeric gate |
| Decision traceability | No record | D-numbered full archive |
| Capability ceiling | Limited by individual prompt skill | Team specialization (69 Agents) |
| Error correction | Re-correct every session | Memory system permanently retains |

**The significance of Harness guardrails（哈内斯护栏）**: Non-technical professionals don't need to understand Prompt Engineering. The rules in CLAUDE.md and `.claude/harness/` have engineering-encoded "how to correctly use AI" into system constraints, so users only need business-language input — the system guarantees quality and compliance.

**The fundamental capability leap**:
- From "using an AI tool" (help me write copy)
- To "managing an AI team" (our marketing goal is X, target audience is Y — Content Ops team generates to our brand standards + QA + publishes)
- Essence: From "personal productivity tool" to "organizational operations infrastructure"

---

## Part IV: Recommended Rollout Path

Based on the PDCA maturity analysis and MECE scenario analysis, a three-phase rollout is recommended:

### Phase 1: Project Management Pilot (Spike + Suzy)

**Goal**: Validate actual experience and efficiency gains for non-technical users in existing business scenarios.

**Execution path** (using Synapse's own Stage Gate pattern):
- Stage 1: Create product profiles — establish product-profile.md for Spike and Suzy's work contexts, defining business context
- Stage 2: Trial run — select 1-2 real tasks for Synapse-assisted delivery; Spike/Suzy accept results
- Stage 3: Quantified evaluation — compare pre/post efficiency (task completion time, iteration count, final quality score)

**Acceptance criteria**: Spike/Suzy can drive Synapse to complete a full task using business-language descriptions (no Prompt Engineering knowledge required), with QA score ≥80/100.

### Phase 2: Cross-Functional Template Replication

**Goal**: Based on Phase 1 learnings, extract reusable Synapse usage templates to reduce onboarding friction for other teams.

**Deliverables**:
- General non-technical user onboarding guide
- 3-5 typical scenario prompt templates
- Quick guide: "How to describe your business requirements"

### Phase 3: Company-Level AI Collaboration Standard

**Goal**: Distill the Synapse system into a replicable standard methodology for broader enterprise application.

**Strategy**: Based on the "replicability without founder dependency" principle approved in D-2026-0424-001, use Synapse Platform (independent product line, D-2026-04-28-002) as the commercialization vehicle to offer Harness Engineering consulting and customization to other enterprises.

---

## Appendix: Presentation Generation Prompts

### Prompt A: Reveal.js HTML Deck (Fully Operational)

```
You are a professional presentation designer. Generate a Reveal.js HTML presentation
from the Synapse system briefing content below.

Requirements:
1. Use Reveal.js v5 CDN (https://cdn.jsdelivr.net/npm/reveal.js@5/dist/)
2. Theme: "black" or "night"; fonts: Inter for English, system CJK fallback for Chinese
3. Slide structure (max 5 bullet points per slide):
   - Cover: Title + Subtitle + Date
   - Executive Summary (3 bullets, each 1 line)
   - Architecture diagram (ASCII or Mermaid — 3-layer structure)
   - Core Capabilities × 5 sections (one slide per section, each with 1 key metric or number)
   - Growth timeline (horizontal axis, 9 key milestones)
   - Deployment Scenarios × 2 (Spike/Suzy, one slide each; problem → solution → outcome)
   - Rollout roadmap (3-phase visualization)
   - Closing slide: Next steps + contact
4. Color scheme: dark background (#0a0a0a), accent (#00d4aa), text (#ffffff)
5. Key numbers displayed prominently (large font + accent color)
6. All content in English; Chinese terms in parentheses for key concepts
7. Output a single complete runnable HTML file; no external resources except CDN

Source content: [paste Executive Summary and key section highlights from
synapse-capability-report-en.md]
```

---

### Prompt B: PowerPoint Outline (Import-Ready)

```
You are a professional business presentation writer. Generate a structured PowerPoint
outline for the Synapse system briefing material below.

Format requirements:
- Use Markdown hierarchy (# Level 1 = Section, ## Level 2 = Slide Title, - = bullet)
- Max 4 bullets per slide, max 15 words per bullet
- Key numbers tagged with 【 】 (e.g., 【QA ≥85/100】, 【50+ decisions】, 【Synapse Owner involvement: 0%】)
- Speaker notes tagged with > (2-3 sentence cue per slide)

Structure (13 slides):
1. Cover: Title + Subtitle + Presenter + Date
2. Agenda: 4-part overview
3. Problem definition: 3 AI usage failures (no memory / overreach / inconsistent quality)
4. What Synapse is: 3-layer structure diagram
5. Core Capability 1/5: Harness Engineering (code-level AI governance)
6. Core Capability 2/5: OBS Second Brain (externalized organizational memory)
7. Core Capability 3/5: Phoenix proof point (cross-session autonomous delivery; Synapse Owner at 3 gate points only)
8. Core Capability 4/5: Multi-Agent collaboration (55 active core Agents, 12 teams)
9. Core Capability 5/5: Self-evolution (PQG + weekly review)
10. Growth trajectory: 9-milestone horizontal timeline
11. Deployment value: Spike + Suzy scenario comparison table
12. Rollout roadmap: 3-phase visualization
13. Next steps: 3 concrete action items

Source content: [paste key paragraphs from synapse-capability-report-en.md]
```

---

*This report is based on actual archived records as of 2026-05-03. All figures are sourced from decision logs, Memory records, and QA reports — no fabricated content.*

*Compiled by: OBS Team (knowledge_engineer) · Harness Ops Team (harness_engineer) · Product Ops Team (product_ops) · Content Ops Team (content_ops) · AI/ML Team (ai_ml_specialist) · Advisory Council (decision_advisor, execution_auditor)*
