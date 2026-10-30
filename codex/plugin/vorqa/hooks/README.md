# VORQA Codex native hook pilot — NOT production enforcement

Package: `vorqa` `0.2.0-alpha.1`. This directory is a **local-only feasibility experiment**. Its presence in a PR does not update the user's installed `0.1.0` package or trust hooks in Codex.

## Architecture and safety

The portable plugin defaults to `hooks/hooks.json` discovery. The hook configuration has two synchronous command handlers. Codex must independently discover and trust their exact definitions.

- `UserPromptSubmit`: its native `matcher` is ignored, so `dispatcher.py` uses conservative deterministic selection in **already AVRL-initialized Git roots**; irrelevant prompts are silent. Qualified prompts cause a read-only `bridge.py probe`. Output is a fixed, short `additionalContext` message with `controller_present`, no raw prompt, workspace path, private controller state, claimed QA PASS or recorded human approval. This context is guidance to the model, not an automatic test/review execution or a security gate.
- `Stop`: normally returns `{"continue":true}`. It **never blocks normal tasks**. In a disposable Git fixture only, an operator can set `VORQA_HOOK_STOP_PROBE=1` **and** create an ignored file `.avrl/hook-pilot-stop-fixture` containing exactly `VORQA_HOOK_PILOT_V1`. Only then does an initial Stop return `{"decision":"block",...}`; when `stop_hook_active` is true it does not ask to continue again. This exercises the host's continuation mechanism without claiming release gating.

The hook subprocess never executes untrusted `scripts/avrl.py`; it only calls the already tested bridge `probe`, which checks controller file presence and Git root. Probe failure is silent, not success. No network, external API, MCP, telemetry upload, or persistent writes. The script intentionally fails open on malformed hook input; **it is not a security boundary**.

## Before any native installation

1. Confirm `codex --version`, current `vorqa@vorqa-local` package version/ SHA, and official support for plugin-bundled hooks on this exact Codex build. Read the CLI's `/hooks` trust UI.
2. Preserve the installed `0.1.0` cache and its pinned marketplace SHA. Test `0.2.0-alpha.1` only via an operator-approved opt-in local candidate marketplace/revision. Do not mutate existing plugin cache or disable other plugins.
3. Trust **only the candidate VORQA hooks** after checking the definition hash and shell commands; do not use `--dangerously-bypass-hook-trust`, global config changes, or privileged tool approvals.
4. Use disposable AVRL-initialized and unrelated Git fixtures. Keep raw JSONL and prompt input under ignored `.avrl/codex-eval/<run-id>/`. Do not log private user prompts or publicize local paths.

## Native acceptance sequence

- **Gate 1:** Without trusting the new hooks, verify they remain skipped and `0.1.0` stays unchanged.
- **Gate 2:** After operator approval, verify real Codex host delivery of `UserPromptSubmit` once for an initialized fixture, with the expected bounded hook context and real read-only bridge `probe` evidence. Verify irrelevant/uninitialized prompts produce no VORQA context.
- **Gate 3:** In a single disposable fixture, explicitly enable the Stop pilot environment and ignored marker, verify exactly one host continuation; ensure `stop_hook_active` prevents a loop. Remove marker/environment; repeat to verify zero continuation.
- **Gate 4:** Report native observed hook events separately from Python fixture tests. No 10-case automatic-skill selection benchmark until the intended hook-driven workflow is defined and observed.
- **Rollback:** Disable/untrust only the candidate hooks through supported Codex UI, then return to pinned `0.1.0`; verify plugin inventory unchanged apart from the approved candidate. Never delete another installed plugin.

## Local tests

`python3 -m unittest discover -s codex/plugin/vorqa/tests -v`

This suite validates dispatcher output shape, privacy, routing, and one-shot Stop semantics. **It does not verify Codex hook discovery, trust, event delivery, or actual model behavior.** Native host evidence is required for those claims.
