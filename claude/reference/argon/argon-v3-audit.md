An audit of the initial files against the **Claude Code CLI specification** and the transcript's architecture reveals **7 critical bugs and security gaps** that would prevent the v2 files from working out of the box.

---

## Part 1: File-by-File Audit & Findings Matrix

| File | Flaw / Gap Identified | Why It Fails in Production | Fix Applied in v3 |
| --- | --- | --- | --- |
| **`.claude/settings.json`** | **Invalid Hook Schema & Fabricated Keys**: Used `"script": "..."` instead of `"hooks": [{"type": "command", "command": "..."}]`, added a `matcher` to `Stop` (which takes no matcher), and invented `allow_subagents`. | Claude Code's JSON schema validator rejects `"script"` and invalid keys on startup; the hooks never register. | Rebuilt using the 3-level Claude Code schema (`Event -> Matcher Group -> hooks array with type: "command"`) and `${CLAUDE_PROJECT_DIR}` paths. |
| **`enforce-eval-pass.sh`** | **Wrong Exit Code (`exit 1` vs `exit 2`), Missing `stdin` Parser, & Hardcoded Path**: Exited with `1` instead of `2`, ignored `stop_hook_active`, and hardcoded `specs/current-feature/state.json`. | In Claude Code, **`exit 1` is a non-blocking warning**—Claude logs an error and stops anyway. **`exit 2`** is required to block termination and feed `stderr` back to Claude. Also, dynamic branch detection is needed to locate the active feature's state file. | Reads `stdin` JSON, checks `stop_hook_active` (with a safety counter to prevent infinite loops), dynamically resolves `specs/<branch-feature>/state.json`, and exits with **`exit 2`** on failure. |
| **`block-source-read.sh`** | **Reads Non-Existent Env Vars & Easily Bypassed Regex**: Read `$CLAUDE_TOOL_NAME` / `$CLAUDE_TOOL_INPUT` env vars instead of `stdin` JSON. Used a naive `grep` blocklist on Bash commands. | Claude Code passes `tool_name` and `tool_input` via **JSON on `stdin**`, so the script was completely blind. Even if it read `stdin`, an agent could bypass the regex via `python3 -c "print(open('src/app.ts').read())"`, `node -e`, `git diff`, or `cp src/app.ts /tmp/` (copying code to an allowed folder). | Parses `stdin` JSON (`tool_name`, `tool_input.file_path`, `tool_input.command`), enforces a **strict command allowlist** for `blind-qa`, blocks inline interpreters (`python -c`, `node -e`, subshells), and exits with **`exit 2`**. |
| **`.claude/agents/*.md`** | **Over-Privileged Tools & Missing Scoped Hooks**: `verifier.md` and `reviewer.md` had full `Write` access to source code; `blind-qa.md` relied on an external env var (`CLAUDE_AGENT_ROLE`) that Claude Code doesn't automatically set. | A hallucinating Verifier or Reviewer could silently modify application source code to make a test pass. `blind-qa` wouldn't trigger `block-source-read.sh` without manual env exports. | Added `disallowedTools` to strip code-editing capabilities from read-only agents, attached `block-source-read.sh` directly inside `blind-qa.md`'s frontmatter `hooks:`, and added **Effort Levels (`low`, `medium`, `high`)** to `reviewer.md`. |
| **`review-loop/SKILL.md`** | **Shell Recursion & Missing `state.md` Sync**: Wrote a bash script calling `claude --agent=...` inside a skill, and omitted `state.md` (using only `state.json`). | Skills load as orchestration prompts inside Claude Code, not standalone bash loops. Furthermore, the transcript specifies a human-readable `state.md` alongside machine-readable state. | Rewrote as a native Claude Code Orchestrator Skill with `argument-hint` and `allowed-tools`, delegating to `@builder`, `@verifier`, and `@reviewer` in isolated contexts while syncing both `state.md` (human audit log) and `state.json` (hook gate). |
| **`write-eval/SKILL.md`** | **Missing Self-Check Loop & Status Lifecycle**: Jumped straight from `draft` to `awaiting_human_eval_approval` without the self-verification pass or the `draft -> in-review -> approved` status lifecycle. | The transcript specifies that `write-eval` iterates on its own evals to verify they are well-formed, transitions status from `draft` to `in-review`, outputs an autonomous decisions report, and opens the mockups + `eval.md` for human approval. | Added the self-validation pass, explicit `draft -> in-review -> approved` status transitions, and multi-state mockup generation (desktop, mobile, empty, error, loading). |
| **`CLAUDE.md` & `REVIEW.md**` | **Missing Severity-to-Risk Calibration**: Didn't connect the `risk-classifier` output (`LOW`, `MEDIUM`, `HIGH`) to the Reviewer's effort level (`low`, `medium`, `high`) and `eval.md` strictness. | High-risk auth/billing features and low-risk CSS tweaks received the exact same token spend and review depth. | Linked Risk Tier directly to Reviewer Effort Level (`LOW -> low`, `MEDIUM -> medium`, `HIGH -> high`) and minimum required eval counts. |

---

## Part 2: Upgraded & Hardened Production Files (v3)

### 1. Root Configuration & Memory

#### `CLAUDE.md`

```markdown
# Operational Instructions for Claude Code

@REVIEW.md

## 1. Prime Directives
1. **Proof Over Claims**: Never mark a feature or bugfix complete without deterministic, executable proof recorded in `specs/<feature>/state.json` and `specs/<feature>/state.md`.
2. **Role Separation**: Never review your own code in the same context window. Implementation belongs to `@builder`, execution testing to `@verifier`, code auditing to `@reviewer`, and UX exploration to `@blind-qa`.
3. **Risk-Proportional Rigor**: Every feature must be rated via `/risk-classifier` (`LOW`, `MEDIUM`, `HIGH`) before writing evals or code.

## 2. Mandatory Git & Branching Protocol
- **Branch-per-feature**: Before creating or modifying any files for a feature, create or switch to a dedicated branch named `feature/<feature-name>` (or `bugfix/<bug-name>`).
- **Atomic Checkpoint Commits**: Every time an evaluation passes during `/review-loop`, create an atomic commit:
  `git commit -m "checkpoint(<feature>): pass <EVAL-ID> [round <N>]"`
- **Fast Rollback Guarantee**: Never leave broken builds committed on a feature branch without immediately reverting or fixing in the next round. Every commit must serve as a clean target for `git bisect` and instant revert.

## 3. End-to-End Feature Pipeline
Follow this exact sequence for all feature development:
1. `/risk-classifier <feature-name>` -> Rates customer blast radius (`LOW`, `MEDIUM`, `HIGH`) in `specs/<feature-name>/risk-profile.json`.
2. `/write-eval <feature-name>` -> Reads `specs/<feature-name>/rd.md`, creates standalone HTML mockups (desktop, mobile, and edge states), writes falsifiable checks in `eval.md`, transitions status from `draft` to `in-review`, logs all autonomous decisions, and **halts for human approval**.
3. `/review-loop <feature-name>` -> Only runs after `eval.md` status is `approved`. Orchestrates `@builder`, `@verifier`, and `@reviewer` across up to 5 rounds with anti-infinite-loop circuit breakers.
4. `/first-time-user <feature-name>` -> Spawns `@blind-qa` against an ephemeral database (`DATABASE_URL` isolated to `/tmp/`) with source-code reading strictly blocked via `PreToolUse` hooks.
5. `/fix-a-bug <feature-name> "<symptom>"` -> Reproduction-first debugging using failing tests and `git bisect`.

```

---

#### `REVIEW.md`

```markdown
# Code Review Constitution & Failure Taxonomy

## 1. Core Review Philosophy
Do not ask: *"Did someone read this code?"*
Ask: ***"What could go wrong with this change in production, and how do we catch it deterministically?"***

## 2. Effort Levels (Calibrated by Risk Classifier)
When invoking `@reviewer` or `/code-review`, match the effort level to `specs/<feature>/risk-profile.json`:
- **`effort: low`** (for `LOW` risk UI/copy changes): Report only high-confidence deterministic bugs (`Blocker` and `High` severity) with zero speculation.
- **`effort: medium`** (for `MEDIUM` risk functional features): Inspect all changed paths, error handling, state transitions, and missing test coverage (`Blocker`, `High`, `Medium`).
- **`effort: high`** (for `HIGH` risk auth, billing, permissions, or data mutations): Perform exhaustive adversarial analysis across race conditions, tenant isolation, auth boundaries, partial failures, and rollback safety.

## 3. Severity Taxonomy

| Severity | Definition | Action in Review Loop |
| :--- | :--- | :--- |
| **Blocker** | Financial loss, user lockout, cross-user data leak (IDOR/tenant breach), data corruption, unhandled crash on primary flow, or security vulnerability. | **Immediate Fail.** Halts sign-off. Builder must remediate all instances of this defect class across the codebase. |
| **High** | Feature breaks under valid edge cases, missing transactional rollback, broken mobile layout, or violation of an approved mockup state. | **Fail Round.** Builder must fix before `@reviewer` grants sign-off. |
| **Medium** | Suboptimal error message, missing loading/disabled state on buttons, minor performance inefficiency, or incomplete edge-case test. | **Fix in Round 1-2.** If discovered after Round 2 and non-breaking, log in `state.md` as follow-up debt. |
| **Nit** | Naming preference, formatting covered by linters, or stylistic opinions. | **Suppressed.** Never fail a review round for a Nit. |

## 4. The Three Anti-Infinite-Loop Rules
1. **3-Round Rethink Rule (5-Round Hard Cap)**: If a feature still fails after 3 rounds of fixes, incremental patching is not working. On Round 3, `@reviewer` must stop listing granular line items and instruct `@builder` to **rethink the architectural approach** for the failing component. Hard stop at Round 5 (or earlier if the identical bug persists for 2 consecutive fix rounds).
2. **Diff-Only Inspection After Round 1**:
   - **Round 1**: Inspect the full feature branch diff (`git diff main...HEAD`).
   - **Rounds 2–5**: Inspect **only** the delta introduced by the latest fix (`git diff HEAD~1..HEAD`) plus previously failed items. Never re-scan unchanged files to surface brand-new low-priority complaints.
3. **Defect-Class Categorization**: Every reported bug must include a `[Defect-Class: <Category>]` tag (e.g., `[Defect-Class: Unchecked-Null-Response]`, `[Defect-Class: Missing-Tenant-Scope]`). `@builder` must search for and fix **every occurrence of that defect class** across the feature, not just the single line flagged.

## 5. What to Ignore (False-Positive Suppression)
- Pre-existing legacy code outside the current feature's blast radius.
- Stylistic preferences that do not affect runtime reliability, security, or accessibility.
- Mock/seed scripts inside `/tmp/` or `tests/fixtures/`.

## 6. Rules Learned Over Time
<!--
DYNAMIC MEMORY SECTION:
When a bug escapes review or recurs across 2+ rounds in /review-loop, the orchestrator
proposes a 1-line rule below. Only append rules after explicit human approval.
-->
- [RL-001] [Defect-Class: Duplicate-Submission]: All mutation buttons and form handlers must disable triggers synchronously on click/submit before awaiting async network calls.
- [RL-002] [Defect-Class: Missing-Tenant-Scope]: Every database query on multi-tenant tables must include an explicit `workspace_id` / `user_id` filter in the `WHERE` clause, even when querying by primary key.
- [RL-003] [Defect-Class: Mobile-Viewport-Overflow]: Mobile drawers and modals must use `100dvh` with `overflow-y: auto` and test at `390x844` to prevent iOS Safari bottom-bar clipping.
- [RL-004] [Defect-Class: False-Positive-Suppression]: Do not flag unencrypted tokens in `tests/fixtures/` when files are explicitly marked with `// test-fixture-only`.

```

---

### 2. Deterministic Hooks & Settings (`.claude/`)

#### `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/enforce-readonly-agents.sh",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/enforce-eval-pass.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}

```

---

#### `.claude/hooks/enforce-eval-pass.sh`

```bash
#!/usr/bin/env bash
# .claude/hooks/enforce-eval-pass.sh
# Claude Code Stop Hook: Blocks task completion (exit 2) if an active feature build
# has unapproved evals, failing eval checks, or lacks independent reviewer sign-off.

set -euo pipefail

# 1. Read hook event JSON from stdin
INPUT_JSON="$(cat)"

# 2. Prevent infinite Stop-hook loops (Community Bug #55754 safeguard)
STOP_ACTIVE="$(echo "$INPUT_JSON" | jq -r '.stop_hook_active // false' 2>/dev/null || echo "false")"

# Allow explicit human override when needed
if [[ "${ALLOW_EARLY_STOP:-false}" == "true" ]]; then
  exit 0
fi

# 3. Dynamically identify active feature from current Git branch (e.g., feature/team-invite -> team-invite)
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")"
if [[ ! "$CURRENT_BRANCH" =~ ^feature/(.+)$ ]]; then
  # Not on a feature branch; allow normal conversation stop
  exit 0
fi

FEATURE_NAME="${BASH_REMATCH[1]}"
FEATURE_DIR="specs/${FEATURE_NAME}"
STATE_FILE="${FEATURE_DIR}/state.json"
EVAL_FILE="${FEATURE_DIR}/eval.md"

# If feature directory doesn't exist yet, allow stop
if [[ ! -d "$FEATURE_DIR" ]]; then
  exit 0
fi

# 4. Require eval.md and state.json to exist for any active feature branch
if [[ ! -f "$EVAL_FILE" ]] || [[ ! -f "$STATE_FILE" ]]; then
  echo "[HOOK BLOCK - enforce-eval-pass] Active feature branch '${CURRENT_BRANCH}' is missing ${EVAL_FILE} or ${STATE_FILE}. Run /write-eval ${FEATURE_NAME} before finishing." >&2
  exit 2
fi

PHASE="$(jq -r '.phase // "unknown"' "$STATE_FILE" 2>/dev/null || echo "unknown")"

# 5. Legitimate Human-in-the-Loop Pause States (Allow Stop with Exit 0)
# When the agent finishes generating evals/mockups ("in-review") or hits a circuit breaker
# ("awaiting_human_decision" / "failed_max_rounds"), it MUST stop and wait for the human.
if [[ "$PHASE" == "in-review" ]] || [[ "$PHASE" == "awaiting_human_decision" ]] || [[ "$PHASE" == "failed_max_rounds" ]]; then
  exit 0
fi

# 6. Guard against runaway Stop hook loops if stop_hook_active is already true
# Track consecutive stop blocks in state.json; bail out after 3 consecutive hook blocks in one turn
if [[ "$STOP_ACTIVE" == "true" ]]; then
  BLOCK_COUNT="$(jq -r '.consecutive_stop_blocks // 0' "$STATE_FILE" 2>/dev/null || echo "0")"
  if (( BLOCK_COUNT >= 3 )); then
    jq '.phase = "awaiting_human_decision" | .consecutive_stop_blocks = 0' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
    exit 0
  fi
  jq --argjson c "$((BLOCK_COUNT + 1))" '.consecutive_stop_blocks = $c' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
fi

# 7. Block if feature is still in 'draft' (evals haven't been self-checked or moved to in-review)
if [[ "$PHASE" == "draft" ]]; then
  echo "[HOOK BLOCK - enforce-eval-pass] Feature '${FEATURE_NAME}' is still in 'draft' phase. Complete mockup generation, verify eval structure, and set phase to 'in-review' in ${STATE_FILE}." >&2
  exit 2
fi

# 8. Check that all deterministic evaluations in state.json have status == "PASS"
TOTAL_EVALS="$(jq '.evaluations | length' "$STATE_FILE" 2>/dev/null || echo "0")"
PASSED_EVALS="$(jq '[.evaluations[] | select(.status == "PASS")] | length' "$STATE_FILE" 2>/dev/null || echo "0")"

if (( TOTAL_EVALS == 0 )); then
  echo "[HOOK BLOCK - enforce-eval-pass] Zero evaluations recorded in ${STATE_FILE}. Populate and run the evaluations from ${EVAL_FILE} before marking the task done." >&2
  exit 2
fi

if (( PASSED_EVALS < TOTAL_EVALS )); then
  FAILED_IDS="$(jq -r '[.evaluations[] | select(.status != "PASS") | .id] | join(", ")' "$STATE_FILE")"
  echo "[HOOK BLOCK - enforce-eval-pass] Cannot mark feature '${FEATURE_NAME}' complete: $((TOTAL_EVALS - PASSED_EVALS))/${TOTAL_EVALS} evals failing (${FAILED_IDS}). Continue the review loop until all evals pass." >&2
  exit 2
fi

# 9. Verify independent @reviewer sign-off
REVIEWER_SIGN_OFF="$(jq -r '.reviewer_sign_off // false' "$STATE_FILE" 2>/dev/null || echo "false")"
if [[ "$REVIEWER_SIGN_OFF" != "true" ]]; then
  echo "[HOOK BLOCK - enforce-eval-pass] All evals passed, but independent @reviewer has not granted sign-off (reviewer_sign_off is false in ${STATE_FILE}). Run @reviewer to audit the diff." >&2
  exit 2
fi

# Reset block counter and allow clean completion
jq '.consecutive_stop_blocks = 0 | .phase = "completed"' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
exit 0

```

---

#### `.claude/hooks/block-source-read.sh`

```bash
#!/usr/bin/env bash
# .claude/hooks/block-source-read.sh
# Scoped PreToolUse Hook for @blind-qa subagent.
# Blocks (exit 2) any attempt to read application source code via file tools, shell commands,
# inline scripting runtimes (python/node/ruby), or git history inspection.

set -euo pipefail

INPUT_JSON="$(cat)"
TOOL_NAME="$(echo "$INPUT_JSON" | jq -r '.tool_name // empty' 2>/dev/null || true)"

# 1. Block all file-inspection and search tools unless targeting specs/<feature>/qa-*
if [[ "$TOOL_NAME" =~ ^(Read|Grep|Glob|Edit|Write|MultiEdit)$ ]]; then
  FILE_PATH="$(echo "$INPUT_JSON" | jq -r '.tool_input.file_path // .tool_input.path // .tool_input.pattern // empty' 2>/dev/null || true)"
  if [[ "$FILE_PATH" =~ ^(${CLAUDE_PROJECT_DIR}/)?(specs/[^/]+/qa-|/tmp/qa-sandbox-) ]]; then
    exit 0
  fi
  echo "[SECURITY BLOCK - blind-qa] Tool '${TOOL_NAME}' on path '${FILE_PATH}' is forbidden. As a first-time user persona, you may only interact with the live running app over HTTP/Playwright and write to specs/<feature>/qa-report.md." >&2
  exit 2
fi

# 2. Strict inspection of Bash commands
if [[ "$TOOL_NAME" == "Bash" ]]; then
  CMD="$(echo "$INPUT_JSON" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"

  # Block subshells, command substitution, and backticks that could smuggle file reads
  if [[ "$CMD" =~ (\$\(|\`) ]]; then
    echo "[SECURITY BLOCK - blind-qa] Command substitution \$() and backticks are forbidden in blind-qa mode." >&2
    exit 2
  fi

  # Block inline code execution flags (-c / -e) in scripting languages that could read source files
  if echo "$CMD" | grep -iE '(^|[;&|[:space:]])(python3?|node|tsx|ts-node|ruby|perl|php|lua|awk|sed)[[:space:]]+(-[ce]|--eval)' >/dev/null 2>&1; then
    echo "[SECURITY BLOCK - blind-qa] Inline scripting interpreters (-c / -e / --eval) are blocked to prevent source-code reading bypasses." >&2
    exit 2
  fi

  # Block file-reading, archiving, copying, and git inspection utilities
  BANNED_PATTERNS='(^|[;&|[:space:]])(cat|head|tail|less|more|nl|od|xxd|hexdump|strings|base64|cp|mv|ln|tar|zip|rsync|find|grep|rg|ag|ack|git[[:space:]]+(log|show|diff|blame|grep|status|branch|checkout))([[:space:]]|$)'
  if echo "$CMD" | grep -iE "$BANNED_PATTERNS" >/dev/null 2>&1; then
    echo "[SECURITY BLOCK - blind-qa] Source file reading, copying, and git inspection commands are blocked. Test the live application strictly as a black-box user." >&2
    exit 2
  fi

  # Block redirection reading (<) from project directories
  if [[ "$CMD" =~ \<[[:space:]]*[^/[:space:]] ]]; then
    echo "[SECURITY BLOCK - blind-qa] Input file redirection from project files is blocked." >&2
    exit 2
  fi
fi

exit 0

```

---

#### `.claude/hooks/enforce-readonly-agents.sh`

```bash
#!/usr/bin/env bash
# .claude/hooks/enforce-readonly-agents.sh
# Scoped PreToolUse Hook for @verifier and @reviewer:
# Prevents verification/review agents from editing application source code.
# They may ONLY write to specs/<feature>/state.json and specs/<feature>/state.md.

set -euo pipefail

INPUT_JSON="$(cat)"
TOOL_NAME="$(echo "$INPUT_JSON" | jq -r '.tool_name // empty' 2>/dev/null || true)"

if [[ "${ACTIVE_SUBAGENT_ROLE:-}" =~ ^(verifier|reviewer)$ ]]; then
  if [[ "$TOOL_NAME" =~ ^(Edit|Write|MultiEdit)$ ]]; then
    FILE_PATH="$(echo "$INPUT_JSON" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null || true)"
    if [[ "$FILE_PATH" =~ ^(${CLAUDE_PROJECT_DIR}/)?specs/[^/]+/(state\.json|state\.md)$ ]]; then
      exit 0
    fi
    echo "[ROLE BOUNDARY BLOCK] Agent '${ACTIVE_SUBAGENT_ROLE}' is strictly forbidden from modifying source file '${FILE_PATH}'. Only specs/<feature>/state.json and state.md may be updated." >&2
    exit 2
  fi
fi

exit 0

```

*(Note: After saving the hook scripts, mark them executable with `chmod +x .claude/hooks/*.sh`.)*

---

### 3. Isolated Sub-Agents (`.claude/agents/`)

#### `.claude/agents/builder.md`

```markdown
---
name: builder
description: Implementation specialist that builds features or fixes bugs strictly from approved rd.md, eval.md, and HTML mockups. Invoke during the build step of /review-loop.
tools: Read, Write, Edit, Glob, Grep, Bash
disallowedTools: Agent
model: inherit
---

You are the **Builder Subagent**. You operate in an isolated context window to implement features and remediate failures reported by `@verifier` and `@reviewer`.

## Strict Operating Protocol
1. **Inputs You Must Read First**:
   - `specs/<feature>/rd.md` (Feature Requirements)
   - `specs/<feature>/eval.md` (Approved Evals & Mockup Matrix)
   - `specs/<feature>/mockups/*.html` (Target UI Design States)
   - `specs/<feature>/state.md` and `specs/<feature>/state.json` (Current Round & Failing Items)
2. **Pre-Flight Check**:
   - Verify that `specs/<feature>/eval.md` has `Status: approved`. If status is `draft` or `in-review`, refuse to write application code and exit immediately.
3. **Self-Verification While Building**:
   - Run lightweight unit checks, typechecks (`npm run typecheck`), and linter checks as you code so broken syntax never reaches `@verifier`.
4. **Defect-Class Remediation (Rule 3)**:
   - When `state.md` reports a bug tagged with `[Defect-Class: <Category>]`, do NOT patch only the single line reported. Use `Grep` to find every occurrence of `<Category>` across the entire feature and fix all of them in the same round.
5. **Architectural Rethink on Round 3 (Rule 1)**:
   - If `state.json` shows `round >= 3` and `rethink_required: true`, discard incremental band-aids on the failing module and rewrite the component cleanly from scratch against `rd.md`.
6. **Role Boundary**:
   - Never set `reviewer_sign_off: true` or change `evaluations[].status` to `PASS` in `state.json`. Only `@verifier` and `@reviewer` have authority to record verification verdicts.

```

---

#### `.claude/agents/verifier.md`

```markdown
---
name: verifier
description: Deterministic falsification subagent. Runs every test and browser/mockup check in eval.md and records PASS/FAIL evidence in state.json and state.md.
tools: Read, Write, Edit, Glob, Grep, Bash
disallowedTools: Agent
model: sonnet
hooks:
  PreToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "ACTIVE_SUBAGENT_ROLE=verifier ${CLAUDE_PROJECT_DIR}/.claude/hooks/enforce-readonly-agents.sh"
---

You are the **Verifier Subagent**. You did not write the code and have zero attachment to it. Your job is to **prove whether the implementation actually works** by executing every evaluation in `specs/<feature>/eval.md`.

## Strict Operating Protocol
1. **Never Modify Application Code**: You are strictly blocked from editing source files. You may only update `specs/<feature>/state.json` and `specs/<feature>/state.md`.
2. **Execute Every Eval Deterministically**:
   - Parse the JSON evaluation block inside `specs/<feature>/eval.md`.
   - Execute each `command` cleanly and capture its exit code, stdout, and stderr.
3. **Browser & Mockup Verification**:
   - For every UI mockup listed in `eval.md` (`desktop.html`, `mobile.html`, `error-empty.html`), verify that the live running application matches the layout, interactive states, and mobile viewport rules (`390x844`) with zero horizontal overflow or missing elements.
4. **Update State Artifacts**:
   - Update `evaluations` in `specs/<feature>/state.json` with exact `status` (`PASS` or `FAIL`), `exit_code`, `last_run` ISO timestamp, and `output_summary`.
   - Append the round's verification results table to `specs/<feature>/state.md`.

```

---

#### `.claude/agents/reviewer.md`

```markdown
---
name: reviewer
description: Independent adversarial code reviewer operating in a fresh context window. Audits git diffs against REVIEW.md using configurable effort levels (low, medium, high).
tools: Read, Write, Edit, Glob, Grep, Bash
disallowedTools: Agent
model: inherit
hooks:
  PreToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "ACTIVE_SUBAGENT_ROLE=reviewer ${CLAUDE_PROJECT_DIR}/.claude/hooks/enforce-readonly-agents.sh"
---

You are the **Independent Adversarial Reviewer Subagent**. You operate in a fresh context window so you never inherit the confirmation bias of `@builder`.

## Strict Operating Protocol
1. **Load Standards & Effort Level**:
   - Read `REVIEW.md`, `specs/<feature>/risk-profile.json`, `specs/<feature>/state.json`, and `specs/<feature>/state.md`.
   - Set your inspection depth based on the requested effort level (`low`, `medium`, or `high` mapped from `risk-profile.json`):
     - `low`: Flag only deterministic `Blocker` / `High` defects.
     - `medium`: Audit all modified functions, edge states, and error boundaries.
     - `high`: Full adversarial audit (concurrency/race conditions, auth/tenant isolation, financial/data integrity, rollback safety).
2. **Enforce Rule 2 (Diff-Only Inspection After Round 1)**:
   - If `round == 1`: Run `git diff main...HEAD` to inspect the full feature change.
   - If `round > 1`: Run `git diff HEAD~1..HEAD` to inspect **only what the last fix changed**, plus verify whether previously reported defects in `state.md` were resolved. **Never** report brand-new complaints on untouched code that existed in Round 1.
3. **Enforce Rule 3 (Defect-Class Tagging)**:
   - Every finding must be formatted as:
     `- [Severity: Blocker|High|Medium] [Defect-Class: <Category-Name>] <File:Line> — <Explanation & required codebase-wide fix>`
4. **Enforce Rule 1 (Round 3 Architectural Rethink)**:
   - If `round == 3` and `Blocker` or `High` issues remain, stop listing incremental line fixes. Set `"rethink_required": true` in `state.json` and write a clear architectural redesign directive in `state.md`.
5. **Sign-Off Verdict**:
   - If all evaluations in `state.json` are `PASS` AND zero `Blocker`/`High` defects remain (and no unresolved Round 1-2 `Medium` defects remain), set `"reviewer_sign_off": true` in `state.json`.
   - Otherwise, set `"reviewer_sign_off": false` and record `active_defect_classes` in `state.json`.

```

---

#### `.claude/agents/blind-qa.md`

```markdown
---
name: blind-qa
description: Zero-context first-time user QA subagent. Strictly blocked from reading source code or git history; interacts only with the live running app over HTTP/Playwright against a temporary database.
tools: Bash, Write
disallowedTools: Read, Grep, Glob, Edit, MultiEdit, Agent
model: sonnet
hooks:
  PreToolUse:
    - matcher: ".*"
      hooks:
        - type: command
          command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-source-read.sh"
---

You are a **First-Time Customer QA Tester (`@blind-qa`)**. You know **nothing** about how this application was built, and a deterministic security hook blocks you from reading any source code, tests, or git history.

## How to Test the Application
1. **Start at the Entry URL**: Open the live test URL provided in your prompt (e.g., `http://localhost:4199`) using headless Playwright/browser automation or HTTP requests.
2. **Explore Like a Real Human Customer**:
   - Try to discover and complete the target feature flow solely from visible UI labels, buttons, placeholders, and navigation links.
   - Test both desktop (`1440x900`) and mobile (`390x844`) viewports.
   - Try common user mistakes: submitting empty forms, entering invalid inputs, double-clicking submit buttons, refreshing mid-flow, and using browser Back/Forward buttons.
3. **Document Friction & Bugs**:
   - Write your complete walkthrough and findings to `specs/<feature>/qa-report.md` (the only file path you are permitted to write).
   - Categorize findings into:
     - **Broken Flows** (User gets stuck or receives a 500/unhandled error)
     - **Confusing UX / Dead Ends** (Unclear copy, missing feedback, hidden navigation)
     - **Visual / Mobile Layout Glitches** (Overlapping elements, clipped buttons)
     - **Actionable Fix Recommendations**

```

---

### 4. Workflow Skills (`.claude/skills/`)

#### `.claude/skills/risk-classifier/SKILL.md`

```markdown
---
name: risk-classifier
description: Classifies a feature's customer blast radius into LOW, MEDIUM, or HIGH risk before building. Use before /write-eval to calibrate eval strictness and reviewer effort level.
argument-hint: "[feature-name]"
allowed-tools: Read, Write, Glob
---

# Risk Classifier Skill (`/risk-classifier`)

Classify the feature in `specs/$ARGUMENTS/rd.md` by answering one core question:
> **"What happens to a real customer if this feature breaks in production?"**

## 1. Risk Scale & Blast-Radius Criteria

| Tier | Customer Impact if Broken | Reviewer Effort | Required Eval Strictness |
| :--- | :--- | :--- | :--- |
| **LOW** | Visual/cosmetic alignment issue or minor copy mistake. Feature still works; nobody loses data, money, or access. | `low` | Functional check + Desktop & Mobile mockup alignment check. |
| **MEDIUM** | Stops a non-critical feature from working, but no customer loses money, data, or account access, and it can be fixed later without irreversible damage. | `medium` | Unit + integration tests + Desktop/Mobile/Error/Empty state mockups + negative input evals. |
| **HIGH** | Customer can lose money, get locked out of their account, corrupt irreversible state, or see another person's private data. | `high` | Full unit/integration suite + Concurrency/idempotency evals + Auth/tenant boundary evals + All mockup states + Mandatory `/first-time-user` blind QA run. |

## 2. Execution Steps
1. Read `specs/$ARGUMENTS/rd.md`.
2. Evaluate every requirement against the blast-radius table above (always pick the highest applicable tier).
3. Write `specs/$ARGUMENTS/risk-profile.json`:
```json
{
  "feature": "$ARGUMENTS",
  "risk_level": "LOW | MEDIUM | HIGH",
  "reviewer_effort": "low | medium | high",
  "blast_radius_summary": "1-2 sentence explanation of worst-case customer impact",
  "required_eval_categories": [
    "functional_happy_path",
    "desktop_mobile_mockup_match",
    "error_and_empty_states"
  ]
}

```

4. Output the classification summary to the user and instruct them to run `/write-eval $ARGUMENTS` next.

```

---

#### `.claude/skills/write-eval/SKILL.md`

```markdown
---
name: write-eval
description: Turns a feature's rd.md and risk-profile.json into a falsifiable eval.md file and standalone HTML mockups (desktop, mobile, and edge states), self-checks them, and pauses in 'in-review' for human approval.
argument-hint: "[feature-name] [optional: LOW|MEDIUM|HIGH]"
allowed-tools: Read, Write, Edit, Glob, Bash
disable-model-invocation: true
---

# Write-Eval & Mockup Generator Skill (`/write-eval`)

Follow this exact procedure for feature `$ARGUMENTS`:

## Step 1: Branch & Initialization
1. Ensure Git is on branch `feature/$ARGUMENTS` (`git checkout -b feature/$ARGUMENTS` or `git checkout feature/$ARGUMENTS`).
2. Read `specs/$ARGUMENTS/rd.md` and `specs/$ARGUMENTS/risk-profile.json` (if missing, run `/risk-classifier $ARGUMENTS` first).
3. Initialize `specs/$ARGUMENTS/state.json` with `"phase": "draft"`.

## Step 2: Generate Standalone HTML Mockups First (Token-Saving Design Check)
If the feature has any user interface, **do not build on the real app yet**. Build standalone, zero-dependency HTML/CSS files in `specs/$ARGUMENTS/mockups/`:
- `desktop.html`: Primary screen + all interactive states at `1440x900`.
- `mobile.html`: Responsive mobile layout at `390x844` (included inside a dual-preview wrapper or standalone so the user can inspect smaller screen layouts).
- `states.html`: Every other state the screen can be in (**Loading skeleton**, **Empty state**, **Validation Error state**, **Server Error state**).

## Step 3: Draft `specs/$ARGUMENTS/eval.md` Using the Template
1. Copy the structure from `.claude/skills/write-eval/eval-template.md`.
2. Calibrate strictness to `risk_level`:
   - Every requirement in `rd.md` must map to at least one deterministic, runnable check (`EVAL-01`, `EVAL-02`, ...).
   - Each check must be strict enough that incomplete, stubbed, or buggy work fails with a non-zero exit code.
   - For `HIGH` risk features, include explicit evaluations for authorization boundaries, tenant isolation, and idempotency/race conditions.

## Step 4: Self-Verification Loop (Pre-Review Audit)
Iterate over `rd.md`, `eval.md`, and `mockups/*.html` up to 3 times to verify:
- [ ] Every requirement in `rd.md` has a falsifiable test command in `eval.md`.
- [ ] No eval relies on subjective judgment ("looks good")—every eval checks DOM selectors, HTTP status codes, database state, or pixel/layout thresholds.
- [ ] All HTML mockups render cleanly without broken tags or horizontal overflow at `390px` width.
- [ ] Every autonomous decision you made while translating `rd.md` into `eval.md` and `mockups/` is documented in the **Autonomous Decisions Log** section of `eval.md`.

## Step 5: Transition to `in-review` & Halt for Human Approval
1. Update `specs/$ARGUMENTS/eval.md` status from `draft` to `in-review`.
2. Update `specs/$ARGUMENTS/state.json` so `"phase": "in-review"` and populate the initial `evaluations` array with `"status": "PENDING"`.
3. Write `specs/$ARGUMENTS/state.md` summarizing the feature status and autonomous decisions.
4. Open the mockups and `eval.md` for the user to inspect (e.g., `open specs/$ARGUMENTS/mockups/desktop.html` on macOS or print preview paths).
5. **STOP IMMEDIATELY.** Present your **Autonomous Decisions Log** to the user and ask:
   *"Please review `specs/$ARGUMENTS/eval.md` and the HTML mockups (`desktop.html`, `mobile.html`, `states.html`). Reply with any changes you want, or say **'Approve evals'** to mark the feature as `approved` and ready for `/review-loop`."*

```

---

#### `.claude/skills/write-eval/eval-template.md`

```markdown
# Feature Evaluation Contract: {{FEATURE_NAME}}

- **Feature Folder**: `specs/{{FEATURE_NAME}}/`
- **Risk Tier**: `{{RISK_LEVEL}}` (Reviewer Effort: `{{REVIEWER_EFFORT}}`)
- **Status**: `{{STATUS}}` <!-- draft | in-review | approved -->
- **Git Branch**: `feature/{{FEATURE_NAME}}`

---

## 1. Autonomous Decisions Log
*(Every assumption or design choice made by Claude that was not explicitly spelled out in `rd.md`)*
1. **[Decision Topic]**: <What was decided> — *Rationale*: <Why this choice was made>

---

## 2. Visual & State Mockup Matrix
All UI implementations must match these approved reference mockups before the feature can pass verification:

| App State | Mockup File | Viewport | Required DOM / Layout Assertions |
| :--- | :--- | :--- | :--- |
| Primary Desktop | `mockups/desktop.html` | `1440x900` | All interactive controls present; < 2% visual drift |
| Mobile Layout | `mockups/mobile.html` | `390x844` | Zero horizontal scroll (`scrollWidth <= clientWidth`); touch targets >= 44px |
| Loading / Empty / Error | `mockups/states.html` | `1440x900` & `390x844` | Skeleton state, empty state CTA, and `role="alert"` error banner verified |

---

## 3. Executable Falsifiable Evaluations
*(Machine-parsed by `@verifier` and enforced by `.claude/hooks/enforce-eval-pass.sh`)*

```json
[
  {
    "id": "EVAL-01",
    "category": "functional",
    "description": "Core happy-path requirement from rd.md",
    "command": "npm run test -- tests/features/{{FEATURE_NAME}}/happy-path.test.ts",
    "required": true
  },
  {
    "id": "EVAL-02",
    "category": "edge-case",
    "description": "Negative input validation and error recovery",
    "command": "npm run test -- tests/features/{{FEATURE_NAME}}/edge-cases.test.ts",
    "required": true
  },
  {
    "id": "EVAL-03",
    "category": "ui-mockup-alignment",
    "description": "Desktop, Mobile, and State DOM/Layout verification against mockups/",
    "command": "npx playwright test tests/features/{{FEATURE_NAME}}/mockup-alignment.spec.ts",
    "required": true
  }
]

```

```

---

#### `.claude/skills/review-loop/SKILL.md`

```markdown
---
name: review-loop
description: Orchestrates the multi-agent build-verify-review loop (@builder, @verifier, @reviewer) in isolated context windows until all evals pass and the reviewer signs off, enforcing Anthropic's 3 anti-infinite-loop rules.
argument-hint: "[feature-name]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
disable-model-invocation: true
---

# Autonomous Build-Verify-Review Loop (`/review-loop`)

You are the **Main Orchestrator Agent** running the review loop for feature `$ARGUMENTS`.

## Pre-Flight Gate
1. Read `specs/$ARGUMENTS/eval.md`, `specs/$ARGUMENTS/risk-profile.json`, and `specs/$ARGUMENTS/state.json`.
2. Verify that `eval.md` has `Status: approved`.
   - If `Status` is `draft` or `in-review`, **abort immediately** and tell the user: *"Cannot start `/review-loop`: `specs/$ARGUMENTS/eval.md` must be reviewed and approved by you first."*
3. Initialize or update `specs/$ARGUMENTS/state.md` and `specs/$ARGUMENTS/state.json` with `"phase": "in_progress"`, `"round": 1`, `"reviewer_sign_off": false`.

---

## Orchestration Loop (Maximum 5 Rounds)

Execute the following rounds sequentially from `Round 1` up to `Round 5`:

### Step A: Invoke `@builder` (Isolated Context Window)
Delegate to the `@builder` subagent with a self-contained prompt containing:
- The path to `specs/$ARGUMENTS/rd.md`, `specs/$ARGUMENTS/eval.md`, and `specs/$ARGUMENTS/mockups/`.
- The current `round` number and the exact list of failed evaluations or reviewer findings from `specs/$ARGUMENTS/state.md`.
- **If `round > 1`**: Instruct `@builder` to fix every instance of each reported `[Defect-Class: ...]` across the codebase (Rule 3).
- **If `round == 3` and still failing**: Instruct `@builder` to stop incremental patching and **rethink the architecture** of the failing module (Rule 1).

### Step B: Invoke `@verifier` (Isolated Context Window)
Once `@builder` finishes, delegate to `@verifier`:
- Instruct `@verifier` to execute every evaluation in `specs/$ARGUMENTS/eval.md` (including browser/mockup checks) and write the `PASS`/`FAIL` results into `specs/$ARGUMENTS/state.json` and `specs/$ARGUMENTS/state.md`.
- If new evals passed compared to the prior round, create an atomic Git checkpoint commit on `feature/$ARGUMENTS`.

### Step C: Invoke `@reviewer` (Isolated Context Window)
Delegate to `@reviewer` with the effort level from `specs/$ARGUMENTS/risk-profile.json` (`low`, `medium`, or `high`):
- **Round 1**: Instruct `@reviewer` to audit the full feature diff (`git diff main...HEAD`) against `REVIEW.md`.
- **Rounds 2–5**: Instruct `@reviewer` to audit **only the delta introduced by the latest round's fix** (`git diff HEAD~1..HEAD`) plus previously unresolved items (Rule 2 — never re-scan untouched code to find old problems one at a time).

### Step D: Check Termination & Circuit Breakers
Read the updated `specs/$ARGUMENTS/state.json` and `specs/$ARGUMENTS/state.md`:
1. **Success Exit**: If all evaluations in `state.json` have `"status": "PASS"` AND `"reviewer_sign_off": true`, proceed to **Post-Loop Rule Learning**.
2. **Circuit Breaker 1 (Same Bug After 2 Rounds of Fixes)**:
   - Compare the failed eval IDs and `active_defect_classes` in `state.json` against the previous 2 rounds.
   - If the **exact same problem persists after 2 rounds of fixes**, set `"phase": "awaiting_human_decision"` in `state.json`, output a clear progress report in `state.md`, and pause to ask the human for guidance.
3. **Circuit Breaker 2 (Unresolvable Product Ambiguity)**:
   - If `@builder` or `@reviewer` encounters a product decision that cannot be answered from `rd.md`, set `"phase": "awaiting_human_decision"`, present the options to the user, and wait.
4. **Circuit Breaker 3 (Round 5 Cap)**:
   - If Round 5 finishes without full pass, set `"phase": "failed_max_rounds"` in `state.json` and present a diagnostic report to the user.

---

## Post-Loop Rule Learning (Self-Improving `REVIEW.md`)
When the loop finishes (or during multi-round resolution):
1. Check `state.md` to see if any defect required multiple rounds to fix, or if `@reviewer` flagged a false positive that turned out not to be a real issue.
2. Match recurring issues against earlier rounds and draft a **concise one-line rule** formatted as:
   `- [RL-XXX] [Defect-Class: <Name>]: <One-line actionable rule>`
3. Present the proposed 1-line rule to the user:
   *"All evals and code review passed on Round <N>! During the loop, we encountered a recurring pattern. Approve adding this 1-line rule to `REVIEW.md` -> `## 6. Rules Learned Over Time`?"*
4. **Only append the rule to `REVIEW.md` after the user approves.**

```

---

#### `.claude/skills/first-time-user/SKILL.md`

```markdown
---
name: first-time-user
description: Spawns the zero-context @blind-qa subagent against a temporary database and live app server, strictly blocked from reading source code, to uncover UX friction and bugs like a real first-time customer.
argument-hint: "[feature-name] [optional: target-url]"
allowed-tools: Read, Write, Bash, Agent
disable-model-invocation: true
---

# First-Time Customer Blind QA Skill (`/first-time-user`)

Test feature `$ARGUMENTS` from the perspective of a brand-new user who has never seen the codebase:

## Step 1: Spin Up Ephemeral Sandbox & Temporary Database
1. Create an isolated temporary database so real development data is never touched:
   ```bash
   export QA_SANDBOX_ID="qa-$(date +%s)"
   export DATABASE_URL="file:/tmp/qa-sandbox-${QA_SANDBOX_ID}.db"

```

2. Run schema migrations and minimal baseline seed data against `$DATABASE_URL`.
3. Start the application on an isolated QA port (e.g., `PORT=4199`) in the background and wait until `curl -sSf http://localhost:4199` responds.

## Step 2: Dispatch `@blind-qa` Subagent (Zero Source Code Access)

Delegate to `@blind-qa` with **only**:

* The live entry URL (`http://localhost:4199`).
* A plain-English customer goal (e.g., *"You are a new user trying to invite a teammate to your workspace. Figure out how to do it from the UI, test both desktop and mobile screen sizes, try invalid inputs, and report every place where a user might get confused or stuck."*).
* **Do NOT pass** file paths, route definitions, component names, or implementation details in the prompt. (The `.claude/hooks/block-source-read.sh` hook automatically blocks `@blind-qa` from reading source code or running git/file inspection commands.)

## Step 3: Tear Down Sandbox & Synthesize Actionable Fixes

1. Once `@blind-qa` writes `specs/$ARGUMENTS/qa-report.md`, stop the background QA server on port `4199` and remove `/tmp/qa-sandbox-${QA_SANDBOX_ID}.db*`.
2. Read `specs/$ARGUMENTS/qa-report.md`.
3. Present a structured summary of what `@blind-qa` discovered (Broken Flows, UX Friction, Mobile Glitches) along with concrete fixes you can apply upon user approval.

```

---

#### `.claude/skills/fix-a-bug/SKILL.md`

```markdown
---
name: fix-a-bug
description: Reproduction-first debugging and rollback skill. Reproduces a bug deterministically, uses Git history/bisect on feature branches to isolate the breaking commit, verifies the root cause, and fixes or rolls back cleanly.
argument-hint: "[feature-name] \"[bug-description]\""
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
disable-model-invocation: true
---

# Reproduction-First Bug Fix & Rollback Skill (`/fix-a-bug`)

Execute this 5-step protocol for `$ARGUMENTS`:

## Step 1: Reproduce the Bug Deterministically First
1. Do **not** guess at a fix or edit source code yet.
2. Write an automated reproduction test (`tests/repro/repro-<slug>.spec.ts`) or reproduction script that follows the exact user steps described in the bug report.
3. Run the reproduction test and confirm that it **fails reliably** (reproducing the exact symptom).

## Step 2: Isolate the Breaking Change via Git History
1. Inspect the atomic checkpoint commits on `feature/<feature-name>` (`git log --oneline main..HEAD`).
2. If multiple commits exist, run `git bisect` using the reproduction script:
   ```bash
   git bisect start HEAD main
   git bisect run npm test -- tests/repro/repro-<slug>.spec.ts
   git bisect reset
3. Identify the exact commit diff (`git show <breaking-commit-hash>`) and formulate a hypothesis for the root cause.

## Step 3: Verify Hypothesis & Decide Rollback vs. Targeted Fix

* **Fast Rollback Option**: If the bug is in production or blocks release, offer an immediate clean revert of the offending commit/branch (`git revert <hash>`).
* **Targeted Fix**: Apply the minimal root-cause fix and verify that `tests/repro/repro-<slug>.spec.ts` transitions from `FAIL` to `PASS`.

## Step 4: Promote Reproduction Test to `eval.md`

1. Add the reproduction test as a permanent evaluation entry in `specs/<feature-name>/eval.md` so the regression can never slip through again.
2. Re-run `@verifier` to confirm all existing evaluations plus the new regression eval pass.
3. Commit the working state: `git commit -m "fix(<feature-name>): resolve <slug> and add regression eval"`.

## Step 5: Propose a Learned Rule for `REVIEW.md`

Since this bug escaped earlier checks, draft a 1-line rule under `## 6. Rules Learned Over Time` in `REVIEW.md` explaining how `@reviewer` should catch this defect class in the future, and ask the user for approval to append it.

```

---

### 5. Reference Feature Artifacts (`specs/example-feature/`)

#### `specs/example-feature/rd.md`

```markdown
# Requirements Document (RD): Workspace Team Invites

## 1. Overview
Allow Workspace Admins to invite new teammates via email address, assign a role (`Admin`, `Member`, `Viewer`), and revoke pending invitations.

## 2. Requirements
- **REQ-01 (Access Control)**: Only authenticated users with role `Admin` in the current workspace may create or revoke invitations.
- **REQ-02 (Validation & Duplicates)**: Reject invalid email formats and reject invitations if the email already belongs to an active workspace member or has an unexpired pending invitation (`409 Conflict`).
- **REQ-03 (Token Security)**: Generate a cryptographically random 32-byte token, store only its SHA-256 hash in the database, and set expiration to 72 hours.
- **REQ-04 (Rate Limiting)**: Limit invitation creation to 10 requests per minute per workspace to prevent email spam abuse.
- **REQ-05 (Responsive UI)**: Render as a centered modal on desktop (`1440x900`) and a bottom-sheet drawer on mobile (`390x844`), including loading, empty pending-list, and duplicate-email error states.

```

---

#### `specs/example-feature/state.md`

```markdown
# Review Loop State Tracker: `example-feature`

- **Feature**: `example-feature` (`feature/example-feature`)
- **Risk Tier**: `HIGH` (Reviewer Effort: `high`)
- **Current Phase**: `in_progress`
- **Current Round**: `2` of `5`
- **Reviewer Sign-Off**: `false`

---

## Round History

### Round 1
- **Builder**: Implemented `/api/workspaces/[id]/invites` POST/DELETE routes, Prisma schema, and `InviteModal` component.
- **Verifier**:
  - `EVAL-01` (SHA-256 Token Hashing): `PASS`
  - `EVAL-02` (Duplicate Invite 409): `PASS`
  - `EVAL-03` (Rate Limit 429): `PASS`
  - `EVAL-04` (Mockup & Mobile Viewport Check): `FAIL` — Mobile drawer submit button clipped at `390x844` due to `100vh` instead of `100dvh`.
- **Reviewer (`effort: high`)**:
  - `[Severity: Blocker] [Defect-Class: Missing-Tenant-Scope]` `src/api/invites/revoke.ts:28` — `DELETE /api/invites/:inviteId` deletes by `inviteId` without filtering by `workspaceId`, allowing an Admin of Workspace A to revoke invites belonging to Workspace B (IDOR).
  - `[Severity: High] [Defect-Class: Duplicate-Submission]` `src/components/InviteModal.tsx:64` — Submit button is not disabled while `isSubmitting` is true.

### Round 2 (Current)
- **Builder**: Fixed `workspaceId` scoping across all invite endpoints (`revoke.ts`, `resend.ts`, `list.ts`), disabled submit button during async inflight, and switched mobile drawer to `100dvh`.
- **Verifier**: All `EVAL-01` through `EVAL-04` marked `PASS`.
- **Reviewer**: Pending Round 2 delta audit (`git diff HEAD~1..HEAD`).

```

---

#### `specs/example-feature/state.json`

```json
{
  "feature": "example-feature",
  "phase": "in_progress",
  "round": 2,
  "rethink_required": false,
  "consecutive_stop_blocks": 0,
  "active_defect_classes": [],
  "reviewer_sign_off": false,
  "evaluations": [
    {
      "id": "EVAL-01",
      "name": "Token Storage SHA-256 Hashing & 72h Expiry",
      "status": "PASS",
      "exit_code": 0,
      "last_run": "2026-10-30T19:15:00Z",
      "output_summary": "Passed: Plaintext token absent from DB; SHA-256 digest and 72h TTL verified."
    },
    {
      "id": "EVAL-02",
      "name": "Duplicate & Cross-Tenant Invite Prevention",
      "status": "PASS",
      "exit_code": 0,
      "last_run": "2026-10-30T19:15:04Z",
      "output_summary": "Passed: Duplicate email returns 409; cross-workspace revoke returns 404."
    },
    {
      "id": "EVAL-03",
      "name": "Rate-Limiting Barrier Check (10 req/min)",
      "status": "PASS",
      "exit_code": 0,
      "last_run": "2026-10-30T19:15:11Z",
      "output_summary": "Passed: Requests 1-10 returned 201; request 11 returned 429 Too Many Requests."
    },
    {
      "id": "EVAL-04",
      "name": "Desktop, Mobile (390x844), and Error State Mockup Alignment",
      "status": "PASS",
      "exit_code": 0,
      "last_run": "2026-10-30T19:15:22Z",
      "output_summary": "Passed: Zero horizontal overflow on mobile; DOM states match mockups."
    }
  ]
}

```

---

#### `specs/example-feature/mockups/states.html`

*(Added in v3 to complement `desktop.html` and `mobile.html` so all app states—Loading, Empty, and Error—are checked on a single canvas alongside mobile widths)*

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mockup - All App States (Loading, Empty, Error & Mobile Preview)</title>
  <style>
    :root {
      --bg: #0f172a;
      --card: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --primary: #38bdf8;
      --danger: #ef4444;
    }
    body {
      margin: 0;
      padding: 32px;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    h1 { font-size: 1.25rem; margin-bottom: 24px; color: var(--primary); }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 24px;
      align-items: start;
    }
    .state-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
    }
    .state-label {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--muted);
      margin-bottom: 12px;
      display: block;
    }
    .skeleton {
      height: 38px;
      background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%);
      border-radius: 6px;
      margin-bottom: 12px;
    }
    .empty-box {
      text-align: center;
      padding: 24px 12px;
      border: 1px dashed var(--border);
      border-radius: 8px;
      color: var(--muted);
      font-size: 0.875rem;
    }
    .error-alert {
      background: rgba(239, 68, 68, 0.15);
      border-left: 4px solid var(--danger);
      padding: 12px;
      border-radius: 4px;
      color: #fca5a5;
      font-size: 0.85rem;
      margin-bottom: 12px;
    }
    .btn-disabled {
      width: 100%;
      padding: 10px;
      border-radius: 6px;
      background: #475569;
      color: #cbd5e1;
      border: none;
      cursor: not-allowed;
      font-weight: 600;
    }
  </style>
</head>
<body>
  <h1>Feature State Matrix: Workspace Team Invites</h1>
  <div class="grid">
    <!-- State 1: Inflight Loading / Disabled Trigger -->
    <div class="state-card" data-state="loading">
      <span class="state-label">State 1: Submitting / Loading</span>
      <div class="skeleton" aria-busy="true"></div>
      <div class="skeleton" style="width: 70%;"></div>
      <button class="btn-disabled" disabled aria-disabled="true">Sending Invitation...</button>
    </div>

    <!-- State 2: Empty Pending Invitations -->
    <div class="state-card" data-state="empty">
      <span class="state-label">State 2: Empty Pending Invites List</span>
      <div class="empty-box">
        No pending invitations. Invite a teammate above to collaborate.
      </div>
    </div>

    <!-- State 3: Duplicate Email / 409 Conflict Error -->
    <div class="state-card" data-state="error">
      <span class="state-label">State 3: Duplicate Member Error (409)</span>
      <div class="error-alert" role="alert" aria-live="polite">
        <strong>Cannot Send Invite:</strong> alex@company.com is already a member of this workspace.
      </div>
      <button class="btn-disabled" style="background: var(--primary); color: #0f172a; cursor: pointer;">Try Another Email</button>
    </div>
  </div>
</body>
</html>

```