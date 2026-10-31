"""Opt-in AVRL bootstrap checks; never touch a user's real Git repository."""
from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "codex_avrl_setup.py"
SPEC = importlib.util.spec_from_file_location("codex_avrl_setup", SCRIPT)
SETUP = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SETUP)


class OptInSetupTests(unittest.TestCase):
    def test_canonical_controller_sources_match_bridge_pins(self):
        sources = SETUP.source_files()
        self.assertEqual(set(sources), set(SETUP.RUNTIME))
        self.assertNotIn("hooks.json", sources)
        self.assertNotIn("demo_server.py", sources)

    def test_dry_run_preserves_clean_workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._init_git(root)
            before = SETUP.checked(["git", "status", "--porcelain"], cwd=root)
            result = SETUP.install(root, apply=False)
            self.assertFalse(result["applied"])
            self.assertFalse((root / "scripts").exists())
            self.assertEqual(SETUP.checked(["git", "status", "--porcelain"], cwd=root), before)

    def test_apply_copies_only_reviewed_scripts_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._init_git(root)
            result = SETUP.install(root, apply=True)
            self.assertTrue(result["applied"])
            for name, content in SETUP.source_files().items():
                self.assertEqual((root / "scripts" / name).read_bytes(), content)
            self.assertFalse((root / ".claude").exists())
            with self.assertRaises(SETUP.SetupError):
                SETUP.install(root, apply=True)

    def test_dirty_workspace_is_rejected_before_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._init_git(root)
            (root / "untracked.txt").write_text("keep")
            with self.assertRaisesRegex(SETUP.SetupError, "dirty"):
                SETUP.install(root, apply=True)
            self.assertFalse((root / "scripts").exists())

    def test_missing_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(SETUP.SetupError):
                SETUP.install(Path(temp) / "not-there", apply=True)

    def test_modified_controller_pin_fails_closed(self):
        with patch.object(SETUP, "PINNED", {"avrl.py": "0" * 64}):
            with self.assertRaisesRegex(SETUP.SetupError, "does not match"):
                SETUP.source_files()

    def test_positive_smoke_uses_real_controller_and_bridge(self):
        output = SETUP.smoke()
        self.assertEqual(output["result"], "POSITIVE_PROBE_STATUS_PASS")
        self.assertEqual(output["probe"]["reason"], "controller_present")
        self.assertEqual(output["status"]["reason"], "observed_unverified")
        self.assertEqual(output["status"]["feature"], "example-signup")
        self.assertEqual(output["status"]["status"], "in-review")
        self.assertEqual(output["approval"], "not_performed")
        self.assertEqual(output["verify"], "not_performed")
        self.assertEqual(len(output["git_sha"]), 40)

    @staticmethod
    def _init_git(root: Path) -> None:
        for command in (
            ["git", "init", "-b", "main"],
            ["git", "config", "user.name", "Test Fixture"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "commit", "--allow-empty", "-m", "fixture baseline"],
        ):
            result = subprocess.run(command, cwd=root, text=True,
                                    capture_output=True, check=False)
            if result.returncode:
                raise AssertionError(f"fixture setup failed: {command[0]}")


if __name__ == "__main__":
    unittest.main()
