# Legacy Workspace Migration and Cross-Agent Discovery

## Prefer compatibility-first migration

Inventory before moving anything:

- the workspace root and optional `.obsidian/` configuration when present;
- human-authored paths such as `data/`, `inbox/`, and `notes/`;
- frontmatter and IDs in legacy `raw/entries/*.md`;
- `wiki/_index.md`, `_backlinks.json`, and page types;
- `also`, `last_updated`, legacy `sources`, and wikilinks;
- `.claude/skills`, `.codex/skills`, `.opencode/skills`, `.agents/skills`, `AGENTS.md`, and `CLAUDE.md`;
- Git, synchronization, symlinks, and case sensitivity.

Map existing paths in `.wiki/config.json`. Preserve them in place by default; do not force new directory casing or taxonomy.

## Preserve the legacy personal-wiki contract

- Treat `data/` as a human-owned source drop and never rewrite it.
- Treat `raw/entries/` as valid, immutable legacy source cards. Continue parsing fields such as `id`, `date`, `source_type`, and `source_path`.
- Keep legacy source IDs as citation targets. Do not bulk-convert them to `src-*`.
- Continue using `also` for retrieval and link resolution; use `aliases` on new pages. During an explicit migration, dual-write both fields for a transition period when needed.
- Continue reading `last_updated`; use `updated` on new pages. Do not remove legacy fields until every consumer has upgraded.
- Preserve headings, categories, summaries, and comments in the curated `wiki/_index.md`. Let the CLI generate only `_catalog.md`, `_sources.md`, and `_backlinks.json`.
- Continue reading legacy `_backlinks.json`. Allow the new CLI to rebuild it in a compatible format only after backing it up and validating consumers.

Backfill fields in bulk only when the user explicitly requests schema unification. Record schema migration and content revision as separate transactions and events.

## Keep one canonical skill layout

Maintain:

```text
<workspace>/.agents/skills/
  wiki-ingest/
  wiki-query/
  wiki-maintain/
  wiki-configure/
```

Treat `.agents/skills` as the only editable source of truth. Point other clients to canonical `SKILL.md` files with thin wrappers or symlinks; do not copy four independent suites.

Prefer installing the complete suite from the workspace root with `npx skills`:

```text
npx skills add arronKler/llm-wiki --skill '*' -a universal -a claude-code -y
```

Keep installation project-scoped and do not use `-g`. Accept installer-managed `skills-lock.json`, the canonical `.agents/skills` copy, and the `.claude/skills` directory symlink. The four skills share `wiki-configure/scripts/wiki.py` through sibling-relative paths, so never install only part of the suite.

When generating a wrapper:

- make its frontmatter name and description sufficient for triggering;
- point its body only to the canonical skill and require complete reading;
- use relative paths or rebuildable links instead of machine-specific absolute paths;
- preserve existing `.claude/skills`, `.codex/skills`, `AGENTS.md`, and `CLAUDE.md` instructions;
- do not use `--force` unless explicitly requested.

## Explain agent discovery boundaries

Agent clients differ in discovery paths and symlink support. Never promise that placing files in a workspace makes them automatically discoverable by every agent launched from any directory. Use these guarantee levels:

1. When launched inside the workspace as a project or repository, use project-level `.agents/skills`.
2. For Claude or clients that scan only dedicated directories, generate thin `.claude/skills` wrappers or use the client's add-directory or project mechanism.
3. Let Gemini CLI, OpenCode, and current Codex discover `.agents/skills` directly. Generate optional `.opencode/skills` wrappers only when client policy disables agent-compatible paths.
4. For legacy Codex configuration, generate a `.codex/skills` bridge when needed and prefer migration to `.agents/skills`.
5. When launching outside the workspace, install an explicit user-level link or skill, or add the directory to the client's workspace. Treat this as one-time client configuration.
6. For agents without Agent Skills support, add a very short `AGENTS.md` or `CLAUDE.md` that states the workspace root, permission boundaries, and four canonical skill paths.

Do not embed the complete knowledge contract in a bridge; it will drift during upgrades.

## Move a workspace

After moving, rerun `locate`, `install-bridges`, and `doctor`. Check:

- symlink targets and wrapper-relative paths;
- workspace-relative paths in `.wiki/config.json`;
- absolute paths left in adapters;
- Obsidian attachments and wikilinks;
- Git submodule and synchronization ignore rules;
- user-level links that may still target the old location.

Do not globally replace original paths inside raw sources. Raw content is evidence. Update only configuration, derived mappings, and bridges.

## Upgrade and roll back

1. Record the current skill and version, config, schema, policy, and bridge hashes.
2. Upgrade only canonical skills and compatible CLI or assets.
3. Do not bulk-rewrite wiki content in the same transaction.
4. Regenerate wrappers, then run `doctor`, `lint`, and the legacy fixture.
5. On failure, restore canonical skills, config, and bridges. Do not roll back or rewrite newly captured raw sources.

At minimum, verify that ingest, query, maintain, and configure trigger from inside the workspace; legacy sources and aliases remain searchable; bridges preserve existing instructions; and launching outside the workspace produces a clear installation prompt rather than silent failure.
