---
name: fix-a-bug
description: Reproduction-first Git history bisect and minimal fix or safe revert for feature regressions
argument-hint: <feature-slug> <symptom>
disable-model-invocation: true
---
# Debug and recover

1. Confirm the feature branch, current SHA, dirty working tree and symptom. Preserve user changes. Record expected vs actual behavior in a reproducible failing test, preferably a narrow automated regression; do not edit production data to reproduce.
2. Run the failing test against the current SHA, isolate environmental variability and derive a specific falsifiable root-cause hypothesis.
3. Inspect `git log --oneline -- <affected-path>` and a bounded `git blame`; on the feature branch with known good/bad commits and clean state use `git bisect start`, `git bisect bad <sha>`, `git bisect good <sha>` with a deterministic test runner; always `git bisect reset` afterward. If no good baseline or nondeterministic test exists, say bisect is inconclusive.
4. Fix the smallest correct **defect class** across all occurrences or use `git revert <bad-sha>` on the feature branch if rollback is safer. Never `git reset --hard` in a shared or dirty worktree. Add a regression test, and check compatibility/security/rollback risk.
5. Run unit/integration/browser checks and independent review again; commit working states atomically. A new source SHA invalidates old evidence and requires re-verification before `complete`.
6. Produce root cause, introduced SHA (if proven), reproducer, all affected instances, correction/revert SHA, verification output and one proposed learned rule for human review.
