# VORQA

**Verification · Orchestration · Review · Quality Assurance**

VORQA is an evidence-oriented verification and code-review framework with separate adapters. The Codex adapter has a hook-free explicit-workflow developer preview, `0.2.0-preview.1`; Antigravity and Copilot remain deferred. This preview is not a stable or public release.

## Platform layout

| Directory | Scope | Status |
| --- | --- | --- |
| [claude/](claude/OVERVIEW.md) | AVRL candidate core, Claude adapter work and curated history | Separate implementation and acceptance scope |
| [codex/](codex/README.md) | OpenAI Codex plugin and explicit workflow | `0.2.0-preview.1`, hook-free preview |
| [antigravity/](antigravity/README.md) | Google Antigravity adapter material | Deferred |
| [copilot/](copilot/README.md) | GitHub Copilot adapter material | Deferred |
| [docs/](docs/ARCHITECTURE.md) | Architecture, roadmap, governance and provenance | Active |

An agent's statement that work is complete is not proof. VORQA reports controller state and evidence boundaries; it does not authenticate human identity or replace operating-system isolation.

## Codex preview

The plugin is available through the opt-in repository marketplace at `.agents/plugins/marketplace.json`. Installation, explicit `$vorqa-workflow` use, bridge behavior, security limits and rollback are documented in [codex/plugin/vorqa/README.md](codex/plugin/vorqa/README.md). Automatic skill selection is best-effort. Native hooks are excluded. `observed_unverified` is not a PASS or approval, and `verify` runs project commands with the caller's OS permissions.

## Source and rights

Public repository visibility does not grant redistribution rights. MIT was selected as the maintainer's intended license, but no root LICENSE is being added until rights for every historical item are supported. This preview does not add historical transcripts or native-hook experiments to the plugin package.

See [architecture](docs/ARCHITECTURE.md), [roadmap](docs/ROADMAP.md), [source publication policy](docs/REPOSITORY_POLICY.md), [contributing](CONTRIBUTING.md) and [security](SECURITY.md).
