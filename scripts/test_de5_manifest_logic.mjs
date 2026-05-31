// test_de5_manifest_logic.mjs — DE-5 frontend manifest-decision probes (Phase 3, PR-6)
//
// Proves the manifest-DRIVEN display decision (genuine vs honest-empty + ring binding)
// without an Astro build. Pure logic from src/lib/intelManifestCore.mjs.
//
//   PR-6a  a GREEN day with real content → genuine mode, topDate = that date.
//   PR-6b  a DEGRADED (honest-empty) day → honest-empty mode (no stale-as-fresh).
//   PR-6c  an UNHEALTHY-only history → honest-empty (fail-closed).
//   PR-6d  no manifest at all → honest-empty (fail-closed), ring all 'idle'.
//   PR-6e  most-recent trustworthy date wins (date-align: a newer green beats older).
//   PR-6f  ring binds per-stage status: green→green, empty→empty, failed/stale→failed.
//
// Run: node scripts/test_de5_manifest_logic.mjs
import assert from 'node:assert/strict';
import {
  decideHubDisplay,
  latestTrustworthy,
  ringStatuses,
  RING_STEPS,
} from '../src/lib/intelManifestCore.mjs';

let passed = 0;
function ok(name) { passed++; console.log(`  ok ${name}`); }

function greenStages(itemCount = 3) {
  const s = {};
  for (const st of RING_STEPS) {
    s[st.stage] = { present: true, status: 'green', fresh: true, fault: null, item_count: itemCount, honest_empty: false };
  }
  return s;
}
function emptyStages() {
  const s = {};
  for (const st of RING_STEPS) {
    s[st.stage] = { present: true, status: 'empty', fresh: true, fault: null, item_count: 0, honest_empty: true };
  }
  return s;
}

// PR-6a — green + real_content → genuine
{
  const overalls = [{ date: '2026-05-31', status: 'green', stages: greenStages(), findings: [], real_content: true }];
  const hub = decideHubDisplay(overalls);
  assert.equal(hub.mode, 'genuine');
  assert.equal(hub.topDate, '2026-05-31');
  ok('PR-6a green+real_content → genuine, topDate set');
}

// PR-6b — degraded (honest-empty) → honest-empty
{
  const overalls = [{ date: '2026-05-31', status: 'degraded', stages: emptyStages(), findings: [], real_content: false }];
  const hub = decideHubDisplay(overalls);
  assert.equal(hub.mode, 'honest-empty');
  assert.equal(hub.topDate, null);
  ok('PR-6b degraded/honest-empty → honest-empty (no stale-as-fresh)');
}

// PR-6c — only unhealthy days → honest-empty (fail-closed)
{
  const overalls = [{ date: '2026-05-31', status: 'unhealthy', stages: {}, findings: ['scan: missing'], real_content: false }];
  const hub = decideHubDisplay(overalls);
  assert.equal(hub.mode, 'honest-empty');
  assert.equal(latestTrustworthy(overalls), null);
  ok('PR-6c unhealthy-only → honest-empty (fail-closed)');
}

// PR-6d — no manifest → honest-empty + ring all idle
{
  const hub = decideHubDisplay([]);
  assert.equal(hub.mode, 'honest-empty');
  const ring = ringStatuses(null);
  assert.equal(ring.length, 5);
  assert.ok(ring.every((r) => r.state === 'idle'));
  ok('PR-6d no manifest → honest-empty, ring all idle, still 5 steps');
}

// PR-6e — most-recent trustworthy date wins (date-align)
{
  const overalls = [
    { date: '2026-05-29', status: 'green', stages: greenStages(), findings: [], real_content: true },
    { date: '2026-05-31', status: 'green', stages: greenStages(), findings: [], real_content: true },
    { date: '2026-05-30', status: 'unhealthy', stages: {}, findings: [], real_content: false },
  ];
  const hub = decideHubDisplay(overalls);
  assert.equal(hub.topDate, '2026-05-31'); // newest green, not the unhealthy 05-30 nor older 05-29
  ok('PR-6e most-recent green date wins (date-align, skips unhealthy)');
}

// PR-6f — ring binds per-stage status
{
  const stages = greenStages();
  stages.daily = { present: true, status: 'empty', fresh: true, fault: null, item_count: 0, honest_empty: true };
  stages.action = { present: true, status: 'green', fresh: false, fault: 'stale', item_count: 1, honest_empty: false };
  stages.outcome = { present: false, status: null, fresh: false, fault: 'missing', item_count: 0, honest_empty: false };
  const ring = ringStatuses({ date: '2026-05-31', status: 'green', stages, findings: [], real_content: true });
  const byStage = Object.fromEntries(ring.map((r) => [r.stage, r.state]));
  assert.equal(byStage.scan, 'green');
  assert.equal(byStage.daily, 'empty');
  assert.equal(byStage.action, 'failed');   // stale → not-green
  assert.equal(byStage.outcome, 'failed');  // missing/fault → not-green
  ok('PR-6f ring binds per-stage: green/empty/stale→failed/missing→failed');
}

console.log(`\nDE-5 manifest logic: ${passed} checks OK`);
