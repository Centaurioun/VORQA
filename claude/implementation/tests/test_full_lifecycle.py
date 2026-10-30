"""End-to-end controller pilot tests (disposable repo only)."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts'/'full_lifecycle_pilot.py'

class FullLifecycleTests(unittest.TestCase):
    def test_clean_positive_path_and_stale_evidence_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'summary.json'
            p=subprocess.run([sys.executable,str(SCRIPT),'--mode','fixture','--output',str(target)],
                             cwd=ROOT,capture_output=True,text=True,timeout=130)
            self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
            report=json.loads(target.read_text())
            self.assertEqual(report['status'],'passed')
            self.assertFalse(report['native_claude_verified'])
            self.assertEqual(report['qa_mode'],'synthetic-fixture')
            self.assertEqual(report['stages'],['init','approve','round','verify','review','blind','release-attest','complete'])
            self.assertTrue(report['guards']['completed_stop_allowed'])
            self.assertTrue(report['guards']['tampered_review_denied'])
            self.assertEqual(report['coverage']['expected'],8)
            self.assertEqual(report['coverage']['observed'],8)

if __name__=='__main__': unittest.main()
