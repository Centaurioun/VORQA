#!/usr/bin/env python3
"""Read-only bridge to an existing AVRL workspace; not a plugin installer.

A workspace must contain its own trusted scripts/avrl.py and specs/ tree.
The bridge reports observed controller state, never a verified PASS decision.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

SLUG = re.compile(r"[a-z][a-z0-9-]{1,48}\\Z")
TIMEOUT = 12
STATUSES = frozenset({"draft", "in-review", "awaiting-approval", "approved", "building", "verifying", "reviewing", "rethink", "paused", "failed", "completed"})
RISKS = frozenset({"low", "medium", "high"})


def emit(kind: str, **fields: object) -> None:
    print(json.dumps({"bridge_schema": 1, "kind": kind, **fields}, sort_keys=True))


def inspect_workspace(root: Path) -> tuple[bool, str]:
    """Reject incomplete, non-root, or symlinked controllers before execution."""
    if not root.is_dir():
        return False, "workspace_missing"
    controller = root / "scripts" / "avrl.py"
    if not controller.is_file() or controller.is_symlink() or not (root / "specs").is_dir():
        return False, "controller_not_installed"
    try:
        result = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                                capture_output=True, text=True, timeout=TIMEOUT, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False, "git_unavailable"
    if result.returncode or Path(result.stdout.strip()).resolve() != root:
        return False, "not_git_root"
    return True, "controller_present"


def observed_status(root: Path, feature: str) -> tuple[bool, str, dict[str, object]]:
    if not SLUG.fullmatch(feature):
        return False, "invalid_feature", {}
    ready, reason = inspect_workspace(root)
    if not ready:
        return False, reason, {}
    try:
        result = subprocess.run([sys.executable, str(root / "scripts" / "avrl.py"),
                                 "status", feature, "--json"],
                                cwd=root, capture_output=True, text=True,
                                timeout=TIMEOUT, check=False)
    except subprocess.TimeoutExpired:
        return False, "controller_timeout", {}
    except OSError:
        return False, "controller_unavailable", {}
    if result.returncode:
        return False, "controller_rejected", {}
    try:
        state = json.loads(result.stdout)
    except (TypeError, ValueError):
        return False, "malformed_controller_response", {}
    if not isinstance(state, dict) or state.get("feature") != feature:
        return False, "mismatched_controller_response", {}
    if state.get("status") not in STATUSES or state.get("risk") not in RISKS:
        return False, "malformed_controller_response", {}
    if any(type(state.get(key)) is not int or not 0 <= state[key] <= 100
           for key in ("round", "max_rounds")):
        return False, "malformed_controller_response", {}
    public = {key: state[key] for key in ("feature", "status", "risk", "round", "max_rounds")
              if key in state and isinstance(state[key], (str, int)) and not isinstance(state[key], bool)}
    return True, "observed_unverified", public


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("probe")
    status = actions.add_parser("status")
    status.add_argument("--feature", required=True)
    args = parser.parse_args(argv)
    root = args.workspace.expanduser().resolve()
    if args.action == "probe":
        ready, reason = inspect_workspace(root)
        emit("probe", available=ready, reason=reason)
        return 0 if ready else 2
    ok, reason, fields = observed_status(root, args.feature)
    emit("status", available=ok, reason=reason, **fields)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
