# Export and Publishing

Use this reference when the user asks to export, share, publish, or generate a static view of a managed wiki. Treat export as creation of a derived local artifact. Do not infer authorization to deploy, upload, email, or otherwise disclose it.

## Select an export profile

The current built-in profile is `site`. It creates a dependency-free static site with navigation, safe Markdown rendering, Wikilinks, backlinks, local search, and graph data.

When the user asks for a visual theme, table of contents, interactive graph, code-copy controls, facets, or other optional presentation behavior, read [export-themes-and-addons.md](export-themes-and-addons.md) after this reference.

Use the shared CLI relative to `wiki-configure/SKILL.md`:

```text
python3 <wiki.py> --workspace <workspace-root> export outputs/site --format site
```

Set a user-facing title when requested:

```text
python3 <wiki.py> --workspace <workspace-root> export outputs/site --format site --title "Knowledge Base"
```

Discover the exact themes, add-ons, option schemas, and Workspace defaults before composing non-default output:

```text
python3 <wiki.py> --workspace <workspace-root> --json export-capabilities --format site
```

## Enforce the disclosure boundary

- Export only pages explicitly classified as `public` by default. Exclude pages with missing or invalid classification.
- Treat `public` as implicitly included when the user explicitly adds another classification.
- Repeat `--classification` for each additional trust zone the user authorizes, for example `--classification internal` or `--classification internal --classification confidential`.
- Require every source cited by a selected page to have an allowed classification. Stop on unknown, invalid, or disallowed source evidence instead of silently publishing an incomplete trust decision.
- Never copy `raw/sources/`, source originals, credentials, origin URIs, absolute workspace paths, excluded-page names, or excluded-page content into the site.
- Remember that classification labels are metadata, not access control. Keep trust zones in separate workspaces when technical isolation is required.

## Protect the target

- Require a workspace-relative target below the configured `outputs` directory. Reject absolute paths, parent traversal, symlinks, and the outputs root itself.
- Generate into a same-filesystem staging directory, then replace the target only after all files and hashes are complete.
- Recheck page, source-metadata, and configuration hashes before committing the staged site. Retry when the knowledge snapshot changed during rendering.
- Replace an existing site automatically only when its `export-report.json` proves it is an unchanged llm-wiki generated bundle.
- Use `--force` only after the user explicitly authorizes takeover of an unmanaged or modified target. Preserve the prior target under `.wiki/transactions/` and report the backup path.
- Treat the generated site as disposable. Never modify authoritative pages, raw evidence, human-owned notes, or editor settings during export.

## Inspect the result

Open `<target>/index.html` directly or serve the target directory with a static file server. Confirm that:

- `export-report.json` reports the expected classifications and page counts;
- `report_sha256` and the recorded generated-file hashes still verify before replacement or publication;
- the effective theme, add-ons, validated options, and `profile_sha256` match the request;
- excluded content is absent from HTML, search indexes, graph data, and the report;
- unresolved links are visible in `link_findings` and render as unavailable text;
- the site contains no external scripts, stylesheets, remote images, or executable source content.

Generating the site is not publication. Deploy or transmit it only when the user separately names the destination and authorizes that external state change.
