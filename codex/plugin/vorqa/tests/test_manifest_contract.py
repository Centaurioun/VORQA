"""Static contracts for the Codex plugin's bundled prompt hook."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ManifestContractTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())

    def test_codex_manifest_explicitly_resolves_bundled_hooks(self):
        self.assertEqual(self.manifest["hooks"], "./hooks/hooks.json")
        self.assertTrue((ROOT / self.manifest["hooks"]).is_file())

    def test_manifest_hook_path_stays_inside_plugin_root(self):
        hook_path = Path(self.manifest["hooks"])
        resolved = (ROOT / hook_path).resolve()
        self.assertFalse(hook_path.is_absolute())
        self.assertNotIn("..", hook_path.parts)
        self.assertTrue(resolved.is_relative_to(ROOT.resolve()))

    def test_hooks_json_matches_supported_event_contract(self):
        hooks = json.loads((ROOT / "hooks/hooks.json").read_text())["hooks"]
        handler = hooks["UserPromptSubmit"][0]["hooks"][0]
        self.assertIsInstance(hooks["UserPromptSubmit"], list)
        self.assertNotIn("matcher", hooks["UserPromptSubmit"][0])
        self.assertEqual(handler["type"], "command")
        self.assertEqual(handler["timeout"], 8)
        self.assertEqual(handler["additionalContextLimit"], 500)
        self.assertNotIn("async", handler)

    def test_plugin_dispatcher_path_exists(self):
        handlers = json.loads((ROOT / "hooks/hooks.json").read_text())["hooks"]
        command = handlers["UserPromptSubmit"][0]["hooks"][0]["command"]
        self.assertIn('"${PLUGIN_ROOT}/hooks/dispatcher.py"', command)
        self.assertTrue((ROOT / "hooks/dispatcher.py").is_file())

    def test_manifest_does_not_introduce_unapproved_events(self):
        hooks = json.loads((ROOT / "hooks/hooks.json").read_text())["hooks"]
        self.assertEqual(set(hooks), {"UserPromptSubmit"})


if __name__ == "__main__":
    unittest.main()
