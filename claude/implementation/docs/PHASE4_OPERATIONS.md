# Phase 4: operator gates, recovery, and incident playbook

## Before every feature

1. Confirm you are in the intended Git repo, on a clean feature branch. Verify current CI and changes to settings/hooks.
2. Classify blast radius and freeze a complete testable PRD. Generate eval.md, eval.json, browser scenarios and standalone desktop/mobile/edge HTML and PNGs.
3. Commit the contract, run `init`, and request a real human's interactive eval approval. For high-risk features use two **different** humans.
4. Begin an implementation round. Commit working code and test output; request independent verification and review with the exact SHA.
5. Run blind QA only on test-only seed data; preserve UI evidence, block source inspection and reset cookies/DB afterward.
6. Have the required release reviewers attest the **final SHA** using the interactive `release-attest` command. If any code changes, re-run verification and renew release signoffs.
7. Call `complete` only after all gates pass; the orchestrator may then propose PR/merge readiness but must not auto-merge or deploy.

## Exact controller operations

```bash
python3 scripts/avrl.py doctor
python3 scripts/avrl.py init example-signup --risk medium --max-rounds 3
python3 scripts/avrl.py approve example-signup --actor qa-lead@example.test
python3 scripts/avrl.py round example-signup
python3 scripts/avrl.py verify example-signup
python3 scripts/avrl.py review example-signup --result pass
python3 scripts/avrl.py blind example-signup --result pass --evidence .avrl/blind/event-3.png
python3 scripts/avrl.py release-attest example-signup --actor tech-lead@example.test
python3 scripts/avrl.py complete example-signup
```

The browser evidence file name is an illustrative output from an actual blind browser session; **use the concrete path printed by your run**, not an assumed path. `approve` and `release-attest` cannot run noninteractively. For high risk repeat both approval commands with a second distinct operator.

For rounds four and five only, initialize with `--max-rounds 5`, reach the architectural rethink gate, present a changed architecture and get the operator to run:

```bash
python3 scripts/avrl.py authorize-rethink example-signup --reason "Human reviewed new architecture and targeted risk controls"
python3 scripts/avrl.py round example-signup
```

If retry still fails or a defect fingerprint repeats after two fixes, pause and change direction rather than suppressing the finding.

## Disaster recovery

If a subagent terminates midway through a round, first capture SHA, branch, Git porcelain status, state and latest `.avrl/evidence/` logs. Do not edit runtime state manually. Preserve unsaved source changes, commit only coherent work, and re-run `verify`. A corrupted state must be reconciled with the bounded backup and operator oversight, then all final checks repeated; the backup is not an approval credential. Unexpected production data, leaked secrets or unauthorized writes require immediate incident escalation, not loop retries.

## Minimal deployment integration checklist

CI/branch protection must rerun tests against the merged base; enforce protected paths for hooks and evals, distinct release reviewers, no secrets in fixture logs, and minimum permissions for pipelines. Production deploy is separate, explicitly authorized, and preceded by a rollback rehearsal, feature flag plan and telemetry thresholds. Track post-merge failures, revert speed and defect class recurrence to refine `REVIEW.md` with operator approval.
