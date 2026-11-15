# Stage 1: Plan - capture intent as `intent.md`

**Goal:** the person who has the need writes it down in their own terms, with your help, in one sitting. No backlog entries, story points or refinement meetings in between, because each of those handoffs loses a little of what was actually wanted.

**Needs first:** nothing. This play can be the very first thing a team adopts.

**Output:** `intent/<date>-<slug>/intent.md`, committed, status `draft` until the product owner accepts it.

## Where intent comes from

| Source | What changes |
|---|---|
| A person's idea or request | Run the steps below with them. |
| A ticket or tracker item | Read the ticket (through a connector if available), then run the same steps with whoever owns it. Put the ticket ID in `source`. |
| An incident or alert | The Maintain stage writes the `intent.md` (anomaly and evidence instead of "problem"). See `6-maintain.md`. |

The steps are the same whatever the source, and so is the gate: a human reviews and corrects the agent-written file before it is committed as accepted.

## Steps

1. **Let them describe it in their own words.** Ask for four things: what they cannot do today, who is affected, what "better" looks like, and what is explicitly out of scope. Do not correct their vocabulary into technical terms; the file should sound like them.

2. **Brainstorm until it is concrete.** Ask what an analyst would ask, covering scope, users, constraints and success. Keep it humane: three to five questions at a time, most important first, each with a suggested answer they can simply accept. Useful probes:
   - Who exactly does this, how often, and what do they do today instead?
   - What is the smallest version that would already be useful?
   - What must not change or break? (existing logins, data that must stay private, a deadline, a budget)
   - How would we know, a month after launch, that it worked?
   - Who else is touched by this: other teams, other systems, customers?

   If nobody can answer (a non-interactive run, or they asked you not to ask), decide sensibly and record each decision under **Assumptions**.

3. **Write `intent.md` from the template** (`assets/templates/change/intent.md`, or `python scripts/sdlc.py new <repo> "<title>"`). Sections: problem, proposed outcome, affected users and systems, constraints, out of scope, success measures, assumptions, open questions.

4. **Read it back and let them correct it.** Summarise in a few sentences, then ask specifically about the parts you inferred. Corrections here cost minutes; the same corrections after code exists cost days.

5. **Commit it to the shared home** the product owner watches. Author and timestamp become part of the record. When the owner accepts, set `status: accepted`, `accepted_by` and `accepted_on`, and commit again (in a team, the accepting merge or review is the record). Acceptance is what starts Stage 2.

## Quality bar

Before you call it done, check:

- Someone who was not in the conversation could say what the problem is and for whom.
- The outcome is described from the user's side ("customers can see...") and at least one success measure could actually be checked.
- It says **what and why, not how.** No screens, tables, frameworks or endpoints, unless one is a genuine constraint ("must use the existing login"). Solutions sneaking in here bypass the design stage and its policy checks.
- Constraints are real ones someone stated or that the context implies, not boilerplate.
- Unknowns are listed as open questions instead of being quietly answered.
- Any number you did not get from the person or from data is marked as an estimate to verify. An invented statistic in an intent file will be quoted as fact two stages later.
- It is one change. If it describes three outcomes for three groups of users, split it into three files and say so.

## Example

```markdown
---
id: 2026-11-15-appointment-reminders
title: Appointment reminders for clinic patients
status: draft
author: Front-desk manager
created: 2026-11-15
accepted_by:
accepted_on:
source: conversation
---

## Problem
Patients forget appointments. Front-desk staff phone each patient the day before, which
takes most of one person's afternoon, and missed appointments still leave empty chairs.

## Proposed outcome
Patients get a reminder automatically the day before and can confirm or ask to reschedule
without phoning. Staff only call the patients who have not responded.

## Affected users and systems
Patients; front-desk staff; the booking system that holds appointments and phone numbers.

## Constraints
- No medical details in the message: date, time and clinic name only.
- Must work for patients without a smartphone.
- Patients who opted out of messages must not receive any.

## Out of scope
Online booking of new appointments. Payment.

## Success measures
- Missed appointments fall (current rate: estimate ~1 in 8, to verify from the booking system).
- Staff time on reminder calls drops by more than half.

## Assumptions
- The booking system can export tomorrow's appointments.

## Open questions
- Which channel do patients prefer: SMS or a messaging app?
- Who handles a "reschedule" reply: staff, or the system directly?
```

## People who do not use git

A product owner does not need a terminal. From claude.ai or Cowork with a version-control connector, Claude can commit the markdown on their behalf. Setting up where intent lives, and who may write there, is a one-time job for whoever looks after the repo:

- **Simplest:** an `intent/` folder in the product's repo.
- **Intent that spans many repos:** a dedicated intent repo.
- **Monorepo:** a directory per product.

## Evidence this stage leaves (governance)

- The committed `intent.md` with author, timestamp and full revision history in git.
- The owner's accept or reject, recorded as the merge, closing review, or the `accepted_by` header.

## What to measure

- **Leading:** time from first conversation to committed `intent.md`. Expect hours where elicitation used to take weeks.
- **Lagging:** survival rate (share of intent files accepted into Design instead of closed), and how many times an `intent.md` is changed after the first `spec.md` commit for the same change. Many late changes mean the brainstorm is stopping too early.

## Common mistakes

- Writing the solution into the problem statement.
- Asking fifteen questions at once, so the person gives up and says "whatever you think".
- Treating a missing answer as permission to guess silently.
- Accepting your own draft. Acceptance belongs to the person who owns the outcome.
