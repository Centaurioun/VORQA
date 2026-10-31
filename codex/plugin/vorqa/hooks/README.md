# VORQA Codex native hook pilot — NOT production enforcement

Package: `vorqa` `0.2.0-alpha.1`. This directory is a **local-only feasibility experiment**. Its presence in a PR does not update the user's installed `0.1.0` package or trust hooks in Codex.

## Architecture and safety

The Codex compatibility manifest explicitly points to `./hooks/hooks.json`; Codex also supports the default `hooks/hooks.json` path when a manifest omits `hooks`. The first acceptance candidate registers one synchronous `UserPromptSubmit` handler. Codex must independently discover and trust that exact definition.

- `UserPromptSubmit`: its native `matcher` is ignored, so `dispatcher.py` uses conservative deterministic selection in **already AVRL-initialized Git roots**; irrelevant prompts are silent. Qualified prompts cause a read-only `bridge.py probe`. Output is a fixed, short `additionalContext` message with `controller_present`, no raw prompt, workspace path, private controller state, claimed QA PASS or recorded human approval. This context is guidance to the model, not an automatic test/review execution or a security gate.
**Stop scope:** The dispatcher retains its `Stop` implementation and fixture tests, but `hooks.json` does not register `Stop` in this first candidate. No Stop continuation behavior is changed or included in this package.

The hook subprocess never executes untrusted `scripts/avrl.py`; it only calls the already tested bridge `probe`, which checks controller file presence and Git root. Probe failure is silent, not success. No network, external API, MCP, telemetry upload, or persistent writes. The script intentionally fails open on malformed hook input; **it is not a security boundary**.

## Before any native installation

1. Confirm `codex --version`, current `vorqa@vorqa-local` package version/ SHA, and official support for plugin-bundled hooks on this exact Codex build. Read the CLI's `/hooks` trust UI.
2. Preserve the installed `0.1.0` cache and its pinned marketplace SHA. Test `0.2.0-alpha.1` only via an operator-approved opt-in local candidate marketplace/revision. Do not mutate existing plugin cache or disable other plugins.
3. Trust **only the candidate VORQA hooks** after checking the definition hash and shell commands; do not use `--dangerously-bypass-hook-trust`, global config changes, or privileged tool approvals.
4. Use disposable AVRL-initialized and unrelated Git fixtures. Keep raw JSONL and prompt input under ignored `.avrl/codex-eval/<run-id>/`. Do not log private user prompts or publicize local paths.

## Native acceptance sequence

- **Gate 1:** Without trusting the new hooks, verify they remain skipped and `0.1.0` stays unchanged.
- **Gate 2:** After operator approval, verify real Codex host delivery of `UserPromptSubmit` once for an initialized fixture, with the expected bounded hook context and real read-only bridge `probe` evidence. Verify irrelevant/uninitialized prompts produce no VORQA context.
- **Gate 3:** Report native observed `UserPromptSubmit` events separately from Python fixture tests. No 10-case automatic-skill selection benchmark until the intended hook-driven workflow is defined and observed.
- **Rollback:** Disable/untrust only the candidate hooks through supported Codex UI, then return to pinned `0.1.0`; verify plugin inventory unchanged apart from the approved candidate. Never delete another installed plugin.

## Local tests

`python3 -m unittest discover -s codex/plugin/vorqa/tests -v`

This suite validates dispatcher output shape, privacy, routing, retained Stop guards, and the plugin manifest/event contract. **It does not verify Codex hook discovery, trust, event delivery, or actual model behavior.** Native host evidence is required for those claims.
