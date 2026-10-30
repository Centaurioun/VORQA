#!/usr/bin/env python3
"""AVRL lifecycle acceptance in disposable fixtures, never a real human approval.

Fixture mode tests controller gates with explicitly synthetic QA images.
Full mode drives a real Playwright browser and verifies SQLite persistence.
Neither mode certifies native Claude Code hooks or reviewer independence.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import pty
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request

from observability_pilot import prepare, call
from trace_events import coverage, read

SLUG='example-signup'
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/NwAAAABJRU5ErkJggg==')
STAGES=['init','approve','round','verify','review','blind','release-attest','complete']
EXPECTED=[
 {'kind':'state','from_status':'none','to_status':'in-review'},
 {'kind':'state','from_status':'in-review','to_status':'approved'},
 {'kind':'state','from_status':'approved','to_status':'building'},
 {'kind':'state','from_status':'building','to_status':'reviewing'},
 {'kind':'state','to_status':'reviewing','action':'reviewer'},
 {'kind':'state','to_status':'reviewing','action':'blind'},
 {'kind':'state','to_status':'reviewing','action':'release'},
 {'kind':'state','from_status':'reviewing','to_status':'completed'},
]


def operator_fixture(repo: Path, argv: list[str], phrase: str, env: dict):
    """Send test-only phrase to a pseudo-terminal; not an actual human review."""
    master, slave=pty.openpty()
    try:
        process=subprocess.Popen(argv,cwd=repo,stdin=slave,stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,text=True,
                                 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1',**env})
        os.close(slave)
        slave=-1
        os.write(master,(phrase+'\n').encode())
        stdout,stderr=process.communicate(timeout=20)
        return subprocess.CompletedProcess(argv,process.returncode,stdout,stderr)
    finally:
        os.close(master)
        if slave>=0:os.close(slave)


def wait_server(base: str):
    for _ in range(60):
        try:
            with urllib.request.urlopen(base+'/health',timeout=.3) as response:
                if response.status==200:return
        except OSError:time.sleep(.1)
    raise RuntimeError('Fixture server health check failed')


def synthetic_qa(repo: Path, state: dict, commit: str):
    """Clearly synthetic receipt: verifies receipt parsing, not UI behavior."""
    folder=repo/'.avrl/blind'
    folder.mkdir(parents=True,exist_ok=True)
    events=[]
    for i,action in enumerate(('inspect','fill-label','click-role')):
        image=folder/f'event-{i}.png'
        image.write_bytes(PNG)
        events.append({'feature':SLUG,'commit':commit,'eval_digest':state['eval_digest'],
                       'round':state['round'],'verification_nonce':state['verification_nonce'],
                       'command':action,'url':'http://127.0.0.1:8765/signup',
                       'capture':f'.avrl/blind/event-{i}.png',
                       'sha256':hashlib.sha256(image.read_bytes()).hexdigest()})
    (folder/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    return '.avrl/blind/event-2.png','synthetic-fixture'


def real_browser_qa(repo: Path, env: dict):
    """Trigger actual UI interactions then confirm signup reached SQLite."""
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port=sock.getsockname()[1]
    server=subprocess.Popen([sys.executable,'scripts/demo_server.py',str(port)],cwd=repo,
                            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    base=f'http://127.0.0.1:{port}'
    try:
        wait_server(base)
        runtime={**env,'AVRL_BLIND_BASE_URL':base}
        for action in (('reset',),('inspect',),
                       ('fill-label','Full name','Fixture Test'),
                       ('fill-label','Email address','fixture@example.test'),
                       ('click-role','button','Create account')):
            p=call(repo,[sys.executable,'scripts/blind_browser.py',*action],env=runtime,timeout=25)
            if p.returncode:
                raise RuntimeError('Real browser failed at '+action[0])
        databases=list((repo/'.avrl/tmp').glob('qa-*.sqlite3'))
        if len(databases)!=1:
            raise RuntimeError('Expected one temporary SQLite database')
        for _ in range(30):
            with sqlite3.connect(databases[0]) as connection:
                rows=connection.execute('SELECT COUNT(*) FROM demo_accounts WHERE email=?',
                                        ('fixture@example.test',)).fetchone()[0]
            if rows==1:break
            time.sleep(.1)
        else:
            raise RuntimeError('Browser form submission did not persist')
        events=[json.loads(line) for line in
                (repo/'.avrl/blind/events.jsonl').read_text().splitlines()]
        return events[-1]['capture'],'playwright-real-ui'
    finally:
        server.terminate()
        try:server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


def pilot(mode: str):
    with tempfile.TemporaryDirectory(prefix='vorqa-positive-lifecycle-') as temp:
        directory=Path(temp)
        repo=prepare(directory)
        env={'AVRL_APPROVAL_HOME':str(directory/'fixture-approval')}
        controller=[sys.executable,'scripts/avrl.py']
        stages=[]

        def run(stage: str, *argv: str):
            p=call(repo,controller+list(argv),env=env,timeout=180)
            if p.returncode:
                raise RuntimeError(stage+' failed with exit '+str(p.returncode))
            stages.append(stage)

        run('init','init',SLUG,'--risk','medium')
        state_file=repo/'.avrl/state'/f'{SLUG}.json'
        state=json.loads(state_file.read_text())
        phrase=f'APPROVE {SLUG} {state["eval_digest"][:12]}'
        p=operator_fixture(repo,controller+['approve',SLUG,'--actor','fixture-operator'],phrase,env)
        if p.returncode:raise RuntimeError('Fixture pseudo-terminal approval rejected')
        stages.append('approve')
        run('round','round',SLUG)
        run('verify','verify',SLUG)
        state=json.loads(state_file.read_text())
        sha=call(repo,['git','rev-parse','HEAD']).stdout.strip()
        review_file=repo/'.avrl/review'/SLUG/'report.json'
        review_file.parent.mkdir(parents=True,exist_ok=True)
        review_file.write_text(json.dumps({
            'schema_version':1,'feature':SLUG,'commit':sha,
            'eval_digest':state['eval_digest'],'round':state['round'],
            'verification_nonce':state['verification_nonce'],'verdict':'pass',
            'reviewer':'fixture-reviewer','summary':'Generated automated fixture review',
            'reviewed_files':['example_app/index.html'],'findings':[]}))
        run('review','review',SLUG,'--result','pass',
            '--evidence',f'.avrl/review/{SLUG}/report.json')
        if mode=='full':
            screenshot,qa_mode=real_browser_qa(repo,env)
        else:
            screenshot,qa_mode=synthetic_qa(repo,state,sha)
        run('blind','blind',SLUG,'--result','pass','--evidence',screenshot)
        p=operator_fixture(repo,controller+['release-attest',SLUG,'--actor','fixture-operator'],
                           f'RELEASE {SLUG} {sha[:12]}',env)
        if p.returncode:raise RuntimeError('Fixture pseudo-terminal release rejected')
        stages.append('release-attest')
        run('complete','complete',SLUG)

        hook=[sys.executable,'.claude/hooks/hook_logic.py','completion']
        event=json.dumps({'hook_event_name':'Stop','stop_hook_active':False})
        allowed=call(repo,hook,stdin=event,env=env)
        review_file.write_text(review_file.read_text().replace('fixture-reviewer','altered-reviewer'))
        blocked=call(repo,hook,stdin=event,env=env)
        guards={'completed_stop_allowed':allowed.returncode==0,
                'tampered_review_denied':blocked.returncode==2}
        result=coverage(read(repo/'.avrl/trace.jsonl'),EXPECTED)
        passed=stages==STAGES and result['complete'] and all(guards.values())
        return {'status':'passed' if passed else 'failed','stages':stages,'coverage':result,
                'guards':guards,'qa_mode':qa_mode,'native_claude_verified':False,
                'operator_approval':'synthetic-pty-fixture',
                'reviewer_identity':'synthetic-fixture','git_evidence':'disposable-repo'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['fixture','full'],required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:result=pilot(args.mode)
    except (OSError,RuntimeError,KeyError,ValueError,subprocess.TimeoutExpired) as error:
        result={'status':'failed','error_type':type(error).__name__,
                'native_claude_verified':False,'mode':args.mode}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('FULL LIFECYCLE',result['status'],'mode='+args.mode,'native_claude=UNVERIFIED')
    return 0 if result['status']=='passed' else 1

if __name__=='__main__':
    raise SystemExit(main())
