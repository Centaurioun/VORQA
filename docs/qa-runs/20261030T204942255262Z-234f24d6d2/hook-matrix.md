# Hook inventory and execution matrix

The project settings define 12 event groups and 13 configured command entries (PreToolUse has two). Each configured shell command was invoked with a synthetic JSON event in a disposable copy of the implementation. The pilot also recorded 14 expected event patterns over 15 trace records. Synthetic dispatch tests handler behavior and exit codes; it does not establish that Claude Code emitted any event. No native Claude session was available.

| Event | Configured handler | Matcher | Expected trigger | Observed | Exit | Decision | State before → after |
|---|---|---|---|---|---:|---|---|
| PreToolUse | block-source-read.sh | .*; Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell | Before a tool runs; source-read policy for blind-qa, and write/edit/shell policy for configured tool matchers. | SYNTHETIC | 2 | BLOCK | in-review | in-review |
| PreToolUse | guard-unapproved-code.sh | .*; Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell | Before a tool runs; source-read policy for blind-qa, and write/edit/shell policy for configured tool matchers. | SYNTHETIC | 2 | BLOCK | in-review | in-review |
| Stop | enforce-eval-pass.sh | (no matcher) | When Claude finishes a response; tested in-review and paused states, plus completed/tampered lifecycle guards. | SYNTHETIC | 0 | ALLOW (Stop continuation) | in-review | in-review |
| TaskCompleted | enforce-eval-pass.sh | (no matcher) | When a task is marked complete; tested before feature completion. | SYNTHETIC | 2 | BLOCK | in-review | in-review |
| PostToolUse | audit-tool-use.sh | .* | After a matched tool succeeds. | SYNTHETIC | 0 | OBSERVE / no permission decision | in-review | in-review |
| SessionStart | audit-tool-use.sh | (no matcher) | At session start or resume; fixture modeled startup. | SYNTHETIC | 0 | OBSERVE / no permission decision | in-review | in-review |
| SubagentStart | audit-tool-use.sh | (no matcher) | When a subagent starts; fixture modeled agent_type=builder. | SYNTHETIC | 0 | OBSERVE / no permission decision | in-review | in-review |
| SubagentStop | audit-tool-use.sh | (no matcher) | When a subagent finishes; fixture modeled agent_type=builder. | SYNTHETIC | 0 | OBSERVE / no permission decision | in-review | in-review |
| PostToolUseFailure | audit-tool-use.sh | (no matcher) | After a matched tool fails. | SYNTHETIC | 0 | OBSERVE / no permission decision | in-review | in-review |
| PermissionRequest | audit-tool-use.sh | (no matcher) | When a tool call needs a permission decision; the synthetic fixture did not show a user dialog. | SYNTHETIC | 0 | OBSERVE / no permission decision | in-review | in-review |
| PermissionDenied | audit-tool-use.sh | (no matcher) | When auto mode denies a tool call; a human rejecting a dialog is not equivalent. | SYNTHETIC | 0 | OBSERVE / no permission decision | in-review | in-review |
| SessionEnd | audit-tool-use.sh | (no matcher) | When a session ends; fixture modeled reason=other. | SYNTHETIC | 0 | OBSERVE / no permission decision | in-review | in-review |
| StopFailure | audit-tool-use.sh | (no matcher) | When a turn ends due to an API error; fixture modeled unknown failure. | SYNTHETIC | 0 | OBSERVE / no permission decision | in-review | in-review |

**Origin:** every row above is `SYNTHETIC`. For native Claude Code, all 12 event types are `NOT OBSERVED` because `claude` is not installed. The direct hook tests use the same shell handlers configured in `.claude/settings.json`; the observability pilot additionally exercises their `hook_logic.py` backend and traces metadata only.

**Permission behavior:** official Claude Code documentation says `PermissionRequest` occurs when a tool call needs a permission decision; `PermissionDenied` occurs when auto mode denies a tool call. A manually rejected approval dialog is not evidence that `PermissionDenied` fired. Both event names were delivered synthetically only; there was no native dialog or auto-mode event. See [Hooks reference](https://code.claude.com/docs/en/hooks#permissiondenied).

`PreToolUse` source-read fixture used a blind-qa Read and returned 2/block; code-write fixture used a Write before approval and returned 2/block. `TaskCompleted` before completion returned 2/block. `Stop` in `in-review` and `paused` returned 0/allowed; the lifecycle also allowed a valid completed stop and blocked tampered review evidence. All audit handlers returned 0 and left controller state unchanged.
