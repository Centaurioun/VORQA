# VORQA native Codex hook pilot — design (2026-10-31)

## Decision

Prior native evidence shows VORQA's installed bridge works directly and via explicit instructions, but ordinary positive routing fails under both full and one-skill catalogs. Model-driven skill selection is not a reliable enforcement trigger in the tested environment. We select a **separate native hook feasibility pilot**, not a full AVRL orchestration rewrite.

The existing Claude AVRL controller and Codex v0.1.0 are unchanged. This experimental package adds read-only prompt context and a fixture-only Stop continuation test. Neither is a release gate.

## Alternatives

1. Continue optimizing skill description — insufficient causal evidence.
2. MCP server — introduces deployment/tool plumbing without solving host activation.
3. Repository AGENTS.md — useful guidance, not a hook or hard completion gate.
4. **Native `UserPromptSubmit`/ `Stop` pilot** — selected for proving host event delivery and trust in a controlled setting.

## Event contract

- Codex documents plugin-bundled hooks and a required trust review, but deployed alpha CLI behavior must be checked. `UserPromptSubmit` and `Stop` ignore `matcher`.
- Prompt event: classify without logging raw text, check existing AVRL initialization via the canonical read-only bridge `probe`, inject fixed context only when a coding/QA request is plausibly eligible. An untouched/uninitialized repo remains silent.
- Stop event: observational by default; a fixture marker and explicit environment flag allow **one** continuation in a sandboxed test. `decision: block` creates a continuation prompt; it does not reject or revoke a task result.
- Bounded input, output, timeout; no persistent writes, no secret spill, no automatic approval or forged evidence.

## Acceptance and critical exclusions

GitHub CI can validate syntax, hook JSON, contract tests and regression safety. **Only trusted real Codex sessions** can validate plugin hook discovery, event delivery, model-context injection, and one-time Stop continuation. No production release enforcement, no security boundary claim, no global settings, no hook-trust bypass, no forced plugin upgrade, no full 10-case benchmark until native feasibility passes.

User approval is needed before installing/trusting hook definitions on the Mac. A successful native hook pilot should lead to a separate design for deterministic state/receipt enforcement with fail-safe rollout, not a declaration that v0.2 is complete.
