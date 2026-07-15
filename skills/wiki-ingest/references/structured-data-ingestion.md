# Structured Data Ingestion

Use this reference when a source is a spreadsheet, delimited table, database query, API response, dashboard export, or analytical dataset. Apply [source-handling.md](source-handling.md) during acquisition, then read [integration-contract.md](integration-contract.md) before creating or editing wiki pages. Specialize the analytical evidence here without repeating generic capture, classification, or synthesis rules.

## Contents

- [Define the analytical scope](#define-the-analytical-scope)
- [Identify the system of record](#identify-the-system-of-record)
- [Acquire data without source changes](#acquire-data-without-source-changes)
- [Freeze query identity](#freeze-query-identity)
- [Establish schema and completeness](#establish-schema-and-completeness)
- [Inspect spreadsheets](#inspect-spreadsheets)
- [Preserve formulas and computed fields](#preserve-formulas-and-computed-fields)
- [Acquire APIs with pagination](#acquire-apis-with-pagination)
- [Resolve dashboard filters](#resolve-dashboard-filters)
- [Map evidence into capture](#map-evidence-into-capture)
- [Assess data quality](#assess-data-quality)
- [Define metric semantics](#define-metric-semantics)
- [Protect privacy](#protect-privacy)
- [Create reproducible citations](#create-reproducible-citations)
- [Process updates](#process-updates)
- [Stop or accept](#stop-or-accept)

## Define the analytical scope

Start from the decision or question the data must support.

- State the requested measures, dimensions, entities, grain, population, and comparison groups.
- Fix the business time window, event-time field, timezone, and data-availability cutoff.
- Distinguish a one-time snapshot from an incremental series, recurring refresh, or historical backfill, and state whether exact reconstruction, sampling, validation, or directional analysis is required.
- Bound rows, columns, sheets, endpoints, partitions, and dashboard tiles before retrieving bodies; record exclusions and explain how they limit the conclusions.
- Do not broaden a focused question into a warehouse-wide, workbook-wide, or account-wide export.

## Identify the system of record

Assign authority per field and claim instead of treating every analytical surface as equivalent.

- Identify the operational source, warehouse or lake, semantic layer, spreadsheet, API, and dashboard involved.
- Name the authoritative system for identifiers, dimensions, metric definitions, corrections, and effective dates.
- Distinguish source-of-record data from replicated, cached, sampled, manually entered, or presentation-only data.
- Record pipeline or model names when they affect lineage, latency, or transformations, and preserve disagreements between analytical surfaces with their timestamps.
- Treat dashboard labels and workbook titles as navigation unless their definitions are independently evidenced.
- Do not infer production truth from a test dataset, preview, cached extract, or stale workbook.

## Acquire data without source changes

Use an approved read-only connector, export, query surface, or local file.

- Verify that database statements are read-only before execution. Do not issue DDL, DML, transaction-control statements, stored procedures, user-defined functions with side effects, materialization, refresh, repair, optimization, or administrative commands.
- Use API operations with verified non-mutating semantics. Do not call GraphQL mutations, create/update/delete endpoints, webhook tests, export jobs that alter state, or endpoints whose side effects are uncertain.
- Do not save dashboard filters, trigger dataset refreshes, acknowledge alerts, edit reports, or change shared view state during acquisition.
- Do not run spreadsheet macros, external-data refreshes, custom functions, or recalculation as an ingestion side effect.
- Use temporary local storage for authorized results, then let the shared CLI perform the first persistent write.
- Stop and request a safer export or explicit isolated workflow when read-only behavior cannot be established.

## Freeze query identity

Make every database or analytical query reproducible without preserving credentials.

- Preserve the exact SQL, query language, API query document, or semantic-model request.
- Record engine, account or project, catalog, database, schema, dataset, model version, parameters, partition selection, timezone, role context, and row-limit behavior.
- Record the execution or job ID, timing, snapshot or transaction boundary, and result status; resolve relative dates and dynamic functions into explicit values or record their evaluation time.
- Preserve result row count, column order, output format, and content hash.
- Remove passwords, tokens, cookies, signed URLs, and session identifiers from query evidence.
- Capture the query definition separately from its result when either can change independently.

## Establish schema and completeness

Verify structure before interpreting values.

- Record every selected column's name, type, nullability, unit, encoding, and controlled-value meaning.
- Identify the row grain, primary or candidate keys, foreign keys, partition keys, and expected uniqueness.
- Record source and output row counts when access permits; check missing partitions, truncation, row caps, sampling, pagination, inaccessible sheets, and permission gaps.
- Distinguish null, blank, zero, “not applicable,” redacted, and unknown values.
- Record date parsing, timezone conversion, locale, decimal separator, character encoding, and rounding behavior.
- Detect duplicate keys, unexpected schema drift, mixed types, and columns whose meaning changed over time.
- Do not call a sample, top-N result, preview, or partial page a complete dataset.

## Inspect spreadsheets

Preserve the original workbook before extracting tables.

- Record workbook identity, file version, sheet names, visible and hidden sheets, and used ranges.
- Inspect hidden rows and columns, filters, merged cells, named or protected ranges, and frozen headers; record the date system, locale, units, display formats, and errors.
- Distinguish source tables, lookup sheets, presentation sheets, pivots, charts, and manually maintained assumptions.
- Preserve stable row keys and column headers; do not rely on row numbers after sorting or filtering.
- Export a normalized table only as derived evidence and retain its mapping to workbook, sheet, range, and cells.
- Do not reduce a formula-bearing workbook to CSV when formulas, formatting, hidden state, or multiple sheets matter.
- Do not run macros, refresh connections, follow external links, or recalculate the workbook during ingestion.

## Preserve formulas and computed fields

Treat formulas as definitions and cached values as observations of a calculation state.

- Record formula text, cached or displayed value, cell or field locator, and last-calculated state when available.
- Distinguish constants, formulas, query outputs, pivot calculations, semantic measures, and manual overrides.
- Record dependencies on named ranges, sheets, external workbooks, custom functions, or remote models; flag volatility, circular references, errors, stale caches, and missing dependencies.
- Preserve rounding, null handling, branching, scaling, and unit conversions that change interpretation.
- Do not claim to have verified a formula merely because its cached result is present.
- Do not recalculate formulas or execute custom code unless separately authorized and captured as new evidence.

## Acquire APIs with pagination

Capture the request contract and prove where retrieval stopped.

- Record method, canonical endpoint, API version, content negotiation, safe parameters, request body shape, and any GraphQL document and variables.
- Remove authorization headers, cookies, signatures, and secret-bearing parameters before capture.
- Record response status, response schema, server time, request or trace ID, and documented rate-limit state.
- Follow cursor, token, offset, link-header, or page-number pagination until the declared boundary is reached.
- Record the initial cursor, cursor chain or page range, page count, item count, termination condition, and retries.
- Check ordering stability, repeated or missing objects across pages, concurrent updates, and per-page errors.
- Preserve partial responses and error objects; never silently treat them as a complete successful result.
- Stop rather than guess when a next-page token, rate limit, permission boundary, or consistency rule is unclear.

## Resolve dashboard filters

Treat a dashboard as a parameterized view, not a self-explanatory source.

- Record dashboard, workbook, report, tile, or chart identity and version when available.
- Record global, page, tile, hidden, inherited, and default filters with their resolved values.
- Record date range, timezone, comparison period, cohort, segment, grouping, sort, top-N, and row-limit settings.
- Identify the backing dataset, semantic measure, refresh time, cache state, and displayed-versus-exported precision.
- Prefer an underlying-data export or query result over a screenshot when claims depend on exact values.
- Preserve a screenshot only as presentation evidence and pair it with filter state and underlying evidence.
- Do not combine values from differently filtered tiles without making the mismatch explicit.
- Do not infer unfiltered totals from a chart whose filters or suppression rules are unavailable.

## Map evidence into capture

Use the generic CLI and map analytical identity explicitly.

- Capture a local CSV, TSV, XLSX, JSON, or export file with `capture <local-path> --source-type <type> --adapter <adapter> --origin <stable-origin> --external-key <stable-key> --classification <level>`.
- Capture a text query definition with `capture --stdin --name <name> --source-type query --adapter <adapter> --origin <stable-origin> --external-key <stable-query-key> --classification <level>`.
- Capture a small API or query result through `--stdin` only when preserving its exact bytes and format; otherwise save and capture a local file.
- Capture an unavailable or non-copyable dashboard or dataset with `capture <stable-uri-or-object-id> --pointer-only --title <title> --source-type <type> --adapter <adapter> --external-key <stable-key> --classification <level> --authority <authority>` and record the reproducibility limit.
- Use `--published-at` only for a known publication or business-effective time, not as a substitute for execution time.
- Use `--authority` for the workspace-recognized authority label and preserve finer lineage inside the captured manifest.
- Use `--supersedes <prior-source-id>` when a new snapshot replaces a known prior evidence state.
- Capture query definition, result, schema or manifest, and presentation separately when they have independent identities.
- Give each captured object its own stable `--origin` and `--external-key`; do not reuse one key across pages, sheets, or query executions.

Include a compact manifest with system identity, query or export identity, parameters, schema, grain, row counts, pagination or filter state, acquisition time, content hashes, exclusions, and reproducibility limits. Treat a provider-native schema or manifest as source evidence. Keep an agent-generated manifest as derived navigation by default; capture it with `--authority agent-provenance` only when immutable coverage or reconstruction requires it, and never use it as evidence for the underlying values.

## Assess data quality

Measure fitness for the stated analytical purpose before synthesizing conclusions.

- Check completeness, uniqueness, validity, consistency, timeliness, lineage, and reconciliation.
- Report counts and rates for nulls, duplicates, rejected rows, missing periods, and invalid values.
- Compare totals and key distributions with an authoritative control when one exists.
- Check join cardinality and row multiplication before accepting cross-table metrics.
- Separate source defects from extraction defects, transformation defects, and interpretation uncertainty.
- Preserve raw values unchanged; write cleaning, coercion, deduplication, and imputation only as derived evidence.
- Record each transformation, affected row count, and before-and-after hash or summary.
- Lower confidence or stop when a quality defect can materially reverse the conclusion.

## Define metric semantics

Write the definition before reporting a metric value.

- Record numerator, denominator, eligible population, exclusions, unit, scaling, sign, and aggregation method.
- Record grain, grouping dimensions, event time, processing time, window, timezone, and late-arrival policy.
- Record attribution, deduplication, identity resolution, currency conversion, and restatement rules.
- Distinguish counts, distinct counts, sums, ratios, rates, percentages, indexes, estimates, and modeled scores.
- Do not sum ratios, average averages without weights, or combine non-additive metrics across grains.
- Distinguish configured targets, forecast values, observed values, and manually overridden values.
- Preserve the metric owner, semantic-layer definition, effective period, and known definition changes.
- Reconcile similarly named metrics before treating them as the same concept.

## Protect privacy

Minimize structured data before capture without weakening required evidence.

- Retrieve only necessary columns, rows, entities, and time windows.
- Prefer approved aggregates when row-level personal or company-sensitive records are unnecessary.
- Exclude credentials, tokens, cookies, private keys, signed URLs, and connection strings from all artifacts.
- Identify direct identifiers, quasi-identifiers, free-text fields, sensitive categories, and small-cell disclosure risk.
- Apply approved suppression, aggregation, pseudonymization, or redaction before external processing.
- Preserve a local restricted original only when authorized and required for verification.
- Keep differently classified datasets in appropriate trust zones; do not lower classification after aggregation without policy support.
- Do not place sensitive values in filenames, source titles, query text, logs, or wiki prose.

## Create reproducible citations

Tie each analytical claim to the captured source and the narrowest stable locator.

- Cite spreadsheets by source ID, workbook, sheet, stable row key, column, and cell or range when useful.
- Cite tables by source ID, table or result identity, primary key or stable row key, and column.
- Cite queries by source ID, query identity, execution ID, parameter set, and result row or aggregate slice.
- Cite APIs by source ID, endpoint version, object ID, response page or cursor, and JSON pointer.
- Cite dashboards by source ID, dashboard and tile ID, filter state, refresh time, and backing export or query.
- Cite aggregates with both the metric definition and the exact result slice that supports the value.
- Use an immutable result hash plus record or line index only when no stable key exists, and state that limitation.
- Do not cite only a screenshot, mutable dashboard URL, workbook row number, or agent-generated summary.

## Process updates

Treat every refresh, rerun, backfill, or restatement as a new evidence state.

1. Preserve the prior query, result, workbook, export, or API batch unchanged.
2. Capture the new schema and parameters before comparing values.
3. Separate data changes from query, filter, formula, metric-definition, and pipeline changes.
4. Compare row counts, key coverage, schema, quality findings, and affected metrics.
5. Link a replacement snapshot of the same logical evidence unit with `--supersedes` when the prior source is known. Keep append-only batches, late arrivals, and backfills as independent evidence and record their range or batch relationship in the manifest instead of superseding prior data.
6. Preserve historically correct values with their original as-of and availability times.
7. Record backfills, late-arriving data, corrections, and restatements instead of silently replacing old claims.
8. Revalidate only the affected wiki claims while retaining unresolved differences.

## Stop or accept

Stop and report the boundary when:

- the decision, grain, population, time window, timezone, or authority is ambiguous;
- access would exceed the user's authorization or expose credentials or sensitive rows;
- query text, parameters, filter state, formula state, or source identity cannot be preserved;
- pagination, row caps, sampling, hidden filters, missing sheets, or permissions make completeness unknown;
- schema, keys, units, joins, or metric semantics are too unclear to support the claim;
- stale formulas, broken links, API errors, dashboard cache, or missing partitions materially affect results;
- privacy, licensing, size, or policy prevents an acceptable evidence representation;
- data-quality or reconciliation failures can materially change the conclusion.
- database, API, dashboard, or spreadsheet acquisition cannot be proven read-only.

Accept the ingest only when:

- scope, authority, query or export identity, grain, time semantics, and parameters are explicit;
- schema, keys, row counts, filters, pagination, omissions, and completeness are auditable;
- formulas and metric definitions are distinguishable from observed values;
- quality checks and reconciliations are sufficient for the intended use;
- privacy minimization and classification match workspace policy;
- immutable captures preserve source identity without credentials;
- every material claim has a source ID and stable row, cell, object, query, or result locator;
- updates preserve prior evidence and explain definition or value changes;
- normal ingest rebuild, lint, and acceptance checks pass.
