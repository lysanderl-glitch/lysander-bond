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
    '/synapse/zh/pricing': '/academy',
    '/synapse/zh/get-started': '/synapse/get-started',
    '/synapse/zh/beta': '/synapse/beta',
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
    // ── /intelligence TAKEN OFFLINE (President L5② decision, 2026-05-30) ──
    // The self-evolution pipeline page is temporarily offline pending a
    // foundation fix + verification ("PG-0"). The intelligence pipeline
    // published fabricated content (date-handoff bug, ~2026-05-23+), so the
    // whole /intelligence tree is taken offline.
    //
    // Two-part take-offline (both REVERSIBLE, page source KEPT intact):
    //  1. These static-index redirects send the hub + section indexes to home.
    //  2. The dynamic detail routes (daily/[date], decisions/[id], results/[date])
    //     return an empty getStaticPaths() so no detail pages are built — see the
    //     OFFLINE guards in src/pages/(en/)intelligence/**/[date].astro & [id].astro.
    //     (Astro forbids redirecting a dynamic route to a static destination, so a
    //     redirect cannot be used for the detail routes.)
    // RESTORE: delete this block AND remove the OFFLINE guards in the detail routes.
    // Fabricated content is quarantined in _quarantine/intelligence-fabricated-2026-05/.
    // NOTE: do NOT redirect /intel — that is the separate weekly External
    // Capability Radar (ECR), unaffected by this decision.
    '/intelligence': '/',
    '/intelligence/daily': '/',
    '/intelligence/decisions': '/',
    '/intelligence/results': '/',
    '/en/intelligence': '/en/',
    '/en/intelligence/daily': '/en/',
    '/en/intelligence/decisions': '/en/',
    '/en/intelligence/results': '/en/',
  },
  vite: {
    plugins: [tailwindcss()]
  }
});
