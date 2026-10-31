---
name: vorqa-workflow
description: Use for substantial application implementation, regression repair, or evidence-backed QA in a repository already initialized with the VORQA/AVRL controller, or when the user explicitly asks to inspect a VORQA run. Do not activate for read-only explanations, trivial text edits, or projects without VORQA unless the user explicitly asks for VORQA setup guidance.
---

# VORQA workflow — Codex developer preview

This initial plugin is **not** a full Codex implementation. It contains only a read-only bridge to a **pre-existing and trusted** AVRL workspace. Installing this plugin does not install AVRL in an application, enable host hooks, or create verified evidence. Do not claim it can enforce a Codex tool permission or a task completion event.

1. Identify the Git workspace root. Read its `AGENTS.md` and project instructions. Do not modify files for this preliminary inspection.
2. Resolve this plugin's root from the installed skill path, then invoke `python3 <plugin-root>/scripts/bridge.py --workspace <absolute-workspace-root> probe`. Use the user's configured Python environment. Never infer success from an absent controller.
3. If the bridge returns `controller_not_installed` or `not_git_root`, report **NOT INITIALIZED**; do not silently copy the Claude controller, change repository settings, or create an AVRL state directory.
4. If initialized and the user supplied a feature slug, call `python3 <plugin-root>/scripts/bridge.py --workspace <absolute-workspace-root> status --feature <slug>`. Treat `observed_unverified` as **an observed state only**, not a verified PASS or reviewer/QA approval.
5. For an implementation task, explain which required lifecycle stages are missing and request meaningful human approval through the existing controller or ordinary Codex UI, not a fabricated approval receipt. Normal coding can proceed only within the user's scope and permissions, and must not be reported as VORQA-certified until the controller's real completion gate has been exercised with actual evidence.
6. Report exact observed status, missing prerequisites, and unverified host capabilities. Do not manufacture hooks, agent starts, approvals, browser interactions, or log events.

## When **not** to use

- General conceptual or research questions without a coding task.
- A simple spelling or formatting change with no request for verification.
- Any unrelated repository that does not have the VORQA controller, unless the user is explicitly asking how to adopt it.

## Evidence rules

- Keep user approval separate from a Codex shell permission prompt.
- Claude `TaskCompleted` cannot be assumed to map to Codex `Stop`.
- Missing Codex host events are `NOT OBSERVED`, never synthetic success.
- Never log raw prompts, passwords, personal data, unfiltered exception text, or private reasoning.
- Do not start an MCP server or register hooks in this preview. Native hook delivery and automatic skill activation remain **UNVERIFIED** until installed-host evaluation.
