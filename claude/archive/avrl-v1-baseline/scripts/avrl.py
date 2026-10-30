#!/usr/bin/env python3
"""AVRL: deterministic controls for Claude Code review workflows.

Targets Python 3.11+, POSIX. The human approval record is an advisory local
attestation, not a cryptographic boundary against a process with user privileges.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.avrl'
SLUG = re.compile(r'^[a-z][a-z0-9-]{1,48}$')
ID = re.compile(r'^[A-Z][A-Z0-9_-]{1,40}$')
VALID_STATUSES = {'draft', 'in-review', 'awaiting-approval', 'approved', 'building', 'verifying', 'reviewing', 'rethink', 'paused', 'failed', 'completed'}
FINAL_HUMAN_STATES = {'awaiting-approval', 'rethink', 'paused', 'failed'}


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic(path: Path, data: bytes, mode: int = 0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.tmp-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_DIRECTORY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def json_bytes(data):
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def git(*args, check=True):
    result = subprocess.run(['git', '-C', str(ROOT), *args], text=True, capture_output=True)
    if check and result.returncode:
        raise ValueError('Git failed: ' + result.stderr.strip())
    return result.stdout.strip()


def assert_git_branch(slug):
    if not (ROOT / '.git').exists():
        raise ValueError('Initialize Git and commit the template before starting.')
    branch = git('branch', '--show-current')
    if branch != 'feature/' + slug and branch != 'fix/' + slug:
        raise ValueError(f'Expected feature/{slug} or fix/{slug}; found {branch!r}')
    return branch


def assert_clean():
    changes = git('status', '--porcelain', '--untracked-files=all')
    if changes:
        raise ValueError('Commit the complete working state before recording evidence: ' + changes[:350])


def paths(slug):
    if not SLUG.fullmatch(slug): raise ValueError('Invalid feature slug')
    base = ROOT / 'specs' / slug
    return base, RUNTIME / 'state' / (slug + '.json'), base / 'state.md'


@contextlib.contextmanager
def locked(slug):
    RUNTIME.mkdir(parents=True, exist_ok=True)
    lockpath = RUNTIME / (slug + '.lock')
    with lockpath.open('a+') as file:
        fcntl.flock(file.fileno(), fcntl.LOCK_EX)
        yield


def load(slug):
    _, target, _ = paths(slug)
    if not target.exists(): raise ValueError(f'No state for {slug}; run init')
    state = json.loads(target.read_text())
    if state.get('version') != 2 or state.get('feature') != slug or state.get('status') not in VALID_STATUSES:
        raise ValueError('Corrupt or incompatible state; recover from audit/state backup')
    if state.get('round', -1) < 0 or state.get('round', 0) > state.get('max_rounds', 0):
        raise ValueError('Corrupt round counter')
    return state


def render(state):
    checks = '\n'.join(f"| {c} | {d['status']} | {d.get('evidence','—')} |" for c, d in sorted(state['checks'].items()))
    if not checks: checks = '| (none) | PENDING | — |'
    return (f"# Review state: {state['feature']}\n\n"
            f"Generated from `.avrl/state/{state['feature']}.json`; do not edit this projection.\n\n"
            f"- Status: **{state['status']}**\n- Risk: **{state['risk']}**\n"
            f"- Round: **{state['round']}/{state['max_rounds']}**\n"
            f"- Baseline: `{state.get('baseline') or 'none'}`\n"
            f"- Eval digest: `{state.get('eval_digest') or 'none'}`\n"
            f"- Approval: **{'recorded' if state.get('approval_digest') else 'missing'}**\n"
            f"- Blocker: {state.get('reason') or 'none'}\n\n"
            f"| Criterion | Result | Evidence |\n|---|---|---|\n{checks}\n\n"
            f"## Last updates\n" + '\n'.join(f"- {a['at']} — {a['event']}" for a in state['events'][-12:]) + '\n')


def save(slug, state, event):
    state['updated_at'] = stamp()
    state['events'].append({'at': state['updated_at'], 'event': event})
    if len(state['events']) > 120: state['events'] = state['events'][-120:]
    _, target, projection = paths(slug)
    atomic(target, json_bytes(state))
    atomic(projection, render(state).encode(), 0o644)
    # For recovery, retain a bounded per-feature snapshot, never trust it as approval.
    atomic(RUNTIME / 'backups' / (slug + '.json'), json_bytes(state))


def eval_files(slug):
    base, _, _ = paths(slug)
    paths_to_sign = [base / 'prd.md', base / 'eval.md', base / 'eval.json']
    mockups = sorted((base / 'mockups').glob('*'))
    if not mockups or not any(p.name.endswith('.html') for p in mockups):
        raise ValueError('Desktop/mobile/edge mockups are required')
    paths_to_sign += [p for p in mockups if p.is_file()]
    if any(not p.is_file() for p in paths_to_sign):
        raise ValueError('Missing PRD, eval or mockup files')
    h = hashlib.sha256()
    for path in paths_to_sign:
        h.update(str(path.relative_to(ROOT)).encode() + b'\0')
        h.update(path.read_bytes() + b'\0')
    return h.hexdigest()


def criteria(slug):
    base, _, _ = paths(slug)
    data = json.loads((base / 'eval.json').read_text())
    if not isinstance(data.get('criteria'), list) or not data['criteria']:
        raise ValueError('eval.json needs nonempty criteria')
    ids = set()
    for entry in data['criteria']:
        k = entry.get('id')
        if not isinstance(k, str) or not ID.fullmatch(k) or k in ids:
            raise ValueError('Invalid or duplicate criterion ID')
        ids.add(k)
        if entry.get('type') not in {'command', 'browser', 'visual'}:
            raise ValueError('Only deterministic command/browser/visual criteria supported')
        if entry['type'] == 'command':
            argv = entry.get('argv')
            if not isinstance(argv, list) or not argv or not all(isinstance(a, str) and a for a in argv):
                raise ValueError(f'Criterion {k}: argv must be a nonempty string list')
            if entry.get('timeout', 1) > 180 or entry.get('timeout', 1) <= 0:
                raise ValueError('Timeout must be 1-180 seconds')
        else:
            if not isinstance(entry.get('scenario'), str) or not entry['scenario'].endswith('.json'):
                raise ValueError('Browser criteria require a scenario JSON file')
    return data['criteria']


def private_dir():
    repo_key = digest(str(ROOT.resolve()).encode())[:20]
    dest = Path(os.environ.get('AVRL_APPROVAL_HOME', str(Path.home() / '.config' / 'avrl'))) / repo_key
    dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(dest, 0o700)
    return dest


def private_secret(create=False):
    target = private_dir() / 'signing.key'
    if create and not target.exists(): atomic(target, secrets.token_bytes(32))
    if not target.exists() or target.stat().st_mode & 0o077:
        raise ValueError('Approval key missing or insecure permissions')
    return target.read_bytes()


def signature(slug, eval_hash, actor):
    return hmac.new(private_secret(), f'{slug}\0{eval_hash}\0{actor}'.encode(), hashlib.sha256).hexdigest()


def approval_valid(slug, state):
    try:
        approval = json.loads((private_dir() / (slug + '.json')).read_text())
        expected_hash = eval_files(slug)
        return (approval.get('eval_digest') == expected_hash
                and state.get('approval_digest') == expected_hash
                and hmac.compare_digest(signature(slug, expected_hash, approval.get('actor','')), approval.get('signature','')))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return False


def cmd_init(args):
    slug = args.feature
    with locked(slug):
        base, dest, _ = paths(slug)
        assert_git_branch(slug)
        assert_clean()
        if dest.exists(): raise ValueError('Already initialized')
        if not (base / 'prd.md').exists(): raise ValueError('PRD required')
        checks = {c['id']: {'status':'PENDING'} for c in criteria(slug)}
        state = {'version':2, 'feature':slug, 'status':'in-review', 'risk':args.risk,
                 'max_rounds':args.max_rounds, 'round':0, 'baseline':git('rev-parse','HEAD'),
                 'eval_digest':eval_files(slug), 'approval_digest':None, 'checks':checks,
                 'events':[], 'reason':'Human sign-off required', 'last_finding_signature':None,
                 'repeat_count':0, 'round_commits':[], 'findings':[], 'review_pass':False,
                 'blind_qa_pass':False}
        save(slug, state, 'initialized; awaiting human approval')
        atomic(RUNTIME / 'active.json', json_bytes({'feature':slug}))
        print('Initialized', slug, state['eval_digest'][:12])


def cmd_approve(args):
    with locked(args.feature):
        s = load(args.feature)
        if s['status'] not in {'in-review','awaiting-approval'}: raise ValueError('Not awaiting approval')
        expected = eval_files(args.feature)
        print('Review PRD, eval.md, eval.json and every mockup before signing.')
        phrase = f'APPROVE {args.feature} {expected[:12]}'
        if not sys.stdin.isatty(): raise ValueError('Approval requires an interactive operator terminal')
        if input('Type "' + phrase + '": ').strip() != phrase:
            raise ValueError('Approval phrase did not match')
        private_secret(create=True)
        record = {'actor':args.actor,'approved_at':stamp(),'eval_digest':expected,
                  'signature':signature(args.feature,expected,args.actor)}
        atomic(private_dir() / (args.feature + '.json'), json_bytes(record))
        s['approval_digest'] = expected
        s['status'] = 'approved'
        s['reason'] = None
        save(args.feature,s,'human evaluation approved by ' + args.actor)
        print('Approval attested for', args.feature)


def cmd_round(args):
    with locked(args.feature):
        s=load(args.feature)
        assert_git_branch(args.feature)
        if not approval_valid(args.feature,s): raise ValueError('Approval absent/expired/tampered; re-approve after changing eval')
        if s['status'] not in {'approved','reviewing','verifying'}:
            raise ValueError(f'Cannot start round from {s["status"]}')
        if s['round'] >= s['max_rounds'] or s['round'] >= 3:
            s['status']='rethink'; s['reason']='Three-round architectural rethink required'
            save(args.feature,s,'circuit breaker at 3 rounds')
            raise ValueError(s['reason'])
        assert_clean()
        s['round']+=1
        s['status']='building'; s['review_pass']=False; s['blind_qa_pass']=False
        s['checks']={x['id']:{'status':'PENDING'} for x in criteria(args.feature)}
        s['reason']=None
        s['round_commits'].append({'round':s['round'],'base':git('rev-parse','HEAD')})
        save(args.feature,s,'round ' + str(s['round']) + ' begun')
        print('Round',s['round'],'started; delegate builder')


def cmd_verify(args):
    with locked(args.feature):
        s=load(args.feature)
        if s['status'] not in {'building','verifying'}: raise ValueError('Verify only during active building/verifying')
        if not approval_valid(args.feature,s): raise ValueError('Eval approval invalid')
        assert_git_branch(args.feature); assert_clean()
        s['status']='verifying'
        commit=git('rev-parse','HEAD')
        results={}
        for entry in criteria(args.feature):
            name=entry['id']
            if entry['type']=='command':
                try:
                    result=subprocess.run(entry['argv'], cwd=ROOT, capture_output=True, text=True,
                                          timeout=entry.get('timeout',90), env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
                    output=(result.stdout+'\n'+result.stderr)[-14000:]
                    passed=result.returncode==0
                except (OSError, subprocess.TimeoutExpired) as exc:
                    output=str(exc); passed=False
            else:
                scenario=ROOT / 'specs' / args.feature / 'scenarios' / entry['scenario']
                script=ROOT / 'scripts' / 'browser_checks.py'
                try:
                    result=subprocess.run([sys.executable,str(script),'--scenario',str(scenario),
                                          '--feature',args.feature],cwd=ROOT,capture_output=True,text=True,timeout=120)
                    output=(result.stdout+'\n'+result.stderr)[-14000:]
                    passed=result.returncode==0
                except (OSError, subprocess.TimeoutExpired) as exc:
                    output=str(exc); passed=False
            artifact=RUNTIME/'evidence'/args.feature/(f'round{s["round"]}-{name}-{commit[:12]}.log')
            atomic(artifact,(f'commit={commit}\neval={s["eval_digest"]}\ncriterion={name}\nresult={"PASS" if passed else "FAIL"}\n'+output).encode())
            results[name]={'status':'PASS' if passed else 'FAIL','evidence':str(artifact.relative_to(ROOT)),
                           'commit':commit,'eval_digest':s['eval_digest'],'sha256':digest(artifact.read_bytes())}
        s['checks']=results
        s['status']='reviewing' if all(r['status']=='PASS' for r in results.values()) else 'building'
        save(args.feature,s,'verification: '+str(sum(x['status']=='PASS' for x in results.values()))+'/'+str(len(results)))
        for k,v in results.items():print(k,v['status'],v['evidence'])
        if any(v['status']!='PASS' for v in results.values()): sys.exit(1)


def cmd_review(args):
    with locked(args.feature):
        s=load(args.feature)
        if s['status']!='reviewing': raise ValueError('Only review after all deterministic checks pass')
        assert_git_branch(args.feature); assert_clean()
        if not approval_valid(args.feature,s): raise ValueError('Eval changed')
        current=git('rev-parse','HEAD')
        if any(d.get('commit')!=current or d.get('eval_digest')!=s['eval_digest'] or d['status']!='PASS'
               or not (ROOT/d.get('evidence','')).is_file() or digest((ROOT/d['evidence']).read_bytes())!=d.get('sha256')
               for d in s['checks'].values()): raise ValueError('Stale or missing evidence')
        if args.result=='fail':
            if not args.finding_class or not args.fingerprint: raise ValueError('Fail requires defect class and stable fingerprint')
            sig=digest((args.finding_class+'\0'+args.fingerprint).encode())
            s['repeat_count'] = s['repeat_count']+1 if s['last_finding_signature']==sig else 1
            s['last_finding_signature']=sig
            s['findings'].append({'round':s['round'],'class':args.finding_class,'fingerprint':args.fingerprint,'commit':current})
            s['status']='rethink' if s['repeat_count']>=2 or s['round']>=3 else 'reviewing'
            s['reason']='Same defect persists after two fix attempts' if s['repeat_count']>=2 else 'Fix entire defect class and re-verify'
            s['review_pass']=False
        else:
            s['review_pass']=True; s['reason']=None
        save(args.feature,s,'reviewer '+args.result + (' — '+args.finding_class if args.finding_class else ''))
        print('Reviewer recorded:',args.result,'status:',s['status'])


def cmd_blind(args):
    with locked(args.feature):
        s=load(args.feature)
        if not s['review_pass'] or s['status']!='reviewing': raise ValueError('Pass independent review first')
        if args.result=='fail':
            s['blind_qa_pass']=False;s['status']='reviewing';s['reason']='Blind QA failed; address friction and reverify'
        else:
            s['blind_qa_pass']=True
        save(args.feature,s,'blind QA '+args.result+': '+args.evidence)
        print('Blind QA result:',args.result)


def cmd_complete(args):
    with locked(args.feature):
        s=load(args.feature)
        assert_git_branch(args.feature); assert_clean()
        if not approval_valid(args.feature,s): raise ValueError('Approval invalid')
        if s['status']!='reviewing' or not s['review_pass'] or not s['blind_qa_pass']:
            raise ValueError('Independent reviewer and blind QA required')
        commit=git('rev-parse','HEAD')
        for record in s['checks'].values():
            p=ROOT/record.get('evidence','')
            if record['status']!='PASS' or record.get('commit')!=commit or record.get('eval_digest')!=s['eval_digest'] or not p.is_file() or digest(p.read_bytes())!=record.get('sha256'):
                raise ValueError('All checks must PASS with fresh immutable evidence')
        s['status']='completed';s['reason']=None
        save(args.feature,s,'completed with approved fresh evidence')
        print('COMPLETED',args.feature,commit)


def cmd_pause(args):
    with locked(args.feature):
        s=load(args.feature)
        if s['status']=='completed': raise ValueError('Completed feature cannot be paused')
        if args.kind not in {'paused','rethink','failed','awaiting-approval'}: raise ValueError('Invalid pause kind')
        s['status']=args.kind;s['reason']=args.reason
        save(args.feature,s,'paused: '+args.reason)
        print(s['status'],args.reason)


def cmd_status(args):
    s=load(args.feature)
    print(render(s) if not args.json else json.dumps(s,indent=2))


def cmd_doctor(_args):
    print('Python:',sys.version.split()[0]);print('Git:',subprocess.run(['git','--version'],capture_output=True,text=True).stdout.strip())
    print('Claude:', 'available' if shutil_which('claude') else 'NOT FOUND — agent orchestration unavailable')
    try:
        from playwright.sync_api import sync_playwright
        from browser_runtime import launch_chromium
        with sync_playwright() as p:
            b=launch_chromium(p);b.close()
        print('Playwright Chromium: available')
    except Exception as e:print('Playwright Chromium: NOT READY —',str(e).splitlines()[0])
    print('Template settings:', 'valid' if json.loads((ROOT/'.claude/settings.json').read_text()) else 'invalid')
    print('WARNING: Hooks are not a hardened OS sandbox; untrusted agents need external isolation.')


def shutil_which(s):
    import shutil
    return shutil.which(s)


def parser():
    p=argparse.ArgumentParser(description='Autonomous Verification & Review Loop deterministic controller')
    sub=p.add_subparsers(dest='cmd',required=True)
    sp=sub.add_parser('init');sp.add_argument('feature');sp.add_argument('--risk',required=True,choices=['low','medium','high']);sp.add_argument('--max-rounds',type=int,default=3,choices=[3,4,5]);sp.set_defaults(run=cmd_init)
    sp=sub.add_parser('approve');sp.add_argument('feature');sp.add_argument('--actor',required=True);sp.set_defaults(run=cmd_approve)
    sp=sub.add_parser('round');sp.add_argument('feature');sp.set_defaults(run=cmd_round)
    sp=sub.add_parser('verify');sp.add_argument('feature');sp.set_defaults(run=cmd_verify)
    sp=sub.add_parser('review');sp.add_argument('feature');sp.add_argument('--result',required=True,choices=['pass','fail']);sp.add_argument('--finding-class');sp.add_argument('--fingerprint');sp.set_defaults(run=cmd_review)
    sp=sub.add_parser('blind');sp.add_argument('feature');sp.add_argument('--result',required=True,choices=['pass','fail']);sp.add_argument('--evidence',required=True);sp.set_defaults(run=cmd_blind)
    sp=sub.add_parser('complete');sp.add_argument('feature');sp.set_defaults(run=cmd_complete)
    sp=sub.add_parser('pause');sp.add_argument('feature');sp.add_argument('--kind',default='paused');sp.add_argument('--reason',required=True);sp.set_defaults(run=cmd_pause)
    sp=sub.add_parser('status');sp.add_argument('feature');sp.add_argument('--json',action='store_true');sp.set_defaults(run=cmd_status)
    sp=sub.add_parser('doctor');sp.set_defaults(run=cmd_doctor)
    return p


def main():
    a=parser().parse_args()
    try:a.run(a)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print('AVRL ERROR:',exc,file=sys.stderr);sys.exit(2)


if __name__=='__main__': main()
