---
id: "D-2026-0428-021-intelligence-hub-launch"
title: "D-2026-0428-021：Intelligence Hub 上线"
date: "2026-04-28"
publishDate: 2026-04-28T00:00:00.000Z
decisionLevel: "L3"
decidedBy: "Lysander"
summary: "建立 lysander.bond `/intelligence/` 三层路由体系："
lang: zh
tags:
  - 执行决策
  - L3
---

# D-2026-0428-021：Intelligence Hub 上线

## 决策内容

建立 lysander.bond `/intelligence/` 三层路由体系：
- `/intelligence/` — Hub 总览（三栏布局）
- `/intelligence/daily/[date]` — 每日情报快报详情
- `/intelligence/decisions/[id]` — 执行决策记录
- `/intelligence/results/[date]` — 执行结果报告

## 关键修复

| Bug | 根因 | 修复 |
|-----|------|------|
| 构建持续失败 | Astro 6 废弃 `post.render()`，改为 `render(post)` | 3个动态路由文件全部修复 |
| /intelligence 路由不可达 | astro.config.mjs 遗留 redirect 覆盖实际页面 | 删除 redirect 条目 |
| 主导航无情报入口 | Layout.astro 主导航无 intelligence 链接 | 新增"情报/Intel"导航项 |

## 防复发措施

见 `obs/03-process-knowledge/astro-content-layer-pitfalls.md`

## Commits

- `0f0bd0f` — Astro 6 render API fix + redirect 删除
- `9bc2538` — 主导航情报入口
- `13fa216` — 三卡片入口 + Hero CTA
- `fec8870` — 历史数据回填（43个文件）
- `499d044` — Intelligence Hub 前端页面
