# Codex-Only Release Readiness

**Public release decision: `NO-GO`.** VORQA `0.2.0-preview.1` is a local explicit-workflow preview, not a public or stable release.

| Area | State | Evidence / boundary |
| --- | --- | --- |
| Explicit workflow product | `PREVIEW` | Skill and bounded bridge use an existing pinned AVRL controller; no AVRL installation or project trust grant |
| Local regression | `PASS` | VORQA 56/56 and Foundation 22/22 on the selected candidate |
| Real Codex explicit path | `PARTIAL` | Prior isolated explicit invocation and trusted probe/status were observed |
| Automatic activation | `BEST-EFFORT / UNVERIFIED` | Direct selection telemetry absent; activation is not guaranteed |
| Complete AVRL lifecycle | `PARTIAL` | Approval/release-attestation remain human decisions; full lifecycle acceptance is not claimed |
| Native hooks | `EXCLUDED` | PR #15/#19 remain unmerged, rejected experiments; no native delivery claim |
| Installation and rollback | `DISPOSABLE PASS` | Previous disposable install/uninstall/rollback passed; normal profile remains outside scope |
| Package reproducibility | `PASS` | Minimal allowlisted ZIP, SHA-256 recorded; no hooks, cache, credentials, tests, controller or transcripts |
| CI / independent review | `PENDING EXACT FINAL HEAD` | Local tests do not substitute for GitHub Actions or an independent review of the final PR |
| Source rights | `BLOCKED` | File-specific basis for historical `workflow-transcript.md` remains unverified; do not add a repository-wide LICENSE or redistribute that item |
| Signer trust | `UNVERIFIED` | Signature presence alone does not establish authorized signer identity |

## Stop conditions

Keep public release `NO-GO` until source rights and signer provenance are established, exact-head CI and review pass, and the release owner approves the exact artifact. Do not infer human approval, independent review, or release-attestation from a model statement or fixture.
