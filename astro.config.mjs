// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from "@tailwindcss/vite";
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: process.env.SITE_URL || 'https://lysander.bond',
  output: 'static',
  // Stage 4 Step 1 (2026-04-24): Astro 6 native i18n preparation.
  // - Chinese is the default locale (no URL prefix, stays at `/`).
  // - English is served from `/en/*` once `src/pages/en/` files are added.
  // - No page files moved yet; Forge URL migration is deferred to next
  //   session (see obs/04-decision-knowledge/2026-04-24-stage4-i18n-
  //   architecture-plan.md) pending Lysander review.
  i18n: {
    defaultLocale: 'zh',
    locales: ['zh', 'en'],
    routing: {
      prefixDefaultLocale: false
    }
  },
  integrations: [
    sitemap({
      // 2026-11-15: 归档内容不进站点地图（Synapse 体系已下线）。
      filter: (page) => !page.includes('/archive/'),
    }),
  ],
  // 2026-04-23: Nginx deployment does not honor Cloudflare _redirects
  // format. Astro's native redirects config generates static HTML pages
  // with meta-refresh, which works on any static host (Nginx, Cloudflare,
  // etc.). Maps old /synapse/zh/* URLs to the new default-locale paths.
  redirects: {
    '/synapse/zh': '/archive/synapse',
    '/synapse/zh/': '/archive/synapse/',
    '/synapse/zh/capabilities': '/archive/synapse/capabilities',
    '/synapse/zh/how-it-works': '/archive/synapse/how-it-works',
    '/synapse/zh/team': '/archive/synapse/team',
    '/synapse/zh/intelligence': '/archive/synapse/intelligence',
    '/synapse/zh/pricing': '/academy',
    '/synapse/zh/get-started': '/archive/synapse/get-started',
    '/synapse/zh/beta': '/archive/synapse/beta',

    // ========================================================
    // 2026-11-15 — Synapse 体系归档下线
    // 决策：Synapse 经验证不再适用于当前规划，内容页整体移至
    // /archive/synapse/*（保留可追溯），并从主导航移除。
    // 页面本身带 robots noindex 且已排除出 sitemap。
    // ⚠️ 不要重定向 /synapse/version.json 与 /api/synapse/version.json —
    //    那是已安装客户端轮询的版本检查端点，必须留在原路径。
    // ========================================================
    '/synapse': '/archive/synapse',
    '/synapse/beta': '/archive/synapse/beta',
    '/synapse/capabilities': '/archive/synapse/capabilities',
    '/synapse/cases': '/archive/synapse/cases',
    '/synapse/compare': '/archive/synapse/compare',
    '/synapse/get-started': '/archive/synapse/get-started',
    '/synapse/glossary': '/archive/synapse/glossary',
    '/synapse/how-it-works': '/archive/synapse/how-it-works',
    '/synapse/intelligence': '/archive/synapse/intelligence',
    '/synapse/principles': '/archive/synapse/principles',
    '/synapse/team': '/archive/synapse/team',
    '/en/synapse': '/en/archive/synapse',
    '/en/synapse/beta': '/en/archive/synapse/beta',
    '/en/synapse/capabilities': '/en/archive/synapse/capabilities',
    '/en/synapse/get-started': '/en/archive/synapse/get-started',
    '/en/synapse/how-it-works': '/en/archive/synapse/how-it-works',
    '/en/synapse/intelligence': '/en/archive/synapse/intelligence',
    '/en/synapse/team': '/en/archive/synapse/team',
    // 2026-04-26: IA consolidation — services/training/intelligence pages
    // merged into Synapse pricing + intelligence sub-pages.
    '/services': '/academy',
    '/training': '/academy',
    '/en/services': '/en/academy',
    '/en/training': '/en/academy',
    // Pricing pages removed (2026-04-28): redirect to academy.
    '/synapse/pricing': '/academy',
    '/en/synapse/pricing': '/en/academy',
    // Academy placeholder pages removed (decision ②A 2026-04-26).
    '/academy/dashboard': '/academy',
    '/academy/course': '/academy',
    '/en/academy/dashboard': '/en/academy',
    '/en/academy/course': '/en/academy',
    // NOTE: do NOT redirect /intel — that is the separate weekly External
    // Capability Radar (ECR), unaffected by this section.
    // /intelligence RESTORED (2026-06-01): page redesigned with new BRD v1.1 design.
    // The OFFLINE redirects have been removed. The OFFLINE guards in detail routes
    // remain for now (no fresh content yet), but the hub pages are fully live.
  },
  vite: {
    plugins: [tailwindcss()]
  }
});
