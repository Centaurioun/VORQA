#!/usr/bin/env python3
"""Preview or move historical untracked Claude files without editing or publishing."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import stat
import sys
from typing import NamedTuple


class Move(NamedTuple):
    source: Path
    destination: Path
    digest: str


SOURCE_MAP: tuple[tuple[str, str], ...] = (
    ("README.md", "reference/exports/avrl-v2-original-readme.md"),
    ("PHASE3_RED_TEAM_AUDIT.md", "reference/exports/avrl-v2-red-team-audit.md"),
    ("An audit of the initial files against th.md", "reference/argon/argon-v3-audit.md"),
    ("Autonomous Agentic Review & Verification.md", "reference/argon/argon-v2-architecture.md"),
    ("gemini-code-1793375431751.md", "reference/argon/argon-vs-avrl-comparison.md"),
    ("anthropic_claude_code_review_research_sources.md", "reference/research/source-dossier.md"),
    ("AVRL_v1_baseline", "archive/avrl-v1-baseline"),
    ("claude-verification-loop", "implementation"),
)

TRANSCRIPT_ALIASES = ("claude_code_review_workflow.md", "claude_code_review_workflow\\.md")
TRANSCRIPT_TARGET = "reference/research/workflow-transcript.md"


class MigrationError(Exception):
    """A source or destination safety condition failed."""


def exists(path: Path) -> bool:
    return os.path.lexists(path)


def digest_path(path: Path) -> str:
    """Hash file or whole directory without following symlinks."""
    digest = hashlib.sha256()
    if path.is_symlink():
        raise MigrationError(f"Symbolic link refused: {path}")
    if path.is_file():
        digest.update(b"FILE\0")
        with path.open("rb") as stream:
            while block := stream.read(1024 * 1024):
                digest.update(block)
        return digest.hexdigest()
    if not path.is_dir():
        raise MigrationError(f"Unsupported source: {path}")
    digest.update(b"DIR\0")
    for parent, directories, filenames in os.walk(path, followlinks=False):
        for name in sorted(directories + filenames):
            item = Path(parent) / name
            mode = item.lstat().st_mode
            if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise MigrationError(f"Symlink or special file refused: {item}")
            digest.update(item.relative_to(path).as_posix().encode())
            digest.update(b"\0")
            if stat.S_ISREG(mode):
                with item.open("rb") as stream:
                    while block := stream.read(1024 * 1024):
                        digest.update(block)
            else:
                digest.update(b"DIRECTORY\0")
    return digest.hexdigest()


def plan(root: Path) -> tuple[list[Move], list[str]]:
    claude = root / "claude"
    if not claude.is_dir() or claude.is_symlink():
        raise MigrationError(f"Not a real directory: {claude}")
    mappings = list(SOURCE_MAP)
    variants = [name for name in TRANSCRIPT_ALIASES if exists(claude / name)]
    if len(variants) > 1:
        raise MigrationError("Both transcript filename variants exist; resolve manually")
    if variants:
        mappings.append((variants[0], TRANSCRIPT_TARGET))
    moves: list[Move] = []
    missing: list[str] = []
    for from_name, to_name in mappings:
        source = claude / from_name
        destination = claude / to_name
        if not exists(source):
            missing.append(from_name)
            continue
        if exists(destination):
            raise MigrationError(f"Target already exists, no overwrite: {destination}")
        parent = destination.parent
        while parent != claude:
            if exists(parent) and (parent.is_symlink() or not parent.is_dir()):
                raise MigrationError(f"Unsafe parent: {parent}")
            parent = parent.parent
        moves.append(Move(source, destination, digest_path(source)))
    return moves, missing


def apply(root: Path, expected: list[Move]) -> None:
    lock_file = root / ".vorqa-source-migration.lock"
    try:
        fd = os.open(lock_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise MigrationError(f"Existing migration lock: {lock_file}") from exc
    moved: list[Move] = []
    created: list[Path] = []
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(f"pid={os.getpid()}\n")
        current, _ = plan(root)
        if current != expected:
            raise MigrationError("Source paths/content changed after preview; retry")
        for entry in expected:
            if digest_path(entry.source) != entry.digest:
                raise MigrationError(f"Source changed: {entry.source}")
            needed: list[Path] = []
            parent = entry.destination.parent
            while not parent.exists():
                needed.append(parent)
                parent = parent.parent
            for directory in reversed(needed):
                directory.mkdir()
                created.append(directory)
            if exists(entry.destination):
                raise MigrationError(f"Destination appeared during move: {entry.destination}")
            entry.source.rename(entry.destination)
            moved.append(entry)
            if digest_path(entry.destination) != entry.digest:
                raise MigrationError(f"Content mismatch after move: {entry.destination}")
            print(f"MOVED {entry.source.relative_to(root)} -> {entry.destination.relative_to(root)}")
    except Exception:
        errors = []
        for entry in reversed(moved):
            try:
                if exists(entry.source):
                    raise MigrationError(f"Original path occupied during rollback: {entry.source}")
                entry.destination.rename(entry.source)
            except (OSError, MigrationError) as exc:
                errors.append(str(exc))
        if errors:
            raise MigrationError("Rollback incomplete: " + "; ".join(errors)) from None
        raise
    finally:
        for directory in reversed(created):
            try:
                directory.rmdir()
            except OSError:
                pass
        lock_file.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview only (default)")
    mode.add_argument("--apply", action="store_true", help="Move local files after review")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="VORQA root directory",
    )
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    try:
        moves, missing = plan(root)
        for entry in moves:
            print(f"PLAN {entry.source.relative_to(root)} -> {entry.destination.relative_to(root)}")
        for name in missing:
            print(f"NOT PRESENT {name}")
        if args.apply and moves:
            apply(root, moves)
            print("Local migration complete; nothing was staged or uploaded.")
        elif moves:
            print("Dry run only. Review paths before using --apply.")
        else:
            print("No remaining known sources require moving.")
    except (MigrationError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
