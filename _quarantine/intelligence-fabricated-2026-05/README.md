# Quarantine — Fabricated Intelligence Content (2026-05-23 → 2026-05-30)

**Status:** RETRACTED / NOT PUBLISHED. President L5① decision (2026-05-30).

These files were moved OUT of the published Astro content collections
(`src/content/intelligence/{daily,decisions,results}/`) because they are
**fabricated** — produced by the intelligence pipeline after the date-handoff
bug, which caused the generator to invent content starting ~2026-05-23. The
last genuine closed-loop output is ~2026-05-22 (left in place).

This directory is OUTSIDE every content-collection `base` glob in
`src/content.config.ts`, so these files are NOT built and will NOT appear on
the site. They are preserved in git for audit / forensics — nothing is deleted.

## Evidence of fabrication (per-file truth markers)

- **daily/2026-05-23, 05-24 (ZH+EN):** `itemCount: 0` degraded "Claude did not
  return JSON schema" raw-text dumps; 05-24 has impossible `topScore: 20` (scale is /10).
- **daily/2026-05-25 → 05-29 (ZH+EN):** invented vendor news citing
  stale/fictional versions as if new — "Claude Code 1.0 正式版 / Claude 4 Sonnet",
  "Claude 4.5 Sonnet", "Claude 4.1", "GPT-5", "n8n v1.80/v1.110/v1.30",
  "MCP v0.9/v1.3", "Cohere Embedding v4". All carry impossible composite scores
  16–19 on a /10 scale.
- **decisions/2026-05-23 → 05-30:** empty scoring matrices (`totalCount: 0`,
  `executeCount: 0`), not traceable to any real scan id.
- **results/2026-05-23 → 05-30 (ZH+EN):** action reports whose own body states the
  upstream source HTML is "(missing)" — `actionsCount: 0` (except 05-25 which
  reports on an empty `items: 0` source).

## Files quarantined

- daily (14): 2026-05-23 … 2026-05-29, ZH + EN
- decisions (6): 2026-05-23, 24, 25, 27, 28, 30
- results (12): 2026-05-23, 24, 25, 27, 28, 30, ZH + EN

## Restore (only after PG-0 foundation fix + verification)

`git mv` each file back into its original
`src/content/intelligence/{daily,decisions,results}/` directory, OR
`git revert` the retraction commit. Do NOT restore until the pipeline is fixed
and the content is re-verified as genuine.

## Regeneration risk (FLAG — not fixed here)

The GHA workflow `.github/workflows/publish-to-bond.yml` (daily cron UTC 01:30)
and the `intel-action` dispatch regenerate intel content from `synapse-ops` and
push it into `src/content/intelligence/`. Until that generator is fixed/paused,
it WILL re-create fabricated daily files here. The `/intelligence` redirects
keep the public page offline regardless, but the quarantine of daily files may
be re-populated by the next cron run. This is owned by the (not-yet-approved)
remediation rebuild — flagged, not fixed.
