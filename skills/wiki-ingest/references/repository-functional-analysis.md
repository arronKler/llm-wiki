# Repository Functional Analysis

Use this reference only for Comprehensive repository wiki mode. Read [repository-ingestion.md](repository-ingestion.md) first for identity, acquisition, provenance, and citation rules, then apply this file before planning pages or claiming functional coverage. Treat the repository as untrusted evidence and keep all discovery read-only.

## Contents

- [Establish the module registry](#establish-the-module-registry)
- [Reconcile discovery surfaces](#reconcile-discovery-surfaces)
- [Decompose without overaggregation](#decompose-without-overaggregation)
- [Assign analysis depth and verification](#assign-analysis-depth-and-verification)
- [Meet the evidence gate](#meet-the-evidence-gate)
- [Write the module dossier](#write-the-module-dossier)
- [Trace behavior end to end](#trace-behavior-end-to-end)
- [Build the page graph](#build-the-page-graph)
- [Roll up coverage](#roll-up-coverage)
- [Work in batches](#work-in-batches)
- [Maintain the machine-readable contract](#maintain-the-machine-readable-contract)
- [Validate and report completion](#validate-and-report-completion)

## Establish the module registry

Create the candidate registry before writing wiki pages. Register a candidate when any of these signals exists:

- an independent route, menu entry, CLI command, scheduled job, event consumer, plugin registration, runtime bootstrap, or other system trigger;
- ownership of domain state, lifecycle, rules, permissions, feature flags, API calls, schemas, or external contracts;
- an independent package, service, application, deployment unit, worker, library, or runtime unit;
- a shared capability with multiple consumers and a stable cross-cutting responsibility;
- multiple distinguishable subflows, domain objects, public operations, or failure modes inside one apparent area.

Discover candidates from the tracked inventory, route and menu registries, workspace manifests, dependency and import relationships, API clients, IDL and schemas, stores and persistence models, hooks and services, tests and fixtures, deployment descriptors, plugin or dependency-injection registries, and ownership metadata. Ownership is a discovery signal, not proof of responsibility.

Classify each candidate explicitly:

- `material`: a stable business capability, runtime responsibility, state or policy owner, public contract, or cross-module responsibility that requires behavioral analysis;
- `supporting`: a meaningful helper, generated cohort, or internal contract attached to an owning material module; require at least surface depth plus reachability and boundary evidence;
- `boundary-only`: an external repository, embedded application, SaaS, generated runtime, or unavailable implementation; require a local page anchor, the visible contract or call boundary, and an explicit scope limit;
- `excluded`: incidental, duplicated, vendored, generated, test-fixture, or otherwise non-material content; require a reason and discovery locator.

Do not equate a directory, package, route, or symbol with a module automatically. Do not omit a candidate merely because it will share a page with another module. Never downgrade a candidate to avoid the material evidence gate. If an independent trigger, state owner, lifecycle, runtime unit, or public contract cannot be classified confidently, record a blocking discovery gap instead of calling it supporting or excluded.

## Reconcile discovery surfaces

Maintain explicit discovery records for every observed route, menu item, command, trigger, workspace package, service, runtime unit, major state owner, API or IDL client, deployment unit, and shared capability. Give each record a stable ID, kind, immutable repository locator, and either a module ID or a disposition with a reason.

Maintain inventory groups for the tracked census. Every manifest file must fall under at least one explicitly described inventory scope, including generated, vendored, fixture, and non-material areas. Map each group to one or more module IDs or give it an explicit disposition and reason. Generated, vendored, fixture, and leaf-utility cohorts may be grouped; do not let one broad catch-all group hide unrelated business or runtime areas.

The registry is auditable only for the discovery surfaces it records. Static analysis cannot prove that an arbitrary repository contains no undiscovered dynamic route or module. Record discovery blind spots such as runtime registration, reflection, generated routing, remote configuration, or inaccessible submodules. Treat a blind spot as blocking when it may conceal a material module; resolve, bound, or explicitly exclude it with evidence before declaring completion.

## Decompose without overaggregation

Give an independent registry row to every material route family, business lifecycle, state owner, runtime unit, public contract, or shared capability. Multiple rows may map to different anchored sections of one page, but no two module rows may share the same normalized page and heading anchor. Keep every dossier locator inside its owning module section and outside any nested child or supporting module section; a parent cannot borrow a child's headings as its dossier.

Split a large module into material children when it contains multiple independently triggered flows, state owners, domain lifecycles, or public contracts. Analyze the material leaves; a parent summary is not evidence for its children.

Use these rules across repository types:

- For backend services, treat callers, operators, jobs, and events as actors; emphasize APIs, state, failure, security, and operations.
- For libraries and SDKs, emphasize public APIs, compatibility, invariants, call sequences, extension seams, and consumer boundaries.
- For infrastructure, describe declared desired state and orchestration; do not infer deployed runtime state.
- For monorepos, inventory every workspace or package, but group trivial or tightly coupled leaf packages under a durable capability while retaining separate discovery records.
- For generated code, cover the generator, inputs, and output cohort unless the generated output is itself an authoritative public contract.

## Assign analysis depth and verification

Track understanding depth separately from verification evidence:

| `analysis_depth` | Meaning |
| --- | --- |
| `inventory` | Only identity, paths, and discovery signals are known. |
| `surface` | Entrypoints, purpose, public surface, and immediate dependencies are known. |
| `behavioral` | Internal orchestration, decisions, state or interface boundaries, outcomes, and failure behavior are explained. |

Track verification independently:

| `verification.status` | Meaning |
| --- | --- |
| `test-supported` | Representative tests directly support the described behavior. |
| `contract-supported` | Schemas, IDL, static contracts, or other authoritative checks support it. |
| `gap` | No adequate repository verification was found; record why and what remains unverified. |
| `not-applicable` | Verification does not apply to a non-material record; give a reason. Material modules must use `gap` when unsupported. |

Only `behavioral` can satisfy a material module. Test support improves evidence quality but is not required when a truthful verification gap is visible. Never upgrade depth because a README, menu, route declaration, package manifest, barrel export, or name lists a capability.

## Meet the evidence gate

For every material module, capture and cite substantive evidence in these classes:

- `reachability`: a real entrypoint, registration, trigger, caller, or orchestration path;
- `implementation`: the core behavior, policy, rule, transformation, or authoritative declaration;
- `boundary`: owned state, data model, API, IDL, message, configuration, dependency, or external-system boundary;
- `verification`: representative tests or contracts when present.

Use different substantive locators; prefer different files when that improves independence, but do not require an arbitrary file count. A small module may express multiple evidence classes in one file. A library, declarative system, or infrastructure module may use an authoritative schema or declaration as implementation evidence. Material modules may share boundary or verification evidence when appropriate, but each must have its own reachability and implementation locator.

List every defining file or directory prefix in the module's `paths`. At least one material-module `implementation` locator must resolve inside those paths; for `supporting` and `boundary-only`, at least one `boundary` locator must resolve inside them. Entrypoint, shared-schema, and test evidence may live outside the owned paths when the dependency direction is explained.

If no representative test or contract exists, set verification to `gap` with an explicit reason. For a large module, meet the gate for each material child instead of sampling only the root entrypoint. Discovery-only evidence cannot establish behavioral coverage.

## Write the module dossier

Give every material module a dedicated page or a stable anchored section. Answer every applicable facet and mark an inapplicable facet with a concise reason:

1. `scope`: identity, revision, responsibility, and non-responsibility;
2. `actors`: target users, callers, operators, events, and use cases;
3. `entrypoints`: routes, menus, commands, triggers, registrations, or call entry;
4. `components`: core components and dependency direction;
5. `behavior`: workflows, decisions, domain objects, invariants, and business rules;
6. `state`: local state, persistence, caches, ownership, and lifecycle;
7. `interfaces`: APIs, IDL, events, schemas, and external systems;
8. `controls`: permissions, roles, feature flags, configuration, and trust boundaries;
9. `failure`: errors, degradation, retries, recovery, safety, and observability;
10. `verification`: behavior proved by tests or contracts and remaining gaps;
11. `evolution`: extension points, migrations, design history, contradictions, and unknowns.

A capability list, filename inventory, or table of names is not a dossier. Do not create empty headings solely to satisfy the checklist; record `not-applicable` once with evidence-based reasoning.

For a material module, `scope`, `entrypoints`, `components`, `behavior`, `failure`, `verification`, and `evolution` must be documented with resolvable page locators. Only `actors`, `state`, `interfaces`, and `controls` may be `not-applicable`, each with a reason. An all-`not-applicable` dossier can never pass.

## Trace behavior end to end

Make every material module participate in at least one evidence-backed behavior trace. Use the architecture-appropriate form of this chain:

```text
actor or event
→ ingress or trigger
→ orchestration
→ domain behavior and decisions
→ state, data, or interface boundary
→ outcome or side effect
→ failure and recovery
→ verification or observability
```

For frontend code, this may pass through route, page, component, hook, store, service, API, state update, and UI feedback. For a service, library, CLI, worker, or infrastructure repository, map the same semantic stages to its actual runtime model.

Name the modules responsible for each step and cite the implementation or contract that supports it. When the trace enters another repository, embedded application, SaaS, or unavailable runtime, stop at `boundary-only`: document direction, contract, data, and locally visible failure handling without inventing the external implementation.

## Build the page graph

Match and update an existing canonical repository page when one exists; otherwise create one home page. Link it to top-level architecture, domain, module, flow, interface, data, runtime, operations, security, verification, evolution, glossary, and coverage subjects that are material for this repository.

Use the smallest page graph that preserves module dossiers and behavior traces, not the smallest number of pages. Multiple modules may share a page only through distinct anchors. Make every repository page reachable from the home page through rendered wikilinks and link each child back to an owning parent or the home page. Every covered lens, documented dossier facet, and declared flow section must contain visible substantive text beyond its heading and navigation links. Links and headings inside frontmatter, HTML comments, inline code, indented code, fenced code blocks, or raw HTML `pre` and `code` blocks do not count as visible navigation or sections.

## Roll up coverage

Treat module-row granularity and page granularity as independent. A parent can be complete only when:

- all material descendants are `behavioral` and meet their dossier, evidence, and flow gates;
- no material descendant has a blocking gap;
- the parent-specific cross-cutting responsibilities are also explained.

Do not let parent evidence replace child evidence. Do not mark a combined row such as “Home, Leads, Merchants, Tasks, and Funds” complete when those subjects have independent entrypoints, state, lifecycles, or contracts. Keep shallow children visible as `inventory`, `surface`, or blocked.

Evaluate every coverage lens from [repository-ingestion.md](repository-ingestion.md#apply-coverage-lenses) at repository level. At module level, record only applicable lenses and group a shared `not-applicable` rationale by module kind when that avoids repetitive empty cells.

## Work in batches

Use one pinned evidence set throughout a run. A pinned evidence set may include a parent revision plus immutable submodule, schema, or external contract identities needed by the claims, but each schema-version-1 coverage registry binds exactly one repository identity and manifest. Represent a submodule as `boundary-only` in its parent registry and use a separately validated child registry when its internal behavior is in scope. A new revision starts a new evidence state.

Use these batches as a default, not a fixed template:

1. census, registry, and repository/runtime `architecture-baseline`;
2. business domains, material modules, and core flows;
3. shared packages, interfaces, data/state, and cross-cutting capabilities;
4. security, operations, verification, and evolution;
5. reconciliation, navigation, and final validation.

Call an interrupted result `architecture-baseline` or `functional-analysis-partial`. Never call it `comprehensive-complete` merely because the architecture batch or repository overview is finished.

## Maintain the machine-readable contract

Keep one logical, versioned coverage artifact under `raw/derived/repository-coverage/<repository-key>/<revision>.json`. Schema version 1 requires one JSON file; it has no shard envelope or merge semantics. A future schema version may add sharding without changing the meaning of the registry. Bind the artifact to a captured repository manifest through `manifest_source_id`; the manifest remains immutable evidence while the derived coverage artifact can evolve during analysis.

The manifest source must be a captured, non-pointer `repository-manifest` using the `git` or `repository` adapter and the shape in [the manifest example](../assets/repository-manifest.example.json). Its provenance and captured content must both bind the same repository identity and revision as the coverage artifact. Every module path, inventory path, discovery locator, and repository-evidence locator must resolve into its tracked-file census. A parent registry cites only the submodule gitlink, never files from the child census. Map every gitlink to exactly one manifest submodule row, one boundary-only module row, and a boundary-only inventory assignment; never aggregate multiple child repositories into one boundary row or let a parent material module own a gitlink path. Do not substitute a repository pointer, README, or arbitrary source record for the manifest.

Use `kind: "llm-wiki.repository-coverage"`, `schema_version: 1`, and include:

- `repository.identity` and immutable `repository.revision`;
- `manifest_source_id`, `home_page`, `batch_state`, and `discovery_gaps`;
- `repository_lenses`, containing exactly one repository-level assessment for each fixed lens below;
- `discovery_records` and `inventory_groups`, each mapped or explicitly disposed with a reason;
- `modules` with ID, title, materiality and reason, hierarchy and ownership, paths, page and anchor, depth, verification, dossier, evidence classes, flow IDs, gaps, and any non-material disposition;
- `flows` with module-aware, evidence-backed steps;
- no hand-authored completion counts that can drift from the registry.

Set `batch_state` to exactly one of `architecture-baseline`, `functional-analysis-partial`, or `comprehensive-complete`. The validator computes completion independently; the declared value never overrides missing depth, evidence, pages, mappings, flows, lenses, or gaps.

Use these fixed `repository_lenses` IDs: `purpose-product-boundary`, `domain-business-logic`, `architecture-dependency-flow`, `public-interfaces`, `data-state`, `configuration-delivery`, `security-trust`, `ownership-maintenance`, `verification`, and `evolution`. Give each lens `{ "id", "status", "page", "anchor", "evidence" }`, where `status` is `covered`, `not-applicable`, `partial`, or `blocked`. The page and anchor must resolve for every status so that coverage or its rationale remains visible. `covered` requires evidence. `not-applicable` requires a reason and is non-blocking. `partial` and `blocked` require a reason and explicit `blocking`; `blocked` must be blocking. Every evidence source ID must appear in the lens page frontmatter. This is one repository-level assessment, not a module-by-lens Cartesian matrix.

Represent a documented dossier facet as `{ "status": "documented", "locator": "wiki/page.md#Heading" }`. Represent an inapplicable facet as `{ "status": "not-applicable", "reason": "..." }`. Represent repository evidence as `{ "class": "implementation", "source_id": "src-...", "locator": "repository@<revision>:path#locator" }`. Evidence locators always name an exact tracked file and a non-empty stable fragment. Evidence sources must follow the exact source-role, pointer, origin, and `external_key` binding rules in [repository-ingestion.md](repository-ingestion.md#cite-commit-path-and-line): non-pointer `code`, pointer-only `repository`, or non-pointer `repository-archive`, using the `git` or `repository` adapter. Do not use web, meeting, manifest, or unrelated source records to satisfy repository evidence gates.

Represent a gap as `{ "id": "gap-id", "kind": "verification", "reason": "...", "blocking": false }`. Use the same shape in top-level `discovery_gaps` and module `gaps`, with globally unique gap IDs.

A discovery or inventory record must map to `module_id` or `module_ids`. Only genuinely excluded or inapplicable records may instead use `{ "disposition": "excluded|not-applicable", "reason": "..." }`. A `supporting` or `boundary-only` candidate must map to a module row so its evidence gate cannot be bypassed. After expanding directory prefixes against the manifest, no tracked file may have both a module assignment and a direct disposition or two different direct dispositions.

Give every module `id`, `title`, `materiality`, `materiality_reason`, `paths`, `analysis_depth`, `verification`, `dossier`, `evidence`, `flow_ids`, and `gaps`, plus optional `parent_id`. Require `page` and one unique heading `anchor` except for `excluded`. A supporting module also requires `owner_module_id` resolving to a material module. Every non-material module requires `{ "disposition": { "reason": "...", "evidence": { "source_id": "src-...", "locator": "..." } } }`; a material module must not have one.

For material modules, require `behavioral` depth and all eleven dossier facets; the seven core facets defined above must be documented. Supporting modules require at least `surface` depth plus `reachability` and `boundary` evidence; boundary-only modules require at least `surface` depth plus `boundary` evidence. A `test-supported` or `contract-supported` verification status also requires `verification` evidence. A verification `gap` or non-material `not-applicable` status requires `verification.reason` and does not require verification-class evidence. Material modules may not use `not-applicable`; use `gap` when no representative test or contract exists. Do not reuse the exact same source ID and locator for multiple required evidence classes.

Give every flow `{ "id", "module_ids", "page", "anchor", "steps" }`. Its unique page heading must be reachable from the repository home, cite all flow evidence sources in frontmatter, and link to participating module pages when separate. Give every step a non-empty `stage`, `description`, `module_ids`, and evidence array. Use all eight semantic stage IDs in every complete flow: `actor-trigger`, `ingress`, `orchestration`, `domain-decision`, `state-interface-boundary`, `outcome`, `failure-recovery`, and `verification-observability`. Map them to the repository's actual architecture rather than inventing UI concepts. Every referenced module and source must resolve. A material module must participate in at least one declared flow and in at least one `orchestration`, `domain-decision`, or `state-interface-boundary` step.

For every page locator, write the literal Markdown heading text as `anchor`. Validation normalizes it with the same Obsidian-style heading normalization used for wikilinks and requires exactly one matching heading in that page. Two module rows or two flows may not share the same normalized page-and-anchor pair. Block IDs are not accepted for module dossier ownership because completion requires a unique heading section.

Schema version 1 required fields are not nullable. Omit an optional field instead of writing `null`, except `parent_id`, which may be `null` for a root module. Unknown properties are tolerated for producer metadata but are ignored by the validator and cannot change materiality, depth, evidence, flow, roll-up, or completion results.

Before constructing this artifact, read [the complete schema example](../assets/repository-coverage.example.json). Replace every example identity, source ID, path, locator, page, module, and explanation with evidence from the current repository; do not copy its sample module boundaries as a default ontology.

The artifact is derived navigation and completion evidence, not primary evidence for implementation claims.

## Validate and report completion

Run the deterministic validator before reporting status:

```text
python3 <wiki.py> --workspace <workspace-root> repository-coverage <coverage-json>
python3 <wiki.py> --workspace <workspace-root> --json repository-coverage <coverage-json>
```

Use `--allow-partial` only for intermediate batches. Without it, exit status `0` means structurally complete, `1` means incomplete or internally inconsistent, and `2` means malformed, unsafe, or unsupported input. With `--allow-partial`, an honestly declared, internally consistent intermediate batch may return `0`; broken mappings, unknown evidence, missing pages, invalid anchors, cycles, invalid roll-ups, and other structural findings still return `1`. The validator checks the declared registry, mappings, repository lenses, page graph, evidence references, dossiers, flows, roll-ups, and completion state. It does not discover arbitrary framework modules or judge prose quality; machine output must keep `semantic_checks_performed: false` visible.

Declare `comprehensive-complete` only when:

- every manifest file belongs to an inventory group, and every discovery record and inventory group is mapped or explicitly disposed;
- every material module maps to a page and stable anchor;
- no material module remains at `inventory` or `surface`;
- every material module meets the dossier, evidence, and behavior-trace gates;
- every verification gap is explicit;
- no material module or descendant has a blocking gap;
- all ten repository lenses are assessed, with no blocking repository lens;
- parent roll-ups are valid, the home page reaches all module pages, and normal rebuild and lint checks pass.

A validator exit status of `0` is necessary but not sufficient for Comprehensive completion. Before claiming completion, perform a reader acceptance review and confirm that a non-code reader can answer, without opening source code:

- what the repository does, who uses it, and what lies outside its boundary;
- how the major modules relate, what each owns, and which dependency directions matter;
- how core end-to-end flows cross modules, apply business rules, and change data or state;
- which public interfaces, integrations, configuration, delivery, security, reliability, and operational concerns matter;
- which behavior is supported by tests or contracts, where verification is absent, and which important gaps remain;
- which design decisions and evolution evidence are documented, and where rationale or deployed-runtime truth remains unknown.

Also reconcile terminology, responsibility boundaries, flow transitions, and business rules across pages. Distinguish documented intent, reachable implementation, tested expectation, configured default, agent inference, and observed runtime. Record the semantic review result separately; never turn a deterministic `0` into a claim that semantic discovery or prose quality was machine-verified.

Report at least:

```text
candidate_records: 58
material_modules: 42
behavioral: 38
test_supported: 28
verification_gaps: 10
surface_only: 2
inventory_only: 0
blocked: 2
unmapped_candidates: 0
completion: partial
```

Treat `test_supported` as a subset of `behavioral`. These counts prove internal consistency for the declared registry, not that semantic discovery was exhaustive. Keep blind spots and agent-only judgments visible in the human report.
