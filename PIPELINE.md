# Lysander.bond — Pipeline Product Governance

> Established: 2026-04-26 (v1.1.0-strategic-overhaul)
> Authority: 总裁 + Lysander
> Scope: lysander.bond website + repository

This document defines how `lysander.bond` is managed as a **pipeline product**:
all future changes flow through versioned baselines with classification,
review gates, and metric snapshots.

---

## 1. Version Convention

Following [Semantic Versioning](https://semver.org/):

| Level | Pattern | Examples | Authority | Review |
|-------|---------|----------|-----------|--------|
| **MAJOR** | `v2.0+` | Architecture rewrite / Brand pivot / Business model change | **L4 总裁审批** | Triple UAT (Product + Quality + Strategic) |
| **MINOR** | `v1.2`, `v1.3` | Strategic content / IA changes / New sections / Bilingual expansion | **L3 Lysander 决策** | Dual UAT (Product + Quality) |
| **PATCH** | `v1.1.1`, `v1.1.2` | Bug fixes / Copy polish / Link corrections / SEO tweaks | **L2 Lysander 自主** | Quality verification only |

## 2. Change Classification Tags

Every commit / PR / change-set must carry one tag:

- `strategic` — Affects 主线 story, brand, business model, or strategic content
- `feature` — New page / section / capability
- `fix` — Bug fix / regression resolution
- `chore` — Tooling / build / deploy maintenance
- `docs` — Documentation / governance / meta-rule
- `i18n` — Translation / locale routing / hreflang

## 3. Review Gates

### MAJOR Release Gate (总裁审批)
1. Product UAT (3 user persona journey walkthrough)
2. Quality UAT (HTTP / i18n / SEO / performance / regression)
3. Strategic Review (smart council: strategy_advisor + execution_auditor + decision_advisor)
4. President L4 approval
5. Version lock + git tag + CHANGELOG entry

### MINOR Release Gate (Lysander 决策)
1. Product UAT
2. Quality UAT
3. Lysander review (auto-approve if both UAT pass ≥85/100)
4. Version lock + git tag + CHANGELOG entry
5. **Brief Lysander to total office** (post-release summary)

### PATCH Release Gate (Lysander 自主)
1. Quality verification (HTTP regression + UAT spot check)
2. Version bump + CHANGELOG entry
3. No briefing needed unless P0 fix

## 4. Metric Baseline (per version)

Every version snapshot must record:

```yaml
version: vX.Y.Z
released_at: ISO date
http_health:
  total_pages_checked: N
  pass_rate: ...
seo:
  hreflang_coverage: ...
  sitemap_url_count: ...
  canonical_coverage: ...
i18n:
  bilingual_pages: ...
  ssot_drift_count: 0 (must be 0)
content:
  blog_count: N
  bilingual_blog_pct: ...
governance:
  license_present: yes/no
  ssot_synced: yes/no
```

Stored in `pipeline-metrics/v{X.Y.Z}.yaml`.

## 5. Deployment Targets

| Domain | Server | Trigger | Status |
|--------|--------|---------|--------|
| **lysander.bond** | Cloudflare Pages | push to `main` (auto via `deploy.yml`) | Active |
| **synapsehd.com** | 火山引擎 `118.196.41.252` | push to `main` (auto via `deploy-volcano.yml`) | ICP 备案中（预计 2026-04-30 激活） |

### synapsehd.com — lysander.bond 镜像分支

- **内容**：100% 同源（同一仓库 `main`，同一构建产物）
- **独立性**：无独立版本迭代，版本号与 lysander.bond 同步
- **构建差异**：`SITE_URL=https://synapsehd.com`（canonical URL 不同）
- **SSL/HTTPS**：ICP 备案通过后自动启用
- **凭证**：需 GitHub Secret `VOLCANO_SSH_KEY`（总裁手动在 GitHub Settings 配置）

## 5b. Branching Strategy

- `main` — current production baseline
- `release/v{X.Y.Z}` — release candidates (optional, for MAJOR)
- `hotfix/*` — PATCH branches off main
- `feature/*` — MINOR feature branches

## 6. Rollback Path

Each version tag is a rollback target:
```bash
git checkout v1.0-bilingual  # rollback to before strategic overhaul
```

Production rollback procedure:
1. Identify regression (UAT or post-release monitoring)
2. Lysander decides rollback target
3. `git checkout <prior-tag>` + force-deploy
4. Brief total office on rollback reason
5. Post-mortem incident report

## 7. Active Pipeline State

| Field | Value |
|-------|-------|
| Current Baseline | v1.2.0-intelligence-hub (2026-04-29) |
| Prior Stable | v1.1.0-strategic-overhaul (2026-04-26) |
| Next Planned | TBD |
| Pipeline Owner | Lysander (AI CEO) + product_manager + ai_systems_dev + integration_qa |
| AI Model | MiniMax-M2.7 |
| Intel Pipelines | intel-daily ✅ · intel-action ✅ · blog-publish ✅ (all operational) |
| Pipeline Version | 1.1.0 |
| Last Verified | 2026-05-03 |
| Pipeline Status | operational |

## 8. Decision Log

Strategic decisions are logged to `Synapse-Mini/obs/04-decision-knowledge/`:
- 2026-04-24 SSOT + i18n strategy
- 2026-04-26 Strategic overhaul + Pipeline Product framework
- 2026-04-29 Intelligence Hub launch (v1.2.0)
- 2026-05-03 Pipeline v1.1.0 operational — MiniMax-M2.7, all 3 intel pipelines verified

---

**Last updated**: 2026-05-03
**Next review**: When releasing v1.3.0 or any MAJOR version
