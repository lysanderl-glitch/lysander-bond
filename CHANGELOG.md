# Changelog

## v1.1.0-strategic-overhaul — 2026-04-26

战略级改造完成，元规则修复，进入"管线产品"治理框架

### Strategic Refactor (基于总裁 2026-04-26 L4 决策)
- **决策 ①B**：网站 0 处 "Janus Digital" / "建筑数字化" 残留；Synapse 为唯一品牌
- **决策 ②A**：Academy SaaS 订阅模式删除（$99/$999 移除）
- **决策 ③A**：品牌统一 — "Synapse Forge" → "Synapse"
- **决策 ④A**：BSL-1.1 LICENSE + 双语 USAGE_TERMS
- **决策 ⑤A**：终身 Pro 承诺保留兑现

### IA Restructure (产品视角)
- 主导航 8 项 → 5 项（产品 / 上手 / 博客 / 定价 / 关于）
- /services /training /intelligence 顶级页删除（301 redirects）
- /academy/dashboard /academy/course 占位页删除
- about.astro 创始人段重构（"Synapse 体系作者" + "AI CEO 角色"双身份）
- /synapse/index hero 重写（去 Janus + Forge → Synapse）

### Meta Rule (元规则修复)
- **44/46/50 Agent 数字漂移根治**：synapse-stats.yaml SSOT 上线（53 unique / 13 modules / 5 presets）
- generate-stats.mjs 自动计数脚本（synapse 仓）
- proposal.md 顶部 note 解释 46/11 是设计快照
- fact-ssot-rule.md 元规则文档（公开版 + 私有版）

### Marketing Strategy Adjustment (推广策略调整)
- /synapse/beta CTA: "Founding 30 Apply Now" → "Currently invitation-only"
- mailto Beta 申请入口移除
- 主导航不暴露 Beta 入口

### Governance (治理护栏)
- LICENSE.md (BSL-1.1) — 4 年 Change Date 自动转 Apache-2.0
- USAGE_TERMS.md (中英双语)
- README.md "Limited Preview — Internal Testing" banner

### Bug Fixes
- /synapse/version.json.ts 数字 44 → 53
- 博客 description 残留清理（"总裁您好，我是 Lysander..." 模板污染）

### Pipeline Product Framework Established
本版本起，lysander.bond 进入"管线产品"治理框架：
- 三层版本约定（MAJOR/MINOR/PATCH）
- MINOR+ 变更必须双轮 UAT
- 度量基线：每版本记录 HTTP/SEO/NPS/DAU 快照

详见 PIPELINE.md。

---

## v1.0-bilingual — 2026-04-25

全站 100% 中英双语化达成

### Architecture
- Astro 6 native i18n integration (zh default, /en/ prefix)
- Forge URL migration: /synapse/* (ZH) + /en/synapse/* (EN)
- Content Collections for 33 blog articles with bilingual schema
- LangToggle: global langtoggle in Header, meta-driven blog detection
- Static 301 redirects via Astro config (Nginx-compatible)
- Build pipeline silent failure root-caused & fixed (set -e + git reset --hard)

### Content Bilingualization (54 pages × 2 = 108 URLs)
- Main site: 5 P0 pages (home/services/training/intelligence/about)
- Forge: 8 pages (overview/capabilities/how-it-works/team/intelligence/pricing/get-started/beta)
- Academy: 7 pages (index/get-synapse/team/skills/learn/dashboard/course)
- Blog: 34 articles (5 P1 full re-creation + 9 P2 translations + 20 P3 abstracts)

### SEO + i18n Compliance
- hreflang zh-CN + en + x-default on every page
- canonical link tied to current locale
- sitemap-0.xml: 110 URLs (55 ZH + 55 EN, 1:1 balance)
- robots.txt with sitemap declaration

### Bug Fixes (UAT 8 findings resolved)
- Layout: Header/Footer links respect lang prop
- /en/synapse/get-started: GitHub URL fix
- /academy/get-synapse: Step 2 added + Step 3 localized
- Home /: Hero/CTA/Sections localized to Chinese
- Agent count unified to 44 across all pages
- Forge ZH "Learn more" → "了解更多"
- Cross-page brand consistency improvements

### Governance
- Bilingual blog production SOP v1.1 (mandatory for new posts)
- Synapse SSOT in github.com/lysanderl-glitch/synapse with docs/public/
- frontmatter 12-field standard + glossary.yaml + content-frontmatter-spec.md
- frontmatter_lint.py validator (warning mode → 2026-07-23 strict)
- sync_from_core.mjs build-time SSOT extractor

### Deploy
- GitHub Actions SSH deploy to /home/ubuntu/website
- Cloudflare-style _redirects retained as backup (Nginx active path uses Astro static redirects)
