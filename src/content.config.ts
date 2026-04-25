// Astro Content Collections — SSOT for typed content (Astro 6 API).
//
// Stage 5 preparation (2026-04-24, scope B, president-approved):
// - Adds `blog` collection with bilingual schema for the 33-post blog migration.
// - Keeps the pre-existing `synapse-core` collection (synced from synapse repo
//   via scripts/sync_from_core.mjs) registered without a strict schema so that
//   files with the auto-generated comment header continue to load unchanged.
//
// Astro 6 requires:
//  - this file at src/content.config.ts (not src/content/config.ts)
//  - every collection to use a loader (the `glob` loader replaces the legacy
//    implicit src/content/<name>/ behavior)
//
// Migration plan: see docs/blog-bilingual-migration-guide.md
import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const blogCollection = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    // Identity
    title: z.string(),
    slug: z.string(),
    description: z.string(),

    // Bilingual
    // - lang: which language this entry is written in
    // - translationOf: slug pointer to the counterpart entry (optional)
    // - hasEnglish: convenience flag for LangToggle / list filtering
    lang: z.enum(['zh', 'en']),
    translationOf: z.string().optional(),
    hasEnglish: z.boolean().default(false),

    // Classification (per content_strategist 33-post tagging)
    pillar: z
      .enum([
        'methodology',
        'multi-agent-case',
        'intelligence-evolution',
        'ops-practical',
      ])
      .optional(),
    priority: z.enum(['P1', 'P2', 'P3']).optional(),

    // Versioning
    publishDate: z.date(),
    updatedDate: z.date().optional(),
    version: z.string().default('1.0'),

    // Authoring
    author: z.string().default('content_strategist'),

    // SEO
    keywords: z.array(z.string()).optional(),
    coverImage: z.string().optional(),
  }),
});

// `synapse-core` is mirrored from the upstream synapse repo and uses a
// different frontmatter shape (id/type/status/lang/version/source_commit/
// published_at/...). Registering it without an explicit schema keeps the
// existing sync working while making the collection discoverable via
// getCollection().
const synapseCoreCollection = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/synapse-core' }),
});

export const collections = {
  blog: blogCollection,
  'synapse-core': synapseCoreCollection,
};
