# Wiki Integration Contract

## Match Before Creating

Check in this order:

1. Human-maintained `wiki/_index.md`.
2. Generated `_catalog.md`, `_sources.md`, and `_backlinks.json`.
3. Title, `aliases`, legacy `also`, properties, and full-text search.
4. One or two hops of wikilinks and backlinks from relevant pages.

Merge aliases for the same entity into an existing page. Add an alias only when it appears in evidence, is already established in the workspace, or is explicitly requested. Never invent translated or transliterated names. Create a page only when the topic is a durable link target, recurs across sources, is central to one source, or supports at least one complete evidence-backed paragraph. Do not create an empty stub for a passing mention.

## Use Standard Markdown Properties

Give every new knowledge page at least `title`, `type`, `created`, `updated`, and `sources`. Use the rest of the schema as needed:

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

Use controlled values defined by the schema. Treat YAML frontmatter as the portable contract and keep it compatible with Obsidian Properties. Prefer stable lowercase kebab-case filenames. Put Chinese or other multilingual names in `title` and `aliases`. Resolve `[[wikilinks]]` through titles and aliases.

When updating a legacy page:

- Preserve `also` and use it for alias matching. Do not delete or bulk-rewrite it without an explicit migration.
- Preserve `last_updated`. When editing the page, add or update modern `updated` without breaking legacy consumers.
- Preserve legacy source IDs such as `text-b185a6a06928`; do not replace them merely to standardize the format.
- Preserve the organization, summaries, and annotations in the human-maintained `_index.md`. Update only affected entries.

## Cite Raw Evidence at Claim Level

Trace facts, numbers, decisions, personal statements, and time-sensitive conclusions directly to a raw source ID:

```markdown
Payment conversion was 18.4% on 2026-06-30.[^src-report-a1b2-p12] ^claim-7f3a

[^src-report-a1b2-p12]: `src-report-a1b2`, page 12, snapshot captured on 2026-07-14.
```

Use a paragraph-level citation when one source supports the whole paragraph. Cite independent claims separately when they share a paragraph. Include every source ID used in the body in frontmatter `sources`.

Do not cite only another agent-generated wiki page or output. Use wiki links for navigation and raw citations for evidence. When citing derived OCR or a transcript, still point to the raw source and add the derived locator.

Quote source text briefly only to preserve exact wording or a person's voice. Identify the speaker and context; never present an agent paraphrase as the user's exact words.

## Synthesize Instead of Appending

- Reread the full page immediately before editing and place new evidence in the most relevant thematic section.
- Lead with the definition or conclusion, then cover change over time, relationships, conflicts, and open questions.
- Replace vague phrases such as "recently," "many," or "people think" with concrete dates, units, owners, scope, and attribution.
- Update wikilinks on related pages. Create only relationships that add explanatory value; do not accumulate a generic related-links list.
- Consider splitting a page when a third independent subtopic appears. Enrich a thin page before splitting it further.
- Keep human statements, source statements, and agent interpretations distinguishable.
- Answer in the user's language. Preserve an existing target page's language. For a new page, honor an explicit workspace language; with `auto`, use the established language of non-generated knowledge and otherwise the user's language. Do not treat system scaffolds, property names, or generated indexes as language evidence. Never translate existing knowledge without an explicit request.

## Preserve Conflicts and Time

When new evidence disagrees with an existing claim:

1. Preserve both statements, their source IDs, locators, and published, captured, or as-of times.
2. Check whether the difference comes from definitions, time windows, scope, or granularity.
3. Mark the page `conflicted` or add a prominent conflict section.
4. Select the current conclusion only from policy-defined authority, an explicit effective time, or a user decision.
5. Mark displaced content as superseded instead of deleting historical evidence.

For a metric, record its definition, unit, window, timezone, filters, system of record, and `as_of`. For a decision, distinguish context, options, evidence, choice, owner, date, rationale, and later outcome.

## Maintain Indexes and Optional Frontend Views

- Treat `_index.md` as human-editable content navigation. Update it incrementally; never let `rebuild` overwrite it.
- Treat `_catalog.md`, `_sources.md`, and `_backlinks.json` as disposable, rebuildable state.
- When an Obsidian workspace is detected, use standard YAML fields for optional `Wiki.base` and Properties. Treat Bases and Dataview as views, never as correctness dependencies.
- Give important claims stable internal links with heading or block anchors.

## Pre-Commit Checks

- Verify that every new page has a source and is not a stub.
- Verify that every material claim traces to raw evidence.
- Verify that `sources`, aliases, status, dates, and classification agree.
- Keep conflicts and uncertainty visible.
- Preserve the human-maintained `_index.md`.
- Generate derived files only through `rebuild`.
- Keep legacy `also`, `last_updated`, and source IDs readable.
- Ensure `lint` reports no errors introduced by this ingest.
