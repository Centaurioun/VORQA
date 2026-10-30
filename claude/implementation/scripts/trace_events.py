#!/usr/bin/env python3
"""Metadata-only AVRL event recorder and coverage report (not agent reasoning)."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re

FIELDS = {'kind', 'event', 'handler', 'decision', 'reason', 'feature',
          'tool_name', 'origin', 'from_status', 'to_status', 'action',
          'criterion', 'outcome', 'git_sha', 'eval_digest', 'round'}
IDENTIFIER = re.compile(r'^[a-zA-Z0-9_.:-]{1,70}$')


def _label(value):
    if not isinstance(value, str):
        return None
    return value if IDENTIFIER.fullmatch(value) else 'redacted'


def append(target: Path, **values) -> None:
    """Write an atomic (single write) bounded JSON line, never input content."""
    record = {'time': dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds')}
    for key in FIELDS:
        if key not in values:
            continue
        val = values[key]
        if key == 'round' and isinstance(val, int) and 0 <= val <= 99:
            record[key] = val
        elif key in {'git_sha', 'eval_digest'}:
            if isinstance(val, str) and re.fullmatch('[0-9a-f]{40,64}', val):
                record[key] = val
        else:
            label = _label(val)
            if label is not None:
                record[key] = label
    if 'session' in values and isinstance(values['session'], str) and values['session']:
        record['session_sha256_prefix'] = hashlib.sha256(values['session'].encode()).hexdigest()[:16]
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    line = (json.dumps(record, sort_keys=True, ensure_ascii=False) + '\n').encode()
    fd = os.open(target, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


def read(source: Path) -> list[dict]:
    if not Path(source).exists():
        return []
    records = []
    for index, line in enumerate(Path(source).read_text().splitlines(), 1):
        try:
            item = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f'Invalid trace JSON at line {index}') from error
        if not isinstance(item, dict) or item.get('kind') not in ('hook', 'state', 'scenario'):
            raise ValueError(f'Invalid trace event at line {index}')
        records.append(item)
    return records


def coverage(records: list[dict], expectations: list[dict]) -> dict:
    missing = [expect for expect in expectations
               if not any(all(r.get(k) == v for k, v in expect.items()) for r in records)]
    return {'complete': not missing, 'expected': len(expectations),
            'observed': len(expectations) - len(missing), 'missing': missing,
            'total_events': len(records)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace', type=Path, default=Path(__file__).resolve().parents[1] / '.avrl/trace.jsonl')
    parser.add_argument('--expect', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    arguments = parser.parse_args()
    expectations = json.loads(arguments.expect.read_text())
    if not isinstance(expectations, list) or not all(isinstance(item, dict) for item in expectations):
        parser.error('Expectation file must contain an array of metadata patterns')
    result = coverage(read(arguments.trace), expectations)
    output = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
    print(output)
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(output + '\n')
    return 0 if result['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
