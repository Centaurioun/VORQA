# Evaluation design decision log

## 2026-10-30 — Approach
Selected a disposable SQLite-based local app rather than a production SaaS demonstration to verify actual browser and persistence interactions without customer data. Approved mockups are standalone HTML/CSS; app code is separately served from a test-only route.

## Alternatives considered
- Pure screenshot-only tests: rejected because they cannot validate server persistence or actual customer outcomes.
- Database-free mock server: rejected because it would not test uniqueness/duplicate state.
- Production credentials or external live URL: prohibited due to data security and repeatability.

## Known residual risks
Pixel differences across browser/font platforms may cause flaky results; Playwright headless viewport and reduced-motion are pinned for local comparisons. External infrastructure and real authentication are outside this demo. Formal human sign-off on the selected thresholds remains mandatory.
