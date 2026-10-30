# GitHub review identity and branch protection policy

**Status:** Phase 1 identity audit implemented; **not yet enforced by repository settings**. This gate reads GitHub PR metadata, not local `reviewer` strings or self-reported `PASS` flags.

## Scope

`scripts/github_review_policy.py` checks an open non-draft PR targeting `main`. It requires an exact expected head SHA, ignores the PR author and bot reviews, queries collaborator permissions, rejects stale commit reviews, and blocks unresolved change requests. STANDARD changes require one authorized GitHub login; HIGH risk changes require two **distinct GitHub accounts** with write/maintain/admin permission. The accounts need to be actual distinct reviewers in repository governance; account identities do **not** prove two separate human beings.

HIGH risk includes GitHub workflow/rule files, root agent/security policy, VORQA review policy, Claude code runtime scripts and Claude agent/hook configuration, including renames *from* these paths. Classification is deterministic and cannot be reduced by a PR description.

The command performs read-only GitHub API calls and emits an inspectable decision. It does **not** alter branch rules or release approvals. If GitHub denies access, pagination is incomplete, an approval is stale, or reviewer permission cannot be verified, the decision is BLOCK.

## Usage (manual identity audit)

1. Open a PR, inspect its exact `head.sha` and ensure proposed reviewers have adequate permissions.
2. Open **Actions → Review identity audit (manual gate) → Run workflow** on the trusted default branch.
3. Enter PR number and exact 40-hex head SHA.
4. The run fails if the required authentic GitHub-account reviews have not been supplied. Any new commit requires a new run/review.

For an authorized workstation with `GITHUB_TOKEN` available:

```sh
python3 scripts/github_review_policy.py \
  --repository Centaurioun/VORQA \
  --pr 123 \
  --head 0123456789abcdef0123456789abcdef01234567
```

The URL and SHA shown above are illustrative. `--report-only` is a **non-enforcing diagnostic**: exit status 0 does not indicate approval.

## What remains before this can prevent merges

An administrator must configure ruleset/branch protection for `main`: require PRs, protected status checks from trusted workflows, at least two approving reviews for high-risk changes (or consistently two for all changes), dismiss stale approvals, require code-owner review where appropriate, disallow force pushes and deletions, and apply to admins/no bypass where available. Inspect repository plan limitations and ownership. `CODEOWNERS` alone does not enforce approvals.

**Do not set this manually triggered job as a required check without a deliberate trigger/rollout design**: its status is not tied to every PR head or review change, and old successful manual checks may mislead. A next project phase must implement a trusted, automatically re-evaluated gate integrated with repository rules. In particular, a pull-request job sourced from untrusted PR code cannot serve as an uncompromisable identity authority. Avoid `pull_request_target` until the repository's Actions policy and trust model have been reviewed.

### Known limits

- The audit has no OS/browser sandbox and does not prevent same-user modification of VORQA local approvals.
- A GitHub login is not proof that two reviews came from two different natural persons.
- Repository owner/admin may still bypass policies unless branch rules explicitly disallow it.
- Protected CI identity and mandatory review need a separately verified live integration. No current local user or Trail workspace changes were read or edited.
- If a token cannot read repository collaborator permissions, the audit intentionally fails; do not downgrade to `author_association` as a shortcut.
