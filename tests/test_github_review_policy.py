"""GitHub PR review policy tests: no live API calls."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import github_review_policy as policy

SHA = "a" * 40


def review(login, state="APPROVED", commit=SHA, rid=1, user_type="User"):
    return {"id": rid, "state": state, "commit_id": commit,
            "user": {"login": login, "type": user_type}}


def context(files=None, reviews=None, permissions=None, author="developer"):
    return {
        "number": 12, "base": {"ref": "main"}, "state": "open",
        "draft": False, "head": {"sha": SHA},
        "user": {"login": author},
    }, (files if files is not None else [{"filename": "README.md"}]), (reviews if reviews is not None else []), (permissions if permissions is not None else {})


class ReviewPolicyTests(unittest.TestCase):
    def check(self, **kwargs):
        return policy.evaluate(*context(**kwargs), expected_head=SHA)

    def test_no_review_fails_closed(self):
        outcome = self.check()
        self.assertFalse(outcome["pass"])
        self.assertEqual(outcome["required"], 1)

    def test_author_approval_never_counts(self):
        o = self.check(reviews=[review("developer")], permissions={"developer": "admin"})
        self.assertFalse(o["pass"])

    def test_one_authorized_approver_for_standard_change(self):
        o = self.check(reviews=[review("Alice")], permissions={"alice": "write"})
        self.assertTrue(o["pass"])
        self.assertEqual(o["approved_by"], ["alice"])

    def test_high_risk_requires_two_distinct_users(self):
        files = [{"filename": "claude/implementation/scripts/avrl.py"}]
        one = self.check(files=files, reviews=[review("Alice")], permissions={"alice": "write"})
        self.assertFalse(one["pass"])
        self.assertEqual(one["required"], 2)
        two = self.check(files=files, reviews=[review("Alice", rid=1), review("Bob", rid=2)],
                         permissions={"alice": "write", "bob": "maintain"})
        self.assertTrue(two["pass"])

    def test_untrusted_or_bot_reviews_rejected(self):
        o = self.check(reviews=[review("Random", rid=1), review("automation[bot]", rid=2)],
                       permissions={"random": "read", "automation[bot]": "admin"})
        self.assertFalse(o["pass"])

    def test_old_head_approval_rejected(self):
        o = self.check(reviews=[review("Alice", commit="b" * 40)], permissions={"alice": "admin"})
        self.assertFalse(o["pass"])

    def test_latest_review_wins(self):
        # A new COMMENTED event must not erase the last decision.
        o = self.check(reviews=[review("Alice", rid=1), review("Alice", "COMMENTED", rid=2)],
                       permissions={"alice": "write"})
        self.assertTrue(o["pass"])
        # Later change request blocks an earlier approval; after a new approval, it clears.
        o = self.check(reviews=[review("Alice", rid=1), review("Alice", "CHANGES_REQUESTED", rid=2)],
                       permissions={"alice": "write"})
        self.assertFalse(o["pass"])
        o = self.check(reviews=[review("Alice", "CHANGES_REQUESTED", rid=1), review("Alice", rid=2)],
                       permissions={"alice": "write"})
        self.assertTrue(o["pass"])

    def test_stale_change_request_blocks_even_if_other_approved(self):
        o = self.check(reviews=[review("Alice", commit="b"*40, state="CHANGES_REQUESTED", rid=1), review("Bob", rid=2)],
                       permissions={"alice": "write", "bob": "write"})
        self.assertFalse(o["pass"])

    def test_dismissed_approval_not_counted(self):
        o = self.check(reviews=[review("Alice", "DISMISSED")], permissions={"alice": "admin"})
        self.assertFalse(o["pass"])

    def test_wrong_head_or_non_main_draft_rejected(self):
        pr, files, reviews, perms = context(reviews=[review("Alice")], permissions={"alice": "write"})
        self.assertFalse(policy.evaluate(pr, files, reviews, perms, expected_head="b"*40)["pass"])
        pr["base"]["ref"] = "experimental"
        self.assertFalse(policy.evaluate(pr, files, reviews, perms, expected_head=SHA)["pass"])
        pr["base"]["ref"] = "main"
        pr["draft"] = True
        self.assertFalse(policy.evaluate(pr, files, reviews, perms, expected_head=SHA)["pass"])

    def test_cannot_downgrade_unknown_privileged_file(self):
        for p in [".github/workflows/new.yml", "scripts/github_review_policy.py", "AGENTS.md",
                  "claude/implementation/.claude/hooks/new.py", "SECURITY.md"]:
            with self.subTest(path=p):
                self.assertEqual(policy.risk_tier([{"filename": p}]), "HIGH")

    def test_missing_or_malformed_api_data_fails_closed(self):
        for reviews in [None, [{"id": 1, "state": "APPROVED", "commit_id": SHA}]]:
            with self.subTest(reviews=reviews):
                pr, files, _, perms = context(reviews=[], permissions={"alice": "admin"})
                self.assertFalse(policy.evaluate(pr, files, reviews, perms, expected_head=SHA)["pass"])

    def test_malformed_permission_and_commit_fail_closed(self):
        o = self.check(reviews=[review("Alice", commit=None)], permissions={"alice": None})
        self.assertFalse(o["pass"])
        o = self.check(reviews=[review("Alice")], permissions={"alice": None})
        self.assertFalse(o["pass"])

    def test_collect_uses_pr_api_not_pr_supplied_urls(self):
        from unittest.mock import patch
        paths = []
        def fake_fetch(path, token):
            paths.append(path)
            if path.endswith("/permission"):
                return {"permission": "write"}
            if "/files?" in path:
                return [{"filename": "README.md", "evil_link": "https://attacker.example"}]
            if "/reviews?" in path:
                return [review("Alice")]
            return context()[0]
        with patch.object(policy, "_get_json", side_effect=fake_fetch):
            pr, files, reviews, perms = policy.collect("Centaurioun", "VORQA", 12, "fake-token")
        self.assertEqual(perms, {"alice": "write"})
        self.assertTrue(all(path.startswith("/repos/Centaurioun/VORQA/") or
                            path == "/repos/Centaurioun/VORQA/pulls/12" for path in paths))

    def test_api_url_only_fixed_github_host(self):
        with self.assertRaises(ValueError):
            policy.github_path("evil.example", "VORQA", 1)
        self.assertEqual(policy.github_path("Centaurioun", "VORQA", 1),
                         "/repos/Centaurioun/VORQA/pulls/1")


if __name__ == "__main__":
    unittest.main()
