# VORQA Codex Activation Evaluation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development. Follow TDD red, green, review and verify.

**Goal:** Establish reproducible evidence requirements for native Codex plugin activation tests.

**Architecture:** Keep the Codex plugin unchanged, add an opt-in repo marketplace and a deterministic scoring layer over future local host observations. Never manufacture native evidence.

**Stack:** Python 3.11+ unittest, GitHub Actions, local Codex Plugin Creator/Plugin Eval (when present).

**Spec:** `docs/superpowers/specs/2026-10-31-codex-plugin-activation-eval-design.md`

## Constraints

- Do not modify the Claude implementation, user Codex settings, Trail or the current main branch.
- Keep raw session evidence in Git-ignored local folders; only sanitized summaries may go to a public PR.
- No forced installation, global config writes, model API calls or native-host claims from CI.
- PR #11 is an unmerged prerequisite: base the acceptance PR on its branch; leave both for human review.

## Tasks

1. **RED:** Add tests asserting missing observations are incomplete, false activations fail, bogus hashes/symlinks block, and duplicate/unrecognized data is rejected. Verified the original import failed before the evaluator existed.
2. **GREEN:** Implement `acceptance_eval.py` with explicit evidence levels and no raw log output; local tests 9/9 passed.
3. **Package discovery:** Add repo marketplace with `AVAILABLE` policy. Validate no forced project Codex configuration.
4. **Runbook:** Document both static Plugin Eval and native Codex trial requirements separately.
5. **CI:** Exercise all new tests in PR, inspect exact head run logs. Record real blockers, never claim successful native activation without host evidence.

## Six-Cycle Iterative Refinement

1. **Discover:** PR #11 plugin has never been loaded by the user's Codex host.
2. **Compare:** Static-only, fake-CI trials and real-host evidence contract. Select third.
3. **Implement:** Scenario catalog, observation checker, marketplace and runbook.
4. **Falsify:** Missing evaluator test import RED; 9 tests GREEN, including forged/missing evidence.
5. **Adversarial review:** Hash manipulation, symlink escape, false activation and incomplete evaluation. A matching hash is still self-reported, not independent native attestation.
6. **Converge:** Hosted CI validates evaluator, user-host Plugin Eval plus real session trials remain the next acceptance gate. PR may be reviewed but native activation is not complete.
