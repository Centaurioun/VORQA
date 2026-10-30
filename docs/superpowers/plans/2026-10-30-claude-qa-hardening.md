# VORQA Phase 1 — slice 1 implementation plan

Spec: [Blind QA design](../specs/2026-10-30-claude-qa-hardening-design.md)

## Tasks and gates
1. **Baseline:** inspect imported `claude/implementation/`; run the existing 16-test suite.
2. **RED:** create `claude/implementation/tests/test_blind_browser_controls.py` with four failing browser regression tests: control discovery, accessible interactions, outbound request denial and redacted session fields.
3. **GREEN:** extend `scripts/blind_browser.py` with `snapshot_controls`, `act_on_control`, `attach_network_guard`, `snapshot_session_fields`; retain the CLI's existing commands.
4. **RED/GREEN hook:** add `inspect`, `fill-label`, `click-role` assertions in `tests/test_security.py`; confirm hook denial before expanding the `hook_logic.py` allowlist.
5. **Host guidance:** update the blind QA agent profile and `first-time-user` skill to discover controls without reading source.
6. **CI:** add a root GitHub Actions workflow that runs nested implementation tests and browser scenarios.
7. **Review:** compile changed Python; run the full test suite, inspect the whole branch and create a PR. **Do not merge unverified or failing CI.**

## Six-cycle iterative refinement record
1. Discover: blind QA could not discover selectors; egress routing absent.
2. Model: compare prompt-only, new browser framework and bounded existing CLI; choose bounded CLI.
3. Implement: controls, routes, session-value filtering and agent/hook instructions.
4. Falsify: four new tests first failed on missing symbols; after implementation 20/20 passed in the local browser-capable sandbox. New hook allowlist tests also failed before the hook update and passed after.
5. Red-team: hidden-control exclusion, credential-value non-disclosure and a denied external HTTPS image request were tested. Same-account reviewer impersonation and full OS isolation remain open.
6. Converge: local tests pass; hosted GitHub CI and native Claude Code status must be reported independently.

## Release limits
This is a bounded Phase 1 slice, **not completion** of Claude Code hardening or cross-platform certification.

## CI bootstrap

PR #4 established the nested Claude regression workflow on the default branch; its baseline GitHub Actions run passed. This feature PR must receive its own CI execution before it is merged. Native Claude Code host testing remains unperformed.
