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
        self.assertTrue((workspace / ".wiki" / "config.json").is_file())
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
