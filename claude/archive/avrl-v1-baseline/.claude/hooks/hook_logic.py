#!/usr/bin/env python3
"""Claude Code hook handler. Reads exactly one event from stdin."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import shlex
import sys

ROOT=Path(__file__).resolve().parents[2]
RUNTIME=ROOT/'.avrl'


def block(reason):
    print('AVRL BLOCK: '+reason, file=sys.stderr)
    return 2


def active():
    ptr=RUNTIME/'active.json'
    if not ptr.exists():return None
    try:
        slug=json.loads(ptr.read_text())['feature']
        if not re.fullmatch(r'[a-z][a-z0-9-]{1,48}',slug):return {'status':'corrupt'}
        state=json.loads((RUNTIME/'state'/f'{slug}.json').read_text())
        if state['feature']!=slug:return {'status':'corrupt'}
        return state
    except (OSError,KeyError,ValueError,TypeError):
        return {'status':'corrupt'}


def is_safe_blind_command(command):
    # Strict positive allowlist. Any shell syntax or expansion is denied before shlex.
    if len(command)>2048 or re.search(r'[;&|`$<>\\\n\r\x00]',command):return False
    try:parts=shlex.split(command,posix=True)
    except ValueError:return False
    if len(parts)<3:return False
    if parts[:2] not in (['python3','scripts/blind_browser.py'],['python','scripts/blind_browser.py']):return False
    action=parts[2]
    if action not in {'open','text','click','fill','screenshot','reset','select'}:return False
    # The browser helper validates URLs/selector arguments again.
    return len(parts)<=8


def blind_guard(event):
    if event.get('agent_type')!='blind-qa':return 0
    tool=event.get('tool_name','')
    inp=event.get('tool_input') or {}
    if tool=='Bash':
        command=inp.get('command','')
        if isinstance(command,str) and is_safe_blind_command(command):return 0
        return block('blind-qa can run only the black-box browser helper; no source or terminal inspection')
    # With the agent's tool allowlist, other tools should not be present at all.
    return block('blind-qa tool not allowed: '+str(tool))


def completion_guard(event):
    state=active()
    if state is None:return 0
    status=state.get('status')
    name=event.get('hook_event_name')
    if status=='completed':return 0
    if name=='TaskCompleted':return block('feature is not completed in verified state')
    if name=='Stop':
        # Do not deadlock. A legitimate pause/approval must be able to return.
        if status in {'awaiting-approval','in-review','approved','paused','rethink','failed','corrupt'}:return 0
        if event.get('stop_hook_active'):return 0
        return block('Feature is still '+str(status)+'. Verify, review and complete; or explicitly pause for human input.')
    return 0


def main():
    try:event=json.load(sys.stdin)
    except Exception:return block('Malformed hook input; fail closed')
    mode=sys.argv[1]
    if mode=='blind':return blind_guard(event)
    if mode=='completion':return completion_guard(event)
    return block('Unknown hook mode')


if __name__=='__main__':sys.exit(main())
