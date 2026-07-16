from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"
CLI_SOURCE = SKILLS_ROOT / "wiki-configure" / "scripts" / "wiki.py"
SUITE_NAMES = ("wiki-configure", "wiki-ingest", "wiki-maintain", "wiki-query")
HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def load_wiki_module():
    spec = importlib.util.spec_from_file_location("llm_wiki_cli", CLI_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {CLI_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


WIKI = load_wiki_module()


class RepositoryLayoutTests(unittest.TestCase):
    def test_repository_origin_binding_is_resource_aware(self) -> None:
        identity = "https://github.com/example/project"
        revision = "a" * 40
        repository_path = "src/main.py"
        for origin in (
            f"{identity}/blob/{revision}/{repository_path}",
            f"{identity}/-/blob/{revision}/{repository_path}",
            f"{identity}/src/commit/{revision}/{repository_path}",
            f"{identity}/+/{revision}/{repository_path}",
            f"{identity}@{revision}:{repository_path}",
        ):
            with self.subTest(origin=origin):
                self.assertTrue(
                    WIKI.repository_origin_binds(
                        origin,
                        identity,
                        revision,
                        repository_path=repository_path,
                    )
                )
        azure_identity = "https://dev.azure.com/example/project/_git/project"
        self.assertTrue(
            WIKI.repository_origin_binds(
                f"{azure_identity}?path=%2Fsrc%2Fmain.py&version=GC{revision}",
                azure_identity,
                revision,
                repository_path=repository_path,
            )
        )
        for origin in (
            f"{identity}/issues/{revision}/{repository_path}",
            f"{identity}/issues/123?unrelated={revision}",
        ):
            with self.subTest(origin=origin):
                self.assertFalse(
                    WIKI.repository_origin_binds(
                        origin,
                        identity,
                        revision,
                        repository_path=repository_path,
                    )
                )
        for origin in (
            f"{identity}/commit/{revision}",
            f"{identity}/+/{revision}",
            f"{identity}@{revision}",
        ):
            self.assertTrue(WIKI.repository_origin_binds(origin, identity, revision))
        self.assertFalse(
            WIKI.repository_origin_binds(
                f"{identity}/issues/{revision}", identity, revision
            )
        )

    def test_markdown_visibility_distinguishes_navigation_from_code(self) -> None:
        self.assertEqual(
            WIKI.extract_links("- Navigation\n    - [[module]]\n"),
            ("module",),
        )
        self.assertEqual(WIKI.extract_links("> [[module]]\n"), ("module",))
        self.assertEqual(
            WIKI.extract_links("- Navigation\n      [[module]]\n"),
            ("module",),
        )
        for hidden in (
            "- Navigation\n\n      [[module]]\n",
            "-     [[module]]\n",
            "-   \n      [[module]]\n",
            "1.   \n       [[module]]\n",
            ">     [[module]]\n",
            "<pre>\n[[module]]\n",
            "- Navigation\n  ```markdown\n  [[module]]\n  ```\n",
        ):
            with self.subTest(hidden=hidden):
                self.assertEqual(WIKI.extract_links(hidden), ())

    def test_all_skills_are_valid_and_self_contained(self) -> None:
        for name in SUITE_NAMES:
            skill_dir = SKILLS_ROOT / name
            skill_file = skill_dir / "SKILL.md"
            self.assertTrue(skill_file.is_file(), name)
            metadata = WIKI.read_skill_frontmatter(skill_file)
            self.assertEqual(metadata.get("name"), name)
            self.assertTrue(metadata.get("description"))
            self.assertEqual(set(metadata), {"name", "description"})
            self.assertTrue((skill_dir / "agents" / "openai.yaml").is_file())
            self.assertLess(len(skill_file.read_text(encoding="utf-8").splitlines()), 500)

    def test_local_markdown_links_resolve(self) -> None:
        link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for markdown in SKILLS_ROOT.rglob("*.md"):
            for target in link_re.findall(markdown.read_text(encoding="utf-8")):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                path = (markdown.parent / target.split("#", 1)[0]).resolve()
                self.assertTrue(path.exists(), f"Broken local link in {markdown}: {target}")

    def test_canonical_instructions_are_english_with_chinese_triggers(self) -> None:
        for name in SUITE_NAMES:
            skill_file = SKILLS_ROOT / name / "SKILL.md"
            metadata, body = WIKI.parse_frontmatter(skill_file.read_text(encoding="utf-8"))
            description = str(metadata["description"])
            self.assertIn("Chinese triggers", description, name)
            self.assertRegex(description, HAN_RE, name)
            self.assertNotRegex(body, HAN_RE, name)

        text_suffixes = {".md", ".base", ".yaml", ".yml", ".json", ".txt"}
        for directory in ("references", "assets"):
            for path in SKILLS_ROOT.glob(f"*/{directory}/*"):
                if path.is_file() and path.suffix.lower() in text_suffixes:
                    self.assertNotRegex(path.read_text(encoding="utf-8"), HAN_RE, str(path))

    def test_web_provider_fallbacks_are_routed_and_evidence_preserving(self) -> None:
        skill_file = SKILLS_ROOT / "wiki-ingest" / "SKILL.md"
        reference = (
            SKILLS_ROOT
            / "wiki-ingest"
            / "references"
            / "web-provider-fallbacks.md"
        )
        _, body = WIKI.parse_frontmatter(skill_file.read_text(encoding="utf-8"))

        self.assertTrue(reference.is_file())
        self.assertIn("references/web-provider-fallbacks.md", body)
        self.assertIn("after ordinary acquisition fails", body)

        contract = reference.read_text(encoding="utf-8")
        for section in (
            "## Apply a recipe consistently",
            "## X or Twitter public post through FxTwitter",
            "### Acquire one bounded representation",
            "### Validate before capture",
            "### Preserve provenance and authority",
            "## Add another provider recipe",
        ):
            self.assertIn(section, contract)
        for invariant in (
            "https://api.fxtwitter.com/2/status/<id>",
            "status.id",
            "status.type: tombstone",
            "retrieved_via",
            "third-party mirror",
            "Do not expand into its thread",
            "Never forward cookies",
            "Do not use an FxTwitter URL as the canonical origin",
            "provider object ID and lookup time are themselves disclosures",
            "A differing handle alone may reflect an account rename",
            "mark it out of scope",
        ):
            self.assertIn(invariant, contract)

    def test_repository_ingestion_is_routed_as_an_on_demand_reference(self) -> None:
        skill_file = SKILLS_ROOT / "wiki-ingest" / "SKILL.md"
        reference = SKILLS_ROOT / "wiki-ingest" / "references" / "repository-ingestion.md"
        functional_reference = (
            SKILLS_ROOT
            / "wiki-ingest"
            / "references"
            / "repository-functional-analysis.md"
        )
        metadata, body = WIKI.parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        description = str(metadata["description"])

        for trigger in (
            "Git repositories",
            "repository URL",
            "local repository directory",
            "GitHub",
            "GitLab",
            "project wiki",
            "comprehensive repository wiki",
            "without opening the code",
        ):
            self.assertIn(trigger, description)
        self.assertIn("为代码仓库创建全量 Wiki", description)
        self.assertNotIn("analyze a GitHub", description)
        self.assertNotIn("整理代码库", description)
        self.assertIn("read-only code analysis", description)
        self.assertIn("references/repository-ingestion.md", body)
        self.assertIn("one-time repository ingest", body)
        self.assertIn("Comprehensive repository wiki mode", body)
        self.assertIn("references/repository-functional-analysis.md", body)
        self.assertIn("repository-coverage <coverage-json>", body)
        self.assertTrue(reference.is_file())
        self.assertTrue(functional_reference.is_file())

        contract = reference.read_text(encoding="utf-8")
        for section in (
            "## Resolve immutable identity",
            "## Route comprehensive functional analysis",
            "## Acquire evidence read-only",
            "## Choose an evidence representation",
            "## Map evidence into capture",
            "## Inventory tracked content",
            "## Apply coverage lenses",
            "## Respect authority boundaries",
            "## Cite commit, path, and line",
            "## Integrate with mixed sources",
            "## Process version updates",
            "## Stop or accept",
        ):
            self.assertIn(section, contract)
        for invariant in ("full commit SHA", "pointer-only", "working-tree overlay", "supersedes"):
            self.assertIn(invariant, contract)
        for comprehensive_contract in (
            "| Comprehensive repository wiki |",
            "without reading source code",
            "one page per file",
            "capture an immutable manifest",
        ):
            self.assertIn(comprehensive_contract, contract)
        self.assertIn("repository URL or local directory", contract)
        self.assertIn("without narrowing the request", contract)
        self.assertIn("Use a narrower mode for read-only explanation", contract)
        for capture_flag in ("--origin", "--source-type", "--adapter", "--external-key"):
            self.assertIn(capture_flag, contract)
        self.assertIn("Avoid blind whole-directory capture", contract)
        self.assertRegex(contract, r"Do not (?:run|execute)")
        manifest_example_path = (
            SKILLS_ROOT
            / "wiki-ingest"
            / "assets"
            / "repository-manifest.example.json"
        )
        self.assertIn("../assets/repository-manifest.example.json", contract)
        manifest_example = json.loads(manifest_example_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest_example["kind"], "llm-wiki.repository-manifest")
        self.assertEqual(
            manifest_example["tracked_file_count"],
            len(manifest_example["tracked_files"]),
        )
        self.assertEqual(
            set(manifest_example["exclusions"][0]),
            {"path", "reason", "blocking"},
        )
        self.assertEqual(
            set(manifest_example["limitations"][0]),
            {"id", "kind", "reason", "blocking"},
        )

        functional_contract = functional_reference.read_text(encoding="utf-8")
        for section in (
            "## Establish the module registry",
            "## Reconcile discovery surfaces",
            "## Assign analysis depth and verification",
            "## Meet the evidence gate",
            "## Write the module dossier",
            "## Trace behavior end to end",
            "## Roll up coverage",
            "## Maintain the machine-readable contract",
            "## Validate and report completion",
        ):
            self.assertIn(section, functional_contract)
        for invariant in (
            "schema_version: 1",
            "discovery_gaps",
            "behavioral",
            "reachability",
            "implementation",
            "boundary",
            "comprehensive-complete",
            "semantic_checks_performed: false",
        ):
            self.assertIn(invariant, functional_contract)
        self.assertIn("Schema version 1 requires one JSON file", functional_contract)
        self.assertIn("pointer-only `repository`", functional_contract)

        example_path = (
            SKILLS_ROOT
            / "wiki-ingest"
            / "assets"
            / "repository-coverage.example.json"
        )
        self.assertIn("../assets/repository-coverage.example.json", functional_contract)
        example = json.loads(example_path.read_text(encoding="utf-8"))
        self.assertEqual(example["kind"], "llm-wiki.repository-coverage")
        self.assertEqual(example["schema_version"], 1)
        self.assertEqual(
            {lens["id"] for lens in example["repository_lenses"]},
            set(WIKI.REPOSITORY_LENS_IDS),
        )
        material = next(
            module for module in example["modules"] if module["materiality"] == "material"
        )
        self.assertEqual(set(material["dossier"]), set(WIKI.REPOSITORY_DOSSIER_FACETS))
        self.assertEqual(
            {step["stage"] for step in example["flows"][0]["steps"]},
            set(WIKI.REPOSITORY_FLOW_STAGES),
        )

    def test_specialized_ingestion_references_are_routed_on_demand(self) -> None:
        skill_file = SKILLS_ROOT / "wiki-ingest" / "SKILL.md"
        references = skill_file.parent / "references"
        metadata, body = WIKI.parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        description = str(metadata["description"])
        source_handling = (references / "source-handling.md").read_text(encoding="utf-8")

        for trigger in ("online documents", "meetings", "tickets", "spreadsheets", "dashboards"):
            self.assertIn(trigger, description)
        self.assertIn("data analysis without persistent capture", description)

        specifications = {
            "web-and-online-document-ingestion.md": (
                (
                    "## Resolve canonical identity",
                    "## Acquire evidence safely",
                    "## Choose an evidence representation",
                    "## Map evidence into capture",
                    "## Bound traversal and dependencies",
                    "## Cite the captured state",
                    "## Process updates and disappearance",
                    "## Stop or accept",
                ),
                ("canonical URI", "pointer-only", "loopback", "cross-origin", "--supersedes"),
            ),
            "meetings-messages-and-email.md": (
                (
                    "## Define the conversation boundary",
                    "## Preserve object identity and time",
                    "## Choose snapshot or incremental evidence",
                    "## Preserve edits, deletions, and visibility",
                    "## Map collaboration evidence into capture",
                    "## Distinguish statements, proposals, decisions, and actions",
                    "## Cite stable event locators",
                    "## Stop or accept",
                ),
                ("stable object ID", "--supersedes", "deletion", "no collaboration state changed"),
            ),
            "structured-data-ingestion.md": (
                (
                    "## Freeze query identity",
                    "## Establish schema and completeness",
                    "## Inspect spreadsheets",
                    "## Acquire APIs with pagination",
                    "## Resolve dashboard filters",
                    "## Map evidence into capture",
                    "## Define metric semantics",
                    "## Create reproducible citations",
                    "## Stop or accept",
                ),
                ("result hash", "pagination", "hidden filters", "GraphQL mutations", "read-only", "--supersedes"),
            ),
        }

        for filename, (sections, invariants) in specifications.items():
            self.assertIn(f"references/{filename}", body)
            self.assertIn(f"]({filename})", source_handling)
            reference = references / filename
            self.assertTrue(reference.is_file())
            contract = reference.read_text(encoding="utf-8")
            self.assertIn("## Contents", contract)
            self.assertLess(len(contract.splitlines()), 300)
            self.assertIn("[source-handling.md](source-handling.md)", contract)
            self.assertIn("[integration-contract.md](integration-contract.md)", contract)
            for section in sections:
                self.assertIn(section, contract)
            for invariant in invariants:
                self.assertIn(invariant, contract)
            for capture_flag in ("--origin", "--source-type", "--adapter", "--external-key"):
                self.assertIn(capture_flag, contract)

    def test_static_site_export_is_routed_as_an_on_demand_reference(self) -> None:
        skill_file = SKILLS_ROOT / "wiki-configure" / "SKILL.md"
        reference = skill_file.parent / "references" / "export-and-publishing.md"
        extension_reference = skill_file.parent / "references" / "export-themes-and-addons.md"
        metadata, body = WIKI.parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        description = str(metadata["description"])

        for trigger in ("export", "static-site", "导出 Wiki", "生成静态站点"):
            self.assertIn(trigger, description)
        self.assertIn("references/export-and-publishing.md", body)
        self.assertTrue(reference.is_file())
        self.assertTrue(extension_reference.is_file())
        contract = reference.read_text(encoding="utf-8")
        for section in (
            "## Select an export profile",
            "## Enforce the disclosure boundary",
            "## Protect the target",
            "## Inspect the result",
        ):
            self.assertIn(section, contract)
        for invariant in (
            "public",
            "export-report.json",
            "raw/sources/",
            "Generating the site is not publication",
        ):
            self.assertIn(invariant, contract)
        static_assets = skill_file.parent / "assets" / "static-site"
        self.assertTrue((static_assets / "core.css").is_file())
        for theme in ("default", "editorial", "minimal"):
            manifest = json.loads(
                (static_assets / "themes" / theme / "theme.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["id"], theme)
            self.assertTrue((static_assets / "themes" / theme / "theme.css").is_file())
        for addon in ("search", "toc", "graph", "code-copy", "facets"):
            manifest = json.loads(
                (static_assets / "addons" / addon / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["id"], addon)

    def test_release_contains_no_machine_specific_paths(self) -> None:
        forbidden = ("/Users/", "\\Users\\", "/home/")
        for path in SKILLS_ROOT.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for marker in forbidden:
                self.assertNotIn(marker, text, f"Private path marker in {path}")


class WikiCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.vault = self.base / "vault"
        self.vault.mkdir()
        (self.vault / ".obsidian").mkdir()
        canonical = self.vault / ".agents" / "skills"
        canonical.mkdir(parents=True)
        for name in SUITE_NAMES:
            shutil.copytree(SKILLS_ROOT / name, canonical / name)
        self.cli = canonical / "wiki-configure" / "scripts" / "wiki.py"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(self.cli), "--vault", str(self.vault), *args],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def init(self) -> dict:
        result = self.run_cli("--json", "init")
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        return json.loads(result.stdout)

    def write_config(self, config: dict) -> None:
        config_dir = self.vault / ".wiki"
        config_dir.mkdir(exist_ok=True)
        (config_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")

    def write_page(
        self,
        relative: str,
        *,
        title: str,
        body: str,
        classification: str = "public",
        sources: list[str] | None = None,
        aliases: list[str] | None = None,
        page_type: str = "concept",
        status: str | None = None,
        domains: list[str] | None = None,
    ) -> Path:
        path = self.vault / "wiki" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        frontmatter = [
            "---",
            f"title: {json.dumps(title, ensure_ascii=False)}",
            f"aliases: {json.dumps(aliases or [], ensure_ascii=False)}",
            f"type: {page_type}",
            f"classification: {classification}",
            "created: 2026-07-15",
            "updated: 2026-07-15",
            f"sources: {json.dumps(sources or [], ensure_ascii=False)}",
            f"domains: {json.dumps(domains or [], ensure_ascii=False)}",
            "---",
            "",
        ]
        if status:
            frontmatter.insert(-2, f"status: {status}")
        path.write_text("\n".join(frontmatter) + body.rstrip() + "\n", encoding="utf-8")
        return path

    def write_repository_coverage_fixture(self) -> tuple[Path, dict]:
        self.init()
        identity = "https://github.com/example/project"
        revision = "a" * 40
        main_source_bytes = b"def main():\n    return 'ok'\n"
        main_blob_id = hashlib.sha1(
            f"blob {len(main_source_bytes)}\0".encode() + main_source_bytes
        ).hexdigest()
        manifest = self.run_cli(
            "--json",
            "capture",
            "--stdin",
            "--name",
            "repository-manifest.json",
            "--title",
            "example/project repository manifest",
            "--source-type",
            "repository-manifest",
            "--adapter",
            "git",
            "--origin",
            f"{identity}/commit/{revision}",
            "--external-key",
            f"{identity}@{revision}:manifest",
            "--authority",
            "agent-provenance",
            "--classification",
            "public",
            input_bytes=json.dumps(
                {
                    "kind": "llm-wiki.repository-manifest",
                    "schema_version": 1,
                    "repository": {
                        "identity": identity,
                        "revision": revision,
                        "vcs": "git",
                    },
                    "ref_context": "refs/heads/main",
                    "acquired_at": "2026-07-15T00:00:00Z",
                    "scope": "Committed tree at the pinned revision",
                    "working_tree": {
                        "clean": True,
                        "overlay_included": False,
                    },
                    "tracked_file_count": 4,
                    "tracked_files": [
                        {
                            "path": path,
                            "mode": "100644",
                            "object_id": (
                                main_blob_id
                                if path == "src/main.py"
                                else str(index + 1) * 40
                            ),
                            "size": 10,
                        }
                        for index, path in enumerate(
                            (
                                "src/main.py",
                                "src/helper.py",
                                "tests/test_main.py",
                                "vendor/library.js",
                            )
                        )
                    ],
                    "exclusions": [],
                    "submodules": [],
                    "lfs": [],
                    "limitations": [],
                }
            ).encode(),
        )
        self.assertEqual(manifest.returncode, 0, manifest.stderr.decode())
        manifest_source_id = json.loads(manifest.stdout)["sources"][0]["source_id"]
        code_source = self.run_cli(
            "--json",
            "capture",
            "--stdin",
            "--name",
            "main.py",
            "--title",
            "example/project source evidence",
            "--source-type",
            "code",
            "--adapter",
            "git",
            "--origin",
            f"{identity}/blob/{revision}/src/main.py",
            "--external-key",
            f"{identity}@{revision}:src/main.py",
            "--classification",
            "public",
            input_bytes=main_source_bytes,
        )
        self.assertEqual(code_source.returncode, 0, code_source.stderr.decode())
        source_id = json.loads(code_source.stdout)["sources"][0]["source_id"]
        repository_source = self.run_cli(
            "--json",
            "capture",
            f"{identity}/commit/{revision}",
            "--pointer-only",
            "--title",
            "example/project repository evidence",
            "--source-type",
            "repository",
            "--adapter",
            "git",
            "--external-key",
            f"{identity}@{revision}",
            "--classification",
            "public",
        )
        self.assertEqual(
            repository_source.returncode, 0, repository_source.stderr.decode()
        )
        repository_source_id = json.loads(repository_source.stdout)["sources"][0][
            "source_id"
        ]

        lens_headings = "\n\n".join(
            f"## {lens_id}\n\nCovered." for lens_id in WIKI.REPOSITORY_LENS_IDS
        )
        self.write_page(
            "repository.md",
            title="Repository",
            sources=[source_id],
            body=f"# Repository\n\n[[module]]\n\n{lens_headings}\n",
        )
        dossier_headings = "\n\n".join(
            f"## {facet}\n\nDocumented." for facet in WIKI.REPOSITORY_DOSSIER_FACETS
        )
        self.write_page(
            "module.md",
            title="Module Capability",
            sources=[source_id, repository_source_id],
            body=f"# Module Capability\n\n[[repository]]\n\n{dossier_headings}\n\n## flow-main\n\nEnd-to-end behavior.\n\n## supporting-helper\n\nHelper contract.\n",
        )

        def evidence(
            evidence_class: str,
            locator: str,
            evidence_source_id: str | None = None,
        ) -> dict:
            return {
                "class": evidence_class,
                "source_id": evidence_source_id or source_id,
                "locator": f"repository@{revision}:{locator}",
            }

        coverage = {
            "kind": "llm-wiki.repository-coverage",
            "schema_version": 1,
            "repository": {"identity": identity, "revision": revision},
            "manifest_source_id": manifest_source_id,
            "home_page": "wiki/repository.md",
            "batch_state": "comprehensive-complete",
            "discovery_gaps": [],
            "repository_lenses": [
                {
                    "id": lens_id,
                    "status": "covered",
                    "page": "wiki/repository.md",
                    "anchor": lens_id,
                    "evidence": [evidence("boundary", f"src/main.py#{lens_id}")],
                    "blocking": False,
                }
                for lens_id in WIKI.REPOSITORY_LENS_IDS
            ],
            "discovery_records": [
                {
                    "id": "route-main",
                    "kind": "runtime-entrypoint",
                    "locator": f"repository@{revision}:src/main.py#main",
                    "module_id": "module-main",
                },
                {
                    "id": "helper-main",
                    "kind": "supporting-contract",
                    "locator": f"repository@{revision}:src/helper.py#helper",
                    "module_id": "module-helper",
                },
                {
                    "id": "vendor-fixture",
                    "kind": "vendored-cohort",
                    "locator": f"repository@{revision}:vendor/library.js",
                    "module_id": "module-vendor",
                },
            ],
            "inventory_groups": [
                {
                    "id": "source-tree",
                    "paths": ["src"],
                    "module_ids": ["module-main", "module-helper"],
                },
                {
                    "id": "vendor-tree",
                    "paths": ["vendor"],
                    "module_ids": ["module-vendor"],
                },
                {
                    "id": "verification-tree",
                    "paths": ["tests"],
                    "module_ids": ["module-main"],
                }
            ],
            "modules": [
                {
                    "id": "module-main",
                    "title": "Module Capability",
                    "materiality": "material",
                    "materiality_reason": "Owns a reachable runtime capability and behavior.",
                    "parent_id": None,
                    "paths": ["src/main.py"],
                    "page": "wiki/module.md",
                    "anchor": "Module Capability",
                    "analysis_depth": "behavioral",
                    "verification": {"status": "test-supported"},
                    "dossier": {
                        facet: {
                            "status": "documented",
                            "locator": f"wiki/module.md#{facet}",
                        }
                        for facet in WIKI.REPOSITORY_DOSSIER_FACETS
                    },
                    "evidence": [
                        evidence("reachability", "src/main.py#main"),
                        evidence("implementation", "src/main.py#run"),
                        evidence("boundary", "src/main.py#output"),
                        evidence(
                            "verification",
                            "tests/test_main.py#test_run",
                            repository_source_id,
                        ),
                    ],
                    "flow_ids": ["flow-main"],
                    "gaps": [],
                },
                {
                    "id": "module-helper",
                    "title": "Supporting Helper",
                    "materiality": "supporting",
                    "materiality_reason": "Provides a stable helper contract for the material owner.",
                    "parent_id": "module-main",
                    "owner_module_id": "module-main",
                    "paths": ["src/helper.py"],
                    "page": "wiki/module.md",
                    "anchor": "supporting-helper",
                    "analysis_depth": "surface",
                    "verification": {
                        "status": "not-applicable",
                        "reason": "The helper has no independent verification contract.",
                    },
                    "dossier": {},
                    "evidence": [
                        evidence("reachability", "src/main.py#helper-call"),
                        evidence(
                            "boundary", "src/helper.py#helper", repository_source_id
                        ),
                    ],
                    "flow_ids": [],
                    "gaps": [],
                    "disposition": {
                        "reason": "Covered through its owning material capability.",
                        "evidence": {
                            "source_id": repository_source_id,
                            "locator": f"repository@{revision}:src/helper.py#helper",
                        },
                    },
                },
                {
                    "id": "module-vendor",
                    "title": "Vendored fixture cohort",
                    "materiality": "excluded",
                    "materiality_reason": "Vendored output has no owned runtime responsibility.",
                    "parent_id": None,
                    "paths": ["vendor/library.js"],
                    "analysis_depth": "inventory",
                    "verification": {
                        "status": "not-applicable",
                        "reason": "Excluded vendored output is not independently verified.",
                    },
                    "dossier": {},
                    "evidence": [],
                    "flow_ids": [],
                    "gaps": [],
                    "disposition": {
                        "reason": "Excluded as auditable vendored output.",
                        "evidence": {
                            "source_id": repository_source_id,
                            "locator": f"repository@{revision}:vendor/library.js#vendored-cohort",
                        },
                    },
                },
            ],
            "flows": [
                {
                    "id": "flow-main",
                    "module_ids": ["module-main"],
                    "page": "wiki/module.md",
                    "anchor": "flow-main",
                    "steps": [
                        {
                            "stage": stage,
                            "description": f"Trace the {stage} portion of the behavior.",
                            "module_ids": ["module-main"],
                            "evidence": [
                                evidence("implementation", f"src/main.py#{stage}")
                            ],
                        }
                        for stage in WIKI.REPOSITORY_FLOW_STAGES
                    ],
                }
            ],
        }
        relative = Path("raw/derived/repository-coverage/example") / f"{revision}.json"
        path = self.vault / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(coverage), encoding="utf-8")
        return relative, coverage

    def rewrite_repository_coverage(self, relative: Path, coverage: dict) -> None:
        (self.vault / relative).write_text(json.dumps(coverage), encoding="utf-8")

    def source_metadata_path(self, source_id: str) -> Path:
        return next(
            path
            for path in (self.vault / "raw" / "sources").glob("*/*/source.json")
            if json.loads(path.read_text(encoding="utf-8"))["id"] == source_id
        )

    def test_repository_coverage_accepts_complete_registry(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()

        result = self.run_cli("--json", "repository-coverage", str(relative))

        self.assertEqual(result.returncode, 0, result.stderr.decode())
        payload = json.loads(result.stdout)
        self.assertTrue(payload["computed_complete"])
        self.assertFalse(payload["semantic_checks_performed"])
        self.assertEqual(payload["summary"]["repository_lenses"], 10)
        self.assertEqual(payload["summary"]["structural_errors"], 0)
        self.assertEqual(payload["summary"]["completion_findings"], 0)
        self.assertEqual(payload["summary"]["completion"], "complete")

        coverage["repository_lenses"][0].update(
            {
                "status": "not-applicable",
                "reason": "This lens does not apply to the repository kind.",
                "evidence": [],
            }
        )
        self.rewrite_repository_coverage(relative, coverage)
        not_applicable = self.run_cli(
            "--json", "repository-coverage", str(relative)
        )
        self.assertEqual(not_applicable.returncode, 0, not_applicable.stderr.decode())
        self.assertTrue(json.loads(not_applicable.stdout)["computed_complete"])

    def test_repository_coverage_reports_shallow_partial_registry(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "functional-analysis-partial"
        coverage["modules"][0]["analysis_depth"] = "surface"
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli("--json", "repository-coverage", str(relative))

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        payload = json.loads(result.stdout)
        self.assertFalse(payload["computed_complete"])
        self.assertEqual(payload["summary"]["surface_only"], 1)
        self.assertEqual(payload["summary"]["structural_errors"], 0)
        self.assertGreater(payload["summary"]["completion_findings"], 0)

    def test_repository_coverage_rejects_one_step_flow_as_complete(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "functional-analysis-partial"
        coverage["flows"][0]["steps"] = coverage["flows"][0]["steps"][:1]
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli("--json", "repository-coverage", str(relative))

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        payload = json.loads(result.stdout)
        self.assertIn(
            "incomplete-end-to-end-flow",
            {item["code"] for item in payload["completion_findings"]},
        )

    def test_repository_coverage_allow_partial_only_relaxes_completion(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "architecture-baseline"
        coverage["repository_lenses"][0].update(
            {"status": "partial", "reason": "History is still being reconciled."}
        )
        self.rewrite_repository_coverage(relative, coverage)

        allowed = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(allowed.returncode, 0, allowed.stderr.decode())
        payload = json.loads(allowed.stdout)
        self.assertEqual(payload["summary"]["structural_errors"], 0)
        self.assertGreater(payload["summary"]["completion_findings"], 0)

        saved_evidence = coverage["repository_lenses"][1]["evidence"]
        coverage["repository_lenses"][1]["evidence"] = []
        self.rewrite_repository_coverage(relative, coverage)
        uncovered_claim = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(uncovered_claim.returncode, 1, uncovered_claim.stderr.decode())
        self.assertIn(
            "covered-lens-without-evidence",
            {item["code"] for item in json.loads(uncovered_claim.stdout)["structural_errors"]},
        )
        coverage["repository_lenses"][1]["evidence"] = saved_evidence
        coverage["repository_lenses"].pop()
        self.rewrite_repository_coverage(relative, coverage)
        structural = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(structural.returncode, 1, structural.stderr.decode())
        structural_payload = json.loads(structural.stdout)
        self.assertIn(
            "missing-repository-lens",
            {item["code"] for item in structural_payload["structural_errors"]},
        )

    def test_repository_coverage_rejects_malformed_contract(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage.pop("kind")
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli("repository-coverage", str(relative), "--allow-partial")

        self.assertEqual(result.returncode, 2)
        self.assertIn(b"Unsupported repository coverage kind", result.stderr)

    def test_repository_coverage_rejects_mutable_git_revision(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        pinned_revision = "a" * 40
        coverage = json.loads(
            json.dumps(coverage).replace(pinned_revision, "main")
        )
        coverage["batch_state"] = "functional-analysis-partial"
        self.rewrite_repository_coverage(relative, coverage)
        metadata_path = self.source_metadata_path(coverage["manifest_source_id"])
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        original_path = self.vault / metadata["original_path"]
        manifest = json.loads(original_path.read_text(encoding="utf-8"))
        manifest["repository"]["revision"] = "main"
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(
            "mutable-git-revision",
            {item["code"] for item in json.loads(result.stdout)["structural_errors"]},
        )

    def test_repository_coverage_rejects_direct_supporting_disposition(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["discovery_records"][0].pop("module_id")
        coverage["discovery_records"][0].update(
            {"disposition": "supporting", "reason": "Must use a module row."}
        )
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli(
            "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn(b"disposition is unsupported", result.stderr)

    def test_repository_coverage_requires_material_verification_gap(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "functional-analysis-partial"
        coverage["modules"][0]["verification"] = {
            "status": "not-applicable",
            "reason": "Incorrectly hidden for this test.",
        }
        coverage["modules"][0]["evidence"] = [
            item
            for item in coverage["modules"][0]["evidence"]
            if item["class"] != "verification"
        ]
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(
            "material-verification-not-applicable",
            {item["code"] for item in json.loads(result.stdout)["structural_errors"]},
        )

    def test_repository_coverage_requires_module_owner_backlink(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        module_page = self.vault / "wiki" / "module.md"
        module_page.write_text(
            module_page.read_text(encoding="utf-8").replace(
                "[[repository]]", "<!-- [[repository]] -->"
            ),
            encoding="utf-8",
        )
        coverage["batch_state"] = "functional-analysis-partial"
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(
            "module-page-missing-owner-backlink",
            {item["code"] for item in json.loads(result.stdout)["structural_errors"]},
        )

    def test_repository_coverage_accepts_rendered_nested_list_link(self) -> None:
        relative, _ = self.write_repository_coverage_fixture()
        repository_page = self.vault / "wiki" / "repository.md"
        repository_page.write_text(
            repository_page.read_text(encoding="utf-8").replace(
                "[[module]]", "- Navigation\n    - [[module]]"
            ),
            encoding="utf-8",
        )

        result = self.run_cli("--json", "repository-coverage", str(relative))

        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertTrue(json.loads(result.stdout)["computed_complete"])

    def test_repository_coverage_requires_substantive_sections(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        repository_page = self.vault / "wiki" / "repository.md"
        repository_page.write_text(
            repository_page.read_text(encoding="utf-8").replace("Covered.", "&nbsp;"),
            encoding="utf-8",
        )
        module_page = self.vault / "wiki" / "module.md"
        module_page.write_text(
            module_page.read_text(encoding="utf-8")
            .replace("Documented.", "&#8203;")
            .replace("End-to-end behavior.", "&nbsp;"),
            encoding="utf-8",
        )
        coverage["batch_state"] = "functional-analysis-partial"
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        codes = {item["code"] for item in json.loads(result.stdout)["structural_errors"]}
        self.assertIn("repository-lens-section-empty", codes)
        self.assertIn("dossier-section-empty", codes)
        self.assertIn("flow-section-empty", codes)

    def test_repository_coverage_requires_lens_home_backlink(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        source_id = coverage["modules"][0]["evidence"][0]["source_id"]
        lens = coverage["repository_lenses"][0]
        self.write_page(
            "lens.md",
            title="Standalone Lens",
            sources=[source_id],
            body=f"# Standalone Lens\n\n## {lens['anchor']}\n\nCovered in detail.\n",
        )
        lens["page"] = "wiki/lens.md"
        repository_page = self.vault / "wiki" / "repository.md"
        repository_page.write_text(
            repository_page.read_text(encoding="utf-8") + "\n[[lens]]\n",
            encoding="utf-8",
        )
        coverage["batch_state"] = "functional-analysis-partial"
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(
            "repository-lens-page-missing-home-backlink",
            {item["code"] for item in json.loads(result.stdout)["structural_errors"]},
        )

    def test_repository_coverage_rejects_flow_heading_in_code_fence(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        module_page = self.vault / "wiki" / "module.md"
        module_page.write_text(
            module_page.read_text(encoding="utf-8").replace(
                "## flow-main\n\nEnd-to-end behavior.",
                "```markdown\n## flow-main\n```\n\nEnd-to-end behavior.",
            ),
            encoding="utf-8",
        )
        coverage["batch_state"] = "functional-analysis-partial"
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(
            "missing-flow-anchor",
            {item["code"] for item in json.loads(result.stdout)["structural_errors"]},
        )

    def test_repository_coverage_isolates_material_module_sections(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "functional-analysis-partial"
        second = copy.deepcopy(coverage["modules"][0])
        second.update({"id": "module-second", "title": "Second Capability"})
        coverage["modules"].append(second)
        coverage["discovery_records"].append(
            {
                "id": "route-second",
                "kind": "runtime-entrypoint",
                "locator": f"repository@{'a' * 40}:src/main.py#second",
                "module_id": "module-second",
            }
        )
        coverage["inventory_groups"][0]["module_ids"].append("module-second")
        coverage["flows"][0]["module_ids"].append("module-second")
        for step in coverage["flows"][0]["steps"]:
            step["module_ids"].append("module-second")
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        codes = {item["code"] for item in json.loads(result.stdout)["structural_errors"]}
        self.assertIn("duplicate-module-page-anchor", codes)
        self.assertIn("material-evidence-reused-across-modules", codes)

    def test_repository_coverage_rejects_dossier_owned_by_nested_module(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "functional-analysis-partial"
        revision = "a" * 40
        repository_source_id = coverage["modules"][0]["evidence"][3]["source_id"]
        nested_headings = {
            facet: f"Nested {facet}" for facet in WIKI.REPOSITORY_DOSSIER_FACETS
        }
        coverage["modules"][0]["dossier"] = {
            facet: {
                "status": "documented",
                "locator": f"wiki/module.md#{heading}",
            }
            for facet, heading in nested_headings.items()
        }
        coverage["modules"].append(
            {
                "id": "module-nested",
                "title": "Nested Capability",
                "materiality": "material",
                "materiality_reason": "Owns an independently reachable child behavior.",
                "parent_id": "module-main",
                "paths": ["src/helper.py"],
                "page": "wiki/module.md",
                "anchor": "Nested Capability",
                "analysis_depth": "behavioral",
                "verification": {
                    "status": "gap",
                    "reason": "No representative verification was found.",
                },
                "dossier": {
                    facet: {
                        "status": "documented",
                        "locator": f"wiki/module.md#{heading}",
                    }
                    for facet, heading in nested_headings.items()
                },
                "evidence": [
                    {
                        "class": evidence_class,
                        "source_id": repository_source_id,
                        "locator": f"repository@{revision}:src/helper.py#nested-{evidence_class}",
                    }
                    for evidence_class in ("reachability", "implementation", "boundary")
                ],
                "flow_ids": ["flow-main"],
                "gaps": [],
            }
        )
        coverage["discovery_records"].append(
            {
                "id": "route-nested",
                "kind": "runtime-entrypoint",
                "locator": f"repository@{revision}:src/helper.py#nested-entry",
                "module_id": "module-nested",
            }
        )
        coverage["inventory_groups"][0]["module_ids"].append("module-nested")
        coverage["flows"][0]["module_ids"].append("module-nested")
        for step in coverage["flows"][0]["steps"]:
            step["module_ids"].append("module-nested")
        module_page = self.vault / "wiki" / "module.md"
        nested_body = "\n\n".join(
            f"### {heading}\n\nDocumented." for heading in nested_headings.values()
        )
        module_page.write_text(
            module_page.read_text(encoding="utf-8")
            + f"\n## Nested Capability\n\n{nested_body}\n",
            encoding="utf-8",
        )
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(
            "dossier-owned-by-nested-module",
            {item["code"] for item in json.loads(result.stdout)["structural_errors"]},
        )

    def test_repository_coverage_binds_implementation_to_module_paths(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "functional-analysis-partial"
        coverage["modules"][0]["paths"] = ["src/helper.py"]
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(
            "module-evidence-path-mismatch",
            {item["code"] for item in json.loads(result.stdout)["structural_errors"]},
        )

    def test_repository_coverage_rejects_missing_and_out_of_bounds_evidence(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "functional-analysis-partial"
        coverage["modules"][0]["evidence"][0]["locator"] = (
            f"repository@{'a' * 40}:src/main.py#L999-L1000"
        )
        self.rewrite_repository_coverage(relative, coverage)

        out_of_bounds = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(out_of_bounds.returncode, 1, out_of_bounds.stderr.decode())
        self.assertIn(
            "evidence-line-locator-out-of-bounds",
            {
                item["code"]
                for item in json.loads(out_of_bounds.stdout)["structural_errors"]
            },
        )

        code_source_id = coverage["modules"][0]["evidence"][0]["source_id"]
        metadata = json.loads(
            self.source_metadata_path(code_source_id).read_text(encoding="utf-8")
        )
        (self.vault / metadata["original_path"]).unlink()
        missing = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(missing.returncode, 1, missing.stderr.decode())
        self.assertIn(
            "evidence-source-content-missing",
            {item["code"] for item in json.loads(missing.stdout)["structural_errors"]},
        )

    def test_repository_coverage_binds_selected_code_to_git_blob(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "functional-analysis-partial"
        self.rewrite_repository_coverage(relative, coverage)
        code_source_id = coverage["modules"][0]["evidence"][0]["source_id"]
        metadata_path = self.source_metadata_path(code_source_id)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        original_path = self.vault / metadata["original_path"]
        original_path.write_bytes(b"not the source at the pinned revision\n")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(
            "evidence-code-blob-mismatch",
            {item["code"] for item in json.loads(result.stdout)["structural_errors"]},
        )

    def test_repository_coverage_rejects_noncanonical_code_origin(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "functional-analysis-partial"
        self.rewrite_repository_coverage(relative, coverage)
        code_source_id = coverage["modules"][0]["evidence"][0]["source_id"]
        metadata_path = self.source_metadata_path(code_source_id)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["origin_uri"] = (
            "https://github.com/example/project/issues/123?unrelated=" + "a" * 40
        )
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(
            "evidence-source-origin-mismatch",
            {item["code"] for item in json.loads(result.stdout)["structural_errors"]},
        )

    def test_repository_coverage_requires_one_git_object_format(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        metadata_path = self.source_metadata_path(coverage["manifest_source_id"])
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        original_path = self.vault / metadata["original_path"]
        manifest = json.loads(original_path.read_text(encoding="utf-8"))
        manifest["tracked_files"][1]["object_id"] = "f" * 64
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(
            "manifest-object-id-invalid",
            {item["code"] for item in json.loads(result.stdout)["structural_errors"]},
        )

        manifest["tracked_files"][1]["object_id"] = "2" * 40
        manifest["tracked_files"][1]["mode"] = " 100644 "
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        invalid_mode = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(invalid_mode.returncode, 1, invalid_mode.stderr.decode())
        self.assertIn(
            "manifest-file-mode-invalid",
            {
                item["code"]
                for item in json.loads(invalid_mode.stdout)["structural_errors"]
            },
        )

    def test_repository_coverage_validates_materialized_lfs_evidence(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        metadata_path = self.source_metadata_path(coverage["manifest_source_id"])
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        original_path = self.vault / metadata["original_path"]
        manifest = json.loads(original_path.read_text(encoding="utf-8"))
        code_source_id = coverage["modules"][0]["evidence"][0]["source_id"]
        code_metadata = json.loads(
            self.source_metadata_path(code_source_id).read_text(encoding="utf-8")
        )
        materialized_path = self.vault / code_metadata["original_path"]
        manifest["lfs"] = [
            {
                "path": "src/main.py",
                "object_id": "sha256:" + WIKI.sha256_file(materialized_path),
                "materialized": True,
                "blocking": False,
            }
        ]
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        valid = self.run_cli("--json", "repository-coverage", str(relative))
        self.assertEqual(valid.returncode, 0, valid.stderr.decode())

        manifest["lfs"][0]["object_id"] = "sha256:" + "f" * 64
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        mismatched = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(mismatched.returncode, 1, mismatched.stderr.decode())
        self.assertIn(
            "evidence-code-lfs-object-mismatch",
            {
                item["code"]
                for item in json.loads(mismatched.stdout)["structural_errors"]
            },
        )

        manifest["lfs"][0].update(
            {
                "object_id": "sha256:" + WIKI.sha256_file(materialized_path),
                "materialized": False,
                "reason": "Only the tracked LFS pointer is available.",
            }
        )
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        unmaterialized = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(unmaterialized.returncode, 1, unmaterialized.stderr.decode())
        self.assertIn(
            "unmaterialized-lfs-evidence-must-be-boundary",
            {
                item["code"]
                for item in json.loads(unmaterialized.stdout)["structural_errors"]
            },
        )

    def test_repository_coverage_preserves_manifest_path_identity(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        metadata_path = self.source_metadata_path(coverage["manifest_source_id"])
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        original_path = self.vault / metadata["original_path"]
        manifest = json.loads(original_path.read_text(encoding="utf-8"))
        manifest["tracked_files"][0]["path"] = "src/main.py "
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        spaced = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(spaced.returncode, 1, spaced.stderr.decode())
        self.assertIn(
            "manifest-tracked-file-path-invalid",
            {item["code"] for item in json.loads(spaced.stdout)["structural_errors"]},
        )

        manifest["tracked_files"][0]["path"] = "src/#main.py"
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        delimiter_path = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(delimiter_path.returncode, 1, delimiter_path.stderr.decode())
        self.assertIn(
            "manifest-tracked-file-path-invalid",
            {
                item["code"]
                for item in json.loads(delimiter_path.stdout)["structural_errors"]
            },
        )

        manifest["tracked_files"][0]["path"] = "src/main.py"
        manifest["tracked_files"].append(
            {
                "path": "src",
                "mode": "100644",
                "object_id": "f" * 40,
                "size": 1,
            }
        )
        manifest["tracked_file_count"] = len(manifest["tracked_files"])
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        collision = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(collision.returncode, 1, collision.stderr.decode())
        self.assertIn(
            "manifest-tracked-path-collision",
            {
                item["code"]
                for item in json.loads(collision.stdout)["structural_errors"]
            },
        )

    def test_repository_coverage_rejects_non_manifest_source_binding(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        manifest_id = coverage["manifest_source_id"]
        metadata_path = next(
            path
            for path in (self.vault / "raw" / "sources").glob("*/*/source.json")
            if json.loads(path.read_text(encoding="utf-8"))["id"] == manifest_id
        )
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata.update({"source_type": "web", "authority": "unknown"})
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        codes = {item["code"] for item in json.loads(result.stdout)["structural_errors"]}
        self.assertIn("manifest-source-type-mismatch", codes)
        self.assertIn("manifest-source-authority-mismatch", codes)

    def test_repository_coverage_reconciles_paths_with_manifest(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        manifest_id = coverage["manifest_source_id"]
        metadata_path = next(
            path
            for path in (self.vault / "raw" / "sources").glob("*/*/source.json")
            if json.loads(path.read_text(encoding="utf-8"))["id"] == manifest_id
        )
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        original_path = self.vault / metadata["original_path"]
        manifest = json.loads(original_path.read_text(encoding="utf-8"))
        manifest["tracked_files"] = [
            entry
            for entry in manifest["tracked_files"]
            if entry["path"] != "src/helper.py"
        ]
        manifest["tracked_file_count"] = len(manifest["tracked_files"])
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        codes = {item["code"] for item in json.loads(result.stdout)["structural_errors"]}
        self.assertIn("module-path-not-in-manifest", codes)
        self.assertIn("evidence-path-not-in-manifest", codes)

    def test_repository_coverage_validates_nonempty_manifest_collections(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "functional-analysis-partial"
        self.rewrite_repository_coverage(relative, coverage)
        metadata_path = self.source_metadata_path(coverage["manifest_source_id"])
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        original_path = self.vault / metadata["original_path"]
        manifest = json.loads(original_path.read_text(encoding="utf-8"))
        manifest.update(
            {
                "exclusions": [
                    {
                        "path": "tests",
                        "reason": "Tests are verification evidence, not runtime behavior.",
                        "blocking": False,
                    }
                ],
                "submodules": [
                    {
                        "path": "vendor/library.js",
                        "identity": "https://example.invalid/vendor/library",
                        "revision": "b" * 40,
                        "available": False,
                        "blocking": False,
                        "reason": "Represented as a parent gitlink boundary.",
                    }
                ],
                "lfs": [
                    {
                        "path": "src/helper.py",
                        "object_id": "sha256:" + "c" * 64,
                        "materialized": False,
                        "blocking": False,
                        "reason": "The pointer is sufficient for the surface contract.",
                    }
                ],
                "limitations": [
                    {
                        "id": "history-not-needed",
                        "kind": "history",
                        "reason": "No history claim is in scope.",
                        "blocking": True,
                    }
                ],
            }
        )
        next(
            entry
            for entry in manifest["tracked_files"]
            if entry["path"] == "vendor/library.js"
        ).update({"mode": "160000", "object_id": "b" * 40})
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        repository_source_id = coverage["modules"][0]["evidence"][3]["source_id"]
        coverage["modules"][2].update(
            {
                "title": "Vendored submodule boundary",
                "materiality": "boundary-only",
                "materiality_reason": "The gitlink is an independent repository boundary.",
                "page": "wiki/module.md",
                "anchor": "submodule-boundary",
                "analysis_depth": "surface",
                "evidence": [
                    {
                        "class": "boundary",
                        "source_id": repository_source_id,
                        "locator": f"repository@{'a' * 40}:vendor/library.js#gitlink",
                    }
                ],
            }
        )
        module_page = self.vault / "wiki" / "module.md"
        module_page.write_text(
            module_page.read_text(encoding="utf-8")
            + "\n## submodule-boundary\n\nIndependent repository boundary.\n",
            encoding="utf-8",
        )
        self.rewrite_repository_coverage(relative, coverage)

        valid_partial = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(valid_partial.returncode, 0, valid_partial.stderr.decode())
        payload = json.loads(valid_partial.stdout)
        self.assertEqual(payload["summary"]["structural_errors"], 0)
        self.assertEqual(payload["summary"]["blocked"], 1)
        self.assertIn(
            "blocking-manifest-limitation",
            {item["code"] for item in payload["completion_findings"]},
        )

        manifest["lfs"].append(
            {
                "path": "vendor/library.js",
                "object_id": "sha256:" + "d" * 64,
                "materialized": False,
                "blocking": False,
                "reason": "Invalid overlap used for contract validation.",
            }
        )
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        overlapping_lfs = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(overlapping_lfs.returncode, 1, overlapping_lfs.stderr.decode())
        overlap_codes = {
            item["code"]
            for item in json.loads(overlapping_lfs.stdout)["structural_errors"]
        }
        self.assertIn("manifest-lfs-mode-invalid", overlap_codes)
        self.assertIn("manifest-lfs-submodule-overlap", overlap_codes)
        manifest["lfs"].pop()
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        manifest["submodules"][0]["revision"] = "c" * 40
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        mismatched_gitlink = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(
            mismatched_gitlink.returncode, 1, mismatched_gitlink.stderr.decode()
        )
        self.assertIn(
            "manifest-submodule-revision-mismatch",
            {
                item["code"]
                for item in json.loads(mismatched_gitlink.stdout)["structural_errors"]
            },
        )

        manifest["submodules"][0]["revision"] = "b" * 40
        saved_submodules = manifest["submodules"]
        manifest["submodules"] = []
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        missing_submodule_census = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(
            missing_submodule_census.returncode,
            1,
            missing_submodule_census.stderr.decode(),
        )
        self.assertIn(
            "manifest-gitlink-submodule-missing",
            {
                item["code"]
                for item in json.loads(missing_submodule_census.stdout)[
                    "structural_errors"
                ]
            },
        )
        manifest["submodules"] = saved_submodules
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        original_main_path = coverage["modules"][0]["paths"]
        original_implementation = coverage["modules"][0]["evidence"][1]["locator"]
        coverage["modules"][0]["paths"] = ["vendor"]
        coverage["modules"][0]["evidence"][1]["locator"] = (
            f"repository@{'a' * 40}:vendor/library.js#ChildImplementation.execute"
        )
        coverage["inventory_groups"][1]["module_ids"].append("module-main")
        self.rewrite_repository_coverage(relative, coverage)
        escaped_submodule = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(escaped_submodule.returncode, 1, escaped_submodule.stderr.decode())
        escaped_codes = {
            item["code"]
            for item in json.loads(escaped_submodule.stdout)["structural_errors"]
        }
        self.assertIn("material-module-owns-submodule-path", escaped_codes)
        self.assertIn("submodule-evidence-must-be-boundary", escaped_codes)
        self.assertIn("submodule-inventory-not-boundary-only", escaped_codes)
        coverage["modules"][0]["paths"] = original_main_path
        coverage["modules"][0]["evidence"][1]["locator"] = original_implementation
        coverage["inventory_groups"][1]["module_ids"].remove("module-main")
        self.rewrite_repository_coverage(relative, coverage)

        coverage["modules"][2]["materiality"] = "excluded"
        self.rewrite_repository_coverage(relative, coverage)
        missing_boundary = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(missing_boundary.returncode, 1, missing_boundary.stderr.decode())
        self.assertIn(
            "submodule-boundary-module-missing",
            {
                item["code"]
                for item in json.loads(missing_boundary.stdout)["structural_errors"]
            },
        )
        coverage["modules"][2]["materiality"] = "boundary-only"
        self.rewrite_repository_coverage(relative, coverage)

        manifest["lfs"][0]["materialized"] = "no"
        original_path.write_text(json.dumps(manifest), encoding="utf-8")
        metadata["sha256"] = WIKI.sha256_file(original_path)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        invalid = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )
        self.assertEqual(invalid.returncode, 1, invalid.stderr.decode())
        self.assertIn(
            "manifest-collection-boolean-invalid",
            {item["code"] for item in json.loads(invalid.stdout)["structural_errors"]},
        )

    def test_repository_coverage_requires_inventory_for_every_manifest_file(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["inventory_groups"] = [
            group
            for group in coverage["inventory_groups"]
            if group["id"] != "verification-tree"
        ]
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(
            "manifest-file-not-in-inventory",
            {item["code"] for item in json.loads(result.stdout)["structural_errors"]},
        )

    def test_repository_coverage_rejects_conflicting_inventory_disposition(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "functional-analysis-partial"
        coverage["inventory_groups"].append(
            {
                "id": "incorrect-exclusion",
                "paths": ["src/main.py"],
                "disposition": "excluded",
                "reason": "Conflicts with the material module assignment.",
            }
        )
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(
            "conflicting-inventory-assignment",
            {item["code"] for item in json.loads(result.stdout)["structural_errors"]},
        )

    def test_repository_coverage_handles_deep_parent_graph_iteratively(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "functional-analysis-partial"
        coverage["modules"][0]["analysis_depth"] = "surface"
        template = coverage["modules"][2]
        previous_id = template["id"]
        for index in range(1100):
            module_id = f"deep-excluded-{index}"
            module = copy.deepcopy(template)
            module.update(
                {
                    "id": module_id,
                    "title": f"Deep excluded {index}",
                    "parent_id": previous_id,
                }
            )
            coverage["modules"].append(module)
            coverage["discovery_records"].append(
                {
                    "id": f"deep-discovery-{index}",
                    "kind": "excluded-cohort",
                    "locator": f"repository@{'a' * 40}:vendor/library.js#deep-{index}",
                    "module_id": module_id,
                }
            )
            previous_id = module_id
        coverage["modules"][0]["parent_id"] = previous_id
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(json.loads(result.stdout)["summary"]["structural_errors"], 0)

    def test_repository_coverage_treats_parent_rollup_as_partial_completion(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        revision = "a" * 40
        repository_source_id = coverage["modules"][0]["evidence"][3]["source_id"]
        child_facets = {
            facet: f"Child {facet}" for facet in WIKI.REPOSITORY_DOSSIER_FACETS
        }
        child = copy.deepcopy(coverage["modules"][0])
        child.update(
            {
                "id": "module-child",
                "title": "Child Capability",
                "parent_id": "module-main",
                "paths": ["src/helper.py"],
                "anchor": "Child Capability",
                "analysis_depth": "surface",
                "verification": {
                    "status": "gap",
                    "reason": "No representative verification was found.",
                },
                "dossier": {
                    facet: {
                        "status": "documented",
                        "locator": f"wiki/module.md#{heading}",
                    }
                    for facet, heading in child_facets.items()
                },
                "evidence": [
                    {
                        "class": evidence_class,
                        "source_id": repository_source_id,
                        "locator": (
                            f"repository@{revision}:src/helper.py#child-{evidence_class}"
                        ),
                    }
                    for evidence_class in ("reachability", "implementation", "boundary")
                ],
                "flow_ids": ["flow-main"],
            }
        )
        coverage["modules"].append(child)
        coverage["discovery_records"].append(
            {
                "id": "route-child",
                "kind": "runtime-entrypoint",
                "locator": f"repository@{revision}:src/helper.py#child",
                "module_id": "module-child",
            }
        )
        coverage["inventory_groups"][0]["module_ids"].append("module-child")
        coverage["flows"][0]["module_ids"].append("module-child")
        for step in coverage["flows"][0]["steps"]:
            step["module_ids"].append("module-child")
        module_page = self.vault / "wiki" / "module.md"
        child_sections = "\n\n".join(
            f"### {heading}\n\nDocumented for the child capability."
            for heading in child_facets.values()
        )
        module_page.write_text(
            module_page.read_text(encoding="utf-8")
            + f"\n## Child Capability\n\nChild behavior.\n\n{child_sections}\n",
            encoding="utf-8",
        )
        coverage["batch_state"] = "functional-analysis-partial"
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode())
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["structural_errors"], 0)
        self.assertIn(
            "incomplete-material-descendant",
            {item["code"] for item in payload["completion_findings"]},
        )

    def test_repository_coverage_rejects_non_repository_evidence(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        evidence_source_id = coverage["modules"][0]["evidence"][0]["source_id"]
        metadata_path = next(
            path
            for path in (self.vault / "raw" / "sources").glob("*/*/source.json")
            if json.loads(path.read_text(encoding="utf-8"))["id"]
            == evidence_source_id
        )
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata.update({"source_type": "web", "adapter": "web"})
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(
            "non-repository-evidence-source",
            {item["code"] for item in json.loads(result.stdout)["structural_errors"]},
        )

    def test_repository_coverage_enforces_evidence_source_roles(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "functional-analysis-partial"
        self.rewrite_repository_coverage(relative, coverage)
        code_source_id = coverage["modules"][0]["evidence"][0]["source_id"]
        code_metadata_path = self.source_metadata_path(code_source_id)
        code_metadata = json.loads(code_metadata_path.read_text(encoding="utf-8"))
        code_metadata.update(
            {
                "origin_uri": "https://example.invalid/other/revision",
                "external_key": "https://example.invalid/other@revision:path",
                "pointer_only": True,
            }
        )
        code_metadata_path.write_text(json.dumps(code_metadata), encoding="utf-8")
        repository_source_id = coverage["modules"][0]["evidence"][3]["source_id"]
        repository_metadata_path = self.source_metadata_path(repository_source_id)
        repository_metadata = json.loads(
            repository_metadata_path.read_text(encoding="utf-8")
        )
        repository_metadata["pointer_only"] = False
        repository_metadata_path.write_text(
            json.dumps(repository_metadata), encoding="utf-8"
        )

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        codes = {item["code"] for item in json.loads(result.stdout)["structural_errors"]}
        self.assertIn("evidence-source-origin-mismatch", codes)
        self.assertIn("evidence-source-provenance-mismatch", codes)
        self.assertIn("evidence-source-content-missing", codes)
        self.assertIn("repository-evidence-not-pointer", codes)

    def test_repository_coverage_rejects_unsafe_and_symlinked_paths(self) -> None:
        relative, _ = self.write_repository_coverage_fixture()

        escaped = self.run_cli("repository-coverage", "../coverage.json")
        self.assertEqual(escaped.returncode, 2)
        self.assertIn(b"workspace-relative", escaped.stderr)

        target = self.base / "coverage-target.json"
        target.write_text((self.vault / relative).read_text(encoding="utf-8"), encoding="utf-8")
        link = self.vault / relative.parent / "linked.json"
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        symlinked = self.run_cli("repository-coverage", str(link.relative_to(self.vault)))
        self.assertEqual(symlinked.returncode, 2)
        self.assertRegex(symlinked.stderr, rb"(?:symlinks|escapes the workspace)")

        internal_target = self.vault / relative.parent / "internal-target.json"
        internal_target.write_text(
            (self.vault / relative).read_text(encoding="utf-8"), encoding="utf-8"
        )
        internal_link = self.vault / relative.parent / "internal-link.json"
        internal_link.symlink_to(internal_target.name)
        internal = self.run_cli(
            "repository-coverage", str(internal_link.relative_to(self.vault))
        )
        self.assertEqual(internal.returncode, 2)
        self.assertIn(b"cannot contain symlinks", internal.stderr)

    def test_repository_coverage_detects_unmapped_discovery_even_when_partial_allowed(self) -> None:
        relative, coverage = self.write_repository_coverage_fixture()
        coverage["batch_state"] = "functional-analysis-partial"
        coverage["discovery_records"][0].pop("module_id")
        coverage["discovery_records"][0].update(
            {"disposition": "excluded", "reason": "Incorrectly classified for this test."}
        )
        self.rewrite_repository_coverage(relative, coverage)

        result = self.run_cli(
            "--json", "repository-coverage", str(relative), "--allow-partial"
        )

        self.assertEqual(result.returncode, 1, result.stderr.decode())
        payload = json.loads(result.stdout)
        self.assertIn(
            "module-not-discovered",
            {item["code"] for item in payload["structural_errors"]},
        )

    def test_init_is_incremental_and_preserves_existing_instructions(self) -> None:
        agents = self.vault / "AGENTS.md"
        agents.write_text("keep me\n", encoding="utf-8")
        payload = self.init()
        self.assertEqual(agents.read_text(encoding="utf-8"), "keep me\n")
        self.assertIn(".wiki/config.json", payload["created"])
        self.assertIn("AGENTS.md", payload["preserved"])
        self.assertTrue((self.vault / "wiki" / "Wiki.base").is_file())

    def test_plain_directory_is_a_first_class_workspace(self) -> None:
        workspace = self.base / "plain-workspace"
        workspace.mkdir()
        canonical = workspace / ".agents" / "skills"
        canonical.mkdir(parents=True)
        for name in SUITE_NAMES:
            shutil.copytree(SKILLS_ROOT / name, canonical / name)
        cli = canonical / "wiki-configure" / "scripts" / "wiki.py"

        def run(*args: str) -> subprocess.CompletedProcess[bytes]:
            return subprocess.run(
                [sys.executable, str(cli), "--workspace", str(workspace), *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        initialized = run("--json", "init")
        self.assertEqual(initialized.returncode, 0, initialized.stderr.decode())
        initialized_payload = json.loads(initialized.stdout)
        self.assertEqual(Path(initialized_payload["workspace"]).resolve(), workspace.resolve())
        self.assertEqual(Path(initialized_payload["vault"]).resolve(), workspace.resolve())
        config = json.loads((workspace / ".wiki" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(config["language"], "auto")
        self.assertFalse((workspace / ".obsidian").exists())
        self.assertFalse((workspace / "wiki" / "Wiki.base").exists())

        doctor = run("doctor")
        self.assertEqual(doctor.returncode, 0, doctor.stdout.decode() + doctor.stderr.decode())
        self.assertIn(b"OK: workspace, skills, and bridges are structurally ready", doctor.stdout)

        lint = run("lint", "--strict")
        self.assertEqual(lint.returncode, 0, lint.stdout.decode() + lint.stderr.decode())

    def test_explicit_uninitialized_plain_directory_reaches_diagnostics(self) -> None:
        workspace = self.base / "uninitialized"
        workspace.mkdir()
        result = subprocess.run(
            [sys.executable, str(CLI_SOURCE), "--workspace", str(workspace), "lint"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(b"missing-config", result.stdout)
        self.assertNotIn(b"Could not locate", result.stderr)

    def test_init_preserves_an_explicit_workspace_language(self) -> None:
        config = copy.deepcopy(WIKI.DEFAULT_CONFIG)
        config["language"] = "zh-CN"
        self.write_config(config)

        self.init()

        persisted = json.loads((self.vault / ".wiki" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(persisted["language"], "zh-CN")

    def test_invalid_workspace_language_is_rejected_before_init_writes(self) -> None:
        config = copy.deepcopy(WIKI.DEFAULT_CONFIG)
        config["language"] = "Chinese (Simplified)"
        self.write_config(config)

        result = self.run_cli("init")

        self.assertEqual(result.returncode, 2)
        self.assertIn(b"BCP 47-style language tag", result.stderr)
        self.assertFalse((self.vault / "wiki").exists())

    def test_config_path_escape_is_rejected_before_init_writes(self) -> None:
        config = copy.deepcopy(WIKI.DEFAULT_CONFIG)
        config["paths"]["raw_sources"] = "../outside"
        self.write_config(config)
        result = self.run_cli("init")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"escapes the workspace", result.stderr)
        self.assertFalse((self.base / "outside").exists())
        self.assertFalse((self.vault / "wiki").exists())

    def test_absolute_and_symlinked_config_paths_are_rejected(self) -> None:
        absolute = copy.deepcopy(WIKI.DEFAULT_CONFIG)
        absolute["paths"]["raw_sources"] = str(self.base / "absolute-outside")
        self.write_config(absolute)
        result = self.run_cli("init")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"must be workspace-relative", result.stderr)

        outside = self.base / "symlink-outside"
        outside.mkdir()
        link = self.vault / "escaped"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        symlinked = copy.deepcopy(WIKI.DEFAULT_CONFIG)
        symlinked["paths"]["raw_sources"] = "escaped/raw"
        self.write_config(symlinked)
        result = self.run_cli("init")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"escapes the workspace", result.stderr)
        self.assertFalse((outside / "raw").exists())

    def test_parent_capture_exclude_is_rejected_during_preflight(self) -> None:
        config = copy.deepcopy(WIKI.DEFAULT_CONFIG)
        config["capture_exclude"] = ["../../secret/**"]
        self.write_config(config)
        result = self.run_cli("init")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"capture_exclude", result.stderr)
        self.assertFalse((self.vault / "raw").exists())

    def test_custom_managed_paths_and_files_are_never_recaptured(self) -> None:
        config = copy.deepcopy(WIKI.DEFAULT_CONFIG)
        config["paths"]["wiki"] = "knowledge"
        config["files"]["schema"] = "governance/schema.md"
        config["capture_exclude"] = []
        self.write_config(config)
        self.init()
        (self.vault / "knowledge" / "topic.md").write_text("managed", encoding="utf-8")
        (self.vault / "governance" / "schema.md").write_text("managed schema", encoding="utf-8")
        incoming = self.vault / "incoming.txt"
        incoming.write_text("capture me", encoding="utf-8")
        result = self.run_cli("--json", "capture", str(self.vault), "--classification", "public")
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["sources"]), 1)
        source_dir = self.vault / payload["sources"][0]["path"]
        metadata = json.loads((source_dir / "source.json").read_text(encoding="utf-8"))
        self.assertEqual(Path(metadata["original_path"]).name, incoming.name)

    def test_repository_url_requires_acquisition_or_a_stable_pointer(self) -> None:
        self.init()
        repository_url = "https://github.com/example/project"
        commit_sha = "a" * 40
        commit_url = f"{repository_url}/commit/{commit_sha}"

        direct = self.run_cli("capture", repository_url)
        self.assertEqual(direct.returncode, 2)
        self.assertIn(b"URLs must be snapshotted through --stdin or captured with --pointer-only", direct.stderr)

        pointer = self.run_cli(
            "--json",
            "capture",
            commit_url,
            "--pointer-only",
            "--title",
            "example/project at aaaaaaaa",
            "--source-type",
            "repository",
            "--adapter",
            "git",
            "--external-key",
            f"github.com/example/project@{commit_sha}",
            "--classification",
            "public",
        )
        self.assertEqual(pointer.returncode, 0, pointer.stderr.decode())
        payload = json.loads(pointer.stdout)
        self.assertEqual(len(payload["sources"]), 1)
        source_dir = self.vault / payload["sources"][0]["path"]
        metadata = json.loads((source_dir / "source.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["origin_uri"], commit_url)
        self.assertEqual(metadata["external_key"], f"github.com/example/project@{commit_sha}")
        self.assertEqual(metadata["source_type"], "repository")
        self.assertEqual(metadata["adapter"], "git")
        self.assertTrue(metadata["pointer_only"])

    def test_specialized_ingestion_provenance_round_trips(self) -> None:
        self.init()

        def source_metadata(result: subprocess.CompletedProcess[bytes]) -> tuple[dict, dict]:
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            payload = json.loads(result.stdout)
            self.assertEqual(len(payload["sources"]), 1)
            source_dir = self.vault / payload["sources"][0]["path"]
            metadata = json.loads((source_dir / "source.json").read_text(encoding="utf-8"))
            return payload, metadata

        canonical_url = "https://docs.example.com/metrics/revenue"
        web_v1, web_v1_metadata = source_metadata(
            self.run_cli(
                "--json",
                "capture",
                "--stdin",
                "--name",
                "revenue.md",
                "--title",
                "Revenue metric",
                "--source-type",
                "web-page",
                "--adapter",
                "web",
                "--classification",
                "public",
                "--authority",
                "publisher",
                "--origin",
                canonical_url,
                "--published-at",
                "2026-07-01T00:00:00Z",
                "--external-key",
                "docs.example.com:metrics/revenue",
                input_bytes=b"# Revenue\n\nVersion one.\n",
            )
        )
        web_v1_id = web_v1["sources"][0]["source_id"]
        self.assertEqual(web_v1_metadata["origin_uri"], canonical_url)
        self.assertEqual(web_v1_metadata["source_type"], "web-page")
        self.assertEqual(web_v1_metadata["adapter"], "web")
        self.assertEqual(web_v1_metadata["published_at"], "2026-07-01T00:00:00Z")
        self.assertEqual(web_v1_metadata["external_key"], "docs.example.com:metrics/revenue")

        _, web_v2_metadata = source_metadata(
            self.run_cli(
                "--json",
                "capture",
                "--stdin",
                "--name",
                "revenue.md",
                "--title",
                "Revenue metric",
                "--source-type",
                "web-page",
                "--adapter",
                "web",
                "--classification",
                "public",
                "--authority",
                "publisher",
                "--origin",
                canonical_url,
                "--published-at",
                "2026-07-15T00:00:00Z",
                "--external-key",
                "docs.example.com:metrics/revenue",
                "--supersedes",
                web_v1_id,
                input_bytes=b"# Revenue\n\nVersion two.\n",
            )
        )
        self.assertEqual(web_v2_metadata["supersedes"], [web_v1_id])

        _, web_pointer_metadata = source_metadata(
            self.run_cli(
                "--json",
                "capture",
                "https://docs.example.com/restricted/policy",
                "--pointer-only",
                "--title",
                "Restricted policy",
                "--source-type",
                "web",
                "--adapter",
                "web",
                "--classification",
                "restricted",
                "--authority",
                "publisher",
                "--external-key",
                "docs.example.com:restricted/policy",
            )
        )
        self.assertEqual(web_pointer_metadata["origin_uri"], "https://docs.example.com/restricted/policy")
        self.assertEqual(web_pointer_metadata["source_type"], "web")
        self.assertEqual(web_pointer_metadata["adapter"], "web")
        self.assertEqual(web_pointer_metadata["external_key"], "docs.example.com:restricted/policy")
        self.assertTrue(web_pointer_metadata["pointer_only"])

        thread_file = self.vault / "thread.json"
        thread_file.write_text(
            json.dumps({"thread_id": "thread-42", "messages": [{"id": "m-1", "state": "edited"}]}),
            encoding="utf-8",
        )
        _, thread_metadata = source_metadata(
            self.run_cli(
                "--json",
                "capture",
                str(thread_file),
                "--source-type",
                "message-batch",
                "--adapter",
                "chat",
                "--classification",
                "internal",
                "--authority",
                "participants",
                "--origin",
                "chat://workspace/channel/thread-42",
                "--published-at",
                "2026-07-15T09:00:00+08:00",
                "--external-key",
                "chat:thread:thread-42:batch-1",
            )
        )
        self.assertEqual(thread_metadata["source_type"], "message-batch")
        self.assertEqual(thread_metadata["classification"], "internal")
        self.assertEqual(thread_metadata["authority"], "participants")

        result_file = self.vault / "revenue-result.csv"
        result_file.write_text("month,revenue\n2026-06,42\n", encoding="utf-8")
        _, result_metadata = source_metadata(
            self.run_cli(
                "--json",
                "capture",
                str(result_file),
                "--source-type",
                "query-result",
                "--adapter",
                "warehouse",
                "--classification",
                "internal",
                "--authority",
                "system-of-record",
                "--origin",
                "warehouse://analytics/jobs/job-123",
                "--published-at",
                "2026-06-30T23:59:59Z",
                "--external-key",
                "warehouse:job:job-123:result",
            )
        )
        self.assertEqual(result_metadata["source_type"], "query-result")
        self.assertEqual(result_metadata["adapter"], "warehouse")
        self.assertEqual(result_metadata["external_key"], "warehouse:job:job-123:result")
        self.assertEqual(result_metadata["published_at"], "2026-06-30T23:59:59Z")

        dashboard_uri = "dashboard://analytics/revenue/tiles/monthly"
        _, dashboard_metadata = source_metadata(
            self.run_cli(
                "--json",
                "capture",
                dashboard_uri,
                "--pointer-only",
                "--title",
                "Monthly revenue dashboard",
                "--source-type",
                "dashboard",
                "--adapter",
                "bi",
                "--classification",
                "internal",
                "--authority",
                "system-of-record",
                "--external-key",
                "bi:dashboard:revenue:tile:monthly",
            )
        )
        self.assertEqual(dashboard_metadata["origin_uri"], dashboard_uri)
        self.assertEqual(dashboard_metadata["source_type"], "dashboard")
        self.assertEqual(dashboard_metadata["adapter"], "bi")
        self.assertEqual(dashboard_metadata["external_key"], "bi:dashboard:revenue:tile:monthly")
        self.assertTrue(dashboard_metadata["pointer_only"])

    def test_explicit_symlink_is_rejected_and_recursive_symlink_is_skipped(self) -> None:
        self.init()
        outside = self.base / "secret.txt"
        outside.write_text("do not capture", encoding="utf-8")
        incoming = self.vault / "incoming"
        incoming.mkdir()
        link = incoming / "secret-link.txt"
        try:
            link.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")

        explicit = self.run_cli("capture", str(link))
        self.assertEqual(explicit.returncode, 2)
        self.assertIn(b"Symlink inputs are not captured", explicit.stderr)

        (incoming / "allowed.txt").write_text("allowed", encoding="utf-8")
        recursive = self.run_cli("--json", "capture", str(incoming), "--classification", "public")
        self.assertEqual(recursive.returncode, 0, recursive.stderr.decode())
        payload = json.loads(recursive.stdout)
        self.assertEqual(len(payload["sources"]), 1)
        source_dir = self.vault / payload["sources"][0]["path"]
        self.assertEqual((source_dir / "original" / "allowed.txt").read_text(encoding="utf-8"), "allowed")
        self.assertFalse((source_dir / "original" / "secret-link.txt").exists())

    def test_capture_rejects_symlinked_destination_year(self) -> None:
        self.init()
        outside = self.base / "outside-captures"
        outside.mkdir()
        year = WIKI.iso_now()[:4]
        year_entry = self.vault / "raw" / "sources" / year
        try:
            year_entry.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        source = self.vault / "fact.txt"
        source.write_text("must stay in the vault", encoding="utf-8")

        result = self.run_cli("capture", str(source), "--classification", "public")

        self.assertEqual(result.returncode, 2)
        self.assertIn(b"Capture destination escapes the workspace", result.stderr)
        self.assertEqual(list(outside.iterdir()), [])

    def test_reserved_source_filename_is_preserved_under_original(self) -> None:
        self.init()
        incoming = self.vault / "incoming"
        incoming.mkdir()
        source = incoming / "source.json"
        source.write_text('{"real": "content"}', encoding="utf-8")
        result = self.run_cli("--json", "capture", str(source), "--classification", "public")
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        source_dir = self.vault / json.loads(result.stdout)["sources"][0]["path"]
        self.assertTrue((source_dir / "source.json").is_file())
        self.assertEqual((source_dir / "original" / "source.json").read_text(encoding="utf-8"), '{"real": "content"}')

    def test_same_bytes_with_stricter_classification_create_variant(self) -> None:
        self.init()
        source = self.vault / "fact.txt"
        source.write_text("same bytes", encoding="utf-8")
        public = self.run_cli("--json", "capture", str(source), "--classification", "public")
        restricted = self.run_cli("--json", "capture", str(source), "--classification", "restricted")
        duplicate = self.run_cli("--json", "capture", str(source), "--classification", "restricted")
        self.assertEqual(public.returncode, restricted.returncode, public.stderr.decode())
        self.assertEqual(restricted.returncode, duplicate.returncode, restricted.stderr.decode())
        public_source = json.loads(public.stdout)["sources"][0]
        restricted_source = json.loads(restricted.stdout)["sources"][0]
        duplicate_source = json.loads(duplicate.stdout)["sources"][0]
        self.assertNotEqual(public_source["source_id"], restricted_source["source_id"])
        self.assertEqual(restricted_source["status"], "created-variant")
        self.assertEqual(duplicate_source["status"], "duplicate")
        self.assertEqual(duplicate_source["source_id"], restricted_source["source_id"])

    def test_lint_reports_non_object_metadata_without_crashing(self) -> None:
        self.init()
        source_dir = self.vault / "raw" / "sources" / "2026" / "src-invalid"
        source_dir.mkdir(parents=True)
        (source_dir / "source.json").write_text("[]", encoding="utf-8")
        (source_dir / "source.md").write_text("invalid", encoding="utf-8")
        result = self.run_cli("lint")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"invalid-source-metadata", result.stdout)
        self.assertNotIn(b"Traceback", result.stderr)

    def test_lint_requires_original_path_under_original_directory(self) -> None:
        self.init()
        source = self.vault / "fact.txt"
        source.write_text("fact", encoding="utf-8")
        captured = self.run_cli("--json", "capture", str(source), "--classification", "public")
        source_dir = self.vault / json.loads(captured.stdout)["sources"][0]["path"]
        metadata_path = source_dir / "source.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["original_path"] = (source_dir / "source.md").relative_to(self.vault).as_posix()
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        result = self.run_cli("lint")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"invalid-original-location", result.stdout)

    def test_rebuild_refuses_unmanaged_outputs_and_force_backs_them_up(self) -> None:
        self.init()
        catalog = self.vault / "wiki" / "_catalog.md"
        catalog.write_text("human content\n", encoding="utf-8")
        refused = self.run_cli("rebuild")
        self.assertEqual(refused.returncode, 2)
        self.assertIn(b"Refusing to overwrite unmanaged", refused.stderr)
        self.assertEqual(catalog.read_text(encoding="utf-8"), "human content\n")

        forced = self.run_cli("--json", "rebuild", "--force")
        self.assertEqual(forced.returncode, 0, forced.stderr.decode())
        payload = json.loads(forced.stdout)
        self.assertIsNotNone(payload["backup"])
        backup = self.vault / payload["backup"] / "wiki" / "_catalog.md"
        self.assertEqual(backup.read_text(encoding="utf-8"), "human content\n")
        self.assertIn(WIKI.GENERATED_MARKER, catalog.read_text(encoding="utf-8"))

        rebuilt = self.run_cli("rebuild")
        self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr.decode())

    def test_site_export_is_public_safe_searchable_and_self_contained(self) -> None:
        self.init()
        self.write_page(
            "public-overview.md",
            title="Public Overview",
            body="""# Public Overview

See [[Other#Details|the other page]].

<script id="xss">alert("unsafe")</script>

[Unsafe action](javascript:alert(1)) must not become a link.

Supported statement.[^note]

[^note]: Public supporting note.
""",
        )
        self.write_page(
            "nested/other.md",
            title="Other & Details",
            aliases=["Other"],
            body="""# Other & Details

## Details

Linked public knowledge.
""",
        )
        secret = "SECRET-ROADMAP-MUST-NOT-LEAK"
        self.write_page(
            "secret-roadmap.md",
            title="Secret Roadmap",
            classification="internal",
            body=f"# Secret Roadmap\n\n{secret}\n",
        )
        unclassified = "UNCLASSIFIED-PAGE-MUST-NOT-LEAK"
        (self.vault / "wiki" / "unclassified.md").write_text(
            "---\n"
            "title: Unclassified Page\n"
            "type: concept\n"
            "created: 2026-07-15\n"
            "updated: 2026-07-15\n"
            "sources: []\n"
            "---\n\n"
            f"# Unclassified Page\n\n{unclassified}\n",
            encoding="utf-8",
        )

        result = self.run_cli(
            "--json",
            "export",
            "outputs/site",
            "--format",
            "site",
            "--title",
            "Example Knowledge",
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode())
        payload = json.loads(result.stdout)
        self.assertEqual(payload["format"], "site")
        self.assertEqual(payload["entrypoint"], "outputs/site/index.html")
        self.assertEqual(payload["report"], "outputs/site/export-report.json")
        self.assertEqual(payload["classifications"], ["public"])
        self.assertEqual(payload["theme"], "default")
        self.assertEqual(payload["addons"], ["search"])
        self.assertEqual(payload["exported_pages"], 2)
        self.assertEqual(payload["excluded_pages"], 2)

        site = self.vault / "outputs" / "site"
        expected = {
            "index.html",
            "pages/public-overview.html",
            "pages/nested/other.html",
            "assets/style.css",
            "assets/app.js",
            "assets/addon-options.js",
            "assets/search-index.js",
            "search-index.json",
            "graph.json",
            "export-report.json",
        }
        actual = {path.relative_to(site).as_posix() for path in site.rglob("*") if path.is_file()}
        self.assertEqual(actual, expected)

        overview = (site / "pages" / "public-overview.html").read_text(encoding="utf-8")
        self.assertIn('href="nested/other.html#details"', overview)
        self.assertIn("&lt;script id=&quot;xss&quot;&gt;", overview)
        self.assertNotIn('<script id="xss">', overview)
        self.assertNotIn('href="javascript:', overview)
        self.assertIn('class="broken-link">Unsafe action</span>', overview)
        self.assertIn('id="footnote-note"', overview)
        self.assertIn("Content-Security-Policy", overview)
        homepage = (site / "index.html").read_text(encoding="utf-8")
        self.assertIn("See the other page", homepage)
        self.assertNotIn("[[Other#Details|the other page]]", homepage)
        self.assertIn('class="site-nav site-nav-desktop"', homepage)
        self.assertIn('class="site-nav site-nav-mobile"', homepage)
        self.assertIn("<summary>Browse pages</summary>", homepage)

        report = json.loads((site / "export-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["theme"]["id"], "default")
        self.assertEqual([addon["id"] for addon in report["addons"]], ["search"])
        self.assertEqual(len(report["profile_sha256"]), 64)
        self.assertEqual(report["counts"], {"excluded_pages": 2, "exported_pages": 2, "source_pages": 4})
        self.assertEqual(
            report["excluded_by_reason"],
            {"invalid-page-classification": 1, "page-classification": 1},
        )
        graph = json.loads((site / "graph.json").read_text(encoding="utf-8"))
        self.assertEqual(graph["edges"], [{"source": "public-overview", "target": "nested/other"}])
        search = json.loads((site / "search-index.json").read_text(encoding="utf-8"))
        self.assertEqual({entry["id"] for entry in search}, {"public-overview", "nested/other"})

        for path in site.rglob("*"):
            if path.is_file():
                exported = path.read_text(encoding="utf-8", errors="ignore")
                for forbidden in (secret, "Secret Roadmap", unclassified, "Unclassified Page"):
                    self.assertNotIn(forbidden, exported, str(path))
        self.assertFalse((site / "raw").exists())
        event = json.loads((self.vault / payload["event"]).read_text(encoding="utf-8"))
        self.assertEqual(event["action"], "export")

    def test_export_capabilities_are_machine_discoverable(self) -> None:
        self.init()

        result = self.run_cli("--json", "export-capabilities", "--format", "site")

        self.assertEqual(result.returncode, 0, result.stderr.decode())
        payload = json.loads(result.stdout)
        self.assertEqual(payload["engine"], "llm-wiki-site-v1")
        self.assertEqual(
            {theme["id"] for theme in payload["themes"]},
            {"default", "editorial", "minimal"},
        )
        self.assertEqual(
            {addon["id"] for addon in payload["addons"]},
            {"search", "toc", "graph", "code-copy", "facets"},
        )
        self.assertEqual(payload["workspace_defaults"]["theme"], "default")
        self.assertTrue(payload["workspace_defaults"]["addons"]["search"]["enabled"])
        facets = next(addon for addon in payload["addons"] if addon["id"] == "facets")
        self.assertEqual(facets["requires"], ["search"])

    def test_site_export_composes_theme_and_addons(self) -> None:
        self.init()
        self.write_page(
            "guide.md",
            title="Export Guide",
            page_type="technique",
            status="active",
            domains=["publishing", "knowledge"],
            body="""# Export Guide

## Prepare

Read the source material.

```python
print("safe")
```

## Publish

Link to [[Reference]].
""",
        )
        self.write_page(
            "reference.md",
            title="Reference",
            page_type="concept",
            status="stable",
            domains=["knowledge"],
            body="# Reference\n\n## Details\n\nSupporting material.\n",
        )

        result = self.run_cli(
            "--json",
            "export",
            "outputs/editorial",
            "--format",
            "site",
            "--title",
            "Editorial Wiki",
            "--theme",
            "editorial",
            "--theme-option",
            "density=compact",
            "--theme-option",
            "accent=#6b4eff",
            "--addon",
            "toc",
            "--addon",
            "graph",
            "--addon",
            "code-copy",
            "--addon",
            "facets",
            "--addon-option",
            "toc.max_level=3",
            "--addon-option",
            'facets.fields=["type","domains"]',
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode())
        payload = json.loads(result.stdout)
        self.assertEqual(payload["theme"], "editorial")
        self.assertEqual(
            payload["addons"], ["search", "facets", "toc", "graph", "code-copy"]
        )
        site = self.vault / "outputs" / "editorial"
        for relative in (
            "assets/addon-options.js",
            "assets/app.js",
            "assets/graph-data.js",
            "assets/search-index.js",
            "assets/style.css",
        ):
            self.assertTrue((site / relative).is_file(), relative)

        index = (site / "index.html").read_text(encoding="utf-8")
        page = (site / "pages" / "guide.html").read_text(encoding="utf-8")
        style = (site / "assets" / "style.css").read_text(encoding="utf-8")
        application = (site / "assets" / "app.js").read_text(encoding="utf-8")
        self.assertIn('data-theme="editorial"', index)
        self.assertIn('data-density="compact"', index)
        self.assertIn('data-addons="search facets toc graph code-copy"', index)
        self.assertIn('data-domains="publishing,knowledge"', index)
        self.assertIn("assets/graph-data.js", index)
        self.assertIn("Iowan Old Style", style)
        self.assertIn("--accent: #6b4eff", style)
        self.assertIn("data-addon-graph", application)
        self.assertIn("data-addon-toc", application)
        self.assertIn("code-copy-button", application)
        self.assertIn("data-addon-facets", application)
        self.assertIn("assets/graph-data.js", page)
        self.assertEqual(page.count("<h1"), 1)
        self.assertIn("connect-src 'none'", page)

        search = json.loads((site / "search-index.json").read_text(encoding="utf-8"))
        guide = next(entry for entry in search if entry["id"] == "guide")
        self.assertEqual(guide["domains"], ["publishing", "knowledge"])
        self.assertEqual(guide["status"], "active")
        graph = json.loads((site / "graph.json").read_text(encoding="utf-8"))
        self.assertEqual(
            next(node for node in graph["nodes"] if node["id"] == "guide")["href"],
            "pages/guide.html",
        )
        report = json.loads((site / "export-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["theme"]["options"]["accent"], "#6b4eff")
        self.assertEqual(
            [addon["id"] for addon in report["addons"]],
            ["search", "facets", "toc", "graph", "code-copy"],
        )
        report_digest = report.pop("report_sha256")
        self.assertEqual(report_digest, WIKI.canonical_json_sha256(report))

    def test_site_export_can_disable_default_search(self) -> None:
        self.init()
        self.write_page("page.md", title="Page", body="# Page\n\nVisible.\n")

        result = self.run_cli(
            "--json", "export", "outputs/bare", "--format", "site", "--no-addon", "search"
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode())
        payload = json.loads(result.stdout)
        self.assertEqual(payload["addons"], [])
        site = self.vault / "outputs" / "bare"
        self.assertFalse((site / "assets" / "addon-options.js").exists())
        self.assertFalse((site / "assets" / "app.js").exists())
        self.assertFalse((site / "assets" / "search-index.js").exists())
        self.assertTrue((site / "search-index.json").is_file())
        index = (site / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("data-search-input", index)

    def test_site_export_rejects_invalid_profile_options_and_dependencies(self) -> None:
        self.init()
        self.write_page("page.md", title="Page", body="# Page\n")

        invalid_color = self.run_cli(
            "export",
            "outputs/color",
            "--format",
            "site",
            "--theme-option",
            "accent=red",
        )
        self.assertEqual(invalid_color.returncode, 2)
        self.assertIn(b"six-digit hex color", invalid_color.stderr)

        non_finite_scale = self.run_cli(
            "export",
            "outputs/non-finite",
            "--format",
            "site",
            "--theme-option",
            "font_scale=1e999",
        )
        self.assertEqual(non_finite_scale.returncode, 2)
        self.assertIn(b"must be a finite number", non_finite_scale.stderr)

        nan_scale = self.run_cli(
            "export",
            "outputs/nan",
            "--format",
            "site",
            "--theme-option",
            "font_scale=NaN",
        )
        self.assertEqual(nan_scale.returncode, 2)
        self.assertIn(b"must be a number", nan_scale.stderr)

        invalid_toc = self.run_cli(
            "export",
            "outputs/toc",
            "--format",
            "site",
            "--addon",
            "toc",
            "--addon-option",
            "toc.min_level=5",
            "--addon-option",
            "toc.max_level=2",
        )
        self.assertEqual(invalid_toc.returncode, 2)
        self.assertIn(b"min_level cannot be greater", invalid_toc.stderr)

        missing_dependency = self.run_cli(
            "export",
            "outputs/facets",
            "--format",
            "site",
            "--addon",
            "facets",
            "--no-addon",
            "search",
        )
        self.assertEqual(missing_dependency.returncode, 2)
        self.assertIn(b"requires explicitly disabled add-on search", missing_dependency.stderr)
        for target in ("color", "toc", "facets"):
            self.assertFalse((self.vault / "outputs" / target).exists())

    def test_site_export_blocks_selected_pages_with_disallowed_sources(self) -> None:
        self.init()
        source = self.run_cli(
            "--json",
            "capture",
            "--stdin",
            "--name",
            "internal.txt",
            "--classification",
            "internal",
            input_bytes=b"INTERNAL-SOURCE-BYTES",
        )
        self.assertEqual(source.returncode, 0, source.stderr.decode())
        source_result = json.loads(source.stdout)["sources"][0]
        source_id = source_result["source_id"]
        self.write_page(
            "published-claim.md",
            title="Published Claim",
            sources=[source_id],
            body="# Published Claim\n\nA claim with controlled evidence.\n",
        )

        blocked = self.run_cli("export", "outputs/site", "--format", "site")

        self.assertEqual(blocked.returncode, 2)
        self.assertIn(b"source-classification=1", blocked.stderr)
        self.assertFalse((self.vault / "outputs" / "site").exists())

        allowed = self.run_cli(
            "--json",
            "export",
            "outputs/site",
            "--format",
            "site",
            "--classification",
            "internal",
        )
        self.assertEqual(allowed.returncode, 0, allowed.stderr.decode())
        payload = json.loads(allowed.stdout)
        self.assertEqual(payload["classifications"], ["public", "internal"])
        site = self.vault / "outputs" / "site"
        self.assertTrue((site / "pages" / "published-claim.html").is_file())
        for path in site.rglob("*"):
            if path.is_file():
                self.assertNotIn("INTERNAL-SOURCE-BYTES", path.read_text(encoding="utf-8", errors="ignore"))

        metadata_path = self.vault / source_result["path"] / "source.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        del metadata["classification"]
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        missing_classification = self.run_cli(
            "export",
            "outputs/site",
            "--format",
            "site",
            "--classification",
            "internal",
        )
        self.assertEqual(missing_classification.returncode, 2)
        self.assertIn(b"invalid-source-classification=1", missing_classification.stderr)
        self.assertTrue((site / "pages" / "published-claim.html").is_file())

    def test_site_export_rejects_duplicate_and_mismatched_source_ids(self) -> None:
        self.init()
        self.write_page(
            "claim.md",
            title="Claim",
            body="# Claim\n\nCited claim.\n",
            sources=["src-collision"],
        )
        first = self.vault / "raw" / "sources" / "2026" / "src-collision" / "source.json"
        second = self.vault / "raw" / "sources" / "2027" / "src-collision" / "source.json"
        first.parent.mkdir(parents=True)
        second.parent.mkdir(parents=True)
        first.write_text(
            json.dumps({"id": "src-collision", "classification": "public"}),
            encoding="utf-8",
        )
        second.write_text(
            json.dumps({"id": "src-collision", "classification": "internal"}),
            encoding="utf-8",
        )

        duplicate = self.run_cli("export", "outputs/site", "--format", "site")
        self.assertEqual(duplicate.returncode, 2)
        self.assertIn(b"Duplicate source ID", duplicate.stderr)
        self.assertFalse((self.vault / "outputs" / "site").exists())

        shutil.rmtree(second.parent)
        legacy = self.vault / "raw" / "entries" / "legacy.md"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_text(
            "---\nid: src-collision\nclassification: internal\n---\n",
            encoding="utf-8",
        )
        cross_format = self.run_cli("export", "outputs/site", "--format", "site")
        self.assertEqual(cross_format.returncode, 2)
        self.assertIn(b"across legacy and current source registries", cross_format.stderr)

        legacy.unlink()
        first.write_text(
            json.dumps({"id": "src-different", "classification": "public"}),
            encoding="utf-8",
        )
        mismatched = self.run_cli("export", "outputs/site", "--format", "site")
        self.assertEqual(mismatched.returncode, 2)
        self.assertIn(b"must match its envelope directory", mismatched.stderr)

    def test_site_export_rejects_symlinked_source_metadata_before_reading(self) -> None:
        self.init()
        self.write_page("page.md", title="Page", body="# Page\n\nVisible.\n")
        external = self.base / "external-source.json"
        external.write_text("not valid source metadata", encoding="utf-8")
        linked = (
            self.vault
            / "raw"
            / "sources"
            / "2026"
            / "src-linked"
            / "source.json"
        )
        linked.parent.mkdir(parents=True)
        try:
            linked.symlink_to(external)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")

        current = self.run_cli("export", "outputs/site", "--format", "site")
        self.assertEqual(current.returncode, 2)
        self.assertIn(b"Symlinked source metadata is not allowed", current.stderr)
        self.assertNotIn(b"Invalid source metadata", current.stderr)

        linked.unlink()
        legacy = self.vault / "raw" / "entries" / "linked.md"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.symlink_to(external)
        old_format = self.run_cli("export", "outputs/site", "--format", "site")
        self.assertEqual(old_format.returncode, 2)
        self.assertIn(b"Symlinked legacy source metadata is not allowed", old_format.stderr)

    def test_site_export_replaces_only_unchanged_managed_targets(self) -> None:
        self.init()
        first_page = self.write_page(
            "first.md",
            title="First",
            body="# First\n\nFirst page.\n",
        )
        stale_page = self.write_page(
            "stale.md",
            title="Stale",
            body="# Stale\n\nThis page will disappear.\n",
        )
        first = self.run_cli("--json", "export", "outputs/site", "--format", "site")
        self.assertEqual(first.returncode, 0, first.stderr.decode())
        site = self.vault / "outputs" / "site"
        self.assertTrue((site / "pages" / "stale.html").is_file())

        stale_page.unlink()
        first_page.write_text(first_page.read_text(encoding="utf-8").replace("First page.", "Updated page."), encoding="utf-8")
        replaced = self.run_cli("--json", "export", "outputs/site", "--format", "site")
        self.assertEqual(replaced.returncode, 0, replaced.stderr.decode())
        self.assertFalse((site / "pages" / "stale.html").exists())
        self.assertIn("Updated page.", (site / "pages" / "first.html").read_text(encoding="utf-8"))

        index = site / "index.html"
        index.write_text("human customization\n", encoding="utf-8")
        refused = self.run_cli("export", "outputs/site", "--format", "site")
        self.assertEqual(refused.returncode, 2)
        self.assertIn(b"Refusing to overwrite unmanaged or modified export target", refused.stderr)
        self.assertEqual(index.read_text(encoding="utf-8"), "human customization\n")

        forced = self.run_cli("--json", "export", "outputs/site", "--format", "site", "--force")
        self.assertEqual(forced.returncode, 0, forced.stderr.decode())
        payload = json.loads(forced.stdout)
        self.assertIsNotNone(payload["backup"])
        backup = self.vault / payload["backup"] / "index.html"
        self.assertEqual(backup.read_text(encoding="utf-8"), "human customization\n")
        self.assertIn("<!doctype html>", index.read_text(encoding="utf-8"))

    def test_site_export_treats_report_edits_as_target_modifications(self) -> None:
        self.init()
        self.write_page("page.md", title="Page", body="# Page\n\nVisible.\n")
        initial = self.run_cli("export", "outputs/site", "--format", "site")
        self.assertEqual(initial.returncode, 0, initial.stderr.decode())
        report_path = self.vault / "outputs" / "site" / "export-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["counts"]["exported_pages"] = 999
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        refused = self.run_cli("export", "outputs/site", "--format", "site")

        self.assertEqual(refused.returncode, 2)
        self.assertIn(b"Refusing to overwrite unmanaged or modified export target", refused.stderr)
        persisted = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["counts"]["exported_pages"], 999)

    def test_site_export_rejects_unsafe_targets(self) -> None:
        self.init()
        self.write_page("page.md", title="Page", body="# Page\n")

        for target, message in (
            ("outputs", b"must be a child"),
            ("wiki/site", b"must be inside the configured outputs"),
            ("../outside", b"cannot contain '..'"),
            (str(self.base / "absolute-site"), b"must be workspace-relative"),
        ):
            result = self.run_cli("export", target, "--format", "site")
            self.assertEqual(result.returncode, 2, target)
            self.assertIn(message, result.stderr, target)

        outside = self.base / "outside-site"
        outside.mkdir()
        link = self.vault / "outputs" / "linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        linked = self.run_cli("export", "outputs/linked/site", "--format", "site")
        self.assertEqual(linked.returncode, 2)
        self.assertIn(b"cannot contain symlinks", linked.stderr)
        self.assertEqual(list(outside.iterdir()), [])

        outside_page = self.base / "outside-page.md"
        outside_page.write_text("EXTERNAL-PAGE-MUST-NOT-BE-READ", encoding="utf-8")
        try:
            (self.vault / "wiki" / "linked-page.md").symlink_to(outside_page)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        linked_page = self.run_cli("export", "outputs/site", "--format", "site")
        self.assertEqual(linked_page.returncode, 2)
        self.assertIn(b"Symlinked wiki pages are not allowed", linked_page.stderr)
        self.assertFalse((self.vault / "outputs" / "site").exists())

        (self.vault / "wiki" / "linked-page.md").unlink()
        config = json.loads((self.vault / ".wiki" / "config.json").read_text(encoding="utf-8"))
        config["paths"]["outputs"] = "."
        (self.vault / ".wiki" / "config.json").write_text(json.dumps(config), encoding="utf-8")
        overlap = self.run_cli("export", "wiki/site", "--format", "site", "--force")
        self.assertEqual(overlap.returncode, 2)
        self.assertIn(b"must be a dedicated workspace child", overlap.stderr)
        self.assertTrue((self.vault / "wiki" / "page.md").is_file())

        config["paths"]["outputs"] = "deliverables"
        config["files"]["index"] = "deliverables/site/index.md"
        (self.vault / ".wiki" / "config.json").write_text(json.dumps(config), encoding="utf-8")
        custom_file_overlap = self.run_cli(
            "export", "deliverables/site", "--format", "site", "--force"
        )
        self.assertEqual(custom_file_overlap.returncode, 2)
        self.assertIn(
            b"overlaps protected workspace path: deliverables/site/index.md",
            custom_file_overlap.stderr,
        )
        self.assertTrue((self.vault / "wiki" / "page.md").is_file())

    def test_site_export_restores_previous_bundle_when_event_write_fails(self) -> None:
        self.init()
        page = self.write_page("page.md", title="Page", body="# Page\n\nVersion one.\n")
        initial = self.run_cli("export", "outputs/site", "--format", "site")
        self.assertEqual(initial.returncode, 0, initial.stderr.decode())
        site = self.vault / "outputs" / "site"
        before = {
            path.relative_to(site).as_posix(): path.read_bytes()
            for path in site.rglob("*")
            if path.is_file()
        }
        page.write_text(page.read_text(encoding="utf-8").replace("Version one.", "Version two."), encoding="utf-8")
        parser = WIKI.build_parser()
        args = parser.parse_args(["--vault", str(self.vault), "export", "outputs/site", "--format", "site"])

        with mock.patch.object(WIKI, "create_event", side_effect=OSError("synthetic export event failure")):
            with self.assertRaises(OSError):
                WIKI.command_export(args)

        after = {
            path.relative_to(site).as_posix(): path.read_bytes()
            for path in site.rglob("*")
            if path.is_file()
        }
        self.assertEqual(after, before)
        self.assertFalse(any(site.parent.glob(".site.stage-*")))
        self.assertFalse(any(site.parent.glob(".site.previous-*")))

    def test_site_export_rejects_input_changes_before_commit(self) -> None:
        self.init()
        page = self.write_page("page.md", title="Page", body="# Page\n\nVersion one.\n")
        parser = WIKI.build_parser()
        args = parser.parse_args(["--vault", str(self.vault), "export", "outputs/site", "--format", "site"])
        original = WIKI.write_site_bundle

        def mutate_after_render(*call_args, **call_kwargs):
            report = original(*call_args, **call_kwargs)
            page.write_text(page.read_text(encoding="utf-8").replace("Version one.", "Version two."), encoding="utf-8")
            return report

        with mock.patch.object(WIKI, "write_site_bundle", side_effect=mutate_after_render):
            with self.assertRaisesRegex(WIKI.WikiError, "changed during export"):
                WIKI.command_export(args)

        self.assertFalse((self.vault / "outputs" / "site").exists())
        self.assertFalse(any((self.vault / "outputs").glob(".site.stage-*")))
        actions = [
            json.loads(path.read_text(encoding="utf-8"))["action"]
            for path in (self.vault / ".wiki" / "events").glob("*.json")
        ]
        self.assertNotIn("export", actions)

    def test_site_export_rechecks_target_before_commit(self) -> None:
        self.init()
        self.write_page("page.md", title="Page", body="# Page\n\nVisible.\n")
        parser = WIKI.build_parser()
        args = parser.parse_args(
            ["--vault", str(self.vault), "export", "outputs/site", "--format", "site"]
        )
        original = WIKI.write_site_bundle
        outside = self.base / "outside-target"
        outside.mkdir()
        target = self.vault / "outputs" / "site"

        def redirect_target_after_render(*call_args, **call_kwargs):
            report = original(*call_args, **call_kwargs)
            target.symlink_to(outside, target_is_directory=True)
            return report

        with mock.patch.object(
            WIKI, "write_site_bundle", side_effect=redirect_target_after_render
        ):
            with self.assertRaisesRegex(WIKI.WikiError, "cannot contain symlinks"):
                WIKI.command_export(args)

        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse(any((self.vault / "outputs").glob(".site.stage-*")))

    def test_batch_failure_rolls_back_new_envelopes_and_records_failure(self) -> None:
        self.init()
        first = self.vault / "first.txt"
        second = self.vault / "second.txt"
        first.write_text("first", encoding="utf-8")
        second.write_text("second", encoding="utf-8")
        parser = WIKI.build_parser()
        args = parser.parse_args(["--vault", str(self.vault), "capture", str(first), str(second)])
        original = WIKI.capture_one
        calls = 0

        def flaky(*call_args, **call_kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise WIKI.WikiError("synthetic second-source failure")
            return original(*call_args, **call_kwargs)

        with mock.patch.object(WIKI, "capture_one", side_effect=flaky):
            with self.assertRaises(WIKI.WikiError):
                WIKI.command_capture(args)

        source_dirs = list((self.vault / "raw" / "sources").glob("*/*"))
        self.assertEqual(source_dirs, [])
        actions = [json.loads(path.read_text(encoding="utf-8"))["action"] for path in (self.vault / ".wiki" / "events").glob("*.json")]
        self.assertIn("capture-failed", actions)
        self.assertNotIn("capture", actions)

    def test_event_failure_rolls_back_entire_capture_batch(self) -> None:
        self.init()
        first = self.vault / "first.txt"
        second = self.vault / "second.txt"
        first.write_text("first", encoding="utf-8")
        second.write_text("second", encoding="utf-8")
        parser = WIKI.build_parser()
        args = parser.parse_args(["--vault", str(self.vault), "capture", str(first), str(second)])
        original = WIKI.create_event
        failed = False

        def flaky_event(root, config, action, message, data):
            nonlocal failed
            if action == "capture" and not failed:
                failed = True
                raise OSError("synthetic event failure")
            return original(root, config, action, message, data)

        with mock.patch.object(WIKI, "create_event", side_effect=flaky_event):
            with self.assertRaises(OSError):
                WIKI.command_capture(args)

        source_dirs = list((self.vault / "raw" / "sources").glob("*/*"))
        self.assertEqual(source_dirs, [])
        actions = [json.loads(path.read_text(encoding="utf-8"))["action"] for path in (self.vault / ".wiki" / "events").glob("*.json")]
        self.assertIn("capture-failed", actions)
        self.assertNotIn("capture", actions)

    def test_batch_rollback_preserves_preexisting_duplicate(self) -> None:
        self.init()
        existing = self.vault / "existing.txt"
        failing = self.vault / "failing.txt"
        existing.write_text("existing", encoding="utf-8")
        failing.write_text("failing", encoding="utf-8")
        first_capture = self.run_cli("--json", "capture", str(existing), "--classification", "public")
        self.assertEqual(first_capture.returncode, 0, first_capture.stderr.decode())
        existing_result = json.loads(first_capture.stdout)["sources"][0]
        existing_dir = self.vault / existing_result["path"]

        parser = WIKI.build_parser()
        args = parser.parse_args(
            ["--vault", str(self.vault), "capture", str(existing), str(failing), "--classification", "public"]
        )
        original = WIKI.capture_one
        calls = 0

        def fail_after_duplicate(*call_args, **call_kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise WIKI.WikiError("synthetic failure after duplicate")
            return original(*call_args, **call_kwargs)

        with mock.patch.object(WIKI, "capture_one", side_effect=fail_after_duplicate):
            with self.assertRaises(WIKI.WikiError):
                WIKI.command_capture(args)

        self.assertTrue(existing_dir.is_dir())
        self.assertEqual(
            (existing_dir / "original" / existing.name).read_text(encoding="utf-8"),
            "existing",
        )

    def test_doctor_accepts_npx_directory_symlinks(self) -> None:
        claude = self.vault / ".claude" / "skills"
        claude.mkdir(parents=True)
        try:
            for name in SUITE_NAMES:
                (claude / name).symlink_to(self.vault / ".agents" / "skills" / name, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        self.init()
        result = self.run_cli("doctor")
        self.assertEqual(result.returncode, 0, result.stdout.decode() + result.stderr.decode())
        self.assertIn(b"OK: workspace, skills, and bridges are structurally ready", result.stdout)

    def test_doctor_rejects_external_bridge_symlink(self) -> None:
        self.init()
        outside = self.base / "outside-skill"
        outside.mkdir()
        (outside / "SKILL.md").write_text("---\nname: wiki-ingest\ndescription: bad\n---\n", encoding="utf-8")
        claude = self.vault / ".claude" / "skills"
        claude.mkdir(parents=True, exist_ok=True)
        shutil.rmtree(claude / "wiki-ingest")
        try:
            (claude / "wiki-ingest").symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        result = self.run_cli("doctor")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"claude-bridge-unsafe", result.stdout)

    def test_init_rejects_external_empty_bridge_directory(self) -> None:
        outside = self.base / "outside-bridge"
        outside.mkdir()
        claude = self.vault / ".claude" / "skills"
        claude.mkdir(parents=True)
        bridge = claude / "wiki-ingest"
        try:
            bridge.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")

        result = self.run_cli("init")

        self.assertEqual(result.returncode, 2)
        self.assertIn(b"Unsafe claude bridge directory symlink", result.stderr)
        self.assertFalse((outside / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
