# Changelog

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
