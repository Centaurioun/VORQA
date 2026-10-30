# VORQA: GitHub identity verification design (slice 3)

Date: 2026-10-30. State: initial implementation, **not enforced by repository rules**.

## Why

The current AVRL HMAC and commit-bound local reviewer/QA receipts prove that recorded bytes match an earlier verified state. They cannot establish separate human reviewers. VORQA needs an external source of identity before declaring high-risk changes independently approved.

## Approaches considered

1. Continue relying on local HMAC and claimed actor names — rejected: same user can impersonate actors.
2. Immediately enable two-reviewer branch protection — rejected for this iteration: no confirmed independent reviewers or repository-level admin controls available; risks locking single-maintainer workflows.
3. Add read-only GitHub PR review and permissions audit, test its decisions independently, and document the future mandatory branch protection gate — **selected**.

## Required properties

- Trusted PR head commit and target branch; no draft/closed PR passes.
- No self approvals or bot approvals count.
- Only GitHub users with current write/maintain/admin permission count.
- Review must apply to current exact PR SHA; latest decisive review state wins; unresolved change requests block.
- A high-risk path or *previous filename* requires two different GitHub accounts.
- Malformed, missing or truncated GitHub API data fails closed; no PR source is executed.
- No false claim of two separate human beings, or production enforcement, before an independent identity-backed review operation and branch settings are configured.

## Non-goals

No runtime Claude engine changes, no Trail file changes, no protected GitHub rules mutation, no new paid dependencies, and no automatic production release. This is a bounded precursor to full external attestation.

## Acceptance

Test red/green policy decisions, run GitHub foundation CI on a PR and report live integration limitations. This design document and any status claims must distinguish a working **decision tool** from **mandatory merge protection**.
