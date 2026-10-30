# VORQA Observability and Real Scenario Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development. Follow TDD RED → GREEN on each slice.

**Goal:** Verify actual application behavior and observe when AVRL lifecycle and hook actions block, pause or proceed.

**Architecture:** Reuse AVRL controller, existing hook wrappers, demo signup HTTP API and SQLite fixture. Add a bounded JSONL event stream and a deterministic matrix-driven smoke pilot; do not add mandatory permissions infrastructure.

**Tech Stack:** Python 3.11+, unittest, Git, HTTPServer/SQLite, Playwright, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-30-observability-real-scenario-design.md`

## Global constraints

- No PR branch protection or mandatory external reviewer setup.
- Keep current AVRL guards; monitor rather than weaken them.
- Never store prompts, raw commands, form contents, tokens or purported private chain-of-thought.
- Native Claude Code host coverage is not earned by synthetic hook injection.
- Only the bundled test app and disposable fixture data are used.

## Review focus

- A hook denied a tool, but no audit event was recorded.
- Session/agent events never fire because settings omitted them.
- Private input/command values leak into diagnostic JSON.
- A paused Stop incorrectly blocks, or early TaskCompleted incorrectly passes.
- CI labels synthetic hooks as real native Claude execution, or marks a browser error as passed.

### Task 1 — Metadata trace and hook wiring
- [x] RED: tests fail for missing trace writer, missing blocked event, and missing lifecycle registrations.
- [x] GREEN: append only sanitized metadata; trace hook handler outcomes; register PostToolUseFailure, SessionStart and Subagent events.
- [x] Preserve original guard exit codes.

### Task 2 — State transitions and explicit missing-event detection
- [x] RED: no state transitions were recorded; missing matrix events reported incorrectly.
- [x] GREEN: append from/to status for controller saves; implement report CLI with nonzero exit on missing expectations.
- [x] Never copy raw pause reason or reviewer names into the trace.

### Task 3 — Real scenario
- [x] RED: end-to-end pilot missing.
- [x] GREEN: real disposable Git, AVRL init/pause, hook wrapper decisions, HTTP 201/409/400 and SQLite persistence.
- [x] Local 26/26 baseline + added unit tests passed; environment denied browser navigation with `ERR_BLOCKED_BY_ADMINISTRATOR`.
- [ ] GitHub CI executes actual Playwright scenario and publishes sanitized JSON summary.
- [ ] Native Claude Code trigger verification remains a user-host acceptance step.

### Six-cycle iterative refinement
1. **Discovery:** PostToolUse-only auditing missed denial and failed-tool events.
2. **Brainstorm:** compared narration, intrusive full capture, and bounded metadata tracing; chose bounded tracing.
3. **Implementation:** trace writer, hook registration, state transitions, pilot.
4. **Falsification:** 10 new tests use red/green, local suite 26/26 passes on bundled baseline.
5. **Red-team:** secret marker non-disclosure, missing-event failure, incomplete native coverage and environment browser denial distinguished.
6. **Convergence:** GitHub CI and real host acceptance are separate gates; no new branch protection or isolation system.
