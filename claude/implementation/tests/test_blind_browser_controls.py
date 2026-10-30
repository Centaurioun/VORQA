"""Black-box UI discovery and egress-denial regression tests.

Static in-memory pages only: no live server or Claude Code host is assumed.
"""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


class BlindBrowserControlsTests(unittest.TestCase):
    def setUp(self):
        try:
            from playwright.sync_api import sync_playwright
            from browser_runtime import launch_chromium
        except ImportError:
            self.skipTest('Playwright unavailable; browser behavior unverified')
        self.p = sync_playwright().start()
        self.browser = launch_chromium(self.p)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.addCleanup(self.p.stop)
        self.addCleanup(self.browser.close)

    def test_controls_discovered_without_source_or_values(self):
        from blind_browser import snapshot_controls
        self.page.set_content('''
          <label for="email">Email address</label><input id="email" value="private@invalid.test" />
          <label for="pwd">Password</label><input id="pwd" type="password" value="secret-123" />
          <button>Create account</button>
          <a href="/help">Help</a>
          <div hidden><button id="hidden-button">Hidden</button></div>
        ''')
        results = snapshot_controls(self.page)
        self.assertEqual([r['name'] for r in results], ['Email address', 'Password', 'Create account', 'Help'])
        self.assertEqual(results[0]['selector'], '#email')
        self.assertEqual(results[1]['type'], 'password')
        self.assertNotIn('private@invalid.test', str(results))
        self.assertNotIn('secret-123', str(results))

    def test_accessible_role_and_label_actions(self):
        from blind_browser import act_on_control
        self.page.set_content('''
          <label>Email address<input type="email" /></label>
          <button type="button" onclick="document.body.dataset.clicked='yes'">Create account</button>
        ''')
        act_on_control(self.page, 'fill-label', ['Email address', 'qa@example.test'])
        self.assertEqual(self.page.get_by_label('Email address').input_value(), 'qa@example.test')
        act_on_control(self.page, 'click-role', ['button', 'Create account'])
        self.assertEqual(self.page.locator('body').get_attribute('data-clicked'), 'yes')

    def test_external_requests_are_blocked_and_recorded(self):
        from blind_browser import attach_network_guard
        blocked = attach_network_guard(self.context, 'http://127.0.0.1:8765')
        self.page.set_content('<img src="https://example.org/track.png">')
        self.page.wait_for_timeout(100)
        self.assertEqual(len(blocked), 1)
        self.assertIn('example.org', blocked[0])

    def test_sensitive_inputs_not_persisted(self):
        from blind_browser import snapshot_session_fields
        self.page.set_content('''
          <input id="name" value="Test Person" />
          <input id="pwd" type="password" value="dont-save-me" />
          <input id="key" name="access_token" value="dont-save-token" />
          <input id="otp" autocomplete="one-time-code" value="123456" />
        ''')
        result = snapshot_session_fields(self.page)
        self.assertEqual(result, [{'id': 'name', 'value': 'Test Person'}])


if __name__ == '__main__':
    unittest.main()
