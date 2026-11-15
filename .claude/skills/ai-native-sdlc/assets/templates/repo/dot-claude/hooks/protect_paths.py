#!/usr/bin/env python3
"""PreToolUse hook for Edit / Write / Bash: guard protected paths and locked tests.

Reads two plain-text lists in .claude/:

  protected-paths.txt   lines of:  block|ask  <pattern>  # reason and who can approve
  locked-tests.txt      one pattern per line: tests that must not be edited during a fix

Patterns are matched against the path relative to the repo root; `*` also matches
across folders, so `src/gen/*` covers everything beneath src/gen.

Decisions:  block -> exit 2 (the reason on stderr is shown to the agent)
            ask   -> a person is asked to approve this one action
            otherwise no opinion, and the normal permission flow continues.

Edit and Write are judged exactly, by file path. A Bash command has no file path, so
its text is checked instead: it counts as an edit when one part of it both names a
listed path and changes files (rm, mv, cp, sed -i, an output redirect, an interpreter
one-liner, ...). That is pattern matching. It catches the usual forms; it cannot catch
a script or a wildcard that changes files without naming them. For a rule that must
hold with certainty, add a `permissions.deny` rule in settings.json and a CI check too.

Try it:   python3 .claude/hooks/check_guardrails.py edit src/gen/a.py
          python3 .claude/hooks/check_guardrails.py bash "rm src/gen/a.py"
"""

import fnmatch
import json
import os
import re
import sys
from pathlib import Path

LOCK_FILE = ".claude/locked-tests.txt"
RULES_FILE = ".claude/protected-paths.txt"

# What "changes files" looks like inside one shell command.
SHELL_WRITES = [
    r"(?:^|[\s;&|(`])(?:rm|rmdir|unlink|mv|cp|touch|truncate|tee|dd|patch|rsync|install|chmod|chown)(?=\s|$)",
    r"\bsed\b[^|]*\s(?:-[a-zA-Z]*i|--in-place)",
    r"\bperl\b[^|]*\s-[a-zA-Z]*i",
    r"\bgit\s+(?:-\S+\s+)*(?:checkout|restore|apply|rm|mv|clean)\b",
    r"\b(?:python[0-9.]*|node|nodejs|deno|bun|ruby|perl)\b[^|]*\s(?:-c|-e|-p|--eval|--print)\b",
    r"\bfind\b[^|]*\s-(?:delete|exec|execdir)\b",
    r"(?<![0-9&=<>-])>{1,2}(?![&>=])(?!\s*/dev/null)",  # > file, >> file; not 2>&1 or =>
]


def lines(path):
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def matches(rel, pattern):
    pattern = pattern.strip().rstrip("/")
    if not pattern:
        return False
    return rel == pattern or fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(rel, pattern + "/*")


def names(text, pattern):
    """True if shell text mentions a path covered by the pattern."""
    base = pattern.strip().rstrip("/")
    while base.endswith("/*"):
        base = base[:-2]
    if not base:
        return False
    body = re.escape(base).replace(r"\*", r"[^\s'\";|&<>]*")
    return re.search(r"(?<![\w.-])" + body + r"(?![\w-])", text) is not None


def changes_files(part):
    return any(re.search(regex, part) for regex in SHELL_WRITES)


def shell_edits(command, pattern):
    """True if some part of a shell command would change a path covered by the pattern."""
    inside = False  # an earlier `cd` moved into the protected path
    for part in re.split(r"&&|\|\||;|\n", command):
        named = names(part, pattern)
        if named and re.match(r"[\s({]*(?:cd|pushd)\s", part):
            inside = True
            continue
        if (named or inside) and changes_files(part):
            return True
    return False


def checkout_root(start):
    """Nearest folder at or above `start` that holds .git: the checkout a path belongs to."""
    start = Path(start).resolve()
    for folder in [start, *start.parents]:
        if (folder / ".git").exists():
            return folder
    return None


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
    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
    if not isinstance(tool_input, dict):
        sys.exit(0)

    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    command = "" if target else (tool_input.get("command") or "")
    if not isinstance(target or command, str) or not (target or command):
        sys.exit(0)

    cwd = payload.get("cwd") or os.getcwd()
    # In a git worktree the work happens in another checkout of the same repo, while
    # CLAUDE_PROJECT_DIR may still point at the main one. Judge against both.
    roots = [Path(os.environ.get("CLAUDE_PROJECT_DIR") or cwd).resolve()]

    if target:
        path = Path(target)
        if not path.is_absolute():
            path = Path(cwd) / path
        path = path.resolve()
        checkout = checkout_root(path.parent)
        if checkout and checkout not in roots:
            roots.append(checkout)
        rels = [path.relative_to(r).as_posix() for r in roots if r in path.parents]
        if not rels:
            sys.exit(0)  # outside this repo
        what = f"editing {rels[-1]}"

        def hit(pattern):
            return any(matches(rel, pattern) for rel in rels)
    else:
        if not any(changes_files(part) for part in re.split(r"&&|\|\||;|\n", command)):
            sys.exit(0)  # nothing in the command changes files
        checkout = checkout_root(cwd)
        if checkout and checkout not in roots:
            roots.append(checkout)
        rels = []
        what = "this command"

        def hit(pattern):
            return shell_edits(command, pattern)

    def listed(name):
        seen = []
        for root in roots:
            for line in lines(root / name):
                if line not in seen:
                    seen.append(line)
        return seen

    shell_note = ("" if target else
                  "\nIf the command only reads that path, use a plain read (cat, grep) so it is "
                  "not mistaken for an edit.")

    locked = [l.split("#", 1)[0].strip() for l in listed(LOCK_FILE)]
    locked = [l for l in locked if l]
    for pattern in locked:
        if hit(pattern):
            block(
                f"Blocked: {what} would change a locked test ({LOCK_FILE}: {pattern}).\n"
                "This is a fix task: make the test pass by changing the code, not the test.\n"
                "If the test itself is wrong, stop and explain why to the person you are working "
                "with; they can unlock it." + shell_note
            )

    if locked and (LOCK_FILE in rels or (not target and shell_edits(command, LOCK_FILE))):
        ask(
            f"{LOCK_FILE} currently locks {len(locked)} test pattern(s). Changing it unlocks "
            "tests during a fix. Approve only if the fix is finished or the test was wrong."
        )

    pending = None
    for raw in listed(RULES_FILE):
        rule, _, reason = raw.partition("#")
        parts = rule.split()
        if len(parts) != 2 or parts[0] not in ("block", "ask"):
            continue
        mode, pattern = parts
        if not hit(pattern):
            continue
        if mode == "block":
            block(
                f"Blocked: {what} would change a protected path ({RULES_FILE}: {pattern}).\n"
                f"Reason: {reason.strip() or 'not given'}\n"
                "Do not work around this. Say what you needed to change and why, so the "
                "owner of this path can decide." + shell_note
            )
        pending = pending or (pattern, reason.strip())

    if pending:
        pattern, reason = pending
        ask(f"{what} would change a path matching protected pattern '{pattern}'. "
            f"{reason or 'Needs approval.'}")

    sys.exit(0)


if __name__ == "__main__":
    main()
