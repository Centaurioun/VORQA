#!/usr/bin/env python3
"""Constrained black-box browser CLI: rendered UI controls, never source files.

The CLI only accesses an explicitly configured loopback origin. Host-level sandboxing
remains necessary: Playwright routing is a browser-level guard, not OS isolation.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
from pathlib import Path
import sys
from urllib.parse import urlsplit

from browser_checks import loopback_url

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / '.avrl' / 'blind'


def attach_network_guard(context, base: str) -> list[str]:
    """Refuse all browser traffic outside the exact configured HTTP origin."""
    expected = urlsplit(loopback_url(base))
    blocked: list[str] = []

    def guard(route):
        destination = urlsplit(route.request.url)
        if destination.scheme != 'http' or destination.netloc != expected.netloc:
            blocked.append(route.request.url)
            route.abort()
        else:
            route.continue_()

    context.route('**/*', guard)
    return blocked


def snapshot_controls(page) -> list[dict[str, str]]:
    """Describe visible actionable controls, excluding values and hidden DOM.

    Names follow user-visible labels/ARIA cues. This is a deliberately bounded
    rendered-DOM discovery surface, not an HTML or source-code dump.
    """
    return page.evaluate('''() => {
      const nodes = [...document.querySelectorAll(
        'input, textarea, select, button, a[href], [role="button"], [role="link"], [role="textbox"], [role="combobox"]'
      )];
      const result = [];
      for (const el of nodes) {
        if (result.length >= 40) break;
        const style = getComputedStyle(el);
        if (el.hidden || el.closest('[hidden], [inert]') || style.display === 'none' ||
            style.visibility === 'hidden' || el.getClientRects().length === 0) continue;
        const tag = el.tagName.toLowerCase();
        if (tag === 'input' && el.type === 'hidden') continue;
        let role = el.getAttribute('role');
        if (!role) role = tag === 'button' ? 'button' : tag === 'a' ? 'link' :
          tag === 'select' ? 'combobox' : tag === 'textarea' ? 'textbox' :
          tag === 'input' && ['button', 'submit', 'reset'].includes(el.type) ? 'button' : 'textbox';
        const describedBy = el.getAttribute('aria-labelledby');
        const linked = describedBy ? describedBy.split(/\\s+/).map(id => document.getElementById(id)?.textContent ?? '').join(' ').trim() : '';
        const label = [...(el.labels || [])].map(node => node.textContent.trim()).join(' ').trim();
        const name = el.getAttribute('aria-label') || linked || label ||
          (tag === 'button' || tag === 'a' ? el.textContent.trim() : '') ||
          el.getAttribute('title') || el.getAttribute('placeholder') || '';
        result.push({role, name: name.slice(0, 120), tag, type: el.type || '',
          selector: el.id ? '#' + CSS.escape(el.id) : ''});
      }
      return result;
    }''')


def snapshot_session_fields(page) -> list[dict[str, str]]:
    """Save only non-credential text inputs for stateless CLI rehydration."""
    return page.evaluate('''() => [...document.querySelectorAll('input[id]')]
      .filter(el => {
        const kind = (el.type || '').toLowerCase();
        const detail = [el.id, el.name, el.autocomplete].join(' ').toLowerCase();
        return ['text', 'email', 'search', 'tel', 'url'].includes(kind) &&
          !/(password|secret|token|key|auth|otp|code|cvv|card|credit|ssn|bank|api)/.test(detail) &&
          !el.closest('[hidden], [inert]') && el.value.length < 200;
      })
      .map(el => ({id: el.id, value: el.value}))''')


def act_on_control(page, command: str, values: list[str]) -> None:
    """Use accessibility relationships instead of guessed CSS selectors."""
    if command == 'fill-label':
        page.get_by_label(values[0], exact=True).fill(values[1])
    elif command == 'click-role':
        page.get_by_role(values[0], name=values[1], exact=True).click(timeout=5000)
    elif command == 'select-label':
        page.get_by_label(values[0], exact=True).select_option(label=values[1])
    else:
        raise ValueError('Unsupported accessible control action')


def active_receipt_context() -> dict[str, str | int]:
    """Stamp browser evidence with the currently reviewed local Git state.

    The tool reads internal state, but never exposes this file's source or hidden
    state contents to the black-box agent. This is integrity metadata, not an
    independent identity/security attestation.
    """
    active = json.loads((ROOT / '.avrl' / 'active.json').read_text())
    slug = active['feature']
    if not isinstance(slug, str) or not slug or '/' in slug or '..' in slug:
        raise ValueError('Invalid active feature')
    state = json.loads((ROOT / '.avrl' / 'state' / (slug + '.json')).read_text())
    if state.get('feature') != slug or state.get('status') != 'reviewing':
        raise ValueError('Blind QA requires an active feature in reviewing state')
    commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    return {'feature': slug, 'commit': commit, 'round': state['round'],
            'eval_digest': state['eval_digest'],
            'verification_nonce': state.get('verification_nonce')}


def main() -> None:
    from playwright.sync_api import sync_playwright
    from browser_runtime import launch_chromium

    base = loopback_url(os.environ.get('AVRL_BLIND_BASE_URL', 'http://127.0.0.1:8765'))
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    values = sys.argv[2:]
    valid = {'open', 'text', 'click', 'fill', 'select', 'screenshot', 'reset',
             'inspect', 'fill-label', 'click-role', 'select-label'}
    if command not in valid:
        raise ValueError('Invalid command')
    if command in {'open', 'click', 'text', 'select'} and len(values) != 1:
        raise ValueError('Expected one argument')
    if command in {'fill', 'fill-label', 'click-role', 'select-label'} and len(values) != 2:
        raise ValueError('Expected two arguments')
    if command in {'screenshot', 'reset', 'inspect'} and values:
        raise ValueError('No extra arguments accepted')

    DEST.mkdir(parents=True, exist_ok=True, mode=0o700)
    session = DEST / 'session.json'
    if command == 'reset':
        session.unlink(missing_ok=True)
        (DEST / 'cookies.json').unlink(missing_ok=True)
        (DEST / 'events.jsonl').unlink(missing_ok=True)
        print('Browser session reset')
        return

    receipt = active_receipt_context()
    saved = json.loads(session.read_text()) if session.exists() else {'url': base + '/signup'}
    saved_url = loopback_url(saved['url'])
    if urlsplit(saved_url).netloc != urlsplit(base).netloc:
        raise ValueError('Cross-origin navigation forbidden')

    with sync_playwright() as p:
        browser = launch_chromium(p)
        try:
            cookies = DEST / 'cookies.json'
            context = browser.new_context(storage_state=str(cookies) if cookies.exists() else None)
            blocked_requests = attach_network_guard(context, base)
            page = context.new_page()
            page.goto(saved_url, wait_until='networkidle', timeout=12000)
            for field in saved.get('fields', []):
                try:
                    page.locator('#' + field['id']).fill(field['value'], timeout=1000)
                except Exception:
                    pass

            if command == 'open':
                path = values[0]
                if not path.startswith('/') or path.startswith('//'):
                    raise ValueError('Only local paths')
                page.goto(base + path, wait_until='networkidle', timeout=12000)
            elif command == 'click':
                page.locator(values[0]).click(timeout=5000)
                page.wait_for_timeout(500)
            elif command == 'fill':
                page.locator(values[0]).fill(values[1])
            elif command == 'select':
                page.locator(values[0]).select_option(index=1)
            elif command == 'text':
                print(page.locator(values[0]).inner_text(timeout=5000)[:2500])
            elif command in {'fill-label', 'click-role', 'select-label'}:
                act_on_control(page, command, values)

            target = urlsplit(page.url)
            if target.scheme != 'http' or target.netloc != urlsplit(base).netloc:
                raise ValueError('Browser left allowed origin')
            if blocked_requests:
                raise ValueError('External browser requests blocked: ' + str(len(blocked_requests)))

            if command == 'screenshot':
                path = DEST / 'last.png'
                page.screenshot(path=str(path))
                print('Screenshot:', path.relative_to(ROOT))

            context.storage_state(path=str(cookies))
            session.write_text(json.dumps({'url': page.url, 'fields': snapshot_session_fields(page)}))
            events = DEST / 'events.jsonl'
            count = len(events.read_text().splitlines()) if events.exists() else 0
            capture = DEST / f'event-{count}.png'
            page.screenshot(path=str(capture), animations='disabled')
            record = {**receipt, 'at': dt.datetime.now(dt.timezone.utc).isoformat(),
                      'command': command, 'url': page.url,
                      'capture': str(capture.relative_to(ROOT)),
                      'sha256': hashlib.sha256(capture.read_bytes()).hexdigest()}
            with events.open('a') as event_file:
                event_file.write(json.dumps(record) + '\n')
            print('EVIDENCE', capture.relative_to(ROOT))
            print('PAGE', page.url)
            if command in {'open', 'click', 'fill', 'fill-label', 'click-role', 'select-label', 'inspect'}:
                print('VISIBLE TEXT', page.locator('body').inner_text()[:1800])
                print('INTERACTIVE ELEMENTS', json.dumps(snapshot_controls(page), ensure_ascii=False))
        finally:
            browser.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('BROWSER ERROR:', exc, file=sys.stderr)
        sys.exit(2)
