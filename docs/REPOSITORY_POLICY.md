# Repository and source publication policy

**Repository:** `Centaurioun/VORQA` (public). Public visibility does **not** grant reuse rights. A license for the original code has not been chosen.

## Classes

1. Original AVRL/VORQA code — audit secrets and ownership before publishing.
2. AI-generated audits/reviews — historical input; never a substitute for independent tests.
3. Source dossiers and copied transcripts — may contain third-party copyright material; do not republish entire documents without redistribution rights.
4. Runtime outputs — signatures/keys, temporary DBs, logs and evidence: never commit.

## Import gate

Before staging anything from the current local `claude/` folder: inspect hidden files, secrets, personal paths, credentials, copyright and licenses; confirm every item is intended for public distribution. Prefer short summaries and official source links to copying protected text. Stage reviewed paths explicitly, not by `git add .`. Preserve original baselines without rewriting them.

## GitHub metadata

Repository name: **VORQA**. Recommended description: "VORQA — Verification, Orchestration, Review & Quality Assurance: an evidence-driven, cross-platform agent review framework." Recommended topics after platform verification: `ai-agents`, `agentic-workflows`, `code-review`, `verification`, `quality-assurance`, `claude-code`, `codex`.

`CODEOWNERS` requests reviewers but **does not itself enable mandatory review/branch protection**. Verify GitHub repository rules separately.
