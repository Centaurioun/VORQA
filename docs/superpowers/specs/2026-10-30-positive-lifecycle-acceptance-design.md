# VORQA — Positive lifecycle acceptance design

**Date:** 2026-10-30. **Phase:** Claude candidate, after observability PR #7.

## User intent

Go beyond negative-hook checks and isolated unit tests. Prove that the existing state machine can advance an actual disposable test project through `init → approve → round → verify → review → blind → release-attest → complete`, and report precisely why it stops if any gate fails.

## Brainstorming alternatives

1. Rely on existing 28 unit tests and negative-state pilot: rejected, no successful completion path.
2. Run against a user's real repository and real credentials: rejected, unnecessary scope and side effects.
3. **Disposable Git repository plus full CLI smoke**, fixture terminal input, structured evidence, real browser/SQLite assertions in CI: selected.

## Design

- Use the source-controlled bundled signup fixture in an independently created temporary Git repository.
- Invoke the real AVRL CLI for all eight stages.
- The terminal approval and reviewer report in the automated run are explicitly **synthetic fixtures**; they exercise program logic, not the presence of separate humans.
- For unit tests, synthetic PNG receipts verify the QA evidence parser. For CI full mode, invoke the actual black-box browser helper and confirm the signup reached SQLite.
- Confirm the completion hook allows a valid finished state, then edit the **temporary** reviewer report and require that the same hook now blocks stale evidence.
- Publish only summarized stage/coverage outcomes as short-lived CI artifacts; no raw source, credential, or detailed browser capture upload.
- A successfully simulated host hook call **does not certify** native Claude Code hook invocation. Run the separate native host checklist later.
- No new branch protection, reviewer enforcement, extra sandboxing or changes to Trail.

## Criteria

The report must require eight ordered stages, eight observable state events, an allowed completed Stop, a denied tampered Stop, and an explicit `native_claude_verified: false` field. The full mode must fail if Playwright actions or SQLite persistence fails; never silently downgrade to synthetic UI mode.

## Compatibility note

`PermissionDenied` fires only for **auto-mode** denials, not a human click on a permission dialog in normal/manual-approval mode. Do not promise to observe every manually denied tool through this event alone. Reference: https://code.claude.com/docs/en/hooks.
