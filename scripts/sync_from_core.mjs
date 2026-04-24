#!/usr/bin/env node
/**
 * sync_from_core.mjs — Extract Synapse SSOT content from synapse repo.
 *
 * Clones/updates github.com/lysanderl-glitch/synapse into .cache/ and copies
 * public content (docs/public/*) into src/data/ and src/content/synapse-core/.
 *
 * Runs as npm prebuild. Idempotent; uses commit-based cache.
 *
 * Ref: SSOT plan, stage 2 (2026-04-24 approved).
 */
import { execSync } from 'node:child_process';
import { mkdirSync, existsSync, readFileSync, writeFileSync, copyFileSync, rmSync, readdirSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const CACHE_DIR = join(ROOT, '.cache', 'synapse-core');
const SYNAPSE_REPO = 'https://github.com/lysanderl-glitch/synapse.git';
const COMMIT_MARKER = join(CACHE_DIR, '.commit');
const DEST_DATA = join(ROOT, 'src', 'data', 'synapse-core');
const DEST_CONTENT = join(ROOT, 'src', 'content', 'synapse-core');

function sh(cmd, opts = {}) {
  return execSync(cmd, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], ...opts }).trim();
}

function ensureDir(p) { mkdirSync(p, { recursive: true }); }

function getCurrentRemoteCommit() {
  try {
    const out = sh(`git ls-remote ${SYNAPSE_REPO} HEAD`);
    return out.split(/\s+/)[0];
  } catch (e) {
    console.warn(`[sync] Cannot reach ${SYNAPSE_REPO}: ${e.message}`);
    return null;
  }
}

function cacheUpToDate(remoteCommit) {
  if (!remoteCommit || !existsSync(COMMIT_MARKER)) return false;
  const cached = readFileSync(COMMIT_MARKER, 'utf8').trim();
  return cached === remoteCommit;
}

function cloneOrUpdate(remoteCommit) {
  if (existsSync(CACHE_DIR)) {
    try {
      sh('git fetch --depth=1 origin main', { cwd: CACHE_DIR });
      sh('git reset --hard origin/main', { cwd: CACHE_DIR });
    } catch (e) {
      console.warn(`[sync] fetch failed, re-cloning: ${e.message}`);
      rmSync(CACHE_DIR, { recursive: true, force: true });
      ensureDir(dirname(CACHE_DIR));
      sh(`git clone --depth=1 ${SYNAPSE_REPO} ${CACHE_DIR}`);
    }
  } else {
    ensureDir(dirname(CACHE_DIR));
    sh(`git clone --depth=1 ${SYNAPSE_REPO} ${CACHE_DIR}`);
  }
  writeFileSync(COMMIT_MARKER, remoteCommit || 'unknown');
}

function copyTree(srcDir, destDir, opts = {}) {
  if (!existsSync(srcDir)) {
    console.warn(`[sync] source not found: ${srcDir}`);
    return 0;
  }
  ensureDir(destDir);
  let count = 0;
  for (const entry of readdirSync(srcDir)) {
    const s = join(srcDir, entry);
    const d = join(destDir, entry);
    const st = statSync(s);
    if (st.isDirectory()) {
      count += copyTree(s, d, opts);
    } else {
      copyFileSync(s, d);
      try {
        const body = readFileSync(d, 'utf8');
        const banner = entry.endsWith('.md')
          ? `<!-- Auto-generated from synapse@${opts.commit || 'unknown'} on ${new Date().toISOString()}; DO NOT EDIT. -->\n`
          : `# Auto-generated from synapse@${opts.commit || 'unknown'} on ${new Date().toISOString()}; DO NOT EDIT.\n`;
        if (!body.startsWith(banner.trim().slice(0, 40))) {
          writeFileSync(d, banner + body);
        }
      } catch { /* binary or unreadable, leave as-is */ }
      count++;
    }
  }
  return count;
}

function copyYamlWithBanner(src, dst, commit) {
  copyFileSync(src, dst);
  const body = readFileSync(dst, 'utf8');
  const banner = `# Auto-generated from synapse@${commit} on ${new Date().toISOString()}; DO NOT EDIT.\n`;
  if (!body.startsWith('# Auto-generated')) writeFileSync(dst, banner + body);
}

async function main() {
  console.log('[sync] starting');
  const remoteCommit = getCurrentRemoteCommit();

  if (cacheUpToDate(remoteCommit)) {
    console.log(`[sync] cache up to date (@${remoteCommit.slice(0, 7)})`);
  } else {
    console.log('[sync] syncing cache...');
    cloneOrUpdate(remoteCommit);
  }

  const publicDir = join(CACHE_DIR, 'docs', 'public');
  if (!existsSync(publicDir)) {
    console.error('[sync] docs/public/ not found in synapse repo; skipping');
    process.exit(0);  // non-fatal; let build proceed
  }

  // Clear previous sync output
  for (const d of [DEST_DATA, DEST_CONTENT]) {
    if (existsSync(d)) rmSync(d, { recursive: true, force: true });
  }
  ensureDir(DEST_DATA);
  ensureDir(DEST_CONTENT);

  const commit = (remoteCommit || 'unknown').slice(0, 7);
  const opts = { commit };

  let total = 0;

  // onboarding-steps.yaml → src/data/synapse-core/
  const onboardingSrc = join(publicDir, 'onboarding-steps.yaml');
  if (existsSync(onboardingSrc)) {
    copyYamlWithBanner(onboardingSrc, join(DEST_DATA, 'onboarding-steps.yaml'), commit);
    total++;
  } else {
    console.warn('[sync] onboarding-steps.yaml not found');
  }

  // glossary/glossary.yaml → src/data/synapse-core/glossary.yaml
  const glossarySrc = join(publicDir, 'glossary', 'glossary.yaml');
  if (existsSync(glossarySrc)) {
    copyYamlWithBanner(glossarySrc, join(DEST_DATA, 'glossary.yaml'), commit);
    total++;
  } else {
    console.warn('[sync] glossary/glossary.yaml not found');
  }

  // methodology/*.md → src/content/synapse-core/methodology/
  const mDir = join(publicDir, 'methodology');
  if (existsSync(mDir)) {
    total += copyTree(mDir, join(DEST_CONTENT, 'methodology'), opts);
  } else {
    console.warn('[sync] methodology/ not found');
  }

  console.log(`[sync] copied ${total} files from synapse@${commit}`);
}

main().catch(e => {
  console.error('[sync] fatal:', e);
  process.exit(1);
});
