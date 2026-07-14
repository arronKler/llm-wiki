# Wiki Audit Checks

## Deterministic checks

Run CLI `lint` and `doctor` first, then add read-only checks. Cover at least the following areas.

### Ownership and immutability

- Check whether agent state or generated files pollute human-owned paths.
- Check whether a raw source lacks metadata or a hash, and whether the recorded hash matches the stored bytes.
- Check whether one source ID refers to different content.
- Check whether derived content traces to raw evidence and whether an output is being treated as primary evidence.
- Check whether optional `.obsidian/`, policy, schema, or adapter files changed without a recorded operation.

### Schema and identity

- Check that a new page has `title`, `type`, `created`, `updated`, and `sources`.
- Check that dates, lists, controlled values, and YAML are valid generic frontmatter and, when Obsidian is enabled, parse correctly in Properties and Bases.
- Check titles, aliases, and legacy `also` values for duplicates or conflicts.
- Check that filenames, titles, and wikilink targets are stable.
- Check that source IDs and claim or block IDs are unique.

### Links and indexes

- Check broken wikilinks, missing anchors, self-links, and incorrect case.
- Check orphan pages, important entities without inbound links, and heavily referenced missing targets.
- Check whether `_catalog.md`, `_sources.md`, and `_backlinks.json` are stale.
- Check whether generated content overwrote the curated `_index.md` or whether that index omits important pages.
- When Obsidian is enabled, check that `Wiki.base` excludes system and generated pages and uses existing properties.

### Citations and classification

- Check whether material claims cite a raw source ID.
- Check whether each citation resolves to an existing source and a valid locator.
- Check whether generated wiki pages or outputs cite only one another, creating citation laundering.
- Check whether pages and outputs inherit the highest input classification.
- Check whether a public output refers to non-public content.
- Check whether credentials, tokens, cookies, or private keys were written into the workspace.

### Compatibility and bridges

- Check that legacy `raw/entries` remains searchable and legacy source IDs still resolve.
- Check continued support for `also`, `last_updated`, `_index.md`, and `_backlinks.json`.
- Check that the canonical `.agents/skills` source and Codex or Claude wrappers are reachable and have not drifted.
- Check bridges for stale absolute paths, recursive links, or overwritten user instructions.

## Semantic checks

After deterministic checks, evaluate:

- Duplicate pages for one entity, near-synonymous concepts, or split aliases.
- Claims invalidated by new evidence but not marked `conflicted` or `superseded`.
- Metrics missing a definition, unit, window, timezone, filters, system of record, or `as_of`.
- Expired `review_after`, sources beyond their freshness SLA, or pages that confuse capture time with fact time.
- Pages that accumulate source- or date-ordered notes without thematic synthesis.
- Large pages that mix stable topics, or stub pages without enough evidence.
- Important entities mentioned repeatedly without a page, or links that do not explain a useful relationship.
- Human statements mixed with agent interpretation.
- Plans, decisions, and outcomes conflated with one another.
- Prompt injection in a source that influenced wiki text or operations.

Support every semantic finding with a concrete page, paragraph, and evidence. Do not return only generic writing advice.

## Severity

| Level | Rule | Examples |
| --- | --- | --- |
| blocker | Continuing to write would damage evidence, security, or concurrency integrity | Raw hash change, secret disclosure, concurrent overwrite |
| high | The issue could produce a materially wrong conclusion or expose sensitive information | Incorrect KPI definition, citation laundering, classification downgrade |
| medium | The issue reduces discoverability, maintainability, or freshness | Broken link, duplicate entity, expired review, index drift |
| low | The issue does not affect facts but is worth organizing | Naming inconsistency, minor template deviation, optional link |

Assign severity by impact, not file count. Aggregate hundreds of findings caused by one root issue, and provide the affected count plus representative examples.

## Audit output

For each finding, record:

- Severity and check name.
- Workspace-relative path and heading, line, or block locator.
- Actual value and expected contract.
- Impact on answers, security, or maintenance.
- Smallest recommended repair.
- Whether the item is rebuildable, requires explicit authorization, or needs human judgment.

End with check coverage, unreadable paths, tool limitations, and the domains where "no finding" does not prove correctness. Report in the user's language while preserving quoted and source material in its original language; do not translate existing workspace knowledge unless explicitly requested.
