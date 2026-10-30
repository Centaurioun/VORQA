# VORQA Codex skill-context budget and native smoke QA

**Run date:** 2026-10-31
**Evaluation baseline:** PR #12 head `b5efb79615cd305fbc33ad57f96b31830d9e2811`
**Codex CLI:** `0.166.0-alpha.5.1`
**Configured model:** `gpt-6-luna`, model catalog context window `272,000` tokens
**Installed plugin:** `vorqa@vorqa-local` `0.1.0`, installed and enabled
**Result:** `ROOT CAUSE IDENTIFIED — REMEDIATION PENDING`

## Summary

The prior overflow is explained by Codex's available-skills catalog budget. With this model, the documented default is 2% of the 272,000-token context window: 5,440 tokens. The controlled `skills.max_context_tokens=10000` prompt-input render exposed VORQA's skill name and description; the default render did not. The 10,000-token override was passed only to individual CLI commands, and no persistent Codex setting was changed.

That visibility result did not establish automatic activation. Three fresh native smoke sessions under the override completed without a budget warning, but neither positive scenario invoked the required VORQA bridge calls. The conceptual negative scenario made no bridge call. Codex emitted no direct skill-selection event, and the per-session model input was not exported, so skill selection and scenario-specific visibility remain unverified. The smoke gate failed; the other seven scenarios were not rerun.

The local PR #12 plugin test suite also exposed a separate evidence-validator bug on macOS: it rejected valid evidence when the evidence root sat beneath a symlinked temporary-directory alias. A regression test was observed failing before a minimal fix, then the focused test and all 22 plugin tests passed locally. This fixes evidence-path validation only; it does not change VORQA activation behavior.

## Environment and catalog inventory

The Codex inventory showed 77 installed plugins, 71 enabled plugins, 10 registered marketplaces, and one enabled VORQA plugin at `0.1.0`. The VORQA marketplace cache resolved to the exact PR #12 SHA above. The portable root manifest and compatibility manifest both identify version `0.1.0`; the package contains one `vorqa-workflow` skill. No VORQA-specific `skills.config` override was present.

The A/B comparison used the same PR #12 checkout, configured model, plugin inventory, prompt-input probe, and CLI version. Only the one-command budget override differed. The prompt-input JSON was stored privately because it contains conversation and local environment context.

| Prompt-input condition | Budget | Skill entries rendered | Descriptions rendered | VORQA name and description |
|---|---:|---:|---:|---|
| A — default | 5,440 tokens (2% of context) | 220 | 0 | Not visible |
| B — command-local override | 10,000 tokens | 269 unique paths | 269 | Visible in the rendered catalog |

Condition B contained about 15,317 description characters, approximately 3,830 tokens using a coarse four-characters-per-token estimate. This is an estimate, not tokenizer output. The A render contained no skill descriptions and omitted 49 additional entries. Previous native default-budget logs recorded Codex's overflow diagnostic saying all skill descriptions were removed; across those trials, the count of additional omitted skills varied from 49 to 336. The new prompt-input A render did not itself contain the warning text.

The official configuration reference documents the default as 2% of the model context window and caps explicit values at 10,000 tokens. The skill guide says large catalogs may shorten descriptions and omit skills and that a selected skill still loads its complete instructions. See [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) and [Build skills](https://learn.chatgpt.com/docs/build-skills).

## Root-cause hypotheses

| Hypothesis | Status | Evidence and limit |
|---|---|---|
| 1. The default catalog budget is too small for the installed skill catalog. | **CONFIRMED** | The current model's default is 5,440 tokens. A rendered 220 skill entries without descriptions and omitted 49; the one-command 10,000-token comparison rendered 269 descriptions, including VORQA. Prior native default sessions emitted the all-descriptions-removed overflow diagnostic. |
| 2. Codex CLI 0.166.0-alpha.5.1 has a catalog-processing bug. | **REJECTED as the cause of the observed overflow** | The installed CLI accepted the documented `-c skills.max_context_tokens=10000` override, and its rendered catalog changed as expected. The default behavior matches the documented overflow fallback. This does not rule out an unrelated selection defect. |
| 3. Marketplace discovery duplicated or repeated VORQA skills. | **REJECTED for VORQA** | One enabled VORQA plugin, one unique VORQA skill path, and one VORQA catalog entry appeared. Other installed plugins were left untouched. |
| 4. VORQA's manifest or trigger description prevents selection. | **UNVERIFIED** | The package identities and versions match. Plugin Eval flags the skill description as a weak trigger, and positive smoke bridge calls were absent even though the separate 10,000-token prompt-input render included the VORQA row. The smoke sessions expose neither selection nor their full input, so description causality is not isolated. |
| 5. An enabled plugin is not transferred into each native session's model context. | **UNVERIFIED per native session** | VORQA is present in the 10,000-token debug render and the CLI inventory marks it enabled. The three session logs do not expose per-session skill descriptions or selection. |
| 6. A model or context-window change explains the A/B difference. | **REJECTED for the controlled A/B result** | The model and 272,000-token context window were held constant; only the command-local budget differed. The model used by each JSONL trial was not recorded as a field in the event stream. |
| 7. Host telemetry is insufficient to distinguish selection from non-selection. | **CONFIRMED** | No `skill_selected` event appeared in the three new sessions or the prior ten. CLI lifecycle and command events do not prove skill selection. |

## Native smoke results

The original scenario prompts were used unchanged. Each ran in a new ephemeral CLI session on a disposable initialized fixture. The fixtures were separate from the VORQA source checkout and user projects. All three turns completed under the one-command 10,000-token override; none emitted the prior budget warning. The actual session JSONL did not include direct prompt-input or skill-selection telemetry.

| Scenario | VORQA description visible in that session | Expected bridge calls | Observed bridge calls | Duration | Input / output tokens | Result |
|---|---|---|---|---:|---:|---|
| `explicit-probe-existing` | **UNVERIFIED** — no per-session input trace | `probe` | None | 17.65 s | 148,600 / 570 | **Workflow mismatch:** expected call missing; activation unverified |
| `explicit-status-existing` | **UNVERIFIED** — no per-session input trace | `probe`, `status` | None | 16.17 s | 194,391 / 567 | **Workflow mismatch:** expected calls missing; activation unverified |
| `conceptual-explanation-existing` | **UNVERIFIED** — no per-session input trace | None | None | 7.48 s | 35,486 / 44 | No false-positive bridge call observed; selection unverified |

Across these sessions, two expected-positive workflows missed their bridge contract. This is not reported as two independently observed false-negative skill selections: the host did not expose selection telemetry. No false-positive bridge call was observed in the conceptual negative case. No session field provided a model identifier; the configured model at test time was `gpt-6-luna`.

The local `acceptance_eval.py` result is **INCOMPLETE**: 3 `BLOCKED`, 7 `NOT_RUN`, 0 `PASS`, 0 `FAIL`. The evaluator correctly blocks activation scoring when `selected_skill` is unknown. This schema verdict is reported separately from the observed missing bridge calls above.

The ten-case matrix was not run because the positive smoke bridge calls did not match. This follows the runbook gate and avoids repeating the previous ten default-budget runs without a successful remediation signal.

## Plugin Eval and package review

Plugin Eval `0.1.2` returned **0/100, grade F, high risk: 12 failures, 3 warnings, 2 informational checks** on the PR #12 plugin source. This is static analysis, not an activation score.

All 12 failures again inspect `.codex-plugin/plugin.json` as if it were the canonical portable manifest:

1. `manifest-missing-author` — `author` exists in the portable root `plugin.json`.
2. `manifest-missing-interface` — the portable interface is at `extensions.com.openai.interface`.
3. `interface-missing-displayName` — present in the portable interface.
4. `interface-missing-shortDescription` — present.
5. `interface-missing-longDescription` — present.
6. `interface-missing-developerName` — present.
7. `interface-missing-category` — present.
8. `interface-missing-capabilities` — present.
9. `interface-missing-websiteURL` — absent; not a local Codex installation requirement. Public-listing metadata was not assessed.
10. `interface-missing-privacyPolicyURL` — absent; not a local Codex installation requirement. Public-listing metadata was not assessed.
11. `interface-missing-termsOfServiceURL` — absent; not a local Codex installation requirement. Public-listing metadata was not assessed.
12. `interface-missing-defaultPrompt` — present in the portable interface.

The three absent URL fields are not claimed as present. They do not explain the local CLI installation, which remains enabled. Plugin Creator's package guidance and the official package documentation treat root `plugin.json` as the portable package manifest and `.codex-plugin/plugin.json` as a compatibility fallback for clients that need it; root identity and portable components remain canonical. No manifest changes were made. See [Codex plugin packaging guidance](https://developers.openai.com/plugins/build/plugins).

The three warnings were `description-trigger-weak` (actionable selection risk), Python cyclomatic complexity 72, and 9 long Python lines. The informational findings include unavailable coverage artifacts. The 0/100 static result is not native activation evidence.

## Harness regression and remediation

The PR #12 local plugin test suite initially ran 21 tests with 19 passing and 2 failing. Both failures were valid evidence being returned as invalid under a temporary directory whose path traversed a system symlink. A new regression test first reproduced the rejection (RED). The minimal fix now checks symlinks only for the file and directories beneath the supplied evidence root, while retaining the resolved-path containment check. Existing direct-file symlink escape rejection remains covered.

- Focused regression: **RED before fix**, **1/1 GREEN after fix**.
- Complete Codex plugin local unittest suite after fix: **22/22 passed**.
- `git diff --check`: clean.
- The fix changes only the local acceptance evaluator's evidence-path validation and its test. It does not alter plugin manifests, skill text, dependencies, global Codex configuration, marketplace entries, or installed plugin state.

These are local test results. GitHub CI for the new PR is pending and must finish before CI can be reported as passing.

## Hooks and observability

VORQA declares no hooks and has no `hooks/hooks.json`; no hook event was observed. Native CLI JSONL showed session/turn/item lifecycle events (`thread.started`, `turn.started`, `item.started`, `item.completed`, `turn.completed`) and no direct skill-selection event. Command/tool events can prove an observed bridge invocation, but absence of a bridge invocation cannot independently distinguish a skill that was not selected from a selected skill that did not call its bridge.

## Remediation decision and next steps

No permanent budget or other Codex setting was changed. The documented command-local 10,000-token override restores the VORQA row in `debug prompt-input` and suppresses the overflow diagnostic in the three smoke sessions, but it did not produce expected bridge calls. No VORQA plugin version, skill description, or manifest change is justified by these observations alone.

Priorities:

1. Obtain supported per-session skill-input or skill-selection telemetry from Codex, or a supported way to render the exact input of each `codex exec` session.
2. Evaluate a proposed clearer VORQA trigger description in a separate plugin revision and controlled rollout; do not replace the installed `0.1.0` package without rollback evidence.
3. Re-run the three smoke scenarios only after the exact native-session visibility condition can be verified. Run the full ten-case matrix only if positive smoke bridge calls match and the negative remains free of bridge calls.
4. Improve Plugin Eval to validate the portable root manifest and compatibility overlay against their distinct schemas.

## Privacy and evidence

Raw prompt-input JSON, native session JSONL, CLI inventories, stderr, fixtures, and local paths remain under the Git-ignored `.avrl/` run directory. The PR includes only this sanitized report and the minimal evaluator regression fix. A private SHA-256 manifest covers local evidence files; it does not publish transcript content or identifiers.

## References

- [PR #12](https://github.com/Centaurioun/VORQA/pull/12)
- [PR #13 historical native activation report](https://github.com/Centaurioun/VORQA/pull/13)
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Codex plugin packaging guidance](https://developers.openai.com/plugins/build/plugins)
