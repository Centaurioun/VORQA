# Six-cycle iterative refinement

This is a **VORQA project protocol**, inspired by structured brainstorming/planning/review; it is not a claim that Superpowers has a native skill with this exact title.

1. **Discover** — inspect the existing repository and supplied sources before suggesting changes.
2. **Model** — compare alternatives, identify constraints and architecture decisions.
3. **Implement** — make scoped, reversible changes under the approved phase.
4. **Falsify** — run checks appropriate to the scope; do not claim unrun tests passed.
5. **Red-team** — seek bypasses, provenance errors, race conditions and misleading completion claims.
6. **Converge** — fix findings, rerun relevant checks, report remaining risks and traceability.

## Phase 0 decisions

- One core plus thin host adapters, not four cloned projects.
- Preserve the local `claude/README.md` rather than publishing a conflicting file at the same path.
- Local source migration is dry-run-first, hash-preserving, with no automatic upload.
- Root `AGENTS.md` and `CLAUDE.md` govern VORQA development, not future consumer installs.
- A public repository does not authorize third-party transcript redistribution.
- Do not generate fake host plugins or mark untested adapters as complete.

## Acceptance

Root structure documented; source moves previewable without modification; collisions refused; no raw sources or sensitive data published. Claude runtime checks intentionally deferred.
