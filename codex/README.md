# Codex adapter — v0.2.0-preview.1

VORQA's hook-free Codex preview contains the portable plugin manifest, the Codex compatibility manifest, the `vorqa-workflow` skill and a bounded bridge to a pre-existing AVRL workspace. The normal user profile's previously installed `vorqa@vorqa-local` v0.1.0 is a separate installation; do not assume GitHub changes update its cached copy.

The exact plugin and user guide are in [plugin/vorqa](plugin/vorqa/README.md). The GitHub marketplace at `.agents/plugins/marketplace.json` points to `./codex/plugin/vorqa` and makes the package available; it does not install or enable the plugin.

## Install from GitHub

On a disposable Codex profile, use supported CLI commands:

```sh
codex plugin marketplace add Centaurioun/VORQA --ref main
codex plugin marketplace list
codex plugin add vorqa@vorqa-local
codex plugin list --marketplace vorqa-local
```

After installing, verify the manifest version and explicitly invoke `$vorqa-workflow`. Use `codex plugin marketplace upgrade` only when refreshing a Git-backed source. Do not edit Codex configuration or plugin cache files manually. If the marketplace name is already configured, inspect its source before replacing anything.

## Runtime evidence and limits

The v0.2.0-preview.1 source passed 56 VORQA tests and 22 Foundation tests. Earlier isolated host runs observed explicit skill/bridge invocation and trusted-controller `probe`/`status`; they do not establish that the final changed default prompt was reloaded, that activation is automatic, or that the complete lifecycle is accepted. Automatic skill activation is best-effort. Native hooks are excluded and unverified.

`probe` is a structural availability check. `status` reports `observed_unverified`, not PASS, approval, review, completion, or release readiness. The bridge verifies pinned controller source before running it and does not initialize/copy AVRL into a project. Its explicitly requested **state-changing** stages include `controller round`, `controller verify`, `controller review`, `controller blind` and `controller complete`. `controller approve` and `controller release-attest` stop with `operator_handoff_required`; only an authorized human may perform those decisions through a separately governed process. `verify` executes project-defined commands with the user's OS permissions; this bridge is **not an OS sandbox**.

No repository-wide LICENSE is included. The selected license intent does not resolve rights for every historical item; this preview excludes transcripts and hook experiments. Public release remains pending source-rights clearance.
