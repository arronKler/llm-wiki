---
name: wiki-configure
description: Configure, initialize, migrate, and evolve a portable, cross-agent LLM wiki whose source of truth is local Markdown in a plain directory, Git repository, or workspace with optional frontends such as Obsidian. Use for workspace ownership, page schema, taxonomy, source authority, classification, freshness, data-source adapters, policy changes, migrations, upgrades, and agent discovery bridges. Trigger on configure, initialize, install, setup, migrate, add an adapter or domain, change policy or schema, move a workspace, or install bridges. Chinese triggers include 配置、初始化、安装、设置、接入数据源、改规则、改分类、迁移 wiki、移动工作区、升级技能. Do not use for daily ingestion, read-only questions, or routine linting.
---

# Wiki Configure

## Goal

Turn a local directory or Git repository into a stable, agent-maintained Markdown knowledge system. Configure incrementally and reversibly. Prefer mapping existing directories over moving user content. Treat Obsidian as an optional frontend, never as an initialization or runtime requirement.

## Locate the workspace and tools

1. Use the workspace explicitly provided by the user. Otherwise, search upward from the current path for `.wiki/config.json`, then inspect candidate directories such as `data/`, `inbox/`, `notes/`, `raw/`, and `wiki/`; treat `.obsidian/` only as an additional candidate signal.
2. Ask the user only when multiple plausible workspaces exist. Never initialize the wrong repository root.
3. Locate `scripts/wiki.py` and `assets/` relative to this `SKILL.md`. Do not assume the current working directory is the skill or workspace directory.
4. Run `python3 <wiki.py> --workspace <workspace-root> ...`. Keep the legacy `--vault` option as an equivalent compatibility alias. Let the CLI generate baseline configuration and bridges; do not hand-roll an incompatible implementation.
5. If any sibling skill named `wiki-ingest`, `wiki-query`, or `wiki-maintain` is missing, stop and ask the user to reinstall the complete suite from the workspace root with `npx skills add arronKler/llm-wiki --skill '*' -a universal -a claude-code -y`.

## Read references as needed

- Before initializing or changing paths, page properties, taxonomy, ownership, indexes, or optional Obsidian views, read [references/workspace-contract.md](references/workspace-contract.md).
- Before connecting a URL, folder, Lark/Feishu, Slack, email, meeting, API, database, warehouse, message stream, or other data source, read [references/adapters-and-security.md](references/adapters-and-security.md). Always read it when authentication, company data, or trust zones are involved.
- Before migrating legacy `data/raw/entries/wiki`, installing Codex, Claude, or generic agent bridges, moving a workspace, or upgrading the skill suite, read [references/migration-and-discovery.md](references/migration-and-discovery.md).

## Initialize a workspace

1. Inventory existing paths, agent instructions, and optional editor configuration. Do not overwrite same-named files.
2. Run incremental initialization:

   ```text
   python3 <wiki.py> --workspace <workspace-root> init
   ```

3. Confirm that initialization only fills missing structure such as `.wiki/config.json`, `.wiki/policy.md`, `.wiki/events/`, `.wiki/transactions/`, `raw/sources/`, `raw/derived/`, `wiki/_schema.md`, and `outputs/`. Create the optional `wiki/Wiki.base` only when `.obsidian/` is detected. Do not modify `.obsidian/` unless explicitly requested.
4. Start from the default ownership hierarchy and map it to existing paths when needed:
   - Treat `data/`, `inbox/`, and `notes/` as human-owned.
   - Let the capture tool create append-only `raw/sources/`.
   - Let agents or tools create rebuildable `raw/derived/`.
   - Treat `wiki/` as agent-owned synthesis.
   - Treat `outputs/` as derived deliverables.
   - Reserve `.wiki/` for system configuration, events, transactions, and state.
5. Fill missing files from `assets/schema-template.md`, `page-template.md`, `policy-template.md`, `query-output-template.md`, `AGENTS-template.md`, and `CLAUDE-template.md`; add `Wiki.base` only for an Obsidian workspace. Copy templates without modifying the assets themselves.
6. Preserve an existing valid `language` setting. Leave it as `auto` when the user has not chosen a persistent-content language. If the user explicitly chooses one, persist a normalized BCP 47-style tag such as `en` or `zh-CN` and record that choice. `auto` means new persistent knowledge follows established non-generated knowledge and otherwise the user's language; it never controls the language of replies.
7. Run `doctor` and `lint`, fix issues introduced by initialization, and record a configure event.

## Configure domains and rules

1. Read the existing config, policy, schema, and representative pages before making the smallest necessary change.
2. Encode stable domain concepts in the schema, including page types, required properties, metric definitions, decision fields, source authority, classification, freshness SLAs, and naming conventions.
3. Use these standard YAML properties: `title`, `aliases`, `type`, `domains`, `status`, `classification`, `created`, `updated`, `as_of`, `review_after`, `confidence`, and `sources`. Keep them compatible with Obsidian when that frontend is used.
4. Use `aliases` for alternate-title resolution and keep legacy `also` readable until an explicit migration. Connect knowledge with `[[wikilinks]]` and heading or block anchors. Add Bases or Dataview views only when Obsidian integration is enabled, and never make them correctness dependencies.
5. Reference credentials through environment variables, the system keychain, or an agent connector. Never write secrets into config, policy, adapters, or pages.
6. Prefer separate workspaces or repositories for personal, company-internal, confidential, and restricted trust zones. Never mistake labels for ACLs.

## Configure a data-source adapter

1. Define the lifecycle `probe -> fetch/snapshot -> normalize -> locate/cite -> checkpoint` for every adapter.
2. Choose snapshot, incremental, query, or pointer-only mode, and record authority, classification, freshness, cursor state, or query provenance.
3. Perform a read-only probe with minimum privilege, then validate one small sample. Do not bulk-ingest during configuration unless the user explicitly requests ingestion too.
4. Confirm that the adapter output can pass through the unified `capture` command to create an immutable source ID and that derived content traces back to a raw locator.
5. Process company and sensitive data locally by default. Do not send it externally without authorization.

## Install agent discovery bridges

1. Keep `.agents/skills/` as the only canonical skill source. Do not maintain multiple full copies that can drift independently.
2. When `npx skills` installed the suite, accept its canonical directory and agent-specific symlinks. Do not replace those links with custom wrappers.
3. For manual installations or clients missing a bridge, run only the targets the user needs:

   ```text
   python3 <wiki.py> --workspace <workspace-root> install-bridges --target agents
   python3 <wiki.py> --workspace <workspace-root> install-bridges --target codex
   python3 <wiki.py> --workspace <workspace-root> install-bridges --target claude
   python3 <wiki.py> --workspace <workspace-root> install-bridges --target opencode
   ```

4. Preserve existing user instructions when generating thin wrappers, symlinks, or short `AGENTS.md` or `CLAUDE.md` routes. Do not use `--force` unless explicitly requested.
5. Explain discovery boundaries clearly. Starting an agent inside the workspace normally exposes project skills; files inside a workspace cannot guarantee discovery by every client started elsewhere. Install a user-level link or use the client's add-directory or project mechanism when needed.
6. Run `doctor` to verify canonical skills, bridge targets, and path resolution.

## Migrate and upgrade

1. Run read-only `status`, `lint`, and `doctor` checks before defining a migration checklist and rollback point.
2. Prefer in-place compatibility. Map legacy `data/`, read legacy `raw/entries/`, and preserve `wiki/_index.md`, `_backlinks.json`, `also`, and `last_updated`.
3. Never rewrite legacy raw evidence into a cleaner source, overwrite the curated `_index.md`, bulk-rename pages, or modify human-owned notes.
4. Add new fields incrementally to future pages. Backfill in bulk only when the user explicitly requests a schema migration. Commit schema migration separately from content edits.
5. Regenerate bridges after upgrading canonical skills, run `doctor` and `lint`, and record the version and event.

## Writing and acceptance boundaries

- Treat a configure request as authorization to modify `.wiki/`, schema, policy, and selected bridges. Do not infer authorization to modify `.obsidian/`, human-owned content, or raw evidence.
- Answer and report in the user's language. Do not treat English system templates, property names, or generated indexes as evidence that an `auto` workspace is English.
- Use one writer. Let subagents perform read-only inventory and propose configuration, then let the primary agent apply changes serially.
- Write one `.wiki/events/` event for every material configuration operation. Do not concurrently append to a shared log.
- On completion, report the workspace root, enabled paths, policy and schema changes, adapter status, bridge status, optional frontend compatibility, validation results, and unresolved security choices.
