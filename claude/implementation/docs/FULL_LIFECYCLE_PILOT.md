# Complete AVRL controller lifecycle pilot

This script is an acceptance test of actual AVRL CLI behavior. It is **not** a substitute for an independent human operator or a native Claude Code session.

From `claude/implementation/`:

```sh
python3 scripts/full_lifecycle_pilot.py --mode fixture --output .avrl/pilot/lifecycle-fixture.json
python3 scripts/full_lifecycle_pilot.py --mode full --output .avrl/pilot/lifecycle-full.json
```

Both variants create a disposable Git fixture and run `init`, `approve`, `round`, `verify`, `review`, `blind`, `release-attest`, and `complete` with the actual controller. The `approve` and `release-attest` terminal interactions use synthetic PTY input strictly inside the test fixture. The review report is programmatically generated as a fixture, **not** an independent reviewer decision.

The fixture variant uses labeled synthetic QA screenshots to exercise evidence receipt checks. The full variant drives actual Playwright black-box commands, submits the signup form, and queries SQLite to verify that user input reached the application. Both modes verify a clean completed `Stop` and that modifying the temporary reviewer report blocks completion afterward.

Only the report JSON is meant to be uploaded to CI artifacts. No raw prompts, real accounts or private reasoning are captured. `native_claude_verified: false` is mandatory.

**Manual-permission note:** `PermissionDenied` is emitted for auto-mode denials, not manual 'approve for me' dialog rejections. Observe `PermissionRequest` and the actual tool outcome as appropriate, but don't infer that every human choice triggers `PermissionDenied`.

The genuine Claude Code host remains a separate acceptance procedure: check whether agent starts, tools, permission decisions, hook scripts and stop decisions occur in a real session. Do not report that as PASS based on this script.
