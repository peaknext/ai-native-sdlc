#!/usr/bin/env python3
"""PostToolUse hook for Edit / Write: format and lint the one file that just changed.

Running the formatter after every edit means style drift never builds up, and review
comments are about substance. It only touches the changed file, so it stays fast.

Nothing runs until you fill in FORMATTERS for this project. `{file}` is replaced by
the path of the edited file. If a command fails, its output is passed back to the
agent so it can fix the problem straight away.
"""

import json
import shlex
import subprocess
import sys
from pathlib import Path

FORMATTERS = {
    # ".py":  ["ruff format {file}", "ruff check --fix {file}"],
    # ".ts":  ["npx prettier --write {file}", "npx eslint --fix {file}"],
    # ".tsx": ["npx prettier --write {file}", "npx eslint --fix {file}"],
    # ".go":  ["gofmt -w {file}"],
}


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    target = (payload.get("tool_input") or {}).get("file_path")
    if not target:
        sys.exit(0)
    path = Path(target)
    commands = FORMATTERS.get(path.suffix)
    if not commands or not path.exists():
        sys.exit(0)

    failures = []
    for template in commands:
        cmd = [part.replace("{file}", str(path)) for part in shlex.split(template)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                                    cwd=payload.get("cwd") or None)
        except (OSError, subprocess.SubprocessError) as exc:
            failures.append(f"$ {template}\n{exc}")
            continue
        if result.returncode != 0:
            failures.append(f"$ {template}\n{(result.stdout + result.stderr).strip()[-2000:]}")

    if failures:
        print("Formatter or linter reported problems in the file you just edited:\n\n"
              + "\n\n".join(failures), file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
