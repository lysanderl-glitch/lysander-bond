// intelManifest.ts — DE-5 frontend manifest reader (INTEL-PIPELINE-REMEDIATION v3 Phase 3)
//
// The DE-4 run-manifest (mirrored from synapse-ops into the `intelligence-manifest`
// content collection) is the structural truth ledger of the intel pipeline. DE-5
// makes the frontend DECIDE WHAT TO DISPLAY from this manifest instead of trusting
// the mere existence of a brief file:
//
//   - GREEN day      → the pipeline genuinely produced content → render real items.
//   - DEGRADED/empty → honest-empty day (今日无新情报 / 重建中) — render the honest
//                       empty state, NEVER stale-as-fresh or fabricated content.
//   - absent/unhealthy → no trustworthy manifest → honest-empty (fail-closed).
//
// This is the read side only. The page stays OFFLINE behind the existing redirects /
// getStaticPaths guards until the PG-0 restore (a separate, President-final step);
// wiring the display logic does NOT make the page live.
//
// The PURE decision logic (decideHubDisplay / latestTrustworthy / ringStatuses /
// RING_STEPS) lives in ./intelManifestCore.mjs so it is unit-testable in plain Node
// (scripts/test_de5_manifest_logic.mjs, PR-6) without an Astro build. This file adds
// ONLY the astro:content-dependent loader on top.
import { getCollection } from 'astro:content';
import {
  RING_STEPS,
  latestTrustworthy,
  decideHubDisplay,
  ringStatuses,
  sortOverallsByDateDesc,
} from './intelManifestCore.mjs';

export { RING_STEPS, latestTrustworthy, decideHubDisplay, ringStatuses };

export type OverallStatus = 'green' | 'degraded' | 'unhealthy';

export interface StageVerdict {
  present: boolean;
  status: string | null;
  fresh: boolean;
  fault: string | null;
  item_count: number;
  honest_empty: boolean;
}

export interface OverallManifest {
  date: string;
  status: OverallStatus;
  stages: Record<string, StageVerdict>;
  findings: string[];
  real_content: boolean;
}

export interface HubDisplay {
  mode: 'genuine' | 'honest-empty';
  topDate: string | null;
  overall: OverallManifest | null;
}

function isOverallEntryId(id: string): boolean {
  // Collection ids are dir-prefixed without extension, e.g. "2026-05-31/_overall".
  return id.endsWith('/_overall') || id === '_overall';
}

function dateFromOverallId(id: string): string {
  const parts = id.split('/');
  return parts.length >= 2 ? parts[parts.length - 2] : '';
}

/**
 * Load every `_overall.json` manifest entry, newest date first.
 * Returns [] when the collection is empty or unavailable (fail-closed).
 */
export async function loadOverallManifests(): Promise<OverallManifest[]> {
  let entries: any[] = [];
  try {
    entries = await getCollection('intelligence-manifest');
  } catch {
    return [];
  }
  const overalls: OverallManifest[] = [];
  for (const e of entries) {
    if (!isOverallEntryId(String(e.id))) continue;
    const d = (e.data ?? {}) as Partial<OverallManifest>;
    const date = (d.date as string) || dateFromOverallId(String(e.id));
    if (!date) continue;
    overalls.push({
      date,
      status: ((d.status as OverallStatus) ?? 'unhealthy'),
      stages: (d.stages as Record<string, StageVerdict>) ?? {},
      findings: (d.findings as string[]) ?? [],
      real_content: Boolean(d.real_content),
    });
  }
  return sortOverallsByDateDesc(overalls) as OverallManifest[];
}
