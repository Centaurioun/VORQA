---
name: review-loop
description: Run a bounded independent builder, verifier and reviewer loop with frozen evals and blind QA
argument-hint: <feature-slug>
disable-model-invocation: true
---
# Autonomous verification and review orchestration

The main session owns orchestration and state transitions, not feature implementation. Review `CLAUDE.md`, `REVIEW.md`, PRD, eval contract, state and Git branch. Require a clean feature branch, approved eval digest and operator-confirmed mockups. Ask for the operator's approval rather than faking it.

Six-cycle iterative refinement with bounded correction:

1. **Define**: classify risk, freeze requirements, enumerate acceptance and external dependencies. Ensure `python3 scripts/avrl.py status <slug>` is `approved`.
2. **Design**: inspect approved standalone mockups, edge states and alternative architectures, without changing contract.
3. **Build**: `python3 scripts/avrl.py round <slug>`; delegate implementation to isolated `builder` with only the PRD/eval/mockup context. Commit a complete working state; no uncommitted proof.
4. **Verify**: delegate to fresh `verifier`; execute `python3 scripts/avrl.py verify <slug>` against frozen eval; collect tests and browser/screenshot artifacts. On FAIL, return concrete falsification steps to builder; do not report completion.
5. **Challenge**: delegate independent `reviewer`, choose low/medium/high effort proportionate to risk; record `python3 scripts/avrl.py review <slug> --result fail --finding-class <class> --fingerprint <stable-id>` or `--result pass --evidence .avrl/review/<slug>/report.json` after writing the matching report described in `docs/REVIEW_QA_RECEIPTS.md`. Round 1 reviews full feature diff. Subsequent rounds review the latest fix delta and targeted regressions, suppress old duplicates, and fix the entire class across the codebase. If the identical fingerprint survives two fixes, pause for architecture rethink. After three unsuccessful rounds stop incremental nits, present reconsidered architecture and obtain operator direction; never exceed five rounds.
6. **Release readiness**: spawn `blind-qa` with no source or Git access against seeded local server, first run `python3 scripts/blind_browser.py reset`, record at least three real browser actions including an interaction, and use the final `event-N.png` screenshot; run `python3 scripts/avrl.py blind <slug> --result pass|fail --evidence <path>`, then `python3 scripts/avrl.py complete <slug>`. Suggest at most three one-line REVIEW.md rules with evidence for separate human approval. Do not merge or deploy.

## State and exception handling

State source of truth is `.avrl/state/<slug>.json`, written atomically under an exclusive lock and mirrored as `specs/<slug>/state.md`. The `Stop` hook may allow an explicit `paused`, `awaiting-approval`, `rethink` or `failed` state; it should never force an agent to hallucinate success. If a subagent crashes, record a pause and restart it in a fresh context; re-run tests against the latest commit. All evidence must bind to the same current SHA and immutable eval digest.

A human override does not turn a failing test into PASS. Change requirements only by new eval revision and new human sign-off. Commit feature work in small, tested states and use staging/CI/flags only after independent approvals.
