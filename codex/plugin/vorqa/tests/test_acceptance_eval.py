"""Test real evidence handling for Codex activation acceptance (no Codex host required)."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'eval'))
import acceptance_eval as evaluator


class EvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'eval/scenarios.json').read_text())

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def observation(self, scenario, selected, calls, *, state='completed', proof=True):
        content = f'REDACTED CODEX SESSION EVIDENCE: {scenario}\n'.encode()
        path = self.root / f'{scenario}.log'
        path.write_bytes(content)
        return {'scenario_id': scenario, 'outcome': state,
                'selected_skill': selected, 'bridge_calls': calls,
                'artifact': {'file': path.name, 'sha256': hashlib.sha256(content).hexdigest()}} if proof else {
                'scenario_id': scenario, 'outcome': state, 'selected_skill': selected, 'bridge_calls': calls}

    def test_missing_observations_does_not_pass_or_invent_native_evidence(self):
        result = evaluator.evaluate(self.catalog, {'schema_version': 1, 'observations': []}, self.root)
        self.assertEqual(result['summary']['not_run'], 10)
        self.assertEqual(result['verdict'], 'INCOMPLETE')
        self.assertNotIn('native_verified', json.dumps(result).lower())

    def test_positive_and_negative_routing_require_matching_evidence(self):
        records = [self.observation(s['id'], s['expected_activation'], s['expected_bridge_calls']) for s in self.catalog['scenarios']]
        outcome = evaluator.evaluate(self.catalog, {'schema_version': 1, 'observations': records}, self.root)
        self.assertEqual(outcome['verdict'], 'REPORTED_PASS')
        self.assertEqual(outcome['summary']['pass'], 10)
        self.assertEqual(outcome['summary']['false_positive'], 0)
        self.assertEqual(outcome['summary']['false_negative'], 0)
        self.assertEqual(outcome['evidence_level'], 'self_reported_artifact_checksum_only')

    def test_negative_false_activation_and_positive_miss_fail(self):
        records = [self.observation('nonsoftware-question', True, ['probe']),
                   self.observation('explicit-probe-existing', False, [])]
        outcome = evaluator.evaluate(self.catalog, {'schema_version': 1, 'observations': records}, self.root)
        self.assertEqual(outcome['summary']['fail'], 2)
        self.assertEqual(outcome['summary']['false_positive'], 1)
        self.assertEqual(outcome['summary']['false_negative'], 1)

    def test_missing_or_modified_artifact_cannot_pass(self):
        s=self.catalog['scenarios'][0]
        a=self.observation(s['id'], True, ['probe'])
        (self.root/a['artifact']['file']).write_text('modified evidence')
        outcome=evaluator.evaluate(self.catalog,{'schema_version':1,'observations':[a]},self.root)
        self.assertEqual(outcome['results'][0]['status'],'BLOCKED')
        self.assertEqual(outcome['results'][0]['reason'],'invalid_evidence')

    def test_symlink_escape_is_rejected(self):
        s=self.catalog['scenarios'][0]
        a=self.observation(s['id'],True,['probe'])
        with tempfile.TemporaryDirectory() as other:
            p=Path(other)/'proof.txt'
            p.write_text('outside')
            link=self.root/'linked.log'
            link.symlink_to(p)
            a['artifact']={'file':'linked.log','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            result=evaluator.evaluate(self.catalog,{'schema_version':1,'observations':[a]},self.root)
            self.assertEqual(result['results'][0]['status'],'BLOCKED')

    def test_duplicate_unknown_or_malformed_observation_fails_closed(self):
        a=self.observation('explicit-probe-existing',True,['probe'])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            evaluator.evaluate(self.catalog,{'schema_version':1,'observations':[a,a]},self.root)
        with self.assertRaisesRegex(ValueError, 'unknown'):
            evaluator.evaluate(self.catalog,{'schema_version':1,'observations':[self.observation('fake-id',False,[])]},self.root)
        with self.assertRaisesRegex(ValueError, 'boolean'):
            evaluator.evaluate(self.catalog,{'schema_version':1,'observations':[{'scenario_id':'explicit-probe-existing','outcome':'completed','selected_skill':'yes','bridge_calls':[]}]},self.root)

    def test_blocked_execution_not_counted_as_false_negative(self):
        a=self.observation('explicit-probe-existing',None,[],state='blocked',proof=False)
        result=evaluator.evaluate(self.catalog,{'schema_version':1,'observations':[a]},self.root)
        self.assertEqual(result['results'][0]['status'],'BLOCKED')
        self.assertEqual(result['summary']['false_negative'],0)

    def test_report_does_not_copy_raw_prompts_or_local_paths(self):
        a=self.observation('explicit-probe-existing', True,['probe'])
        result=evaluator.evaluate(self.catalog,{'schema_version':1,'observations':[a]},self.root)
        body=json.dumps(result)
        self.assertNotIn(str(self.root),body)
        self.assertNotIn('Suggest a simple vegetarian dinner',body)
        self.assertNotIn('REDACTED CODEX SESSION EVIDENCE',body)

    def test_catalog_rejects_duplicate_ids_and_unknown_calls(self):
        catalog=json.loads(json.dumps(self.catalog))
        catalog['scenarios'].append(catalog['scenarios'][0])
        with self.assertRaisesRegex(ValueError,'duplicate'):
            evaluator.evaluate(catalog,{'schema_version':1,'observations':[]},self.root)
        catalog=json.loads(json.dumps(self.catalog))
        catalog['scenarios'][0]['expected_bridge_calls']=['shell-init']
        with self.assertRaisesRegex(ValueError,'action'):
            evaluator.evaluate(catalog,{'schema_version':1,'observations':[]},self.root)


if __name__ == '__main__':
    unittest.main()
