# Review and QA Evidence Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Implement each task with a failing test, then a passing test, and a review gate.

**Goal:** Reject reviewer and blind-QA PASS results without valid commit-bound, fresh local evidence.

**Architecture:** Extend the existing controller with structured review reports, verifier nonces and screenshot-backed QA receipts. Keep implementation isolated under the Claude adapter.

**Tech Stack:** Python 3.11+, unittest, Playwright and GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-30-review-qa-evidence-integrity-design.md`

## Global constraints

No new runtime dependencies, no source archive rewriting, no claims of independently authenticated reviewers or OS sandboxing, no changes to Codex/Antigravity/Copilot adapters.

## Review focus

- Replayed same-SHA receipts after a fresh verifier invocation
- Invalid or symlink-escaped evidence paths
- Missing, duplicate, malformed or modified browser event images
- Review PASS with unresolved findings or wrong feature/round/contract
- Unverified identity appearing as an alleged cryptographic guarantee

## Task 1 — Reviewer evidence

**Files:** `claude/implementation/scripts/avrl.py`; `claude/implementation/tests/test_attestation_evidence.py`

- [x] RED: missing, stale, unresolved or altered reviewer report cases fail on original controller.
- [x] GREEN: add validated JSON reviewer report, file digest and mandatory PASS evidence parameter.
- [x] Verify reviewer negative tests.

## Task 2 — QA evidence

**Files:** controller and `scripts/blind_browser.py`; receipt tests.

- [x] RED: show prior controller accepted replayed event lines and changed screenshots.
- [x] GREEN: stamp SHA/contract/feature/round/verification nonce, validate every event image, meaningful interaction and loopback origin.
- [x] Reset old approval receipts on new rounds and verifier runs.

## Task 3 — Documentation and verification

**Files:** `claude/implementation/README.md`, reviewer agent, review-loop/first-time-user skills, `docs/REVIEW_QA_RECEIPTS.md`.

- [x] Document receipt schema and migration from flag-only commands.
- [x] Run full local suite (28 tests passed before publishing branch).
- [ ] Verify the GitHub PR diff and fresh GitHub Actions checks.
- [ ] Record PR disposition and residual trust boundaries.

## Six-cycle iterative refinement

1. **Discover:** Existing controller accepted unaudited success flags.
2. **Model:** Compared prompt-only, external identity, and local evidence receipts; selected bounded local receipts.
3. **Implement:** Report/QA proof, nonce, commit binding and docs.
4. **Falsify:** First six receipt tests failed on original code; eight tests passed after implementation; total 28 local tests passed.
5. **Red-team:** Stale/modified reports, event tampering, wrong nonce/commit/round/digest and cross-origin cases.
6. **Converge:** Hosted CI plus peer review remain the integration gates. A local reviewer name is not an authenticated identity.
