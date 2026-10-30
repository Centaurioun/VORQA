"""Phase 0 local-only source organizer regression tests."""

from __future__ import annotations

import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from scripts.organize_claude_sources import main, plan


class OrganizerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "claude").mkdir()

    def run_cli(self, *args: str) -> int:
        with contextlib.redirect_stdout(io.StringIO()):
            return main(["--root", str(self.root), *args])

    def test_preview_is_read_only(self) -> None:
        file = self.root / "claude/README.md"
        file.write_bytes(b"hello\x00")
        self.assertEqual(0, self.run_cli("--dry-run"))
        self.assertEqual(b"hello\x00", file.read_bytes())
        self.assertFalse((self.root / "claude/reference").exists())

    def test_apply_preserves_bytes_and_is_idempotent(self) -> None:
        file = self.root / "claude/README.md"
        file.write_bytes(b"hello\x00")
        self.assertEqual(0, self.run_cli("--apply"))
        self.assertFalse(file.exists())
        target = self.root / "claude/reference/exports/avrl-v2-original-readme.md"
        self.assertEqual(b"hello\x00", target.read_bytes())
        self.assertEqual(0, self.run_cli("--apply"))

    def test_existing_target_is_never_overwritten(self) -> None:
        (self.root / "claude/README.md").write_text("keep original")
        dest = self.root / "claude/reference/exports/avrl-v2-original-readme.md"
        dest.parent.mkdir(parents=True)
        dest.write_text("existing target")
        self.assertEqual(2, self.run_cli("--apply"))
        self.assertEqual("keep original", (self.root / "claude/README.md").read_text())
        self.assertEqual("existing target", dest.read_text())

    def test_source_symlink_rejected(self) -> None:
        (self.root / "claude/README.md").symlink_to(self.root / "outside.txt")
        self.assertEqual(2, self.run_cli("--apply"))

    def test_nested_symlink_rejected(self) -> None:
        folder = self.root / "claude/claude-verification-loop"
        folder.mkdir()
        (folder / "link").symlink_to(self.root / "outside.txt")
        self.assertEqual(2, self.run_cli("--apply"))

    def test_literal_backslash_alias_recognized(self) -> None:
        (self.root / "claude/claude_code_review_workflow\\.md").write_text("workflow")
        moves, _ = plan(self.root)
        self.assertEqual(1, len(moves))
        self.assertEqual("workflow-transcript.md", moves[0].destination.name)

    def test_two_transcript_aliases_refused(self) -> None:
        for name in ("claude_code_review_workflow.md", "claude_code_review_workflow\\.md"):
            (self.root / "claude" / name).write_text("workflow")
        self.assertEqual(2, self.run_cli("--apply"))


if __name__ == "__main__":
    unittest.main()
