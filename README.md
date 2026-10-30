# VORQA

**Verification · Orchestration · Review · Quality Assurance**

VORQA is an evidence-oriented, cross-platform autonomous verification and code-review framework. Its goal is a **single auditable core** with separate Claude Code, Codex, Antigravity and GitHub Copilot adapters.

> **Status: repository foundation.** The AVRL v2 implementation and historic reference files are still on the maintainer's Mac under an **untracked** `claude/` directory. They have NOT been published or validated by this repository. Do not treat this skeleton as a production-certified tool.

## Platform layout

| Directory | Scope | Status |
| --- | --- | --- |
| [claude/](claude/OVERVIEW.md) | Claude Code candidate implementation and source curation | First priority; historical code is local |
| [codex/](codex/README.md) | OpenAI Codex skill/plugin adapter | Reserved |
| [antigravity/](antigravity/README.md) | Google Antigravity skills/rules adapter | Reserved |
| [copilot/](copilot/README.md) | GitHub Copilot integration | Reserved |
| [docs/](docs/ARCHITECTURE.md) | Architecture, roadmap, governance and provenance | Active |
| [scripts/organize_claude_sources.py](scripts/organize_claude_sources.py) | Non-destructive source-folder organizer | Available |

## Why this approach?

An agent's claim that work is complete is not proof of completion. VORQA aims to bind evaluations and independent review evidence to a specific Git state and an approved acceptance contract. Agent instructions and local hooks are **not** an OS security sandbox.

## Initial local migration

After pulling the foundation files, keep your existing untracked `claude/` sources in place:

```bash
git pull --ff-only origin main
python3 scripts/organize_claude_sources.py --dry-run
```

If the proposed source/destination mapping is correct, run the script again with `--apply`. It never stages, commits, pushes, uploads or edits file contents. See [migration instructions](docs/LOCAL_MIGRATION.md).

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
