"""Regress metadata-only hook, state and coverage evidence."""
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
HOOK=ROOT/'.claude/hooks/hook_logic.py'
SCRIPT=ROOT/'scripts/trace_events.py'
spec=importlib.util.spec_from_file_location('vorqa_trace',SCRIPT)
trace=importlib.util.module_from_spec(spec)
spec.loader.exec_module(trace)


class TraceUnitTests(unittest.TestCase):
    def test_writer_never_serializes_secrets_or_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'trace.jsonl'
            trace.append(target,kind='hook',event='PreToolUse',handler='code',decision='blocked',
                         feature='example-signup',reason='approval_required',tool_name='Bash',
                         input_payload={'command':'export API_TOKEN=SECRET_X'},session='SESSION_SECRET')
            raw=target.read_text()
            self.assertNotIn('SECRET_X',raw)
            self.assertNotIn('SESSION_SECRET',raw)
            saved=json.loads(raw)
            self.assertEqual(saved['decision'],'blocked')
            self.assertEqual(saved['event'],'PreToolUse')

    def test_trace_matrix_rejects_missing_observations(self):
        records=[{'kind':'hook','event':'PreToolUse','decision':'blocked','origin':'synthetic'}]
        coverage=trace.coverage(records,[{'kind':'hook','event':'PreToolUse','decision':'blocked'},
                                         {'kind':'hook','event':'TaskCompleted','decision':'blocked'}])
        self.assertFalse(coverage['complete'])
        self.assertEqual(coverage['missing'][0]['event'],'TaskCompleted')

    def test_native_claim_not_supported_by_synthetic_trace(self):
        records=[{'kind':'hook','event':'PreToolUse','origin':'synthetic','decision':'allowed'}]
        self.assertFalse(trace.coverage(records,[{'kind':'hook','event':'PreToolUse','origin':'native'}])['complete'])

    def test_report_rejects_malformed_jsonl(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'trace.jsonl'
            path.write_text('{bad\n')
            with self.assertRaises(ValueError):
                trace.read(path)


class TraceHookTests(unittest.TestCase):
    def test_denied_hook_and_failed_tool_are_traced_without_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            import os
            target=Path(temp)/'trace.jsonl'
            env={**os.environ,'VORQA_TRACE_FILE':str(target),'VORQA_TRACE_ORIGIN':'synthetic'}
            event={'hook_event_name':'PreToolUse','agent_type':'blind-qa','tool_name':'Bash',
                   'tool_input':{'command':'echo SECRET_X'}}
            p=subprocess.run([sys.executable,str(HOOK),'blind'],input=json.dumps(event),text=True,capture_output=True,
                             cwd=ROOT,env=env)
            self.assertEqual(p.returncode,2)
            self.assertTrue(target.exists())
            records=trace.read(target)
            self.assertEqual(records[0]['decision'],'blocked')
            self.assertNotIn('SECRET_X',target.read_text())
            failed={'hook_event_name':'PostToolUseFailure','tool_name':'Bash','tool_input':{'command':'SECRET_X'}}
            p=subprocess.run([sys.executable,str(HOOK),'audit'],input=json.dumps(failed),text=True,capture_output=True,
                             cwd=ROOT,env=env)
            self.assertEqual(p.returncode,0)
            self.assertEqual(trace.read(target)[-1]['decision'],'observed_failure')


class TraceControllerTests(unittest.TestCase):
    def test_controller_records_status_transitions_without_reason(self):
        spec=importlib.util.spec_from_file_location('controller_trace_test',ROOT/'scripts/avrl.py')
        controller=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(controller)
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            runtime=folder/'.avrl'
            (folder/'specs/example-signup').mkdir(parents=True)
            state={'feature':'example-signup','status':'in-review','risk':'medium','round':0,'max_rounds':3,
                   'events':[],'checks':{},'reason':None}
            with patch.object(controller,'ROOT',folder),patch.object(controller,'RUNTIME',runtime):
                controller.save('example-signup',state,'initialized; awaiting human approval')
                state['status']='paused'
                state['reason']='SECRET_X private reason'
                controller.save('example-signup',state,'paused: SECRET_X private reason')
                records=trace.read(runtime/'trace.jsonl')
                self.assertEqual(len(records),2)
                self.assertEqual(records[0]['from_status'],'none')
                self.assertEqual(records[0]['to_status'],'in-review')
                self.assertEqual(records[1]['from_status'],'in-review')
                self.assertEqual(records[1]['to_status'],'paused')
                self.assertNotIn('SECRET_X',(runtime/'trace.jsonl').read_text())


class TraceSettingsTests(unittest.TestCase):
    def test_config_registers_lifecycle_and_failure_events(self):
        data=json.loads((ROOT/'.claude/settings.json').read_text())['hooks']
        for name in ('PreToolUse','PostToolUse','PostToolUseFailure','SessionStart',
                     'SubagentStart','SubagentStop','Stop','TaskCompleted',
                     'PermissionRequest','PermissionDenied','SessionEnd','StopFailure'):
            with self.subTest(event=name):
                self.assertIn(name,data)
                self.assertTrue(data[name])


if __name__=='__main__':
    unittest.main()


class TraceCriterionTests(unittest.TestCase):
    def test_controller_logs_individual_criterion_results(self):
        spec=importlib.util.spec_from_file_location('controller_criterion_test',ROOT/'scripts/avrl.py')
        controller=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(controller)
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            runtime=folder/'.avrl'
            (folder/'specs/example-signup').mkdir(parents=True)
            state={'feature':'example-signup','status':'reviewing','risk':'medium','round':1,'max_rounds':3,
                   'events':[],'checks':{'UNIT':{'status':'PASS'},'BROWSER':{'status':'FAIL'}},'reason':None}
            with patch.object(controller,'ROOT',folder),patch.object(controller,'RUNTIME',runtime):
                controller.save('example-signup',state,'verification: 1/2')
            rows=trace.read(runtime/'trace.jsonl')
            found={(r.get('criterion'),r.get('outcome')) for r in rows if r.get('event')=='criterion'}
            self.assertEqual(found,{('UNIT','pass'),('BROWSER','fail')})

    def test_agent_type_is_redacted_when_untrusted(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'trace.jsonl'
            trace.append(target,kind='hook',event='SubagentStart',agent_type='SECRET sensitive agent text')
            self.assertEqual(trace.read(target)[0]['agent_type'],'redacted')
