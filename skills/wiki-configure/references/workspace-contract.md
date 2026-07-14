# Workspace Contract and Optional Obsidian Integration

Keep the legacy CLI option `--vault` as an alias for `--workspace`. Do not require `.obsidian/`. Treat Markdown and local files as the authoritative layer and Obsidian as an optional frontend.

## Use the default hierarchy

| Path | Owner | Rule |
| --- | --- | --- |
| `data/`, `inbox/`, `notes/` | Human | Read freely; write only when the user explicitly names the content. |
| `raw/sources/` | Capture tool | Create exclusively and append only; never modify an existing version. |
| `raw/derived/` | Agent/tool | Store rebuildable OCR, transcripts, and normalization that trace to raw evidence. |
| `wiki/` | Agent | Maintain durable, connected synthesis. |
| `outputs/` | Agent | Store reports, tables, slides, and other derived deliverables. |
| `.wiki/` | System | Store config, policy, events, transactions, and state. |
| `.obsidian/` | Human/app | Leave unchanged by default. |

Map actual paths in `.wiki/config.json`. Declare additional globs as human-owned or agent-owned when an existing workspace needs them. Do not move content merely to match the default hierarchy.

Treat the Markdown wiki as authoritative synthesis. Treat FTS, vectors, qmd, Dataview, Bases results, and generated catalogs as rebuildable indexes or views, never as factual sources.

## Preserve language

Treat `.wiki/config.json` `language` as the persistent-content language, not the reply language. Use either `auto` or a BCP 47-style language tag such as `en`, `zh-CN`, or `pt-BR`.

- Answer and report in the user's language.
- With an explicit language tag, write new persistent knowledge in that language.
- With `auto`, use the established primary language of non-generated wiki pages and human-owned notes. If none exists, use the user's language. System scaffolds, frontmatter property names, generated indexes, and raw quotations do not establish a workspace language.
- In a mixed-language workspace, preserve the target page's language. For a new page with no clear precedent, follow the user's language or ask only when the choice materially affects the result.
- Preserve quotations, source titles, proper names, and existing knowledge in their original language unless the user explicitly requests translation.

Preserve an existing valid setting during initialization. When the user explicitly chooses a workspace content language, persist its normalized language tag and record a configure event. Do not silently convert an existing explicit tag back to `auto`.

## Keep system-file responsibilities distinct

- Use `.wiki/config.json` for version, path mappings, search backend, and limited runtime options.
- Use `.wiki/policy.md` for authority, classification, external-tool, and writing boundaries.
- Use `wiki/_schema.md` for page types, properties, citations, and writing rules.
- Write one operation per file in `.wiki/events/`.
- Use `.wiki/transactions/` for pre-write hashes, candidate patches, and commit state.
- Use `.wiki/state/` for locks, caches, and other rebuildable state.
- Keep `wiki/_index.md` as curated, human-maintained navigation.
- Treat `wiki/_catalog.md`, `_sources.md`, and `_backlinks.json` as generated navigation.
- Create `wiki/Wiki.base` only as an optional Bases view when an Obsidian workspace is detected.

Never let the CLI overwrite `_index.md`. Do not require multiple agents to append to one shared log; generate timelines from event files instead.

## Use stable page properties

Require at least `title`, `type`, `created`, `updated`, and `sources` on new knowledge pages. Use these stable common fields:

```yaml
title: Page title
aliases: [Alternate name]
type: concept
domains: [work]
status: current
classification: internal
created: YYYY-MM-DD
updated: YYYY-MM-DD
as_of: YYYY-MM-DD
review_after: YYYY-MM-DD
confidence: medium
sources: [src-web-0123456789ab]
```

Use these recommended status values: `draft`, `current`, `needs-review`, `conflicted`, `superseded`, and `archived`.

Use these recommended classification values: `public`, `personal`, `internal`, `confidential`, and `restricted`.

Use these recommended confidence values: `high`, `medium`, `low`, and `unknown`.

Add domain-specific fields only after defining their semantics in `_schema.md`. Keep YAML readable by generic Markdown tools and compatible with Obsidian Properties and Bases when that frontend is enabled.

## Reuse page types

- Use `entity` for a person, team, organization, customer, product, system, dataset, or place.
- Use `concept` for a method, policy, mental model, or reusable idea.
- Use `project` for goals, scope, owners, status, milestones, and outcomes.
- Use `process` for a business workflow, responsibility boundary, or runbook.
- Use `decision` for context, options, evidence, choice, rationale, and consequences.
- Use `metric` for definition, lineage, time semantics, limitations, and observations.
- Use `comparison` for evaluation along explicit dimensions.
- Use `synthesis` for a cross-source answer or evolving thesis.
- Use `timeline` when sequence is itself important.

Let folders emerge from the data instead of prebuilding a complex taxonomy. Use `domains` to classify pages across folders.

## Enable Obsidian only as an optional integration

- Use `[[wikilinks]]` for durable relationships and standard `aliases` for alternate-title resolution.
- Use heading or block anchors such as `^claim-...` for important claims when useful.
- Prefer lowercase kebab-case filenames; allow multilingual titles and aliases.
- When an Obsidian workspace is detected, use Bases as the default optional visualization layer and Dataview only as an enhancement. Never require either for correctness.
- Keep original attachments in raw evidence and reference them from derived Markdown. Do not rely on an unstable remote URL as the only evidence.
- Never modify `.obsidian/` attachment, plugin, hotkey, or workspace settings automatically. Offer a recommendation and change them only when explicitly requested.

## Maintain content quality and evidence

Trace material factual, numeric, personal, and decision claims to a raw source ID and locator. Use wiki links for navigation and citations for proof. Preserve conflicting claims and their time context; resolve them only through source authority, effective time, or a user decision.

Keep human statements distinct from agent synthesis. Synthesize around topics instead of writing ingestion logs. Prefer `superseded` or `archived` status over hard deletion.

## Enforce concurrency and security

Use one writer. Let subagents perform read-only analysis and propose patches. Check hashes immediately before writing and stop on conflicts. Treat labels as metadata, not ACLs. Isolate personal and company trust zones with separate workspaces or repositories when technical separation is required.
