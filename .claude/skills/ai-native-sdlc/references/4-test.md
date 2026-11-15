# Stage 4: Test - prove it before a human looks

Two ideas run through this stage:

1. **Every session checks its own work before a person sees it.**
2. **The configuration that steers the agent (CLAUDE.md, skills, hooks, prompts, model) is regression-tested like code.**

Testing here is not a gate at the end. It is woven through Build and repeated as many times as it takes.

## 1. Give yourself a feedback loop

In the traditional flow the signals arrive late: CI minutes later, a tester days later, production weeks later. If a person has to check all agent output, that person becomes the bottleneck. So the session runs the tests, the build or a screenshot itself and iterates until the check passes.

**Needs first:** nothing. Required infrastructure: a test suite and a build that each run locally with **one command**, and for UI work a way to see the result (a browser tool or screenshot utility).

Steps:

1. **Wrap multi-step checks in one target** such as `make test` or `npm test` that exits non-zero on failure. If the project lacks this, creating it is the first task.
2. **List each command in `CLAUDE.md`** with an example of what healthy output looks like, so "passed" is unambiguous.
3. **State targets that can be checked:** "all tests in `test_reminders.py` pass", "the screenshot matches the mock", "the endpoint returns 200 with the new field". Vague goals produce vague verification.
4. **For bug fixes, use the failing-test-first protocol** (below).
5. **For UI work, loop:** implement, take a screenshot, compare with the mock, adjust. Two or three rounds is typical.
6. **Make verification part of the definition of done** in `CLAUDE.md`: run build, test and lint before reporting completion, and show the output.
7. **Protect the loop:** a hook that blocks edits to test files during fix tasks, or a review rule that rejects any change to an existing test in a fix PR.

### The failing-test-first protocol for bugs

A test that existed before the fix, and that the agent was not allowed to rewrite, is the proof that the bug is gone.

1. **Reproduce the bug** and find the cause. Say what the cause is in one or two sentences.
2. **Write a test that fails because of the bug.** Run it and confirm it fails for the expected reason (not because of a typo or a missing import).
3. **Commit the failing test on its own.** That commit is the evidence of "before".
4. **Lock it.** With the hook template installed, add the test's path to `.claude/locked-tests.txt`. Without the hook, treat it as locked anyway.
5. **Fix the code until the test passes, without editing the test.** If the test turns out to be wrong, stop and tell the human; do not quietly change it.
6. **Run the whole suite,** not only the new test, to catch what the fix broke.
7. **Report with real output:** the failing run, the passing run, the full-suite run. Unlock the test afterwards.

If the project has no test setup at all, say so, add the smallest one that can run the new test, and note it as a deviation in the plan.

### What to put in `CLAUDE.md`

```markdown
## Verifying your work
- Build: `make build`   (must end with "Build succeeded")
- Test:  `make test`    (all green; never skip or delete a failing test)
- Lint:  `make lint`    (zero warnings)
Run all three before reporting completion and paste the output.
If a test fails, fix the code, not the test.
```

### A verifier in a fresh context

A verifier subagent is the packaged final check. Because it starts with a fresh context window, its verdict is not shaped by the assumptions that produced the code. It runs the app, exercises the changed behaviour and its nearest neighbours, compares what it saw with `plan.md`, and reports. It does not fix. Template: `assets/templates/repo/dot-claude/agents/verifier.md`.

### Evidence and measures

- **Evidence:** the literal toolchain output, build log or screenshot comparison, kept in the session transcript and attached to the PR check run. Because the mechanical evidence is attached, the code owner can spend their review on intent and risk.
- **Enforcement where required:** hooks for "verification before done" and "no test edits during fixes".
- **Leading metric:** first-pass CI success rate for agent-written changes.
- **Lagging metrics:** review time per PR (should fall); change failure rate from the incident tracker.

## 2. Continuous evals in CI

An eval is a recorded task with a known good outcome. A suite of them answers one question: *after this change to the agent's setup, does the agent still meet our standard?* It runs whenever the configuration changes (a new model, a rewritten prompt, an edited `CLAUDE.md`, skill or hook). It is the AI-native counterpart of stage-gate QA.

**Needs first:** `CLAUDE.md` and a working feedback loop. Infrastructure: CI that can run the agent non-interactively (`claude -p ...`) and an API key with a budget for eval runs.

Steps:

1. **Collect 20 to 50 real, recent tasks with their accepted outcomes.** Real tasks, not invented puzzles; the suite should look like the team's actual work.
2. **Write each as an eval:** the prompt plus acceptance checks (tests pass, lint clean, behaviour unchanged, policy followed). Checks are commands that exit zero or non-zero.
3. **Run the suite non-interactively in CI,** on a schedule and on any change to `CLAUDE.md`, skills or hooks.
4. **Gate configuration changes on the result.** A skill change that drops the pass rate gets looked at before it merges.
5. **Every production incident gets an eval,** written by the owning team and kept forever as a regression test.

Keep the suite alive: as models improve, easy cases stop telling good configurations from bad ones and should be replaced. Some teams run the suite offline on a fixed cadence instead of on every change; that is fine if configuration changes still wait for a run.

Templates (installed by `sdlc.py init --with evals`):

- `evals/cases/*.json`: one file per eval (`name`, `prompt`, `base_ref`, `allowed_tools`, `checks`).
- `evals/run_evals.py`: runs each case in a throwaway git worktree, applies the checks, prints the pass rate, and exits non-zero below `--threshold`.
- `.github/workflows/agent-evals.yml`: runs it on pull requests that touch the agent's configuration, and nightly.

Governance: the pass-rate threshold is a merge check; runs are logged so they can be compared over time; the team that owns the configuration approves changes to it.

What to measure:
- **Leading:** eval pass rate over time; time from an incident to its permanent eval.
- **Lagging:** regressions caught in CI versus regressions that reached production.

## Common mistakes

- Reporting "tests pass" without having run them, or showing a summary instead of the output.
- Making a failing test pass by weakening it, skipping it or deleting it.
- Running only the new test and missing what the change broke elsewhere.
- Writing the "failing" test after the fix, where it proves nothing.
- An eval suite of toy cases that every configuration passes.
