#!/usr/bin/env python3
"""Codex-native lifecycle feasibility experiment. No persistent writes or PASS claims.

UserPromptSubmit emits bounded contextual guidance after read-only bridge probe.
Stop is observational, except for an explicit disposable fixture experiment.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

MAX_INPUT = 64 * 1024
NEGATIVE_START = re.compile(
    r'^\s*(?:what\s+is|what\s+are|explain\b|define\b|translate\b|summarize\b|suggest\b|'
    r'correct\s+(?:the\s+)?spelling\b|fix\s+(?:a\s+)?typo\b|'
    r'nedir\b|açıkla\b|çevir\b|özetle\b|öner\b|yazım\s+hatasını\b)', re.I)
EXPLICIT = re.compile(r'\b(?:vorqa|avrl)\b', re.I)
ACTION = re.compile(r'\b(?:fix|repair|implement|refactor|review|audit|verify|test|debug|'
                    r'düzelt|geliştir|incele|doğrula)\b', re.I)
OBJECT = re.compile(r'\b(?:regression|failing|validation|code|change|tests?|bug|feature|'
                    r'security|repository|pull\s+request|\bpr\b|'
                    r'regresyon|kod|güvenlik|test|hata)\b', re.I)


def quiet() -> dict:
    return {'continue': True}


def eligible(prompt: object) -> bool:
    if not isinstance(prompt, str) or len(prompt) > 25000:
        return False
    line = prompt.strip()
    if not line or NEGATIVE_START.match(line):
        return False
    return bool(EXPLICIT.search(line) or (ACTION.search(line) and OBJECT.search(line)))


def probe(root: Path) -> bool:
    """Run ONLY the existing read-only bridge probe, never arbitrary AVRL commands."""
    bridge = Path(__file__).resolve().parents[1] / 'scripts' / 'bridge.py'
    if not bridge.is_file() or bridge.is_symlink():
        return False
    try:
        process = subprocess.run(
            [sys.executable, str(bridge), '--workspace', str(root), 'probe'],
            capture_output=True, text=True, timeout=5, check=False)
        result = json.loads(process.stdout) if process.returncode == 0 else {}
        return (process.returncode == 0 and result.get('bridge_schema') == 1
                and result.get('kind') == 'probe' and result.get('available') is True
                and result.get('reason') == 'controller_present')
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False


def prompt_hook(data: dict, root: Path) -> dict:
    if not eligible(data.get('prompt')) or not probe(root):
        return quiet()
    # Fixed text: no user prompt, workspace path, private state, or secret is copied.
    guidance = (
        'VORQA hook: read-only AVRL probe returned controller_present for this Git root. '
        'For implementation or evidence-backed review, first inspect existing VORQA status '
        'using the installed plugin bridge.py (probe, then status only for a known feature). '
        'The observation is UNVERIFIED, not QA PASS or human approval. '
        'Do not fabricate review/approval receipts or alter the controller state.'
    )
    return {'continue': True, 'hookSpecificOutput': {
        'hookEventName': 'UserPromptSubmit', 'additionalContext': guidance}}


def stop_hook(data: dict, root: Path) -> dict:
    # Test-only continuation probe. Never an automatic production release gate.
    if os.environ.get('VORQA_HOOK_STOP_PROBE') != '1' or data.get('stop_hook_active') is not False:
        return quiet()
    marker = root / '.avrl' / 'hook-pilot-stop-fixture'
    try:
        if (marker.is_symlink() or not marker.is_file()
                or marker.read_text(encoding='utf-8') != 'VORQA_HOOK_PILOT_V1\n'
                or not probe(root)):
            return quiet()
    except (OSError, ValueError):
        return quiet()
    return {'decision': 'block', 'reason':
            'VORQA HOOK PILOT: one-time Stop continuation in an isolated fixture; do not claim QA PASS.'}


def handle(data: object) -> dict:
    if not isinstance(data, dict):
        return quiet()
    cwd = data.get('cwd')
    if not isinstance(cwd, str) or not cwd or '\x00' in cwd:
        return quiet()
    try:
        root = Path(cwd).resolve()
    except (OSError, RuntimeError):
        return quiet()
    event = data.get('hook_event_name')
    if event == 'UserPromptSubmit':
        return prompt_hook(data, root)
    if event == 'Stop':
        return stop_hook(data, root)
    return quiet()


def main() -> None:
    try:
        raw = sys.stdin.read(MAX_INPUT + 1)
        answer = quiet() if len(raw) > MAX_INPUT else handle(json.loads(raw))
    except (OSError, ValueError, TypeError, RecursionError):
        answer = quiet()
    print(json.dumps(answer, sort_keys=True))


if __name__ == '__main__':
    main()
