---
name: write-eval
description: Generate falsifiable evals and standalone approved UI mockups before feature implementation
argument-hint: <feature-slug>
disable-model-invocation: true
---
# Evaluation first

Read `specs/<slug>/prd.md`, risk classification, user journeys and abuse cases. Do not change application code during this skill.

1. Identify each observable requirement, boundary case, accessibility condition and failure state. Convert them into stable criterion IDs with unambiguous expected output and a concrete test oracle. For high-risk features include adversarial actor isolation, rollback and concurrency.
2. Create `specs/<slug>/eval.md` as a readable contract using `eval-template.md`; create `eval.json` with matching identifiers and deterministic executable steps. Criteria types are `command` with an argv array and timeout, `browser` or `visual` pointing at a scenario JSON. No free-form shell expressions; never use test steps that do production writes.
3. For UI features create standalone `mockups/desktop.html`, `mobile.html`, `edge.html` with complete HTML and CSS, not screenshots cut from the app. Cover responsive breakpoints, loading/empty/error/retry states, focus and semantics. Capture stable PNG baselines with the bundled Playwright capture script after dependency validation.
4. Produce `decision-log.md` with design alternatives, risks, rejected options, accessibility concerns, consequences, and what remains unverified. Add each criterion's observable falsification condition. Avoid anything that can only be judged by the builder's opinion.
5. Mark draft as `in-review` using the controller on an appropriately named clean feature branch. `python3 scripts/avrl.py init <slug> --risk <tier>` fingerprints PRD/eval/mockups. Commit the immutable contract **before** initialization. Then halt and explicitly request operator review and a real terminal approval. Never call `approve` as an agent or pretend approval.

Only after operator approval can `/review-loop <slug>` begin app changes. Editing PRD, eval or mockup files invalidates approval until another explicit operator review.
