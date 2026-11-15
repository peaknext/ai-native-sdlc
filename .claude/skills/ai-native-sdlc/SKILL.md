---
name: ai-native-sdlc
description: Run software work as an AI-native development loop - Plan (intent.md), Design (spec.md), Build (plan.md, CLAUDE.md, hooks), Test (self-verification, evals), Deploy (review, approval gates, CI/CD), Maintain (monitoring, scans, incidents). Every stage ends in a committed artifact and a human approves at the gates. Use this skill whenever someone wants to build or change software beyond a trivial edit - turning an idea into an app or feature, writing requirements or a spec, planning an implementation, fixing a bug properly, setting up a repo for AI-assisted development (CLAUDE.md, hooks, review rules, evals, CI), reviewing or shipping a change, handling a production incident, or adopting an AI-native process as a team - even if they never say SDLC or playbook. Also use for Thai requests such as อยากทำแอป, อยากได้ระบบ, เริ่มโปรเจกต์ใหม่, เพิ่มฟีเจอร์, แก้บั๊ก, วางแผนพัฒนา, เขียน requirement หรือ spec, ตั้งค่า repo, รีวิวโค้ด, ปล่อยขึ้น production.
---

# AI-native SDLC

Writing code is no longer the slow part of software development. Deciding what to build, proving it works, and shipping it safely are. This skill runs development as a loop of six stages built around that fact:

- **You (Claude) do the work inside each stage.**
- **A human makes the judgment call at the gate between stages.**
- **Every stage leaves a small file in git that the next stage starts from.**

The approach follows Anthropic's "The AI-native SDLC playbook" (claude.com/resources/articles/the-ai-native-sdlc-playbook), adapted so it also works for one person with an idea, not only for a large engineering organisation.

## The loop

| # | Stage | Question it answers | What gets committed | Who decides at the gate |
|---|-------|---------------------|---------------------|-------------------------|
| 1 | Plan | What do we want, and why? | `intent.md` | The person who owns the outcome (product owner / requester) |
| 2 | Design | What exactly will we build? | `spec.md` | Product owner; a tech lead too if it is risky |
| 3 | Build | How will the code change? | `plan.md`, then the diff and its tests | The engineer (plan); tech lead for risky changes |
| 4 | Test | Is it proven to work? | Test results, screenshots, eval runs | Nobody waits here: evidence is attached automatically |
| 5 | Deploy | Is it safe to merge and release? | The pull request with review findings | Code owner (merge); release manager (production) |
| 6 | Maintain | Is it still healthy? | Incident record, which becomes a new `intent.md` | Service owner / on-call |

Stage 6 feeds stage 1: a production problem is written up as a new `intent.md`, which is why this is a loop and not a line.

The commit history of these files is the audit trail: who asked, what was produced, who approved. That is the reason artifacts are written to files and committed instead of being left in the conversation, where they disappear.

## Where the files live

Use this layout unless the repo already has its own (if a ticket system or requirements tool is the official record, read `references/governance.md` first):

```
intent/
  2026-11-15-short-name/     one folder per change
    intent.md                Stage 1
    spec.md                  Stage 2
    plan.md                  Stage 3
CLAUDE.md                    what a new teammate needs on day one (read every session)
REVIEW.md                    how pull requests get reviewed
.claude/skills/              policies and know-how, written so they are applied automatically
.claude/agents/              reusable helpers (verifier, researcher, ...)
.claude/hooks/               checks that cannot be skipped
evals/                       regression tests for the agent's own setup
ops/                         production monitoring bands and lessons learned
```

Each artifact starts with a small header so both people and scripts can see its state:

```yaml
---
id: 2026-11-15-short-name
title: One line a non-engineer would recognise
status: draft            # draft -> accepted | rejected | superseded
author: who asked for it
created: 2026-11-15
accepted_by:
accepted_on:
source:                  # ticket, incident or conversation it came from
---
```

Templates for every file are in `assets/templates/`. Copy them; do not invent a new shape each time, because consistent shape is what lets the next stage (and the next person) read them quickly.

## Step 0: find your place in the loop

Before doing anything, look at what already exists. From the skill directory:

```bash
python scripts/sdlc.py status <repo-root>
```

It lists every change under `intent/`, which artifacts exist, their status, and the next step. Also check whether `CLAUDE.md` exists and whether tests, build and lint each run with one command.

Then match the request to an entry point:

| The person says something like... | Start at | Read |
|---|---|---|
| "I have an idea", "I want an app that...", "we need a feature for..." | Stage 1 | `references/1-plan.md` |
| There is an accepted `intent.md`; "write the requirements / spec / design" | Stage 2 | `references/2-design.md` |
| There is an accepted `spec.md`; "implement this", "plan the work" | Stage 3 | `references/3-build.md` |
| "Fix this bug", "this is broken" | Small track (below): stage 3 plan + stage 4 failing-test-first | `references/4-test.md` |
| "Set this repo up for AI development", "write a CLAUDE.md", "add guardrails" | Bootstrap (below) | `references/3-build.md` |
| "Review this PR", "is this ready to merge", "set up CI", "release it" | Stage 5 | `references/5-deploy.md` |
| "Production is down", "we got an alert", "scan the codebase", "write the post-mortem" | Stage 6 | `references/6-maintain.md` |
| "How should our team adopt this?", "what should we measure?" | Adoption | `references/adoption-and-metrics.md` |
| Questions about approvals, audit, compliance, existing tools like Jira | Governance | `references/governance.md` |

Read only the reference file for the stage you are in. Each one has the detailed steps, the quality bar, the evidence to keep and the metrics.

## Step 1: pick a track

The loop exists to make intent reviewable before code exists. It is not a quota of documents. Size the process to the change:

| Track | Use when | What you do |
|---|---|---|
| **Tiny** | Typo, one-line config, rename: obvious and reversible | Make the change, verify it, say what you did. No artifacts. |
| **Small** | A bug fix or a contained change with a clear ask, a few files | A short plan (in `plan.md`, or in chat if the repo keeps no `intent/` folder), a failing test first for bugs, verification output, a pull request. |
| **Full** | A new product or feature; anything touching users, data, money or security; anything where what is wanted is not yet clear | `intent.md` -> `spec.md` -> `plan.md` -> build -> verify -> review. |

If you are unsure, take the lighter track and say which one you chose and why in one sentence. Move up a track the moment you find the change is bigger than it looked (more files than expected, an unclear requirement, a risk to data). Escalating late is a common failure: a "small fix" that quietly became a redesign has skipped every gate.

## Step 2: run the stage

Short version of each stage. The reference file has the full play.

**1. Plan: capture intent.** Get the originator to describe the problem in their own words: what they cannot do today, who is affected, what better looks like, what is out of scope. Ask the questions a good analyst would (a few at a time, with suggested answers). Write `intent.md`: what and why, never how. Read it back, let them correct it, commit it. -> `references/1-plan.md`

**2. Design: requirements and design in one session.** Read the accepted `intent.md` and the existing code. Apply the organisation's policies (skills for brand, security, compliance, UX) while writing, not afterwards. Produce `spec.md` with numbered requirements, each with an acceptance check, plus a "flagged concerns" section for anything risky or contradictory. The owner reviews; they do not write it. -> `references/2-design.md`

**3. Build: plan first, then implement.** Explore the code without changing it, write `plan.md` (files that change, order of work, risks, options rejected, how it will be proven), and get the plan accepted before the first edit. Then implement, keeping `plan.md` true to what you actually did. This is also where `CLAUDE.md`, skills, hooks, parallel sessions and subagents come in. -> `references/3-build.md`

**4. Test: prove it before a human looks.** Run the tests, the build and the linter yourself and iterate until they pass. For bugs, write a failing test first and then make it pass without touching that test. For UI, look at a screenshot and compare. Paste the real output. Guard the setup itself (CLAUDE.md, skills, hooks) with evals in CI. -> `references/4-test.md`

**5. Deploy: review both ways, gates enforced.** Review the pull request in passes (bugs, security, compliance with spec and plan), rank findings by severity, and fix review comments on your own PRs. You may do everything up to the production gate and nothing past it. -> `references/5-deploy.md`

**6. Maintain: close the loop.** A deterministic check watches production; when a band is breached you diagnose, act only through gated routes (a PR, a pre-approved runbook), and write the finding up as an `intent.md`. Every incident leaves behind a regression test or eval. -> `references/6-maintain.md`

## Gates: where you stop

At a gate, do three things: summarise the artifact in a few plain sentences, list the open questions and flagged concerns, and ask for accept / correct / reject. Record the answer in the artifact header (`status`, `accepted_by`, `accepted_on`) and commit.

How strictly to pause depends on what the person asked for:

- **They want to be involved** (the default for the Full track): stop after each artifact. Misunderstandings are cheapest to fix in `intent.md`, more expensive in `spec.md`, and most expensive in code.
- **They said "just build it"**, or nobody is available to answer (a non-interactive run): do not stall and do not skip the artifacts either. Write each one, put your guesses in an explicit **Assumptions** section, leave real unknowns in **Open questions**, set `accepted_by` to a note such as `requester (asked to proceed without stage review)`, and continue as far as their instruction covers. Tell them at the end which assumptions most deserve a second look.

Some gates are never yours to open, whatever the instruction, because they are the controls that make agent-written code trustworthy:

- Approving or merging your own pull request. The author of a change cannot be its approver.
- Deploying to production, or anything else a hook or policy reserves for a named person.
- Changing a test, a hook, a permission rule or a protected file in order to get a green result.

When one of these blocks you, say what is blocked, why, and who can approve it. A block that explains itself is a working control; a block you route around is a broken one.

## Rules that hold in every stage

1. **Artifact before action, and commit it.** If it is not in git, the next stage cannot read it and nobody can audit it.
2. **Prove, don't claim.** "Done" means the check ran and the output is shown. If a test fails, fix the code, not the test.
3. **Know which controls are advisory and which are certain.** `CLAUDE.md` and skills make the right behaviour likely. Hooks, CI checks and branch protection make it certain. When someone says a rule must always hold, propose the deterministic backstop instead of promising to remember.
4. **Same mistake twice goes into `CLAUDE.md`.** Keep that file under a page: it is read in full every session, and stale lines cost attention.
5. **Keep `plan.md` in step with the diff.** When implementation departs from the plan, update the plan in the same commit, so reviewers compare the code against what was actually intended.
6. **One source of truth per artifact.** If a ticket or requirements system already holds the record, link both ways (record ID in the file, commit SHA in the record) instead of creating a silent second copy.
7. **Right-size, and say so.** State the track you chose. Ceremony that nobody reads is cost with no control behind it.

## Bootstrapping a repo

When a repo is not yet set up for this way of working, scaffold it:

```bash
python scripts/sdlc.py init <repo-root>                      # CLAUDE.md, intent/, REVIEW.md
python scripts/sdlc.py init <repo-root> --with hooks,agents  # add guardrails and helper agents
python scripts/sdlc.py init <repo-root> --all                # everything, including evals, CI and ops
python scripts/sdlc.py new  <repo-root> "Title of the change" --author "Name"
```

`init` never overwrites an existing file; it reports what it created and what it skipped. Then do the part a script cannot: replace every placeholder with facts from this repo. Read the manifest files (`package.json`, `Makefile`, `pyproject.toml`, ...) to find the real build, test and lint commands and run each once to confirm it works before writing it into `CLAUDE.md`. A `CLAUDE.md` with placeholder commands is worse than none, because it will be trusted.

When someone names things the AI must never do ("never edit the generated client", "never deploy on its own"), install the hooks and turn each rule into a deterministic control: a line in `.claude/protected-paths.txt` or a setting in `production_gate.py`, a `permissions.deny` rule as a second layer, and a line in `.claude/guardrail-checks.txt`. Then run `python3 .claude/hooks/check_guardrails.py` and show its output. The hook templates are already tested, so configure them instead of rewriting them. Details: `references/3-build.md` (section 5) and `references/5-deploy.md` (section 2).

Bring in the heavier pieces in the order the team can absorb them; `references/adoption-and-metrics.md` gives the order and what each piece depends on. For someone working alone, `CLAUDE.md`, the `intent/` folder and a one-command test run are enough to start.

## Working with people who do not write code

Many people using this loop are product owners, founders or domain experts. Stage 1 and 2 are designed for them, so:

- Answer in the language they write in. File names, commands and field names stay in English because they are identifiers, but explain each the first time it appears ("`intent.md`: a one-page note saying what you want and why").
- At each gate say what the file contains, what you need from them, and what happens next, in two to four plain sentences. Do not paste a long document and ask "approve?".
- When a technical choice has to be made, recommend one option with the reason in everyday terms, and say what it would cost to change later. Do not hand them a menu.
- Write artifacts in their language too, unless the team's convention is otherwise. The document is for the person who has to approve it.
- Never invent facts to fill a template. Numbers you estimated are labelled as estimates to verify; unknowns go under Open questions.

## Reference map

| File | Read it when |
|---|---|
| `references/1-plan.md` | Turning an idea, ticket or incident into `intent.md` |
| `references/2-design.md` | Turning accepted intent into `spec.md`; applying policy skills; flagged concerns |
| `references/3-build.md` | Planning and implementing; `CLAUDE.md`; writing skills; build-time hooks; parallel sessions and subagents; brand-new projects |
| `references/4-test.md` | Feedback loops; the failing-test-first bug protocol; UI verification; evals in CI |
| `references/5-deploy.md` | PR review and `REVIEW.md`; approval-gate hooks; locked-down settings; CI/CD and rollback |
| `references/6-maintain.md` | Monitoring bands and response tiers; recurring scans; incidents in chat; post-mortems |
| `references/governance.md` | Who approves what; evidence per stage; advisory vs deterministic controls; living alongside Jira and other systems of record |
| `references/adoption-and-metrics.md` | Rolling this out to a team; what depends on what; what to measure |

Templates: `assets/templates/change/` (intent, spec, plan), `assets/templates/repo/` (everything `init` installs), `assets/templates/policy-skill.md` (turning a written policy into a skill).
