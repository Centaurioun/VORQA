# VORQA Native Codex Hook Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Follow TDD and verification-before-completion.

**Goal:** Create an isolated, opt-in Codex-native hook feasibility candidate without modifying the currently installed VORQA plugin.

**Architecture:** Versioned package defaults to plugin-root `hooks/hooks.json`; synchronous Python handler conservatively classifies prompt events, reuses read-only bridge probe, and makes Stop observational except in an explicit disposable-fixture test.

**Tech Stack:** Python 3.11+, unittest, Git, Codex plugin lifecycle hooks.

**Spec:** `docs/superpowers/specs/2026-10-31-codex-native-hook-pilot.md`

## Tasks

- [x] Examine prior PR #14 diagnostics and official Codex hook event, trust and output schema.
- [x] RED: add fail-closed/negative routing, privacy and one-shot Stop contract tests before handler implementation; confirm initial failures.
- [x] GREEN: implement bounded read-only handler and run 10 initial focused local tests (used a disposable bridge stand-in; GitHub CI must use the canonical bridge).
- [x] Add `hooks/hooks.json`, version package as `0.2.0-alpha.1`, update metadata expectations.
- [x] Document manual trust review, native acceptance and rollback.
- [ ] Run current-head GitHub CI including all actual bridge + hook tests; inspect logs.
- [ ] Native Codex installation, trust and event-delivery test — **operator approval pending**, not covered by CI.
- [ ] Evaluate real prompt-context relevance and fixture-only Stop continuation; report negative cases.

## Six-Cycle Iterative Refinement

1. Discover: auto skill selection unreliable in both large and single-skill catalogs.
2. Compare: skill text, MCP, AGENTS.md, hooks; select smallest native event experiment.
3. Implement: two hooks, one handler, canonical read-only bridge, alpha manifests.
4. Falsify: missing handler created RED test failures; after implementation local harness passed.
5. Red-team: no raw prompt output, no automatic approval, no false-positive conceptual/translation routing, Stop protected by env + ignored marker and one-shot guard.
6. Converge: GitHub CI and operator-approved native hook trust/event observations are separate gates. Not production-ready.
