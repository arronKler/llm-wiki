# Safe Repair Protocol

## Confirm the authorized scope first

| Target | Default audit | After explicit repair authorization | Additional requirement |
| --- | --- | --- | --- |
| Generated `_catalog/_sources/_backlinks` | Read-only | May `rebuild` | Never overwrite `_index.md` |
| Agent-owned `wiki/` | Read-only | May apply the smallest repair | Reread immediately and preserve citations |
| `outputs/` | Read-only | May repair an agent artifact | Preserve classification |
| Human-owned `data/inbox/notes` | Read-only | Still do not edit by default | Require explicit authorization for the specific content |
| `raw/sources` | Hash check | Never modify or delete | Isolate and report anomalies |
| `raw/derived`, `.wiki/state` | Read-only | May rebuild | Preserve traceability to raw evidence |
| Schema, policy, adapters, bridges | Read-only | Hand to `wiki-configure` | Separate the migration |
| `.obsidian/` | Read-only | Do not modify in maintain | Require an explicit configuration request |

"Cleanup" does not authorize deleting human content or raw evidence. "Fix all" covers only safely repairable, agent-owned issues in the current report.

## Establish a transaction

1. Fix the repair scope and finding list.
2. Record the path, current hash, and intended change for every target file.
3. Produce a minimal diff. Let subagents propose candidate diffs without writing to disk.
4. Let one primary agent reread every target immediately before writing.
5. If a hash differs or an editor or another agent changed the file, stop overwriting and merge again.
6. After applying the repair, run lint and doctor and record one maintain event.

Do not include unrelated formatting, directory reorganization, or prose rewrites in the repair transaction.

## Repair links and indexes

- Confirm the target's title, aliases, and legacy `also` before repairing a wikilink. Do not infer identity from string similarity alone.
- When renaming a page, update every inbound link, alias, curated `_index.md` entry, and anchor. Preserve the old alias when risk is high.
- Use only `rebuild` to generate `_catalog.md`, `_sources.md`, and `_backlinks.json`. Stop immediately if the generator attempts to modify `_index.md`.
- For an orphan page, decide whether it should be linked, merged, archived, or remain an entry page. Do not add meaningless links merely to eliminate all orphans.

## Merge duplicate pages

1. Verify that both pages describe the same entity or concept rather than namesakes or different time versions.
2. Select the page with stable links and more complete evidence as canonical.
3. Merge claim by claim, preserving source IDs, locators, dates, conflicts, and human wording.
4. Add the merged title to canonical `aliases`, then update inbound links.
5. Mark the old page `superseded` or retain a short redirect by default. Do not delete it directly.
6. Rebuild indexes and check backlinks.

## Repair stale or conflicting claims

- Without new evidence, only mark `needs-review`, set `review_after`, or state the gap. Do not browse to invent a replacement fact.
- Preserve both sides of a source conflict and mark the page `conflicted`. Select a current claim only when authority, effective time, or explicit user judgment resolves it.
- Update `as_of` only when evidence supports that date. Do not use the page edit date as the fact date.
- When a metric definition is incomplete, record the gap. Do not infer the definition from the number itself.

## Handle raw anomalies

When a raw hash changes:

1. Stop every operation that would write to the wiki.
2. Save a read-only diagnosis containing source ID, metadata hash, actual hash, mtime, and pages that cite it.
3. Do not overwrite current bytes with a presumed correct version or alter metadata to match the change.
4. Ask the user to restore from a trusted backup, or capture the changed content as a new source and record the relationship.
5. After recovery, lint the affected citations again.

## Preserve legacy contracts

- Do not bulk-delete `also` or `last_updated`; modern `aliases` and `updated` may coexist incrementally.
- Do not move `raw/entries` into the new layout as an ordinary repair.
- Do not overwrite or regenerate curated `_index.md`.
- Treat field normalization, directory moves, and bridge upgrades as separate configure migrations.

## Acceptance

Before completing a repair, confirm that authorized findings are closed; raw hashes are unchanged; human-owned files are unchanged; the curated index remains intact; generated state is rebuildable; citations resolve; classification did not decrease; legacy compatibility fixtures still pass; and the event accurately lists changes and validation results.
