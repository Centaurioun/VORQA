---
name: risk-classifier
description: Classify feature customer blast radius and select tests and approvals before writing evals
argument-hint: <feature-slug>
disable-model-invocation: true
---
# Risk classification

Input is the feature slug in `$ARGUMENTS`. Read `specs/<slug>/prd.md` and the actual routes, data surfaces, authorization boundaries, and rollback capability. Explicitly ask, *what happens to the customer if this fails?*

Return this structured report, with exact fields and defensible reasoning:

```json
{
  "feature": "example-signup",
  "tier": "medium",
  "customer_impact": "Recoverable inability to register a test account",
  "threat_surfaces": ["form validation", "server write path"],
  "likelihood": "medium",
  "blast_radius": "new test accounts only",
  "rollback": "feature branch revert; no live users",
  "eval_depth": ["unit", "integration", "browser/mobile", "negative cases"],
  "human_eval_approval": true,
  "release_human_approvals": 1
}
```

Tiers: **Low** only cosmetic, text or layout defects, no behavior/data/security changes. **Medium** a recoverable broken feature without financial loss, data loss, lockout, or confidentiality breach. **High** any plausible financial loss, unauthorized access, auth lockout, cross-user data leak, secrets, or destructive irreversible mutation. When uncertain, choose the higher tier and disclose uncertainty. Docs-only is low only after verifying no behavioral implications.

Pre-implementation operator approval of the exact eval/mockups is mandatory at every tier. High-risk changes also require two independent humans for final merge in protected CI; this repository cannot itself enforce Git host branch protections. Save the classification rationale in the PRD; initialize controller with `--risk <tier>` and never downgrade solely to shorten tests.
