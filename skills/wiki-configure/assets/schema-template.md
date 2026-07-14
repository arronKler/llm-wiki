---
title: Wiki Schema
type: system
schema_version: 1
created: {{date}}
updated: {{date}}
---

# Wiki schema

This file is the durable contract for the compiled wiki. Change it deliberately through `wiki-configure`, then record the change as an event.

## Layers and ownership

| Layer | Default owner | Rule |
| --- | --- | --- |
| `data/`, `inbox/`, `notes/` | Human | Read freely; edit only on an explicit request. |
| `raw/sources/` | Capture tool | Append only. Originals live under each envelope's `original/`; changed content or provenance becomes a new source/capture variant. |
| `raw/derived/` | Agent/tool | OCR, transcripts, and normalized text; always trace back to raw. |
| `wiki/` | Agent | Maintain coherent, interlinked synthesis with source IDs. |
| `outputs/` | Agent | Reports and other deliverables; never primary evidence. |
| `.wiki/` | System | Configuration, events, transactions, and rebuildable state. |
| `.obsidian/` | Human/app | Optional Obsidian settings; do not change unless explicitly requested. |

## Page properties

Use portable YAML frontmatter properties:

```yaml
---
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
---
```

Required for new knowledge pages: `title`, `type`, `created`, `updated`, and `sources`. Use standard `aliases`, not custom fields alone, so alternate-title links remain portable across tools. Preserve the legacy `also` field when encountered until an explicit migration.

Recommended controlled values:

- `status`: `draft`, `current`, `needs-review`, `conflicted`, `superseded`, `archived`
- `classification`: `public`, `personal`, `internal`, `confidential`, `restricted`
- `confidence`: `high`, `medium`, `low`, `unknown`

Add domain-specific properties only after documenting their meaning here. For metrics, record definition, unit, window, timezone, filters, system of record, and `as_of`. For decisions, distinguish the decision, owner, rationale, date, and later outcome.

## Page types

Let folders emerge from content. Prefer these stable types when applicable:

- `entity`: person, team, organization, customer, product, system, dataset, or place
- `concept`: a reusable idea, method, policy, or mental model
- `project`: goal, scope, ownership, state, milestones, decisions, and outcomes
- `process`: an operational flow, responsibility boundary, or runbook
- `decision`: context, options, evidence, choice, rationale, and consequences
- `metric`: exact definition, lineage, time semantics, caveats, and observed values
- `comparison`: evidence-backed comparison along explicit dimensions
- `synthesis`: a substantial cross-source answer or evolving thesis
- `timeline`: dated events whose sequence matters

Create a page when the subject is central to one source, appears in multiple sources, or is a durable link target. Do not create empty stubs for passing mentions. Split pages that mix distinct subjects or become difficult to navigate.

## Evidence and citations

Every material factual, numeric, personal, or decision claim must trace to a raw source ID. Cite at claim or paragraph level when precision matters:

```markdown
Payment conversion was 18.4% as of 2026-06-30.[^src-report-a1b2-p12] ^claim-7f3a

[^src-report-a1b2-p12]: `src-report-a1b2`, p. 12, captured 2026-07-14.
```

Use a stable locator when available: page, line, heading, block, timestamp, message ID, row key, query ID, or commit SHA. Derived pages must cite raw evidence, not only another generated summary. Keep `sources` in frontmatter as the complete source-ID set used by the page.

## Integration rules

1. Read `_index.md` or `_catalog.md`, then search before opening page bodies.
2. Read every page immediately before editing it.
3. Integrate new evidence into the right section; do not append a chronological dump.
4. Update `updated`, sources, aliases, related links, conflicts, and `as_of` where relevant.
5. Preserve attributed human statements as quotations or clearly labeled observations. Keep agent interpretation distinguishable.
6. Keep both sides of a contradiction with dates and sources. Resolve only from source authority, recency, or explicit human judgment.
7. Prefer marking `superseded` or archiving over hard deletion.
8. Update the curated `_index.md` after page edits; rebuild generated catalog/backlinks only at the end.

## Markdown and link conventions

- Use `[[wikilinks]]` for durable internal relationships and standard `aliases` for alternate titles.
- Use heading or block anchors for stable claim locations when useful.
- Keep filenames lowercase kebab-case where practical; titles and aliases may be Chinese or multilingual.
- Keep YAML frontmatter portable. When Obsidian is used, keep it compatible with Properties and Bases; Dataview may be added as an optional view layer but is never required for correctness.
- Keep generated files prefixed with `_` and exclude them from normal knowledge-page counts.

## Writing standard

Lead with the answer or definition. Write neutral, concrete prose organized by theme. Synthesize across sources instead of listing source summaries. Use dates, units, owners, and attributed statements in place of vague adjectives. State evidence gaps and uncertainty plainly. A page should explain why its subject matters within this wiki, not reproduce a generic encyclopedia entry.

## Language

- Answer and report in the user's language.
- For new persistent knowledge, honor an explicit workspace language. When the workspace language is `auto`, use the established primary language of non-generated knowledge; if none exists, use the user's language.
- Do not infer the primary language from system scaffolds, property names, generated indexes, or raw quotations. In a mixed-language workspace, preserve the target page's language and ask only when the choice would materially affect a new page.
- Keep quotations, source titles, proper names, and existing knowledge in their original language unless translation is requested.
- Do not translate or rewrite existing knowledge solely for language consistency without explicit authorization.

## Schema evolution

Change the smallest necessary rule. Preserve backward compatibility or document a migration. Run a read-only lint before and after a migration. Never mix a schema migration with unrelated content edits, and never silently recategorize or delete human-authored material.
