---
name: wiki-maintain
description: "Audit and safely maintain a managed local Markdown wiki for integrity, links, orphan pages, duplicate entities, citations, raw hashes, index drift, stale or conflicting claims, schema, classification, and agent bridges. Use when the user asks to audit, maintain, repair, rebuild, reindex, deduplicate, run lint or doctor, check integrity, or review freshness. Chinese triggers include: 检查、体检、清理、去重、修复、重建索引、刷新反链、审查新鲜度. Keep audits read-only by default; write only after an explicit repair or fix request."
---

# Wiki Maintain

## Goal

Detect wiki drift with reproducible checks, then repair it with the smallest auditable changes. Protect raw evidence, human notes, and the curated index from destructive cleanup.

## Locate the workspace and tool

1. Starting from a user-provided path, search upward for `.wiki/config.json`. If no path is provided, search upward from the current directory.
2. Include a workspace containing legacy `raw/entries/`, `wiki/_index.md`, or `wiki/_backlinks.json` in the audit without requiring migration first.
3. Resolve `../wiki-configure/scripts/wiki.py` relative to this `SKILL.md`. Use `python3 <wiki.py> --workspace <workspace-root> ...`; legacy `--vault` remains an equivalent compatibility flag. Do not depend on the current working directory.
   If the CLI is missing, remain read-only and ask the user to reinstall the complete suite with `npx skills add arronKler/llm-wiki --skill '*' -a universal -a claude-code -y`. Do not improvise a separate repair tool.
4. Read `.wiki/config.json`, `.wiki/policy.md`, `wiki/_schema.md`, and recent relevant events. Report missing system files as findings; do not create them during an audit.

## Read references as needed

- Before any audit, lint, doctor, cleanup, breakdown, freshness review, or integrity check, read [references/audit-checks.md](references/audit-checks.md). Also read it before deciding severity or coverage.
- Before any rebuild, fix, repair, deduplication, rename, archive, or semantic rewrite, read [references/repair-protocol.md](references/repair-protocol.md). Always read its upgrade boundaries for schema, policy, adapter, bridge, or legacy-layout work.

## Audit workflow by default

1. Define the scope: the full workspace, one domain, one ingest, one problem class, or one time window. Cover system contracts and the wiki by default without scanning unrelated large files.
2. Stay strictly read-only: do not run `rebuild`, write an event, auto-format files, or revise prose.
3. Run:

   ```text
   python3 <wiki.py> --workspace <workspace-root> status
   python3 <wiki.py> --workspace <workspace-root> lint
   python3 <wiki.py> --workspace <workspace-root> doctor
   ```

4. Check raw content hashes, ownership violations, schema, source IDs, citation locators, wikilinks, aliases, duplicate titles, orphan pages, generated-index drift, and classification inheritance.
5. Then perform a semantic audit for duplicate concepts, claims invalidated by newer evidence but not marked, stale metrics, high-value entities without pages, incorrect attribution, citation laundering, and undisclosed conflicts.
6. If subagents inspect pages in parallel, keep them read-only and ask them to return findings and candidate patches. Let one primary agent deduplicate, decide, and write; do not let subagents modify shared files.
7. Report findings in blocker, high, medium, low order. For each finding, provide path, locator, evidence, impact, recommended action, and whether user confirmation is required.
8. Report in the user's language while preserving quotations and source text in their original language. Do not translate existing workspace knowledge unless the user explicitly requests translation.

## Repair workflow only with explicit authorization

1. Treat an explicit fix, repair, cleanup, or rebuild request as write authorization only for the named scope. Do not expand one repair into a repository-wide refactor.
2. Before editing, record the target file hashes and create a minimal transaction or diff. Reread every target page immediately before editing. If a concurrent change appears, stop overwriting and merge again.
3. Respect layer permissions:
   - Rebuild generated `_catalog.md`, `_sources.md`, and `_backlinks.json` when authorized.
   - Repair agent-owned `wiki/` only within the authorized scope.
   - Do not modify human-owned `data/`, `inbox/`, or `notes/`.
   - Never modify or delete an existing `raw/sources/` entry. Isolate and report hash anomalies.
   - Never overwrite curated `wiki/_index.md` with generated content.
4. Prefer adding links and citations, consolidating duplicate aliases, and marking `conflicted`, `superseded`, or `archived`. Do not hard-delete pages by default.
5. Run `rebuild` only when the user explicitly requests it. Then run `lint` and `doctor` and confirm that the repair introduced no new broken links, schema problems, or classification errors.
   If the CLI refuses to overwrite an unmanaged or modified generated file, show the conflict first. Run `rebuild --force` only after the user explicitly accepts takeover. The command backs up conflicting files under `.wiki/transactions/`; report each backup path when complete.
6. Record one event file with `event maintain --message <summary> --data <json>`.
7. Return the actual changes, preserved content, validation results, remaining risks, and conflicts that still require a decision.

## Upgrade boundaries

- Hand schema, policy, adapter, ownership, freshness-rule, or agent-discovery bridge changes to `wiki-configure`.
- Hand new external evidence to `wiki-ingest`. Do not silently browse or fetch material during maintenance to fill a knowledge gap.
- Hand read-only knowledge questions to `wiki-query`.
- Stop repair immediately on a raw hash anomaly, concurrent write conflict, suspected sensitive-data disclosure, or uncertain ownership. Preserve evidence and report the condition.
