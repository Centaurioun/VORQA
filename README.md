# VORQA

**Verification · Orchestration · Review · Quality Assurance**

VORQA is an evidence-oriented, cross-platform autonomous verification and code-review framework. Its goal is a **single auditable core** with separate Claude Code, Codex, Antigravity and GitHub Copilot adapters.

> **Status: repository foundation.** The source import (PR #2) published the reviewed AVRL v1/v2 implementation snapshots under `claude/`. The Claude Code candidate is being hardened in Phase 1. No native Claude Code host verification or production certification has been completed.

## Platform layout

| Directory | Scope | Status |
| --- | --- | --- |
| [claude/](claude/OVERVIEW.md) | Claude Code implementation, archived baseline and curated references | Phase 1 hardening in progress |
| [codex/](codex/README.md) | OpenAI Codex skill/plugin adapter | Reserved |
| [antigravity/](antigravity/README.md) | Google Antigravity skills/rules adapter | Reserved |
| [copilot/](copilot/README.md) | GitHub Copilot integration | Reserved |
| [docs/](docs/ARCHITECTURE.md) | Architecture, roadmap, governance and provenance | Active |
| [scripts/organize_claude_sources.py](scripts/organize_claude_sources.py) | Non-destructive source-folder organizer | Available |

## Why this approach?

An agent's claim that work is complete is not proof of completion. VORQA aims to bind evaluations and independent review evidence to a specific Git state and an approved acceptance contract. Agent instructions and local hooks are **not** an OS security sandbox.

## Initial local migration

For historical reference, the original local import used this source-organizer process (already completed in PR #2):

```bash
git pull --ff-only origin main
python3 scripts/organize_claude_sources.py --dry-run
```

Do **not** re-run `--apply` on already migrated folders. The organizer remains available for legacy imports; see [migration instructions](docs/LOCAL_MIGRATION.md).

## Roadmap and rules

- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Six-cycle refinement](docs/SIX_CYCLE_REFINEMENT.md)
- [Local source inventory](docs/SOURCE_MANIFEST.md)
- [Source publication policy](docs/REPOSITORY_POLICY.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

**Public does not mean open source.** No redistribution license has yet been selected; source provenance and rights need review before historic transcripts or implementation files are published.

https://github.com/Centaurioun/VORQA
