# Stage 6: Maintain - close the loop

Traditional maintenance is reactive: an alert at 3 a.m. is missed, tickets sit in the backlog, post-mortem actions never reach the codebase. Here a trigger (a breached control band, a ticket, a chat message, a schedule) invokes the agent with no person in the starting path. The agent diagnoses, acts only through gated routes, and writes its findings as `intent.md`. People triage and review instead of starting the work.

Between stages of a headless run there is an **independent confidence gate**: deterministic checks, or a separate reviewing agent whose job is to find fault, decide whether the run continues or escalates to a person.

Contents:
1. Monitoring bands and response tiers
2. Recurring codebase scans
3. Incidents that arrive in chat, and post-mortems

## 1. Monitoring bands and response tiers

**Needs first:** `intent.md` as a structured output (Stage 1); fast PR review (Stage 5); hooks as the action boundary; a rehearsed rollback path (used by the highest tier).

**Infrastructure:** a metrics store the detection script can query (Prometheus, a CI API, ...); read access to the repo; a way to run the agent non-interactively (a CI step, or a small webhook service built on the Agent SDK).

Steps:

1. **Pick one metric with a stable rolling baseline:** CI test-failure rate, post-deploy 5xx rate, PR cycle time. Start with one.
2. **Write the detection deterministically.** No model involved: a rolling mean and standard deviation over a window, with run rules (the Western Electric rules are a common choice) so the bands catch slow drift as well as spikes. Version-control it and unit-test it. Detection must be boring and predictable; judgment comes after.
3. **Define response tiers in version-controlled config:**

   | Breach | What happens | What the agent may do |
   |---|---|---|
   | 1 sigma | Log only | Nothing |
   | 2 sigma | Diagnose | Read-only tools: read code, search, view CI runs |
   | 3 sigma | Propose or act | Only by opening a PR into the review gate, or triggering a pre-approved runbook such as rollback |

4. **Trigger it:** a scheduled CI workflow, a webhook from monitoring, or a cron job inside the network. The agent runs stateless, in a sandboxed container.
5. **The agent writes its diagnosis as `intent.md`** in the Stage 1 format, with "anomaly and evidence" in place of "problem": what was observed, the data, the proposed outcome, affected systems, open questions.
6. **A human triages:** fix now, schedule, or dismiss. The service owner or on-call engineer decides; product-facing findings go to the product owner. Dismissals are information too: use them to tune the bands.
7. **When the fix ships, add an eval for the incident** (see `4-test.md`), so the same class of problem is caught before production next time.

Templates (installed by `sdlc.py init --with ops`): `ops/bands.json` (metric, baseline window, tiers) and `ops/detect_bands.py` (rolling baseline plus Western Electric rules; prints the tier as JSON for the pipeline to act on).

Three illustrations of the tiers at work:

- CI test-failure rate breaches 3 sigma: the agent quarantines the flaky test or opens a revert PR, and the review gate decides.
- Post-deploy 5xx rate breaches 3 sigma with a deployment inside the window: the agent triggers the existing, pre-approved rollback pipeline.
- PR cycle time trips a drift rule: the agent writes a report for engineering leadership. The same harness works for process metrics.

Governance: tier boundaries are enforced from version-controlled config; permissions and managed settings deny production access; invocations, findings and triage decisions are logged with timestamps; every change goes through the normal PR gate; runbooks the agent may trigger are approved in advance.

What to measure:
- **Leading:** time from band breach to an `intent.md` in the triage queue, against the old time from incident to post-mortem action.
- **Lagging:** share of findings that become merged fixes; repeat incidents of the same class (should fall as evals accumulate).

## 2. Recurring codebase scans

A security scan is a statement about one moment. It goes stale as the code changes, and each new model generation finds issues earlier ones missed. So scans are scheduled, nobody has to remember to start them, and findings go through the same gates as any other change.

**Needs first:** the PR review gate and approval-gate hooks (Stage 5); the `intent.md` format (Stage 1) for findings too large for one PR.

Steps:

1. **Connect the repos** and group them by service or team.
2. **Run a first full scan of the most critical repos,** including ones scanned before by other tools or older models. Treat the result as the baseline; expect findings in code that was thought clean.
3. **Set a schedule per group.** Weekly is a reasonable default for active services. Scope to a directory or branch where repos are large or mixed.
4. **Triage using the confidence rating.** Dismiss with a written reason, so the dismissal is on record and does not come back as "new".
5. **A bounded finding gets a patch through the PR review gate.** The agent that proposed the patch cannot approve it.
6. **A wider issue** (an architectural weakness, a pattern across services) becomes an `intent.md` and starts at Plan.
7. **Once a fix ships, add an eval for that class of vulnerability.**
8. **Export findings** to the existing tracker and audit systems, which stay the system of record.

A hosted product for this exists (Claude Security, in public beta for Claude Enterprise at the time the source article was written). Availability and requirements change, so check the current product page before recommending it. Model-driven scans add to static analysis and dependency scanning; they do not replace them. Deterministic checks stay in CI; the scan covers the context-dependent problems those checks miss.

Governance: admins control which repos are connected, who may run scans, and the spend limit. Each finding carries a validation result and a confidence rating, each dismissal a reason; the scan history is an audit record of what was found, fixed and consciously accepted.

What to measure:
- **Leading:** share of connected repos on a schedule; time from a finding being reported to its patch entering review.
- **Lagging:** vulnerabilities found by scans versus found in production or reported externally; findings per scan on repos with several runs (should fall).

## 3. Incidents in chat, and post-mortems

Incidents also arrive as a message in a team channel at 10 p.m. An agent that is a member of the incident channel under its own identity (Claude Tag does this in Slack; public beta at the time the source article was written) gives every incident a first responder:

- The conversation and the knowledge stay in the channel, where anyone can steer.
- People test hypotheses with the agent in real time.
- After the fix, the agent verifies the metric is back at baseline and says so in the thread.
- Small, bounded fixes arrive as PRs through the review gate. Larger work becomes an `intent.md` for Stage 1.
- The channel history is the audit trail: request, diagnosis, human authorisation and fix, all in one place.

### Post-mortem

Whether or not a chat agent is involved, every incident ends with a written record in version control, so future investigations can read it. Use `assets/templates/repo/ops/incident-template.md`:

1. **What happened**, in plain language, with the timeline.
2. **Impact:** who was affected, for how long.
3. **Cause:** the technical cause and the reason it was not caught earlier.
4. **What fixed it** and how recovery was verified.
5. **What changes** so it does not recur: the regression test or eval that was added, the `CLAUDE.md` line, the hook, the band that was tuned.
6. **Follow-up intent:** a link to the new `intent.md` if the real fix is bigger than the patch.

Add a short entry to `ops/lessons.md`. A lessons file that agents read at the start of an investigation is how the organisation stops rediscovering the same cause.

## Common mistakes

- Putting a model in the detection path, so alerts become unpredictable.
- Letting the highest tier act directly on production instead of through a PR or an approved runbook.
- Fixing the incident and skipping the eval, which guarantees a repeat.
- Dismissing findings without a reason, so the same finding is re-triaged every week.
