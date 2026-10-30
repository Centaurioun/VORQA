# VORQA — Real Scenario & Lifecycle Observability Design

**Date:** 2026-10-30. **Scope:** Claude Code adapter, Phase 1 slice 4. No branch protection, mandatory reviewer service or additional isolation infrastructure.

## Problem

The existing `PostToolUse` audit recorded limited metadata for successful tools. It did not give an auditable answer to: was PreToolUse denied, was TaskCompleted blocked, did Stop allow a pause, did a tool fail, or did state move to paused? Unit test pass did not establish actual runtime lifecycle coverage.

## Brainstorming approaches

1. Prompt-only instructions asking agents to narrate decisions — rejected: inconsistent and not executable.
2. Capture all prompts, tool arguments and internal agent reasoning — rejected: secrets, privacy, and unavailable private reasoning.
3. **Bounded metadata-only lifecycle recorder plus an executable fixture pilot** — selected: deterministic, inspectable, no new infrastructure.

## Implementation design

- Local JSONL event recorder `.avrl/trace.jsonl` with event time, phase, event, handler, allow/deny result, bounded reason code, feature, state transition, and optional hashed session identifier.
- No raw prompts, tool arguments, file bodies, input values, secrets, or private chain-of-thought. The recorder is advisory, not tamper-proof. A logging write failure is surfaced as a warning and will appear as missing evidence.
- Hook events wired: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `Stop`, `TaskCompleted`, `SessionStart`, `SubagentStart`, `SubagentStop`.
- A disposable **actual Git repository** runs the AVRL CLI and hook wrapper scripts to exercise approval denial, early completion denial, pause and permissible Stop.
- A real seeded **HTTP and SQLite** demo processes valid, duplicate and invalid signup data (201, 409, 400); the SQLite row count is asserted.
- Optional real Chromium/Playwright desktop/mobile/edge scenarios run in a CI environment; any browser failure is reported as failure, not silently skipped.
- The pilot declares hook injection as **synthetic**; the native Claude Code host must be tested separately. An event absent from the trace is `not observed`, not `passed`.

## Non-goals

No new branch protection rulesets, GitHub approval enforcement, additional OS/browser sandbox, upload of sensitive logs, or recording of an agent's hidden thought process. Existing review safeguards remain intact.

## Acceptance

Red-green tests for missing lifecycle registration, no raw secret logging, state transitions, missing observations, and actual pilot subprocess outcomes. Entire test suite plus GitHub browser pilot must pass before merge. Native host remains UNVERIFIED until a genuine user-driven Claude Code session is inspected.
