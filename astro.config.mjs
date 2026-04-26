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
  integrations: [sitemap()],
  // 2026-04-23: Nginx deployment does not honor Cloudflare _redirects
  // format. Astro's native redirects config generates static HTML pages
  // with meta-refresh, which works on any static host (Nginx, Cloudflare,
  // etc.). Maps old /synapse/zh/* URLs to the new default-locale paths.
  redirects: {
    '/synapse/zh': '/synapse',
    '/synapse/zh/': '/synapse/',
    '/synapse/zh/capabilities': '/synapse/capabilities',
    '/synapse/zh/how-it-works': '/synapse/how-it-works',
    '/synapse/zh/team': '/synapse/team',
    '/synapse/zh/intelligence': '/synapse/intelligence',
    '/synapse/zh/pricing': '/synapse/pricing',
    '/synapse/zh/get-started': '/synapse/get-started',
    '/synapse/zh/beta': '/synapse/beta',
    // 2026-04-26: IA consolidation — services/training/intelligence pages
    // merged into Synapse pricing + intelligence sub-pages.
    '/services': '/synapse/pricing',
    '/training': '/synapse/pricing',
    '/intelligence': '/synapse/intelligence',
    '/en/services': '/en/synapse/pricing',
    '/en/training': '/en/synapse/pricing',
    '/en/intelligence': '/en/synapse/intelligence',
    // Academy placeholder pages removed (decision ②A 2026-04-26).
    '/academy/dashboard': '/academy',
    '/academy/course': '/synapse/pricing',
    '/en/academy/dashboard': '/en/academy',
    '/en/academy/course': '/en/synapse/pricing',
  },
  vite: {
    plugins: [tailwindcss()]
  }
});
