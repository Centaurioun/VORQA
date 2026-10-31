"""Portable read-only Codex bridge contract tests (unittest, no API calls)."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "bridge.py"


class CodexBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)

    def cli(self, *args):
        proc = subprocess.run([sys.executable, str(SCRIPT), "--workspace", str(self.root), *args],
                              capture_output=True, text=True, timeout=20)
        return proc, json.loads(proc.stdout)

    def install_fixture(self, source):
        (self.root / "scripts").mkdir(exist_ok=True)
        (self.root / "specs").mkdir(exist_ok=True)
        (self.root / "scripts" / "avrl.py").write_text(source)

    def test_probe_rejects_uninitialized_workspace(self):
        process, payload = self.cli("probe")
        self.assertEqual(process.returncode, 2)
        self.assertFalse(payload["available"])
        self.assertEqual(payload["reason"], "controller_not_installed")

    def test_probe_accepts_local_controller_without_running_it(self):
        self.install_fixture('raise RuntimeError("must not run during probe")\n')
        process, payload = self.cli("probe")
        self.assertEqual(process.returncode, 0)
        self.assertTrue(payload["available"])
        self.assertEqual(payload["reason"], "controller_present")

    def test_status_is_observed_not_approved(self):
        self.install_fixture('import json\nprint(json.dumps({"feature":"sample-feature","status":"reviewing","risk":"high","round":2,"max_rounds":3,"secret":"DO_NOT_LEAK"}))\n')
        process, payload = self.cli("status", "--feature", "sample-feature")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(payload["status"], "reviewing")
        self.assertEqual(payload["reason"], "observed_unverified")
        self.assertNotIn("DO_NOT_LEAK", process.stdout)
        self.assertNotIn("secret", process.stdout)
        self.assertNotIn("PASS", process.stdout)

    def test_invalid_feature_does_not_execute_controller(self):
        self.install_fixture('raise RuntimeError("should never execute")\n')
        process, payload = self.cli("status", "--feature", "../../secret")
        self.assertEqual(process.returncode, 2)
        self.assertEqual(payload["reason"], "invalid_feature")

    def test_bad_json_and_controller_failure_do_not_leak_output(self):
        self.install_fixture('print("SENSITIVE_RAW_PAYLOAD")\n')
        process, payload = self.cli("status", "--feature", "sample-feature")
        self.assertEqual(process.returncode, 2)
        self.assertEqual(payload["reason"], "malformed_controller_response")
        self.assertNotIn("SENSITIVE_RAW_PAYLOAD", process.stdout)
        (self.root / "scripts" / "avrl.py").write_text('import sys\nprint("SENSITIVE_STDERR", file=sys.stderr)\nsys.exit(7)\n')
        process, payload = self.cli("status", "--feature", "sample-feature")
        self.assertEqual(payload["reason"], "controller_rejected")
        self.assertNotIn("SENSITIVE_STDERR", process.stdout)

    def test_symlink_controller_rejected(self):
        (self.root / "scripts").mkdir()
        (self.root / "specs").mkdir()
        outside = self.root / "elsewhere.py"
        outside.write_text('print("unsafe")')
        (self.root / "scripts" / "avrl.py").symlink_to(outside)
        process, payload = self.cli("probe")
        self.assertEqual(process.returncode, 2)
        self.assertEqual(payload["reason"], "controller_not_installed")


if __name__ == "__main__":
    unittest.main()

class PackageManifestTests(unittest.TestCase):
    def test_portable_and_compatibility_manifests_match_identity(self):
        root = SCRIPT.parents[1]
        portable = json.loads((root / "plugin.json").read_text())
        legacy = json.loads((root / ".codex-plugin/plugin.json").read_text())
        for key in ("name", "version", "description"):
            self.assertEqual(portable[key], legacy[key])
        self.assertEqual(portable["name"], "vorqa")
        self.assertEqual(legacy["skills"], "./skills/")
        self.assertLessEqual(len(portable["extensions"]["com.openai"]["interface"]["shortDescription"]), 30)
        self.assertFalse((root / "hooks").exists())
        self.assertFalse((root / "mcp.json").exists())

    def test_skill_discovery_and_explicit_negative_examples(self):
        path = SCRIPT.parents[1] / "skills/vorqa-workflow/SKILL.md"
        content = path.read_text()
        self.assertTrue(content.startswith("---\nname: vorqa-workflow\n"))
        self.assertIn("description:", content)
        self.assertIn("When **not** to use", content)
        self.assertIn("NOT OBSERVED", content)
        self.assertIn("UNVERIFIED", content)

class UntrustedStateTests(unittest.TestCase):
    def test_controller_cannot_inject_sensitive_status(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
            (root / "scripts").mkdir()
            (root / "specs").mkdir()
            (root / "scripts/avrl.py").write_text('import json\nprint(json.dumps({"feature":"sample-feature","status":"SECRET_STATE_VALUE","risk":"high","round":1,"max_rounds":3}))\n')
            proc=subprocess.run([sys.executable, str(SCRIPT), "--workspace", str(root), "status", "--feature", "sample-feature"], capture_output=True, text=True)
            self.assertEqual(proc.returncode,2)
            self.assertEqual(json.loads(proc.stdout)["reason"], "malformed_controller_response")
            self.assertNotIn("SECRET_STATE_VALUE", proc.stdout)

    def test_non_string_status_and_risk_are_rejected_without_traceback(self):
        for field, value in (("status", []), ("risk", {})):
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
                    (root / "scripts").mkdir()
                    (root / "specs").mkdir()
                    state = {"feature": "sample-feature", "status": "reviewing", "risk": "high",
                             "round": 1, "max_rounds": 3}
                    state[field] = value
                    source = "import json\nprint(json.dumps(" + repr(state) + "))\n"
                    (root / "scripts/avrl.py").write_text(source)
                    proc = subprocess.run(
                        [sys.executable, str(SCRIPT), "--workspace", str(root),
                         "status", "--feature", "sample-feature"],
                        capture_output=True, text=True, timeout=20,
                    )
                    self.assertEqual(proc.returncode, 2, proc.stderr)
                    payload = json.loads(proc.stdout)
                    self.assertEqual(payload["reason"], "malformed_controller_response")
                    self.assertNotIn("Traceback", proc.stderr)

class SymlinkParentTests(unittest.TestCase):
    def test_parent_scripts_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "repository"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
            (root / "specs").mkdir()
            (outside / "avrl.py").write_text('print("must not execute")\n')
            (root / "scripts").symlink_to(outside, target_is_directory=True)
            proc = subprocess.run([sys.executable, str(SCRIPT), "--workspace", str(root), "probe"], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(json.loads(proc.stdout)["reason"], "controller_not_installed")
