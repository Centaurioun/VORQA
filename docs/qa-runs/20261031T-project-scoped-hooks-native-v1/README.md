# VORQA project-local hook isolation preflight — blocked

**Decision:** `PROJECT-SCOPED HOOKS BLOCKED`

## Scope and pinned artifacts

Codex CLI `0.166.0-alpha.5.1` was used. PR #15 was re-read from GitHub at head `a4de8a1c7402d787a37df130fa6f69cdc369bfb2` (open, draft, unmerged). A read-only working snapshot of the candidate was verified against that revision:

| File | SHA-256 |
|---|---|
| `dispatcher.py` | `fd12dba108512929f2d25b43331d6bea4a2447c2b41fd41f4557185c929d1b0f` |
| `bridge.py` | `c6f4a0c288579ef6e08d0028d0d81ecc8fa457d47ea1dd926e0040ec8c64fd24` |
| candidate `hooks.json` | `a82fd43cfe744c604a7cf845d72af05d829bc104e0e9c6faeff15884492c529b` |

The interpreter was Python 3.14.9. A fixture-local JSON configuration was constructed with absolute, shell-quoted paths to the pinned dispatcher and parsed successfully. This was a JSON parse check only; it does not prove Codex acceptance or delivery.

## Control A — unrelated Git fixture

Codex required and saved a folder-access trust decision before opening the fixture. `/hooks` then showed two installed `UserPromptSubmit` entries, one active: a user-config hook and a TokenEconomizer plugin hook. No VORQA hook source appeared. No hook-specific VORQA trust was changed and no user prompt was submitted.

This establishes source absence for that unrelated fixture at inspection time. It does **not** establish whether trusted hook hashes are project-scoped across other projects.

## Why Control B and native tests stopped

The disposable fixture's project-local `.codex/hooks.json` requires the project `.codex` layer to be trusted before Codex will load it. A one-invocation `projects.<path>.trust_level="trusted"` override did not remove the folder-access prompt. The only observed supported flow saved a project trust record in user-level Codex state.

Before proceeding, the test needed to demonstrate the fixture-local hook sources in `/hooks`, assess the trust scope, obtain approval for the exact fixture hook hash, and have a verified rollback path. The safety review rejected the attempted `/permissions` action while the TUI was showing an unrelated Daybreak security setup screen. No alternate route was used to edit trust state.

Accordingly:

- Control B `/hooks` discovery: **BLOCKED**.
- Fixture-local hook-hash trust: **NOT GRANTED**.
- Native `UserPromptSubmit` delivery, bridge invocation, negative routing, and `Stop` continuation: **NOT RUN**.
- Native VORQA hook deliveries: 0 observed; this is not a handler failure result.
- Model context delivery: **UNVERIFIED**.

The fixture hook files and Stop marker were removed after the block. A temporary unrelated-project trust entry remains and needs operator cleanup before the disposable folder is reused. No project-specific or global VORQA hook was trusted.

## Protected VORQA installation

Post-inspection `codex plugin list --json` reports `vorqa@vorqa-local` v0.1.0 installed and enabled. Its portable manifest, compatibility manifest, skill, and bridge hashes still match the saved baseline values. The candidate v0.2.0-alpha.1 was not installed. The inventory command could not refresh the remote marketplace catalogue because the endpoint was unavailable; its local installed list still returned VORQA.

No unit test, synthetic fixture run, native event test, or CI run is claimed by this report. No source code changed. Existing PRs #9–16 were not merged.

## Next milestone

First revoke the one temporary project trust record through the supported Codex UI and verify the folder is untrusted. Then repeat only the preflight with a reversible fixture-only trust mechanism: inspect both `/hooks` views, prove exact hash scope, obtain new approval for the fixture-local hashes, and only then begin native positive/negative prompt and Stop tests.
