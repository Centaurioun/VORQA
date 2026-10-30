# VORQA roadmap

## Phase 0 — Repository foundation and source import (completed)

Create the root README, agent rules, source inventory, safe local organizer, public-source policy, and four adapter directories. Source import completed through PR #2. Phase 0 did not certify Claude runtime behavior.

## Phase 1 — Claude Code hardening (in progress)

The imported AVRL v2 candidate is now tracked at `claude/implementation/`. Phase 1 proceeds as bounded, test-backed slices; see [first design](superpowers/specs/2026-10-30-claude-qa-hardening-design.md) and [implementation plan](superpowers/plans/2026-10-30-claude-qa-hardening.md). Address independent human/reviewer approval, evidence authenticity, browser isolation/selector discovery, configurable server adapters, independent mockups, regression coverage, concurrency, crash recovery and maintainability. Claude Code integration tests are deferred until the target host is used.

### Phase 1 slice 2 — evidence-bound review and QA

Structured reviewer reports and browser event receipts are bound to the Git commit, accepted contract, round and a fresh verifier nonce. The new checks only establish **local evidence consistency**; separate user identities, externally authenticated reviewer sign-off and protected CI release attestations are not part of the selected local workflow. See [design](superpowers/specs/2026-10-30-review-qa-evidence-integrity-design.md).

### Phase 1 slice 3 — GitHub identity audit (implemented, not enforced)

A read-only, GitHub API-backed PR approval audit evaluates current reviewer account permissions and exact-head approval freshness; high-risk changes request two distinct authorized GitHub accounts. See [identity and branch-protection runbook](GITHUB_REVIEW_POLICY.md). This is **not** a mandatory merge gate: branch protection and automatic trusted review checks remain optional, not enforced by this repository.

### Phase 1 slice 4 — lifecycle observability and real-scenario pilot

The Claude candidate now records sanitized hook outcomes and controller state transitions, with a scenario matrix exercising real Git, a seeded HTTP/SQLite app and Playwright on capable CI hosts. **Native Claude Code hook dispatch is a separate, unverified acceptance check.** See [pilot runbook](../claude/implementation/docs/OBSERVABILITY_PILOT.md) and [design](superpowers/specs/2026-10-30-observability-real-scenario-design.md).

**Operator decision (2026-10-30):** Do not add branch protection, mandatory external reviewer approvals or additional isolation infrastructure as development milestones. The GitHub review identity auditor remains an optional, read-only tool; it does not enforce merges. Existing hook and acceptance guards stay in place. This changes the target assurance level: do not claim hardened security against a process sharing the same OS user.

### Phase 1 slice 5 — full positive lifecycle acceptance

Add a disposable, real Git/AVRL controller smoke from `init` to `complete` with explicit test-fixture PTY approvals. GitHub CI full mode drives black-box Playwright and checks SQLite persistence; a tampered reviewer report must invalidate the finished state. This does not prove independent human approval or native Claude Code agent dispatch. See [pilot runbook](../claude/implementation/docs/FULL_LIFECYCLE_PILOT.md).

## Phase 2 — Codex

Build a native skill integration and, when justified, an installable Codex plugin. Reuse the core; do not paste Claude-specific hook semantics into Codex.

## Phase 3 — Antigravity

Map supported skill/rule discovery and tool permissions to the VORQA core, then test on Antigravity.

## Phase 4 — GitHub Copilot

Implement native repo guidance, custom agent, skills and hook configuration using the supported Copilot environment, with honest limits.

## Phase 5 — Production release

Add real target-host test matrices, independent audit and CI release gates, reproducible packaging, approved license and verified provenance. No platform is "done" merely because a directory exists.
