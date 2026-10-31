#!/usr/bin/env python3
"""Headless DOM + optional deterministic visual checks for approved eval scenarios."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]


def loopback_url(url):
    parts=urlsplit(url)
    if parts.scheme!='http' or parts.hostname not in {'127.0.0.1','localhost'} or parts.username or parts.password:
        raise ValueError('Only HTTP loopback targets are allowed in the bundled harness')
    return url.rstrip('/')


def wait(base,timeout=10):
    import urllib.request
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        try:
            with urllib.request.urlopen(base+'/health',timeout=.3) as response:
                if response.status==200:return
        except Exception:time.sleep(.15)
    raise RuntimeError('Local test server did not start')


def browser_diagnostics_failed(diagnostics):
    return any(diagnostics.values())


def safe_browser_summary(diagnostics):
    result = {'console_errors': len(diagnostics['console_errors']),
              'page_errors': len(diagnostics['page_errors']),
              'failed_requests': len(diagnostics['failed_requests']),
              'server_error_statuses': [item['status'] for item in diagnostics['server_errors']],
              'blocked_external_requests': len(diagnostics['blocked_external_requests'])}
    failure = diagnostics.get('execution_failure')
    if failure:
        result['execution_failure_category'] = failure['category']
        result['failed_step_index'] = failure['step_index']
    return result


def run_scenario(path,feature):
    from playwright.sync_api import sync_playwright
    from browser_runtime import launch_chromium
    config=json.loads(path.read_text())
    base=loopback_url(config['base_url'])
    process=None
    if 'server' in config:
        argv=config['server']['argv']
        if argv!=['python3','scripts/demo_server.py',str(urlsplit(base).port)]:
            raise ValueError('Only bundled seeded demo server launcher is accepted')
        process=subprocess.Popen([sys.executable,str(ROOT/'scripts'/'demo_server.py'),str(urlsplit(base).port)],
                                 cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            wait(base)
        except Exception:
            process.terminate()
            process.wait(timeout=4)
            raise
    artifact=ROOT/'.avrl'/'browser-evidence'/feature
    artifact.mkdir(parents=True,exist_ok=True)
    blocked_requests=[]
    diagnostics={'console_errors':[],'page_errors':[],
                 'failed_requests':[],'server_errors':[],
                 'blocked_external_requests':blocked_requests,
                 'execution_failure':None}
    failed_step=None
    phase='browser_start'
    browser=None
    try:
        with sync_playwright() as playwright:
            browser=launch_chromium(playwright)
            viewport=config.get('viewport',{'width':1280,'height':800})
            context=browser.new_context(viewport=viewport,device_scale_factor=1,locale='en-US',color_scheme='light',reduced_motion='reduce')
            def network_guard(route):
                target=urlsplit(route.request.url)
                if target.scheme!='http' or target.netloc!=urlsplit(base).netloc:
                    blocked_requests.append(route.request.url)
                    route.abort()
                else:
                    route.continue_()
            context.route('**/*',network_guard)
            page=context.new_page()
            page.on('console',lambda message: diagnostics['console_errors'].append(message.text)
                    if message.type=='error' else None)
            page.on('pageerror',lambda error: diagnostics['page_errors'].append(str(error)))
            page.on('requestfailed',lambda request: diagnostics['failed_requests'].append(
                {'method':request.method,'url':request.url,'failure':request.failure}))
            page.on('response',lambda response: diagnostics['server_errors'].append(
                {'status':response.status,'url':response.url}) if response.status>=500 else None)
            page.on('framenavigated' ,lambda frame: loopback_url(frame.url) if frame.url.startswith('http') else None)
            for index,step in enumerate(config['actions']):
                phase='scenario_action'
                failed_step=index
                if 'goto' in step:
                    if not step['goto'].startswith('/') or step['goto'].startswith('//'):raise ValueError('Navigation must be a local path')
                    page.goto(base+step['goto'],wait_until='networkidle',timeout=12000)
                    loopback_url(page.url)
                    if urlsplit(page.url).netloc!=urlsplit(base).netloc:raise ValueError('Cross-origin redirect blocked')
                elif 'fill' in step:page.locator(step['fill']).fill(step['value'])
                elif 'click' in step:page.locator(step['click']).click()
                elif 'press' in step:
                    page.locator(step['press']['selector']).press(step['press']['key'])
                elif 'expect_text' in step:page.get_by_text(step['expect_text'],exact=False).first.wait_for(state='visible',timeout=6000)
                elif 'expect_role' in step:
                    role=step['expect_role'];page.get_by_role(role['role'],name=role['name']).wait_for(state='visible',timeout=6000)
                elif 'screenshot' in step:
                    safe=''.join(c for c in step['screenshot'] if c.isalnum() or c in '-_')[:60]
                    target=artifact/(safe+'.png');page.screenshot(path=str(target),full_page=True,animations='disabled')
                    print('SCREENSHOT',target.relative_to(ROOT))
                elif 'compare_mockup' in step:
                    from PIL import Image,ImageChops,ImageStat
                    mockup=(ROOT/'specs'/feature/'mockups'/step['compare_mockup']['filename']).resolve()
                    if not mockup.is_relative_to((ROOT/'specs'/feature/'mockups').resolve()) or mockup.suffix!='.png':raise ValueError('Invalid baseline image')
                    current=artifact/f'visual-{index}.png';page.screenshot(path=str(current),full_page=True,animations='disabled')
                    with Image.open(mockup) as a,Image.open(current) as b:
                        if a.size!=b.size:raise ValueError(f'Size mismatch {a.size} vs {b.size}')
                        error=sum(ImageStat.Stat(ImageChops.difference(a.convert('RGB'),b.convert('RGB'))).mean)/(3*255)
                        limit=step['compare_mockup']['max_mean_error']
                        print('VISUAL_ERROR',round(error,5),'LIMIT',limit)
                        if error>limit:raise AssertionError('Visual regression')
                else:raise ValueError('Unknown browser action: '+str(step))
            phase='browser_close'
            browser.close()
            browser=None
            phase='post_run_checks'
            failed_step=None
            if blocked_requests:raise AssertionError('Unexpected external requests: '+str(len(blocked_requests)))
            if browser_diagnostics_failed(diagnostics):
                raise AssertionError('Browser diagnostics reported console, runtime, request, or server errors')
        print('BROWSER PASS',path.name)
    except Exception as error:
        # Class/phase/index are safe diagnostic metadata; never store exception
        # text, raw scenario arguments, request URLs or user input here.
        diagnostics['execution_failure']={
            'category':type(error).__name__,
            'phase':phase,
            'step_index':failed_step,
        }
        raise
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass  # Preserve original failure; the diagnostic stays available.
        diagnostics_path=artifact/f'diagnostics-{path.stem}.json'
        diagnostics_path.write_text(json.dumps(diagnostics,sort_keys=True,indent=2)+'\n')
        print('BROWSER_DIAGNOSTICS',
              json.dumps(safe_browser_summary(diagnostics),sort_keys=True))
        if process is not None:
            process.terminate()
            try:process.wait(timeout=4)
            except subprocess.TimeoutExpired:process.kill();process.wait()


def main():
    p=argparse.ArgumentParser();p.add_argument('--scenario',required=True);p.add_argument('--feature',required=True)
    args=p.parse_args();source=Path(args.scenario).resolve()
    expected=(ROOT/'specs'/args.feature/'scenarios').resolve()
    if not source.is_relative_to(expected) or source.suffix!='.json':raise SystemExit('Scenario path outside feature')
    run_scenario(source,args.feature)

if __name__=='__main__':main()
