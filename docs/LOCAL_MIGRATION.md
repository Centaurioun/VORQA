# Local-only migration of existing Claude sources

The files described in [the inventory](SOURCE_MANIFEST.md) are **untracked local files** on the maintainer's machine. GitHub cannot rename them until they have been added; this process deliberately avoids uploading them before a public-source audit.

From the local VORQA root:

```bash
git status --short
git pull --ff-only origin main
python3 scripts/organize_claude_sources.py --dry-run
```

Review proposed paths, especially the Argon comparison and the workflow filename variant. If correct:

```bash
python3 scripts/organize_claude_sources.py --apply
git status --short
```

The organizer refuses existing destinations/symlinks, preserves file bytes, and makes a best-effort rollback if interrupted by an ordinary exception. It does not stage, commit, push or publish. Do not run `git add .` after migration.

**Important:** No changes to the actual Mac folder have been performed from ChatGPT; the migration occurs only when the local command runs.
