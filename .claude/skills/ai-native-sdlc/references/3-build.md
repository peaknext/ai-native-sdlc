# Stage 3: Build - plan first, then implement

Contents:
1. Plan before the first edit (`plan.md`)
2. Implementing, and when to run without per-edit approval
3. `CLAUDE.md`: what a new teammate needs
4. Skills: institutional knowledge that gets applied
5. Hooks: build-time guardrails
6. Parallel sessions and subagents
7. Brand-new projects

## 1. Plan before the first edit

**Goal:** the design review happens before code exists. In the traditional flow the engineer reads the design and starts typing; which files, which tests and which trade-offs stay in their head, and reviewers only ever see the finished diff. A written plan makes those decisions reviewable while they are still cheap to change.

**Needs first:** `intent.md` / `spec.md` if they exist. `CLAUDE.md` helps.

**Output:** `plan.md`, committed, then the diff and its tests.

Steps:

1. **Start read-only.** Use plan mode when the tool has it (in Claude Code: `claude --permission-mode plan`, or set `permissions.defaultMode` to `plan`). Otherwise behave the same way: read and search the code, change nothing until the plan is accepted.
2. **Give yourself the inputs:** the intent and spec. Ask for whatever is missing instead of guessing at requirements.
3. **Write the plan** (`assets/templates/change/plan.md`): the files that change, the order of work, and the tests that will prove it. Tie steps back to the spec's requirement numbers.
4. **Interrogate it.** Answer in writing: what could this break? Which step is riskiest? What options were rejected, and why? A plan that lists no risks has not been examined.
5. **Iterate until someone who never saw the conversation could implement from the plan alone.** That is the bar.
6. **Commit the approved plan as `plan.md`.** Review will later check the diff against it.
7. **When implementation departs from the plan, update `plan.md` in the same commit** (a "Deviations" section works well). A hook can enforce that the two stay in sync.

Who approves: the engineer for routine changes; a tech lead or architect for higher-risk ones. For a non-technical owner, summarise the plan as "what will change, what could go wrong, how we will know it works".

A plan for a small bug fix can be six lines. A plan for a feature is usually under a page. If it needs more, the change probably wants splitting.

What to measure:
- **Leading:** share of changes that merge from the first implementation pass; time from plan approval to merged PR.
- **Lagging:** rework cycles per change; how often the merged diff still matches `plan.md`.

## 2. Implementing

Once the plan is accepted, implement it, usually in one pass, running the checks from `4-test.md` as you go.

**Running without per-edit approval (auto-accept / auto mode).** Watching every edit is the wrong place for human attention once guardrails exist. It becomes the sensible default for routine work when all of these are true:

- the spec is tight and the blast radius is small;
- the code is covered by tests the agent can run itself;
- `CLAUDE.md` is tuned, policy skills exist, and blocking hooks protect what must not be touched.

Review then shifts from watching edits to reviewing artifacts after a longer autonomous stretch: the plan, the diff, the test output. Without those guardrails, stay in the mode that asks.

## 3. `CLAUDE.md`

**Goal:** move the knowledge a new joiner needs (conventions, commands, architecture, common mistakes) out of heads and wikis into a file that is read at the start of every session.

Steps:

1. Generate a starting point (`/init` in Claude Code) or copy `assets/templates/repo/CLAUDE.md`.
2. **Cut it to day-one essentials:** build, test and lint commands (with what healthy output looks like); key conventions; the shape of the architecture; things Claude keeps getting wrong.
3. Commit it at the repo root so changes are reviewed like code. Code owners approve them.
4. **Working rule:** when the same mistake happens twice, the correction goes into `CLAUDE.md`.
5. **Keep it under a page.** It is read in full every session; stale or bloated content costs attention on every task.

Verify each command by running it before writing it down. Wrong commands in this file are trusted and repeated.

What belongs elsewhere: a policy that must be applied consistently across repos is a skill; a rule that must never be broken needs a hook; a one-off instruction belongs in the prompt.

What to measure:
- **Leading:** how often a mistake repeats that `CLAUDE.md` should have prevented.
- **Lagging:** time to first merged PR for a new team member.

## 4. Skills as institutional knowledge

A skill makes a piece of organisational knowledge operational: explicit, versioned, applied automatically when relevant, and updated in one place.

**Rule of thumb:** write a skill for institutional knowledge that must be applied consistently (a security standard, an API convention, a brand rule). Do not write one for something that belongs in `CLAUDE.md` or in a prompt.

Steps:

1. Pick one piece of knowledge that is currently enforced inconsistently, with a **named owner** and a **written source of truth**.
2. Write it as a folder containing `SKILL.md`: frontmatter that says when it applies, a body that says what to do. Draft it from the owner's document. Start from `assets/templates/policy-skill.md`.
3. Put it in `.claude/skills/<name>/` in the repo, or distribute it organisation-wide as a plugin.
4. **Test that it triggers:** ask for the task several different ways and confirm the skill is picked up each time.
5. When the policy changes, update the skill and have the policy owner sign off the change, like a code review.
6. People get the new version in their next session.

**A skill is an advisory control.** It makes compliance likely; it does not force it. Any policy that must hold without exception needs a deterministic backstop: a blocking hook, or a re-check at PR time. Say this plainly when someone asks a skill to "guarantee" something.

What to measure:
- **Leading:** time from a policy being approved to the updated skill being merged.
- **Lagging:** PR review findings that cite the policy. This should trend to zero; if it does not, the skill is not triggering or its text has drifted from the policy.

## 5. Hooks as build-time guardrails

A hook is a script the tool runs automatically at a fixed point (before a file edit, after a shell command, ...). It is the deterministic layer behind the advisory ones. Most agent actions during build are file edits and shell commands, so this is where hooks fire most.

Useful build-time hooks:

- **Block edits to protected paths:** generated code, frozen packages, vendored files.
- **Run the formatter and linter after each edit,** so drift never accumulates.
- **Keep credentials out of the diff.**
- **Back any skill whose policy must hold without exception.**

Design rules:

- Hooks run on every matching action, so keep them **fast and scoped to the changed file**. Heavier checks (the full test suite) belong at commit or PR time.
- **A block must explain itself:** the reason and the route to approval, printed where the agent and the human will see it.
- **Human-approval hooks belong at the Deploy gates,** not in the build loop. An approval prompt during build puts a person on the critical path of every parallel session.

Templates (installed by `sdlc.py init --with hooks`):

- `protect_paths.py`: blocks or asks on the paths listed in `.claude/protected-paths.txt`, and locks tests during a fix. Edits are judged exactly by path; shell commands that name a listed path and change files (`rm`, `sed -i`, a redirect, ...) are caught by pattern; git worktrees are covered.
- `production_gate.py`: see `5-deploy.md`.
- `format_on_edit.py`: does nothing until you list the project's formatter.
- `check_guardrails.py` with `.claude/guardrail-checks.txt`: one command that shows what the hooks decide for each listed action. Add a line per rule and run it.
- `settings.json`: wires them up, failing closed.

These templates are tested. Configure them (the two lists, and the three settings at the top of `production_gate.py`) instead of rewriting them, then prove the result with `python3 .claude/hooks/check_guardrails.py`.

When a rule is stated as "never", layer it: the hook, plus a `permissions.deny` rule in `.claude/settings.json` (for example `Edit(/src/generated/**)`), which holds even if the hook cannot run, plus where possible a check outside the agent altogether (CI that fails on a hand-edited generated file; production credentials that are not on developer machines). Say which layers exist and which do not.

Mechanics of the hook format are in `5-deploy.md`.

## 6. Parallel sessions and subagents

Two different things:

- A **parallel session** is another full agent instance working on a separate task in its own git worktree (a second checkout of the same repo, so sessions cannot overwrite each other's files). Sessions know nothing about each other; the engineer is the only thing they share.
- A **subagent** runs inside one session with its own context window and its own tool limits, for a recurring job such as checking that the app actually runs.

**Needs first:** `CLAUDE.md` (every session reads it) and a feedback loop (`4-test.md`), because sessions that can verify themselves need far less supervision. Permission settings should pre-allow the commands the organisation considers safe, or every session stalls on prompts.

Steps:

1. **Split the work into tasks that touch different files,** using the plan to find independent pieces. Tasks that share files run one after another in a single session.
2. **Give each parallel task its own worktree,** for example `claude --worktree <name>` in separate terminals.
3. **Start with two or three sessions.** Add more only while review keeps up; unreviewed output is not progress.
4. **Turn repeated jobs into subagents**: markdown files in `.claude/agents/` with a name, a description of when to use it, and the tools it may use, committed for the whole team. Typical roles:
   - a **verifier** that starts the app, exercises the changed behaviour and its nearest neighbours, and reports what it saw without fixing anything;
   - a **code simplifier** that strips needless complexity once the main work is done;
   - a **researcher** that explores the codebase and reports back, keeping the main context clean.

   Templates are in `assets/templates/repo/dot-claude/agents/`.

Governance: hooks and permission settings come from the repo configuration, so they apply to every session; activity is attributed to the engineer who ran it.

What to measure:
- **Leading:** concurrent sessions per engineer while review quality holds; share of the day spent steering instead of waiting.
- **Lagging:** changes merged per engineer per week, read alongside the rework rate.

## 7. Brand-new projects

With no code yet, the first build step is to create the conditions everything else depends on:

1. Scaffold the project with the technology chosen in the spec.
2. Make **build, test and lint each run with one command** (a `Makefile` or package scripts), and add one real test so "green" means something.
3. Write `CLAUDE.md` with those commands and run `python scripts/sdlc.py init <repo>` for the rest of the layout.
4. Commit that as the first change, before feature work.

Then build the smallest slice of the spec that a user could actually try, verify it, and show it. For a non-technical owner, something they can click beats a long status report.
