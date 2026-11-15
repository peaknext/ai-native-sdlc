#!/usr/bin/env python3
"""Check what the guardrail hooks decide, without starting an agent session.

    python3 .claude/hooks/check_guardrails.py                    run every check in the list
    python3 .claude/hooks/check_guardrails.py edit <path>        what happens to one edit
    python3 .claude/hooks/check_guardrails.py bash "<command>"   what happens to one command

It reads .claude/settings.json, hands each matching PreToolUse hook the same JSON the
agent's tool call would send, and reports ALLOW, ASK or BLOCK with the reason shown.

The list of expected outcomes is .claude/guardrail-checks.txt, one per line:

    block  edit  src/generated/client.js
    allow  bash  npm test

Run with no arguments it exits 1 if any outcome differs from what the list expects, so
it can sit in the test suite or CI and fail when someone weakens a guardrail.

Limits: only hooks are exercised. `permissions` rules in settings.json are applied by
the tool itself and are not simulated here, and nothing replaces watching a real
session refuse the action once.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKS = ROOT / ".claude" / "guardrail-checks.txt"
TOOLS = {"edit": "Edit", "write": "Write", "bash": "Bash"}


def decide(kind, argument, settings):
    """Return (verdict, reason): the strongest decision among the matching hooks."""
    tool = TOOLS[kind]
    if kind == "bash":
        tool_input = {"command": argument}
    else:
        path = Path(argument)
        tool_input = {"file_path": str(path if path.is_absolute() else ROOT / path)}
        tool_input.update({"content": ""} if kind == "write" else {"old_string": "", "new_string": ""})
    payload = json.dumps({"session_id": "guardrail-check", "hook_event_name": "PreToolUse",
                          "tool_name": tool, "tool_input": tool_input, "cwd": str(ROOT),
                          "permission_mode": "default"})
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(ROOT))
    env.pop("RELEASE_APPROVAL", None)  # check the state in which nobody has approved

    def expand(text):
        return re.sub(r"\$\{?(\w+)\}?", lambda m: env.get(m.group(1), m.group(0)), text)

    verdict, reason = "allow", ""
    for group in (settings.get("hooks") or {}).get("PreToolUse", []):
        matcher = group.get("matcher", "")
        if matcher not in ("", "*") and not re.fullmatch(matcher, tool):
            continue
        for hook in group.get("hooks", []):
            if hook.get("type") != "command":
                continue
            command = hook["command"]
            use_shell = "args" not in hook
            if not use_shell:
                command = [expand(command)] + [expand(a) for a in hook["args"]]
            try:
                done = subprocess.run(command, shell=use_shell, input=payload, env=env, cwd=ROOT,
                                      capture_output=True, text=True, timeout=30)
            except (OSError, subprocess.SubprocessError) as exc:
                return "error", f"hook could not run: {exc}"
            decision = None
            try:
                decision = json.loads(done.stdout)["hookSpecificOutput"]["permissionDecision"]
                why = json.loads(done.stdout)["hookSpecificOutput"].get("permissionDecisionReason", "")
            except (ValueError, KeyError, TypeError):
                why = ""
            if done.returncode == 2 or decision == "deny":
                return "block", (done.stderr.strip() or why)
            if done.returncode != 0:
                return "error", f"hook exited {done.returncode}: {done.stderr.strip()[-300:]}"
            if decision == "ask":
                verdict, reason = "ask", why
    return verdict, reason


def main():
    settings_path = ROOT / ".claude" / "settings.json"
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"cannot read {settings_path}: {exc}", file=sys.stderr)
        return 1

    args = sys.argv[1:]
    if args:
        if len(args) < 2 or args[0] not in TOOLS:
            print(__doc__)
            return 1
        verdict, reason = decide(args[0], " ".join(args[1:]), settings)
        print(verdict.upper() + (f"\n{reason}" if reason else ""))
        return 0 if verdict != "error" else 1

    if not CHECKS.exists():
        print(f"no checks listed: {CHECKS.relative_to(ROOT)} does not exist")
        return 1
    failed = total = 0
    for raw in CHECKS.read_text(encoding="utf-8").splitlines():
        line = raw.split(" #", 1)[0].strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) != 3 or parts[0] not in ("allow", "ask", "block") or parts[1] not in TOOLS:
            print(f"skipped (expected: allow|ask|block  edit|bash  argument): {raw}")
            continue
        expected, kind, argument = parts
        verdict, reason = decide(kind, argument, settings)
        total += 1
        ok = verdict == expected
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {expected:5s} {kind:4s} {argument}"
              + ("" if ok else f"\n       got {verdict.upper()}: {reason.splitlines()[0] if reason else ''}"))
    print(f"\n{total - failed}/{total} guardrail checks passed")
    return 1 if failed or not total else 0


if __name__ == "__main__":
    sys.exit(main())
