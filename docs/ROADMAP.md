# VORQA roadmap

## Phase 0 — Repository foundation and source import (completed)

Create the root README, agent rules, source inventory, safe local organizer, public-source policy, and four adapter directories. Source import completed through PR #2. Phase 0 did not certify Claude runtime behavior.

## Phase 1 — Claude Code hardening (in progress)

The imported AVRL v2 candidate is now tracked at `claude/implementation/`. Phase 1 proceeds as bounded, test-backed slices; see [first design](superpowers/specs/2026-10-30-claude-qa-hardening-design.md) and [implementation plan](superpowers/plans/2026-10-30-claude-qa-hardening.md). Address independent human/reviewer approval, evidence authenticity, browser isolation/selector discovery, configurable server adapters, independent mockups, regression coverage, concurrency, crash recovery and maintainability. Claude Code integration tests are deferred until the target host is used.

### Phase 1 slice 2 — evidence-bound review and QA

Structured reviewer reports and browser event receipts are bound to the Git commit, accepted contract, round and a fresh verifier nonce. The new checks only establish **local evidence consistency**; separate user identities, externally authenticated reviewer sign-off and protected CI release attestations remain release blockers. See [design](superpowers/specs/2026-10-30-review-qa-evidence-integrity-design.md).

## Phase 2 — Codex

Build a native skill integration and, when justified, an installable Codex plugin. Reuse the core; do not paste Claude-specific hook semantics into Codex.

## Phase 3 — Antigravity

Map supported skill/rule discovery and tool permissions to the VORQA core, then test on Antigravity.

## Phase 4 — GitHub Copilot

Implement native repo guidance, custom agent, skills and hook configuration using the supported Copilot environment, with honest limits.

## Phase 5 — Production release

Add real target-host test matrices, independent audit and CI release gates, reproducible packaging, approved license and verified provenance. No platform is "done" merely because a directory exists.
