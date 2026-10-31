# VORQA Codex plugin foundation — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Every code change needs a falsifiable test and a verification gate.

**Goal:** Establish a safe, read-only Codex plugin foundation with one auto-discoverable skill and an AVRL status bridge.

**Architecture:** Keep the Claude controller unchanged; a Codex-specific, skills-first plugin previews an existing controller's state. Native hook and MCP support are not part of P0.

**Tech stack:** Python 3.11+, unittest, Git, portable Agent Plugins 1.0, Codex compatibility manifest.

**Spec:** `docs/superpowers/specs/2026-10-31-codex-plugin-foundation-design.md`

## Global constraints

No branch protection, new isolation system, package installation, Claude runtime rewrites, external APIs, or user Mac modifications. Do not merge automatically; leave PR for maintainer review. New code is restricted to `codex/` and a foundation CI check.

## Review focus

- Foreign/untrusted workspace supplied as root — block when no matching Git root.
- A symlink controller outside workspace — refuse without executing it.
- Feature slug attempts path traversal — refuse before calling controller.
- Controller prints secrets on stdout/stderr — suppress and return bounded error.
- Malformed or injected state labels — refuse; never convert a controller status into a verified PASS.
- Plugin manifest incompatible with the installed Codex runtime — mark native discovery unverified until acceptance.

## Tasks

1. RED: write bridge tests using temporary Git repos and fake controller; verify without bridge they fail.
2. GREEN: implement `probe` and `status` with structured JSON, sanitized responses and failures; verify tests.
3. Package portable `plugin.json`, legacy `.codex-plugin/plugin.json`, and one high-signal `SKILL.md`; test metadata and activation boundaries statically.
4. Add CI to root Foundation workflow and update `codex/README.md`.
5. Read entire PR diff, run focused tests and syntax/JSON checks, verify fresh GitHub CI, leave PR open for host testing.

## Six-Cycle Iterative Refinement

1. **Discover:** Claude source is tightly bound to its own root and not a generic Codex runtime.
2. **Compare:** reject naïve Claude copying, big-bang core extraction and premature MCP; choose small plugin bridge.
3. **Implement:** add manifest, skill, read-only bridge and tests.
4. **Falsify:** missing bridge produced six test errors in isolated RED check; 9/9 tests passed after implementation. GitHub CI pending at design time.
5. **Red-team:** invalid slug, symlink, missing workspace, leaked subprocess output and untrusted status rejected; native hooks and model-driven skill activation not assumed.
6. **Converge:** update only after current-head CI; status is a developer preview until Codex-host activation plus plugin eval succeed.

## Next phase (not implemented)

Native Codex plugin installation and skill activation EVAL, deterministic runtime deployment across other projects, safe controller command interface, eventual hook compatibility testing. No false production readiness.
