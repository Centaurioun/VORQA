# Codex host acceptance task — operator handoff

Run this task **in Codex on the Mac that has access to the VORQA repository** after checking out the branch containing this evaluation harness. It is not an instruction to execute it in GitHub Actions.

## Mission

Act as a QA engineer. Evaluate whether the local VORQA plugin is available and selected correctly, without fabricating host events or altering production repositories.

1. Inspect `git status`, `codex --version`, installed Plugin Creator and Plugin Eval, Codex plugin help, and the local `.agents/plugins/marketplace.json`. Preserve all existing settings and uncommitted changes.
2. Check if VORQA has **already been explicitly enabled**. If not, do not silently install it; report `BLOCKED: plugin not enabled` and continue static evaluation. Ask for the operator's explicit installation approval before changing plugin state.
3. Run `plugin-eval analyze codex/plugin/vorqa --format markdown` if the CLI exists. Store output only under ignored `.avrl/codex-eval/<run-id>/`; if unavailable, mark static analysis BLOCKED and continue.
4. For native trials use the ten prompts from `eval/scenarios.json` **unchanged**, each in a fresh Codex session. Use a disposable Git copy of an initialized AVRL fixture for `initialized` cases and an unrelated disposable Git project for `not_initialized` cases. Do not touch real user repositories beyond read-only inspection. Do not change the prompts in an attempt to force activation.
5. Capture the host's actual skill-selection evidence if exposed and any `probe`, `status`, or `controller:<allowlisted-command>` bridge calls. When such evidence is unavailable, report an unverified observation rather than guessing based on the assistant's text. Separate human inference from host logs.
6. Write metadata observations exactly in the JSON schema in the README; keep raw logs inside ignored `.avrl/`, compute SHA-256 for each referenced local evidence file. Run `acceptance_eval.py` to generate a summary. Never upload raw conversations, credentials, home paths or browser storage.
7. Compare Plugin Eval's **static** findings to the native trials. Record plugin revision, Codex version, number of completed/failed/blocked/NOT_RUN trials, false positives, false negatives, bridge-call mismatches, performance if the host exposes it, and clear remaining gaps.
8. If a failure belongs to this harness, fix it with a failing regression test on a new branch. If the plugin itself needs changes, write a separate prioritized proposal first. Do not weaken negative activation criteria to make the score appear better.
9. Publish sanitized test coverage, environment and a compact result as a PR **only if actual host trials were executed**. If all trials are blocked, report blockers without generating an artificial success PR. Never merge automatically.

## Required verdict

Use **NATIVE OBSERVED**, **SELF-REPORTED**, **BLOCKED**, or **NOT RUN** precisely. Static plugin-eval success alone is not a native host pass.

No new global configuration, forced plugin installation, branch protection, Cloud API, MCP server or sandboxing is authorized by this handoff.
