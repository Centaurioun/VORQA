# Failures, blockers, and retests

## Confirmed issue found and corrected

An initial host run found three attestation test errors on macOS: the test patched the controller root using the `/var/...` temporary path, while the candidate evidence path was resolved through `/private/var/...`; `Path.relative_to()` then rejected the mismatched spellings. This was a test-fixture path normalization defect, not a production controller failure. The fixture now resolves its temporary root to match the controller’s canonical root. The focused 8-test file passed afterward, and the final full suite passed 43/43.

## Environment-restricted attempt

The first sandboxed attempt could not bind loopback sockets, access Chromium’s macOS bootstrap IPC, or write disposable Git fixture commits. It produced blocked browser/lifecycle results and unrelated harness errors. The same commands were rerun with the host permissions needed for local QA: the final suite and all browser, observability, and lifecycle commands passed. No `--no-sandbox` override was added. These initial restricted logs remain local and are not treated as product results.

## Remaining blockers and blind spots

- Native Claude Code host execution is **UNVERIFIED**: `claude` is absent from PATH. No login, account modification, or authentication attempt was made.
- Native event delivery, including permission UI outcomes, remains unobserved. The synthetic `PermissionDenied` payload models the documented auto-mode event and does not represent a user pressing Reject.
- Review and operator identities in both lifecycle runs are synthetic fixtures, not independent human approvals.
- Browser diagnostics capture console errors, runtime exceptions, failed requests, external requests, and HTTP 5xx. The tested routes returned expected 200/201 responses; broader response-status taxonomy and accessibility/screen-reader automation were outside these scenarios.
- GitHub Actions run #41126724426 completed successfully (all 10 Claude candidate job steps); Foundation checks run #41126724273 also passed. The sanitized artifact was uploaded and expires 2026-11-06.

No product-code defect was confirmed by the final campaign.
