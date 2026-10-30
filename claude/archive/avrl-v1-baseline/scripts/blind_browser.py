#!/usr/bin/env python3
"""Constrained black-box browser CLI; gives agent rendered UI, not source files."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit
from browser_checks import loopback_url

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'.avrl'/'blind'


def main():
    from playwright.sync_api import sync_playwright
from browser_runtime import launch_chromium
    base=loopback_url(os.environ.get('AVRL_BLIND_BASE_URL','http://127.0.0.1:8765'))
    command=sys.argv[1] if len(sys.argv)>1 else ''
    values=sys.argv[2:]
    if command not in {'open','text','click','fill','select','screenshot','reset'}:raise ValueError('Invalid command')
    if command in {'open','click','text','select'} and len(values)!=1:raise ValueError('Expected one argument')
    if command=='fill' and len(values)!=2:raise ValueError('Expected selector and value')
    if command in {'screenshot','reset'} and values:raise ValueError('No extra arguments accepted')
    DEST.mkdir(parents=True,exist_ok=True,mode=0o700)
    session=DEST/'session.json'
    if command=='reset':
        session.unlink(missing_ok=True);(DEST/'cookies.json').unlink(missing_ok=True)
        print('Browser session reset');return
    saved=json.loads(session.read_text()) if session.exists() else {'url':base+'/signup'}
    saved_url=loopback_url(saved['url'])
    if urlsplit(saved_url).netloc!=urlsplit(base).netloc:raise ValueError('Cross-origin navigation forbidden')
    with sync_playwright() as p:
        browser=launch_chromium(p)
        cookies=DEST/'cookies.json'
        context=browser.new_context(storage_state=str(cookies) if cookies.exists() else None)
        page=context.new_page()
        page.goto(saved_url,wait_until='networkidle',timeout=12000)
        if command=='open':
            path=values[0]
            if not path.startswith('/') or path.startswith('//'):raise ValueError('Only local paths')
            page.goto(base+path,wait_until='networkidle')
        elif command=='click':page.locator(values[0]).click(timeout=5000)
        elif command=='fill':page.locator(values[0]).fill(values[1])
        elif command=='select':page.locator(values[0]).select_option(index=1)
        elif command=='text':print(page.locator(values[0]).inner_text(timeout=5000)[:2500])
        elif command=='screenshot':
            path=DEST/'last.png';page.screenshot(path=str(path));print('Screenshot:',path.relative_to(ROOT))
        if not page.url.startswith(base+'/') and page.url!=base:raise ValueError('Browser left allowed origin')
        context.storage_state(path=str(cookies))
        session.write_text(json.dumps({'url':page.url}))
        print('PAGE',page.url)
        if command in {'open','click','fill'}:
            print('VISIBLE TEXT',page.locator('body').inner_text()[:1800])
        browser.close()

if __name__=='__main__':
    try:main()
    except Exception as exc:print('BROWSER ERROR:',exc,file=sys.stderr);sys.exit(2)
