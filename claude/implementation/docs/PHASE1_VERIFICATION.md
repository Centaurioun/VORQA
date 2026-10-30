# Phase 1: Primary-source verification and ground-truth decisions

Verified on **2026-10-30**. The two uploaded files are workflow requirements and an annotated source dossier, **not** automatically an official Anthropic configuration. This repository implements a custom local workflow derived from them.

## Primary documentation verified

| Feature | Official primary-source reference | Architecture decision |
|---|---|---|
| CLAUDE.md | https://code.claude.com/docs/en/memory | Root project instructions and a non-fenced `@REVIEW.md` import |
| Skills | https://code.claude.com/docs/en/skills | `.claude/skills/<name>/SKILL.md`, YAML frontmatter, user-triggered high-impact workflows |
| Custom agents | https://code.claude.com/docs/en/sub-agents | `.claude/agents/*.md`, `tools` allowlist, `effort`, `maxTurns`, `omitClaudeMd` for blind agent |
| Hook event/exit semantics | https://code.claude.com/docs/en/hooks | `PreToolUse` blocks before execution on exit 2; `PostToolUse` records after the fact; `Stop` may continue conversation; `TaskCompleted` can refuse completion |
| Hook error semantics | https://code.claude.com/docs/en/hooks | `onFailure: block` on supported command PreToolUse hooks, **requires v2.1.295+**; impossible to assume fail-closed hooks if client is older |
| Settings hierarchy | https://code.claude.com/docs/en/settings | Project `.claude/settings.json` may be overridden or disabled by higher-precedence settings; inspect `/hooks` and effective configuration |
| Official review process | https://claude.dev/blog/solving-code-review-at-anthropic/ (2026-10-15) | Independent pre-PR verification, adversarial PR review, automated security, CI, risk-scaled humans, staged deployment, rollback |
| Source control scale | https://www.anthropic.com/research/redesigning-source-control (2026-10-13; updated 2026-10-15) | Git is correct for this local template; internal Scion/Antique are not open implementations |
| Hosted review access | https://support.claude.com/en/articles/14233555-set-up-code-review-for-claude-code | Anthropic's hosted Code Review is separate, Team/Enterprise gated and does not itself block PR merges |

## Claims reconciled

- Anthropic's engineering article verifies the 50+ cycle anecdote, ~59% previously present code, and after-three-round architectural reconsideration. It describes diff-only re-review after early passes, plus suppression of duplicates and defect-class fixes. The local default of a strict three-round breaker is **our implementation**, not a native Claude Code hook.
- The source dossier's seven-layer outline counts fast telemetry/rollback as a seventh stage; the article labels its diagram **six layers with rollback underneath**. We preserve six gates with rollback as an independent operational safety net instead of claiming a literal seven-stage built-in Claude feature.
- Human risk tiers in Anthropic's article: low 0 PR approvals, medium 1, high 2. This repository deliberately requires **prebuild eval/mockup approval at every tier** (AI Labs addition), and separately records release-commit human attestations for medium/high; Git hosting must enforce protected-branch approval rules.
- `REVIEW.md` is automatically discovered by the hosted Code Review service at repository root; the local CLI agent also imports it explicitly from `CLAUDE.md` to avoid relying on hosted behavior.
- Browser DOM comparison and ephemeral test-database creation are **locally implemented tools** in this repository, not automatic capabilities of Claude Code hooks or skills. They need a permitted browser runtime.
- A hook cannot guarantee source confidentiality against untrusted processes, user-level `--settings` overrides or code with the same operating-system permissions. True isolation needs OS-level sandboxes and enforced CI.

## Version prerequisites

The repository targets Claude Code **v2.1.295 or newer** for the documented `onFailure: "block"` behavior. Use `claude --version`, `/doctor`, and `/hooks` to inspect actual installation and loaded hooks. Python standard library controller requires Python 3.11 or newer; optional Playwright and Pillow versions are constrained in `requirements-browser.txt`. Only POSIX hosts are supported by the controller's `fcntl` locking and the Bash hooks.

## Source-to-file traceability

- Uploaded transcript sections `write-eval`, review agent independence, convergence, first-time user, fix a bug: `.claude/skills/*` and `.claude/agents/*`.
- Uploaded source dossier review severity, rounds, approvals and rollback: `REVIEW.md`, `scripts/avrl.py`, `.github/workflows/verify.yml` and this reference.
- Hook mechanism, JSON payload, `agent_type` and `stop_hook_active`: `.claude/hooks/hook_logic.py`.
- Missing actual browser/DB orchestration: `scripts/browser_checks.py`, `scripts/blind_browser.py`, `scripts/ephemeral_db.py`, `scripts/demo_server.py`.
