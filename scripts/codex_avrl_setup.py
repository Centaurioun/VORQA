#!/usr/bin/env python3
"""Opt-in Codex/AVRL bootstrap and disposable positive bridge smoke test.

This is a repository-side utility, not an automatic plugin installer. It never
enables Claude/Codex hooks, approves a feature, or releases a project.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

REPOSITORY = Path(__file__).resolve().parents[1]
CORE = REPOSITORY / "claude" / "implementation"
BRIDGE = REPOSITORY / "codex" / "plugin" / "vorqa" / "scripts" / "bridge.py"
PINNED = {
    "avrl.py": "db6a055f7f944c7925156890e19bcab7506b3281f51c26878c61845ad14cd0b2",
    "trace_events.py": "3e957a79077e3b905017640de545464905e9eea208b7797236c6ae249367b35e",
}
RUNTIME = ("avrl.py", "trace_events.py", "browser_checks.py",
           "browser_runtime.py", "blind_browser.py")
FEATURE = "example-signup"


class SetupError(Exception):
    pass


def source_files() -> dict[str, bytes]:
    """Read only the reviewed AVRL runtime, pinning the controller and helper."""
    result = {}
    scripts = CORE / "scripts"
    for name in RUNTIME:
        path = scripts / name
        if path.is_symlink() or not path.is_file():
            raise SetupError(f"missing or symlinked core source: {name}")
        data = path.read_bytes()
        if name in PINNED and hashlib.sha256(data).hexdigest() != PINNED[name]:
            raise SetupError(f"controller source does not match Codex bridge pin: {name}")
        result[name] = data
    if not BRIDGE.is_file() or BRIDGE.is_symlink():
        raise SetupError("VORQA bridge missing or symlinked")
    return result


def run(argv: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                              text=True, timeout=45, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SetupError(f"subprocess unavailable: {argv[0]}") from exc


def checked(argv: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    outcome = run(argv, cwd=cwd, env=env)
    if outcome.returncode:
        raise SetupError(f"step failed ({argv[0]} exit={outcome.returncode})")
    return outcome.stdout.strip()


def git_workspace(path: Path) -> Path:
    if not path.is_dir() or path.is_symlink():
        raise SetupError("workspace must be an existing, non-symlinked directory")
    resolved = path.resolve()
    if not (resolved / ".git").exists():
        raise SetupError("workspace must be an initialized Git repository")
    root = checked(["git", "rev-parse", "--show-toplevel"], cwd=resolved)
    if Path(root).resolve() != resolved:
        raise SetupError("workspace must be exactly the Git root")
    if checked(["git", "status", "--porcelain", "--untracked-files=all"], cwd=resolved):
        raise SetupError("workspace is dirty; no files written")
    return resolved


def install(workspace: Path, *, apply: bool) -> dict[str, object]:
    files = source_files()
    root = git_workspace(workspace)
    scripts = root / "scripts"
    if scripts.is_symlink():
        raise SetupError("workspace scripts path is a symlink")
    if scripts.exists() and not scripts.is_dir():
        raise SetupError("workspace scripts path is not a directory")
    for name in RUNTIME:
        target = scripts / name
        if target.exists() or target.is_symlink():
            raise SetupError(f"destination exists; refuse overwrite: scripts/{name}")
    if apply:
        scripts.mkdir(exist_ok=True)
        for name, data in files.items():
            (scripts / name).write_bytes(data)
    return {"mode": "install", "applied": apply,
            "files": [f"scripts/{name}" for name in RUNTIME],
            "next": ("Review and commit these files; add .avrl/ and specs/*/state.md "
                     "to .gitignore; author a feature-specific PRD/eval/scenarios. "
                     "Init and human approvals remain separate operator steps.")}


def copy_example_spec(target: Path) -> None:
    source = CORE / "specs" / FEATURE
    if not source.is_dir():
        raise SetupError("example feature specification missing")
    for entry in source.rglob("*"):
        if entry.is_symlink():
            raise SetupError("example specifications contain symlinks")
    shutil.copytree(source, target, ignore=lambda _folder, names:
                    {"state.md"} if "state.md" in names else set())


def smoke() -> dict[str, object]:
    files = source_files()
    with tempfile.TemporaryDirectory(prefix="vorqa-codex-smoke-") as tmp:
        root = Path(tmp) / "fixture"
        scripts = root / "scripts"
        scripts.mkdir(parents=True)
        for name, data in files.items():
            (scripts / name).write_bytes(data)
        copy_example_spec(root / "specs" / FEATURE)
        (root / ".gitignore").write_text(".avrl/\nspecs/*/state.md\n__pycache__/\n*.pyc\n")
        commands = (
            ["git", "init", "-b", "main"],
            ["git", "config", "user.name", "VORQA Disposable Fixture"],
            ["git", "config", "user.email", "fixture@example.invalid"],
            ["git", "add", "."],
            ["git", "commit", "-m", "test: seed isolated AVRL contract"],
            ["git", "switch", "-c", f"feature/{FEATURE}"],
        )
        for command in commands:
            checked(command, cwd=root)
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
               "AVRL_APPROVAL_HOME": str(Path(tmp) / "approval")}
        checked([sys.executable, str(scripts / "avrl.py"),
                 "init", FEATURE, "--risk", "low"], cwd=root, env=env)
        git_sha = checked(["git", "rev-parse", "HEAD"], cwd=root)
        observed = {}
        for command, arguments in (
            ("probe", ["probe"]),
            ("status", ["status", "--feature", FEATURE]),
        ):
            response = run([sys.executable, str(BRIDGE), "--workspace", str(root),
                            *arguments], cwd=root, env=env)
            if response.returncode:
                raise SetupError(f"bridge {command} failed (exit={response.returncode})")
            try:
                payload = json.loads(response.stdout)
            except ValueError as exc:
                raise SetupError(f"bridge {command} returned invalid JSON") from exc
            observed[command] = payload
        if not (observed["probe"].get("available") is True
                and observed["probe"].get("reason") == "controller_present"
                and observed["status"].get("available") is True
                and observed["status"].get("reason") == "observed_unverified"
                and observed["status"].get("feature") == FEATURE
                and observed["status"].get("status") == "in-review"):
            raise SetupError("real controller probe/status did not meet expected bounds")
        return {"mode": "smoke", "result": "POSITIVE_PROBE_STATUS_PASS",
                "git_sha": git_sha, "probe": observed["probe"],
                "status": observed["status"], "approval": "not_performed",
                "verify": "not_performed", "independent_review": "not_performed",
                "fixture": "disposable; removed after check"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_subparsers(dest="action", required=True)
    action.add_parser("smoke", help="Create, initialize and verify a disposable fixture")
    install_parser = action.add_parser("install", help="Opt-in install to a clean Git root")
    install_parser.add_argument("--workspace", type=Path, required=True)
    install_parser.add_argument("--apply", action="store_true",
                                help="Copy reviewed AVRL scripts; default is dry-run")
    args = parser.parse_args()
    try:
        result = smoke() if args.action == "smoke" else install(
            args.workspace, apply=args.apply)
        print(json.dumps(result, sort_keys=True))
        return 0
    except SetupError as exc:
        print(json.dumps({"result": "BLOCKED", "reason": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
