<!-- Auto-generated from synapse@36ab925 on 2026-04-24T17:39:28.209Z; DO NOT EDIT. -->
---
id: content-frontmatter-spec
type: core
status: published
lang: en
version: 1.0
published_at: 2026-04-24
updated_at: 2026-04-24
author: [knowledge_engineer, harness_engineer]
review_by: [decision_advisor, execution_auditor]
audience: [content_strategist, knowledge_engineer, technical_builder]
stale_after: 2026-10-24
---

# Content Frontmatter Specification

## Purpose

All content exported from `synapse/docs/public/` or published downstream (Synapse Forge, Synapse Academy, Synapse Blog, and any future surfaces derived from this repository) MUST declare a YAML frontmatter block with the twelve fields defined in this specification.

This spec is a **public contract** under `docs/public/_manifest.yaml` and follows the stability policy declared there (SemVer, breaking changes bump the major version, removals require a deprecation notice for at least one minor version).

The frontmatter contract enables:

- **Automated governance** — `scripts/audit_content.py`, `scripts/frontmatter_lint.py`, and `scripts/translation_status.py` all read these fields to produce the weekly knowledge-base health report.
- **Single Source of Truth (SSOT) tracking** — `source_commit` propagation makes it possible to answer "which upstream synapse-core commit produced this downstream page?" for any Forge/Academy page.
- **Entropy budget enforcement** — `stale_after` feeds the 180-day stale-candidate review defined in the harness-governance rules.
- **Breaking-change detection** — CI fails when a downstream consumer references an `id` whose `version` has bumped its major number without an accompanying migration note.
- **Translation accountability** — `translation_of` + `source_commit` together make it trivial to detect when a `zh` translation has fallen behind its `en` original by more than N commits.

## Scope

This specification applies to:

- All Markdown files under `docs/public/` in `synapse-core`.
- All Markdown pages in downstream repositories (`synapse-forge`, `synapse-academy`, `synapse-blog`) whose content derives from `synapse-core`.
- All YAML files under `docs/public/` that represent structured content (manifests, glossaries, onboarding step lists). YAML files use a top-level `_meta:` key instead of `---` delimiters but carry the same fields.

It does NOT apply to:

- Internal operational documents (`agent-CEO/**`, `obs/**`, `logs/**`).
- Source code, configuration files, CI workflows, or ADRs.
- Draft content not yet under `docs/public/`.

## The 12 Fields

### Identity (3 fields)

- **`id`** (string, required) — Globally unique identifier, kebab-case, lowercase, no file extension. Example: `content-frontmatter-spec`. Once assigned, an `id` MUST NOT change; changing it is equivalent to deleting one document and creating another.
- **`type`** (enum, required) — One of:
  - `core` — Foundational methodology or architectural spec. Changes require L2 review.
  - `living` — Living document expected to change frequently (CHANGELOG, roadmap, version manifests). `stale_after` is optional for living docs.
  - `reference` — Structured reference content (glossary, API spec, onboarding steps). Changes require diff review against downstream consumers.
  - `narrative` — Long-form editorial content (blog posts, case studies). Lower review overhead, but still carries `author` + `review_by`.
  - `private` — Declared private; MUST NOT appear in `_manifest.yaml`. Present only as a signal that the content was deliberately kept internal.
- **`status`** (enum, required) — One of `draft`, `review`, `published`, `deprecated`. Only `published` documents may be referenced from `_manifest.yaml` and from downstream repositories.

### Language & Translation (2 fields)

- **`lang`** (enum, required) — `en` or `zh`. Bilingual pages exist as two separate files with matching structure, linked through `translation_of`.
- **`translation_of`** (string, optional) — The `id` of the source document when this document is a translation. When present, this document MUST also carry a `source_commit` pointing to the upstream commit that was translated.

### Versioning (4 fields)

- **`version`** (SemVer string, required) — The document's own version, independent of the Synapse Core release version. Start at `1.0`. Bump minor for additive changes, major for breaking changes.
- **`source_commit`** (git short hash, required for synced content) — The `synapse-core` commit this downstream copy was derived from. Required in Forge/Academy/Blog copies; optional in the `synapse-core` original.
- **`synapse_version`** (SemVer string, optional) — The Synapse Core release this content is known to map to. Useful for version-gated content such as "upgrading from 2.x to 3.x".
- **`published_at`** (ISO date, required) — Date of first publication. Never changes after set.
- **`updated_at`** (ISO date, required) — Date of the most recent non-trivial update. Typos do not require bumping; semantic changes do.

(Note: the spec calls these four "Versioning" fields; `published_at` + `updated_at` together function as the versioning timeline, so they are grouped here.)

### Attribution & Review (3 fields)

- **`author`** (string or array, required) — Agent id(s) of author(s), e.g. `knowledge_engineer` or `[knowledge_engineer, harness_engineer]`. Human contributors are represented as agent-id aliases registered in `agent-CEO/config/organization.yaml`.
- **`review_by`** (array, required) — Agent id(s) of reviewers who approved publication. MUST include at least one reviewer distinct from the author. For `core` docs, `review_by` MUST include at least one of `decision_advisor`, `execution_auditor`, or `harness_engineer`.
- **`audience`** (array, required) — Non-empty subset of `[team_partner, technical_builder, enterprise_decider, content_strategist, knowledge_engineer, all]`. Declaring `all` is shorthand for "every documented persona"; avoid `all` when a narrower audience is more accurate.

### Lifecycle (1 field, counted within Versioning above for the "12-field" bookkeeping)

- **`stale_after`** (ISO date, required for `type: core` and `type: reference`) — Date after which this document enters the stale-candidate list in the weekly audit. Owner is expected to review and either (a) confirm still accurate and push the date forward, (b) bump `version` to reflect an update, or (c) move status to `deprecated`.

## Examples

### Example A — `core` methodology doc

```yaml
---
id: harness-methodology
type: core
status: published
lang: en
version: 2.1
published_at: 2026-01-10
updated_at: 2026-04-18
author: harness_engineer
review_by: [decision_advisor, execution_auditor]
audience: [technical_builder, knowledge_engineer]
stale_after: 2026-10-18
---
```

### Example B — `narrative` blog post (translation)

```yaml
---
id: why-harness-engineering-matters
type: narrative
status: published
lang: zh
translation_of: why-harness-engineering-matters-en
source_commit: 6e1f5ad
version: 1.0
published_at: 2026-04-20
updated_at: 2026-04-20
author: content_strategist
review_by: [knowledge_engineer]
audience: [team_partner, enterprise_decider]
---
```

### Example C — `living` manifest (YAML body, `_meta:` form)

```yaml
_meta:
  id: public-manifest
  type: living
  status: published
  lang: en
  version: 1.0
  published_at: 2026-04-24
  updated_at: 2026-04-24
  author: knowledge_engineer
  review_by: [harness_engineer]
  audience: [all]
```

## Validation

- **`scripts/frontmatter_lint.py`** is the authoritative validator. It runs on CI for every pull request that touches `docs/public/**`.
- **Warning mode**: for the first 90 days after this spec is published (until 2026-07-23), the linter runs in warning-only mode to allow existing content to migrate.
- **Error mode**: after 2026-07-23, missing required fields become CI errors that block merge.
- **Invalid enum values** (e.g., `type: stable` instead of `type: core`) are always CI errors, even in warning mode.
- **Bad `id`** (non-kebab-case, duplicate) is always a CI error.
- **`translation_of` without `source_commit`** is always a CI error.

Downstream repositories (Forge, Academy, Blog) run a lighter version of the same linter that additionally verifies `source_commit` resolves in the `synapse-core` history.

## Amendment Process

Changes to this specification are **L2 decisions** under the Synapse decision system:

1. `knowledge_engineer` drafts the change as a pull request against this file.
2. `harness_engineer` reviews for impact on the existing linter and for entropy budget.
3. If approved, `version` bumps (minor for additive, major for breaking), `updated_at` is set to the approval date, and a `CHANGELOG.md` entry is added in the `synapse-core` root changelog under a "Content Governance" section.
4. Breaking changes trigger a grace window (minimum 30 days) during which both old and new schemas are accepted, before the linter flips to error-only on the new schema.

The spec itself carries `stale_after: 2026-10-24`; if no amendment is issued before that date, the owners review to either refresh the date or bump the version.

## Related

- `docs/public/_manifest.yaml` — declares which files carry the stability contract.
- `docs/public/glossary/glossary.yaml` — canonical bilingual terminology referenced by translations.
- `CHANGELOG.md` (repo root) — records breaking changes across all public files.
