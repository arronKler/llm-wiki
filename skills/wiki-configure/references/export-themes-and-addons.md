# Export Themes and Add-ons

Use this reference after [export-and-publishing.md](export-and-publishing.md) when the user wants to change a static site's appearance or enable optional site features. Keep presentation choices separate from classification and publication authorization.

## Contents

- Discover available capabilities
- Select a theme
- Compose add-ons
- Apply Workspace defaults
- Preserve security and portability
- Inspect the effective profile

## Discover available capabilities

Do not guess which extensions or options are installed. Inspect the current Skill bundle and Workspace defaults:

```text
python3 <wiki.py> --workspace <workspace-root> --json export-capabilities --format site
```

Use the returned IDs, descriptions, option schemas, dependencies, conflicts, and Workspace defaults. The effective precedence is:

```text
built-in defaults < .wiki/config.json < command-line overrides
```

## Select a theme

A theme controls CSS, typography, color, density, and layout within the stable site DOM. It never changes page selection, classifications, evidence, links, or generated data.

Built-in themes:

- `default`: balanced knowledge-base layout and the compatibility default;
- `editorial`: prose-first reading with warm paper tones and local serif fonts;
- `minimal`: compact technical-documentation layout with restrained styling.

Select a theme and validated options:

```text
python3 <wiki.py> --workspace <workspace-root> export outputs/site --format site \
  --theme editorial \
  --theme-option density=compact \
  --theme-option content_width=narrow \
  --theme-option accent=#6b4eff
```

Supported theme options are `accent`, `density`, `content_width`, `font_scale`, and `color_scheme`. Use only values reported by `export-capabilities`. Do not edit generated CSS or accept arbitrary CSS, paths, URLs, remote fonts, or scripts as a theme.

## Compose add-ons

Add-ons enhance an already filtered site model. They cannot read raw evidence, excluded pages, Workspace paths, or source registries.

Built-in add-ons:

- `search`: local body search and keyboard navigation; enabled by default;
- `toc`: an in-page heading outline;
- `graph`: a deterministic interactive relationship graph plus accessible list;
- `code-copy`: copy buttons for fenced code blocks;
- `facets`: homepage filters for type, status, and domains; requires `search`.

Enable, disable, and configure add-ons with repeatable flags:

```text
python3 <wiki.py> --workspace <workspace-root> export outputs/site --format site \
  --addon toc \
  --addon graph \
  --addon code-copy \
  --addon-option toc.max_level=3 \
  --addon-option graph.max_nodes=300
```

Disable a default or configured add-on explicitly:

```text
python3 <wiki.py> --workspace <workspace-root> export outputs/site --format site \
  --no-addon search
```

Reject unknown IDs or options, invalid types, dependency cycles, missing dependencies, and conflicting enable/disable requests before writing the target. Add-on options imply that add-on is enabled unless the same command explicitly disables it.

## Apply Workspace defaults

Use command-line options for one export. Modify `.wiki/config.json` only when the user explicitly asks to make appearance or features the Workspace default:

```json
{
  "exports": {
    "site": {
      "theme": "editorial",
      "theme_options": {
        "density": "comfortable",
        "content_width": "narrow"
      },
      "addons": {
        "search": {
          "enabled": true,
          "options": {
            "max_results": 12
          }
        },
        "toc": {
          "enabled": true,
          "options": {
            "min_level": 2,
            "max_level": 4
          }
        },
        "graph": {
          "enabled": false
        }
      }
    }
  }
}
```

Do not persist additional classifications inside an appearance profile. Classification flags remain an explicit disclosure decision for each export.

## Preserve security and portability

- Load themes and add-ons only from the installed `wiki-configure/assets/static-site/` bundle.
- Never accept an extension path, URL, npm package, Workspace JavaScript, arbitrary HTML, or remote asset.
- Keep the exporter CSP fixed with `connect-src 'none'` and no remote assets. Bundled add-ons are trusted code shipped and reviewed with the Skill; the loader's static checks reject common network and dynamic-code APIs as defense in depth, not as a sandbox for third-party code.
- Keep `file://` support. Emit data as local JavaScript globals when browser fetch restrictions would block JSON.
- Provide add-ons only the post-classification site model. Never include excluded content in HTML, search, facets, graph data, options, reports, or assets.
- Treat Sources, metadata, and Referenced by as evidence-traceability core, not optional appearance features.

## Inspect the effective profile

After export, inspect the CLI payload and `export-report.json`. Confirm:

- the selected theme ID and validated effective options;
- the ordered add-on list, resolved dependencies, and effective options;
- `profile_sha256` plus theme, manifest, and asset hashes;
- the expected generated files such as `addon-options.js` or `graph-data.js`;
- unchanged disclosure counts and no excluded content.

Generating or styling a site remains separate from publishing it. Return to [export-and-publishing.md](export-and-publishing.md) before any external deployment.
