#!/usr/bin/env python3
"""Run the agent eval suite: each case in a throwaway git worktree, then its checks.

    python3 evals/run_evals.py [--threshold 0.9] [--only NAME] [--timeout 900]

Exit code 0 if the pass rate meets the threshold, 1 otherwise. Results are written
to evals/results/. Standard library only.

The agent is started with:  claude -p <prompt> --allowedTools <case.allowed_tools>
                            --permission-mode acceptEdits --output-format json
Set SDLC_EVAL_AGENT_CMD to a shell command to use something else (it receives the
prompt in $EVAL_PROMPT and runs in the worktree); handy for testing the harness.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def sh(cmd, cwd, timeout=None, env=None, shell=False):
    return subprocess.run(cmd, cwd=cwd, timeout=timeout, env=env, shell=shell,
                          capture_output=True, text=True)


def run_agent(case, worktree, timeout):
    override = os.environ.get("SDLC_EVAL_AGENT_CMD")
    env = dict(os.environ, EVAL_PROMPT=case["prompt"])
    if override:
        return sh(override, worktree, timeout, env, shell=True)
    cmd = ["claude", "-p", case["prompt"],
           "--allowedTools", case.get("allowed_tools", "Read,Grep,Glob"),
           "--permission-mode", "acceptEdits",
           "--output-format", "json"]
    return sh(cmd, worktree, timeout, env)


def run_case(case, timeout):
    name = case["name"]
    result = {"name": name, "passed": False, "checks": [], "error": None}
    tmp = Path(tempfile.mkdtemp(prefix=f"eval-{name}-"))
    worktree = tmp / "wt"
    started = time.time()
    try:
        added = sh(["git", "worktree", "add", "--detach", str(worktree),
                    case.get("base_ref", "HEAD")], REPO)
        if added.returncode != 0:
            result["error"] = f"could not create worktree: {added.stderr.strip()}"
            return result
        try:
            agent = run_agent(case, worktree, timeout)
        except subprocess.TimeoutExpired:
            result["error"] = f"agent timed out after {timeout}s"
            return result
        except FileNotFoundError:
            result["error"] = "the 'claude' command was not found"
            return result
        result["agent_exit_code"] = agent.returncode
        result["agent_output_tail"] = agent.stdout[-4000:]
        if agent.returncode != 0:
            result["error"] = f"agent exited {agent.returncode}: {agent.stderr.strip()[-500:]}"
            return result

        all_ok = True
        for check in case.get("checks", []):
            try:
                done = sh(check, worktree, 600, shell=True)
                ok = done.returncode == 0
                tail = (done.stdout + done.stderr).strip()[-1500:]
            except subprocess.TimeoutExpired:
                ok, tail = False, "check timed out"
            result["checks"].append({"command": check, "passed": ok, "output_tail": tail})
            all_ok = all_ok and ok
        result["passed"] = all_ok and bool(case.get("checks"))
        if not case.get("checks"):
            result["error"] = "case has no checks, so it cannot pass"
        return result
    finally:
        result["seconds"] = round(time.time() - started, 1)
        sh(["git", "worktree", "remove", "--force", str(worktree)], REPO)
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--threshold", type=float, default=1.0,
                        help="minimum pass rate, 0 to 1 (default 1.0)")
    parser.add_argument("--only", help="run a single case by name")
    parser.add_argument("--timeout", type=int, default=900, help="seconds per agent run")
    args = parser.parse_args()

    cases = []
    for path in sorted((HERE / "cases").glob("*.json")):
        try:
            case = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            print(f"error: {path.name} is not valid JSON: {exc}", file=sys.stderr)
            return 1
        for key in ("name", "prompt"):
            if key not in case:
                print(f"error: {path.name} has no '{key}'", file=sys.stderr)
                return 1
        if not args.only or case["name"] == args.only:
            cases.append(case)

    if not cases:
        print("No eval cases found in evals/cases/*.json. Nothing to run.")
        return 0

    results = []
    for case in cases:
        print(f"- {case['name']} ... ", end="", flush=True)
        result = run_case(case, args.timeout)
        results.append(result)
        print("pass" if result["passed"] else f"FAIL ({result['error'] or 'a check failed'})")
        for check in result["checks"]:
            if not check["passed"]:
                print(f"    failed check: {check['command']}")

    passed = sum(r["passed"] for r in results)
    rate = passed / len(results)
    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    summary = {"passed": passed, "total": len(results), "pass_rate": round(rate, 3),
               "threshold": args.threshold, "results": results}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\nPass rate: {passed}/{len(results)} = {rate:.0%} (threshold {args.threshold:.0%})")
    return 0 if rate >= args.threshold else 1


if __name__ == "__main__":
    sys.exit(main())
