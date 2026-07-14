# Answer and Citation Contract

## Lead with the answer

Use the smallest sufficient structure for the question's complexity:

```markdown
Conclusion: Answer the user's question directly.

Evidence: List the two to five strongest points, with nearby wiki-page and raw-source locators.

Conflicts and limits: State definition differences, time boundaries, freshness, counterevidence, and missing evidence.

As of: YYYY-MM-DD, or "The current wiki does not record a reliable as_of date."
```

Do not force this template onto a simple fact. For a complex comparison, decision briefing, or analysis, separate fact, inference, and recommendation.

## Provide two-layer citations nearby

Provide both:

1. `[[Page title#Relevant heading]]` or an explicit workspace-relative path so the user can navigate in any Markdown frontend; wikilinks become directly navigable when Obsidian is enabled.
2. A raw `source_id` plus locator that supports the material claim.

Example:

```markdown
The recorded Q2 payment conversion rate was 18.4%, excluding refunded orders.
([[Payment conversion rate#2026 Q2]]; `src-report-a1b2` p.12; as_of 2026-06-30)
```

If only wiki synthesis is available and no raw citation resolves, state "secondary synthesis; raw evidence unresolved" and lower confidence. Do not let multiple agent-generated pages cite one another into a false evidence chain.

## Label evidence status

Use precise language:

- "The source explicitly records ..." for direct evidence.
- "Multiple independent sources support ..." for corroboration.
- "This suggests ..." or "It is reasonable to infer ..." for agent interpretation.
- "The wiki contains a conflict ..." when preserving competing claims.
- "No evidence was found ..." for an evidence gap.
- "As of YYYY-MM-DD ..." for a time boundary.

Do not turn absence of evidence into evidence of absence, correlation into causation, or a plan into a completed result.

## Compare consistently and report business data completely

Fix common comparison dimensions first: definition, time, scope, source, unit, cost, risk, and unknowns. Do not give a falsely precise ranking when the evidence is not comparable.

For KPI or operating data, provide:

- Metric definition and system of record.
- Value, unit, window, filters, timezone, and `as_of`.
- Query/source ID and locator.
- Freshness, confidence, anomalies, and conflicts.

Separate facts recorded in the wiki, inferences from those facts, and recommended actions.

## Preserve language and source fidelity

Answer in the user's language. Preserve quotations, source titles, proper names, and existing workspace knowledge in their original language unless the user explicitly asks for translation. Quote only the minimum source text needed to support the conclusion, and retain the speaker and context for personal, meeting, or message excerpts. Do not bypass classification through a quotation.

## Handle external refreshes

When the user asks for the latest or current state and the wiki is stale:

1. State the wiki's `as_of` first.
2. Use only external tools permitted for the active agent and public or approved data.
3. Do not leak non-public content in an external query.
4. Cite temporary external results separately from workspace evidence.
5. Do not write temporary results back to the wiki unless the user explicitly requests ingest.

## Produce a persistent output only when requested

Write under `outputs/` only when the user explicitly requests a file. Record title, type, classification, created/updated, `as_of`, and sources, and mark the file as derived. Cite raw source IDs, and do not make the output the sole evidence for a later fact.

When the user wants new synthesis to become long-term knowledge, hand it to the ingest workflow to recheck page matching, conflicts, and raw citations.
