# PRD: Example signup (local test-only application)

## Customer outcome
A first-time visitor registers using a full name and email and receives a visible, accessible confirmation. This demo must never create production or shared-stage accounts.

## Scope and scenarios
- Accessible labels and keyboard-focus states on desktop 1280×800 and mobile 390×844.
- Valid unique name/email sends POST `/api/signup`, persists in a seeded disposable SQLite database, and displays `Account created`.
- Invalid name/email shows `Enter a valid name and email` without contacting the endpoint.
- Duplicate email returns 409 and visible `Email already registered`.
- Unknown route 404; non-JSON requests rejected; no arbitrary filesystem routes exposed.

## Threat and failure model
Risk: **medium** for recoverable inability to register test accounts; escalate to high for any real user authentication/account lifecycle. Fixture DB is created in `.avrl/tmp` and is destroyed at server exit. No persistent production access, external URLs, or paid services.

## Nonfunctional acceptance
Browser assertions and approved visual baselines must succeed with headless Chromium. Failure to launch browser, missing screenshots, or non-clean commit cannot be counted as PASS.
