---
title: "Notes from the Field: An n8n Workflow That Publishes to WeChat Drafts"
slug: n8n-wechat-blog-workflow
description: "An abstract of a Chinese implementation log for an n8n workflow that scrapes Astro/Tailwind blog HTML and pushes a stripped-down version to WeChat Official Account drafts."
lang: en
translationOf: n8n-wechat-blog-workflow
hasEnglish: true
pillar: ops-practical
priority: P3
publishDate: 2026-04-06
author: content_strategist
keywords:
  - "n8n"
  - "WeChat"
  - "workflow"
---

# Notes from the Field: An n8n Workflow That Publishes to WeChat Drafts

This is an abstract of a Chinese implementation log. The goal: take blog posts from a personal Astro + Tailwind site and auto-publish them to a WeChat Official Account draft box. WeChat supports a tiny subset of HTML — no `class`, no `div`/`section`/`article`, partial-only `style` — so Tailwind output renders as plain text by default. The full Chinese article documents the four-node n8n pipeline, the inline-style transformation regex set, and three n8n-specific configuration traps. Most useful for Chinese-language publishers running international tech stacks who need a one-click pipeline into WeChat.

## Key Takeaways

- **Tailwind classes must be inline-style transformed**: a JavaScript Code node strips `class` attributes and rewrites tags (`<p>`, `<h2>`, `<code>`, etc.) with explicit `style="..."` strings. WeChat will silently drop anything outside its tag allowlist.
- **n8n's `sendQuery: true` overrides URL query strings**: `access_token` must go via `queryParameters`, not appended to the URL. This trap consumed the largest debug chunk.
- **`indexOf` beats regex for nested-tag content extraction**: `class="prose"...</div>` with nested divs causes regex to terminate early. Position-based extraction with `indexOf`/`lastIndexOf` is reliable.
- **`thumb_media_id` is required**: WeChat draft API rejects submissions without an uploaded cover image's media_id. There is no way to skip this with an empty value.

## Why This Matters

WeChat Official Accounts remain the primary distribution channel for Chinese tech writing, but their HTML restrictions and API quirks aren't well-documented in English. This workflow is small enough to ship as a template but representative of a recurring pattern: bridging modern web stacks (Astro, Tailwind, headless CMS) with legacy Chinese platforms that demand a 2010-era HTML subset. The Chinese article includes the exact n8n node configurations and JS transformation snippets — treat it as a starter template if you need this pipeline yourself.

---

*This is an abstract. Read the full article in Chinese →* [n8n 微信公众号博客发布工作流开发复盘](/blog/n8n-wechat-blog-workflow)
