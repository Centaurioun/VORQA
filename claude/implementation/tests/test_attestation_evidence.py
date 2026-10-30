"""Commit-bound review and browser receipt regression tests.

These tests enforce *local integrity*, not reviewer/approver identity.
"""
from __future__ import annotations

from contextlib import ExitStack, nullcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'avrl.py'
spec = importlib.util.spec_from_file_location('avrl_attestation_test', MODULE_PATH)
avrl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(avrl)

COMMIT = 'a' * 40
DIGEST = 'b' * 64


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.runtime = self.root / '.avrl'
        self.runtime.mkdir()
        self.state = {
            'feature': 'example-signup', 'risk': 'medium', 'status': 'reviewing',
            'round': 1, 'eval_digest': DIGEST, 'verification_nonce': '11111111111111111111111111111111', 'checks': {
                'EVAL-01': {'status': 'PASS', 'commit': COMMIT, 'eval_digest': DIGEST,
                            'evidence': '.avrl/evidence/example-signup/check.log', 'sha256': 'to-be-set'}},
            'review_pass': False, 'blind_qa_pass': False,
        }
        log = self.runtime / 'evidence' / 'example-signup' / 'check.log'
        log.parent.mkdir(parents=True)
        log.write_text('PASS')
        self.state['checks']['EVAL-01']['sha256'] = hashlib.sha256(log.read_bytes()).hexdigest()
        self.ctx = ExitStack()
        self.addCleanup(self.ctx.close)
        for name, value in (
            ('ROOT', self.root), ('RUNTIME', self.runtime),
            ('locked', lambda slug: nullcontext()), ('load', lambda slug: self.state),
            ('save', lambda slug, state, event: None),
            ('git', lambda *args: COMMIT), ('assert_clean', lambda: None),
            ('assert_git_branch', lambda slug: None), ('approval_valid', lambda *args: True),
            ('criteria', lambda slug: [{'id': 'EVAL-01'}]),
            ('release_valid', lambda *args: True),
        ):
            self.ctx.enter_context(patch.object(avrl, name, value))

    def review_report(self, **changes):
        path = self.runtime / 'review' / 'example-signup' / 'review.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        report = {'schema_version': 1, 'feature': 'example-signup', 'commit': COMMIT,
                  'eval_digest': DIGEST, 'round': 1, 'verdict': 'pass',
                  'verification_nonce': '11111111111111111111111111111111',
                  'reviewer': 'independent-reviewer', 'summary': 'Checked edge cases and feature diff.',
                  'reviewed_files': ['example_app/index.html'], 'findings': []}
        report.update(changes)
        path.write_text(json.dumps(report))
        return '.avrl/review/example-signup/review.json'

    def call_review(self, evidence=None):
        return avrl.cmd_review(SimpleNamespace(feature='example-signup', result='pass',
                                                evidence=evidence, finding_class=None, fingerprint=None))

    def test_review_pass_requires_report(self):
        with self.assertRaisesRegex(ValueError, 'evidence'):
            self.call_review()
        self.assertFalse(self.state['review_pass'])

    def test_review_rejects_stale_commit_and_contract(self):
        for changes in ({'commit': 'c'*40}, {'eval_digest': 'd'*64}, {'round': 2}, {'verification_nonce': 'old-nonce'},
                        {'findings': ['unresolved finding']}, {'reviewed_files': []}):
            with self.subTest(changes=changes):
                path = self.review_report(**changes)
                with self.assertRaises(ValueError):
                    self.call_review(path)
                self.assertFalse(self.state['review_pass'])

    def test_review_receipt_detects_tampering(self):
        path = self.review_report()
        self.call_review(path)
        self.assertTrue(self.state['review_pass'])
        self.assertTrue(avrl.final_evidence_valid('example-signup', self.state) is False)  # QA not signed
        file = self.root / path
        file.write_text(file.read_text().replace('independent-reviewer', 'forged-reviewer'))
        self.assertFalse(avrl.review_evidence_valid('example-signup', self.state, COMMIT))

    def qa_events(self, *, modified=None):
        folder = self.runtime / 'blind'
        folder.mkdir(parents=True, exist_ok=True)
        events = []
        for index, command in enumerate(['inspect', 'fill-label', 'click-role']):
            file = folder / f'event-{index}.png'
            file.write_bytes(f'image-{index}'.encode())
            events.append({'at': '2026-10-30T19:00:00+00:00', 'command': command,
                           'feature': 'example-signup', 'commit': COMMIT, 'round': 1, 'eval_digest': DIGEST,
                           'verification_nonce': '11111111111111111111111111111111',
                           'url': 'http://127.0.0.1:8765/signup',
                           'capture': f'.avrl/blind/event-{index}.png',
                           'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
        if modified:
            modified(events)
        (folder / 'events.jsonl').write_text('\n'.join(json.dumps(e) for e in events)+'\n')
        return '.avrl/blind/event-2.png'

    def call_blind(self, evidence):
        self.state['review_pass'] = True
        self.state['review_evidence'] = {'evidence': self.review_report(),
                                         'sha256': hashlib.sha256((self.runtime/'review'/'example-signup'/'review.json').read_bytes()).hexdigest()}
        return avrl.cmd_blind(SimpleNamespace(feature='example-signup', result='pass', evidence=evidence))

    def test_blind_rejects_event_commit_or_digest_mismatch(self):
        for key, value in [('commit', 'c'*40), ('eval_digest', 'd'*64), ('feature', 'other'), ('verification_nonce', 'old-nonce')]:
            with self.subTest(key=key):
                screenshot = self.qa_events(modified=lambda ev: ev[1].update({key:value}))
                with self.assertRaises(ValueError):
                    self.call_blind(screenshot)
                self.assertFalse(self.state['blind_qa_pass'])

    def test_blind_rejects_modified_screenshot_and_fake_events(self):
        screenshot = self.qa_events()
        (self.runtime/'blind'/'event-0.png').write_bytes(b'tampered')
        with self.assertRaises(ValueError):
            self.call_blind(screenshot)
        self.assertFalse(self.state['blind_qa_pass'])

    def test_blind_rejects_external_or_duplicate_capture(self):
        for altered in (
            lambda events: events[0].update({'url': 'https://attacker.example/collect'}),
            lambda events: events[1].update({'capture': events[0]['capture']}),
            lambda events: events[0].update({'round': 2}),
            lambda events: events[1].update({'url': 'http://127.0.0.1:8777/signup'}),
        ):
            with self.subTest(altered=altered):
                screenshot = self.qa_events(modified=altered)
                with self.assertRaises(ValueError):
                    self.call_blind(screenshot)

    def test_completion_requires_untampered_review_and_qa_receipts(self):
        self.state['review_pass'] = True
        self.state['blind_qa_pass'] = True
        self.assertFalse(avrl.final_evidence_valid('example-signup', self.state))
        self.call_blind(self.qa_events())
        self.assertTrue(avrl.final_evidence_valid('example-signup', self.state))
        (self.runtime/'review'/'example-signup'/'review.json').write_text('{}')
        self.assertFalse(avrl.final_evidence_valid('example-signup', self.state))

    def test_blind_receipt_invalidated_by_event_tampering(self):
        screenshot = self.qa_events()
        self.call_blind(screenshot)
        self.assertTrue(self.state['blind_qa_pass'])
        self.assertTrue(avrl.blind_evidence_valid('example-signup', self.state, COMMIT))
        events = self.runtime/'blind'/'events.jsonl'
        events.write_text(events.read_text().replace('fill-label', 'open'))
        self.assertFalse(avrl.blind_evidence_valid('example-signup', self.state, COMMIT))


if __name__ == '__main__':
    unittest.main()
