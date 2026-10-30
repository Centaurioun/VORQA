# VORQA Codex plugin native activation QA

**Run date:** 2026-10-31  
**Plugin revision:** `b5efb79615cd305fbc33ad57f96b31830d9e2811` (PR #12 head)  
**Codex CLI:** `0.166.0-alpha.5.1`  
**Installed plugin:** `vorqa@vorqa-local` `0.1.0`, listed as `installed, enabled`

## Verdict

**NATIVE OBSERVED — activation failed for the five expected-positive cases because Codex removed skill descriptions from the model-visible context after a skill-context budget overflow.** This is a real host diagnostic from each run, not an inference from the assistant’s wording. The plugin was installed and enabled, but its workflow was not available for automatic selection in these sessions.

All ten catalog prompts ran unchanged in ten fresh, independent, ephemeral Codex CLI sessions on disposable Git repositories. Every turn completed. Codex’s JSONL stream did not include a direct `skill_selected` event. Instead, each session emitted the host diagnostic that the skill context budget was exceeded and all skill descriptions were removed. No VORQA bridge invocation appeared in any session.

No case is reported as a full PASS. Five expected activations are false-negative workflow outcomes. Four also missed their required bridge calls. The five negative cases produced no bridge calls, so no false-positive bridge use was observed; direct skill selection remains unobservable and those cases do not establish a clean false-positive rate under normal skill visibility.

## Installation and source verification

The official Codex CLI marketplace command registered `Centaurioun/VORQA` at the exact PR #12 head SHA. The CLI reported the marketplace root and installed `vorqa` at version `0.1.0`; a fresh `codex plugin list` showed `vorqa@vorqa-local` as enabled. The cached marketplace `HEAD` matched the pinned SHA. The before/after inventory contains exactly one added marketplace (`vorqa-local`) and one added plugin (`vorqa@vorqa-local`); no other marketplace registration or plugin state was intentionally changed.

Remote marketplace discovery returned a network warning both before and after setup. It did not prevent the local marketplace and plugin inventory from being read. One Codex session also logged an unrelated existing marketplace refresh timeout during startup; it did not complete, no other marketplace was registered or installed, and the local marketplace working tree remained clean. Identifying details for that unrelated source are retained only in the private `.avrl/` logs.

## Native scenario matrix

`selected_skill` is **UNVERIFIED** in every row: Codex emitted no direct skill-selection event. The host’s budget diagnostic states that skill descriptions were removed from the model-visible list. Observed bridge calls below come from actual Codex JSONL tool-call records, not assistant claims.

| Scenario | Expected activation | Expected bridge calls | Observed bridge calls | Result |
|---|---:|---|---|---|
| `explicit-probe-existing` | Yes | `probe` | None | **FAIL — false-negative workflow; required call missing** |
| `explicit-status-existing` | Yes | `probe`, `status` | None | **FAIL — false-negative workflow; required calls missing** |
| `regression-repair-existing` | Yes | `probe` | None | **FAIL — false-negative workflow; required call missing** |
| `security-review-existing` | Yes | `probe` | None | **FAIL — false-negative workflow; required call missing** |
| `explicit-adoption-not-installed` | Yes | None | None | **FAIL — false-negative activation; no skill available to select** |
| `trivial-typo-existing` | No | None | None | **UNVERIFIED selection; no bridge call** |
| `conceptual-explanation-existing` | No | None | None | **UNVERIFIED selection; no bridge call** |
| `uninitialized-unrelated-coding` | No | None | None | **UNVERIFIED selection; no bridge call** |
| `quoted-vorqa-not-requested` | No | None | None | **UNVERIFIED selection; no bridge call** |
| `nonsoftware-question` | No | None | None | **UNVERIFIED selection; no bridge call** |

The first typo run had the typo in the wrong fixture file, so a new isolated fixture was created with the typo in `README.md` and the unchanged catalog prompt was run again in a fresh session. The corrected run is the matrix result; the initial attempt remains only in local evidence.

### Counts and evidence limits

- Native sessions: **10/10 completed**, with 10 unique session IDs retained locally.
- Skill-context overflow diagnostics: **10/10**.
- Direct skill-selection events: **0 observed**.
- VORQA bridge calls: **0 observed**.
- Expected-positive cases: **5 false-negative workflow outcomes**; **4/5** additionally missed expected bridge calls.
- Expected-negative cases: **0 false-positive bridge calls observed**; direct activation is unverified because skill-selection telemetry was not emitted and skill descriptions were unavailable.
- Codex JSONL lifecycle events observed: `thread.started`, `turn.started`, `item.started`, `item.completed`, and `turn.completed`. These are session/turn events, not VORQA activation or hook events.
- Wrapper-measured turn durations ranged from about **7 to 45 seconds** for the instrumented sessions; one session’s duration was not recorded by the wrapper.

## Plugin Eval static result and review of all 12 failures

Plugin Eval `0.1.2` returned **0/100, grade F, high risk**, with 12 failed checks, 3 warnings, and 2 informational checks. The 12 failures all target `.codex-plugin/plugin.json`. Plugin Eval’s plugin evaluator unconditionally reads that compatibility manifest and requires a top-level `author`, a top-level `interface`, and ten top-level interface fields.

VORQA also has the canonical portable `plugin.json`. It contains `author` and the `extensions.com.openai.interface` object. The Plugin Creator package guidance describes the root manifest as canonical for portable packages and `.codex-plugin/plugin.json` as a Codex compatibility fallback; OpenAI’s package documentation also says the root `extensions.com.openai` object supplies OpenAI-specific settings instead of merging with the compatibility overlay. The official CLI independently recognized and installed the VORQA package from the pinned marketplace and marked it enabled. Thus these 12 static errors do **not** establish a Codex installation or activation defect.

| Plugin Eval check | Static complaint | Evidence-based disposition |
|---|---|---|
| `manifest-missing-author` | No `author` in `.codex-plugin/plugin.json` | **False positive for local Codex compatibility.** The portable root manifest has `author`; author is root metadata. |
| `manifest-missing-interface` | No top-level `interface` in compatibility manifest | **False positive for local Codex compatibility.** The portable root manifest has `extensions.com.openai.interface`. |
| `interface-missing-displayName` | Missing display name | **False positive.** Present in the root interface. |
| `interface-missing-shortDescription` | Missing short description | **False positive.** Present in the root interface. |
| `interface-missing-longDescription` | Missing long description | **False positive.** Present in the root interface. |
| `interface-missing-developerName` | Missing developer name | **False positive.** Present in the root interface. |
| `interface-missing-category` | Missing category | **False positive.** Present in the root interface. |
| `interface-missing-capabilities` | Missing capabilities | **False positive.** Present as `Read` in the root interface. |
| `interface-missing-websiteURL` | Missing website URL | **Not a local Codex install failure.** Not supplied in the portable manifest; any public-listing requirements are outside this local acceptance test. |
| `interface-missing-privacyPolicyURL` | Missing privacy URL | **Not a local Codex install failure.** Not supplied in the portable manifest; any public-listing requirements are outside this local acceptance test. |
| `interface-missing-termsOfServiceURL` | Missing terms URL | **Not a local Codex install failure.** Not supplied in the portable manifest; any public-listing requirements are outside this local acceptance test. |
| `interface-missing-defaultPrompt` | Missing default prompt | **False positive.** Present in the root interface. |

The three URLs are absent from the canonical portable manifest, so they are not described as “present”; the evidence shows only that Plugin Eval reports them against the wrong compatibility file and that they did not prevent the local Codex install. A separate public-submission review was not performed.

The remaining Plugin Eval warnings are separate from those 12 failures: `description-trigger-weak`, Python cyclomatic complexity `72`, and `9` long Python lines. The trigger warning is actionable, though this run’s context-budget overflow prevents isolating trigger wording as the cause. The complexity and line-length warnings are maintainability findings, not native activation measurements. The score is structural/static analysis only and does not measure Codex selection.

## Hook events and missing evidence

VORQA declares no lifecycle hooks in either manifest and includes no `hooks/hooks.json`. No hook event was observed in the ten CLI event streams. The current public Codex hooks guide documents these event names: `SessionStart`, `SessionEnd`, `SubagentStart`, `SubagentStop`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `Stop`, and `Interrupt`. These host capabilities were not invoked or tested for VORQA because the plugin declares no hooks.

Missing evidence is direct skill-selection telemetry and a run in which skill descriptions remain available to the model. The activation result is therefore a real host-level failure under this Codex context-budget condition, while a normal-context false-positive rate remains unmeasured.

## Synthetic task evidence

The regression-repair scenario ran against a disposable initialized AVRL fixture. Codex changed only fixture files and added tests. Its final test command reported **“Ran 0 tests”**, so that session did not establish test success. A separate post-run check against the disposable fixture discovered and ran all three tests; **3/3 passed**. This is synthetic fixture behavior and does not prove VORQA skill activation or real application quality.

## Recommended follow-up

1. Diagnose how the installed Codex environment’s skill-context budget excludes the VORQA description; repeat the positive and negative matrix only after the host confirms that the VORQA skill is model-visible.
2. Improve the VORQA skill trigger description so explicit controller inspection and adoption requests are clearly advertised.
3. Update Plugin Eval to inspect the canonical portable manifest and compatibility overlay according to their separate schemas; do not score optional presentation URLs as mandatory Codex install fields.
4. Keep native selection evidence, bridge-call evidence, static Plugin Eval findings, and fixture task results as separate measurements.

## References

- [PR #12](https://github.com/Centaurioun/VORQA/pull/12)
- [OpenAI plugin packaging guidance](https://developers.openai.com/plugins/build/plugins)
- [Codex hooks guide](https://learn.chatgpt.com/docs/hooks)
