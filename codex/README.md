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


## Opt-in AVRL project setup and reproducible positive demo

The Codex plugin remains hook-free and does **not** install its controller automatically.
From a reviewed checkout of this repository, a repository-side setup utility is available:

```sh
python3 scripts/codex_avrl_setup.py smoke
```

The command creates an isolated temporary Git fixture using the pinned AVRL controller
and the published example feature specification, runs the real controller's **init**
only in that disposable fixture, then invokes the actual Codex bridge's `probe`
and `status --feature example-signup`. It removes the fixture afterwards.
The expected result is `POSITIVE_PROBE_STATUS_PASS` with `observed_unverified`,
**not** acceptance, independent review, or a release attestation. No hooks are enabled.

To prepare a separate, clean, trusted **existing Git repository** for explicit
AVRL usage, first review the code and inspect the dry-run:

```sh
python3 scripts/codex_avrl_setup.py install --workspace /path/to/project
# Only after reviewing the exact destination and source:
python3 scripts/codex_avrl_setup.py install --workspace /path/to/project --apply
```

This opt-in action copies the pinned controller, event recorder, and generic browser
helpers to `scripts/` **without overwriting existing files**; it does not copy
Claude hooks, initialize a feature, add test specifications, obtain project trust,
modify an existing Git history, or grant approval. It refuses non-Git, nested,
dirty, or symlinked/conflicting workspaces. Review the added files before committing;
add `.avrl/` and `specs/*/state.md` to the project's `.gitignore` as appropriate,
author real project-specific PRD/eval/browser scenarios and commit them on the proper
feature branch, then obtain the required human decisions separately.

The source checkout, not the plugin-only ZIP, provides the canonical AVRL runtime.
Use this utility only after explicitly deciding to introduce that runtime into the
target repository. **This is not an OS sandbox**: project-defined verification
commands can run with the invoking user's privileges. A positive smoke test
does not certify the full lifecycle or native Claude/Codex hook delivery.
