---
title: 归档说明
---

# Synapse 体系已归档（2026-11-15）

本目录内容原由 `scripts/sync_from_core.mjs` 在每次构建前（npm prebuild）
从 https://github.com/lysanderl-glitch/synapse 自动拉取。

**决策**：Synapse 体系经验证不再适用于当前规划，整体归档下线。

**本次变更**：
- `prebuild` 自动同步已停用，本目录冻结为归档快照，不再跟随上游更新。
- 目录内容仅作历史留存，站内无任何页面渲染它。
- 页面内容已迁至 `/archive/synapse/*`，带 robots noindex，并已排除出 sitemap。

**如需恢复同步**：在 `package.json` 的 scripts 中重新加入
`"prebuild": "node scripts/sync_from_core.mjs"`，或手动执行 `npm run sync-content`。
