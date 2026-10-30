# Codex adapter — developer preview (not certified)

The first Codex-specific package is under [plugin/vorqa](plugin/vorqa/) with portable `plugin.json`, a compatible `.codex-plugin/plugin.json`, one discoverable `vorqa-workflow` skill, and a small **read-only** Python bridge.

The original **v0.1.0** bridge package was installed on the user's Mac and tested: direct bridge and explicitly requested bridge calls worked, but ordinary model-driven automatic routing remained unverified/unsuccessful. This branch adds a **new, uninstalled v0.2.0-alpha.1 candidate** with plugin-bundled hook feasibility handlers. Neither native hook delivery nor a production QA gate has been verified; there is no MCP server.

## Experimental native hook pilot (uninstalled)

The experimental candidate includes [hooks/README.md](plugin/vorqa/hooks/README.md) and [two bounded hook handlers](plugin/vorqa/hooks/hooks.json). `UserPromptSubmit` may inject a short, read-only `probe` observation in a trusted initialized Git root. `Stop` does not gate ordinary work; a test-only fixture marker and environment flag allow one continuation for native acceptance testing. **The hook trust review is mandatory** and the candidate must not overwrite the currently installed v0.1.0 without operator consent. No global Codex settings, permissions or other plugins are changed here.

## Probe a trusted VORQA-initialized workspace

```bash
python3 codex/plugin/vorqa/scripts/bridge.py --workspace /path/to/existing/avrl-workspace probe
python3 codex/plugin/vorqa/scripts/bridge.py --workspace /path/to/existing/avrl-workspace status --feature example-signup
```

Commands above run from the **VORQA repository root**. Only point them at source you trust. The target Git repository must already contain `scripts/avrl.py` at its root and a `specs/` directory. The plugin does **not** install that controller into arbitrary applications.

The bridge returns machine-readable, bounded diagnostic metadata. Even `status: completed` is **observed only**, not a fresh verification of PASS evidence or genuine independent approval. The canonical AVRL controller still owns all approvals and final completion decisions.

Run the focused unit tests (safe disposable Git fixtures):

```bash
python3 -m unittest discover -s codex/plugin/vorqa/tests -v
```

## Activation evaluation infrastructure

This stacked follow-up adds an **opt-in** marketplace at `.agents/plugins/marketplace.json` and a versioned, ten-scenario evaluation matrix under [plugin/vorqa/eval/](plugin/vorqa/eval/). The test cases include both expected activation and **must-not-activate** requests.

The deterministic `acceptance_eval.py` checks a reported observation against local evidence hashes and rejects missing or mismatched entries. It intentionally reports `self_reported_artifact_checksum_only` and never certifies the Codex host's actual skill selection. Plugin Eval's structural analysis is a different test from real Codex activation. See [the native host acceptance task](plugin/vorqa/eval/CODEX_HOST_TASK.md).

The marketplace makes the package discoverable but **does not install, enable or auto-run it**; no user or global Codex config is changed. Native activation is still unverified.

## Next acceptance gates

1. **Native Codex plugin discovery** on the actual installed Codex Desktop/CLI, including skill selection with positive and negative user requests.
2. **Runtime deployment design**: safely supply the canonical controller to external application repositories without copying Claude-specific hook semantics.
3. **Controlled full workflow**: verify actual Codex tool/agent events and controller state; never infer native host events from synthetic data.
4. **Plugin Eval**: activation rate, false triggers, model/tool calls and real acceptance scenarios.

See [Superpowers design](../docs/superpowers/specs/2026-10-31-codex-plugin-foundation-design.md), [implementation plan](../docs/superpowers/plans/2026-10-31-codex-plugin-foundation.md), and [Codex architecture assessment PR #10](https://github.com/Centaurioun/VORQA/pull/10).

Claude-specific hooks must not be copied into Codex without verifying their actual support and enforcement. No branch protection or additional isolation infrastructure is introduced here.
