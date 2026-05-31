// intelManifestCore.mjs — DE-5 PURE manifest decision logic (no astro:content dep).
//
// The genuine-vs-honest-empty decision and the ring-status mapping are pure data
// transforms with NO Astro/content-collection dependency, so they live here and are
// (a) re-exported by intelManifest.ts for the frontend, and (b) unit-tested directly
// with Node (scripts/test_de5_manifest_logic.mjs, PR-6) without an Astro build.
//
// _overall.json schema (written by synapse-ops manifest_aggregate.py):
//   { date, status: 'green'|'degraded'|'unhealthy', stages: {stage:
//     {present,status,fresh,fault,item_count,honest_empty,...}}, findings, real_content }

// The 5 canonical pipeline stages, in display order (DE-5: keep 5 steps).
export const RING_STEPS = [
  { stage: 'scan', step: '01', en: 'Scan', zh: '扫描' },
  { stage: 'daily', step: '02', en: 'Bulletin', zh: '快报' },
  { stage: 'action', step: '03', en: 'Decision', zh: '决策' },
  { stage: 'outcome', step: '04', en: 'Track', zh: '追踪' },
  { stage: 'evolution', step: '05', en: 'Evolve', zh: '演进' },
];

/**
 * Sort overall-manifest objects newest-date-first. Pure; returns a new array.
 */
export function sortOverallsByDateDesc(overalls) {
  return [...overalls].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );
}

/**
 * The most-recent manifest whose status is green or degraded (a recorded,
 * trustworthy day). 'unhealthy' days are skipped. Returns null when none.
 * Assumes input is already newest-first (or sorts defensively).
 */
export function latestTrustworthy(overalls) {
  const sorted = sortOverallsByDateDesc(overalls);
  for (const o of sorted) {
    if (o.status === 'green' || o.status === 'degraded') return o;
  }
  return null;
}

/**
 * Hub display decision, derived ENTIRELY from the manifest. Genuine ONLY when the
 * latest trustworthy day is green AND produced real content; otherwise honest-empty
 * (fail-closed). Never renders stale-as-fresh or fabricated content.
 */
export function decideHubDisplay(overalls) {
  const latest = latestTrustworthy(overalls);
  if (latest && latest.status === 'green' && latest.real_content) {
    return { mode: 'genuine', topDate: latest.date, overall: latest };
  }
  return { mode: 'honest-empty', topDate: null, overall: latest };
}

/**
 * Per-ring-step status, bound to the manifest stages. 'idle' when no manifest.
 */
export function ringStatuses(overall) {
  return RING_STEPS.map((s) => {
    const v = overall && overall.stages ? overall.stages[s.stage] : undefined;
    let state = 'idle';
    if (v) {
      if (v.fault) state = 'failed'; // failed/stale/any fault → not-green
      else if (v.status === 'green' && (v.item_count || 0) > 0) state = 'green';
      else if (v.status === 'empty' || v.honest_empty) state = 'empty';
      else if (v.status === 'green') state = 'green';
    }
    return { ...s, state };
  });
}
