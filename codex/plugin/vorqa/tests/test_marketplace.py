"""Repository marketplace is discoverable but never force-installs VORQA."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[4]


class MarketplaceTests(unittest.TestCase):
    def test_marketplace_points_to_plugin_without_installing_it(self):
        marketplace = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text())
        self.assertEqual(marketplace['name'], 'vorqa-local')
        plugins = marketplace['plugins']
        self.assertEqual(len(plugins), 1)
        entry = plugins[0]
        self.assertEqual(entry['name'], 'vorqa')
        self.assertEqual(entry['source'], {'source': 'local', 'path': './codex/plugin/vorqa'})
        self.assertEqual(entry['policy']['installation'], 'AVAILABLE')
        self.assertEqual(entry['policy']['authentication'], 'ON_INSTALL')
        self.assertEqual(entry['category'], 'Productivity')
        self.assertTrue((ROOT / entry['source']['path'] / 'plugin.json').is_file())

    def test_marketplace_does_not_change_local_codex_settings(self):
        # The test package may provide a marketplace, but not a forced
        # installation, machine policy, or repo-local plugin-enable setting.
        self.assertFalse((ROOT / '.codex/config.toml').is_file())


if __name__ == '__main__':
    unittest.main()
