#!/usr/bin/env python3
"""PreToolUse hook for Edit / Write: guard protected paths and locked tests.

Reads two plain-text lists in .claude/:

  protected-paths.txt   lines of:  block|ask  <pattern>  # reason and who can approve
  locked-tests.txt      one pattern per line: tests that must not be edited during a fix

Patterns are matched against the path relative to the repo root; `*` also matches
across folders, so `src/gen/*` covers everything beneath src/gen.

Decisions:  block -> exit 2 (the reason on stderr is shown to the agent)
            ask   -> a person is asked to approve this one edit
            otherwise no opinion, and the normal permission flow continues.

Test it:  echo '{"tool_input":{"file_path":"src/gen/a.py"}}' | python3 protect_paths.py
"""

import fnmatch
import json
import os
import sys
from pathlib import Path

LOCK_FILE = ".claude/locked-tests.txt"
RULES_FILE = ".claude/protected-paths.txt"


def lines(path):
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def matches(rel, pattern):
    pattern = pattern.strip().rstrip("/")
    if not pattern:
        return False
    return rel == pattern or fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(rel, pattern + "/*")


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


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)  # not our input format: stay out of the way

    tool_input = payload.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not target:
        sys.exit(0)

    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()).resolve()
    path = Path(target)
    if not path.is_absolute():
        path = root / path
    try:
        rel = path.resolve().relative_to(root).as_posix()
    except ValueError:
        sys.exit(0)  # outside this repo

    locked = [l.split("#", 1)[0].strip() for l in lines(root / LOCK_FILE)]
    locked = [l for l in locked if l]

    for pattern in locked:
        if matches(rel, pattern):
            block(
                f"Blocked: {rel} is a locked test ({LOCK_FILE}).\n"
                "This is a fix task: make the test pass by changing the code, not the test.\n"
                "If the test itself is wrong, stop and explain why to the person you are working "
                "with; they can unlock it."
            )

    if rel == LOCK_FILE and locked:
        ask(
            f"{LOCK_FILE} currently locks {len(locked)} test pattern(s). Changing it unlocks "
            "tests during a fix. Approve only if the fix is finished or the test was wrong."
        )

    decision = None
    for raw in lines(root / RULES_FILE):
        rule, _, reason = raw.partition("#")
        parts = rule.split()
        if len(parts) != 2 or parts[0] not in ("block", "ask"):
            continue
        mode, pattern = parts
        if matches(rel, pattern):
            if mode == "block":
                block(
                    f"Blocked: {rel} is a protected path ({RULES_FILE}: {pattern}).\n"
                    f"Reason: {reason.strip() or 'not given'}\n"
                    "Do not work around this. Say what you needed to change and why, so the "
                    "owner of this path can decide."
                )
            decision = decision or (pattern, reason.strip())

    if decision:
        pattern, reason = decision
        ask(f"{rel} matches protected pattern '{pattern}'. {reason or 'Needs approval.'}")

    sys.exit(0)


if __name__ == "__main__":
    main()
