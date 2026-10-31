"""Codex bridge safety and explicit-workflow contract tests."""
from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PLUGIN_ROOT / "scripts" / "bridge.py"
SPEC = importlib.util.spec_from_file_location("vorqa_codex_bridge_under_test", BRIDGE_PATH)
BRIDGE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BRIDGE)


class BridgeResolutionTests(unittest.TestCase):
    def test_workspace_resolution_error_is_normalized_without_path_leak(self):
        output = io.StringIO()
        with patch.object(Path, "resolve", side_effect=OSError("PRIVATE_WORKSPACE_PATH")):
            with redirect_stdout(output):
                result = BRIDGE.main(["--workspace", "/private/example", "probe"])

        self.assertEqual(result, 2)
        self.assertEqual(output.getvalue().strip(),
                         '{"available": false, "bridge_schema": 1, "kind": "probe", '
                         '"reason": "workspace_resolution_failed"}')
        self.assertNotIn("PRIVATE_WORKSPACE_PATH", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())


class ExplicitWorkflowSkillTests(unittest.TestCase):
    def setUp(self):
        skill_path = PLUGIN_ROOT / "skills" / "vorqa-workflow" / "SKILL.md"
        self.content = skill_path.read_text()

    def test_codex_readme_describes_state_changing_bridge_and_safety_bounds(self):
        readme = (PLUGIN_ROOT.parents[2] / "codex" / "README.md").read_text()
        for requirement in (
            "state-changing",
            "controller round",
            "controller verify",
            "operator_handoff_required",
            "not an OS sandbox",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, readme)

    def test_skill_describes_the_canonical_explicit_controller_stages(self):
        commands = (
            "controller round <feature>",
            "controller verify <feature>",
            "controller review <feature> --result pass",
            "controller blind <feature> --result pass",
            "operator_handoff_required",
            "controller complete <feature>",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertIn(command, self.content)

    def test_skill_inspects_eval_commands_before_verification(self):
        self.assertIn("Before `verify <feature>`, read `specs/<feature>/eval.json`", self.content)
        self.assertIn("inspect every command", self.content)
        self.assertIn("bridge process environment", self.content)
        self.assertIn("this runner does not sandbox project checks", self.content)

    def test_skill_does_not_fabricate_approval_or_independent_identity(self):
        self.assertIn("Do not synthesize or submit approval", self.content)
        self.assertIn("a TTY does not establish human presence", self.content)
        self.assertIn("does not authenticate reviewer identity", self.content)
        self.assertIn("or claim independent review when the reviewing agent is the same actor", self.content)

    def test_skill_requires_operator_for_release_attestation(self):
        self.assertIn("separately governed process tied to the current SHA", self.content)
        self.assertIn("human operator", self.content)

    def test_skill_keeps_native_hooks_and_observed_status_out_of_pass_claims(self):
        self.assertIn("`observed_unverified`", self.content)
        self.assertIn("native hook delivery and automatic skill activation remain", self.content.lower())
        self.assertIn("unverified", self.content.lower())
        self.assertIn("not a PASS", self.content)

    def test_skill_requires_pinned_controller_identity_and_project_trust(self):
        self.assertIn("pins the canonical `avrl.py` SHA-256", self.content)
        self.assertIn("pinned `trace_events.py` dependency", self.content)
        self.assertIn("untrusted_controller_dependency", self.content)
        self.assertIn("independent project trust decision", self.content.lower())
        self.assertIn("untrusted_controller", self.content)

    def test_plugin_metadata_discloses_stateful_workflow_capability(self):
        manifest = json.loads((PLUGIN_ROOT / "plugin.json").read_text())
        capabilities = manifest["extensions"]["com.openai"]["interface"]["capabilities"]
        self.assertEqual(capabilities, ["Read", "Write"])


if __name__ == "__main__":
    unittest.main()
