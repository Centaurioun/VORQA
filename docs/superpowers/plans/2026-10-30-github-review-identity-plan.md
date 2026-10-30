# GitHub Review Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development. Follow RED → GREEN → verify for each task.

**Goal:** Assess real GitHub PR approvals, permissions and commit freshness without trusting local reviewer names.

**Architecture:** A read-only stdlib Python evaluator computes decisions from authenticated GitHub REST data. An opt-in manual workflow runs only trusted default-branch code. Repository ruleset enforcement remains a separate operator-approved deployment.

**Tech Stack:** Python 3.13 CI (stdlib only), GitHub REST API, unittest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-30-github-review-identity-design.md`

## Global constraints

- Do not read or modify untracked user Trail files.
- Do not trust PR body risk declarations.
- Do not check out untrusted PR head into a token-enabled identity check.
- Do not turn manual audit into a silently required check.
- Fail closed when GitHub review, permission or head SHA data is unavailable.

## Review focus

- One person acting as both author and reviewer.
- Previous commit approvals recycled after new push.
- Hidden high-risk changes via file rename.
- Missing collaborator permission APIs or incomplete pagination.
- Review comments or dismissed reviews incorrectly overriding real decisions.

### Task 1: Policy logic and TDD

**Files:** `scripts/github_review_policy.py`, `tests/test_github_review_policy.py`.

- [x] Write initial regression tests (13 failures prior to implementation).
- [x] Implement `risk_tier(files)`, `evaluate(pr, files, reviews, permissions, *, expected_head)`.
- [x] Add API fixed-host validation and permission collection tests.
- [x] Run full focused suite: 15 passing tests in the isolated local sandbox.

### Task 2: Trusted audit integration

**Files:** `.github/workflows/review-identity-audit.yml`, `.github/workflows/foundation.yml`.

- [x] Add manual, read-only audit workflow with trusted `main` checkout and no execution of PR source.
- [x] Add pure evaluator test job to existing foundation CI.
- [ ] Verify GitHub workflows on PR; confirm workflow_dispatch appears after merge.

### Task 3: Documentation and staged rollout

**Files:** `docs/GITHUB_REVIEW_POLICY.md`, this plan, roadmap.

- [x] Document actual user/account limits and required branch rules.
- [ ] Perform whole PR review and verify CI after commit.
- [ ] Leave mandatory ruleset activation OPEN until external reviewers and trusted automatic gate are configured.

## Six-cycle iterative refinement

1. **Discovery:** local receipts and HMAC cannot independently authenticate the reviewer.
2. **Architecture alternatives:** local actor strings vs immediate branch rule enforcement vs external read-only audit; selected third.
3. **Implementation:** deterministic risk tiers and GitHub identity decision, safe fixed-host API, manual workflow.
4. **Verification:** negative/positive author, stale SHA, change request, permission, bot, high-risk rename and pagination cases.
5. **Adversarial review:** user can spoof two account identities outside GitHub; GitHub owners can bypass unprotected main; a manual workflow is not an automatic gate. Those remain explicit risks.
6. **Convergence:** local policy tests pass, GitHub CI required for final merge. Remaining P0: live branch protection and independent attestation.
