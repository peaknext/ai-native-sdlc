# evals/

Regression tests for the agent's own setup. Each case is a real task with a known good
outcome. The suite answers one question: after a change to `CLAUDE.md`, a skill, a hook,
a prompt or the model, does the agent still do our work to our standard?

## Layout

```
evals/
  cases/            one JSON file per case (files ending .sample are ignored)
  run_evals.py      runs every case in a throwaway copy of the repo and checks the result
  results/          written by the runner; do not commit
```

## A case

```json
{
  "name": "fix-rounding-in-invoice-total",
  "description": "Real bug from March: totals were rounded per line instead of once.",
  "base_ref": "a1b2c3d",
  "prompt": "Invoice totals are off by a cent for some orders. Find and fix the cause.",
  "allowed_tools": "Read,Edit,Write,Grep,Glob,Bash(make test *)",
  "checks": [
    "make test",
    "git diff --quiet a1b2c3d -- tests/"
  ]
}
```

- `base_ref`: the commit the task starts from (the state of the repo before the fix).
- `checks`: shell commands run after the agent finishes. Every one must exit 0.
  The second check above fails if the agent edited existing tests.

## Running

```bash
python3 evals/run_evals.py                    # all cases
python3 evals/run_evals.py --threshold 0.9    # fail unless at least 90% pass
python3 evals/run_evals.py --only fix-rounding-in-invoice-total
```

These are real, billed model runs. In CI, `.github/workflows/agent-evals.yml` runs the
suite nightly and on any pull request that touches the agent's configuration.

## Keeping it useful

- Start with 20 to 50 recent, real tasks.
- Add a case for every production incident, and keep it.
- Retire cases every configuration passes; they no longer tell you anything.
