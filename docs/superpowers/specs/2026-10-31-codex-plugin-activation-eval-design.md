# VORQA Codex activation evaluation — design

**Date:** 2026-10-31. **Stage:** Phase 2 acceptance infrastructure; stacked on plugin foundation PR #11.

## Goal

Measure both correct VORQA activation and avoidance of unwanted activation in real Codex sessions. The operator does not want to manually call many skills. This stage tests automatic skill selection without pretending that static plugin evaluation validates runtime decisions.

## Brainstorming alternatives

1. **Only Plugin Eval's static score:** quick but cannot measure actual Codex skill selection; reject as sufficient evidence.
2. **Automatically create fake session results in CI:** fast but would create false confidence; reject.
3. **Versioned positive/negative scenario catalog + strict observation evidence validator + opt-in local marketplace:** selected. CI proves the evaluator's decision behavior; Mac-host trials must separately establish native activation.

## Components

- `.agents/plugins/marketplace.json` exposes a local package as `AVAILABLE`, never installs or enables it.
- `codex/plugin/vorqa/eval/scenarios.json` stores 10 fixed, safe prompts (5 positive, 5 negative).
- `acceptance_eval.py` takes user/host observations and evidence artifact hashes. Missing trial = NOT_RUN; environment refusal = BLOCKED; mismatched activation = FAIL; properly reported trial = PASS.
- `tests/test_acceptance_eval.py` tests missing, false-positive, false-negative, stale/modified proof, symlink escape, malformed and duplicate data, and accidental information disclosures.
- `tests/test_marketplace.py` validates packaging is discoverable but not force-enabled.
- `CODEX_HOST_TASK.md` provides an operator-scoped runbook to execute in the Codex host; no native tests are claimed as run by GitHub CI.

## Assurance limits

Proof hashes show a reported local artifact remained unchanged during scoring. They do **not** independently authenticate that Codex generated it or that a skill was truly selected. Plugin Eval v1 is primarily deterministic static analysis; do not label it a live-run benchmark. A real host observation/third-party review remains necessary for certification.

## Non-goals

No shared core refactor, AVRL provisioning in unrelated repos, live Codex plugin installation, hook enforcement, MCP, branch protection, new isolation infrastructure or claims of full automation.

## Acceptance

GitHub CI passes the existing Codex package tests and the new evaluator/marketplace tests. The CLI fails closed on absent/invalid observations. PR remains open and stacked above #11 until reviewed; native Mac verification stays explicitly pending.
