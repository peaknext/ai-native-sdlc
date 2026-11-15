#!/usr/bin/env python3
"""PreToolUse hook for Bash: the agent works up to the production gate, not past it.

  - A command that looks like a production deployment is BLOCKED unless a release
    approval is present in the environment (RELEASE_APPROVAL=<ticket or approver>).
  - A force-push to a protected branch is BLOCKED.
  - A direct push to a protected branch ASKS a person first (changes should arrive
    as pull requests).

This is a local safety net written with simple pattern matching. The real control is
outside this file: branch protection, your deployment platform's own approvals, and
production credentials that are not reachable from an agent session.
Edit the three settings below to match how this project deploys.

Try it:   python3 .claude/hooks/check_guardrails.py bash "make deploy ENV=production"
"""

import json
import os
import re
import shlex
import subprocess
import sys

# 1. What a production deployment looks like here (regular expressions, case-insensitive).
#    Each is tried against one command at a time, so that
#    `NODE_ENV=production make build && make deploy-staging` is not taken for one.
DEPLOY_PATTERNS = [
    r"\bdeploy\w*\b.*\bprod(uction)?\b",
    r"\bprod(uction)?\b.*\bdeploy\w*\b",
    r"\b(release|publish)\b.*\bprod(uction)?\b",
]
# 2. The environment variable that carries the release manager's approval.
APPROVAL_ENV = "RELEASE_APPROVAL"
# 3. Branches that only receive changes through pull requests.
PROTECTED_BRANCHES = {"main", "master", "production", "release"}

# Commands that only talk about text (a commit message, a search) and run nothing.
TEXT_ONLY = re.compile(r"\s*(?:git\s+(?:commit|log|show|diff|grep|tag)|grep|rg|cat|less|head|tail|ls)\b")


def block(message):
    print(message, file=sys.stderr)
    sys.exit(2)


def ask(message):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": message,
        }
    }))
    sys.exit(0)


def current_branch(cwd):
    try:
        out = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],  # also works before the first commit
            cwd=cwd or None, capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def pushed_branches(segment, cwd):
    """Branch names a `git push ...` command would update (best effort)."""
    try:
        tokens = shlex.split(segment)
    except ValueError:
        tokens = segment.split()
    if "push" not in tokens:
        return set(), False
    args = tokens[tokens.index("push") + 1:]
    force = any(a in ("-f", "--force") or a.startswith("--force-with-lease") or a.startswith("+")
                for a in args)
    positional = [a for a in args if not a.startswith("-")]
    refspecs = positional[1:]  # the first positional argument is the remote
    if not refspecs:
        branch = current_branch(cwd)
        return ({branch} if branch else set()), force
    targets = set()
    for ref in refspecs:
        target = ref.lstrip("+").split(":")[-1]
        targets.add(target.replace("refs/heads/", ""))
    return targets, force


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not command or not isinstance(command, str):
        sys.exit(0)

    for segment in re.split(r"&&|\|\||;|\n", command):
        text_only = TEXT_ONLY.match(segment) and "|" not in segment

        if not text_only and any(re.search(p, segment, re.IGNORECASE) for p in DEPLOY_PATTERNS):
            if not os.environ.get(APPROVAL_ENV, "").strip():
                block(
                    "Blocked: this looks like a production deployment and no release approval is "
                    f"present ({APPROVAL_ENV} is not set).\n"
                    "You may prepare the release (changelog, staging deploy, checks) but not "
                    "ship it.\n"
                    "Route to approval: tell the person you are working with that the release is "
                    "ready. The release manager either runs the deployment themselves, or starts "
                    f"the session or pipeline with {APPROVAL_ENV}=<change ticket or their name>.\n"
                    "Never split or disguise a deploy command to get past this check."
                )

        if re.search(r"\bgit\b.*\bpush\b", segment):
            targets, force = pushed_branches(segment, payload.get("cwd"))
            hit = sorted(targets & PROTECTED_BRANCHES)
            if not hit:
                continue
            if force:
                block(
                    f"Blocked: force-push to protected branch '{hit[0]}'. This rewrites shared "
                    "history. Open a pull request instead."
                )
            ask(
                f"This pushes directly to protected branch '{hit[0]}'. Changes normally arrive "
                "as pull requests so a code owner can review them. Approve only if that is "
                "intended."
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
