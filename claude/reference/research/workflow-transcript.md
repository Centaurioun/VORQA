# Mastering AI Agent Code Reviews: The Claude Code Workflow

There is a huge problem with using AI agents: whenever you give them a task, they write a lot of code and immediately call the task "done." However, when you actually test what they built, you often find they have missed several key requirements. 

That is why the most important part of working with AI is verifying whether the agents actually did what they claimed. While there are many ways to handle this, **Anthropic’s Claude Code team** recently shared their internal approach. With their setup:
* They ship **more than twice as many changes** as before.
* The share of changes they have to undo or roll back **dropped by over 40%**.

They shared the core principles behind their system, and we have turned that system into a practical workflow you can follow to get the same quality of output. 

> **Welcome to AI Labs!** If this is your first time here, we are a software company, and in this guide, we will walk through each step of Anthropic's process, explain why it matters, and show you the exact prompts and skills we used so you can build this system for yourself.

---

## The Growing Problem of Agent Output

As AI models get better, reviewing what your agent builds matters more than ever. Models have gotten so capable that you can hand them a massive list of features and let them work autonomously for hours. When you come back, every feature is built without you watching a single line of code being written.

The Claude Code team sees this speed as a bottleneck: **more features built faster means exponentially more code to review.** 

* Across Anthropic, the number of daily changes to review skyrocketed from **~2,500 to over 30,000 in just four months**.
* Even though agents are capable, human verification is still required. With that much volume, the odds of a critical mistake slipping through increase dramatically.

If a bug reaches your real users without a check, it becomes a much costlier problem. According to the team, instead of saving time, skipping thorough reviews causes you to spend **twice as much time** later—first diagnosing the broken changes and then fixing the live bugs. Rushing checks simply pushes the time cost into the future, where fixes are much more expensive.

### Shifting the Review Mindset
Since review is a step you cannot skip, the real question is: *how do you scale it?* 

First, the team changed the core question they ask during a review:
* **Old Question:** *"Did someone read the code?"*
* **New Question:** *"What could go wrong with this change, and how do we catch it?"*

Second, they changed **when** the checks run. Instead of waiting until the end, checks happen *while* Claude is building. By the time a human looks at a change, it has already been tested and fixed at least once, allowing you to focus your energy only on the parts most likely to break.

*(If you find this breakdown helpful, please consider subscribing to the channel and hitting the hype button—this small gesture of support goes a long way for us!)*

---

## Step 1: Deep Checks & The `write-eval` Skill

While Claude runs small checks as it builds, you need deeper evaluations to ensure the app holds up when real people use it in unexpected ways. Before a change goes anywhere, the team asks Claude to run a test that **proves** it works and shows the result—such as automated app tests or comparing a live screenshot against a design.

**Boris Cherny**, the creator of Claude Code, notes that the best way to get Claude to perform well is to give it a way to verify its own work through **evals** (fixed, strict tests that tell you whether the work is truly done).

### How We Built the `write-eval` Skill
In our demo app, we organized our project with a `specs/` folder containing sub-folders for each feature. Inside each feature folder, an `rd.md` (Requirements Document) file lists what needs to be built.

You can prompt Claude to create a skill that turns each feature into an `eval.md` file:
1. **Create Mockups First:** If a feature has a UI design, Claude first builds it as a simple standalone web page (a mockup) rather than building straight into the app. This saves tokens and gives us a visual benchmark.
2. **Generate `eval.md`:** Claude writes the exact testing methods it will use to check its work against the requirements and the mockup.
3. **Human Approval Gate:** Claude must get the `eval.md` and mockups (including mobile layouts and alternate screen states) reviewed by you *before* writing any application code.
4. **Enforce with Hooks:** Claude creates a hook in the `.claude` folder that blocks the agent from marking any task as "done" until all evals pass.

Once you approve the `eval.md` and mockups, the feature status moves from `draft` to `reviewed` and is ready for building.

*(Note: This skill, along with all others shown here, is available in our **AI Labs Pro** community—check the link in the description to support the channel!)*

---

## Step 2: Independent Code Review (`review.md`)

Even after Claude builds a feature based on your evals, the agent that reviews the work **should not be the same agent that built it**. A builder agent has context bias—it made every decision during coding and will naturally agree with itself.

To solve this, the Claude Code team uses a **separate reviewer agent** to inspect every change before a human sees it. While the full automated agent is currently exclusive to Team and Enterprise plans, a lighter version is built into Claude Code via the `/review` (code review) command.

### Setting Up `review.md`
To tell the reviewer what matters in your specific app, Anthropic recommends writing your rules in a `review.md` file and linking it inside your main `CLAUDE.md` file so it loads automatically every session. 

Your `review.md` should define:
* What counts as a critical failure vs. a minor issue.
* What the reviewer should ignore.
* How the review report should be formatted.
* Specific testing protocols for your app.

---

## Step 3: The Multi-Agent Review Loop

With your evaluation criteria (`eval.md`) and review standards (`review.md`) in place, the next step is creating an automated **Review Loop Skill** using sub-agents with fresh context windows.

When you trigger the review loop for a feature, the main agent acts as an **Orchestrator**, tracking progress in a `state.md` file and managing three specialized sub-agents:

1. **The Builder Agent:** Builds the feature based on the requirements document and mockup. (A hook prevents it from finishing early).
2. **The Verifier Agent:** Runs the app against the `eval.md` checklist, marking each item as passed or failed.
3. **The Reviewer Agent:** Inspects the code using the rules in `review.md` to catch anything the evals missed.

The orchestrator loops through building, verifying, and reviewing in rounds until all evals pass and no new review issues are found. If it hits an ambiguous product decision, it pauses and presents a progress report for your input.

### Continuous Learning (Self-Updating Rules)
Because Claude doesn't retain memories across sessions, it might repeat the same coding mistakes on future features. To prevent this, we added a **"Rules Learned Over Time"** section at the bottom of `review.md`.
* Whenever a bug slips through or a reviewer repeatedly flags a false positive, the review loop matches the pattern across rounds.
* At the end of the run, it suggests a concise, one-line rule to add to `review.md` (pending your approval), making every future review smarter.

---

## Step 4: Risk Classification & Loop Guardrails

Running a deep, multi-agent review loop on every tiny change wastes time and tokens. The Claude Code team uses a **Classifier Agent** to sort changes by risk, asking one simple question: ***What happens to a customer if this feature breaks?***

* **Low Risk:** Visual glitches or minor UI issues.
* **Medium Risk:** A feature stops working, but no data or money is lost (can be fixed later).
* **High Risk:** Customers lose money, get locked out, or see another user's private data (irreversible damage).

By turning this classifier into a skill, you can rate a feature before building it and pass that rating to your `write-eval` skill—ensuring high-risk features get strict verification while low-risk tweaks move fast.

### Preventing Infinite Token Loops
Without boundaries, Builder and Reviewer agents can argue endlessly. Anthropic once had a loop run **over 50 times** until a human manually stopped it! When they analyzed the logs, **59% of the reported issues had been there since Round 1**—the reviewer was just re-reporting old problems and burning tokens.

To fix this without needing unlimited tokens, the team introduced **three strict rules**:
1. **The 3-Round Rethink Rule:** After 3 failed rounds (we use 5 rounds in our browser-heavy setup, or stop after 2 identical failures), the reviewer stops listing bugs and tells the builder to fundamentally rethink its approach.
2. **Delta-Only Reviews:** After Round 1, the reviewer *only* inspects code changed by the most recent fix, preventing it from re-scanning the whole feature.
3. **Categorized Fixes:** When the reviewer flags a bug, it identifies the *category* of the problem, forcing the builder to fix that pattern everywhere in the codebase at once, not just on a single line.

---

## Step 5: Post-Build Safety Nets (Blind Testing & Fast Rollbacks)

Even when every eval passes, subtle usability issues can slip through. The Claude Code team relies on two final safety nets: **finding mistakes like a real user** and **undoing broken changes in minutes**.

### 1. The "First-Time User" Skill
Because you built the feature, you have blind spots regarding how it works. To simulate a fresh perspective, you can create a **First-Time User Skill**:
* It spawns a sub-agent to navigate your live app in a browser using a temporary test database.
* **Strict Code Block:** A hook blocks this agent from reading your source code or running terminal inspection commands.
* Knowing nothing about how the app was built, the agent explores the feature like a brand-new customer, reporting every confusing workflow or UI dead-end it encounters.

### 2. Git Branching & The "Fix-a-Bug" Skill
Finding mistakes is half the battle; undoing them fast is the other. By instructing Claude in `CLAUDE.md` to use **Git**—creating a dedicated branch for every feature and committing every working state—you can roll back broken releases in seconds.

Furthermore, you can create a **Fix-a-Bug Skill**:
* When a bug occurs, you describe the symptom to the skill.
* The agent reproduces the bug step-by-step, verifies its hypothesis about the root cause, checks the Git history to see which commit introduced the regression, and applies the fix (or rolls it back).

---

*That brings us to the end of this guide! If you would like to support AI Labs and help us keep making deep-dive workflows like this, feel free to use the Super Thanks button below. Thank you for reading, and we will see you in the next one!*