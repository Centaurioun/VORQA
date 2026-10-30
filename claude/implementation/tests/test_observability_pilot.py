"""Real controller, hook wrappers and HTTP/SQLite pilot acceptance tests."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/observability_pilot.py'


class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='vorqa-pilot-test-')
        cls.output=Path(cls.temp.name)/'report.json'
        cls.result=subprocess.run([sys.executable,str(SCRIPT),'--output',str(cls.output),'--no-browser'],
                                  cwd=ROOT,capture_output=True,text=True,timeout=70)
        cls.report=json.loads(cls.output.read_text()) if cls.output.exists() else {}

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_real_git_and_hook_decision_pilot(self):
        self.assertEqual(self.result.returncode,0,self.result.stdout+'\n'+self.result.stderr)
        report=self.report
        self.assertTrue(report['coverage']['complete'])
        self.assertEqual(report['kind'],'synthetic_hook_dispatch_real_git_controller')
        self.assertEqual(report['browser']['status'],'not_run')
        self.assertEqual(report['api']['status'],'passed')
        self.assertEqual([v['http_status'] for v in report['api']['cases']],[201,409,400])
        self.assertEqual(report['steps']['preapproval_write']['exit'],2)
        self.assertEqual(report['steps']['task_completed']['exit'],2)
        self.assertEqual(report['steps']['paused_stop']['exit'],0)
        self.assertEqual(report['steps']['verify_without_approval']['exit'],2)
        self.assertNotIn('SENSITIVE_FIXTURE_MARKER',self.output.read_text())

    def test_native_host_is_not_claimed(self):
        self.assertFalse(self.report['native_claude_verified'])
        self.assertEqual(self.report['browser']['status'],'not_run')


if __name__=='__main__':
    unittest.main()
