#!/usr/bin/env node
/**
 * scripts/migrate-blog-to-collection.mjs
 *
 * Stage 5 / scope B (president-approved 2026-04-24):
 *   Migrate the 33 hand-written `.astro` blog pages under
 *   `src/pages/blog/*.astro` into typed Astro Content Collection
 *   entries under `src/content/blog/zh/<slug>.md`.
 *
 *   The dynamic route `src/pages/blog/[...slug].astro` consumes the
 *   collection so the existing `/blog/<slug>/` URLs stay live.
 *
 * What this script does:
 *   1. Walks `src/pages/blog/*.astro` (skips `index.astro`).
 *   2. Parses each file:
 *        - Extracts title + description from the `<Layout ...>` tag.
 *        - Extracts the publish date from the `<time>` element in the
 *          header block (falls back to the first `git log` timestamp).
 *        - Extracts the keyword/tag spans inside the header.
 *        - Extracts the inner body of the `prose prose-invert` <div>
 *          (the content area), then HTML-to-Markdown converts it.
 *   3. Classifies pillar (slug-keyword based) and priority (explicit map).
 *   4. Writes `src/content/blog/zh/<slug>.md` with the schema-aligned
 *      frontmatter required by `src/content.config.ts`.
 *
 * Idempotency: existing `.md` files are NOT overwritten unless the
 * `--force` flag is passed. The pilot file
 * `src/content/blog/zh/harness-engineering-guide.md` is therefore
 * preserved on first run.
 *
 * Side-effects: this script ONLY writes to `src/content/blog/zh/`.
 * It does NOT delete any `.astro` file. Removal of the old pages is
 * done in a separate step so the migration can be reviewed.
 */

import { execSync } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = resolve(__dirname, '..');
const PAGES_BLOG = join(REPO_ROOT, 'src', 'pages', 'blog');
const OUT_DIR = join(REPO_ROOT, 'src', 'content', 'blog', 'zh');

const FORCE = process.argv.includes('--force');

// ---------- 33-blog priority + pillar classification ------------------

const P1_SLUGS = new Set([
  'harness-engineering-guide',
  'synapse-multi-agent-evolution-framework',
  'synapse-ai-company-execution-chain-design',
  'ai-ceo-execution-chain-enforcement',
  'synapse-modular-agent-architecture-evolution',
]);

const P2_SLUGS = new Set([
  'ai-agent-deleted-my-files-safety-boundary',
  'claude-code-zero-friction-onboarding',
  'silent-failure-worse-than-errors-in-automation',
  'git-init-missing-cascading-failure-ai-agents',
  'synapse-agents-market-product-design',
  'share-ai-team-system-one-prompt',
  'ai-ceo-autonomous-decision-authority',
  'product-testing-as-ai-agent-training',
  'gstack-team-empowerment',
  'claudecode',
  'claude-code-knowledge-extraction',
]);

function classifyPriority(slug) {
  if (P1_SLUGS.has(slug)) return 'P1';
  if (P2_SLUGS.has(slug)) return 'P2';
  return 'P3';
}

function classifyPillar(slug) {
  // Order matters: more-specific keywords win.
  if (
    slug.includes('harness') ||
    slug.includes('execution-chain') ||
    slug.includes('agent-deleted') ||
    slug.includes('modular')
  ) {
    return 'methodology';
  }
  if (
    slug.includes('intelligence') ||
    slug.includes('evolution')
  ) {
    return 'intelligence-evolution';
  }
  if (
    slug.includes('ai-ceo') ||
    slug.startsWith('ai-') ||
    slug.includes('multi-agent') ||
    slug.includes('agents-market') ||
    slug.includes('story') ||
    slug.includes('case')
  ) {
    return 'multi-agent-case';
  }
  return 'ops-practical';
}

// ---------- helpers ---------------------------------------------------

function gitFirstCommitDate(astroPath) {
  // Returns ISO-8601 string of the first commit that introduced the file,
  // or null if the file is not yet tracked / git fails.
  try {
    const rel = astroPath.replace(REPO_ROOT + '\\', '').replace(/\\/g, '/');
    const out = execSync(
      `git log --diff-filter=A --format="%aI" -- "${rel}"`,
      { cwd: REPO_ROOT, encoding: 'utf-8' }
    ).trim();
    const lines = out.split('\n').filter(Boolean);
    if (lines.length === 0) return null;
    return lines[lines.length - 1]; // last line == oldest add commit
  } catch {
    return null;
  }
}

function isoDateOnly(iso) {
  if (!iso) return null;
  return iso.slice(0, 10); // YYYY-MM-DD
}

// ---------- .astro parser ---------------------------------------------

function parseLayoutAttrs(astroSrc) {
  // Match the OPENING <Layout ...> tag (props can span multiple lines).
  // Use a non-greedy match up to the first '>' that is NOT preceded by
  // an inline expression closer.
  const m = astroSrc.match(/<Layout\b([\s\S]*?)>/);
  if (!m) return { title: null, description: null };
  const attrs = m[1];

  // title="..." OR title='...' OR title={"..."}
  const titleM =
    attrs.match(/\btitle\s*=\s*"([^"]*)"/) ||
    attrs.match(/\btitle\s*=\s*'([^']*)'/) ||
    attrs.match(/\btitle\s*=\s*\{["'`]([^"'`]*)["'`]\}/);
  const descM =
    attrs.match(/\bdescription\s*=\s*"([^"]*)"/) ||
    attrs.match(/\bdescription\s*=\s*'([^']*)'/) ||
    attrs.match(/\bdescription\s*=\s*\{["'`]([^"'`]*)["'`]\}/);

  let title = titleM ? titleM[1] : null;
  // Layout title often appended " - Lysander"; strip it for the post title.
  if (title) title = title.replace(/\s*-\s*Lysander\s*$/, '').trim();
  return {
    title,
    description: descM ? descM[1] : null,
  };
}

function parseHeaderDate(astroSrc) {
  // <time class="..." >2026-04-06</time> or similar
  const m = astroSrc.match(/<time[^>]*>\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*<\/time>/);
  return m ? m[1] : null;
}

function parseHeaderTags(astroSrc) {
  // The header block has a <div class="flex gap-2"> with several
  // <span ...>tag</span>. Also catch keywords from h1 if no tags.
  const tags = [];
  const headerM = astroSrc.match(/<header[\s\S]*?<\/header>/);
  if (!headerM) return tags;
  const header = headerM[0];
  const re = /<span[^>]*>\s*([^<]{1,40})\s*<\/span>/g;
  let s;
  while ((s = re.exec(header)) !== null) {
    const t = s[1].trim();
    if (t && !tags.includes(t)) tags.push(t);
  }
  return tags;
}

function extractBodyJSX(astroSrc) {
  // Locate the <article ...> block. Inside it, the post body lives in
  // <div class="prose prose-invert ..."> ... </div> (sometimes nested
  // class names differ). Fall back to slicing between </header> and
  // <footer ...>.
  const articleM = astroSrc.match(/<article\b[\s\S]*?<\/article>/);
  if (!articleM) {
    // No <article> wrapper — these are presentation-style pages
    // (e.g. ai-application-sharing, ai-second-brain-presentation).
    // Strip <Layout>...</Layout> wrapper and the <style> block, then
    // hand the rest to the JSX-to-Markdown converter.
    let inner = astroSrc;
    // Drop the frontmatter (everything before the closing ---).
    inner = inner.replace(/^---[\s\S]*?---\s*/, '');
    // Drop <style>...</style> blocks.
    inner = inner.replace(/<style[^>]*>[\s\S]*?<\/style>/g, '');
    // Drop <script>...</script> blocks.
    inner = inner.replace(/<script[^>]*>[\s\S]*?<\/script>/g, '');
    // Strip the outer <Layout ...>...</Layout> wrapper (greedy on
    // outermost tags so we keep nested content).
    inner = inner.replace(/^[\s\S]*?<Layout\b[^>]*>/, '');
    inner = inner.replace(/<\/Layout>[\s\S]*$/, '');
    return inner;
  }
  let inner = articleM[0];

  // Prefer the prose div if present.
  const proseStart = inner.search(/<div[^>]*\bprose\s+prose-invert\b[^>]*>/);
  if (proseStart !== -1) {
    // Find matching closing </div> for that prose div.
    // Simple approach: balance <div> tags from proseStart onward.
    const after = inner.slice(proseStart);
    const openTag = after.match(/<div[^>]*>/);
    if (openTag) {
      const startInner = proseStart + openTag.index + openTag[0].length;
      let depth = 1;
      let i = startInner;
      const re = /<\/?div\b[^>]*>/g;
      re.lastIndex = startInner;
      let m;
      while ((m = re.exec(inner)) !== null) {
        if (m[0].startsWith('</')) depth -= 1;
        else depth += 1;
        if (depth === 0) {
          return inner.slice(startInner, m.index);
        }
      }
    }
  }

  // Fallback: between </header> and <footer
  const headerEnd = inner.indexOf('</header>');
  const footerStart = inner.indexOf('<footer');
  if (headerEnd !== -1) {
    const start = headerEnd + '</header>'.length;
    const end = footerStart !== -1 ? footerStart : inner.lastIndexOf('</article>');
    return inner.slice(start, end);
  }
  return inner;
}

// ---------- HTML/JSX -> Markdown (lossy but readable) -----------------

function jsxToMarkdown(jsx) {
  if (!jsx) return '';
  let s = jsx;

  // 1. Strip Astro/JSX expressions of the form {expr} that are obviously
  //    layout-only (we don't have any in body of these posts, but be safe).
  //    We DO keep things like `{post.data.title}` etc out — only happens
  //    in dynamic templates, not the static blog .astro files.

  // 2. Drop comment blocks {/* ... */} and HTML comments.
  s = s.replace(/\{\/\*[\s\S]*?\*\/\}/g, '');
  s = s.replace(/<!--[\s\S]*?-->/g, '');

  // 2.5. Convert <pre><code>...</code></pre> to fenced code blocks.
  //      Must run BEFORE inline <code>...</code> rule.
  s = s.replace(
    /<pre[^>]*>\s*<code(?:\s[^>]*)?>([\s\S]*?)<\/code>\s*<\/pre>/g,
    (_, code) => {
      const text = decodeEntities(code).replace(/\n+$/, '');
      return '\n\n```\n' + text + '\n```\n\n';
    }
  );
  // Plain <pre>...</pre> without inner <code>.
  s = s.replace(/<pre[^>]*>([\s\S]*?)<\/pre>/g, (_, code) => {
    const text = decodeEntities(code).replace(/\n+$/, '');
    return '\n\n```\n' + text + '\n```\n\n';
  });

  // 3. Convert headings: <hN ...>text</hN>  ->  ##... text
  s = s.replace(/<h([1-6])[^>]*>([\s\S]*?)<\/h\1>/g, (_, lvl, inner) => {
    const text = inlineToMd(inner).trim();
    if (!text) return '';
    const hashes = '#'.repeat(Number(lvl));
    return `\n\n${hashes} ${text}\n\n`;
  });

  // 4. Convert blockquotes
  s = s.replace(/<blockquote[^>]*>([\s\S]*?)<\/blockquote>/g, (_, inner) => {
    const text = inlineToMd(inner).trim();
    const lines = text
      .split(/\n+/)
      .map((l) => `> ${l.trim()}`)
      .filter((l) => l !== '> ');
    return '\n\n' + lines.join('\n') + '\n\n';
  });

  // 5. Convert lists. We handle <ul>/<ol> + <li>.
  s = s.replace(/<ul[^>]*>([\s\S]*?)<\/ul>/g, (_, inner) => {
    const items = [];
    const re = /<li[^>]*>([\s\S]*?)<\/li>/g;
    let m;
    while ((m = re.exec(inner)) !== null) {
      const t = inlineToMd(m[1]).trim();
      if (t) items.push(`- ${t}`);
    }
    return '\n\n' + items.join('\n') + '\n\n';
  });
  s = s.replace(/<ol[^>]*>([\s\S]*?)<\/ol>/g, (_, inner) => {
    const items = [];
    const re = /<li[^>]*>([\s\S]*?)<\/li>/g;
    let m;
    let i = 1;
    while ((m = re.exec(inner)) !== null) {
      const t = inlineToMd(m[1]).trim();
      if (t) {
        items.push(`${i}. ${t}`);
        i += 1;
      }
    }
    return '\n\n' + items.join('\n') + '\n\n';
  });

  // 6. Convert <table> with <thead>/<tbody>/<tr>/<th>/<td>.
  s = s.replace(/<table[^>]*>([\s\S]*?)<\/table>/g, (_, inner) => {
    const rows = [];
    const trRe = /<tr[^>]*>([\s\S]*?)<\/tr>/g;
    let trM;
    while ((trM = trRe.exec(inner)) !== null) {
      const cells = [];
      const cellRe = /<(t[hd])[^>]*>([\s\S]*?)<\/\1>/g;
      let cm;
      while ((cm = cellRe.exec(trM[1])) !== null) {
        cells.push(inlineToMd(cm[2]).trim().replace(/\|/g, '\\|'));
      }
      if (cells.length > 0) rows.push(cells);
    }
    if (rows.length === 0) return '';
    const widths = rows[0].length;
    const header = `| ${rows[0].join(' | ')} |`;
    const sep = `| ${Array(widths).fill('---').join(' | ')} |`;
    const body = rows.slice(1).map((r) => `| ${r.join(' | ')} |`).join('\n');
    return `\n\n${header}\n${sep}\n${body}\n\n`;
  });

  // 7. Paragraphs.
  s = s.replace(/<p[^>]*>([\s\S]*?)<\/p>/g, (_, inner) => {
    const t = inlineToMd(inner).trim();
    return t ? `\n\n${t}\n\n` : '';
  });

  // 8. <div ...>...</div> — collapse to inner content (keep text only).
  //    Repeat until stable.
  let prev;
  do {
    prev = s;
    s = s.replace(/<div[^>]*>([\s\S]*?)<\/div>/g, (_, inner) => `\n${inner}\n`);
  } while (s !== prev);

  // 9. Drop any remaining JSX wrappers we don't care about.
  s = s.replace(/<\/?(?:section|article|main|aside|figure|figcaption|nav)[^>]*>/g, '');

  // 10. Final inline pass on the whole thing for stragglers
  //     (links, code, strong/em, br, etc.).
  s = inlineToMd(s);

  // 11. Decode HTML entities and normalize whitespace.
  s = decodeEntities(s);
  s = s.replace(/[ \t]+\n/g, '\n');
  s = s.replace(/\n{3,}/g, '\n\n');
  return s.trim() + '\n';
}

function inlineToMd(html) {
  if (!html) return '';
  let s = html;

  // <a href="...">text</a>  ->  [text](href)
  s = s.replace(/<a\b([^>]*?)>([\s\S]*?)<\/a>/g, (_, attrs, inner) => {
    const hrefM = attrs.match(/\bhref\s*=\s*"([^"]*)"/);
    const href = hrefM ? hrefM[1] : '';
    const text = inlineToMd(inner).trim();
    if (!href) return text;
    return `[${text}](${href})`;
  });

  // <strong>...</strong> -> **...**
  s = s.replace(/<strong[^>]*>([\s\S]*?)<\/strong>/g, (_, t) => `**${inlineToMd(t).trim()}**`);
  s = s.replace(/<b[^>]*>([\s\S]*?)<\/b>/g, (_, t) => `**${inlineToMd(t).trim()}**`);

  // <em>...</em> / <i> -> *...*
  s = s.replace(/<em[^>]*>([\s\S]*?)<\/em>/g, (_, t) => `*${inlineToMd(t).trim()}*`);
  s = s.replace(/<i[^>]*>([\s\S]*?)<\/i>/g, (_, t) => `*${inlineToMd(t).trim()}*`);

  // <code>...</code> -> `...`
  s = s.replace(/<code[^>]*>([\s\S]*?)<\/code>/g, (_, t) => '`' + decodeEntities(t).replace(/`/g, '\\`') + '`');

  // <br />
  s = s.replace(/<br\s*\/?>/g, '\n');

  // <span ...>text</span> -> text (drop styling)
  s = s.replace(/<span[^>]*>([\s\S]*?)<\/span>/g, (_, t) => t);

  // <small>, <sup>, <sub>, <mark>, <u>, <footer ...> inline drops
  s = s.replace(/<\/?(?:small|sup|sub|mark|u|footer|header|time|cite)[^>]*>/g, '');

  return s;
}

function decodeEntities(s) {
  if (!s) return '';
  return s
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&apos;/g, "'")
    .replace(/&nbsp;/g, ' ')
    .replace(/&larr;/g, '←')
    .replace(/&rarr;/g, '→')
    .replace(/&mdash;/g, '—')
    .replace(/&ndash;/g, '–')
    .replace(/&hellip;/g, '…')
    .replace(/&amp;/g, '&'); // last
}

// ---------- frontmatter writer ----------------------------------------

function yamlEscapeString(s) {
  if (s == null) return '""';
  // If the string is "safe" (no special yaml chars), still wrap in quotes
  // for consistency. We always double-quote to preserve `:` in titles.
  return '"' + String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
}

function buildFrontmatter(meta) {
  const lines = ['---'];
  lines.push(`title: ${yamlEscapeString(meta.title)}`);
  lines.push(`slug: ${meta.slug}`);
  lines.push(`description: ${yamlEscapeString(meta.description || meta.title)}`);
  lines.push(`lang: zh`);
  lines.push(`hasEnglish: false`);
  if (meta.pillar) lines.push(`pillar: ${meta.pillar}`);
  if (meta.priority) lines.push(`priority: ${meta.priority}`);
  lines.push(`publishDate: ${meta.publishDate}`);
  lines.push(`author: content_strategist`);
  if (meta.keywords && meta.keywords.length > 0) {
    lines.push(`keywords:`);
    for (const k of meta.keywords) lines.push(`  - ${yamlEscapeString(k)}`);
  }
  lines.push('---');
  lines.push('');
  return lines.join('\n');
}

// ---------- main ------------------------------------------------------

function main() {
  if (!existsSync(OUT_DIR)) mkdirSync(OUT_DIR, { recursive: true });

  const files = readdirSync(PAGES_BLOG).filter(
    (f) => f.endsWith('.astro') && f !== 'index.astro'
  );

  const summary = [];
  for (const file of files) {
    const slug = file.replace(/\.astro$/, '');
    const astroPath = join(PAGES_BLOG, file);
    const outPath = join(OUT_DIR, `${slug}.md`);

    // Always preserve hand-tuned pilot, regardless of --force.
    const PROTECTED = new Set(['harness-engineering-guide']);
    if (existsSync(outPath) && (!FORCE || PROTECTED.has(slug))) {
      summary.push({ slug, status: 'skipped (exists)' });
      continue;
    }

    const src = readFileSync(astroPath, 'utf-8');
    const { title, description } = parseLayoutAttrs(src);
    const headerDate = parseHeaderDate(src);
    const tags = parseHeaderTags(src);
    const bodyJSX = extractBodyJSX(src);
    const bodyMd = jsxToMarkdown(bodyJSX);

    const publishDate =
      headerDate || isoDateOnly(gitFirstCommitDate(astroPath)) || '2026-04-01';

    const meta = {
      title: title || slug,
      description: description || (title || slug),
      slug,
      publishDate,
      pillar: classifyPillar(slug),
      priority: classifyPriority(slug),
      keywords: tags.slice(0, 8),
    };

    const fm = buildFrontmatter(meta);
    writeFileSync(outPath, fm + bodyMd, 'utf-8');
    summary.push({
      slug,
      status: 'written',
      title: meta.title,
      priority: meta.priority,
      pillar: meta.pillar,
      date: meta.publishDate,
      bodyChars: bodyMd.length,
    });
  }

  console.log('--- migration summary ---');
  for (const row of summary) {
    if (row.status === 'written') {
      console.log(
        `  ${row.slug.padEnd(60)}  ${row.priority}  ${row.pillar.padEnd(22)}  ${row.date}  ${row.bodyChars}c  "${row.title}"`
      );
    } else {
      console.log(`  ${row.slug.padEnd(60)}  ${row.status}`);
    }
  }
  console.log(`\nTotal files in source dir: ${files.length}`);
  console.log(`Written: ${summary.filter((s) => s.status === 'written').length}`);
  console.log(`Skipped: ${summary.filter((s) => s.status.startsWith('skipped')).length}`);
}

main();
