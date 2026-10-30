# Observe an AVRL run — what happened, where it stopped, and why

This feature logs *observable tool and state decisions*, **not** Claude's hidden chain of thought or unfiltered conversation content.

## Quick pilot

From `claude/implementation/`:

```sh
python3 scripts/observability_pilot.py --output .avrl/pilot/summary.json --no-browser
```

This runs actual Git/AVRL subprocesses and a real seeded HTTP/SQLite signup API against disposable test data. It synthetically calls existing hook wrappers. It **does not prove** Claude Code itself triggered the hooks.

On a host where Playwright navigation is allowed, omit `--no-browser`:

```sh
python3 scripts/observability_pilot.py --output .avrl/pilot/summary.json
```

The Chromium tests submit the demo form, check validation and responsive/visual scenarios. Errors **fail** the pilot. No production database or external repo is used.

## Evidence matrix

| Stage | Expected observation | Proof |
| --- | --- | --- |
| New feature | `none -> in-review` | controller event |
| Pre-approval app write | blocked | hook: PreToolUse/code |
| Premature task completion | blocked | hook: TaskCompleted/completion |
| Human pause | `in-review -> paused` | controller event |
| Stop while paused | allowed | hook: Stop/completion |
| Command verification before approval | refused | real controller subprocess exit |
| Successful and failed tools | separate entries | PostToolUse / PostToolUseFailure |
| Agent/session activity | events observed | SessionStart, SubagentStart/Stop |
| Actual demo API | 201, 409, 400 | HTTP responses |
| SQLite persistence | 2 rows (seeded + valid) | direct database query |
| Browser | desktop/mobile/edge pass | Playwright (only where available) |
| Real Claude Code trigger | **NOT VERIFIED by this pilot** | must be checked on native Claude host |

The event matrix intentionally treats missing observations as a failure and preserves the distinction between synthetic dispatch and native hook events.

## Live session logs

Hook handlers write metadata to `.avrl/trace.jsonl`; normal controller commands add state transitions. Runtime state and evidence are Git-ignored. To audit a native session, open the actual project in Claude Code, run `/hooks`, perform a small user-approved fixture task, and inspect the trace with `scripts/trace_events.py --trace .avrl/trace.jsonl --expect <expected-patterns.json>`. Confirm whether the hook was **actually delivered by Claude** rather than replayed by this pilot.

Never upload the raw log from a personal project as a public artifact without reviewing it. The schema does not record prompt content or tool arguments, but timestamps, path names and contextual identifiers may still be sensitive. `VORQA_TRACE_ORIGIN` is a descriptive field, **not** cryptographic proof of origin.

## Reasons you can see

`blocked` means the relevant hook handler returned exit 2. `allowed` means the handler returned 0 (normal permission evaluation may still deny a tool). `observed_success` and `observed_failure` are event observations, not quality-assurance verdicts. The controller's from/to statuses explain whether an operation advanced or paused.

No branch protection, forced external reviewers, or new isolation infrastructure is installed by this feature.
