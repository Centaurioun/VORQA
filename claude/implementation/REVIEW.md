# Independent review policy

## Severity and merge disposition

| Level | Definition | Disposition |
|---|---|---|
| Blocker | Cross-tenant data exposure, payments loss, secret disclosure, destructive production mutation, authentication bypass, or verifiable irreversible loss | Block work and escalate immediately |
| High | Reliable exploitable security defect, broken core workflow, unauthorized access or preventable data corruption | Fix before approval |
| Medium | Recoverable broken behavior, regressions under realistic edge cases, unreliable retries or accessibility failure that obstructs a customer | Fix before completion unless operator explicitly de-scopes it and re-approves eval |
| Nit | Nonfunctional style or clarity issue with no plausible customer failure | At most three per review; never block solely on nits |

## Independent review evidence

A finding requires path and line range, scenario that triggers it, expected and actual behavior, severity, defect class, confidence, and a concise reproduction. Security findings must identify a trust boundary and exploit preconditions. Do not call speculative vulnerabilities verified.

Always check changed behavior, error paths, authorization, validation, retries, concurrency, persistence, observability, accessibility, and tests appropriate to risk. For high risk, include abuse cases, isolation across users, and rollback. Failing evals block completion even if review passes.

## False-positive and duplicate suppression

Ignore generated/third-party files, pre-existing defects not introduced or exposed by the change, non-reproducible speculation, cosmetic preferences handled by lint, and repeated reports with unchanged fingerprint. Escalate a pre-existing severe issue separately, clearly marked as out-of-scope; never silently ignore a safety-critical discovery. A suppressed finding must still be recorded with reason. Reopen only when new changed code or new reproducible evidence changes the finding.

Round 1 can analyze the complete feature diff versus base; later rounds inspect just fix deltas, plus a small targeted regression set. Never treat a delta-only review as replacement for the full CI suite. For any defect, search for all same-class occurrences; record what was checked. Stop after the same fingerprint survives two fixes and require design reconsideration. No automatic endless self-review.

## Report format

Report reviewed SHA/base SHA; checks and outputs; findings ordered by severity; `fingerprint`, `defect_class`, and evidence for each; suppression decisions; risks not tested; decision (`PASS`, `FAIL`, `PAUSE`); next action. Approve only if no unresolved Blocker/High/Medium issues and evidence matches the latest commit.

## Rules Learned Over Time

No rules approved yet. After each completed feature propose at most three concise one-line rules with a linked recurring failure and supporting evidence. A human reviews edits here; an agent must not silently append rules.
