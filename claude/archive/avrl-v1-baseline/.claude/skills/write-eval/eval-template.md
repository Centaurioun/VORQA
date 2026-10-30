# Falsifiable evaluation contract template

Every feature eval.md must contain concrete versions of these sections. Do not treat the example values as unspecified defaults.

## Metadata
- Feature ID: `example-signup`
- Risk: `medium`
- Scope: local seeded example service; no production writes
- PRD version: commit SHA recorded by the controller
- Oracle: exact response text, HTTP status or image-diff threshold

## Acceptance matrix
| ID | Given | When | Expected | Evidence |
|---|---|---|---|---|
| DEMO_UNIT | local example app and seeded environment | unittest suite executes | exit status 0 | command log |
| DEMO_BROWSER | desktop viewport, fresh seed | valid registration submitted | visible success and HTTP 201 | Playwright trace/screenshots |
| DEMO_MOBILE | narrow viewport | invalid email submitted | accessible inline error, no data written | mobile browser screenshot |

## Approval protocol
Operator reviews the complete eval.md, eval.json, standalone mockups and captured baselines. The controller hashes these files before taking a human interactive confirmation. A changed hash invalidates the approval. No feature implementation is allowed before this gate.

## Rejection criteria
Mark a check FAIL for a timeout, missing tool, false assertion, unexpected network use, changed eval hash, stale commit, missing evidence or inaccessible UI. A SKIP is not a PASS.
