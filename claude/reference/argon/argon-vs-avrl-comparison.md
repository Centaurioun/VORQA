Act as a Principal AI Systems Architect and Agentic Workflow Engineer. Your objective is to research, verify, architect, red-team, and build the complete, production-ready "Anthropic / AI Labs Autonomous Verification & Review Loop Workflow" described in our conversation.

Execute this task in four strict phases. Do not use placeholders (such as `// TODO` or `...rest of file...`); write complete, production-grade files.

---

### PHASE 1: Deep Verification & Ground-Truth Mapping
1. Search and verify the latest official Claude Code specifications for:
   - Project instructions (`CLAUDE.md`) and modular rule imports (`@REVIEW.md`).
   - Custom Skills / Slash Commands (`.claude/skills/` or `.claude/commands/`).
   - Sub-agent definitions (`.claude/agents/` with isolated context windows and tool restrictions).
   - Lifecycle Hooks in `.claude/settings.json` (`PreToolUse`, `PostToolUse`, `Stop`, and bash/file interception).
2. Cross-check the workflow mechanics from the transcript against Anthropic's engineering guidelines and reference implementations to identify any implicit requirements (e.g., how browser/DOM verification is triggered, how hooks return exit codes to block actions, and how Git state is managed).

---

### PHASE 2: Complete File & Workflow Generation (v1 Baseline)
Generate the full file tree and complete contents for the entire system:

1. **Core Configuration & Memory**
   - `CLAUDE.md`: Root operational rules, mandatory Git branch-per-feature and atomic working-state commit protocol, workflow routing, and `@REVIEW.md` link.
   - `REVIEW.md`: Severity taxonomy (Blocker, High, Medium, Nit), failure definitions, false-positive suppression rules, test expectations, and the dynamic `## Rules Learned Over Time` section.
   - `specs/<feature-name>/prd.md` & `state.md`: Reference example of a feature requirement doc and the loop state tracker.

2. **Skills & Templates (`.claude/skills/`)**
   - `risk-classifier/SKILL.md`: Evaluates customer blast radius (Low = visual/UI only; Medium = broken feature, recoverable, no data/financial loss; High = financial loss, auth lockout, or cross-user data leak) and outputs a structured risk tier.
   - `write-eval/SKILL.md` & `write-eval/eval-template.md`: Reads `prd.md` + risk rating -> generates strict, falsifiable `eval.md` criteria -> generates standalone HTML/CSS mockups (desktop + mobile + edge-case states) prior to app code -> transitions feature status from `draft` to `in-review` -> outputs an autonomous decision log -> halts for human sign-off.
   - `review-loop/SKILL.md`: The orchestrator loop that initializes `state.md`, spawns isolated sub-agents (`builder`, `verifier`, `reviewer`), enforces the 3 Anthropic anti-infinite-loop rules (max 3-to-5 round cap before architectural rethink, diff-only inspection after Round 1, and defect-class categorization so the builder fixes the entire class of bug across the codebase), halts early if the exact same bug persists after 2 rounds of fixes, and proposes 1-line rules for `REVIEW.md` upon completion.
   - `first-time-user/SKILL.md`: Spawns a zero-context black-box QA agent against an ephemeral/seeded test database to navigate the live UI like a new customer and report UX friction or broken flows.
   - `fix-a-bug/SKILL.md`: Reproduction-first debugging skill that writes a failing reproduction test, uses Git history/bisect on feature branches to isolate the breaking commit, verifies the root cause, and applies either a targeted fix or clean rollback.

3. **Isolated Sub-Agents (`.claude/agents/`)**
   - `builder.md`: Implements features strictly against `prd.md`, approved mockups, and `eval.md`.
   - `verifier.md`: Runs automated tests and browser/mockup checks against `eval.md`, marking each criterion `PASS` or `FAIL` with evidence.
   - `reviewer.md`: Independent adversarial code reviewer operating in a fresh context window using `REVIEW.md` and configurable effort levels (`low`, `medium`, `high`).
   - `blind-qa.md`: The restricted sub-agent used by `first-time-user`.

4. **Enforcement Hooks (`.claude/settings.json` + `.claude/hooks/`)**
   - `enforce-eval-pass.sh` (`Stop` / completion hook): Blocks the agent from marking a task done unless `eval.md` exists, is approved, and all eval checks are marked `PASS` in `state.md`.
   - `block-source-read.sh` (`PreToolUse` hook): Blocks the `blind-qa` agent from reading source code via file-reading tools (`Read`, `Grep`, `Glob`) OR bypassing the block via terminal commands (`cat`, `grep`, `rg`, `find`, `git log`, `git show`, etc.).

---

### PHASE 3: Adversarial Audit, Gap Analysis & Edge-Case Discovery
Critically inspect your Phase 2 implementation and explicitly list every flaw, gap, and failure mode you find across these dimensions:
- **Hook Bypass Vulnerabilities**: How could an agent accidentally or creatively bypass the shell/file hooks?
- **State Desynchronization**: What happens if a sub-agent crashes mid-round or corrupts `state.md`?
- **Token & Context Bloat**: Where will context windows overflow during multi-round diffs or mockup comparisons?
- **Deadlocks**: Where could the completion hook accidentally trap the agent when it legitimately needs to pause and ask the human for input?
- **Tooling Gaps**: What scripts or MCP/browser helpers are missing to make mockup-to-live-app visual comparison and ephemeral DB spin-up actually work in practice?

---

### PHASE 4: Iterative Remediation & v2 Production Hardening
Fix every single issue identified in Phase 3. Output the upgraded **v2 Production-Hardened Files** (and package the entire repository structure into a downloadable `.zip` archive or clean, ready-to-use files), complete with a `README.md` quickstart guide showing the exact commands to run the workflow from start to finish.