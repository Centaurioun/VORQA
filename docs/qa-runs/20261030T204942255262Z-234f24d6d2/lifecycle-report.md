# Lifecycle results

Both lifecycle commands exited 0 and reported `passed`; each observed all 8 expected stages and all 8 state-event expectations.

| Mode | QA evidence origin | Approval/reviewer origin | Native Claude verified |
|---|---|---|---|
| fixture | Synthetic QA receipt | Synthetic PTY approval and synthetic reviewer | No |
| full | Real Playwright UI interaction and SQLite persistence | Synthetic PTY approval and synthetic reviewer | No |

Observed stage order: `init → approve → round → verify → review → blind → release-attest → complete`.

Controller state events from the full run:

1. `initialized`: `none` → `in-review` (round 0)
2. `evaluation`: `in-review` → `approved` (round 0)
3. `round`: `approved` → `building` (round 1)
4. `verification`: `building` → `reviewing` (round 1)
5. `reviewer`: `reviewing` → `reviewing` (round 1)
6. `blind`: `reviewing` → `reviewing` (round 1)
7. `release`: `reviewing` → `reviewing` (round 1)
8. `completed`: `reviewing` → `completed` (round 1)

Both modes verified `completed_stop_allowed=true` and `tampered_review_denied=true`. The full mode’s real UI path submitted the signup form and confirmed its row in the disposable SQLite database. Neither mode establishes independent human approval or reviewer identity.
