# Local verification results — 2026-10-30

These results were collected in the artifact-building environment. They do not imply that Claude Code, remote GitHub Actions, or a target production application have been executed.

| Test | Actual observed result | Interpretation |
|---|---|---|
| `python3 -m unittest discover -s tests -v` | **16 tests passed** | Hook policy attacks, controller Git state, sign-off denial, disposable SQLite, local HTTP API, static browser form validation |
| `python3 scripts/capture_mockups.py` | **3 images generated** | Chrome rendered approved-candidate standalone desktop, mobile and edge HTML; not live app E2E |
| `python3 scripts/avrl.py doctor` | Python 3.13.5 and Git available; **Claude Code CLI not installed** | Local Claude orchestration and hook integration cannot be runtime-verified here |
| Playwright Chromium launch | **Succeeded** using system Chromium fallback | Headless browser executable itself works |
| Live Playwright `http://127.0.0.1:8765/signup` | **FAILED**: `net::ERR_BLOCKED_BY_ADMINISTRATOR` | Host browser policy prohibits navigation, so all live browser acceptance checks remain unverified and MUST block completion |
| Seeded local HTTP `/health` | **200** with `ephemeral-test` marker | Test-only server can respond to host HTTP requests |
| SIGTERM fixture teardown | **Passed** | Seeded disposable DB file deleted after graceful shutdown |

## Not tested / must be rerun in the real host

- Full interactive Claude Code subagent orchestration and hook dispatch via Claude Code >=2.1.295.
- Browser DOM journeys and live screenshot comparison against the actual test server on a browser-permitted runner.
- GitHub Actions CI in the target GitHub repository and protected branch settings.
- Two independent operators' interactive approval attestations on the final application commit.
- Any actual application's schema, authentication, billing, deployment, rollback or monitoring.

**Correct final state on this sandbox: verification incomplete.** Do not mark the example feature `completed` here or claim production readiness. Run the published CI job and actual end-to-end acceptance in the intended developer/CI environment.
