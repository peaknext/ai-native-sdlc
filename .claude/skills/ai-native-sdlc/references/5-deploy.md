# Stage 5: Deploy - review both ways, gates enforced as the agent acts

**Principle:** the agent does everything up to the production gate and nothing past it. Review runs in both directions (Claude reviews incoming changes; Claude fixes review comments on its own changes), and governance is enforced at the moment of action instead of in a later review cycle.

Contents:
1. AI in the pull-request review loop (`REVIEW.md`)
2. Hooks as approval gates
3. Locked-down settings for regulated environments
4. CI/CD integration, deployment and rollback

## 1. AI in the PR review loop

When agents write most of the diff, review capacity planned around human output cannot keep up: either the queue grows or code ships under-reviewed. The answer is identical review passes on every PR, with findings ranked by severity, so human attention moves to two questions: *does this change do what the plan intended, and is the risk acceptable?*

**Needs first:** an up-to-date `CLAUDE.md`; policy skills if review must enforce written policies; subagents if you use them for review passes.

**Infrastructure:** a repo with the Claude integration installed: either the managed Code Review service (an admin enables it per repo) or `anthropics/claude-code-action` in your own CI when you need control of the pipeline or model access through your own cloud agreement. Branch protection requiring code-owner approval is strongly recommended.

Steps:

1. **Turn review on** by the fastest route available (managed service first; your own CI when you need the control).
2. **The tech lead writes `REVIEW.md` at the repo root.** It defines the passes, what counts as Important versus a Nit, the nit cap, and what to skip. Template: `assets/templates/repo/REVIEW.md`. It is read from the base branch, never from the PR's own changes, so a PR cannot rewrite the rules it is reviewed under.
3. **Set the human threshold.** Findings neither approve nor block on their own; branch protection still requires a code owner. A platform engineer may additionally gate merges on the machine-readable severity tally.
4. **Close the loop on comments.** When a reviewer or author tags `@claude` on a review comment, Claude addresses it and pushes the fix, recorded in the PR thread. For PRs Claude opened, it can shepherd the PR: sweep unresolved comments and failing checks until everything is green and only the code owner's approval is outstanding.
5. **Feed findings back.** A mistake flagged a second time goes into `CLAUDE.md`. Review also flags when a change makes `CLAUDE.md` out of date.
6. **Tune monthly.** Rate the findings, cap nit volume, exclude generated paths and anything CI already enforces. Reviews nobody reads are noise.

### Doing a review yourself

When asked to review a change (a PR, a branch, a diff):

1. Read `REVIEW.md`, `CLAUDE.md`, and the change's `spec.md` and `plan.md` if they exist.
2. Run the passes separately, because mixing them makes each one shallower:
   - **Bugs and logic errors.**
   - **Security and vulnerabilities.**
   - **Compliance:** does the diff do what `spec.md` and `plan.md` say, no more and no less? Does it follow the design principles and policies?
3. Tag each finding with its pass and a severity. **Important** is reserved for what breaks behaviour, leaks data or breaches policy. Style and naming are **Nits**; cap them (five is a good default) and summarise the rest as a count.
4. For each Important finding give the location, the failure scenario, and a suggested fix.
5. Check the evidence: is the verification output attached? Were existing tests changed in a fix PR?
6. End with a plain-language summary for the approver: what the change does, what the main risk is, what you could not verify.

**Separation of duties:** the agent that wrote the code cannot approve it. Never approve or merge your own PR, and when you both wrote and reviewed a change, say so, so that the human knows the review was not independent.

Evidence: findings, fixes, ratings and approvals live in the PR history, which is the audit record. Approval comes from a human through branch protection.

What to measure:
- **Leading:** time to first review (should fall to minutes); share of comments resolved without a human touching the branch.
- **Lagging:** defects and vulnerabilities caught before merge versus those that escaped to production.

## 2. Hooks as approval gates

A hook can **allow**, **ask** (pause for a person's approval) or **block**. Release gating is the clearest use, but a hook can stand wherever the agent acts: blocking edits to database migrations or infrastructure without a change ticket, blocking test edits during fixes.

Steps:

1. **List the approvals that must survive.** Leadership, change management and compliance decide: change sign-off, release authorisation, edits to protected paths. Write the list down.
2. **Encode each as a hook:** a script that inspects the action before it happens and returns allow, ask or block.
3. **Put team hooks in `.claude/settings.json` in git.** Non-negotiable hooks go in admin-owned managed settings that engineers cannot disable.
4. **Make every block explain itself:** the reason and the route to approval, shown in the agent's output.

### Mechanics (Claude Code)

Wiring, in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [{ "type": "command",
                    "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/production_gate.py" }] },
      { "matcher": "Edit|Write",
        "hooks": [{ "type": "command",
                    "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect_paths.py" }] }
    ]
  }
}
```

- The hook receives JSON on standard input: `tool_name`, and `tool_input` (`command` for Bash; `file_path` for Edit and Write, always absolute).
- **Exit 0** with no output: no opinion, normal permission flow continues.
- **Exit 2:** the action is blocked and whatever was written to standard error is shown to the agent as the reason.
- To **ask** a human, exit 0 and print: `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": "..."}}` (`allow` and `deny` work the same way).
- Use either the exit code or the JSON in one hook, not both.

Formats change between versions. Before relying on a hook in production, check the current hooks reference (code.claude.com/docs/en/hooks) and test the hook by piping a sample JSON into it.

The template `production_gate.py` blocks commands that look like a production deployment unless a release approval is present, and asks before a direct push to a protected branch.

Governance: the gate applies every time, for everyone. Allow and block decisions are logged with timestamps. The gate itself defines what counts as approval: an approved change ticket, or the release manager's sign-off.

What to measure: time spent waiting at each gate; gate violations reaching production before and after hooks.

## 3. Locked-down settings for regulated environments

A platform team can deploy managed settings (through device management or the admin console) that engineers cannot edit or override. Treat the following as a checklist to tailor, not a file to copy:

| Area | Typical control | Why |
|---|---|---|
| Permissions | Deny reads of `.env` files and secrets directories; deny web fetches and shell `curl`/`wget` | Keeps secrets out of the agent's context and limits where data can go |
| Pre-allowed commands | Allow `git` and the build, test and lint targets | Removes prompt fatigue from the inner loop, so people do not learn to click "yes" without reading |
| Lockdown | Disable bypass-permissions mode; only managed permission rules apply | Nobody can switch the guardrails off locally |
| Sandbox | On, refuses to start if unavailable, no unsandboxed retries; an OS-level network allowlist | A tool-level fetch deny does not stop network access from the shell; the sandbox closes that gap |
| Credentials | Deny access to SSH keys and cloud credential files; strip tokens from sandboxed commands | Covers shell reads that file-tool deny rules miss |
| Extensibility | Only managed hooks run; only approved plugin marketplaces and MCP servers; a minimum tool version | Prevents sideloading around the controls |

Exact setting names change; take them from the current settings reference (code.claude.com/docs/en/settings) when writing the real file.

## 4. CI/CD integration, deployment and rollback

Pipelines traditionally run deterministic scripts, and the judgment work (is this test flaky? what caused the build failure? what goes in the changelog?) waits for a person. Run non-interactively, the agent can take those steps, inside per-environment gates.

**Needs first:** the PR review loop and approval-gate hooks. The gates must exist before automation accelerates through them.

**Infrastructure:** CI that can run `claude -p` (or `claude-code-action`); model access; deployment targets exposed as tools (MCP servers) scoped per environment; a sandbox profile for agent jobs with no standing production credentials.

Steps, in order of increasing trust:

1. **Read-only judgment steps first:** triage a failed build, summarise a flaky test, draft a changelog. Low risk, immediately useful.
2. **Write steps behind existing gates:** lint fixes, generated docs, review-comment fixes. The output arrives as a pull request through branch protection. The agent has no route to push to the main branch.
3. **Sandbox agent jobs:** containers under network policy, short-lived scoped tokens, no production credentials by default.
4. **Expose deploy, status and rollback as tools scoped per environment,** so deployment power is an explicit allowlist.
5. **Tier autonomy by environment:** development is free; staging is intermediate; in production the agent prepares the release and the release manager authorises it, enforced by a hook.
6. **Make rollback the most rehearsed path:** a single command the agent can run, exercised regularly in staging. The Maintain stage calls it when a control band is breached.

A first pipeline step to try, on failure only:

```bash
claude -p "Read build.log. Identify the most likely cause, say whether it looks flaky or real, \
and write a three-line summary." --allowedTools "Read" >> triage.md
```

Controls that make this safe:

- Branch protection turns agent writes into PRs; there is no direct path to main.
- The production deploy hook blocks release until a named release manager authorises it.
- Each non-interactive run acts under the agent's own identity, so logs separate agent actions from those of the engineer who triggered it.
- Permission tiers differ per environment.

What to measure:
- **Leading:** share of pipeline failures triaged without paging a human.
- **Lagging:** the DORA measures (deployment frequency, lead time for changes, change failure rate, time to restore service) from CI and deployment tooling.

## Common mistakes

- Treating AI review as approval. It informs the approver; it does not replace them.
- Unlimited nits, so the one Important finding is lost.
- Automating deployment before the gates and the rollback path exist.
- A block with no explanation, which teaches people to look for a way around it.
