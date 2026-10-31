# VORQA Codex plugin foundation — design (2026-10-31)

## Intent

The operator wants **one easy-to-use Codex plugin**, not manual activation of several skills, a new MCP server or unnecessary branch protection. This P0 slice establishes a discoverable packaging/adapter contract while refusing to call unverified Claude functionality "Codex-native".

Reference analysis: [Codex research PR #10](https://github.com/Centaurioun/VORQA/pull/10) (draft); existing QA PR #9 remains independently open.

## Brainstorming alternatives

1. Copy Claude agents/hooks into Codex — rejected: false event equivalence and accidental enforcement claims.
2. Reorganize the whole Claude implementation into `core/` immediately — rejected: high migration risk and fragile old fixture paths.
3. **Portable local Codex plugin + one skill + narrow read-only bridge** — selected. Keep existing AVRL controller authoritative. Real install/activation remains a separate host acceptance step.

## Architecture

- Root package: `codex/plugin/vorqa/plugin.json` (portable Agent Plugins identity and OpenAI extension).
- Compatibility: `.codex-plugin/plugin.json` (Codex legacy discovery; matched identity/version).
- One skill: `skills/vorqa-workflow/SKILL.md` with explicit positive and negative activation cases.
- Bridge: `scripts/bridge.py`; `probe` verifies a **trusted pre-installed** AVRL controller in a Git root and `status --feature` asks the controller for current state.
- JSON output uses bounded, sanitized fields; `observed_unverified` must never be treated as PASS.
- The bridge **does not install AVRL**, mutate or initialize projects, synthesize evidence, invoke private hooks, or mark work complete.
- This first prototype does **not** work on unrelated projects without the AVRL controller; the next phase must design and test the installer/shared runtime extraction.

## Boundaries

Codex plugin hook support in the installed local CLI was not verified. Do not register hooks or MCP. Installing this package in the user's Mac is a separate step; GitHub CI cannot certify native plugin discovery/activation.

An AVRL controller subprocess is executable code; only point the status command at workspaces whose source the user trusts. The `probe` operation never runs it. Do not trust claimed reviewer identities or raw process output.

## Acceptance criteria

- JSON metadata and SKILL front matter can be parsed.
- Probe does not execute code or accept a symlink controller or non-Git-root workspace.
- Status requires a validated feature slug, only exposes whitelisted state and errors without stdout/stderr leaks.
- Exit 2 on missing controller, invalid input, malformed response and failure.
- Test **actual plugin files** in Python CI. Native Codex skill routing, lifecycle and complete workflow remain UNVERIFIED.
