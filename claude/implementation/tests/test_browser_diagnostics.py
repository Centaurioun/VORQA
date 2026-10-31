"""Browser diagnostic policy used by live scenario checks."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'browser_checks.py'
spec = importlib.util.spec_from_file_location('browser_checks', SCRIPT)
browser_checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(browser_checks)


class BrowserDiagnosticsTests(unittest.TestCase):
    def test_empty_diagnostics_are_accepted(self):
        self.assertFalse(browser_checks.browser_diagnostics_failed({
            'console_errors': [], 'page_errors': [],
            'failed_requests': [], 'server_errors': [],
        }))

    def test_each_browser_error_category_fails(self):
        for category in ('console_errors', 'page_errors', 'failed_requests', 'server_errors'):
            with self.subTest(category=category):
                self.assertTrue(browser_checks.browser_diagnostics_failed({
                    'console_errors': [1] if category == 'console_errors' else [],
                    'page_errors': [1] if category == 'page_errors' else [],
                    'failed_requests': [1] if category == 'failed_requests' else [],
                    'server_errors': [1] if category == 'server_errors' else [],
                }))

    def test_safe_summary_excludes_error_text_and_urls(self):
        diagnostics = {
            'console_errors': ['secret-token'], 'page_errors': ['private text'],
            'failed_requests': [{'url': 'https://example.test/?token=secret'}],
            'server_errors': [{'status': 503, 'url': 'http://127.0.0.1/?email=private'}],
            'blocked_external_requests': ['https://example.test/?key=secret'],
        }
        summary = browser_checks.safe_browser_summary(diagnostics)
        self.assertEqual(summary, {
            'console_errors': 1, 'page_errors': 1, 'failed_requests': 1,
            'server_error_statuses': [503], 'blocked_external_requests': 1,
        })
        self.assertNotIn('secret', repr(summary))
        self.assertNotIn('private', repr(summary))


class BrowserFailureEvidenceTests(unittest.TestCase):
    """A failed scenario must still leave inspectable diagnostic metadata."""

    def test_invalid_action_writes_diagnostic_and_step_index(self):
        import json
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scenario = root / 'invalid-action.json'
            scenario.write_text(json.dumps({
                'base_url': 'http://127.0.0.1:8765',
                'actions': [{'unsupported_action': 'do not publish this input'}],
            }))
            with patch.object(browser_checks, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'Unknown browser action'):
                    browser_checks.run_scenario(scenario, 'failure-fixture')
            diagnostic = root / '.avrl/browser-evidence/failure-fixture/diagnostics-invalid-action.json'
            self.assertTrue(diagnostic.is_file(), 'No diagnostic written when scenario failed')
            data = json.loads(diagnostic.read_text())
            self.assertEqual(data['execution_failure']['category'], 'ValueError')
            self.assertEqual(data['execution_failure']['step_index'], 0)
            self.assertNotIn('do not publish this input', diagnostic.read_text())

    def test_browser_start_failure_writes_safe_diagnostic(self):
        import json
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scenario = root / 'startup.json'
            scenario.write_text(json.dumps({
                'base_url': 'http://127.0.0.1:8765', 'actions': [],
            }))
            with patch.object(browser_checks, 'ROOT', root):
                with patch('browser_runtime.launch_chromium',
                           side_effect=RuntimeError('SECRET_MARKER browser launch error')):
                    with self.assertRaisesRegex(RuntimeError, 'SECRET_MARKER'):
                        browser_checks.run_scenario(scenario, 'failure-fixture')
            diagnostic = root / '.avrl/browser-evidence/failure-fixture/diagnostics-startup.json'
            self.assertTrue(diagnostic.is_file(), 'No diagnostic written when browser launch failed')
            data = json.loads(diagnostic.read_text())
            self.assertEqual(data['execution_failure']['category'], 'RuntimeError')
            self.assertIsNone(data['execution_failure']['step_index'])
            self.assertNotIn('SECRET_MARKER', diagnostic.read_text())

if __name__ == '__main__':
    unittest.main()
