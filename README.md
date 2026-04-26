# lysander.bond — Synapse public site

> **Limited Preview — Internal Testing.** By using, you accept LICENSE
> ([BSL-1.1](./LICENSE.md)) + [USAGE_TERMS](./USAGE_TERMS.md). Synapse is
> currently being refined with internal teams; external access opens once
> readiness criteria are met.

This repo is the public site for **Synapse** — an AI team operating
system built on Harness Engineering. The site is built with Astro and
deployed via GitHub Actions.

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
