# Codex adapter — developer preview (not certified)

The first Codex-specific package is under [plugin/vorqa](plugin/vorqa/) with portable `plugin.json`, a compatible `.codex-plugin/plugin.json`, one discoverable `vorqa-workflow` skill, and a small **read-only** Python bridge.

This preview is **not installed on the user's Mac** and has **not been executed as a native Codex plugin**. Plugin auto-activation and lifecycle hook delivery are unverified; this package intentionally contains no hooks or MCP server.

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

## Next acceptance gates

1. **Native Codex plugin discovery** on the actual installed Codex Desktop/CLI, including skill selection with positive and negative user requests.
2. **Runtime deployment design**: safely supply the canonical controller to external application repositories without copying Claude-specific hook semantics.
3. **Controlled full workflow**: verify actual Codex tool/agent events and controller state; never infer native host events from synthetic data.
4. **Plugin Eval**: activation rate, false triggers, model/tool calls and real acceptance scenarios.

See [Superpowers design](../docs/superpowers/specs/2026-10-31-codex-plugin-foundation-design.md), [implementation plan](../docs/superpowers/plans/2026-10-31-codex-plugin-foundation.md), and [Codex architecture assessment PR #10](https://github.com/Centaurioun/VORQA/pull/10).

Claude-specific hooks must not be copied into Codex without verifying their actual support and enforcement. No branch protection or additional isolation infrastructure is introduced here.
