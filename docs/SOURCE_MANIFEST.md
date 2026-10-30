# Claude Code source inventory and planned names

The maintainer reported these files **locally** inside `claude/`. They were not part of the initial GitHub commit. This manifest is based on supplied filenames and descriptions, not independent permission to republish the content.

| Before (relative to `claude/`) | After (relative to `claude/`) |
| --- | --- |
| `README.md` | `reference/exports/avrl-v2-original-readme.md` |
| `PHASE3_RED_TEAM_AUDIT.md` | `reference/exports/avrl-v2-red-team-audit.md` |
| `An audit of the initial files against th.md` | `reference/argon/argon-v3-audit.md` |
| `Autonomous Agentic Review & Verification.md` | `reference/argon/argon-v2-architecture.md` |
| `gemini-code-1793375431751.md` | `reference/argon/argon-vs-avrl-comparison.md` |
| `anthropic_claude_code_review_research_sources.md` | `reference/research/source-dossier.md` |
| `claude_code_review_workflow.md` | `reference/research/workflow-transcript.md` |
| `AVRL_v1_baseline/` | `archive/avrl-v1-baseline/` |
| `claude-verification-loop/` | `implementation/` |

The workflow filename may contain a literal backslash before `.md`; the organizer detects either variant and refuses if both exist. The Argon comparison filename should be checked against its actual content before publishing. Unknown files are never moved.

Neither `reference/` nor `implementation/` should be committed until the [publication gate](REPOSITORY_POLICY.md) passes.
