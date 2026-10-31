# VORQA for Codex — v0.2.0-preview.1

This hook-free preview provides the explicit `$vorqa-workflow` skill and a bridge to an existing, trusted AVRL workspace. It does not bundle or install AVRL.

## Install from the GitHub marketplace

Use a disposable Codex profile first. From the supported Codex CLI:

```sh
codex plugin marketplace add Centaurioun/VORQA --ref main
codex plugin marketplace list
codex plugin add vorqa@vorqa-local
codex plugin list --marketplace vorqa-local
```

The repository marketplace at `.agents/plugins/marketplace.json` resolves `vorqa` to `./codex/plugin/vorqa`. Verify that the installed manifest reports `0.2.0-preview.1`; a marketplace being listed does not prove plugin installation or skill execution. In profiles that already track a marketplace with this name, inspect its source before changing or replacing it. Do not overwrite plugin cache files manually.

## Use the workflow

In a repository that already contains the trusted controller and `specs/` tree, explicitly invoke `$vorqa-workflow` and request the stage you want. Automatic skill activation is best-effort and not guaranteed.

`probe` checks for the expected Git root, controller path and specs directory. It does not establish controller trust. `status --feature <slug>` invokes the pinned controller and reports state as `observed_unverified`; it is not PASS, approval, independent review, completion, or release readiness.

## Security boundaries

The bridge checks the pinned AVRL controller and helper SHA-256 before execution and fails closed on missing or mismatched sources. Do not copy a controller into an unrelated project or change the pin to accept project-provided code. `verify` runs commands in `specs/<feature>/eval.json` with the caller's environment and operating-system permissions; the bridge is not a sandbox. Inspect every command and referenced file before requesting it.

The bridge refuses to perform human `approve` and `release-attest` decisions; these require an authorized human through a separately governed process. Do not fabricate reviewer, QA, approval, or release receipts. No native hooks or MCP server are included.

## Remove and rollback

Use the supported CLI commands:

```sh
codex plugin remove vorqa@vorqa-local
codex plugin marketplace remove vorqa-local
```

For rollback, remove the preview with the CLI and install the previous exact, trusted version/source through its marketplace. Confirm the installed version with `codex plugin list`. Do not edit cache directories or `config.toml` by hand. Test rollback in a disposable profile before changing a profile that contains `vorqa@vorqa-local` v0.1.0.

## Evidence limits

The exact MVP source passed 56 VORQA tests and 22 Foundation tests locally. Real Codex explicit workflow and trusted-controller `probe/status` were previously observed; this does not prove automatic activation, complete lifecycle acceptance, native hook delivery, or release readiness. Repository-wide publication remains subject to source-rights clearance; no root LICENSE is added by this preview.
