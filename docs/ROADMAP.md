# VORQA roadmap

## Phase 0 — Repository foundation (current)

Create the root README, agent rules, source inventory, safe local organizer, public-source policy, and four adapter directories. **No Claude runtime changes or tests are requested in this phase.**

## Phase 1 — Claude Code hardening

After local source curation and publication review, advance the AVRL v2 candidate. Address independent human/reviewer approval, evidence authenticity, browser isolation/selector discovery, configurable server adapters, independent mockups, regression coverage, concurrency, crash recovery and maintainability. Claude Code integration tests are deferred until the target host is used.

## Phase 2 — Codex

Build a native skill integration and, when justified, an installable Codex plugin. Reuse the core; do not paste Claude-specific hook semantics into Codex.

## Phase 3 — Antigravity

Map supported skill/rule discovery and tool permissions to the VORQA core, then test on Antigravity.

## Phase 4 — GitHub Copilot

Implement native repo guidance, custom agent, skills and hook configuration using the supported Copilot environment, with honest limits.

## Phase 5 — Production release

Add real target-host test matrices, independent audit and CI release gates, reproducible packaging, approved license and verified provenance. No platform is "done" merely because a directory exists.
