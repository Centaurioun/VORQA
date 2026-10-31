#!/usr/bin/env python3
"""Validate reported Codex skill-routing trials and local artifact integrity.

A matching local checksum is NOT proof that Codex actually selected the skill.
Native host events must be inspected separately by the operator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ALLOWED_CALLS = frozenset({'probe', 'status'})
ALLOWED_OUTCOMES = frozenset({'completed', 'blocked', 'error'})
ID = re.compile(r'^[a-z][a-z0-9-]{2,60}$')
SHA = re.compile(r'^[0-9a-f]{64}$')
MAX_EVIDENCE_BYTES = 5 * 1024 * 1024


def _catalog(catalog: dict) -> list[dict]:
    if not isinstance(catalog, dict) or catalog.get('schema_version') != 1 or catalog.get('plugin') != 'vorqa':
        raise ValueError('unsupported catalog schema')
    items = catalog.get('scenarios')
    if not isinstance(items, list) or not items:
        raise ValueError('catalog requires scenarios')
    ids = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not ID.fullmatch(item['id']):
            raise ValueError('invalid scenario id')
        if item['id'] in ids:
            raise ValueError('duplicate scenario id')
        ids.add(item['id'])
        if type(item.get('expected_activation')) is not bool:
            raise ValueError('expected_activation must be boolean')
        calls = item.get('expected_bridge_calls')
        if not isinstance(calls, list) or any(not isinstance(v, str) or v not in ALLOWED_CALLS for v in calls):
            raise ValueError('invalid expected bridge action')
        if len(calls) != len(set(calls)):
            raise ValueError('duplicate expected bridge action')
    return items


def _validate_observation(item: dict, known: set[str]):
    scenario_id = item.get('scenario_id') if isinstance(item, dict) else None
    if not isinstance(scenario_id, str) or scenario_id not in known:
        raise ValueError('unknown or invalid scenario id in observation')
    outcome = item.get('outcome')
    if not isinstance(outcome, str) or outcome not in ALLOWED_OUTCOMES:
        raise ValueError('invalid observation outcome')
    selected = item.get('selected_skill')
    if selected is not None and type(selected) is not bool:
        raise ValueError('selected_skill must be boolean or null')
    calls = item.get('bridge_calls')
    if not isinstance(calls, list) or any(not isinstance(v, str) or v not in ALLOWED_CALLS for v in calls):
        raise ValueError('unknown bridge action in observation')
    if outcome == 'completed' and selected is None:
        raise ValueError('completed observation requires boolean selected_skill')


def _valid_evidence(entry: dict, root: Path) -> bool:
    if not isinstance(entry, dict):
        return False
    name = entry.get('file')
    digest = entry.get('sha256')
    if not isinstance(name, str) or not name or not isinstance(digest, str) or not SHA.fullmatch(digest):
        return False
    path = Path(name)
    if path.is_absolute() or any(piece in {'.', '..'} for piece in path.parts):
        return False
    location = root / path
    if location.is_symlink():
        return False
    parent = root
    for piece in path.parts[:-1]:
        parent = parent / piece
        if parent.is_symlink():
            return False
    try:
        if not location.resolve().is_relative_to(root.resolve()) or not location.is_file():
            return False
        if location.stat().st_size <= 0 or location.stat().st_size > MAX_EVIDENCE_BYTES:
            return False
        return hashlib.sha256(location.read_bytes()).hexdigest() == digest
    except (OSError, ValueError):
        return False


def evaluate(catalog: dict, observations: dict, evidence_root: Path) -> dict:
    scenarios = _catalog(catalog)
    if not isinstance(observations, dict) or observations.get('schema_version') != 1:
        raise ValueError('unsupported observation schema')
    provided = observations.get('observations')
    if not isinstance(provided, list):
        raise ValueError('observations must be a list')
    allowed = {s['id'] for s in scenarios}
    lookup = {}
    for item in provided:
        _validate_observation(item, allowed)
        identifier = item['scenario_id']
        if identifier in lookup:
            raise ValueError('duplicate scenario observation')
        lookup[identifier] = item
    results=[]
    summary = {'pass': 0, 'fail': 0, 'blocked': 0, 'not_run': 0,
               'false_positive': 0, 'false_negative': 0}
    for scenario in scenarios:
        identifier = scenario['id']
        item = lookup.get(identifier)
        reason = 'unobserved'
        verdict = 'NOT_RUN'
        if item is not None:
            if item['outcome'] == 'blocked':
                verdict, reason = 'BLOCKED', 'host_blocked'
            elif item['outcome'] == 'error':
                verdict, reason = 'FAIL', 'host_error'
            elif not _valid_evidence(item.get('artifact'), evidence_root):
                verdict, reason = 'BLOCKED', 'invalid_evidence'
            else:
                actual_selected = item['selected_skill']
                actual_calls = item['bridge_calls']
                correct_activation = actual_selected == scenario['expected_activation']
                correct_calls = actual_calls == scenario['expected_bridge_calls']
                verdict = 'PASS' if correct_activation and correct_calls else 'FAIL'
                reason = 'reported_matching_observation' if verdict == 'PASS' else 'routing_mismatch'
                if not scenario['expected_activation'] and actual_selected:
                    summary['false_positive'] += 1
                if scenario['expected_activation'] and not actual_selected:
                    summary['false_negative'] += 1
        summary[verdict.lower()] += 1
        results.append({'scenario_id': identifier, 'category': scenario.get('category', 'unknown'),
                        'status': verdict, 'reason': reason})
    total = len(scenarios)
    return {'schema_version': 1, 'plugin': 'vorqa',
            'verdict': 'REPORTED_PASS' if summary['pass'] == total else
                      'REPORTED_FAIL' if summary['fail'] else 'INCOMPLETE',
            'evidence_level': 'self_reported_artifact_checksum_only',
            'note': 'Artifacts are hash-checked; plugin selection and host identity are NOT independently attested.',
            'summary': summary, 'total_scenarios': total, 'results': results}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog', type=Path, default=Path(__file__).with_name('scenarios.json'))
    p.add_argument('--observations', required=True, type=Path)
    p.add_argument('--evidence-root', required=True, type=Path)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    try:
        result = evaluate(json.loads(args.catalog.read_text()),
                          json.loads(args.observations.read_text()), args.evidence_root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        # Deliberately avoid printing exception text, which can contain local paths.
        print(json.dumps({'verdict': 'INVALID_INPUT', 'error_type': type(error).__name__}))
        return 2
    rendered = json.dumps(result, indent=2, sort_keys=True) + '\n'
    print(rendered, end='')
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    return 0 if result['verdict'] == 'REPORTED_PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
