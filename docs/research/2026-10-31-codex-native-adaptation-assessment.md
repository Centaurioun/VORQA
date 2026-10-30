# VORQA Codex adaptation — research and architecture assessment

> **Archived research snapshot — 2026-10-31.** Codex produced this assessment in **read-only mode**; no native integration, tests, plugin creation, or configuration changes were performed by that assessment. A documentation-only PR preserves it for architecture review. Machine-local paths were replaced by repository-relative source links or redacted; linked line numbers refer to the inspected source revision and may shift. The cited PR #9 status and CLI capabilities are **as observed during assessment** and require rechecking before implementation. This archival publication does not certify the conclusions.


## 1. Executive recommendation

**Use a local Codex plugin as the package, with one high-signal workflow skill and the existing Python controller underneath. Keep the controller’s state and evidence checks authoritative. Do not add an MCP server to the first adaptation.**

The initial hypothesis needs one adjustment: **do not make Codex plugin lifecycle hooks a required part of the first release.** Codex’s current documentation describes plugin-bundled hooks, but this installed CLI reports `plugins` and `hooks` enabled while its `plugin_hooks` feature is marked removed and false. The documentation describes hooks in Codex Desktop; this CLI’s listing does not prove those hooks work in the installed Desktop/runtime combination. Verify them in a native acceptance run before packaging them as a dependency. Meanwhile, the controller can deterministically refuse to advance or complete a workflow when approval or evidence is missing.

The desired “normal task, VORQA starts when applicable” experience is feasible as **automatic skill discovery and model-driven orchestration**. It is not a deterministic platform guarantee. Codex’s skills documentation says the host exposes a skill’s name and description for selection, and the model loads the full skill when the request matches. That can avoid repeated manual skill activation, but it cannot guarantee every relevant task triggers VORQA or that unrelated tasks never do. See [Codex plugin skills](https://developers.openai.com/plugins/concepts/skills).

The lowest-risk path is an incremental adapter, not a shared-core directory reorganization. Preserve AVRL’s evidence formats and existing Claude implementation, extract interfaces as needed, and add Codex-specific invocation and event normalization at the boundary.

## 2. Current VORQA source inventory

Repository documentation labels AVRL v2 a **candidate core**, not a production-certified or native Claude implementation. The top-level architecture assigns contracts, state, verification, evidence, and completion decisions to the core; host skills, agents, hooks, and packaging to adapters. The [architecture](../../docs/ARCHITECTURE.md#L1) and [roadmap](../../docs/ROADMAP.md#L8) both describe Claude as the first target and Codex as a later phase.

| Component | Current implementation and evidence | Classification |
|---|---|---|
| Controller and state machine | `avrl.py` holds state, validates state version/status, locks per feature, and saves transitions and recovery snapshots. `init`, approval, bounded rounds, verification, review, blind QA, release attestation, pause, and completion are in one controller module. [Controller state and save](../../claude/implementation/scripts/avrl.py#L92), [round and verify](../../claude/implementation/scripts/avrl.py#L308), [completion](../../claude/implementation/scripts/avrl.py#L578) | **REFACTOR INTO SHARED CORE**, incrementally |
| Evaluation contracts | `prd.md`, `eval.md`, `eval.json`, scenarios, decision log, and mockups contribute to the contract digest. The controller verifies expected contract files and criteria. [Contract file selection](../../claude/implementation/scripts/avrl.py#L163) | **REUSE AS-IS** initially; extract a stable contract interface later |
| Approval | Interactive terminal confirmation is tied to the evaluation digest; HMAC receipts detect drift. The controller distinguishes requested actor labels, but the label and local HMAC do not independently prove a human’s identity. [Approval checks](../../claude/implementation/scripts/avrl.py#L213), [approval transition](../../claude/implementation/scripts/avrl.py#L270) | **REFACTOR INTO SHARED CORE**; Codex adapter must supply an honest human-input boundary |
| Verification evidence | Test and browser results bind to the current Git SHA, evaluation digest, and verifier nonce; hashes are checked again before review and completion. [Verification](../../claude/implementation/scripts/avrl.py#L331), [review and QA receipts](../../claude/implementation/scripts/avrl.py#L374) | **REUSE AS-IS** for evidence semantics; add host provenance fields through an adapter |
| Independent review | Structured reports are checked for contract, round, SHA, nonce, findings, and reviewed files. The controller explicitly says the recorded reviewer identity is not attested. [Review receipt](../../claude/implementation/scripts/avrl.py#L374) | **REUSE core validation; CODEX ADAPTER REQUIRED** for reviewer orchestration |
| Blind QA | A Playwright-based browser interface exposes visible controls and accessibility-based actions, restricts traffic to the configured loopback origin, and avoids saving credential-like fields. [Browser controls and network guard](../../claude/implementation/scripts/blind_browser.py#L24) | **CODEX ADAPTER REQUIRED** for host-side agent/tool restrictions; retain browser harness for local application testing |
| Browser checks and Chromium | `browser_checks.py` drives Playwright scenarios, captures screenshots, checks diagnostics, and compares mockups. Its current PR version records safe failure metadata in `finally`. [Current PR source](https://github.com/Centaurioun/VORQA/blob/qa/comprehensive-validation-2026-10-30/claude/implementation/scripts/browser_checks.py) | **REUSE AS-IS** as an optional application test runner; browser agent access policy is host-specific |
| SQLite and HTTP fixtures | The demo server and ephemeral database provide seeded test data and local signup behavior; they are test fixtures, not production identity or database services. See [demo and database scripts](../../claude/implementation/scripts/demo_server.py#L1) and [tests](../../claude/implementation/tests/test_demo.py#L1). | **REUSE AS-IS** for acceptance fixtures; **DEFER** other database adapters |
| Roles and delegation | Claude-specific builder, verifier, reviewer, and blind-QA roles live under `.claude/agents/`; workflow skills coordinate them. Examples: [builder](../../claude/implementation/.claude/agents/builder.md#L1), [reviewer](../../claude/implementation/.claude/agents/reviewer.md#L1), [review loop](../../claude/implementation/.claude/skills/review-loop/SKILL.md#L1). | **CODEX ADAPTER REQUIRED** |
| Hooks | `.claude/settings.json` configures tool, permission, session, agent, failure, stop, and task-completion events. Claude event names and decision shapes cannot be copied to Codex. [Claude settings](../../claude/implementation/.claude/settings.json#L1) | **CODEX ADAPTER REQUIRED**, subject to installed-host verification |
| Observability | `trace_events.py` writes bounded JSONL metadata, hashes a session identifier, and excludes arbitrary prompt/tool content. Controller transitions add state events. [Recorder](../../claude/implementation/scripts/trace_events.py#L13), [controller trace](../../claude/implementation/scripts/avrl.py#L127) | **REFACTOR INTO SHARED CORE** for schema and recorder; adapters report host events |
| Pause, retry, recovery | Pause and bounded rounds are in the controller. State snapshots are recovery aids, not trusted approval evidence. [Pause and round limits](../../claude/implementation/scripts/avrl.py#L294) | **REUSE core semantics**; test interruption/resume mapping in Codex |
| Regression and acceptance tests | Unit tests cover contracts, evidence staleness, controller denials, browser controls, trace handling, and fixture lifecycle. [Test inventory](../../claude/implementation/tests/test_security.py#L1), [lifecycle test](../../claude/implementation/tests/test_full_lifecycle.py#L1) | **REUSE AS-IS** for controller invariants; add Codex-native acceptance tests |
| Security checks | Deterministic checks include input validation, stale-evidence rejection, loopback browser constraints, and no-noninteractive approval. Hooks and same-user HMAC are explicitly not OS security boundaries. [Security tests](../../claude/implementation/tests/test_security.py#L1), [implementation limits](../../claude/implementation/README.md#L70) | **REUSE core checks; CODEX ADAPTER REQUIRED** for host guardrails |

**The “shared core” is not yet fully platform-independent.** The controller and orchestration live together in `scripts/avrl.py`; it assumes its own directory structure, checks Claude availability and `.claude/settings.json` in `doctor`, and uses `fcntl.flock`, which is a POSIX-specific lock. Those are concrete extraction/portability concerns, not evidence that the controller’s evidence model itself must be discarded.

### Source and QA revision caveat

The local checkout was clean at `59c358c46844db330b617143154dcb3c886f4575`, on `qa/comprehensive-validation-2026-10-30`, and reported **four commits behind** its tracking ref. GitHub currently reports PR #9 as **open and unmerged**, at head `9a236bf972e4560219c0696a0b7b1cb04dc8d144`. I fetched the newer PR versions of the controller, trace recorder, hook settings, and browser-check source read-only. Thus, the local line references above are useful for source navigation, while the PR links show later source where relevant.

PR history also has two test counts: the PR description records 43 tests for an earlier campaign; a later PR follow-up records **45 tests** and successful current-head Foundation and Claude CI runs. The same follow-up still explicitly says native Claude Code execution, real human approval, and independent reviewer identity are unverified. These are historical CI/PR claims, not tests run for this assessment. See [PR #9 and its review follow-ups](https://github.com/Centaurioun/VORQA/pull/9).

## 3. Installed Codex capability matrix

**Environment inspected:** `codex-cli 0.166.0-alpha.5.1`; Python 3.14.9 and Node 26.12.1 are on PATH. The installed Codex CLI’s plugin listing showed local and bundled marketplaces, including enabled GitHub and Plugin Eval entries. This confirms CLI/environment visibility, not that every plugin feature works in an actual coding session.

| Capability | Finding | Evidence and practical limitation |
|---|---|---|
| Plugins, manifest, discovery | **Available** | `codex plugin` exposes add/list/marketplace/remove commands; `codex plugin list` displayed local marketplaces. Current docs describe portable `plugin.json` and compatibility `.codex-plugin/plugin.json`. Availability is marketplace/surface dependent. [Packaging and local marketplace docs](https://developers.openai.com/plugins/build/plugins) |
| Skills and automatic selection | **Available; selection is model-driven** | Skills are `SKILL.md` directories; metadata is available for selection and full instructions load when matched. This is discovery, not guaranteed invocation. [Skills](https://developers.openai.com/plugins/concepts/skills) |
| `AGENTS.md` | **Available** | The current session received repository instructions. OpenAI’s [AGENTS.md docs](https://developers.openai.com/codex/agent-md) describe user/repository guidance. It guides behavior but is not an independent gate. |
| Agent delegation | **Available** | The CLI reports `multi_agent` stable and enabled; delegation tools are available in this environment. `SubagentStart`/`SubagentStop` hooks are documented. Delegation remains model-selected unless the orchestrating workflow requests it. [Subagents](https://developers.openai.com/codex/subagents) |
| Lifecycle hooks | **Hooks available; plugin-hook status unresolved** | `codex features list` showed `hooks` stable/enabled, but `plugin_hooks` removed/false. Current docs describe Codex hook events and plugin hooks for manually installed Codex Desktop plugins. No hook was dispatched in this assessment, and the Desktop runtime version was not inspected. Treat plugin hook packaging as a prototype question. [Hooks](https://developers.openai.com/codex/hooks) |
| Hook payloads and tool observation | **Documented** | Hooks receive JSON on stdin, with documented event-specific fields. Local shell, `apply_patch`, MCP, and many local function calls are covered; hosted tools are not, and some paths may opt out. Do not infer complete tool-call observability. [Hook tool coverage and payload](https://developers.openai.com/codex/hooks) |
| Permission and approval modes | **Available** | CLI help exposes approval policies; hooks document `PermissionRequest` allow/deny/continue-to-normal-prompt. Preserve the user’s current policy. A permission-request hook sees only requests that reach that approval point; it does not capture every human interaction. [Permissions](https://developers.openai.com/codex/permissions) |
| Stop/completion interception | **Some stop continuation is documented; task-completion equivalence is not** | A Codex `Stop` hook can ask the agent to continue, but this is a continuation prompt, not Claude `TaskCompleted` semantics or a durable controller gate. It has retry-loop risk and is not proof of successful completion. [Stop hook behavior](https://developers.openai.com/codex/hooks) |
| MCP | **Available** | CLI has `codex mcp` commands; plugin manifests can package MCP configuration. It adds a process/protocol boundary and tool approvals, so it should solve a specific need before being adopted. [MCP](https://developers.openai.com/codex/mcp) |
| Local Python and tests | **Available as process execution** | Python is on PATH and Codex exposes shell execution. The repository’s controller requires Python 3.11+; installed Python 3.14.9 meets that stated version floor. No project tests were run in this assessment. |
| Browser automation | **Partially available** | The plugin list showed bundled browser/computer-use packages, and this session has computer/browser automation tools. That does not prove the AVRL Playwright/Chromium runner launches correctly under Codex or can safely constrain a delegated QA agent. |
| Git / GitHub | **Available** | Local Git commands worked for read-only state inspection; the connected GitHub integration fetched PR #9. This verifies these paths for this session, not universal plugin entitlement. |
| Structured logs | **Available, incomplete as a universal audit source** | Hooks expose event metadata; `transcript_path` is explicitly not a stable hook interface. Do not depend on parsing transcripts for durable event data. [Hook inputs](https://developers.openai.com/codex/hooks) |
| Session/workflow persistence | **Available at the host level** | CLI exposes resume/fork/archive and an agent-session browser. That is host conversation persistence, not guaranteed synchronization of every VORQA controller state transition. |
| User notifications | **Permission UI exists; VORQA-specific notifications are not verified** | The permission flow is documented. No evidence here establishes a general VORQA notification API. Use ordinary Codex interaction for meaningful user decisions. |

I did not inspect Codex private model reasoning or treat transcripts as a supported audit API. Codex’s hook docs warn that transcript format can change.

## 4. Claude-to-Codex compatibility matrix

Claude currently configures these hooks in [`.claude/settings.json`](../../claude/implementation/.claude/settings.json#L1). Codex event names and semantics differ.

| Claude purpose/event | Codex mapping | Reliability and enforcement |
|---|---|---|
| Pre-tool permission check (`PreToolUse`) | Codex `PreToolUse`; documented for supported local tools. It can deny a call with a supported response. | **Enforceable for covered tool calls**, but not all host paths. Feature-flag discrepancy means plugin-packaged hook behavior must be verified in Desktop. |
| Post-tool observation (`PostToolUse`) | Codex `PostToolUse` for supported tools. | **Observable after execution**, cannot undo side effects. |
| Failed tool (`PostToolUseFailure`) | No separate verified failure event. Codex `PostToolUse` runs for Bash nonzero exits; capture return/result status if present. | **No exact native equivalent.** Failure observation coverage needs regression cases for shell, edit, MCP, and missing/unsupported paths. |
| Agent start/complete (`SubagentStart`/`SubagentStop`) | Codex has corresponding subagent hooks. | **Documented equivalent, not exact identity or isolation parity.** Record host agent IDs and distinguish absent event from failed workflow stage. |
| Task completion (`TaskCompleted`) | No exact Codex event found. `Stop` may continue a turn. | **NO VERIFIED NATIVE EQUIVALENT** to Claude’s task-completion event. Use controller `complete` checks and report the limitation. |
| Stop and resume (`Stop`, session start) | `Stop`, `SessionStart` (`startup`, `resume`, `fork`, etc.), and `Interrupt`. | Stop is **continuation**, not a final status gate. Session/interrupt events can record lifecycle metadata, but interrupted work still needs controller reconciliation. |
| Permission request (`PermissionRequest`) | Codex `PermissionRequest`. | **Documented equivalent** before a permission prompt; a hook can allow, deny, or defer to normal approval. Do not auto-allow in VORQA. |
| Permission denied (`PermissionDenied`) | No exact verified event. A subsequent tool failure may sometimes reveal denial, but that is not the same event. | **NO VERIFIED NATIVE EQUIVALENT.** Mark denied decision as missing unless a documented source reports it. |
| Review/QA handoff | Skill instructions plus subagent invocation; hook can add subagent context. | **Advisory orchestration**, with event receipts if observed. The controller validates receipts but cannot prove that the subagent was genuinely independent. |
| Verification failure | Controller records criterion FAIL; Codex `PostToolUse` can report a command’s result; subagent stop can record reviewer disposition. | **Controller gate is deterministic** if evidence is actually supplied and validated. Do not treat a missing event or skipped command as PASS. |
| Approval-required state | Controller status (`awaiting-approval`) plus Codex normal permission prompt when a tool requires approval. | **Separate mechanisms.** A tool permission prompt does not approve an evaluation contract or release SHA. |

Codex `UserPromptSubmit` can block or add context, but its matcher is currently ignored. Applying it to every prompt would create unnecessary overhead and expose all user prompts to a hook process. It should not be the first-line VORQA activation or audit mechanism. Codex docs also say `SubagentStart` cannot prevent the subagent from starting by returning `continue:false`. See [Codex hook event details](https://developers.openai.com/codex/hooks).

## 5. Skills vs plugin vs MCP comparison

| Approach | Installation / daily use | Activation and gates | Maintenance, reliability, portability |
|---|---|---|---|
| **A. Skills only** | Lowest setup if repo-local or user-level skills are already discovered. Can auto-select from ordinary requests. | Automatic discovery is model-driven. Controller calls can gate state transitions, but there is no packaged lifecycle integration. | Fewest components and easiest first prototype; easier to lose version coherence between skill and controller. |
| **B. Local plugin with skills and verified hooks** | One installable unit can package workflow and runtime resources. Local marketplaces and plugin enablement are supported. | Skill selection is model-driven. Documented hook events can gate some tools; plugin hook support for this installed CLI remains unresolved, and hooks require user trust. | Best eventual packaging and upgrade story. More moving parts; hook compatibility and host support need native regression tests. |
| **C. Plugin plus MCP controller server** | Single package, but adds server startup, protocol, tool definitions, and per-tool approvals. | Provides structured controller operations, but does not itself make task activation automatic or add unsupported host events. | Useful if the controller needs a stable typed API across clients or callers outside the shell. Adds runtime, transport, and testing complexity without a demonstrated current need. |

**Recommendation:** B as the package direction; start with its skills and CLI controller. Add plugin hooks only after Codex Desktop acceptance confirms event payloads and denials. Choose C only if a concrete limitation of direct local CLI invocation emerges. Codex supports local marketplace sources and plugin files under `.codex-plugin/plugin.json`; its docs describe the compatible layout and installation flow in [Package your plugin](https://developers.openai.com/plugins/build/plugins).

## 6. Recommended VORQA plugin structure

Keep the first package small and local:

```text
vorqa-codex/
├── .codex-plugin/
│   └── plugin.json
├── skills/
│   └── vorqa-workflow/
│       └── SKILL.md
├── scripts/
│   └── codex_adapter.py       # host event normalization / controller bridge
├── references/
│   └── event-map.md
└── (no mcp.json initially)
```

The adapter should locate and call the existing Python controller, normalize only documented Codex hook inputs if hooks are later included, and never write PASS evidence by itself. Keep the canonical state machine, contracts, and receipt checks in the existing implementation until a shared-core interface is extracted safely.

A repository marketplace entry is repo-scoped; a personal marketplace is user-scoped. Both require the user to install or enable the plugin through Codex’s marketplace flow. A plugin is not silently available everywhere merely because its source exists. Current docs describe local marketplace sources and cache behavior at [Package your plugin](https://developers.openai.com/plugins/build/plugins).

## 7. Shared-core refactoring assessment

Do **not** move the whole implementation into the proposed `core/` tree in the first Codex PR.

Extract incrementally around stable boundaries:

- **Shared:** contract parsing and digesting; state transition rules; Git SHA/eval-digest binding; receipt validation; deterministic criterion runner interface; JSONL event schema; pause/round limits.
- **Host-specific:** skill/agent orchestration; hook registration, payloads, trust and approvals; subagent creation; local browser task constraints; plugin marketplace and session lifecycle.
- **Keep test/demo scoped:** SQLite signup fixture, Playwright browser exercise, screenshots and mockup comparison. They demonstrate app behavior, not a reusable verification engine for all products.

The current controller’s `fcntl` lock and Claude-specific `doctor` checks are portability debt. Extract behind an interface and preserve the current filesystem/runtime format until tests show a safe migration. Keep evidence receipts backward-compatible where possible; add versioned optional host-origin fields instead of rewriting historical evidence.

## 8. Automatic activation and workflow design

Separate the four capabilities:

1. **Discovery:** Codex can see the skill description and may select it based on the user’s request.
2. **Orchestration:** Once selected, the skill can instruct the main agent to run controller checks and delegate only relevant stages.
3. **Enforcement:** The controller rejects invalid transitions and stale/missing receipts. Codex hooks may block some local tool calls, but full coverage is not verified.
4. **Human permission:** Normal Codex permission handling and meaningful contract/release approval are distinct. Preserve the user’s configured approval mode.

Recommended activation policy:

- Trigger for requests to implement or repair application behavior, especially multi-file changes, new features, UI/API/database behavior, or changes with an explicit acceptance contract.
- Do not trigger for read-only questions, explanations, trivial formatting, or isolated documentation edits unless the user asks.
- For ambiguous or tiny changes, use the ordinary Codex workflow and avoid launching reviewer, browser QA, or additional agents by default.
- Use one main VORQA orchestration skill. It calls the controller and delegates only stages justified by the changed surface. Reuse one reviewer and one QA pass; do not spawn duplicate agents.
- Apply a bounded retry/circuit-breaker policy already represented by AVRL. A repeated fingerprint, missing dependency, unavailable browser, stale SHA, or missing host event pauses or fails closed; it must not initiate unlimited “one more pass” continuation.
- Do not inject VORQA instructions into every prompt via a universal `UserPromptSubmit` hook.

This satisfies “no repeated manual activation” as a goal, while accurately treating activation as model-selected and acceptance-tested rather than guaranteed.

## 9. Hook, permission, and completion handling

For the first Codex adapter, call the controller from the skill and record controller decisions. Do not claim the host blocked a write unless a native hook receipt proves it.

If plugin hook support is verified in Desktop, start with narrowly useful hooks:

- `SessionStart`: detect an already-active VORQA run and attach concise resume context.
- `PreToolUse`: apply a deterministic gate to supported local edits/commands while a run is awaiting approval.
- `PostToolUse`: record bounded result metadata for supported calls.
- `PermissionRequest`: observe and defer to normal Codex approval unless the user’s policy explicitly decides otherwise.
- `SubagentStart` / `SubagentStop`: record observed agent IDs/types and completion events.
- `Stop` / `Interrupt` / `SessionEnd`: record stop, interruption, or session end; reconcile with controller state on resume.

Do not map `TaskCompleted` to `Stop`. A Codex Stop continuation can prompt further work, which risks loops and is not equivalent to rejecting a terminal task-completion event. The deterministic `complete` command should remain the authoritative VORQA disposition; describe any host-level rejection as unavailable until proven.

Regression tests must cover: supported and unsupported tools; success and nonzero command exit; denied permission; missing hook trust; malformed input; timeout; absent event; duplicate delivery; stale receipt; interrupted and resumed workflow; Stop continuation loop prevention; and controller failure. Required event absence should be **NOT OBSERVED**, not synthesized.

## 10. Observability and log design

The existing JSONL recorder is a useful base: it timestamps events, bounds labels, stores metadata rather than payloads, and hashes the session identifier. It does not provide a complete event vocabulary for Codex. In particular, it currently does not explicitly model task IDs, tool-use IDs, event provenance class, or missing observations. Trace-write errors are printed but do not stop state transitions. See [trace recorder](../../claude/implementation/scripts/trace_events.py#L13) and [controller save path](../../claude/implementation/scripts/avrl.py#L127).

Proposed event envelope:

```json
{
  "schema_version": 1,
  "timestamp_utc": "...",
  "session_id_hash": "...",
  "task_id": "...",
  "project_id_hash": "...",
  "git_sha": "...",
  "contract_digest": "...",
  "trigger_type": "skill | explicit | resume | hook",
  "event_origin": "native_host | controller | synthetic | inferred | missing",
  "event_name": "...",
  "agent_role": "...",
  "tool_name": "...",
  "tool_use_id": "...",
  "decision": "allow | deny | defer | observed_success | observed_failure",
  "controller_from": "...",
  "controller_to": "...",
  "verification_result": "...",
  "evidence_ref": "...",
  "error_category": "...",
  "pause_resume_reason_code": "...",
  "correlation_id": "..."
}
```

Store no prompt bodies, raw model reasoning, secrets, raw tool arguments, user-entered form values, or unfiltered exception text. Prefer enumerated reason codes and opaque evidence references. The provenance field must distinguish an actual Codex hook receipt from controller-generated or synthetic records. A field saying `native_host` is still a claim by the recorder, not cryptographic proof of the host.

An audit view should answer: **what happened, when, why the controller allowed or denied a transition, and which SHA/contract/evidence supports it?** It should also show missing expected observations and the source of each claim. Preserve the existing evidence manifest and JSONL format where practical; version schema changes and test redaction and missing-event behavior.

## 11. Plugin Creator integration strategy

Plugin Creator is available in the app tool catalog, and a cached `create-plugin` skill plus local-plugin and packaging guidance were inspected. I did not invoke creation or installation. The guidance describes:

- A Codex-compatible manifest at `.codex-plugin/plugin.json`.
- Workflow skills under `skills/<name>/SKILL.md`.
- Optional hook configuration under `hooks/hooks.json`.
- Optional MCP configuration, which VORQA does not presently need.
- Local and repo marketplace paths; installation is an explicit user action and restart/refresh may be needed.

Plugin Creator guidance favors hosted/Sites plugins by default but explicitly describes local plugins when local files/processes are needed. VORQA’s local Python controller is such a case. Use the helper later for packaging guidance or manifest review, not as an architectural authority and not to create a hosted service. Version the package and provide rollback by pinning marketplace source/ref or restoring a known package version; do not let plugin upgrades silently overwrite controller state. References: [local plugins](https://developers.openai.com/plugins/build/plugins) and [plugin architecture](https://developers.openai.com/plugins/concepts/plugins).

## 12. Plugin Eval and benchmark plan

Plugin Eval is installed and enabled in the observed Codex plugin listing. Its skill and docs describe static analysis of a plugin/skill and live usage benchmarking through real Codex CLI runs. **It was not run here**, because there is no Codex plugin adaptation yet and the assessment is read-only. Its benchmark writes local run artifacts; use it only later with reviewed fixtures. See the installed Evaluate Plugin skill (local installation; absolute path omitted) and benchmark harness guide (local installation; absolute path omitted).

| Evaluation area | Measure | Synthetic evidence acceptable for | Native Codex execution required for |
|---|---|---|---|
| Activation quality | Relevant positive prompts, unrelated negative prompts, trivial-task false activations, skill selection and added context tokens | Static description review and deterministic prompt set scoring | Actual plugin/skill discovery, false activation rate, missed activation rate |
| Orchestration | Expected stage sequence, skipped/repeated stages, agent IDs and handoff event coverage | Controller state-machine tests and fixture event streams | Actual host selection and observable subagent handoffs |
| Enforcement | Attempts at premature completion, failed test reported as PASS, stale SHA, missing reviewer/QA evidence | Controller gate tests and hook-payload fixtures | Native supported-tool denial and unsupported path behavior |
| Real functionality | UI transitions, API responses, validation, persistence and browser errors | Seeded local app, disposable SQLite, controlled browser | Codex-run browser interaction, observed network/result path, runtime integrations |
| Observability | Event coverage, provenance, missing-event flags, redaction, transition sequence | Synthetic and controller-generated event schema tests | Hook receipt delivery and host event IDs |
| Performance | Input/output tokens when available, model invocation count, tool-call count, total elapsed time, duplicate work | Static token estimates and scripted controller counts | Real `codex exec` usage and workflow duration |
| Reliability | Recovery after tool failure, resume consistency, idempotency, retry limits, stale evidence rejection | Deterministic controller fault injection | Interrupt, resume, hook timeout/trust, and live host state behavior |

Use Plugin Eval’s static analysis for package and skill quality. Use its real-Codex benchmark for activation, usage, and performance data; do not interpret a static score as proof of workflow enforcement. Require explicit evidence for each acceptance criterion; avoid one aggregate score that can conceal a critical failure.

## 13. Three real-world acceptance scenarios

### Scenario 1 — Small Python application

- **Setup:** Disposable Python app with a seeded defect, one deterministic unit test that fails before the fix, no credentials or external services.
- **Expected workflow:** Ordinary bug-fix request selects VORQA; the controller establishes a contract and SHA; Codex fixes the defect, runs the test, and obtains a review of the changed diff.
- **Expected agent behavior:** Main agent owns state and reports; builder and reviewer are separate subagents only if actual delegation is available and useful.
- **Required events:** Skill selection, controller initialization, test invocation/result, changed SHA, reviewer handoff/result, completion decision.
- **Success:** Defect reproduced, corrected, test passes on the recorded SHA, review evidence matches SHA and contract, final report names test evidence.
- **Failure:** Test is skipped or fails; reviewer report is absent/stale; a textual PASS or generated receipt is accepted without verifying artifact hash.
- **Evidence:** Git SHA/diff, test command/result, controller trace, review receipt, native hook receipts if hooks are under test.
- **Limitations:** Synthetic hook events test the controller path only, not Codex host dispatch.

### Scenario 2 — Web application with API and database

- **Setup:** Seeded local web app, API, and disposable SQLite database; deliberately introduced validation or persistence defect; network constrained to loopback.
- **Expected workflow:** Contract includes UI states, API status expectations, database persistence, and browser scenarios; deterministic API/database checks and black-box Playwright/browser run precede review and completion.
- **Expected agent behavior:** Browser QA receives business goals and only the black-box browser interface. Main agent never interprets a screenshot alone as proof of persistence.
- **Required events:** Browser navigation/action/result, failed request/5xx, validation response, persisted row count, browser/network diagnostics, SHA and evaluation digest.
- **Success:** Valid submission persists; duplicate and malformed submissions receive defined errors; browser errors are zero or explicitly dispositioned; observed evidence belongs to current SHA.
- **Failure:** Browser unavailable but reported PASS, failed network request ignored, external service contacted, persistence inferred from UI, or database effect differs from contract.
- **Evidence:** Sanitized browser diagnostic summary, screenshots/event receipts, HTTP responses, database assertions, controller trace, review receipt.
- **Limitations:** AVRL’s existing browser network guard constrains the Playwright context, not the whole OS process; it is not equivalent to a security sandbox.

### Scenario 3 — Existing repository candidate

**Candidate:** the locally installed Teamwork-for-Codex plugin, which appeared as an enabled local plugin source in the installed Codex plugin listing. It was not inspected or executed during this assessment.

- **Setup:** Later, create a disposable clone/copy at a pinned commit. Exclude user config, credentials, caches, and unrelated personal files. Seed a small reproducible defect in the disposable copy only.
- **Expected workflow:** Submit a normal request against the repository, let activation be model-selected, and exercise controller, verification, review, pause, and recovery.
- **Expected agent behavior:** Preserve the repository’s own guidance; no writes to the original checkout; no real service calls or external publication.
- **Required events:** Start/resume identity, baseline SHA, dirty-state check, test command/result, subagent IDs, review/QA receipts, interruption/resume, final disposition.
- **Success:** All edits and tests are confined to the disposable copy; evidence is tied to the pinned baseline and resulting SHA; unrelated work remains unchanged.
- **Failure:** Original repository changes, untracked files are lost, test command reaches real accounts/services, missing event is inferred as delivered, or stale evidence is reused after a change.
- **Evidence:** Disposable copy identity, Git status/diff, command results, event-provenance report, receipts, final controller status.
- **Limitations:** The candidate’s current files and test architecture have not been examined; select a concrete defect only after a future read-only suitability review.

## 14. P0/P1/P2 implementation roadmap

### P0 — Initial working Codex adaptation

- Add one Codex plugin package with a single VORQA workflow skill and a documented local invocation of the existing Python controller.
- Define high-signal activation and explicit non-trigger examples.
- Keep contract digest, SHA binding, evidence receipts, pause semantics, and controller completion gates unchanged.
- Add controller adapter tests and a read-only/fixture acceptance test; do not add an MCP service.
- Label Codex hook-origin evidence unavailable until a native run proves dispatch.

### P1 — Reliable plugin

- Verify skill activation and subagent handoffs in native Codex sessions.
- Prototype plugin-bundled hooks in Codex Desktop and reconcile observed behavior with the installed CLI’s `plugin_hooks` feature state.
- Add event normalization, provenance classes, missing-observation reporting, redaction tests, and interruption/resume tests.
- Extract shared controller interfaces incrementally; address `fcntl` and Claude-specific `doctor` checks behind host abstractions.
- Run the three acceptance scenarios and Plugin Eval on the real package.

### P2 — Optional enhancements

- MCP interface only if typed controller operations, language-neutral calls, or a demonstrable integration need justify it.
- Add cross-platform locking and adapter support when another platform is actually targeted.
- Improve audit visualization and usage/performance trend reporting.
- Evaluate Antigravity and Copilot adapters separately; do not infer their behavior from Codex packaging.

## 15. Six-Cycle Iterative Refinement findings

1. **Discovery:** AVRL already has meaningful deterministic gates and receipt binding, but no Codex adapter exists. The local source is behind the current PR head.
2. **Architecture:** Skills-only is a viable low-friction prototype; a local plugin is the better long-term package. MCP does not solve activation or host hook coverage by itself.
3. **Feasibility:** Codex supports skills, plugins, local process execution, subagents, hooks, permissions, and MCP. Current skill routing is model-selected; event coverage has explicit gaps.
4. **Validation:** Scenarios must test controller invariants and actual native Codex skill/hook behavior separately. Existing CI and synthetic receipts cannot prove host dispatch.
5. **Adversarial review:** Main risks are conflating `Stop` with task completion, claiming plugin hooks work from docs alone, treating reviewer labels as identity, interpreting missing events as success, and retrying indefinitely.
6. **Convergence:** Keep the Python engine and evidence contract; package one orchestration skill; use controller gates; defer MCP and mandatory hooks; accept model-driven activation as a usability layer, not a deterministic control.

## 16. Open technical questions and evidence gaps

- Does the user’s Codex Desktop version load local plugin hooks despite this CLI’s `plugin_hooks` flag showing removed/false?
- Which current local tool paths produce `PostToolUse` receipts, and which are outside the hook path?
- Can a local packaged skill be reliably auto-selected for medium-sized code tasks without frequent false activation?
- What is the stable, low-friction way to pass a human’s contract approval into AVRL while retaining its distinction from tool permission?
- Which controller operations should become a small shared API versus remain CLI commands?
- How should state locking work on Windows if cross-platform support becomes an active milestone?
- The actual Codex-native browser handoff and Playwright execution path have not been validated.
- The exact current PR source differs from the local checkout; PR #9 remains open and unmerged.
- Historical PR CI passed its reported checks, but none were run as part of this read-only assessment.

## 17. Recommended first implementation PR scope

A bounded first PR should add the **Codex adapter skeleton and one workflow skill**, plus tests that prove adapter input validation, status/evidence reporting, and fail-closed controller behavior. It should call the existing controller locally, avoid a shared-directory reorganization, introduce no MCP server, and make no claim that Codex hooks or end-to-end activation are verified. Keep hook registration out of the release-critical path until a separate native prototype demonstrates behavior on the actual Codex Desktop target.

This assessment used Superpowers brainstorming, writing-plans, systematic-debugging, verification-before-completion, and requesting-code-review guidance in **assessment mode**. No implementation plan or review subagent was run because the request requires a read-only report and forbids implementation.

**Files modified: 0. Commits created: 0. Dependencies installed: 0. Plugins installed: 0. Configuration changes: 0.**

