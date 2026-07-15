from __future__ import annotations

import copy
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

    def test_repository_ingestion_is_routed_as_an_on_demand_reference(self) -> None:
        skill_file = SKILLS_ROOT / "wiki-ingest" / "SKILL.md"
        reference = SKILLS_ROOT / "wiki-ingest" / "references" / "repository-ingestion.md"
        metadata, body = WIKI.parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        description = str(metadata["description"])

        for trigger in ("Git repositories", "repository URL", "GitHub", "GitLab", "project wiki"):
            self.assertIn(trigger, description)
        self.assertNotIn("analyze a GitHub", description)
        self.assertNotIn("整理代码库", description)
        self.assertIn("read-only code analysis", description)
        self.assertIn("references/repository-ingestion.md", body)
        self.assertIn("one-time repository ingest", body)
        self.assertTrue(reference.is_file())

        contract = reference.read_text(encoding="utf-8")
        for section in (
            "## Resolve immutable identity",
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
        for capture_flag in ("--origin", "--source-type", "--adapter", "--external-key"):
            self.assertIn(capture_flag, contract)
        self.assertIn("Avoid blind whole-directory capture", contract)
        self.assertRegex(contract, r"Do not (?:run|execute)")

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
