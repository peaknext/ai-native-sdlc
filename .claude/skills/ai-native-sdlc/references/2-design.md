# Stage 2: Design - requirements and design as `spec.md`

**Goal:** turn an accepted `intent.md` into a specification engineering can plan against, in one working session, with the organisation's policies applied while it is written. Traditionally an analyst writes requirements, a designer interprets them, and reviewers check policy at the end; each step is slow and loses detail. Here the product owner reviews the spec but does not have to write it.

**Needs first:** an accepted `intent.md`. Helpful: brand, security, compliance and UX policies written as skills (see "Skills" in `3-build.md`). If none exist, say so in the spec and apply sensible general practice, naming what you applied.

**Output:** `spec.md` next to `intent.md`, committed. The pair records what was asked and what was decided.

## Steps

1. **Open the session with the right context.** Read `intent.md`, the existing codebase (so the design fits what is there), and every relevant policy skill. Note which skills, and which version (git commit), you applied.

2. **Write the spec.** The working instruction is essentially: *read the intent; produce a requirements and design spec that integrates with the existing codebase; apply the available skills for brand, security and UX; document it fully as `spec.md`; describe every area of concern, especially where policies contradict each other or the intent.* Use `assets/templates/change/spec.md`.

3. **The owner reviews the spec against the idea.** Two questions matter: does this solve the stated problem, and has every open question from the intent been answered or deliberately carried forward?

4. **Resolve flagged concerns first, with the people who own those policies,** before engineering sees the spec. A concern discovered here is a conversation; the same concern discovered in code review is rework.

5. **Commit `spec.md` alongside `intent.md`.**

6. **The owner decides whether to proceed,** consulting a tech lead for higher-risk items. A human always makes this call. Acceptance (`status: accepted`) is what starts Build.

## What a good spec contains

- **Summary** in plain language: what will exist when this is done.
- **Requirements**, numbered (`R1`, `R2`, ...), each a single testable statement with an **acceptance check** ("Given a patient who opted out, when reminders run, then no message is sent"). Numbering lets the plan, the tests and the review refer back to them.
- **Design:** how it fits the existing system: components touched, data that is stored or moved, interfaces, the user-facing flow. Detailed enough to plan from, not a line-by-line implementation.
- **Non-functional needs:** performance, availability, accessibility, privacy, anything with a number attached.
- **Policies applied:** which skills or standards, and what each changed in the design.
- **Flagged concerns:** see below.
- **Open questions carried forward** and **out of scope**.
- **Decision record** in the header: who accepted, when.

For a brand-new project, the spec also proposes the technology (language, framework, hosting) with a one-sentence reason each, chosen for the team that has to maintain it. For a non-technical owner, explain the choice in everyday terms and say what it would cost to change later.

## Flagged concerns

This section is the main reason to have a human gate here. Flag, do not silently resolve:

- **Policies that contradict each other** (brand wants the customer's name in the message; privacy forbids personal data in that channel).
- **Intent that conflicts with a policy or a constraint.**
- **Requirements you had to guess.** Say what you assumed and what changes if the assumption is wrong.
- **Risk:** anything touching money, personal data, authentication, irreversible operations, or other teams' systems.
- **Scope pressure:** parts that are much more expensive than the intent seems to assume.

For each concern give the options and your recommendation. A list of worries with no recommendation just moves the work to the reader.

## User interfaces

For anything visual, a mock is part of the spec. The owner can iterate on a design from the intent (for example in Claude Design, or as a simple HTML prototype or annotated screenshot) and export or attach it. The approved mock then becomes a proof target in Build: "the screenshot matches the approved mock".

## From hand-run to automatic

Adopt this in three steps, moving on only when the previous one produces specs people accept without heavy rework:

1. **Prompt it by hand** each time.
2. **Codify it** as a shared slash command or skill, so everyone gets the same pass.
3. **Trigger it**: accepting an `intent.md` starts a non-interactive job that runs the pass and opens a pull request containing `spec.md` (the CI plumbing is in `5-deploy.md`).

## Evidence this stage leaves (governance)

- Policy is applied while the spec is written, not inspected afterwards.
- The spec, the prompt used, and the versions of the skills in force are in version control.
- The owner's sign-off and the routing of each concern to its policy owner are recorded.

## What to measure

- **Leading:** elapsed time between the `intent.md` commit and the `spec.md` commit, compared with the old requirements-plus-design cycle.
- **Lagging:** requirements rework after build starts: count `spec.md` commits dated after the first `plan.md` commit for the same change.

## Common mistakes

- Restating the intent at greater length instead of making decisions.
- Requirements that cannot be checked ("should be fast", "easy to use").
- Designing in isolation from the existing code, so the plan stage discovers the spec does not fit.
- Burying a serious concern in the middle of a paragraph. Concerns go in their own section, at the top of the gate summary.
- Proceeding to Build on your own acceptance.
