# Browser and signup results

Playwright 1.64.1 launched cached Chromium 156.0.8078.4 on macOS 27.0.1. All scenarios used the bundled loopback signup service and a temporary SQLite database.

| Scenario | Viewport | Result | Visual error / limit | Interaction and user-visible result |
|---|---:|---|---:|---|
| desktop | 1280×800 | PASS | 0.01427 / 0.045 | Valid form submit by click; “Account created”.
| mobile | 390×844 | PASS | 0.03959 / 0.045 | Valid form submit by Enter key; “Account created”.
| edge | 1280×800 | PASS | 0.01651 / 0.045 | Invalid email; accessible “Enter a valid name and email” message.

All three reported 0 console errors, 0 JavaScript page errors, 0 failed requests, 0 blocked external requests, and no HTTP 5xx responses. The observability pilot independently observed API outcomes 201 (signup), 409 (duplicate email), and 400 (invalid input), and confirmed 2 SQLite rows (seeded + valid signup).

Keyboard behavior was exercised in the mobile scenario. Browser screenshots were produced for desktop success, mobile success, and edge validation; visual comparison screenshots were also generated. Detailed diagnostics and images remain local under the ignored `.avrl/browser-evidence/example-signup/`. No Playwright trace files were generated.
