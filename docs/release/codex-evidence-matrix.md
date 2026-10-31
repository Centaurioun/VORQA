# Codex Preview Evidence Matrix

This record separates source tests, host observations and release decisions. Local or model-reported results are not elevated into stronger evidence classes.

| Claim | Identity / evidence | Result | Boundary |
| --- | --- | --- | --- |
| Selected product | Hook-free VORQA `0.2.0-preview.1`, derived from main `29ad871abe16515cfa8ffe2fbc1dcf0a4ce3f33b` | Portable and Codex compatibility manifests agree on name/version; default prompt is 93 characters | No native hooks are included |
| Local tests | Selected source candidate; VORQA unittest suite and Foundation suite | 56/56 and 22/22 PASS | Unit tests do not establish host execution |
| Real Codex explicit path | Previous isolated Codex session, candidate skill and bridge | Explicit bridge/probe/status behavior observed on trusted AVRL controller | Not a complete lifecycle or a fresh install of the archived artifact |
| Automatic activation | Prior positive/negative prompt tests | Positive routing partial; negative controls passed; direct selection telemetry unavailable | Best-effort only; no guaranteed activation |
| Controller state | Pinned AVRL controller SHA-256 and helper SHA-256; prior isolated `probe` and `status` | Probe and valid-feature status passed; status classified `observed_unverified` | Not approval, verified QA PASS, completion, or release readiness |
| Install and rollback | Prior disposable Codex profile, supported plugin CLI | Preview install/uninstall and exact-byte v0.1.0 rollback passed | Does not authorize modifying the normal profile |
| Package | Local archive `vorqa-0.2.0-preview.1-codex.zip` | SHA-256 `8e15a8f934874ffd364bd0996a25d80e09ea7b858415bca829a0535bfd712a7c`; deterministic allowlisted package | Excludes controller, cache, credentials, tests, hooks and transcripts |
| Native hooks | Historical PR #15/#19 experiments | Excluded; host delivery was not accepted | No hook support is claimed |
| Public release rights | Root repository policy and unresolved rights basis for historical `workflow-transcript.md` | BLOCKED | No root LICENSE or public release until rights are supported |
| Signer provenance | Prior SSH signature presence; authorized signer identity remains unverified | UNVERIFIED | Does not establish trusted release provenance |

## Classification

- `SOURCE-VERIFIED`: exact source files/manifests inspected.
- `UNIT-TESTED`: named local suite result on the selected source.
- `HOST-OBSERVED`: host command or bridge behavior directly observed.
- `UNVERIFIED`: no direct evidence sufficient for the claim.
- `BLOCKED`: a required release condition is unmet.

A successful probe confirms structural availability, not trust. `observed_unverified` remains an observation only. Human approval, independent review, real QA and release-attestation must be evidenced separately.
