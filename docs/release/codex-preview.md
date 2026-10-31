# VORQA Codex Preview — Scope and Evidence

**Product:** `0.2.0-preview.1`, hook-free explicit workflow. **Public release:** `NO-GO` pending source-rights and trusted-signing clearance.

The normal profile's `vorqa@vorqa-local` v0.1.0 diagnostic plugin remains a distinct installation. The preview adds an explicit `vorqa-workflow` skill and AVRL bridge. It does not bundle the controller or change project trust. The v0.2.0-alpha.1 native-hook experiment remains excluded; PR #15 and #19 were closed unmerged.

## Verified behavior and limits

- The candidate source passed 56 VORQA tests and 22 Foundation tests.
- Previous isolated real-Codex sessions observed explicit workflow/bridge use and successful trusted-controller `probe` and `status` operations.
- Disposable install, removal and exact-byte rollback to v0.1.0 were previously verified.
- Automatic skill activation is best-effort. Positive activation was partial; direct skill-selection telemetry remains unavailable.
- `probe` confirms expected structure, not trust. `status` reports `observed_unverified`; it is not PASS, approval, independent review, completion, or release readiness.
- Full lifecycle completion, normal-profile upgrade, native hooks and public release are not claimed.

The package SHA-256 and exact file inventory are recorded in the delivery manifest. The portable and Codex compatibility manifests both use version `0.2.0-preview.1`; `defaultPrompt` is 93 characters. The plugin archive excludes AVRL controller files, cache, credentials, tests, hooks and historical transcripts.

## Installation and use

Use the supported Codex marketplace and plugin CLI only after reviewing the [plugin guide](../../codex/plugin/vorqa/README.md). Test in a disposable profile first. Explicitly invoke `$vorqa-workflow`; do not rely on automatic routing.

The bridge's `verify` command executes project eval commands with the invoking user's environment and OS permissions. It is not a sandbox. Human approval and release-attestation require an authorized human through a separate governed process.

## Rights and release status

MIT was selected as the intended repository license, but no root LICENSE is included. The rights basis for historical `workflow-transcript.md` remains unverified. That file is not part of this plugin archive or the Codex delivery diff. Public release remains blocked until rights and signer provenance are supported. No GitHub Release or public plugin-directory publication is made by this preview.
