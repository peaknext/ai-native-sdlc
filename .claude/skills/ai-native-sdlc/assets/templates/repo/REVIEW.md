# How pull requests are reviewed here

<!-- Read by AI review and by human reviewers. Keep it short and tune it monthly:
     reviews nobody reads are noise. This file is taken from the base branch, so a
     pull request cannot change the rules it is reviewed under. -->

## Passes
Run each pass separately and tag every finding with its pass.

1. **Bugs:** logic errors, unhandled cases, broken behaviour.
2. **Security:** vulnerabilities, secrets, unsafe handling of input or personal data.
3. **Compliance:** does the change do what its `spec.md` and `plan.md` say, no more and
   no less? Does it follow `CLAUDE.md` and the team's design principles?

## Severity
- **Important:** breaks behaviour, leaks data, or breaches a policy. Give the location,
  the failure scenario, and a suggested fix.
- **Nit:** style, naming, small improvements. At most **5** per review; summarise any
  others as a count.

## Always check
- Verification output (build, test, lint) is attached and matches the change.
- In a bug-fix PR, existing tests were not edited to make them pass.
- `plan.md` matches the diff, with deviations recorded.

## Skip
- Generated files: TODO(paths, e.g. `src/gen/**`)
- Anything CI already enforces: TODO(formatting, import order, ...)

## Approval
Findings inform the approver; they do not approve or block on their own. A code owner
approves every merge. The author of a change, human or AI, never approves it.
