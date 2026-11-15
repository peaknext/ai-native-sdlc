# intent/

One folder per change. Each folder tells the story of that change in up to three files:

| File | Answers | Written in | Accepted by |
|------|---------|-----------|-------------|
| `intent.md` | What do we want, and why? | Stage 1: Plan | Whoever owns the outcome |
| `spec.md` | What exactly will we build? | Stage 2: Design | Product owner (tech lead if risky) |
| `plan.md` | How will the code change? | Stage 3: Build | Engineer (tech lead if risky) |

Small changes (a bug fix, a contained tweak) may have only `plan.md`, or `intent.md` and `plan.md`.

## Rules
- Folder name: `YYYY-MM-DD-short-name`.
- Every file starts with a header whose `status` is `draft`, `accepted`, `rejected` or `superseded`.
- A stage starts only when the previous file is `accepted`. Acceptance is a human decision;
  record who and when in `accepted_by` and `accepted_on`.
- Edit in place and commit. The git history of this folder is the audit trail.
- If a ticket or requirements system is the official record, put its ID in `source`.
