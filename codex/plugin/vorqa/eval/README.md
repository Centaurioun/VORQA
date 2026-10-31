# VORQA Codex plugin activation acceptance — v0.1

**Scope:** Test whether Codex chooses the `vorqa-workflow` skill for appropriate requests and avoids it for irrelevant ones. This is a developer-preview **acceptance harness**, not a simulator that can certify Codex host behavior by itself.

## Two independent evaluations

1. **Plugin Eval structural/static analysis**. In a Codex session with Plugin Eval already available, use `plugin-eval analyze codex/plugin/vorqa --format markdown`. It checks package, skill, and code structure. Its initial deterministic engine does **not** execute Codex or measure live automatic activation.
2. **Native host trials**. Install/enable the local VORQA plugin through Codex's supported UI/CLI with explicit operator consent. A repository marketplace is available at `.agents/plugins/marketplace.json`, which exposes `codex/plugin/vorqa` as `AVAILABLE`, not installed-by-default. Run the scenarios in `scenarios.json` in new Codex sessions, in disposable fixture repositories, then record **observed**, not inferred, skill selection and bridge calls.

## Scenarios

The catalog contains five expected activations and five expected non-activations, including explicit VORQA inspection, substantive regression/QA, unrelated projects, trivial edits, conceptual questions, and quoted instructions that must not trigger a plugin.

Each trial should use a fresh session with a known plugin revision and record Codex version, installed-plugin state, an evidence artifact and whether the host actually emitted a verifiable skill-selection event. No task may rewrite the test catalog during execution to improve the score.

### Local-only observation schema

Store raw Codex/Playwright/terminal logs under `.avrl/codex-eval/<run-id>/evidence/` and an observations JSON file in the parent directory:

```json
{
  "schema_version": 1,
  "observations": [
    {
      "scenario_id": "explicit-probe-existing",
      "outcome": "completed",
      "selected_skill": true,
      "bridge_calls": ["probe"],
      "artifact": {
        "file": "explicit-probe-existing.log",
        "sha256": "<sha256-of-local-artifact>"
      }
    }
  ]
}
```

**This is a schema example, NOT a claim of observed activation.** Record `outcome: "blocked"`, `selected_skill: null` and `bridge_calls: []` when a host test cannot run. Leave untested scenarios out of the array entirely; they become `NOT_RUN`. Do not manufacture a plausible event.

Run:

```bash
python3 codex/plugin/vorqa/eval/acceptance_eval.py \
  --observations .avrl/codex-eval/<run-id>/observations.json \
  --evidence-root .avrl/codex-eval/<run-id>/evidence \
  --output .avrl/codex-eval/<run-id>/summary.json
```

`REPORTED_PASS` means every **reported** trial matches its expected selection/bridge behavior and all referenced local evidence hashes match. It does **not** mean the evidence is authenticated or that actual Codex host selection was independently witnessed. Missing evidence produces `BLOCKED`, missing trials `NOT_RUN`, and wrong selection or tool use `FAIL`.

The script outputs only scenario IDs, status codes and aggregate counts. It never copies raw session transcripts, absolute local paths, prompts or user data into the report. Evidence is read only to check hashes; keep it Git-ignored and private. Inspect sanitized outputs before putting them in a public PR.

## Installation safety

Do not edit global `~/.codex/config.toml`, overwrite the user's existing plugin market­places or force installation. Use the official local-plugin discovery flow to inspect/enable this **one** plugin, with the operator's permission. No new hooks, MCP server, branch protections, or external isolation service are part of this phase.

## Gate before calling Codex-ready

- Native host version and actual plugin install/discovery documented.
- All ten scenarios attempted; missing observations distinguished from failures.
- Raw evidence locally retained and hashes checked; independent manual inspection of positive activation traces.
- False-positive and false-negative activations reported separately.
- Plugin Eval static findings documented separately from host trial findings.
- No false claim that a `REPORTED_PASS` score is independent proof of native automatic activation.
