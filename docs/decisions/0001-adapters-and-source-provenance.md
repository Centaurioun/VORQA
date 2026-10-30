# ADR-0001 — Single core and safe source provenance

**Date:** 2026-10-30  
**Status:** Accepted for repository organization; product runtime design remains subject to review.

## Context

A local, untracked Claude Code source tree contains AVRL v1/v2 historical baselines, original research and Argon analyses. The GitHub repository is public. Planned target hosts: Claude Code, Codex, Antigravity and Copilot.

## Decision

Build a single auditable core with four thin, independently tested host integrations. Start with Claude Code. Classify historical sources before import, preserve snapshots, and do not automatically publish unreviewed transcripts or artifacts.

## Rejected

- Four cloned implementations: divergent security rules and maintenance.
- A generic prompt treated as a functional host adapter: unverified native tool behavior.
- Immediate public upload of all local documents: source secrets/rights not checked.
