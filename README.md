# LLM Wiki

English | [简体中文](README_ZH.md)

Build a durable, local-first knowledge system that Codex, Claude Code, Gemini CLI, OpenCode, and other compatible AI agents can share and maintain.

LLM Wiki stores its source of truth as plain Markdown inside any local directory or Git repository. Obsidian is a supported optional frontend, not a runtime requirement.

This repository ships four interoperable Agent Skills:

- `wiki-configure` initializes the workspace, configures schemas and policies, exports derived views, and manages agent discovery.
- `wiki-ingest` captures immutable sources and integrates their evidence into the wiki.
- `wiki-query` searches, compares, and answers from the wiki with traceable sources.
- `wiki-maintain` audits and repairs links, indexes, citations, freshness, and knowledge drift.

All runtime files are installed inside the workspace. User notes, source evidence, generated wiki content, and local configuration are never bundled with this repository.

## Core Concepts

- **Evidence before synthesis.** Imported material is preserved as immutable source evidence before an agent turns it into durable wiki knowledge.
- **Traceable claims.** Important conclusions in the wiki point back to source IDs and precise locations, so answers can be checked instead of merely trusted.
- **Clear ownership.** Human notes remain human-owned, source evidence stays append-only, and agents maintain only the explicitly managed wiki areas.
- **Focused workflows.** Configuration, ingestion, querying, and maintenance are separate Skills, so agents activate only the workflow needed for the current task.
- **Language-adaptive by default.** The Skills use English as their portable instruction language. Replies follow the user, while new persistent knowledge follows the workspace language and falls back to the user's language when none is established.
- **Safe, incremental change.** Setup preserves existing files, generated indexes are rebuildable, and write operations use validation, audit events, and rollback boundaries.

The resulting knowledge flow is:

```text
Files, web pages, online documents, code repositories, conversations, spreadsheets, APIs, and databases
        ↓ capture
Immutable source evidence in raw/sources/
        ↓ synthesize with citations
Connected knowledge pages in wiki/
        ↓ query and maintain
Evidence-backed answers, briefs, and reports
```

## Storage and Frontends

- Plain Markdown, JSON metadata, and local files remain the source of truth.
- The workspace can be opened with any editor, managed with Git, or synchronized with your existing file tools.
- Obsidian adds optional navigation through wikilinks, Properties, and Bases. LLM Wiki does not require an Obsidian plugin or a running Obsidian application.
- Search indexes and navigation files are rebuildable; no proprietary database is required to recover the knowledge base.

## Installation

Requirements:

- Node.js 18 or newer to run [`npx skills`](https://github.com/vercel-labs/skills).
- Python 3.10 or newer to run the built-in, dependency-free Wiki CLI.
- A writable local directory. An existing Markdown repository or Obsidian vault also works.

Run this command from the root of the target knowledge workspace:

```bash
npx skills add arronKler/llm-wiki \
  --skill '*' \
  -a universal \
  -a claude-code \
  -y
```

`universal` installs the canonical skills into `.agents/skills/` for compatible clients such as Codex, Gemini CLI, OpenCode, and Cursor. Claude Code accesses the same files through links in `.claude/skills/`.

Use a project-scoped installation and do not add `-g`. The current working directory determines the installation target, so run the command from the workspace you want to manage.

If you only use one specific agent, you can target it directly:

```bash
npx skills add arronKler/llm-wiki --skill '*' -a codex -y
```

The four Skills form one suite and must be installed together. Do not use `--all`: that flag installs into every supported agent, rather than selecting every Skill in this repository.

## First Use

After installation, open the same workspace in your agent and say:

```text
Initialize this directory as a managed wiki using the default configuration.
```

You can also begin by importing a source:

```text
Add this meeting transcript to my wiki.
```

On the first write, the Skills incrementally create:

```text
.wiki/          Configuration, policies, audit events, and transaction state
raw/sources/    Append-only source evidence
raw/derived/    Rebuildable OCR, transcripts, and normalized artifacts
wiki/           Agent-maintained durable knowledge
outputs/        Derived reports and other generated deliverables
```

Initialization does not overwrite existing policy, schema, `AGENTS.md`, or `CLAUDE.md` files. If the workspace is also an Obsidian vault, its `.obsidian/` settings remain untouched and an optional Bases view is added.

## Everyday Use

```text
"Save this file or web page to the wiki."                         → wiki-ingest
"Ingest this repository URL and document its architecture."       → wiki-ingest
"Capture this meeting thread and preserve its decisions."         → wiki-ingest
"Save this dashboard snapshot with its metric definition."        → wiki-ingest
"What conclusions and evidence does the wiki have on pricing?"  → wiki-query
"Repair broken links, duplicate pages, and stale information."  → wiki-maintain
"Connect a new data source and adjust the default classification." → wiki-configure
"Export the public wiki as a static website."                     → wiki-configure
```

Each Skill contains its detailed workflow, safety boundaries, and data contracts in its own `SKILL.md` and `references/` directory. Agents load those resources only when needed.

## Static Site Export

Ask your agent to export the public portion of the wiki as a static site, or, with the recommended `universal` installation shown above, run the built-in CLI directly:

```bash
python3 .agents/skills/wiki-configure/scripts/wiki.py \
  --workspace . \
  export outputs/site \
  --format site \
  --title "Knowledge Base"
```

Open `outputs/site/index.html` directly or serve that directory with any static file server. The generated site includes navigation, safe Markdown rendering, Wikilinks, backlinks, local search, and graph data. It does not copy raw source files.

Only pages explicitly classified as `public` are exported by default. Add another classification only for an explicitly authorized local output, for example `--classification internal`. Public remains included, and a selected page is rejected if it cites unknown or disallowed source evidence. Generating a site does not deploy or share it.

The built-in themes are `default`, `editorial`, and `minimal`. Optional add-ons provide local search, a table of contents, an interactive graph, code-copy controls, and homepage facets. Agents can discover the exact installed options automatically, or you can compose them directly:

```bash
python3 .agents/skills/wiki-configure/scripts/wiki.py \
  --workspace . \
  export outputs/site \
  --format site \
  --theme editorial \
  --addon toc \
  --addon graph \
  --addon code-copy
```

Theme and add-on choices affect only the already-authorized site snapshot; they never expand its classification scope. Workspace defaults are optional, while command-line choices apply to one export.

## Updating and Removing

Update project-scoped Skills from the workspace root:

```bash
npx skills update -p -y
```

Runtime updates do not overwrite `.wiki/`, `raw/`, `wiki/`, `outputs/`, or human-maintained notes.

Remove the Skills:

```bash
npx skills remove wiki-configure wiki-ingest wiki-query wiki-maintain -y
```

Removing the Skills does not delete knowledge or evidence already created in the workspace.

## Data and Security Model

- `data/`, `inbox/`, and `notes/` are human-owned and read-only to agents by default.
- `raw/sources/` is append-only. Existing source evidence must not be modified or deleted.
- `wiki/` contains agent-maintained synthesis. Every important claim should trace back to a source ID and precise locator.
- Static exports default to public pages, never copy raw source evidence, and remain local until you explicitly publish them.
- Source content is always treated as untrusted data and must never be executed as agent instructions.
- Credentials must come from environment variables, the system keychain, or an agent connector, never from the workspace.
- Classification labels are not access controls. Separate personal, internal, confidential, and restricted data with distinct workspaces or repositories and real ACLs.
- Multiple agents may read concurrently, but a workspace must have only one writer at a time.

Installing a Skill grants an agent permission to execute its scripts. Review the repository before installation, and use appropriate agent and model policies for sensitive workspaces.

## Inspiration

The design is inspired by [Karpathy's discussion of LLM-oriented knowledge systems](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). This repository contains an independent implementation and does not copy the gist as source code or documentation.

## License

[MIT](LICENSE)
