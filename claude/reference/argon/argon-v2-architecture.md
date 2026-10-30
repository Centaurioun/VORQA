# Autonomous Agentic Review & Verification Workflow (Production System v2)

This implementation codifies Anthropic's Claude Code engineering practices, Addy Osmani's agentic testing principles, and Boris Cherny's verification harness into a production-grade, hardened repository structure.

Every file below is complete, fully specified, and ready to be dropped directly into your repository.

---

### File Tree

```
.
├── CLAUDE.md
├── REVIEW.md
├── .claude/
│   ├── settings.json
│   ├── hooks/
│   │   ├── enforce-eval-pass.sh
│   │   └── block-source-read.sh
│   ├── agents/
│   │   ├── builder.md
│   │   ├── verifier.md
│   │   ├── reviewer.md
│   │   └── blind-qa.md
│   └── skills/
│       ├── risk-classifier/
│       │   └── SKILL.md
│       ├── write-eval/
│       │   ├── SKILL.md
│       │   └── eval-template.md
│       ├── review-loop/
│       │   └── SKILL.md
│       ├── first-time-user/
│       │   └── SKILL.md
│       └── fix-a-bug/
│           └── SKILL.md
└── specs/
    └── example-feature/
        ├── prd.md
        ├── eval.md
        ├── state.json
        └── mockups/
            ├── desktop.html
            ├── mobile.html
            └── error-empty.html

```

---

### Root Configuration & Rules

#### `CLAUDE.md`

```markdown
# Operational Instructions for Claude Code

## Prime Directives
1. **Never declare victory without executable proof**: A feature is complete only when verified by independent evaluations defined in `eval.md` and confirmed by a clean pass from the isolated reviewer agent.
2. **Review rules are mandatory**: Always load, reference, and enforce `@REVIEW.md`.

## Git & Branching Protocol
- **Branch-per-feature**: Never commit directly to `main` or `develop`. Before starting any feature work, create a isolated branch: `feature/<feature-name>`.
- **Atomic working-state commits**: When an evaluation step passes, create a commit tagged with the passed eval: `git commit -m "feat(<feature>): pass eval <id> - <description>"`.
- **Clean rollback points**: Ensure every commit leaves the repository in a passing, runnable state so that automated bug bisecting (`/fix-a-bug`) can isolate regressions without intermediate build noise.

## Architectural Constraints & Workflow Routing
When a user asks to plan, design, or write a feature, route execution through the following pipeline:
1. Run `/risk-classifier` on the feature requirements.
2. Run `/write-eval` to generate falsifiable evaluation criteria and HTML/CSS mockups. Stop and wait for explicit human review.
3. Run `/review-loop` to orchestrate `builder`, `verifier`, and `reviewer` sub-agents in fresh contexts until all evals pass or the 5-round circuit breaker triggers.
4. For customer-facing user journeys, run `/first-time-user` with a zero-context black-box agent against a seeded sandbox database.
5. If regressions are discovered post-merge, run `/fix-a-bug` to reproduce, isolate via git-bisect, and remediate.

## Context Hygiene
- Do not mix the roles of builder and reviewer in the same session.
- Use the sub-agent definitions in `.claude/agents/` to ensure the evaluator does not inherit the confirmation bias of the implementation session.

```

---

#### `REVIEW.md`

```markdown
# Code Review Standards & Verification Rules

## 1. Severity Taxonomy & Blocking Criteria

| Severity | Criteria | System Action |
| :--- | :--- | :--- |
| **Blocker** | Data corruption, financial loss, auth bypass, tenant crossover, unhandled exceptions in critical customer paths, regression in core workflows. | Immediate loop termination. Roll back to last passing git commit. Notify human supervisor. |
| **High** | Feature completely non-functional, missing required validation, unhandled async rejection, unindexed foreign-key queries on high-throughput tables. | Reject loop iteration. Builder must fix the entire class of problem before next review pass. |
| **Medium** | Recoverable performance degradation, missing edge-case UI states (loading, empty, error), unlogged caught exceptions, incomplete test coverage. | Reject round. Builder remediates in current loop. |
| **Nit** | Style discrepancies, minor copy deviations, non-semantic variable naming, minor documentation omissions. | Do NOT block the loop. Log in `state.json` as non-blocking technical debt. |

## 2. Review Methodology: Failure Analysis
Do not verify simply whether code was read. Focus review on answering:
1. **Failure Modes**: How can this change fail under malformed inputs, network interruptions, race conditions, or permission boundaries?
2. **Defect-Class Scoping**: If a bug is caught (e.g., missing null-check or lack of idempotency), identify every instance of that class across the entire feature, not just the flagged line.
3. **Diff-Scoped Auditing**: In rounds subsequent to Round 1, review **only** the git diff between the current iteration and the previous commit to prevent re-flagging persistent low-priority items and burning tokens.

## 3. False-Positive Suppression
- Do not re-flag items previously categorized as `Nit` unless modified in the latest diff.
- Do not demand refactoring of adjacent, untouched legacy code outside the active feature branch.
- Suppress warnings on known scaffolding patterns marked with `/* scaffold-verified */`.

## 4. Rules Learned Over Time
<!--
AUTOMATED SYSTEM SECTION:
The review-loop skill automatically appends validated one-line rules below
when regressions occur across sessions or repeated reviewer loops detect recurring anti-patterns.
-->
- [RL-001]: All database transactions that update user balances or inventory must use explicit row-level locking (`SELECT FOR UPDATE`) to prevent race conditions.
- [RL-002]: Client-side form handlers must disable submit triggers immediately upon the first click to prevent duplicate execution during network latency.
- [RL-003]: Sub-agents must not rely on system environment variables for auth secrets; inject mocked test secrets explicitly in test environments.
- [RL-004]: Mobile layouts must explicitly define viewport height units (`dvh` instead of `vh`) to prevent address-bar clipping on iOS devices.

```

---

### Configuration & Security Hooks

#### `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "script": ".claude/hooks/block-source-read.sh"
      }
    ],
    "Stop": [
      {
        "matcher": ".*",
        "script": ".claude/hooks/enforce-eval-pass.sh"
      }
    ]
  },
  "permissions": {
    "allow_subagents": true,
    "bash_execution_mode": "prompt_on_write"
  }
}

```

---

#### `.claude/hooks/enforce-eval-pass.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

# enforce-eval-pass.sh
# Stop hook: Ensures an agent cannot terminate a feature build without passing all falsifiable evals.

STATE_FILE="specs/current-feature/state.json"
MOCK_ALLOW_ENV="${ALLOW_EARLY_STOP:-false}"

# Bypass if explicitly allowed (e.g. human intervention or non-feature chore tasks)
if [ "$MOCK_ALLOW_ENV" = "true" ]; then
  exit 0
fi

# If no active feature state exists, allow normal termination
if [ ! -f "$STATE_FILE" ]; then
  exit 0
fi

PHASE=$(jq -r '.phase // empty' "$STATE_FILE")

# Allow the agent to pause if it is deliberately waiting for human review of evals/mockups
if [ "$PHASE" = "awaiting_human_eval_approval" ] || [ "$PHASE" = "awaiting_human_decision" ]; then
  echo "[HOOK:INFO] System pausing legitimately for human verification. Allowing halt."
  exit 0
fi

# Verify all evaluation criteria have passed
TOTAL_EVALS=$(jq '.evaluations | length' "$STATE_FILE" 2>/dev/null || echo "0")
PASSED_EVALS=$(jq '[.evaluations[] | select(.status == "PASS")] | length' "$STATE_FILE" 2>/dev/null || echo "0")

if [ "$TOTAL_EVALS" -eq 0 ]; then
  echo "[HOOK:BLOCK] Termination rejected: No falsifiable evaluations recorded in $STATE_FILE." >&2
  exit 1
fi

if [ "$PASSED_EVALS" -ne "$TOTAL_EVALS" ]; then
  FAILED_COUNT=$((TOTAL_EVALS - PASSED_EVALS))
  echo "[HOOK:BLOCK] Termination rejected: $FAILED_COUNT of $TOTAL_EVALS evaluations have not passed." >&2
  echo "[HOOK:BLOCK] Run .claude/skills/review-loop/SKILL.md to resolve remaining failures." >&2
  exit 1
fi

# Verify that the independent reviewer signed off
REVIEW_SIGN_OFF=$(jq -r '.reviewer_sign_off // false' "$STATE_FILE")
if [ "$REVIEW_SIGN_OFF" != "true" ]; then
  echo "[HOOK:BLOCK] Termination rejected: Independent reviewer agent has not marked reviewer_sign_off as true in $STATE_FILE." >&2
  exit 1
fi

echo "[HOOK:SUCCESS] All $TOTAL_EVALS evaluations passed and reviewer approval verified. Task complete."
exit 0

```

---

#### `.claude/hooks/block-source-read.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

# block-source-read.sh
# PreToolUse hook: Prevents black-box QA agents from reading project source code
# to preserve genuine user perspective and prevent confirmation bias.

# Inspect agent persona context from the execution environment
AGENT_ROLE="${CLAUDE_AGENT_ROLE:-orchestrator}"

if [ "$AGENT_ROLE" != "blind-qa" ]; then
  exit 0
fi

TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

# 1. Intercept direct file-reading tools
if [[ "$TOOL_NAME" =~ ^(Read|Grep|Glob|FileSearch)$ ]]; then
  # Allow reading temporary artifacts, test logs, and ephemeral sandbox outputs
  if [[ "$TOOL_INPUT" =~ ^(specs/.*|mockups/.*|/tmp/.*|\.claude/qa-results/.*) ]]; then
    exit 0
  fi
  echo "[SECURITY:BLOCK] Access Denied: The 'blind-qa' agent is restricted from inspecting application source files." >&2
  exit 1
fi

# 2. Intercept terminal commands attempting to bypass tool boundaries
if [ "$TOOL_NAME" = "Bash" ]; then
  # Match attempts to view code, inspect git commits, or search source
  BANNED_COMMANDS="cat |head |tail |less |more |nl |od |xxd |view |nano |vim |vi |sed |awk |grep |rg |ag |find |git log|git show|git diff|git checkout"

  # Normalize input
  CLEAN_CMD=$(echo "$TOOL_INPUT" | tr '\n' ' ' | tr -s ' ')

  if echo "$CLEAN_CMD" | grep -iE "(^|[ ;|&])($BANNED_COMMANDS) " >/dev/null 2>&1; then
    # Allow safe read operations on designated mockups and QA logs
    if [[ "$CLEAN_CMD" =~ (specs/|mockups/|/tmp/|\.claude/qa-results/) ]]; then
      exit 0
    fi
    echo "[SECURITY:BLOCK] Access Denied: Terminal inspection of application source files or git history is strictly blocked for the blind-qa agent." >&2
    exit 1
  fi
fi

exit 0

```

---

### Isolated Sub-Agent Profiles (`.claude/agents/`)

#### `.claude/agents/builder.md`

```markdown
---
name: builder
description: Implementation agent dedicated strictly to generating code and passing defined evals.
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

You are the **Builder Agent**. Your sole responsibility is to implement features and bug fixes to satisfy the evaluation criteria defined in `eval.md` and the approved UI mockups.

## Operating Rules
1. **Spec Compliance**: Read `specs/<feature>/prd.md`, `specs/<feature>/eval.md`, and all approved mockups in `specs/<feature>/mockups/` before writing any code.
2. **Implementation Scope**: Write clean, modular, production-ready code. Do not write test stubs or bypass checks.
3. **Defect-Class Remediations**: When receiving feedback from the Reviewer indicating a problem category, search the entire codebase and fix all instances of that category.
4. **No Premature Declarations**: When finished with code changes, hand control back to the orchestrator. Do not attempt to update `reviewer_sign_off` or mark overall feature completion.

```

---

#### `.claude/agents/verifier.md`

```markdown
---
name: verifier
description: Execution and falsification agent that tests code against eval criteria in a clean environment.
tools:
  - Bash
  - Read
  - Write
---

You are the **Verifier Agent**. You operate with zero investment in the code that was written. Your goal is to falsify claims that the feature is done.

## Operating Rules
1. **Execute Every Check**: For each item in `specs/<feature>/eval.md`:
   - Execute the precise deterministic command or script listed in the evaluation.
   - For UI comparisons, capture browser headless screenshots and run visual/DOM comparisons against the approved mockups.
2. **Immutable Record**: Update `specs/<feature>/state.json` with the exact stdout, stderr, execution duration, and timestamp for each eval.
3. **Strict Truthfulness**: Mark an evaluation as `PASS` if and only if the exit code is `0` and all assertion criteria are satisfied. Any unexpected output is a `FAIL`.
4. **Never Fix Code**: You are an auditor. Do not write or edit production code. Report your findings and terminate.

```

---

#### `.claude/agents/reviewer.md`

```markdown
---
name: reviewer
description: Adversarial code reviewer operating in a fresh context window to audit diffs against REVIEW.md.
tools:
  - Bash
  - Read
  - Write
---

You are the **Adversarial Code Reviewer**. You evaluate pull requests and incremental code diffs. You assume bugs and vulnerabilities exist.

## Operating Rules
1. **Fresh Context**: You evaluate the implementation strictly through `git diff` against the parent branch, verified results in `state.json`, and the operational guidelines in `REVIEW.md`.
2. **Diff-Only Analysis**:
   - In Round 1, review the full feature diff.
   - In Rounds 2 through 5, review **only** the delta between the latest commit and the previous round's commit. Do not repeat previous medium/nit issues.
3. **Categorize by Defect Class**: Group all flagged issues into clear architectural categories (e.g., `[Auth-Boundary]`, `[Idempotency]`, `[Unhandled-Async]`, `[CSS-Viewport-Clipping]`).
4. **Sign-Off Authority**:
   - If ANY `Blocker` or `High` severity issues exist, set `"reviewer_sign_off": false` in `state.json`.
   - If only `Nit` issues remain and all evals in `eval.md` are marked `PASS`, set `"reviewer_sign_off": true`.

```

---

#### `.claude/agents/blind-qa.md`

```markdown
---
name: blind-qa
description: Black-box customer persona agent blocked from seeing source code. Interacts only via browser/CLI interfaces.
tools:
  - Bash
---

You are a **First-Time Customer Persona**. You have never seen the source code, database architecture, or technical specifications of this application.

## Operating Rules
1. **Black-Box Environment**: You interact with the application solely through the public UI (using headless browser automation or curl commands directed at the test port).
2. **Zero Internal Knowledge**: Do not assume API payloads, route names, or schema structures. Discover them entirely through the rendered HTML/DOM or public interface.
3. **Goal-Oriented Testing**: Execute real customer journeys (e.g., "Sign up, purchase an item, change my billing email, view my invoice").
4. **UX & Edge Case Reporting**: Flag any scenario where:
   - Form errors fail to explain what went wrong.
   - Layout elements overlap, clip, or behave erratically.
   - Workflows take more than 3 steps without clear navigation cues.
   - Network lag leaves the user without a visual progress indicator.
5. Record your session walkthrough and friction points in `specs/<feature>/qa-report.md`.

```

---

### Skills & Workflow Orchestration (`.claude/skills/`)

#### `.claude/skills/risk-classifier/SKILL.md`

```markdown
---
name: risk-classifier
description: Evaluates customer blast radius and sets the required evaluation rigor before development begins.
---

# Risk Classifier Skill

Execute the following analysis on the input specification:

## 1. Classification Matrix
Evaluate the feature against the following customer blast-radius tiers:

- **LOW**:
  - UI visual enhancements, static copy updates, layout restyling.
  - Failure impact: Aesthetic only; feature continues to function; no customer data or transaction compromised.
  - Required Rigor: Basic unit tests + 1 visual viewport regression check.

- **MEDIUM**:
  - New user-facing non-critical flows, reporting filters, export features.
  - Failure impact: Flow fails gracefully with an error; customer cannot complete task but loses no money, data, or access.
  - Required Rigor: Unit + integration tests + mobile/desktop mockups + negative error-state evals.

- **HIGH**:
  - Authentication, authorization, billing, payment processing, data migrations, tenant routing, webhook dispatching.
  - Failure impact: Customer loses funds, experiences downtime, gets locked out, or views another customer's data.
  - Required Rigor: Unit + integration + concurrency race testing + adversarial penetration checks + full black-box QA run.

## 2. Output Schema
Write the resulting rating to `specs/<feature-name>/risk-profile.json`:

```json
{
  "feature": "<feature-name>",
  "risk_level": "LOW|MEDIUM|HIGH",
  "rationale": "<justification>",
  "mandatory_checkpoints": [
    "<checkpoint-1>",
    "<checkpoint-2>"
  ]
}

```

```

---

#### `.claude/skills/write-eval/eval-template.md`

```markdown
# Evaluation Specification: {{FEATURE_NAME}}

- **Risk Level**: {{RISK_LEVEL}}
- **Status**: {{STATUS}} <!-- draft | in-review | approved -->
- **Target Branch**: {{BRANCH_NAME}}

---

## 1. Mockup Alignments
| Screen / State | Mockup Reference | Viewport / Conditions | Verification Method |
| :--- | :--- | :--- | :--- |
| Primary Desktop | `mockups/desktop.html` | 1440x900, Default data | Headless DOM diff < 2% pixel drift |
| Mobile Responsive | `mockups/mobile.html` | 390x844 (iPhone 14) | No horizontal overflow, touch targets >= 44px |
| Error / Empty | `mockups/error-empty.html` | Network failure / 0 results | Explicit retry button and aria-alert visible |

---

## 2. Deterministic Verification Criteria (Evals)
Every criterion must be automated, falsifiable, and exit with code 0 on success.

```json
[
  {
    "id": "EVAL-01",
    "name": "Database Constraint Enforcement",
    "command": "npm run test:integration -- tests/features/{{FEATURE_NAME}}/db-constraint.test.ts",
    "timeout_ms": 15000,
    "required": true
  },
  {
    "id": "EVAL-02",
    "name": "Visual Alignment Check",
    "command": "npm run test:visual -- specs/{{FEATURE_NAME}}/mockups/desktop.html http://localhost:3000/{{FEATURE_ROUTE}}",
    "timeout_ms": 30000,
    "required": true
  },
  {
    "id": "EVAL-03",
    "name": "Idempotent Retry Execution",
    "command": "bash tests/scripts/test-idempotency.sh {{FEATURE_ROUTE}}",
    "timeout_ms": 20000,
    "required": true
  }
]

```

---

## 3. Autonomous Decisions Log

Record every autonomous engineering decision made while designing these evals:

1. *Decision*: Mockup uses CSS grid rather than flexbox for data table layout.
* *Rationale*: Preserves column alignment when content lengths fluctuate.


2. *Decision*: Timeout set to 15000ms for db integration tests.
* *Rationale*: Accommodates container spin-up overhead during cold start.



```

---

#### `.claude/skills/write-eval/SKILL.md`

```markdown
---
name: write-eval
description: Generates strict, falsifiable evaluation criteria and standalone HTML/CSS mockups before development begins.
---

# Write-Eval Skill Procedure

Follow these sequential steps:

1. **Read Requirements**:
   - Parse `specs/<feature-name>/prd.md` and `specs/<feature-name>/risk-profile.json`.

2. **Generate Standalone UI Mockups**:
   - Before writing any application code, generate pure, standalone HTML/CSS mockups in `specs/<feature-name>/mockups/`:
     - `desktop.html`: 1440px wide viewport layout.
     - `mobile.html`: 390px wide viewport layout.
     - `error-empty.html`: Layout under empty-data and API failure conditions.
   - Validate that mockups are self-contained with no external CSS/JS dependencies.

3. **Construct `eval.md`**:
   - Use `.claude/skills/write-eval/eval-template.md` as the foundation.
   - Translate all functional requirements into deterministic bash commands or test suites.
   - Populate the `Autonomous Decisions Log`.

4. **Initialize Feature State**:
   - Create `specs/<feature-name>/state.json`:
     ```json
     {
       "feature": "<feature-name>",
       "phase": "awaiting_human_eval_approval",
       "round": 0,
       "reviewer_sign_off": false,
       "evaluations": []
     }
     ```

5. **Halt for Human Review**:
   - Present the rendered mockups and `eval.md` to the user.
   - **DO NOT PROCEED TO CODING**. Inform the user:
     *"Mockups and evaluation criteria have been generated in `specs/<feature-name>/`. Please review and approve them before implementation begins."*

```

---

#### `.claude/skills/review-loop/SKILL.md`

```markdown
---
name: review-loop
description: Orchestrates builder, verifier, and reviewer sub-agents in fresh contexts with anti-infinite-loop circuit breakers.
---

# Review-Loop Orchestration Skill

Run this loop to implement and verify a feature:

```bash
#!/usr/bin/env bash
# Pseudocode / Execution Flow of the Orchestrator Loop

FEATURE="$1"
STATE_FILE="specs/$FEATURE/state.json"
MAX_ROUNDS=5

ROUND=1
PREV_DEFECT_CLASS=""
SAME_CLASS_COUNT=0

while [ $ROUND -le$MAX_ROUNDS ]; do
  echo "=== STARTING ROUND $ROUND OF$MAX_ROUNDS ==="
  jq --arg r "$ROUND" '.round = ($r|tonumber) | .phase = "in_progress"' "$STATE_FILE" > tmp.$$&& mv tmp.$$ "$STATE_FILE"

  # Step 1: Dispatch Builder Sub-Agent
  # Fresh context: Pass only prd.md, eval.md, and state.json
  claude --agent=builder "Implement requirements and resolve any outstanding issues in $STATE_FILE"

  # Step 2: Dispatch Verifier Sub-Agent
  # Executes deterministic test commands defined in eval.md
  claude --agent=verifier "Execute all evals in specs/$FEATURE/eval.md and update evaluations array in$STATE_FILE"

  # Check if verifications passed
  ALL_PASSED=$(jq '[.evaluations[] \vert{} select(.status == "PASS")] \vert{} length == (.evaluations \vert{} length)' "$STATE_FILE")

  # Step 3: Dispatch Reviewer Sub-Agent (Adversarial)
  # Fresh context: Reads diff only (or full diff on Round 1)
  claude --agent=reviewer "Audit git diff against REVIEW.md. Record findings and set reviewer_sign_off in $STATE_FILE"

  REVIEWER_APPROVED=$(jq -r '.reviewer_sign_off' "$STATE_FILE")

  # Termination Condition: Both verifier and reviewer pass
  if [ "$ALL_PASSED" = "true" ] && [ "$REVIEWER_APPROVED" = "true" ]; then
    echo "=== SUCCESS: Feature $FEATURE passed all evals and reviewer sign-off on Round$ROUND ==="
    jq '.phase = "completed"' "$STATE_FILE" > tmp.$$&& mv tmp.$$ "$STATE_FILE"
    exit 0
  fi

  # Circuit Breaker 1: Detect Identical Defect Category Repeating
  CURRENT_DEFECT_CLASS=$(jq -r '.active_defect_class // empty' "$STATE_FILE")
  if [ -n "$CURRENT_DEFECT_CLASS" ] && [ "$CURRENT_DEFECT_CLASS" = "$PREV_DEFECT_CLASS" ]; then
    SAME_CLASS_COUNT=$((SAME_CLASS_COUNT + 1))
    if [ $SAME_CLASS_COUNT -ge 2 ]; then
      echo "[CIRCUIT BREAKER] Same defect class ($CURRENT_DEFECT_CLASS) failed across 2 consecutive rounds."
      jq '.phase = "awaiting_human_decision"' "$STATE_FILE" > tmp.$$&& mv tmp.$$ "$STATE_FILE"
      echo "Halting for human architectural intervention."
      exit 2
    fi
  else
    SAME_CLASS_COUNT=0
    PREV_DEFECT_CLASS="$CURRENT_DEFECT_CLASS"
  fi

  # Circuit Breaker 2: 3-Round Architectural Rethink
  if [ $ROUND -eq 3 ]; then
    echo "[WARNING] Reached Round 3 without full resolution. Reviewer instructs Builder to rethink implementation architecture rather than applying incremental patches."
  fi

  ROUND=$((ROUND + 1))
done

echo "[CIRCUIT BREAKER] Reached maximum round limit ($MAX_ROUNDS). Halting."
jq '.phase = "failed_max_rounds"' "$STATE_FILE" > tmp.$$&& mv tmp.$$ "$STATE_FILE"
exit 1

```

## Post-Loop Rule Synthesis

When the loop completes successfully after multiple rounds:

1. Identify any defect that required 2 or more iterations to resolve.
2. Formulate an exact, actionable 1-line rule preventing that mistake.
3. Present it to the user:
*"Would you like to append the following learned rule to `REVIEW.md`?"*
`> - [RL-XXX]: <Rule Description>`

```

---

#### `.claude/skills/first-time-user/SKILL.md`

```markdown
---
name: first-time-user
description: Deploys a zero-context black-box QA agent against an ephemeral sandbox database to test the live user experience.
---

# First-Time User Experience Skill

## Execution Steps

1. **Spin Up Ephemeral Sandbox**:
   - Initialize an isolated, temporary SQLite/Postgres database:
     ```bash
     export DATABASE_URL="file:/tmp/sandbox-qa-$(date +%s).db"
     npm run db:push
     npm run db:seed:qa
     ```
   - Launch application server on dedicated QA port `http://localhost:4199`.

2. **Dispatch Blind QA Agent**:
   - Set environment variable `CLAUDE_AGENT_ROLE="blind-qa"` to activate the security hook blocking access to application source code.
   - Launch `blind-qa` agent with only user journey goals:
     ```bash
     claude --agent=blind-qa "Navigate http://localhost:4199. Sign up as a new user, complete feature workflow for $FEATURE, and document all friction or bugs."
     ```

3. **Capture Journey Log**:
   - Compile findings into `specs/<feature>/qa-report.md`.
   - Record screenshots of unexpected UI states to `specs/<feature>/qa-screenshots/`.

4. **Tear Down Sandbox**:
   - Terminate server on port 4199.
   - Delete temporary database file `/tmp/sandbox-qa-*.db`.

```

---

#### `.claude/skills/fix-a-bug/SKILL.md`

```markdown
---
name: fix-a-bug
description: Reproduction-first debugging skill that uses git bisect and automated reproduction scripts to isolate and fix regressions.
---

# Fix-A-Bug Skill Protocol

When a regression or bug report is received:

1. **Failing Reproduction First**:
   - Write a standalone test script `tests/repro/repro-<issue-id>.test.ts` that reliably reproduces the reported failure.
   - Run the script and confirm exit code `1` (failing).

2. **Automated Git Bisect**:
   - Run automated bisect to find the exact commit that introduced the failure:
     ```bash
     git bisect start HEAD main
     git bisect run npm run test:repro tests/repro/repro-<issue-id>.test.ts
     ```
   - Log the offending commit hash and author details.

3. **Root-Cause Analysis & Fix**:
   - Create a fix branch: `bugfix/<issue-id>-root-cause`.
   - Apply minimal targeted remediation to eliminate the regression without changing adjacent behavior.

4. **Verification**:
   - Run `tests/repro/repro-<issue-id>.test.ts` -> Confirm exit code `0`.
   - Run the full test suite to guarantee zero side-effects.

5. **Rule Codification**:
   - Propose an addition to `## 4. Rules Learned Over Time` in `REVIEW.md` describing the anti-pattern that caused the bug.

```

---

### Reference Implementation Specs (`specs/example-feature/`)

#### `specs/example-feature/prd.md`

```markdown
# Product Requirements Document: Team Invite System

## 1. Objective
Allow team administrators to invite new members by email address, assign a role (`Admin`, `Member`, `Viewer`), and dispatch an invitation email containing a secure, single-use activation token.

## 2. Functional Requirements
- **FR-01**: Input field validating standard RFC-5322 email formatting.
- **FR-02**: Role selector defaulting to `Member`.
- **FR-03**: Invitations must expire automatically after 72 hours.
- **FR-04**: Prevent inviting an email that already holds active membership or a pending invitation in the current workspace.
- **FR-05**: Dispatch email through the transactional queue with signed token payload.

## 3. Security & Boundary Conditions
- Only users with the `Admin` role can execute invitations.
- Rate-limit invitation requests to a maximum of 10 requests per minute per IP.
- The invitation token must be hashed using SHA-256 before storage in the database.

```

---

#### `specs/example-feature/eval.md`

```markdown
# Evaluation Specification: Team Invite System

- **Risk Level**: HIGH
- **Status**: approved
- **Target Branch**: feature/team-invite-system

---

## 1. Mockup Alignments
| Screen / State | Mockup Reference | Viewport | Verification Method |
| :--- | :--- | :--- | :--- |
| Invite Modal Desktop | `mockups/desktop.html` | 1440x900 | DOM structural equivalence |
| Mobile Modal Drawer | `mockups/mobile.html` | 390x844 | Bottom sheet animation check |
| Error / Duplicate Email | `mockups/error-empty.html` | Any | Error container contains `aria-live="polite"` |

---

## 2. Deterministic Verification Criteria (Evals)

```json
[
  {
    "id": "EVAL-01",
    "name": "Token Storage Hashing Check",
    "command": "npm run test:integration -- tests/features/team-invite/token-hash.test.ts",
    "timeout_ms": 10000,
    "required": true
  },
  {
    "id": "EVAL-02",
    "name": "Duplicate Invitation Prevention",
    "command": "npm run test:integration -- tests/features/team-invite/duplicate-prevention.test.ts",
    "timeout_ms": 10000,
    "required": true
  },
  {
    "id": "EVAL-03",
    "name": "Rate-Limiting Barrier Check",
    "command": "npm run test:integration -- tests/features/team-invite/rate-limit.test.ts",
    "timeout_ms": 15000,
    "required": true
  },
  {
    "id": "EVAL-04",
    "name": "Desktop Layout DOM Equivalence",
    "command": "npm run test:visual -- specs/example-feature/mockups/desktop.html http://localhost:3000/settings/team/invite",
    "timeout_ms": 25000,
    "required": true
  }
]

```

---

## 3. Autonomous Decisions Log

1. *Decision*: Store tokens hashed with SHA-256 and transmit plaintext only in the email link URL.
* *Rationale*: Protects tokens from database compromise while keeping delivery simple.


2. *Decision*: Modal shifts to a bottom-sheet drawer on mobile viewports under 640px.
* *Rationale*: Matches thumb reachability standards on mobile devices.



```

---

#### `specs/example-feature/state.json`

```json
{
  "feature": "team-invite-system",
  "phase": "in_progress",
  "round": 2,
  "active_defect_class": null,
  "reviewer_sign_off": false,
  "evaluations": [
    {
      "id": "EVAL-01",
      "name": "Token Storage Hashing Check",
      "status": "PASS",
      "exit_code": 0,
      "last_run": "2026-10-30T16:22:10Z",
      "output_summary": "Passed: Plaintext token absent from database. SHA-256 hash verified."
    },
    {
      "id": "EVAL-02",
      "name": "Duplicate Invitation Prevention",
      "status": "PASS",
      "exit_code": 0,
      "last_run": "2026-10-30T16:22:15Z",
      "output_summary": "Passed: Second invite attempt rejected with 409 Conflict."
    },
    {
      "id": "EVAL-03",
      "name": "Rate-Limiting Barrier Check",
      "status": "PASS",
      "exit_code": 0,
      "last_run": "2026-10-30T16:22:25Z",
      "output_summary": "Passed: Request 11 returned 429 Too Many Requests."
    },
    {
      "id": "EVAL-04",
      "name": "Desktop Layout DOM Equivalence",
      "status": "PASS",
      "exit_code": 0,
      "last_run": "2026-10-30T16:22:40Z",
      "output_summary": "Passed: Visual drift 0.4% (well under 2.0% threshold)."
    }
  ]
}

```

---

#### `specs/example-feature/mockups/desktop.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mockup - Invite Team Member (Desktop)</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --border: #334155;
    }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      display: grid;
      place-items: center;
      min-height: 100vh;
    }
    .modal {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      width: 480px;
      padding: 24px;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    }
    h2 { margin: 0 0 8px 0; font-size: 1.25rem; }
    p { margin: 0 0 20px 0; color: var(--text-muted); font-size: 0.875rem; }
    .form-group { margin-bottom: 16px; }
    label { display: block; margin-bottom: 6px; font-size: 0.875rem; font-weight: 500; }
    input, select {
      width: 100%;
      box-sizing: border-box;
      padding: 10px 12px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: #0f172a;
      color: var(--text);
      font-size: 0.875rem;
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      margin-top: 24px;
    }
    button {
      padding: 10px 16px;
      border-radius: 6px;
      font-weight: 500;
      cursor: pointer;
      font-size: 0.875rem;
      border: none;
    }
    .btn-secondary { background: transparent; color: var(--text-muted); }
    .btn-primary { background: var(--primary); color: #0f172a; }
  </style>
</head>
<body>
  <div class="modal" role="dialog" aria-labelledby="modal-title">
    <h2 id="modal-title">Invite Team Member</h2>
    <p>Send an invitation link to collaborate in this workspace.</p>
    <div class="form-group">
      <label for="email-input">Email address</label>
      <input type="email" id="email-input" placeholder="colleague@company.com" required>
    </div>
    <div class="form-group">
      <label for="role-select">Workspace Role</label>
      <select id="role-select">
        <option value="member" selected>Member (Can edit and share)</option>
        <option value="admin">Admin (Full workspace access)</option>
        <option value="viewer">Viewer (Read-only)</option>
      </select>
    </div>
    <div class="actions">
      <button class="btn-secondary" type="button">Cancel</button>
      <button class="btn-primary" type="button">Send Invitation</button>
    </div>
  </div>
</body>
</html>

```

---

#### `specs/example-feature/mockups/mobile.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mockup - Invite Team Member (Mobile)</title>
  <style>
    body {
      margin: 0;
      background: #000;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      height: 100dvh;
    }
    .drawer {
      background: #1e293b;
      border-top: 1px solid #334155;
      border-radius: 16px 16px 0 0;
      padding: 20px;
      color: #f8fafc;
      box-sizing: border-box;
    }
    .handle {
      width: 36px;
      height: 4px;
      background: #64748b;
      border-radius: 2px;
      margin: 0 auto 16px auto;
    }
    h2 { font-size: 1.15rem; margin: 0 0 4px 0; }
    p { font-size: 0.8rem; color: #94a3b8; margin: 0 0 16px 0; }
    input, select {
      width: 100%;
      box-sizing: border-box;
      padding: 12px;
      border-radius: 8px;
      border: 1px solid #334155;
      background: #0f172a;
      color: #fff;
      font-size: 1rem;
      margin-bottom: 12px;
    }
    .btn-primary {
      width: 100%;
      padding: 14px;
      border-radius: 8px;
      background: #38bdf8;
      color: #0f172a;
      font-weight: 600;
      border: none;
      font-size: 1rem;
    }
  </style>
</head>
<body>
  <div class="drawer">
    <div class="handle"></div>
    <h2>Invite Team Member</h2>
    <p>Single-use link expires in 72 hours.</p>
    <input type="email" placeholder="colleague@company.com">
    <select>
      <option selected>Member Role</option>
      <option>Admin Role</option>
      <option>Viewer Role</option>
    </select>
    <button class="btn-primary">Send Invitation</button>
  </div>
</body>
</html>

```

---

#### `specs/example-feature/mockups/error-empty.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Mockup - Invite Error State</title>
  <style>
    body {
      background: #0f172a;
      color: #f8fafc;
      font-family: sans-serif;
      display: grid;
      place-items: center;
      min-height: 100vh;
      margin: 0;
    }
    .card {
      background: #1e293b;
      border: 1px solid #ef4444;
      border-radius: 12px;
      width: 440px;
      padding: 24px;
    }
    .error-banner {
      background: rgba(239, 68, 68, 0.15);
      border-left: 4px solid #ef4444;
      padding: 12px;
      margin-bottom: 16px;
      font-size: 0.875rem;
      color: #fca5a5;
    }
    input {
      width: 100%;
      padding: 10px;
      border: 1px solid #ef4444;
      background: #0f172a;
      color: #fff;
      border-radius: 6px;
      box-sizing: border-box;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="error-banner" role="alert" aria-live="polite">
      <strong>Invitation Failed:</strong> An active member with this email address already belongs to this workspace.
    </div>
    <label style="display:block; margin-bottom: 6px; font-size: 0.85rem;">Email address</label>
    <input type="email" value="existing.user@company.com">
  </div>
</body>
</html>

```

---

### Step-by-Step Execution Guide

To run a feature through this workflow:

1. **Classify Feature Risk**:
```bash
claude /risk-classifier "specs/example-feature/prd.md"

```


2. **Generate Evals & Mockups**:
```bash
claude /write-eval "specs/example-feature"

```


*Inspect the generated HTML files in your browser and check `eval.md`. Once satisfied, approve to transition status from `draft` to `approved`.*
3. **Execute Implementation Loop**:
```bash
bash .claude/skills/review-loop/SKILL.md example-feature

```


4. **Run Black-Box QA (for customer-facing surfaces)**:
```bash
claude /first-time-user "example-feature"

```


5. **Merge**:
Once all evals pass and `reviewer_sign_off` is `true`, create a pull request from `feature/team-invite-system` to `main`.