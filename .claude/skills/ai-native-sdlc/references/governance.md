# Governance: who decides, what is recorded, what is enforced

An AI-native process keeps the old control objectives (the right people approve, changes are traceable, policy is followed) and enforces them differently. Controls that assume a human wrote every line stop being workable once agents write most of the diff, and exceptions routed through weekly committees cannot keep pace. So checks move to where the agent acts, and evidence is produced as a by-product of the work.

## Who approves what

| Decision | Approver | Recorded as |
|---|---|---|
| Is this the right problem? (`intent.md`) | Product owner / the person who owns the outcome | Accepting merge or review; `accepted_by` in the header |
| Is this the right solution? (`spec.md`) | Product owner; tech lead for higher-risk items; policy owners for flagged concerns | Same, plus the resolution of each concern |
| Is this the right way to change the code? (`plan.md`) | The engineer for routine changes; tech lead or architect for risky ones | Committed plan and its revisions |
| Can this merge? | A code owner, through branch protection | PR approval |
| Can this go to production? | A named release manager, or an approved change ticket | Hook decision log; release record |
| Can the agent's own setup change? (`CLAUDE.md`, skills, hooks) | Code owners; policy owners for policy skills | PR review plus the eval run |
| What do we do about this incident or finding? | Service owner / on-call; product owner if user-facing | Triage decision with a reason |

For one person working alone, the same person holds several of these roles. Keep the gates anyway, as moments to stop and look; they cost a minute and they are where mistakes get caught.

**Separation of duties:** whoever (or whatever) wrote a change cannot be the one to approve it. An agent never approves or merges its own PR.

## Advisory and deterministic controls

| Layer | Examples | Strength | Use it for |
|---|---|---|---|
| Advisory | `CLAUDE.md`, skills, prompts, `REVIEW.md` | Makes the right behaviour likely | Conventions, know-how, policies where an occasional miss is caught later |
| Deterministic | Hooks, permission rules, sandbox, CI checks, branch protection, managed settings | Makes it certain | Anything that must hold every time: protected paths, secrets, release approval |

A policy that must hold without exception needs both: the skill so the agent does the right thing first time, and the deterministic backstop so that it cannot do the wrong thing. When someone asks for a guarantee and only an advisory control exists, say so and propose the backstop.

## Evidence each stage leaves

| Stage | Evidence | Where |
|---|---|---|
| Plan | `intent.md`, author, timestamp, revisions, acceptance | Git history of the intent home |
| Design | `spec.md`, the prompt used, skill versions applied, sign-off, concern routing | Git |
| Build | `plan.md` and revisions, who accepted; the diff | Git; session logs |
| Test | Literal test, build and lint output; screenshots; eval runs | Session transcript (OpenTelemetry export), PR checks, CI logs |
| Deploy | Review findings, fixes, approvals; hook allow/block decisions with timestamps | PR history; hook logs |
| Maintain | Band breaches, diagnoses, triage decisions and reasons; scan history; incident records | CI/monitoring logs; `ops/`; git |

The chain `intent.md` -> `spec.md` -> `plan.md` -> diff -> PR -> incident record, each a commit, answers the auditor's questions: who asked, what did the agent produce, who approved.

## Living alongside existing systems of record

Jira, requirements tools with regulatory traceability, design tools and change-approval boards are hard to displace, because auditors and other teams depend on them. Do not create a silent second copy. For each artifact, name one system of record and choose a configuration:

| Configuration | How it works | Choose when |
|---|---|---|
| **Repo is the source of truth** | The legacy system links to the committed file | The team is free to change tooling |
| **Legacy system is the source of truth** | The markdown file is a working copy: the agent reads the record at the start of a session and writes the outcome back through a connector | An auditor or another team relies on the legacy record |
| **Linkage (minimum bar)** | Each artifact notes the record ID; each legacy record holds the commit SHA | A starting point; accepts two sources for now |

Coexistence is fine as long as the two are linked or one is declared authoritative. Put the record ID in the artifact's `source` field.

## Human judgment stays above the loop

Automation changes where people spend attention, not who is accountable. Humans remain accountable for: whether the problem is worth solving, whether the solution is acceptable, whether the risk of a change is acceptable, and whether to release. The loop makes those decisions faster to reach and better evidenced; it does not make them.
