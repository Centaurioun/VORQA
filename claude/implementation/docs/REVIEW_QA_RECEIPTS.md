# Review and blind-QA evidence receipts (AVRL v2, Phase 1 slice 2)

This format increases **local evidence integrity**. It does not prove the
reviewer is an independent person, validate human identities, prevent a
same-account adversary from modifying all files, or replace signed CI review.

## Review PASS

Run `python3 scripts/avrl.py verify <slug>` on a **clean committed feature
branch**. Read `.avrl/state/<slug>.json` and obtain its `round`,
`eval_digest` and freshly generated `verification_nonce`. After independent
inspection, write `.avrl/review/<slug>/report.json`:

```json
{
  "schema_version": 1,
  "feature": "example-signup",
  "commit": "<the current 40-character git SHA>",
  "eval_digest": "<current signed contract digest>",
  "round": 1,
  "verification_nonce": "<32 lowercase hexadecimal characters from the latest verify>",
  "verdict": "pass",
  "reviewer": "<reviewer's claimed identifier; not authenticated>",
  "summary": "Specific surfaces and edge cases checked",
  "reviewed_files": ["example_app/index.html"],
  "findings": []
}
```

Run:

```sh
python3 scripts/avrl.py review example-signup --result pass \
  --evidence .avrl/review/example-signup/report.json
```

The controller checks the report structure, feature, exact SHA, approved
contract, round, fresh nonce and whether findings is an empty list. It records
a checksum. Changing the report after recording makes `complete` fail.
A failing review still uses `--result fail --finding-class ... --fingerprint ...`.

## Blind QA PASS

Run 

```sh
python3 scripts/blind_browser.py reset
python3 scripts/blind_browser.py inspect
python3 scripts/blind_browser.py fill-label 'Email address' 'qa@example.test'
python3 scripts/blind_browser.py click-role button 'Create account'
```

These example actions depend on an actual seeded loopback server and valid
application state; they are not claims of successful execution. At least three
browser events including an interaction are required. Each event now records
feature, exact SHA, eval digest, review round and the **same verification
nonce**. The controller checks *every* event's screenshot SHA-256 and path;
`last.png` is permitted only if its hash matches the final event screenshot.

```sh
python3 scripts/avrl.py blind example-signup --result pass \
  --evidence .avrl/blind/event-2.png
```

Choose the actual last event number from the session output. Any new
verification run invalidates old receipts (including a same-commit rerun).

## Limitations and external gate

A local program with access to the same user account may forge local files,
reviewer strings, event records or signing material. A PASS here is evidence
**consistency**, not **independent reviewer identity** or true end-user QA
coverage. High-risk release requires a separately authenticated, protected CI
approval/review workflow and a sandboxed browser outside the local trust
boundary. These controls are a later work package.
