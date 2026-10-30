# VORQA — Claude Code blind-QA hardening design

Date: 2026-10-30  
Status: Phase 1 implementation slice; **not Claude Code host-certified**.

## Intent
The AVRL v2 blind QA saw body text but could not discover CSS selectors, while the blind browser lacked an outbound request filter. This slice addresses both without replacing the controller.

## Alternatives
1. **Prompt-only selector guessing** — rejected: unreliable and no enforcement.
2. **New browser agent framework** — deferred: too much scope and attack surface.
3. **Extend existing bounded Playwright CLI** — chosen: visible control discovery, accessible-name actions, and deny-by-default cross-origin browser routing.

## Requirements
- The `inspect` command returns up to 40 visible actionable controls, with roles, labels and stable identifiers, but **not DOM source or input values**.
- `fill-label`, `click-role` and `select-label` use user-facing accessible names. Existing commands remain supported.
- Requests to origins other than the configured HTTP loopback target are aborted. QA fails rather than logging successful evidence after an external request.
- Rehydrated session fields exclude password, token, OTP and financial credentials.
- Native Claude agent instructions and PreToolUse allowlisting match the CLI.
- Existing tests and new regression tests pass.

## Non-goals
This is not an OS sandbox, identity-backed independent human or reviewer approval, a generic server adapter, independent visual reference generation, or real native Claude Code integration testing. Browser request routing does not provide kernel-level network isolation.

## Security notes
Visible text itself may contain synthetic account data; run on dedicated fixture environments only. The inspector intentionally omits field values and limits output count. Browser-side JavaScript may evade Playwright request routing in ways that require an OS sandbox. The old reviewer and high-risk multi-approver claims still require identity-backed external attestations.

## Follow-up architecture gates
- Independent reviewer/QA attestation linked to exact commit and workflow provenance.
- Identity-backed, truly distinct human signers.
- Configurable **audited** server adapters and independent mockups.
- Full browser isolation and credible black-box scenario coverage.
- Actual Claude Code integration verification in an eligible host before release.
