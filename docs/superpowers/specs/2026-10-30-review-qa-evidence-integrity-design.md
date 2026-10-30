# VORQA — Review and QA Evidence Integrity Design

**Date:** 2026-10-30  
**Status:** Phase 1 slice 2. Not a certification of independent identities.

## Intent

The AVRL v2 controller could accept `review --result pass` without a review report, while `blind --result pass` checked a screenshot and three event lines without verifying their commit, contract, round or image contents. An editable flag must not establish independent proof.

## Brainstormed alternatives

1. Prompt-only tightening: inexpensive but unenforced — rejected.
2. Immediate external identity-backed signed attestations: required for high assurance, but needs a defined host, separately authenticated reviewers and a protected CI workflow — deferred as its own trust-boundary project.
3. **Commit-bound local evidence receipts**: buildable on the existing Python controller, explicitly limited to integrity — selected for this iteration.

## Required behavior

- A reviewer PASS includes a JSON report naming reviewed files, verdict and an explanation; it is bound to feature, SHA, contract digest, round and a fresh verification nonce.
- The black-box QA recorder stamps events with the same context automatically. QA PASS checks at least three events, a meaningful interaction, every PNG checksum, paths and a consistent loopback origin.
- Any new verifier run invalidates previously recorded review and QA receipts, even if Git HEAD is unchanged.
- The completion gate revalidates stored report/event hashes before accepting a finished feature.
- The tests demonstrate negative cases first, then the passing implementation.

## Boundaries

The local filesystem, actor names and user-home HMAC are not independent identity or OS sandbox controls. The change does **not** prove separate reviewers, prevent same-account file forgery or fully verify customer journeys. Actual protected CI identity, repository reviewer policy and native Claude host testing remain separate requirements.

## Interface

The review command now needs `--evidence .avrl/review/<slug>/report.json` when reporting PASS. Blind QA uses a current `event-N.png` or matching `last.png`. See `claude/implementation/docs/REVIEW_QA_RECEIPTS.md`.

## Acceptance

Baseline tests plus negative and positive receipt tests pass; GitHub Actions runs nested tests and seeded local browser checks; risks and incomplete identity controls are clearly documented. No production-ready claim.
