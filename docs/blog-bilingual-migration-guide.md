# Blog Bilingual Migration Guide

> Stage 5 preparation, scope B (president-approved 2026-04-24).
> Owner: ai_systems_dev / content_strategist.

## Context

The blog currently consists of **33 hand-written `.astro` single-page files**
under `src/pages/blog/*.astro`. Each post is a self-contained component with
hard-coded layout, classes, and Chinese content. This setup blocks the
bilingual rollout because:

- No typed schema (every page invents its own frontmatter shape)
- No way to declare "post X has an English translation"
- No way to render the same content with different layouts per locale
- No way to query / filter posts by pillar, priority, or language

## Target architecture

Astro 6 Content Collections + dynamic routes:

```
src/
├── content.config.ts                      ← schema (Astro 6 location)
└── content/
    └── blog/
        ├── zh/
        │   ├── harness-engineering-guide.md   ← Chinese (default)
        │   └── ...                            ← all 33 posts here
        └── en/
            ├── harness-engineering-guide.md   ← English (P1 first batch)
            └── ...                            ← only translated posts

src/pages/
├── blog/
│   ├── index.astro                        ← ZH list (uses getCollection)
│   └── [...slug].astro                    ← ZH dynamic route (deferred)
└── en/
    └── blog/
        ├── index.astro                    ← EN list
        └── [...slug].astro                ← EN dynamic route
```

Schema (already implemented in `src/content.config.ts`):

```typescript
{
  title, slug, description,
  lang: 'zh' | 'en',
  translationOf?: string,     // points at counterpart slug
  hasEnglish: boolean,        // for LangToggle / filtering
  pillar?: 'methodology' | 'multi-agent-case' | 'intelligence-evolution' | 'ops-practical',
  priority?: 'P1' | 'P2' | 'P3',
  publishDate: Date,
  updatedDate?: Date,
  version: string,            // default '1.0'
  author: string,             // default 'content_strategist'
  keywords?: string[],
  coverImage?: string,
}
```

## Migration steps (per post)

For each `src/pages/blog/<slug>.astro`:

1. **Extract frontmatter** from the `<Layout>` props and `<header>` block
   (title, description, publish date, tags → keywords).
2. **Extract body** — convert the JSX-with-Tailwind body into clean Markdown.
   The bespoke component decorations (gradient cards, colored tags, custom
   tables) become standard Markdown; the dynamic route's `Layout` will
   re-apply consistent styling via `prose prose-invert`.
3. **Classify** — set `pillar` and `priority` based on the
   content_strategist 33-post tagging matrix.
4. **Write** to `src/content/blog/zh/<slug>.md` with full frontmatter.
5. **Decide bilingual scope**:
   - P1 → translate to `src/content/blog/en/<slug>.md`, set `hasEnglish: true`
     on both files; cross-link via `translationOf: <slug>`.
   - P2/P3 → leave `hasEnglish: false`; LangToggle shows ZH only.
6. **Delete** `src/pages/blog/<slug>.astro` **only after** the dynamic route
   is in place AND the Markdown version has been visually QA'd.

## Compatibility window

While migration is in progress:

- **Both routes coexist**. Old `.astro` files remain at `src/pages/blog/*.astro`.
  New `[...slug].astro` dynamic route MUST exclude any slug that still has a
  matching `.astro` file (Astro raises a duplicate-route error otherwise).
  Pattern:

  ```typescript
  export async function getStaticPaths() {
    const stillAstro = new Set([
      'harness-engineering-guide',
      // ... slugs of posts not yet migrated
    ]);
    const entries = await getCollection('blog', ({ data }) =>
      data.lang === 'zh' && !stillAstro.has(data.slug)
    );
    return entries.map(entry => ({
      params: { slug: entry.data.slug },
      props: { entry },
    }));
  }
  ```

  Each migration PR shrinks `stillAstro` and removes the `.astro` file in the
  same commit, keeping the URL stable for users.

- **`/blog/index.astro`** can switch to `getCollection('blog')` early because
  it aggregates posts and is not URL-conflicting.

## Phasing

| Phase | Scope | Outcome |
|-------|-------|---------|
| 0 (this PR) | Schema + 1 pilot Markdown + this guide | Build green; no route changes |
| 1 | Dynamic route `[...slug].astro` with exclusion list; migrate 5 P1 posts | URLs unchanged; `/blog/index` reads collection |
| 2 | Migrate remaining 28 posts in batches of 5–10 | All `src/pages/blog/*.astro` deleted except `index.astro` |
| 3 | English translations for 14 P1 posts | `/en/blog/*` live; LangToggle wired |
| 4 | English translations for P2/P3 (optional, on demand) | Full bilingual coverage |

## Constraints honored by phase 0

- 33 existing `.astro` files **untouched**
- No new route created (`[...slug].astro` deferred to phase 1)
- No new dependencies (Astro 6 native Content Collections + `glob` loader)
- Build passes (`npm run build` → 68 pages, all original routes intact)

## References

- `src/content.config.ts` — schema source of truth
- `src/content/blog/zh/harness-engineering-guide.md` — pilot entry
- `src/pages/blog/harness-engineering-guide.astro` — original (still live)
- Astro 6 Content Collections docs:
  https://docs.astro.build/en/guides/content-collections/
