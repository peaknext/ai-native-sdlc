# Adopting the loop, and measuring it

## What depends on what

Each practice ("play") can be adopted on its own, but some need others first. Plays with nothing in the "needs" column are safe starting points.

| Stage | Play | Needs first |
|---|---|---|
| 1 Plan | Capture intent as `intent.md` | nothing |
| 2 Design | Requirements and design as `spec.md` | `intent.md`; policies written as skills |
| 3 Build | Plan first (`plan.md`) | nothing (`CLAUDE.md` helps) |
| 3 Build | `CLAUDE.md` | nothing |
| 3 Build | Skills as institutional knowledge | nothing (a named policy owner and a written source) |
| 3 Build | Hooks as build-time guardrails | nothing |
| 3 Build | Parallel sessions and subagents | `CLAUDE.md`; feedback loop |
| 4 Test | Feedback loop (self-verification) | nothing (one-command test and build) |
| 4 Test | Continuous evals in CI | `CLAUDE.md`; feedback loop |
| 5 Deploy | AI in the PR review loop | `CLAUDE.md`; skills; subagents if used |
| 5 Deploy | Hooks as approval gates | nothing (a written list of required approvals) |
| 5 Deploy | CI/CD integration and deployment | PR review loop; approval-gate hooks |
| 6 Maintain | Monitoring bands, closing the loop | `intent.md`; PR review; hooks; a rollback path |
| 6 Maintain | Recurring codebase scans | PR review gate; approval-gate hooks; `intent.md` |

## A sensible order

**Wave 1: foundations (one team, one repo, a couple of weeks).** `CLAUDE.md`; one-command build, test and lint with self-verification as the definition of done; plan-first for every non-trivial change; `intent.md` for new work. All have no prerequisites and pay back immediately.

**Wave 2: guardrails and knowledge.** The first policy skill (pick the policy that is most often violated); hooks for protected paths and release approval; `REVIEW.md` and AI review on every PR; `spec.md` produced from intent with skills applied.

**Wave 3: scale.** Parallel sessions and subagents; evals in CI guarding the configuration; auto-accept for routine work once the guardrails have proven themselves; read-only CI judgment steps (build triage, changelogs).

**Wave 4: the autonomous loop.** Write steps in CI behind gates; per-environment deployment tools and a rehearsed rollback; monitoring bands that open `intent.md`; scheduled scans.

For one person, or a very small team, Wave 1 plus `REVIEW.md` is a complete and useful practice. Stop there until something hurts.

## From hand-run to automatic

Every stage transition matures the same way:

1. **Prompt each step by hand.** Learn what a good artifact looks like.
2. **Codify the prompt** as a skill or slash command, so everyone runs the same pass.
3. **Trigger it:** accepting one artifact fires the next stage. Accepted `intent.md` starts design; accepted `spec.md` starts planning; a merged PR starts the pipeline; a breached production band writes the next `intent.md`.

The end state is a loop in which human attention is concentrated at the gates. Do not automate a transition until the hand-run version reliably produces artifacts people accept.

## Rolling it out

- **Start with a pilot team and one repo** where the people are willing and the test suite is decent. A repo without tests gets the feedback loop first.
- **Name the owners:** who owns `CLAUDE.md`, each policy skill, `REVIEW.md`, the hooks, the eval suite. Unowned configuration rots.
- **Take a baseline before changing anything:** the measures below, for the last quarter. Without a baseline nobody can say whether it worked.
- **Review the numbers monthly** together with a sample of artifacts. Numbers say that something moved; artifacts say why.
- **Expect the bottleneck to move.** When build speeds up, the queue appears at review, then at deploy. That is the signal for the next wave, not a failure.

## Measures

Leading measures move within weeks and show whether the practice is being followed. Lagging measures move within months and show whether it is paying off.

| Play | Leading | Lagging | Source |
|---|---|---|---|
| Intent | Time from first conversation to committed `intent.md` | Share of intent accepted into Design; intent changes after first spec commit | Git log of `intent/` |
| Spec | Time from `intent.md` commit to `spec.md` commit | Spec commits after the first `plan.md` commit (requirements rework) | Git log |
| Plan first | Share of changes merged from first implementation pass; plan approval to merge time | Rework cycles per change; merged diff still matches `plan.md` | PR metadata, git |
| `CLAUDE.md` | Repeats of mistakes it should have prevented | Time to first merged PR for a new joiner | `CLAUDE.md` history, PRs |
| Skills | Policy approval to skill merged | Review findings citing the policy (should approach zero) | Git, PR findings |
| Parallel work | Concurrent sessions per engineer while review holds; time steering vs waiting | Changes merged per engineer per week, with rework rate | Telemetry export, PRs |
| Feedback loop | First-pass CI success for agent-written changes | Review time per PR; change failure rate | CI, incident tracker |
| Evals | Pass rate over time; incident to permanent eval time | Regressions caught in CI vs in production | CI logs, incident tracker |
| PR review | Time to first review; comments resolved without a human touching the branch | Defects and vulnerabilities caught before merge vs escaped | PR history |
| Approval hooks | Time waiting at each gate | Gate violations reaching production | Hook logs |
| CI/CD | Pipeline failures triaged without paging a human | DORA: deployment frequency, lead time, change failure rate, time to restore | CI and deploy tooling |
| Monitoring loop | Band breach to `intent.md` in triage | Findings that become merged fixes; repeat incidents of the same class | Monitoring, git |
| Scans | Repos on a schedule; finding to patch-in-review time | Found by scan vs found in production; findings per scan trend | Scan history |

Several of these fall straight out of git. For example, requirements rework for one change:

```bash
# spec.md commits made after the first plan.md commit for the same change
first_plan=$(git log --diff-filter=A --format=%cI -- intent/<change>/plan.md | tail -1)
git log --since="$first_plan" --oneline -- intent/<change>/spec.md | wc -l
```

Read the measures in pairs. Speed without its quality partner (merged changes per week without rework rate; time to first review without escaped defects) rewards the wrong behaviour.
