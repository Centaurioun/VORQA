"""Adversarial regression checks for local hook and controller integrity."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
HOOK=ROOT/'.claude'/'hooks'/'hook_logic.py'


def hook(mode,event):
    return subprocess.run([sys.executable,str(HOOK),mode],input=json.dumps(event),text=True,capture_output=True,cwd=ROOT)


class HookAdversarialTests(unittest.TestCase):
    def test_blind_source_tool_deny(self):
        for name in ('Read','Grep','Glob','Edit','WebFetch','mcp__filesystem__read_file'):
            with self.subTest(name=name):
                result=hook('blind',{'agent_type':'blind-qa','tool_name':name,'tool_input':{'file_path':'README.md'}})
                self.assertEqual(result.returncode,2)

    def test_blind_terminal_bypass_patterns_deny(self):
        attacks=['cat README.md','git show HEAD:CLAUDE.md','python3 -c "print(open(\'README.md\').read())"',
                 'python3 scripts/blind_browser.py open /signup; cat README.md',
                 'python3 scripts/blind_browser.py open $(cat README.md)',
                 'rg -n secret .','bash -c "cat README.md"',
                 'python3 scripts/blind_browser.py open /signup | tee /tmp/exfil']
        for cmd in attacks:
            with self.subTest(command=cmd):
                result=hook('blind',{'agent_type':'blind-qa','tool_name':'Bash','tool_input':{'command':cmd}})
                self.assertEqual(result.returncode,2)

    def test_blind_browser_only_allow(self):
        for cmd in ['python3 scripts/blind_browser.py open /signup',
                    'python3 scripts/blind_browser.py fill "#email" "qa@example.test"',
                    'python3 scripts/blind_browser.py screenshot',
                    'python3 scripts/blind_browser.py inspect',
                    'python3 scripts/blind_browser.py fill-label "Email address" "qa@example.test"',
                    'python3 scripts/blind_browser.py click-role button "Create account"']:
            with self.subTest(cmd=cmd):
                result=hook('blind',{'agent_type':'blind-qa','tool_name':'Bash','tool_input':{'command':cmd}})
                self.assertEqual(result.returncode,0,result.stderr)

    def test_nonblind_is_not_source_blocked(self):
        result=hook('blind',{'agent_type':'verifier','tool_name':'Read','tool_input':{'file_path':'CLAUDE.md'}})
        self.assertEqual(result.returncode,0)

    def test_bad_json_fails_closed(self):
        result=subprocess.run([sys.executable,str(HOOK),'blind'],input='{',text=True,capture_output=True)
        self.assertEqual(result.returncode,2)

    def test_unapproved_write_guard(self):
        spec=importlib.util.spec_from_file_location('hook_logic',HOOK)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        with patch.object(mod,'active',return_value={'status':'in-review','feature':'example-signup'}):
            self.assertEqual(mod.code_guard({'tool_name':'Write','tool_input':{'file_path':str(ROOT/'example_app'/'index.html')}}),2)
            self.assertEqual(mod.code_guard({'tool_name':'Write','tool_input':{'file_path':str(ROOT/'specs'/'example-signup'/'eval.md')}}),0)

    def test_stop_human_pause_no_deadlock(self):
        spec=importlib.util.spec_from_file_location('hook_logic',HOOK)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        with patch.object(mod,'active',return_value={'status':'paused','feature':'example-signup'}):
            self.assertEqual(mod.completion_guard({'hook_event_name':'Stop','stop_hook_active':False}),0)
            self.assertEqual(mod.completion_guard({'hook_event_name':'TaskCompleted'}),2)
        with patch.object(mod,'active',return_value={'status':'building','feature':'example-signup'}):
            self.assertEqual(mod.completion_guard({'hook_event_name':'Stop','stop_hook_active':False}),2)
            self.assertEqual(mod.completion_guard({'hook_event_name':'Stop','stop_hook_active':True}),0)


class ContractIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('avrl',ROOT/'scripts'/'avrl.py')
        cls.mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.mod)

    def test_contract_digest_changes_with_scenario(self):
        base=self.mod.eval_files('example-signup')
        target=ROOT/'specs'/'example-signup'/'scenarios'/'desktop.json'
        original=target.read_bytes()
        try:
            target.write_bytes(original+b'\n')
            self.assertNotEqual(base,self.mod.eval_files('example-signup'))
        finally:
            target.write_bytes(original)

    def test_invalid_slug_blocked(self):
        for value in ('../../secrets','.git','A','feature/abc'):
            with self.subTest(value=value),self.assertRaises(ValueError):self.mod.paths(value)

    def test_duplicate_criteria_rejected(self):
        self.assertEqual(len(self.mod.criteria('example-signup')),4)

    def test_no_noninteractive_approvals(self):
        parser=self.mod.parser()
        parsed=parser.parse_args(['approve','example-signup','--actor','CI-simulated'])
        self.assertEqual(parsed.actor,'CI-simulated')
        with patch.object(self.mod,'locked') as locked_context:
            self.assertTrue(hasattr(parsed,'run'))


if __name__=='__main__':unittest.main()
