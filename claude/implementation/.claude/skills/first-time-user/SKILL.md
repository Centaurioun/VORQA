---
name: first-time-user
description: Conduct black-box new-customer QA using seeded ephemeral data and local Playwright UI only
argument-hint: <feature-slug>
disable-model-invocation: true
---
# Zero-context first-time-user test

The main orchestrator first runs `python3 scripts/ephemeral_db.py` or starts the bundled demo service using `python3 scripts/demo_server.py 8765`, confirming it binds only to loopback and the test-only DB. A real integration must supply an equivalent disposable DB fixture and assert environment identity before launch. **Never point this skill at production or a shared/staging account with customer data.**

Invoke the `blind-qa` subagent with only user-facing business goals and the base URL, not implementation details, source paths, internal selectors, PRD or eval assertions. The agent is restricted to an allowlisted `scripts/blind_browser.py` command surface and cannot read files or arbitrary terminal commands; `PreToolUse` enforces this under `agent_type=blind-qa`. Have it reset the browser session with `python3 scripts/blind_browser.py reset`, then start with `python3 scripts/blind_browser.py inspect`. Browser screenshots/events must be recorded after the final deterministic verifier run and carry its nonce, commit, round and contract digest; the QA PASS must refer to the last event screenshot. The helper lists visible user-facing controls, including accessible names and roles, without HTML/source or input values; use `fill-label` and `click-role` to interact by name. The helper fails on blocked cross-origin browser requests. Guide it to independently discover UI flows, edge states, error clarity, keyboard navigation and mobile usability.

Record the exact observed path, action, visible result, UX friction and screenshot for each finding. Reset or discard the ephemeral DB afterward, and clean cookies and local browser state. If Playwright/Chromium or isolation is unavailable, mark `BLOCKED` and pause; never substitute source inspection. The main orchestrator validates evidence and records `blind` outcome; the blind agent cannot approve itself.

Important limitation: Claude Code hooks alone do not stop local filesystem or network access performed by a malicious process that escapes its tool restrictions. Run an untrusted blind agent in an OS sandbox with a dedicated local test server and no source-mounted filesystem.
