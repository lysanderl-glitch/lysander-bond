# lysander.bond

> **Limited Preview — Internal Testing.** By using, you accept LICENSE
> ([BSL-1.1](./LICENSE.md)) + [USAGE_TERMS](./USAGE_TERMS.md).

Astro 静态站点，经 GitHub Actions 构建后部署到自有服务器（nginx）。

## ⚠️ 2026-11-15 — Synapse 体系已归档下线

Synapse（基于 Harness Engineering 的 AI 团队操作系统）经验证不再适用于
当前规划，相关内容整体归档：

| 项目 | 处置 |
| :--- | :--- |
| 内容页（18 个 zh/en） | 迁至 `/archive/synapse/*`，带 `robots noindex`，已排除出 sitemap |
| 旧 URL | 由 `astro.config.mjs` 的 `redirects` 静态重定向到归档路径，不产生 404 |
| 主导航「产品 / Product」 | 已移除 |
| 首页 / 情报页推广入口 | 已移除 |
| `src/content/synapse-core` | 冻结为归档快照，`prebuild` 自动同步已停用（见 `ARCHIVED.md`） |
| `src/components/synapse/*` | 原地保留，仅供归档页使用 |

**刻意保留未动**：
- `/synapse/version.json` 与 `/api/synapse/version.json` —— 已安装客户端
  轮询的版本检查端点，迁移会使其失效。
- `src/content/blog/**` 中涉及 Synapse 的历史文章 —— 属于历史写作记录，
  本次未在归档范围内。

**待办**：首页与 `/intelligence` 的正文文案仍在描述 Synapse，待新定位
（数字分身板块）确定后统一改写；主导航的产品入口同步补回。

## 🚀 Project Structure

Inside of your Astro project, you'll see the following folders and files:

```text
/
├── public/
├── src/
│   └── pages/
│       └── index.astro
└── package.json
```

Astro looks for `.astro` or `.md` files in the `src/pages/` directory. Each page is exposed as a route based on its file name.

There's nothing special about `src/components/`, but that's where we like to put any Astro/React/Vue/Svelte/Preact components.

Any static assets, like images, can be placed in the `public/` directory.

## 🧞 Commands

All commands are run from the root of the project, from a terminal:

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `npm install`             | Installs dependencies                            |
| `npm run dev`             | Starts local dev server at `localhost:4321`      |
| `npm run build`           | Build your production site to `./dist/`          |
| `npm run preview`         | Preview your build locally, before deploying     |
| `npm run astro ...`       | Run CLI commands like `astro add`, `astro check` |
| `npm run astro -- --help` | Get help using the Astro CLI                     |

## CI/CD Status

✅ GitHub Actions CI/CD configured - Auto-deploy on push to main

## 👀 Want to learn more?

Feel free to check [our documentation](https://docs.astro.build) or jump into our [Discord server](https://astro.build/chat).
