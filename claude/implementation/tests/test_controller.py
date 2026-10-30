"""End-to-end controller negative-gate test on a disposable Git repository."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


def command(root,*args):
    return subprocess.run(args,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})


class ControllerGitGates(unittest.TestCase):
    def test_status_and_unapproved_execution_denied(self):
        with tempfile.TemporaryDirectory(prefix='avrl-git-smoke-') as tmp:
            repo=Path(tmp)/'repo'
            shutil.copytree(ROOT,repo,ignore=shutil.ignore_patterns('.avrl','.git','__pycache__','*.pyc'))
            for args in [('init',),('config','user.email','ci@example.test'),('config','user.name','CI')]:
                self.assertEqual(command(repo,'git',*args).returncode,0)
            self.assertEqual(command(repo,'git','add','.').returncode,0)
            res=command(repo,'git','commit','-m','template')
            self.assertEqual(res.returncode,0,res.stderr)
            self.assertEqual(command(repo,'git','switch','-c','feature/example-signup').returncode,0)
            script=str(repo/'scripts'/'avrl.py')
            res=command(repo,sys.executable,script,'init','example-signup','--risk','medium')
            self.assertEqual(res.returncode,0,res.stderr)
            state=json.loads((repo/'.avrl'/'state'/'example-signup.json').read_text())
            self.assertEqual(state['status'],'in-review')
            for action in [('round','example-signup'),('verify','example-signup'),('complete','example-signup'),('approve','example-signup','--actor','forged')]:
                with self.subTest(action=action):
                    res=command(repo,sys.executable,script,*action)
                    self.assertNotEqual(res.returncode,0,res.stdout)
            hook=repo/'.claude'/'hooks'/'enforce-eval-pass.sh'
            res=subprocess.run(['bash',str(hook)],input=json.dumps({'hook_event_name':'TaskCompleted'}),cwd=repo,capture_output=True,text=True)
            self.assertEqual(res.returncode,2)
            self.assertEqual(json.loads((repo/'.avrl'/'state'/'example-signup.json').read_text())['status'],'in-review')


if __name__=='__main__':unittest.main()
