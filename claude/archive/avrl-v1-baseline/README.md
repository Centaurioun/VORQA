# Autonomous Verification & Review Loop (AVRL) — Claude Code v2

A Git-based, human-approved and fail-closed evaluation harness for Claude Code. It implements an **AI Labs-inspired local workflow**, not Anthropic's private Scion/Antique or its hosted Code Review service. Its separate agent skills coordinate a builder, verifier, reviewer and zero-context first-time-user QA; deterministic Python scripts retain canonical state and evidence.

## Requirements

- macOS or Linux with Git, Bash, Python **3.11+**, Claude Code CLI (for orchestration), and a browser executable.
- For browser evaluation: `python3 -m pip install -r requirements-browser.txt`; `python3 -m playwright install chromium` (or set `AVRL_CHROMIUM_EXECUTABLE` to a compatible installed Chromium).
- No LLM API key is needed for the standalone controller or tests. Claude Code itself requires your normal authenticated Claude Code access.
- High-assurance use additionally requires protected Git branches, CI in an isolated runner, signed independent approvals and a sandboxed QA browser. The bundled hooks **are not a security boundary**.

## Install in a new feature repository

Run these commands from this repository's root after extracting the archive:

```bash
python3 scripts/avrl.py doctor
python3 -m pip install -r requirements-browser.txt
python3 -m playwright install chromium
python3 scripts/capture_mockups.py
python3 -m unittest discover -s tests -v

git init
git add CLAUDE.md REVIEW.md README.md .claude .github .gitignore docs scripts tests specs example_app requirements-browser.txt
git commit -m "chore: install verification loop baseline"
git switch -c feature/example-signup
```

If using an existing Git repository, **do not blindly run `git init` or overwrite existing `.claude/settings.json` or `CLAUDE.md`**. Merge hook sections and instructions deliberately and create a feature branch from a clean commit. Check git status before starting. The demo is intentionally isolated from any production service.

## Execute from start to finish

```bash
# 1. Define/verify the already supplied example PRD and standalone mockups.
# In Claude Code: /risk-classifier example-signup
# In Claude Code: /write-eval example-signup
# Commit the frozen specifications/mockups before initializing.
git add specs/example-signup/prd.md specs/example-signup/eval.md specs/example-signup/eval.json specs/example-signup/mockups specs/example-signup/scenarios specs/example-signup/decision-log.md
git commit -m "test: freeze example-signup acceptance contract"

# 2. Initialize deterministic state; terminal must have clean Git status.
python3 scripts/avrl.py init example-signup --risk medium
python3 scripts/avrl.py status example-signup

# 3. A REAL HUMAN reviews all contract files; this command prompts for a
# feature-specific digest phrase and cannot be approved non-interactively.
python3 scripts/avrl.py approve example-signup --actor "reviewer@example.test"

# 4. Start bounded implementation and commit changes, then run verification.
python3 scripts/avrl.py round example-signup
# In Claude Code: /review-loop example-signup
# Builder commits tested code. The example app is already provided.
python3 scripts/avrl.py verify example-signup

# 5. Independent review of actual diff/evidence, then black-box QA.
python3 scripts/avrl.py review example-signup --result pass
python3 scripts/demo_server.py 8765
# In a second terminal or Claude Code session: /first-time-user example-signup
# Use `python3 scripts/blind_browser.py` only against the seeded loopback demo.
# After checking the recorded browser evidence:
python3 scripts/avrl.py blind example-signup --result pass --evidence .avrl/blind/last.png
python3 scripts/avrl.py complete example-signup
python3 scripts/avrl.py status example-signup
```

**The example commands are a runbook, not an assertion of success.** `verify` must fail if the current host cannot launch Chromium or open the local test service. Likewise, `review pass` may only be called after genuinely independent human/agent review. The example's existing app means no implementation is necessary for a happy-path run, but completing it still requires live browser and QA evidence.

## Improved Six-Cycle Iterative Refinement

| Cycle | Gate | Fail behavior |
|---|---|---|
| 1 — Define | Risk / scope / PRD | Clarify uncertain irreversible impact |
| 2 — Design | Mockups + falsifiable criteria + human approval | Pause; never code early |
| 3 — Build | Feature branch, atomic working-state commits | Preserve dirty state, no destructive reset |
| 4 — Verify | Automated command, DOM, screenshot and accessibility checks | Evidence-bound FAIL and repair |
| 5 — Challenge | Fresh-context reviewer, defect-class fixes, diff-only re-review | Repeated fingerprint => rethink |
| 6 — Release readiness | Blind QA, approved SHA, CI, rollout readiness | Pause or fail; no auto-deploy |

The orchestrator makes **three** normal attempts. Longer runs (up to five) require explicit design reconsideration and human authorization; repeated identical defects after two fixes cause early exit. Never treat timeouts or skipped browser tests as PASS.

## Layout

- `CLAUDE.md`, `REVIEW.md`: project operating and review instructions.
- `.claude/skills/`: risk classifier, eval writer, review loop, black-box QA, regression debugger.
- `.claude/agents/`: independent builder/verifier/reviewer/blind QA definitions.
- `.claude/hooks/` and `settings.json`: completion enforcement, least-privilege blind-QA command filtering.
- `specs/example-signup/`: PRD, criterion contract, standalone mockups, approved PNG candidates, browser scenarios, decision log.
- `scripts/avrl.py`: atomic state machine and locked evidence gate; `browser_checks.py`: DOM/visual check harness; `demo_server.py` and `ephemeral_db.py`: disposable test service.
- `docs/`: verification map, adversarial audit, explicit limitations and deployment hardening.
- `.avrl/`: ignored runtime state, evidence, temporary SQLite and browser cookies; not source of Git-tracked truth.

## Safe pause, failed round and rollback

```bash
python3 scripts/avrl.py pause example-signup --kind paused --reason "Need operator choice: copy versus structural redesign"
python3 scripts/avrl.py status example-signup
# In Claude Code: /fix-a-bug example-signup "customer cannot register"
# A human chooses a safe fix or `git revert <sha>` on the feature branch.
```

Stop hooks permit intentional pauses; `TaskCompleted` refuses marking unfinished work complete. For recovery, treat `.avrl/backups/<slug>.json` as a **recovery snapshot**, verify it against Git and original eval before proceeding. Do not promote a restored backup straight to completed without fresh checks.

## Known limitations

The local approval HMAC protects against accidental drift, not against an agent/process with access to the operator's home account and the signing key. Review assertions and blind-QA reports cannot be made independent by a self-reporting CLI. Claude Code tool hooks do not intercept OS processes outside Claude or all novel exfiltration vectors. Use OS-level browser sandboxing, protected CI and branch rules to make these meaningful trust boundaries.

The sample server and SQLite database are **test fixtures**, not a production identity service. Its signup does not implement real authentication, email verification, password storage, rate limiting or deployment. Browser tests require a browser that the host security policy actually permits to navigate to loopback; the harness must not silently fall back to a weaker test if that is prohibited.
