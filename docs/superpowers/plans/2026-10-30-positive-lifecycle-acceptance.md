# Positive AVRL Lifecycle Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development; tests must fail before implementation and pass after.

**Goal:** Exercise a complete positive AVRL workflow and post-completion evidence tampering with honest fixture labels.

**Architecture:** Extend disposable Git + signup fixture pilot; test actual controller commands in a pseudo-terminal, use actual browser on GitHub Actions, verify trace coverage. Do not weaken existing approval or completion guards.

**Tech Stack:** Python 3.11+, unittest, POSIX PTY, Git, Playwright, SQLite, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-30-positive-lifecycle-acceptance-design.md`

## Global constraints

- No branch protection or new isolation system.
- No user project/data/credentials; temp fixture only.
- PTY approvals and reviewer are synthetic, never count as human-independent confirmation.
- Full mode must verify real browser click and SQLite row.
- No native Claude Code certification without a real CLI session.

## Review focus

- PTY approval incorrectly accepted as human identity.
- Successful completion despite a missing or stale reviewer/QA receipt.
- Completion denied despite a valid verified fixture state.
- Browser command returns 0 but did not persist application data.
- CI summary falsely reports native Claude Code hooks.

### Task 1 — RED tests

- [x] Add `tests/test_full_lifecycle.py` requiring completed stage coverage and tamper rejection.
- [x] Run before implementing: expected FAIL, missing pilot script.

### Task 2 — GREEN CLI integration

- [x] Add `scripts/full_lifecycle_pilot.py` with eight real CLI stages, test-only PTY and structured reviewer report.
- [x] Separate `fixture` receipt checking from real `full` browser/SQLite test.
- [x] Check a completed Stop before and after review report alteration.

### Task 3 — CI and convergence

- [x] Add `--mode full` stage to root Claude regression CI workflow.
- [ ] Verify complete GitHub tests and report uploads.
- [ ] Independent source review is desirable; absent native second reviewer, do not claim it was performed.
- [ ] Merge only after successful required CI and clear disclosure of remaining native host verification.

## Six-cycle refinement record

1. **Discover:** PR #7 tests denial/pause and real API/browser; no full positive controller path.
2. **Compare:** negative-only, real user repository, disposable fixture. Select disposable fixture.
3. **Implement:** full CLI, PTY approval fixture, review/QA evidence and browser-based signup.
4. **Falsify:** test-first missing-script failure; GitHub integration checks pending.
5. **Red-team:** tamper reviewer after completion; verify Stop must block. Confirm reporting never mislabels synthetic operator approval.
6. **Converge:** Gate merge on actual GitHub Actions results; native Claude Code remains a separate host acceptance.
