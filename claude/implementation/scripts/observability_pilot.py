#!/usr/bin/env python3
"""Actual Git/controller/HTTP/SQLite pilot with synthetic hook dispatch.

A passing result does NOT certify native Claude Code hook dispatch.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from trace_events import coverage, read

SOURCE = Path(__file__).resolve().parents[1]
EXPECTED = [
    {'kind':'state','from_status':'none','to_status':'in-review'},
    {'kind':'state','from_status':'in-review','to_status':'paused'},
    {'kind':'hook','event':'PreToolUse','handler':'code','decision':'blocked','origin':'synthetic'},
    {'kind':'hook','event':'TaskCompleted','decision':'blocked','origin':'synthetic'},
    {'kind':'hook','event':'Stop','decision':'allowed','origin':'synthetic'},
    {'kind':'hook','event':'PostToolUseFailure','decision':'observed_failure','origin':'synthetic'},
    {'kind':'hook','event':'PostToolUse','decision':'observed_success','origin':'synthetic'},
    {'kind':'hook','event':'SessionStart','origin':'synthetic'},
    {'kind':'hook','event':'SubagentStart','origin':'synthetic'},
    {'kind':'hook','event':'SubagentStop','origin':'synthetic'},
]


def call(repo, argv, *, stdin=None, env=None, timeout=20):
    return subprocess.run(argv,cwd=repo,input=stdin,capture_output=True,text=True,timeout=timeout,
                          env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1',**(env or {})})


def prepare(temp: Path) -> Path:
    repo=temp/'repo'
    shutil.copytree(SOURCE,repo,ignore=shutil.ignore_patterns('.git','.avrl','__pycache__','*.pyc'))
    for args in [['git','init','-b','main'],['git','config','user.email','pilot@example.invalid'],
                 ['git','config','user.name','VORQA Fixture'],['git','add','.'],
                 ['git','commit','-m','seed actual AVRL example app'],
                 ['git','switch','-c','feature/example-signup']]:
        response=call(repo,args)
        if response.returncode:
            raise RuntimeError(f'Fixture Git setup failed (exit {response.returncode})')
    return repo


def exercise_http_sqlite(repo: Path) -> dict:
    """Test real HTTP status and SQLite persistence against seeded temporary service."""
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port=sock.getsockname()[1]
    server=subprocess.Popen([sys.executable,'scripts/demo_server.py',str(port)],
                            cwd=repo,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    base=f'http://127.0.0.1:{port}'
    cases=[]
    try:
        for _ in range(50):
            try:
                with urllib.request.urlopen(base+'/health',timeout=0.3) as response:
                    if response.status==200:break
            except (OSError,urllib.error.URLError):
                time.sleep(0.1)
        else:
            raise RuntimeError('HTTP test service unavailable')
        for name,payload,expected in [
            ('valid_signup',{'name':'Test Person','email':'pilot@example.test'},201),
            ('duplicate_signup',{'name':'Test Person','email':'pilot@example.test'},409),
            ('invalid_signup',{'name':'','email':'not-an-email'},400),
        ]:
            request=urllib.request.Request(base+'/api/signup',data=json.dumps(payload).encode(),
                                           headers={'Content-Type':'application/json'},method='POST')
            try:
                with urllib.request.urlopen(request,timeout=3) as response:status=response.status
            except urllib.error.HTTPError as error:
                status=error.code
            cases.append({'name':name,'http_status':status,'expected':expected})
        databases=list((repo/'.avrl/tmp').glob('qa-*.sqlite3'))
        if len(databases)!=1:
            raise RuntimeError('Unexpected fixture SQLite count')
        with sqlite3.connect(databases[0]) as connection:
            rows=connection.execute('SELECT COUNT(*) FROM demo_accounts').fetchone()[0]
        good=rows==2 and all(c['http_status']==c['expected'] for c in cases)
        return {'status':'passed' if good else 'failed','cases':cases,'sqlite_rows':rows}
    finally:
        server.terminate()
        try: server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


def pilot(*,include_browser: bool) -> dict:
    with tempfile.TemporaryDirectory(prefix='vorqa-observability-') as temp:
        repo=prepare(Path(temp))
        controller=[sys.executable,'scripts/avrl.py']
        hook=[sys.executable,'.claude/hooks/hook_logic.py']
        steps={}
        def record(name,response): steps[name]={'exit':response.returncode}
        def send(name,mode,event):
            event.setdefault('session_id','SENSITIVE_FIXTURE_MARKER')
            response=call(repo,hook+[mode],stdin=json.dumps(event),env={'VORQA_TRACE_ORIGIN':'synthetic'})
            record(name,response)
        response=call(repo,controller+['init','example-signup','--risk','medium'])
        record('init',response)
        if response.returncode: raise RuntimeError('Failed to initialize VORQA pilot')
        send('preapproval_write','code',{'hook_event_name':'PreToolUse','tool_name':'Write',
            'tool_input':{'file_path':str(repo/'example_app/index.html'),'content':'SENSITIVE_FIXTURE_MARKER'}})
        send('task_completed','completion',{'hook_event_name':'TaskCompleted'})
        send('in_review_stop','completion',{'hook_event_name':'Stop','stop_hook_active':False})
        send('successful_tool','audit',{'hook_event_name':'PostToolUse','tool_name':'Read'})
        send('failed_tool','audit',{'hook_event_name':'PostToolUseFailure','tool_name':'Bash',
                                   'tool_input':{'command':'SENSITIVE_FIXTURE_MARKER'}})
        send('session_start','audit',{'hook_event_name':'SessionStart','source':'startup'})
        send('subagent_start','audit',{'hook_event_name':'SubagentStart','agent_type':'builder'})
        send('subagent_stop','audit',{'hook_event_name':'SubagentStop','agent_type':'builder'})
        record('pause',call(repo,controller+['pause','example-signup','--kind','paused',
                                           '--reason','human review needed']))
        send('paused_stop','completion',{'hook_event_name':'Stop','stop_hook_active':False})
        record('verify_without_approval',call(repo,controller+['verify','example-signup']))
        api=exercise_http_sqlite(repo)
        browser={'status':'not_run','scenarios':[]}
        if include_browser:
            browser['status']='passed'
            for name in ('desktop','mobile','edge'):
                response=call(repo,[sys.executable,'scripts/browser_checks.py','--scenario',
                                    f'specs/example-signup/scenarios/{name}.json',
                                    '--feature','example-signup'],timeout=90)
                browser['scenarios'].append({'name':name,'exit':response.returncode})
                if response.returncode:browser['status']='failed'
        matrix=coverage(read(repo/'.avrl/trace.jsonl'),EXPECTED)
        success=(steps['init']['exit']==0 and steps['preapproval_write']['exit']==2 and
                 steps['task_completed']['exit']==2 and steps['paused_stop']['exit']==0 and
                 steps['verify_without_approval']['exit']!=0 and steps['pause']['exit']==0 and
                 all(steps[k]['exit']==0 for k in ('successful_tool','failed_tool','session_start','subagent_start','subagent_stop')))
        return {'kind':'synthetic_hook_dispatch_real_git_controller',
                'native_claude_verified':False,'steps':steps,'coverage':matrix,
                'browser':browser,'api':api,
                'passed':success and matrix['complete'] and api['status']=='passed' and browser['status']!='failed',
                'note':'Real Git, controller, HTTP, SQLite and optional Playwright; hook dispatch synthetic, not Claude native.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args()
    result=pilot(include_browser=not args.no_browser)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(f"PILOT {'PASS' if result['passed'] else 'FAIL'}; coverage={result['coverage']['observed']}/{result['coverage']['expected']}; browser={result['browser']['status']}; native_host=UNVERIFIED")
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
