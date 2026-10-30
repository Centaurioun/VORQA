#!/usr/bin/env python3
"""Read-only GitHub PR review audit; repository protection is required separately.

No PR code is executed. A GitHub account is NOT proof of a distinct human.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

_SHA = re.compile(r"[a-fA-F0-9]{40}\Z")
_NAME = re.compile(r"[A-Za-z0-9_.-]+\Z")
_GH_LOGIN = re.compile(r"[A-Za-z0-9-]{1,39}\Z")
_HIGH_FILES = {
    "AGENTS.md", "CLAUDE.md", "SECURITY.md", ".github/CODEOWNERS",
    "docs/REPOSITORY_POLICY.md",
}
_HIGH_PREFIXES = (
    ".github/", "scripts/github_review_policy.py",
    "claude/implementation/scripts/",
    "claude/implementation/.claude/",
)


def github_path(owner: str, repository: str, number: int) -> str:
    if not _GH_LOGIN.fullmatch(owner) or not _NAME.fullmatch(repository) or not isinstance(number, int) or number <= 0:
        raise ValueError("Invalid GitHub repository or PR number")
    return f"/repos/{owner}/{repository}/pulls/{number}"


def risk_tier(files: list[dict]) -> str:
    if not isinstance(files, list) or not files:
        raise ValueError("PR changed file listing missing")
    for f in files:
        if not isinstance(f, dict) or not isinstance(f.get("filename"), str):
            raise ValueError("Malformed changed file listing")
        path = f["filename"]
        previous = f.get("previous_filename", "")
        if not path or (previous and not isinstance(previous, str)):
            raise ValueError("Invalid changed file name")
        for candidate in (path, previous):
            if candidate in _HIGH_FILES or any(candidate.startswith(prefix) for prefix in _HIGH_PREFIXES):
                return "HIGH"
    return "STANDARD"


def evaluate(pr: dict, files: list[dict], reviews: list[dict], permissions: dict[str, str], *, expected_head: str) -> dict:
    """Compute a deterministic, conservative PR review decision from GitHub data."""
    if not isinstance(pr, dict) or not isinstance(reviews, list) or not isinstance(permissions, dict):
        return {"pass": False, "reasons": ["Missing or malformed GitHub PR evidence"], "required": 2, "approved_by": []}
    try:
        tier = risk_tier(files)
        head = pr["head"]["sha"]
        author = pr["user"]["login"].casefold()
        base = pr["base"]["ref"]
        if not isinstance(head, str) or not _SHA.fullmatch(head) or not author:
            raise ValueError("Missing authenticated PR identity or head")
        if not isinstance(expected_head, str) or not _SHA.fullmatch(expected_head):
            raise ValueError("Expected SHA must be exact")
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        return {"pass": False, "reasons": ["Invalid GitHub PR payload: " + str(exc)], "required": 2, "approved_by": []}
    required = 2 if tier == "HIGH" else 1
    reasons = []
    if pr.get("state") != "open" or pr.get("draft") is not False or base != "main":
        reasons.append("PR must be open, non-draft, and target main")
    if head.lower() != expected_head.lower():
        reasons.append("PR head SHA does not match expected revision")

    latest = {}
    for item in reviews:
        if not isinstance(item, dict) or not isinstance(item.get("id"), int) or not isinstance(item.get("state"), str):
            reasons.append("Malformed review in GitHub response")
            continue
        user = item.get("user")
        if not isinstance(user, dict) or not isinstance(user.get("login"), str) or not user["login"]:
            reasons.append("Review without GitHub login")
            continue
        login = user["login"].casefold()
        if user.get("type") == "Bot" or login.endswith("[bot]") or not _GH_LOGIN.fullmatch(login):
            continue
        state = item["state"].upper()
        if state not in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            continue  # COMMENTED and PENDING do not change review decision
        if login not in latest or item["id"] > latest[login]["id"]:
            latest[login] = item

    authorized = []
    blockers = []
    for login, item in latest.items():
        state = item["state"].upper()
        if state == "CHANGES_REQUESTED":
            blockers.append(login)
        elif (state == "APPROVED" and login != author and
              isinstance(item.get("commit_id"), str) and
              item["commit_id"].lower() == head.lower() and
              isinstance(permissions.get(login), str) and permissions[login].lower() in ("write", "maintain", "admin")):
            authorized.append(login)
    authorized.sort()
    if blockers:
        reasons.append("Unresolved changes-requested reviews: " + ", ".join(sorted(blockers)))
    if len(authorized) < required:
        reasons.append(f"Insufficient fresh authorized approvals: {len(authorized)} of {required}")
    return {"pass": not reasons, "risk": tier, "required": required,
            "approved_by": authorized, "head_sha": head.lower(), "reasons": reasons}


def _get_json(path: str, token: str) -> object:
    # This function cannot fetch caller-provided domains or PR-controlled links.
    if not path.startswith("/repos/"):
        raise ValueError("Non-repository endpoint forbidden")
    request = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json", "Authorization": "Bearer " + token,
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "VORQA-review-policy/1"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def _pages(path: str, token: str) -> list[dict]:
    result = []
    for page in range(1, 31):
        data = _get_json(path + ("&" if "?" in path else "?") + f"per_page=100&page={page}", token)
        if not isinstance(data, list):
            raise ValueError("Unexpected GitHub pagination response")
        result.extend(data)
        if len(data) < 100:
            return result
    raise ValueError("GitHub pagination cap reached; refusing partial evidence")


def collect(owner: str, repo: str, number: int, token: str) -> tuple:
    base = github_path(owner, repo, number)
    pr = _get_json(base, token)
    files = _pages(base + "/files", token)
    reviews = _pages(base + "/reviews", token)
    permissions = {}
    if not isinstance(reviews, list):
        raise ValueError("Expected GitHub review array")
    for review in reviews:
        user = review.get("user") if isinstance(review, dict) else None
        login = user.get("login", "") if isinstance(user, dict) else ""
        if not isinstance(login, str) or not _GH_LOGIN.fullmatch(login):
            continue
        key = login.casefold()
        if key in permissions:
            continue
        data = _get_json(
            f"/repos/{owner}/{repo}/collaborators/{urllib.parse.quote(login, safe='')}/permission", token)
        if not isinstance(data, dict) or data.get("permission") not in ("none", "read", "triage", "write", "maintain", "admin"):
            raise ValueError("Cannot verify collaborator's current permission")
        permissions[key] = data["permission"]
    return pr, files, reviews, permissions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="owner/repository")
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--head", required=True, help="Exact expected PR head SHA")
    parser.add_argument("--report-only", action="store_true", help="Diagnostic mode, does not enforce")
    args = parser.parse_args(argv)
    try:
        owner, repo = args.repository.split("/")
        github_path(owner, repo, args.pr)
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN is required for authenticated GitHub evidence")
        pr, files, reviews, permissions = collect(owner, repo, args.pr, token)
        decision = evaluate(pr, files, reviews, permissions, expected_head=args.head)
    except (ValueError, TypeError, AttributeError, KeyError, urllib.error.URLError, TimeoutError, OSError) as exc:
        decision = {"pass": False, "reasons": ["GitHub evidence unavailable or invalid: " + str(exc)]}
    print(json.dumps({"policy": "vorqa-review-v1", "mode": "report-only" if args.report_only else "enforce",
                      **decision}, indent=2, sort_keys=True))
    return 0 if args.report_only or decision["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
