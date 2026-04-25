---
title: "如何给 AI 产品做 GA 验收：PMO Auto V2.0 版本锁定全流程"
slug: ai-product-ga-validation-version-lock
description: "以 PMO Auto V2.0 为案例，展示 AI 原生产品从「功能完成」到「GA 锁定」需要经历的验收检查清单与版本串联动作"
lang: zh
hasEnglish: false
pillar: multi-agent-case
priority: P3
publishDate: 2026-04-24
author: content_strategist
keywords:
  - "问题日志"
  - "AI工程"
  - "Synapse"
---
## AI 产品做 GA 验收，这件事比你想的要难




我们在构建 PMO Auto，一个基于 AI 的项目管理自动化系统。它会监听 Asana 的 Webhook、自动分配负责人、生成 WBS、发送 Slack 通知。功能不复杂，但做到 2.0 版本时我意识到一件事：这个产品从来没有经历过真正意义上的 GA 验收。




所谓"真正意义"，是指：有明确的验收标准，有覆盖所有核心链路的测试套件，有从需求到版本号的完整可追溯路径，以及——出现 P0 bug 时不会在凌晨靠记忆手动回滚。这些东西，传统软件工程早就有成熟实践，但 AI 产品里却几乎是空白。我在网上找不到一篇讲清楚"如何给 AI Workflow 产品做 GA 锁定"的文章，只好自己摸索。




## 从需求池开始，而不是从代码开始




PMO Auto V2.0 的第一个教训是：需求没有结构化，验收就没有基线。我们引入了 `requirements_pool.yaml`，把每一条需求写成一个带 RICE 评分、验收标准（Acceptance Criteria）、证据链接的结构化条目。比如 REQ-001「全量项目 Asana Webhook 注册」，它的 AC 是：




1. GET /webhooks/asana/list 返回的活跃订阅数等于 target_team 下非 archived 项目总数（允许 ±1 容错）。2. 对新建项目，任务完成后 PM 在 60 秒内收到 Slack DM。3. 重复执行注册脚本，订阅数不增加，已注册项目均返回 SKIP。




这三条 AC 不是自然语言描述，是可以机械验证的测试断言。当 integration_qa 团队跑测试时，他们对着这三条逐一打 PASS/FAIL，不需要靠理解产品意图来判断——这是关键。最终 REQ-001 验收通过，`shipped_at: "2026-04-23"`、`release_tag: "v2.0-ga"`、`evidence: "obs/06-daily-reports/2026-04-23-pmo-v200-acceptance-report-ga.md"` 三个字段同步写入，形成从需求到证据的可追溯闭环。




## 测试套件分层，而不是一锅端




V2.1 验收时，我们把测试划分成了 Suite A/B/C/D 四层。Suite D 是 V2.1 专项，覆盖 WBS 全链路（WF-02 激活 → WF-01 Charter 生成 → WF-04 依赖补齐 → WF-05 Assignee 分配 → E2E 端到端）。这样分层的好处是：版本升级时只需要重跑新增套件，然后做 Regression 确认已有套件不回退。




TC-D04 是这次最有价值的一个测试用例。它在 Test Copy 项目的 111 条 WBS 工序上跑 WF-05 Assignee 分配，结果在 07:40 UTC 第一次触发时直接崩溃——n8n exec 10687 处理到 44/111 就断了，Registry 未回写 `WF05已执行=true`，系统陷入重入循环。




诊断路径：Lysander 拦截崩溃信号 → 派单 product_manager 回滚项目标记为"未维护"阻断重入 → RD 团队排查发现是 Node.js 默认堆内存不足 → n8n docker compose 注入 `N8N_RUNNERS_MAX_OLD_SPACE_SIZE=4096` → 08:35 UTC exec 10721 验证 111/111 全部通过。




这个 bug 如果不是在测试阶段被发现，而是在生产环境里一个有 200+ 工序的真实项目触发，后果是所有子任务 Assignee 为空且陷入无限重试。OOM 这类问题在 AI Workflow 产品里尤其隐蔽——因为你很少在 demo 阶段用足量数据压测。




## 版本串联：五步缺一不可




功能验收通过之后，还有一道经常被省略的步骤：版本锁定。我们要求每一个 GA 版本必须串联完成以下五步，缺一不可：




**第一步，更新 requirements_pool.yaml。**将本次发布覆盖的所有 REQ 状态从 `candidate` 改为 `shipped`，补齐 `shipped_at`、`release_tag`、`evidence` 三个字段。这是需求层面的归档，不是可选操作。




**第二步，更新 VERSION 文件。**写入新版本号，追加一行注释说明本版本核心变更。PMO Auto 的版本文件现在看起来像这样：`v2.1.0 (2026-04-24): V2.1 GA — REQ-002(L3/L4覆盖率统计) + REQ-004(WF-06幂等去重修复) + REQ-012(WBS全链路E2E验证通过)`。任何人拿到这个文件，30 秒内就能知道每个版本做了什么。




**第三步，写 CHANGELOG 条目。**按照"问题 → 发现路径 → 修复方案 → 验证 → 证据"的结构，记录本次发布的所有变更。CHANGELOG 不是给机器看的，是给未来的自己和团队成员看的——三个月后你不会记得为什么某个配置是 4096，但 CHANGELOG 会。




**第四步，提交 commit，commit message 引用 REQ ID。**例如 `feat(pmo-auto): V2.1 GA — REQ-012/002/004 shipped`。这让 git log 和需求池之间建立起双向索引。




**第五步，打 git tag。**我们用 `pmo-auto-2.1.0` 这种格式，产品线前缀 + 语义化版本号。tag 一旦打上，这个状态就固定了，哪怕后续有修复也只能出新的 patch 版本，不能回头修改已发布版本的内容。




## PARTIAL 判定：不是所有验收都是非黑即白




V2.1 的 TC-D02 给了我们另一个教训。这个用例的原始名称是「WF-03 Charter 生成验证」，但在 Phase G（2026-04-17）架构调整后，Charter 功能已经被整合进 WF-01，WF-03 被重定义为里程碑提醒。也就是说，测试用例的前提假设已经不成立了。




我们给 TC-D02 打了 PARTIAL，原因是「Charter 功能本身正常，但测试用例的架构假设已过期」。这个判定不影响 GA 签发，但它触发了一个 P3 遗留事项：Suite D 中 TC-D02 的标题需要更新。这种处理方式——区分"功能缺陷"和"用例过期"——避免了为了让所有用例变绿而强行改代码，也避免了为了赶进度而掩盖真实问题。




## 可复用的原则




回头看整个过程，我提炼出三条可以直接搬走的原则：




**验收标准在需求阶段写，不在测试阶段补。**AC 写得越晚，越容易变成描述现有行为而不是预期行为。requirements_pool.yaml 里的每一条 AC，应该在 REQ 创建时就完成，而不是等开发完成后去对齐。




**版本号是承诺，不是标签。**v2.1.0 意味着 REQ-002、REQ-004、REQ-012 的所有 AC 都通过了验证，有报告为证，有 commit 为证，有 tag 为证。如果只是功能代码合并了但没有走完五步串联，那它不是 v2.1.0，它只是 main 分支上的某个 commit。




**P0 缺陷必须在 GA 前归零。**WF-05 的 OOM 是在 V2.0 GA 后的 V2.1 Sprint 期间发现的。我们没有选择"先发 V2.1，下一版修"，而是当天修复、当天验证、当天打补丁版本 v2.0.3。这多出来的一个 patch 版本让 V2.1 的 GA 基线干净了，也让将来的人能从 CHANGELOG 里读出完整的事故处理链。




如果你在构建 AI 工程团队，欢迎参考我们开源的 Synapse 框架。它包含了完整的 Harness Engineering 规范、requirements_pool 模板、多 Agent 派单流程和版本锁定 SOP。AI 产品的工程化是一个还在被行业共同探索的问题，我们只是把自己踩过的坑整理成了可复用的结构。
