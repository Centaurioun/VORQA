# Architecture: one core, four adapters

VORQA is an evidence-based autonomous verification framework. **The core** owns test contracts, state transitions, evidence provenance, Git binding, review convergence and completion decisions. **Adapters** own only native host integration (skills, agents, hooks and packaging).

The existing AVRL v2 is a **candidate core**, not a security-certified implementation. It needs hardening and real Claude Code validation before reuse elsewhere.

## Logical layers

1. Contract — PRD, risk, eval criteria, independently authored mockups, decisions.
2. State and evidence — atomic state, test results, hashes, Git identifiers and recovery.
3. Runner — tests, browser, disposable database and fail-closed completion.
4. Governance — human approval, independent reviewer/QA, release policy.
5. Platform integration — Claude Code first, then Codex, Antigravity and Copilot.

## Working layout

```text
VORQA/
├── README.md
├── AGENTS.md
├── CLAUDE.md
├── claude/
│   ├── OVERVIEW.md
│   ├── implementation/          # LOCAL source migration; not yet published
│   ├── archive/                 # LOCAL v1 history; not yet published
│   └── reference/               # LOCAL research; not yet published
├── codex/README.md
├── antigravity/README.md
├── copilot/README.md
├── docs/
└── scripts/organize_claude_sources.py
```

**Invariants:** no adapter weakens core gates; PASS belongs to a verifiable code state; human approval is not editable text; agent instructions are not OS isolation; no platform is labeled functional without a test on that host.

See [ADR-0001](decisions/0001-adapters-and-source-provenance.md).
