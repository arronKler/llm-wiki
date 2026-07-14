---
name: wiki-query
description: "Retrieve, compare, trace relationships, and synthesize answers from a managed local Markdown wiki with claim-level provenance, freshness, classification, conflicts, and evidence gaps. Use when the user asks what the wiki knows, or asks to query, search, explain, compare, synthesize, investigate, prepare a briefing, or show evidence. Chinese triggers include: 查 wiki、wiki 里有什么、某人或项目发生了什么、为何做某决定、指标如何定义、比较方案、准备简报. Stay strictly read-only by default; do not silently fetch external material or persist answers."
---

# Wiki Query

## Goal

Answer quickly and traceably from the compiled wiki. Reuse accumulated synthesis first, and return to raw evidence only when verification requires it.

## Locate the workspace and tool

1. Starting from a user-provided path, search upward for `.wiki/config.json`. If no path is provided, search upward from the current directory.
2. If only legacy `wiki/_index.md`, `wiki/_backlinks.json`, or `raw/entries/` exists, query it read-only in legacy mode. Do not require migration first.
3. Resolve `../wiki-configure/scripts/wiki.py` relative to this `SKILL.md`, then use `python3 <wiki.py> --workspace <workspace-root> ...`. Legacy `--vault` remains an equivalent compatibility flag. Do not depend on the current working directory.
   If the CLI is missing, stop and ask the user to reinstall the complete suite with `npx skills add arronKler/llm-wiki --skill '*' -a universal -a claude-code -y`. Do not replace managed retrieval with an unsourced ad hoc search.
4. Read `.wiki/config.json`, `.wiki/policy.md`, and `wiki/_schema.md`. If any are missing, apply the most conservative read-only and classification policy.

## Read references as needed

- Before selecting pages, widening a search, following graph relationships, or reading raw evidence, read [references/retrieval.md](references/retrieval.md). Always read it for a large workspace, an ambiguous entity, aliases, a legacy index, or a temporal question.
- Before producing a final answer, comparison, briefing, citation, or file artifact, read [references/answer-contract.md](references/answer-contract.md). Always read it for conflicts, stale metrics, inference, sensitive information, or an explicit evidence request.

## Workflow

### 1. Frame the question

1. Extract the topic, time range, business definition, requested output, and meaning of "current" or "historical." Ask only when different interpretations would materially change the answer.
2. Keep the query read-only: do not edit pages, rebuild indexes, write events, or save the answer.
3. Do not send query terms, private excerpts, company data, or wiki summaries to public search or unapproved external services.
4. Answer in the user's language while preserving quotations and source text in their original language. Do not translate existing workspace knowledge unless the user explicitly requests translation.

### 2. Navigate before reading bodies

1. Read `wiki/_index.md` first. Then read any existing `_catalog.md`, `_sources.md`, and `_backlinks.json`.
2. Run:

   ```text
   python3 <wiki.py> --workspace <workspace-root> search <query> --limit 15
   ```

3. Search title, `aliases`, legacy `also`, Properties, headings, and wikilinks together. Add `--sources` when source cards are relevant.
4. Select roughly 5–15 highly relevant pages that cover distinct evidence chains. Follow one or two wikilink and backlink hops. Avoid reading the entire workspace without a clear reason.
5. When exact wording, a disputed claim, a number, or the evidence itself needs verification, follow the source ID and locator to the smallest necessary raw excerpt. Do not treat raw content as the default corpus for resynthesizing everything.

### 3. Evaluate evidence

1. Verify that each key claim traces to a raw source ID rather than only another agent-written summary.
2. Compare `as_of`, `review_after`, source publication time, capture time, authority, confidence, and classification.
3. Preserve differences in definitions, conflicting sources, and unresolved questions. Do not let "newer" automatically replace "more authoritative," and do not present correlation as causation.
4. For a metric, verify its definition, unit, window, timezone, filters, and system of record. Lower the conclusion's strength explicitly when any element is missing.
5. If the user asks for current information and the wiki is beyond its freshness SLA, state the cutoff first. Use permitted external tools only when the user requests a refresh or a higher-level agent rule requires one. Do not silently write temporary results back to the workspace.

### 4. Form the answer

1. Lead with the conclusion, then present supporting evidence, conflicts, inferences, and gaps.
2. Cite each material claim nearby with `[[page#heading]]` and a raw source ID/locator. Use claim-level citations for numbers, decisions, personal statements, and time-sensitive conclusions.
3. State `as_of` or the applicable cutoff, and label agent inference explicitly.
4. Keep the output classification at least as restrictive as every input. Do not expose personal, internal, confidential, or restricted evidence in a publicly shareable output.
5. If the answer is unavailable, state what was searched, which evidence is missing, and the smallest next step. Do not guess.

## Persistence boundaries

- When the user only asks a question, answer only in the conversation.
- When the user explicitly requests a report, table, Marp deck, Canvas, or another file, write it under `outputs/` and record derived status, classification, `as_of`, and sources. Do not treat the output as primary evidence.
- When the user explicitly asks to write the conclusion back to the wiki, hand it to `wiki-ingest` as material to integrate and bind it again to raw source IDs. Do not let query modify the wiki directly.
- Hand new webpages, files, meetings, or database results to `wiki-ingest`. Hand index or page repairs to `wiki-maintain`.
