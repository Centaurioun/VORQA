# Architecture: one core, four adapters

VORQA is an evidence-based autonomous verification framework. **The core** owns test contracts, state transitions, evidence provenance, Git binding, review convergence and completion decisions. **Adapters** own only native host integration (skills, agents, hooks and packaging).

The existing AVRL v2 is a **candidate core**, not a security-certified implementation. It needs hardening and real Claude Code validation before reuse elsewhere.

## Logical layers

1. Contract — PRD, risk, eval criteria, independently authored mockups, decisions.
2. State and evidence — atomic state, test results, hashes, Git identifiers and recovery.
3. Runner — tests, browser, disposable database and fail-closed completion.
4. Governance — human approval, independent reviewer/QA, release policy.
5. Platform integration — separate adapters for Claude Code, Codex, Antigravity and GitHub Copilot over the shared AVRL core. The current user-selected delivery priority is Codex completion plus Codex-only release readiness; Antigravity and Copilot are deferred.

## Working layout

```text
VORQA/
├── README.md
├── AGENTS.md
├── CLAUDE.md
├── claude/
│   ├── OVERVIEW.md
│   ├── implementation/          # AVRL candidate core; not security or host certified
│   ├── archive/                 # Historical baseline; publication governed by source policy
│   └── reference/               # Curated references; publication governed by source policy
├── codex/README.md
├── antigravity/README.md
├── copilot/README.md
├── docs/
└── scripts/organize_claude_sources.py
```

**Invariants:** no adapter weakens core gates; PASS belongs to a verifiable code state; human approval is not editable text; agent instructions are not OS isolation; no platform is labeled functional without a test on that host.

## Current Codex scope and evidence boundary

The Codex adapter does not own or duplicate AVRL lifecycle rules. Its previously reported installed v0.1.0 diagnostic bridge exposes read-only `probe` and `status`; `status` invokes the selected workspace's `scripts/avrl.py` controller. The hook-free v0.2.0-preview.1 integration adds explicit state-changing workflow commands on top of GitHub main `29ad871abe16515cfa8ffe2fbc1dcf0a4ce3f33b`; its local tests and disposable install/rollback passed, and explicit Codex bridge/probe/status behavior was previously observed. Automatic activation, full lifecycle and public release remain unverified. This integration is hook-free. The separate v0.2.0-alpha.1 native-hook pilot remains experimental; neither its definitions nor PR #19's packaging changes establish native delivery.

The explicit workflow should use supported Codex invocation mechanisms only when they are actually accepted on the host. Native hooks are not a security boundary or an implied release gate. Project trust, plugin enablement, hook trust and actual event delivery are distinct observations. Current product and release decisions are recorded in the [Codex preview](release/codex-preview.md), [evidence matrix](release/codex-evidence-matrix.md) and [release gates](release/codex-release-gates.md); source selection and public release remain blocked.

See [ADR-0001](decisions/0001-adapters-and-source-provenance.md).
