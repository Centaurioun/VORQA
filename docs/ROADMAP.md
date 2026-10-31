# VORQA roadmap

## Phase 0 — Repository foundation and source import (completed)

Create the root README, agent rules, source inventory, safe local organizer, public-source policy, and four adapter directories. Source import completed through PR #2. Phase 0 did not certify Claude runtime behavior.

## Phase 1 — Claude Code core and adapter work (existing candidate; outside current active priority)

The imported AVRL v2 candidate is tracked at `claude/implementation/`. The earlier Phase 1 plan is documented in [first design](superpowers/specs/2026-10-30-claude-qa-hardening-design.md) and [implementation plan](superpowers/plans/2026-10-30-claude-qa-hardening.md); its outstanding items include independent human/reviewer approval, evidence authenticity, browser isolation/selector discovery, configurable server adapters, independent mockups, regression coverage, concurrency, crash recovery and maintainability. They are not active work in the current Codex-focused Goal. Claude Code integration tests remain deferred until the target host is used.

### Phase 1 slice 2 — evidence-bound review and QA

Structured reviewer reports and browser event receipts are bound to the Git commit, accepted contract, round and a fresh verifier nonce. The new checks only establish **local evidence consistency**; separate user identities, externally authenticated reviewer sign-off and protected CI release attestations are not part of the selected local workflow. See [design](superpowers/specs/2026-10-30-review-qa-evidence-integrity-design.md).

### Phase 1 slice 3 — GitHub identity audit (implemented, not enforced)

A read-only, GitHub API-backed PR approval audit evaluates current reviewer account permissions and exact-head approval freshness; high-risk changes request two distinct authorized GitHub accounts. See [identity and branch-protection runbook](GITHUB_REVIEW_POLICY.md). This is **not** a mandatory merge gate: branch protection and automatic trusted review checks remain optional, not enforced by this repository.

### Phase 1 slice 4 — lifecycle observability and real-scenario pilot

The Claude candidate now records sanitized hook outcomes and controller state transitions, with a scenario matrix exercising real Git, a seeded HTTP/SQLite app and Playwright on capable CI hosts. **Native Claude Code hook dispatch is a separate, unverified acceptance check.** See [pilot runbook](../claude/implementation/docs/OBSERVABILITY_PILOT.md) and [design](superpowers/specs/2026-10-30-observability-real-scenario-design.md).

**Operator decision (2026-10-30):** Do not add branch protection, mandatory external reviewer approvals or additional isolation infrastructure as development milestones. The GitHub review identity auditor remains an optional, read-only tool; it does not enforce merges. Existing hook and acceptance guards stay in place. This changes the target assurance level: do not claim hardened security against a process sharing the same OS user.

### Phase 1 slice 5 — full positive lifecycle acceptance

Add a disposable, real Git/AVRL controller smoke from `init` to `complete` with explicit test-fixture PTY approvals. GitHub CI full mode drives black-box Playwright and checks SQLite persistence; a tampered reviewer report must invalidate the finished state. This does not prove independent human approval or native Claude Code agent dispatch. See [pilot runbook](../claude/implementation/docs/FULL_LIFECYCLE_PILOT.md).

## Phase 2 — Codex integration completion (explicit-workflow preview delivered)

Complete a useful, explicit Codex workflow over the shared AVRL core and prove it with host-observable acceptance. The previously reported installed v0.1.0 bridge provides read-only `probe` and `status` diagnostics. The hook-free v0.2.0-preview.1 integration on GitHub main `29ad871abe16515cfa8ffe2fbc1dcf0a4ce3f33b` adds explicit lifecycle operations and passed 56 VORQA and 22 Foundation tests. Prior isolated Codex runs observed explicit bridge/probe/status behavior; automatic activation and full lifecycle remain unverified. The separate v0.2.0-alpha.1 hook pilot and PR #19 packaging hardening remain hook experiments; neither native hook delivery nor trust acceptance is verified. Local tests and shell bridge calls are not host acceptance. See the [Codex evidence matrix](release/codex-evidence-matrix.md) and [release gates](release/codex-release-gates.md).

## Phase 3 — Antigravity (deferred)

Retain existing adapter material. Do not develop or claim a verified Antigravity adapter during the active Codex-only work.

## Phase 4 — GitHub Copilot (deferred)

Retain existing adapter material. Do not develop or claim a verified Copilot adapter during the active Codex-only work.

## Phase 5 — Codex-only public release (blocked; `RELEASE NO-GO`)

Prepare a release only for the exact Codex feature set demonstrated by evidence. The three preview documents define scope, evidence and gates. Public release remains blocked by unresolved source-rights/provenance for historical repository content and signer identity trust. The local preview package and disposable install/rollback evidence do not waive these requirements. Do not publish or describe the candidate as production-ready while these gates remain open. Native hooks are excluded unless separately accepted; the present pilot remains experimental. See [Codex preview](release/codex-preview.md), [evidence matrix](release/codex-evidence-matrix.md) and [release gates](release/codex-release-gates.md).
