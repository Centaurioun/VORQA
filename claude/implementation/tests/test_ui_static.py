"""Static browser rendering and no-network validation smoke tests.

Passing these tests NEVER substitutes for the live loopback E2E acceptance criteria.
"""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))


class StaticChromiumChecks(unittest.TestCase):
    def test_invalid_signup_shows_accessible_error(self):
        try:
            from playwright.sync_api import sync_playwright
            from browser_runtime import launch_chromium
        except ImportError:
            self.skipTest('Playwright not installed (live eval still requires it)')
        with sync_playwright() as p:
            browser=launch_chromium(p)
            page=browser.new_page(viewport={'width':390,'height':844})
            page.set_content((ROOT/'example_app'/'index.html').read_text())
            page.locator('#name').fill('Test User')
            page.locator('#email').fill('bad-email')
            page.locator('#create').click()
            self.assertIn('Enter a valid name and email',page.locator('[role=status]').inner_text())
            self.assertEqual(page.locator('label[for=email]').count(),1)
            browser.close()


if __name__=='__main__':unittest.main()
