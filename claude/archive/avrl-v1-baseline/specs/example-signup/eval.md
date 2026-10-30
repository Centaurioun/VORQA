# Example signup falsifiable evaluation (v1)

Scope: local seeded test app only; risk: MEDIUM. Human approval required before feature implementation. Criteria IDs are authoritative in `eval.json` and cannot be silently changed.

| Criterion | Setup | Action | Expected observable result | Proof |
|---|---|---|---|---|
| UNIT | Python 3.11+, isolated SQLite | Run `python3 -m unittest discover -s tests -p test_demo.py` | Exit 0; HTTP/data-validation tests pass | captured exit code and output |
| BROWSER_DESKTOP | Chromium, 1280×800, seeded server | Visit signup and submit a unique valid account | Heading and `Account created` visible; initial screenshot difference ≤0.045 | `desktop.json` and screenshot log |
| BROWSER_MOBILE | Chromium, 390×844, seeded server | Visit signup and register a unique account | Visible success; initial screenshot difference ≤0.045 | `mobile.json` and screenshot log |
| VISUAL_ERROR | Chromium, 1280×800, seeded server | Enter invalid email and submit | Visible validation error; screenshot difference ≤0.045 vs approved edge mockup | `edge.json` and screenshot log |

All criteria are mandatory; a timeout, unsupported browser, changed baseline, stale commit or missing log is FAIL. A passing screenshot comparison is necessary but not sufficient for accessibility and behavioral correctness. A fresh independent review and black-box first-time-user test are required before completion.
