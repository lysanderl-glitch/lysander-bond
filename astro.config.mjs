// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from "@tailwindcss/vite";
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://lysander.bond',
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
  vite: {
    plugins: [tailwindcss()]
  }
});
