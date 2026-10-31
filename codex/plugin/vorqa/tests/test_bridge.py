"""Portable read-only Codex bridge contract tests (unittest, no API calls)."""
from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "bridge.py"
PLUGIN_ROOT = SCRIPT.parents[1]
TRUSTED_AVRL_SOURCE = SCRIPT.parents[4] / "claude/implementation/scripts/avrl.py"
TRUSTED_TRACE_SOURCE = TRUSTED_AVRL_SOURCE.with_name("trace_events.py")
BRIDGE_SPEC = importlib.util.spec_from_file_location("vorqa_test_bridge", SCRIPT)
BRIDGE = importlib.util.module_from_spec(BRIDGE_SPEC)
assert BRIDGE_SPEC.loader is not None
BRIDGE_SPEC.loader.exec_module(BRIDGE)


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
        (self.root / "scripts" / "trace_events.py").write_bytes(TRUSTED_TRACE_SOURCE.read_bytes())

    def install_trusted_controller(self):
        (self.root / "scripts").mkdir(exist_ok=True)
        (self.root / "specs").mkdir(exist_ok=True)
        (self.root / "scripts" / "avrl.py").write_bytes(TRUSTED_AVRL_SOURCE.read_bytes())
        (self.root / "scripts" / "trace_events.py").write_bytes(TRUSTED_TRACE_SOURCE.read_bytes())
        state_dir = self.root / ".avrl/state"
        state_dir.mkdir(parents=True)
        (state_dir / "sample-feature.json").write_text(json.dumps({
            "version": 2, "feature": "sample-feature", "status": "reviewing",
            "risk": "high", "round": 2, "max_rounds": 3
        }))

    def run_trusted_fixture(self, source, *args):
        # Test-only digest override exercises response handling with controlled fixture code.
        self.install_fixture(source)
        digest = hashlib.sha256((self.root / "scripts/avrl.py").read_bytes()).hexdigest()
        output = io.StringIO()
        with patch.object(BRIDGE, "TRUSTED_CONTROLLER_SHA256", digest):
            with redirect_stdout(output):
                result = BRIDGE.main(["--workspace", str(self.root), *args])
        return result, json.loads(output.getvalue()), output.getvalue()

    def test_trusted_controller_rejects_modified_trace_dependency(self):
        self.install_trusted_controller()
        (self.root / "scripts" / "trace_events.py").write_text("raise RuntimeError('untrusted helper')\n")
        self.assertIsNone(BRIDGE.trusted_trace_events_source(self.root))

    def test_untrusted_trace_dependency_is_rejected_before_controller_execution(self):
        marker = self.root / "controller-executed"
        self.install_fixture(f'import pathlib; pathlib.Path({str(marker)!r}).write_text("ran")\n')
        (self.root / "scripts" / "trace_events.py").write_text("raise RuntimeError('untrusted helper')\n")
        digest = hashlib.sha256((self.root / "scripts/avrl.py").read_bytes()).hexdigest()
        output = io.StringIO()
        with patch.object(BRIDGE, "TRUSTED_CONTROLLER_SHA256", digest):
            with redirect_stdout(output):
                result = BRIDGE.main(["--workspace", str(self.root), "controller", "round", "sample-feature"])
        payload = json.loads(output.getvalue())
        self.assertEqual(result, 2)
        self.assertEqual(payload["reason"], "untrusted_controller_dependency")
        self.assertFalse(marker.exists())

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

    def test_untrusted_controller_is_rejected_before_execution(self):
        marker = self.root / "controller-executed"
        self.install_fixture(
            f'import pathlib; pathlib.Path({str(marker)!r}).write_text("ran")\n'
        )
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Fixture"],
                       check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "fixture@example.invalid"],
                       check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.root), "add", "scripts/avrl.py", "scripts/trace_events.py"],
                       check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "commit.gpgsign=false", "commit", "-qm", "untrusted controller"],
                       check=True, capture_output=True)
        clean = subprocess.run(["git", "-C", str(self.root), "status", "--porcelain"],
                               check=True, capture_output=True, text=True)
        self.assertEqual(clean.stdout, "")
        process, payload = self.cli("status", "--feature", "sample-feature")
        self.assertEqual(process.returncode, 2)
        self.assertFalse(marker.exists(), "untrusted controller executed before trust validation")
        self.assertEqual(payload["reason"], "untrusted_controller")

    def test_controller_runner_rejects_untrusted_clean_source_before_execution(self):
        marker = self.root / "controller-executed"
        self.install_fixture(
            f'import pathlib; pathlib.Path({str(marker)!r}).write_text("ran")\n'
        )
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Fixture"],
                       check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "fixture@example.invalid"],
                       check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.root), "add", "scripts/avrl.py", "scripts/trace_events.py"],
                       check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "commit.gpgsign=false", "commit", "-qm", "untrusted controller"],
                       check=True, capture_output=True)
        process = subprocess.run(
            [sys.executable, str(SCRIPT), "--workspace", str(self.root), "controller", "--",
             "verify", "sample-feature"],
            capture_output=True, text=True, timeout=20
        )
        self.assertTrue(process.stdout, msg=f"controller runner returned no JSON: {process.stderr.strip()}")
        payload = json.loads(process.stdout)
        self.assertEqual(process.returncode, 2)
        self.assertEqual(payload["reason"], "untrusted_controller")
        self.assertFalse(marker.exists())

    def test_controller_runner_refuses_unapproved_init(self):
        process, payload = self.cli("controller", "init", "sample-feature", "--risk", "low")
        self.assertEqual(process.returncode, 2)
        self.assertEqual(payload["reason"], "unsupported_controller_command")
        self.assertFalse((self.root / ".avrl").exists())

    def test_controller_runner_hands_off_approval_commands_without_execution(self):
        marker = self.root / "controller-executed"
        for command in ("approve", "release-attest"):
            with self.subTest(command=command):
                result, payload, output = self.run_trusted_fixture(
                    f'import pathlib; pathlib.Path({str(marker)!r}).write_text("ran")\n',
                    "controller", command, "sample-feature", "--actor", "Fixture"
                )
                self.assertEqual(result, 2)
                self.assertEqual(payload["reason"], "operator_handoff_required")
                self.assertFalse(marker.exists(), output)

    def test_controller_runner_preserves_canonical_gate_rejection(self):
        self.install_trusted_controller()
        process, payload = self.cli("controller", "round", "sample-feature")
        self.assertEqual(process.returncode, 2)
        self.assertEqual(payload["reason"], "controller_rejected")
        self.assertEqual(payload["command"], "round")
        self.assertEqual(payload["exit_code"], 2)

    def test_controller_runner_emits_one_json_object_for_pinned_status(self):
        self.install_trusted_controller()
        process, payload = self.cli("controller", "status", "sample-feature", "--json")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(payload["reason"], "controller_command_succeeded")
        self.assertEqual(payload["command"], "status")
        self.assertEqual(payload["exit_code"], 0)
        self.assertEqual(payload["summary"], "feature=sample-feature status=reviewing risk=high round=2/3")
        self.assertEqual(len(process.stdout.strip().splitlines()), 1)

    def test_successful_status_does_not_claim_feature_completion(self):
        self.install_trusted_controller()
        process, payload = self.cli("controller", "status", "sample-feature", "--json")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(payload["reason"], "controller_command_succeeded")
        self.assertIn("status=reviewing", payload["summary"])

    def test_controller_runner_status_does_not_echo_untrusted_state_fields(self):
        self.install_trusted_controller()
        state_path = self.root / ".avrl/state/sample-feature.json"
        state = json.loads(state_path.read_text())
        state["reason"] = "PRIVATE_STATE TOKEN=do-not-echo"
        state_path.write_text(json.dumps(state))
        process, payload = self.cli("controller", "status", "sample-feature", "--json")
        self.assertEqual(process.returncode, 0)
        self.assertNotIn("PRIVATE_STATE", process.stdout)
        self.assertNotIn("do-not-echo", process.stdout)
        self.assertEqual(payload["reason"], "controller_command_succeeded")

    def test_controller_runner_bounds_captured_output(self):
        result, payload, output = self.run_trusted_fixture(
            'print("x" * 65537)\n',
            "controller", "status", "sample-feature"
        )
        self.assertEqual(result, 2)
        self.assertEqual(payload["reason"], "controller_output_too_large")
        self.assertLess(len(output.encode()), 2048)

    def test_controller_hash_to_execution_race_uses_validated_bytes(self):
        self.install_trusted_controller()
        controller_path = self.root / "scripts" / "avrl.py"
        marker = self.root / "replacement-executed"
        original = BRIDGE.execute_pinned_controller

        def replace_after_validation(root, source, trace_source, args):
            controller_path.write_text(
                f'import pathlib; pathlib.Path({str(marker)!r}).write_text("ran")\n'
            )
            return original(root, source, trace_source, args)

        output = io.StringIO()
        with patch.object(BRIDGE, "execute_pinned_controller", side_effect=replace_after_validation):
            with redirect_stdout(output):
                result = BRIDGE.main([
                    "--workspace", str(self.root), "controller", "status", "sample-feature", "--json"
                ])
        payload = json.loads(output.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["reason"], "controller_command_succeeded")
        self.assertFalse(marker.exists())

    def test_controller_helper_hash_to_execution_race_uses_validated_bytes(self):
        marker = self.root / "replacement-helper-executed"
        controller = (
            "import importlib.util\n"
            "from pathlib import Path\n"
            "location = Path(__file__).resolve().parent / 'trace_events.py'\n"
            "spec = importlib.util.spec_from_file_location('_avrl_trace', location)\n"
            "module = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(module)\n"
            "print('Round 1 started; delegate builder' if module.coverage([], [])['complete'] else 'bad')\n"
        )
        self.install_fixture(controller)
        original = BRIDGE.execute_pinned_controller

        def replace_helper_after_validation(root, source, trace_source, args):
            (root / "scripts" / "trace_events.py").write_text(
                f'import pathlib; pathlib.Path({str(marker)!r}).write_text("ran")\n'
                "def coverage(records, expectations): return {'complete': False}\n"
            )
            return original(root, source, trace_source, args)

        output = io.StringIO()
        digest = hashlib.sha256((self.root / "scripts/avrl.py").read_bytes()).hexdigest()
        with patch.object(BRIDGE, "TRUSTED_CONTROLLER_SHA256", digest):
            with patch.object(BRIDGE, "execute_pinned_controller", side_effect=replace_helper_after_validation):
                with redirect_stdout(output):
                    result = BRIDGE.main([
                        "--workspace", str(self.root), "controller", "round", "sample-feature"
                    ])
        payload = json.loads(output.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["reason"], "controller_command_succeeded")
        self.assertEqual(payload["summary"], "round_started=1")
        self.assertFalse(marker.exists())

    def test_output_limit_kills_controller_and_descendant(self):
        marker = self.root / "late-child-action"
        child = (
            "import pathlib, time; time.sleep(0.4); "
            f"pathlib.Path({str(marker)!r}).write_text('survived')"
        )
        fixture = (
            "import subprocess, sys\n"
            "subprocess.Popen([sys.executable, '-c', " + repr(child) + "])\n"
            "while True:\n"
            "    sys.stdout.write('x' * 4096)\n"
            "    sys.stdout.flush()\n"
        )
        result, payload, _ = self.run_trusted_fixture(
            fixture, "controller", "status", "sample-feature"
        )
        time.sleep(0.5)
        self.assertEqual(result, 2)
        self.assertEqual(payload["reason"], "controller_output_too_large")
        self.assertFalse(marker.exists())

    def test_short_controller_timeout_kills_descendant(self):
        marker = self.root / "late-timeout-child-action"
        child = (
            "import pathlib, time; time.sleep(0.4); "
            f"pathlib.Path({str(marker)!r}).write_text('survived')"
        )
        fixture = (
            "import subprocess, sys, time\n"
            "subprocess.Popen([sys.executable, '-c', " + repr(child) + "])\n"
            "time.sleep(2)\n"
        )
        with patch.object(BRIDGE, "QUICK_CONTROLLER_TIMEOUT", 0.1):
            result, payload, _ = self.run_trusted_fixture(
                fixture, "controller", "status", "sample-feature"
            )
        time.sleep(0.5)
        self.assertEqual(result, 2)
        self.assertEqual(payload["reason"], "controller_timeout")
        self.assertFalse(marker.exists())

    def test_status_is_observed_not_approved(self):
        self.install_trusted_controller()
        process, payload = self.cli("status", "--feature", "sample-feature")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(payload["status"], "reviewing")
        self.assertEqual(payload["reason"], "observed_unverified")
        self.assertNotIn("PASS", process.stdout)

    def test_status_bridge_caps_controller_output_from_oversized_state(self):
        self.install_trusted_controller()
        state_path = self.root / ".avrl/state/sample-feature.json"
        state = json.loads(state_path.read_text())
        state["untrusted_extra"] = "x" * 70000
        state_path.write_text(json.dumps(state))
        process, payload = self.cli("status", "--feature", "sample-feature")
        self.assertEqual(process.returncode, 2)
        self.assertEqual(payload["reason"], "controller_output_too_large")
        self.assertLess(len(process.stdout), 2048)

    def test_status_output_validation_does_not_leak_controller_output(self):
        result, payload, output = self.run_trusted_fixture(
            'print("SENSITIVE_RAW_PAYLOAD")\n', "status", "--feature", "sample-feature"
        )
        self.assertEqual(result, 2)
        self.assertEqual(payload["reason"], "malformed_controller_response")
        self.assertNotIn("SENSITIVE_RAW_PAYLOAD", output)

    def test_read_only_status_rejects_unhashable_json_fields(self):
        for field, value in (("status", []), ("risk", {})):
            with self.subTest(field=field):
                state = {"feature": "sample-feature", "status": "reviewing", "risk": "high",
                         "round": 1, "max_rounds": 3}
                state[field] = value
                source = "import json\nprint(json.dumps(" + repr(state) + "))\n"
                result, payload, output = self.run_trusted_fixture(
                    source, "status", "--feature", "sample-feature"
                )
                self.assertEqual(result, 2)
                self.assertEqual(payload["reason"], "malformed_controller_response")
                self.assertNotIn("Traceback", output)

    def test_controller_status_rejects_unhashable_json_fields(self):
        for field, value in (("status", []), ("risk", {})):
            with self.subTest(field=field):
                state = {"feature": "sample-feature", "status": "reviewing", "risk": "high",
                         "round": 1, "max_rounds": 3}
                state[field] = value
                source = "import json\nprint(json.dumps(" + repr(state) + "))\n"
                result, payload, output = self.run_trusted_fixture(
                    source, "controller", "status", "sample-feature"
                )
                self.assertEqual(result, 2)
                self.assertEqual(payload["reason"], "malformed_controller_response")
                self.assertNotIn("Traceback", output)

    def test_invalid_feature_does_not_execute_controller(self):
        self.install_fixture('raise RuntimeError("should never execute")\n')
        process, payload = self.cli("status", "--feature", "../../secret")
        self.assertEqual(process.returncode, 2)
        self.assertEqual(payload["reason"], "invalid_feature")

    def test_bad_json_and_controller_failure_do_not_leak_output(self):
        result, payload, output = self.run_trusted_fixture(
            'import sys\nprint("SENSITIVE_STDERR", file=sys.stderr)\nsys.exit(7)\n',
            "status", "--feature", "sample-feature"
        )
        self.assertEqual(result, 2)
        self.assertEqual(payload["reason"], "controller_rejected")
        self.assertNotIn("SENSITIVE_STDERR", output)

    def test_controller_failure_summary_uses_fixed_reason_codes(self):
        summary = BRIDGE.controller_summary(
            "round", b"", b"AVRL ERROR: Cannot start round from private-branch-name\n", 2
        )
        self.assertEqual(summary, "rejected: round_transition_denied")
        self.assertNotIn("private-branch-name", summary)

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
        self.assertEqual(portable["version"], "0.2.0-preview.1")
        self.assertNotIn("hooks", portable)
        self.assertNotIn("hooks", legacy)
        self.assertNotIn("hooks", portable["extensions"]["com.openai"])
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

    def test_skill_routes_lifecycle_through_pinned_bridge_runner(self):
        content = (SCRIPT.parents[1] / "skills/vorqa-workflow/SKILL.md").read_text()
        self.assertIn("bridge.py --workspace <workspace> controller", content)
        self.assertNotIn("Use the pinned controller at `<workspace>/scripts/avrl.py`", content)
        self.assertIn("controller complete", content)

    def test_skill_refuses_to_simulate_approval_or_release_attestation(self):
        content = (SCRIPT.parents[1] / "skills/vorqa-workflow/SKILL.md").read_text()
        self.assertNotIn("controller --interactive", content)
        self.assertIn("operator_handoff_required", content)
        self.assertIn("actual independent reviewer", content)
        self.assertIn("real QA session", content)

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
            self.assertEqual(json.loads(proc.stdout)["reason"], "untrusted_controller")
            self.assertNotIn("SECRET_STATE_VALUE", proc.stdout)

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
