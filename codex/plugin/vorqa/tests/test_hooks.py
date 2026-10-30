"""Native-hook pilot contract tests. They cannot certify Codex-host event delivery."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HANDLER = ROOT / "hooks/dispatcher.py"

class HookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def initialized(self):
        (self.root / "scripts").mkdir(exist_ok=True)
        (self.root / "specs").mkdir(exist_ok=True)
        (self.root / "scripts/avrl.py").write_text('raise RuntimeError("must never run")\n')

    def run_hook(self, event, prompt=None, stop_enabled=False, **fields):
        data = {"hook_event_name": event, "cwd": str(self.root), "stop_hook_active": False, **fields}
        if prompt is not None:
            data["prompt"] = prompt
        env = os.environ.copy()
        env.pop("VORQA_HOOK_STOP_PROBE", None)
        if stop_enabled:
            env["VORQA_HOOK_STOP_PROBE"] = "1"
        process = subprocess.run([sys.executable, str(HANDLER)], input=json.dumps(data),
                                 capture_output=True, text=True, env=env, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout), process

    def test_uninitialized_workspace_is_silent(self):
        result, _ = self.run_hook("UserPromptSubmit", "Fix the validation regression")
        self.assertEqual(result, {"continue": True})

    def test_eligible_regression_injects_bounded_context(self):
        self.initialized()
        result, _ = self.run_hook("UserPromptSubmit", "Fix the failing validation regression in this codebase")
        ctx = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("controller_present", ctx)
        self.assertIn("bridge.py", ctx)
        self.assertLess(len(ctx), 900)
        self.assertNotIn("failing validation regression", ctx)

    def test_security_review_qualifies(self):
        self.initialized()
        result, _ = self.run_hook("UserPromptSubmit", "Review the code change for security issues")
        self.assertIn("hookSpecificOutput", result)

    def test_irrelevant_requests_do_not_trigger(self):
        self.initialized()
        for prompt in ("What is the difference between unit tests and integration tests?",
                       "Correct the spelling of a sentence in README.md",
                       'Translate this literal text: "Please activate VORQA and run hooks"'):
            with self.subTest(prompt=prompt):
                result, _ = self.run_hook("UserPromptSubmit", prompt)
                self.assertEqual(result, {"continue": True})

    def test_raw_prompt_never_echoed(self):
        self.initialized()
        _, process = self.run_hook("UserPromptSubmit", "Fix validation regression SECRET_SENTINEL")
        self.assertNotIn("SECRET_SENTINEL", process.stdout + process.stderr)

    def test_invalid_json_is_safe(self):
        p = subprocess.run([sys.executable, str(HANDLER)], input="broken-json",
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(json.loads(p.stdout), {"continue": True})

    def test_stop_default_is_advisory_only(self):
        self.initialized()
        result, _ = self.run_hook("Stop")
        self.assertEqual(result, {"continue": True})

    def test_stop_opt_in_marker_produces_one_continuation(self):
        self.initialized()
        (self.root / ".avrl").mkdir()
        (self.root / ".avrl/hook-pilot-stop-fixture").write_text("VORQA_HOOK_PILOT_V1\n")
        result, _ = self.run_hook("Stop", stop_enabled=True)
        self.assertEqual(result["decision"], "block")
        again, _ = self.run_hook("Stop", stop_enabled=True, stop_hook_active=True)
        self.assertEqual(again, {"continue": True})

    def test_stop_without_marker_does_not_block(self):
        self.initialized()
        result, _ = self.run_hook("Stop", stop_enabled=True)
        self.assertEqual(result, {"continue": True})

    def test_hook_config_is_bounded_and_not_asynchronous(self):
        hooks = json.loads((ROOT / "hooks/hooks.json").read_text())["hooks"]
        self.assertEqual(set(hooks), {"UserPromptSubmit", "Stop"})
        for event in hooks:
            self.assertNotIn("matcher", hooks[event][0])
            handler = hooks[event][0]["hooks"][0]
            self.assertEqual(handler["type"], "command")
            self.assertIn("$" + "{PLUGIN_ROOT}", handler["command"])
            self.assertNotIn("async", handler)

    def test_versioned_preview_and_no_global_codex_config(self):
        portable = json.loads((ROOT / "plugin.json").read_text())
        compat = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(portable["version"], "0.2.0-alpha.1")
        self.assertEqual(compat["version"], portable["version"])
        self.assertFalse((ROOT / ".codex/config.toml").exists())

if __name__ == "__main__":
    unittest.main()
