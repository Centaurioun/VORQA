# Codex Native Hook QA — VORQA 0.2.0-alpha.1

Date: 2026-10-31
Decision: **BLOCKED — safe test-only plugin isolation was not effective in the verified Codex CLI.**

## Scope

This report records the bounded preflight and attempted setup for PR #15. The target was to prove native Codex delivery of VORQA's `UserPromptSubmit` and `Stop` hooks using only a disposable AVRL fixture. It does not report fixture/unit-test results as host evidence.

## Candidate and CI identity

- PR #15 head: `a4de8a1c7402d787a37df130fa6f69cdc369bfb2`.
- Candidate package: `vorqa` `0.2.0-alpha.1`; portable and Codex compatibility manifests agreed on the version.
- The candidate includes synchronous `UserPromptSubmit` and `Stop` command hooks and a Python dispatcher.
- Both check runs associated with that head completed successfully: `repository-foundation` and `GitGuardian Security Checks`.
- PR #15 remained open and Draft. No PR was merged.

## Isolation attempt

The existing VORQA v0.1.0 installation was preserved. The candidate was installed under the separate identity `vorqa@vorqa-pr15-candidate`; it did not overwrite `vorqa@vorqa-local`.

The candidate was then configured disabled outside the test fixture. Two supported scoping approaches were examined:

1. A one-invocation `-c` override setting the candidate plugin enabled.
2. A trusted fixture-only `.codex/config.toml` override setting the candidate plugin enabled, with the global candidate setting disabled.

In this CLI session, `codex plugin list --json` continued to report the candidate disabled from both the normal repository and the trusted fixture. The native `/hooks` screen in the fixture session did not list a VORQA hook source. The second approach therefore did not establish effective fixture-only enablement in this build. Enabling the candidate globally would allow its trusted hooks to load in other projects, so that unsafe scope was not used.

## Native host evidence

- The Codex CLI and interactive `/hooks` screen ran on Codex CLI `0.166.0-alpha.5.1`.
- The `/hooks` screen was opened from the disposable fixture. It displayed existing non-VORQA hook entries; no VORQA hook definition appeared in the observed `UserPromptSubmit` list.
- No user prompt was submitted and no VORQA `UserPromptSubmit` or `Stop` event was delivered. No VORQA hook was trusted.
- **Hook event delivery: NOT OBSERVED.**
- **Model-visible VORQA context: UNVERIFIED.**
- Positive/negative prompt behavior, bridge execution, normal Stop behavior, one-shot continuation, and loop prevention were not tested natively.

This is not a failed hook execution: the candidate could not be safely enabled only for the fixture, and testing stopped before invoking either event.

## Rollback and preserved installation

The temporary candidate plugin and marketplace were removed with Codex CLI's plugin commands. The temporary fixture project trust entry and its project-scoped override were removed. No hook trust was granted.

After cleanup, the installed VORQA inventory contained only `vorqa@vorqa-local` v0.1.0, still enabled. Its marketplace revision remained `b5efb79615cd305fbc33ad57f96b31830d9e2811`; the portable manifest, compatibility manifest, skill, and bridge SHA-256 values matched the pre-install snapshot. No other plugin was changed.

Raw CLI and host-session evidence is retained locally under the ignored `.avrl/codex-eval/` run directory. It is not included in this report.

## Next gate

Before another native hook attempt, establish a supported CLI mechanism that makes the candidate plugin effective only in a disposable trusted fixture while keeping it disabled in all other projects. Verify that scope with the installed CLI before trusting either hook. Until then, native hook acceptance remains blocked; no claim of `NATIVE HOOKS VERIFIED` is supported.
