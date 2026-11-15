#!/usr/bin/env python3
"""Scaffold and inspect an AI-native SDLC layout in a repository.

    sdlc.py init   <repo> [--with hooks,agents,evals,ci,ops] [--all] [--dry-run]
    sdlc.py new    <repo> "<title>" [--slug s] [--author a] [--source ref]
    sdlc.py add    <repo> <change-id> spec|plan [--author a]
    sdlc.py status <repo> [--json]

Standard library only. `init`, `new` and `add` never overwrite an existing file.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import stat
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "assets" / "templates"
REPO_TEMPLATES = TEMPLATES / "repo"
CHANGE_TEMPLATES = TEMPLATES / "change"

# Template folders are stored without the leading dot so that tools scanning the
# skill folder never mistake them for live configuration.
RENAMES = {"dot-claude": ".claude", "dot-github": ".github"}

# Which template paths (relative to assets/templates/repo) belong to which component.
COMPONENTS = {
    "core": ["CLAUDE.md", "REVIEW.md", "intent/"],
    "hooks": [
        "dot-claude/settings.json",
        "dot-claude/hooks/",
        "dot-claude/protected-paths.txt",
        "dot-claude/locked-tests.txt",
    ],
    "agents": ["dot-claude/agents/"],
    "evals": ["evals/", "dot-github/workflows/agent-evals.yml"],
    "ci": ["dot-github/workflows/ci-triage.yml"],
    "ops": ["ops/"],
}
OPTIONAL = [c for c in COMPONENTS if c != "core"]

ARTIFACTS = ["intent", "spec", "plan"]
CLOSED = {"rejected", "superseded"}


# --------------------------------------------------------------------------- helpers

def die(msg: str) -> "None":
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def repo_path(arg: str) -> Path:
    p = Path(arg).expanduser().resolve()
    if not p.is_dir():
        die(f"{p} is not a directory")
    return p


def dest_for(rel: Path) -> Path:
    parts = [RENAMES.get(part, part) for part in rel.parts]
    return Path(*parts)


def template_files(prefixes: list[str]) -> list[Path]:
    out: list[Path] = []
    for prefix in prefixes:
        src = REPO_TEMPLATES / prefix
        if prefix.endswith("/"):
            out.extend(sorted(p for p in src.rglob("*") if p.is_file()))
        elif src.is_file():
            out.append(src)
    return [p for p in out if "__pycache__" not in p.parts]


def read_header(path: Path) -> dict[str, str]:
    """Read the simple `key: value` header at the top of an artifact."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", text, re.DOTALL)
    if not m:
        return {}
    header: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        value = value.split(" #", 1)[0].strip().strip("\"'")
        header[key.strip()] = value
    return header


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return "-".join(slug.split("-")[:6])[:48].strip("-")


def fill(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


# ------------------------------------------------------------------------------ init

def cmd_init(args: argparse.Namespace) -> int:
    repo = repo_path(args.repo)
    wanted = ["core"]
    if args.all:
        wanted += OPTIONAL
    elif args.with_:
        for name in (n.strip() for n in args.with_.split(",") if n.strip()):
            if name not in OPTIONAL:
                die(f"unknown component '{name}'. Choose from: {', '.join(OPTIONAL)}")
            wanted.append(name)

    created: list[str] = []
    skipped: list[str] = []
    notes: list[str] = []

    for component in wanted:
        for src in template_files(COMPONENTS[component]):
            rel = dest_for(src.relative_to(REPO_TEMPLATES))
            dest = repo / rel
            if dest.exists():
                if rel.as_posix() == ".claude/settings.json":
                    alt = repo / ".claude" / "settings.sdlc-example.json"
                    if not alt.exists():
                        if not args.dry_run:
                            alt.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copyfile(src, alt)
                        created.append(alt.relative_to(repo).as_posix())
                    notes.append(
                        ".claude/settings.json already exists. The hook wiring was written to "
                        ".claude/settings.sdlc-example.json: merge its 'hooks' and 'permissions' "
                        "entries by hand."
                    )
                else:
                    skipped.append(rel.as_posix())
                continue
            if not args.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dest)
                if dest.suffix in {".py", ".sh"}:
                    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            created.append(rel.as_posix())

    label = "would create" if args.dry_run else "created"
    print(f"Components: {', '.join(wanted)}")
    for path in created:
        print(f"  {label}  {path}")
    for path in skipped:
        print(f"  kept     {path} (already exists)")
    for note in notes:
        print(f"note: {note}")

    print("\nNext:")
    print("  1. Open CLAUDE.md and replace every TODO(...) with facts from this repo.")
    print("     Run each command once before writing it down.")
    if "hooks" in wanted:
        print("  2. List the paths that must not be edited in .claude/protected-paths.txt,")
        print("     then test a hook: echo '{\"tool_input\":{\"file_path\":\"<path>\"}}' | \\")
        print("       python3 .claude/hooks/protect_paths.py")
    print("  -  Start the first change:  sdlc.py new <repo> \"<title>\"")
    return 0


# ------------------------------------------------------------------------- new / add

def write_artifact(repo: Path, change_id: str, kind: str, values: dict[str, str]) -> Path:
    dest = repo / "intent" / change_id / f"{kind}.md"
    if dest.exists():
        die(f"{dest.relative_to(repo)} already exists")
    template = (CHANGE_TEMPLATES / f"{kind}.md").read_text(encoding="utf-8")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(fill(template, values), encoding="utf-8")
    return dest


def cmd_new(args: argparse.Namespace) -> int:
    repo = repo_path(args.repo)
    today = _dt.date.today().isoformat()
    slug = slugify(args.slug or args.title) or "change"
    change_id = f"{today}-{slug}"
    n = 2
    while (repo / "intent" / change_id).exists():
        change_id = f"{today}-{slug}-{n}"
        n += 1
    dest = write_artifact(repo, change_id, "intent", {
        "ID": change_id,
        "TITLE": args.title,
        "AUTHOR": args.author or "",
        "DATE": today,
        "SOURCE": args.source or "conversation",
    })
    print(f"created {dest.relative_to(repo).as_posix()}")
    print("Fill it in with the requester, read it back to them, then commit it.")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    repo = repo_path(args.repo)
    change_dir = repo / "intent" / args.change
    if not change_dir.is_dir():
        die(f"no such change: intent/{args.change}")
    order = {"spec": "intent", "plan": "spec"}
    previous = change_dir / f"{order[args.kind]}.md"
    if previous.exists():
        status = read_header(previous).get("status", "")
        if status != "accepted":
            print(
                f"warning: {previous.name} is '{status or 'missing a status'}', not accepted. "
                f"The gate before {args.kind}.md has not been passed.",
                file=sys.stderr,
            )
    intent_header = read_header(change_dir / "intent.md")
    dest = write_artifact(repo, args.change, args.kind, {
        "ID": args.change,
        "TITLE": intent_header.get("title", args.change),
        "AUTHOR": args.author or "",
        "DATE": _dt.date.today().isoformat(),
        "SOURCE": intent_header.get("source", ""),
    })
    print(f"created {dest.relative_to(repo).as_posix()}")
    return 0


# ---------------------------------------------------------------------------- status

def next_step(states: dict[str, str | None]) -> str:
    intent, spec, plan = states["intent"], states["spec"], states["plan"]
    if any(s in CLOSED for s in states.values() if s):
        return "Closed (rejected or superseded)"
    if plan == "accepted":
        return "Stage 3-5: build, verify, open a PR for review"
    if plan is not None:
        return "GATE: plan.md needs accepting before the first edit"
    if spec == "accepted":
        return "Stage 3: write plan.md"
    if spec is not None:
        return "GATE: owner reviews and accepts spec.md"
    if intent == "accepted":
        return "Stage 2: write spec.md (or plan.md directly for a small change)"
    if intent is not None:
        return "GATE: owner reviews and accepts intent.md"
    return "Stage 1: write intent.md"


def readiness(repo: Path) -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []
    claude_md = repo / "CLAUDE.md"
    if claude_md.exists():
        text = claude_md.read_text(encoding="utf-8", errors="replace")
        todos = len(re.findall(r"TODO\(", text))
        lines = len(text.splitlines())
        detail = f"{lines} lines"
        if todos:
            detail += f", {todos} placeholder(s) still to fill in"
        elif lines > 80:
            detail += " (long: aim for under a page)"
        checks.append(("CLAUDE.md", todos == 0, detail))
    else:
        checks.append(("CLAUDE.md", False, "missing"))

    runner = [n for n in ("Makefile", "package.json", "pyproject.toml", "justfile",
                          "Cargo.toml", "go.mod", "pom.xml", "build.gradle")
              if (repo / n).exists()]
    checks.append(("One-command build/test", bool(runner),
                   ", ".join(runner) if runner else "no build or package file found"))
    checks.append(("intent/ folder", (repo / "intent").is_dir(), ""))
    checks.append(("REVIEW.md", (repo / "REVIEW.md").exists(), ""))

    settings = repo / ".claude" / "settings.json"
    hooks = False
    if settings.exists():
        try:
            hooks = bool(json.loads(settings.read_text(encoding="utf-8")).get("hooks"))
        except (ValueError, OSError):
            hooks = False
    checks.append(("Hooks (.claude/settings.json)", hooks, ""))
    skills = repo / ".claude" / "skills"
    n_skills = len(list(skills.glob("*/SKILL.md"))) if skills.is_dir() else 0
    checks.append(("Policy skills (.claude/skills)", n_skills > 0, f"{n_skills} found"))
    agents = repo / ".claude" / "agents"
    n_agents = len(list(agents.glob("*.md"))) if agents.is_dir() else 0
    checks.append(("Subagents (.claude/agents)", n_agents > 0, f"{n_agents} found"))
    cases = repo / "evals" / "cases"
    n_cases = len(list(cases.glob("*.json"))) if cases.is_dir() else 0
    checks.append(("Evals (evals/cases)", n_cases > 0, f"{n_cases} case(s)"))
    checks.append(("Monitoring bands (ops/bands.json)", (repo / "ops" / "bands.json").exists(), ""))
    return checks


def cmd_status(args: argparse.Namespace) -> int:
    repo = repo_path(args.repo)
    changes = []
    intent_dir = repo / "intent"
    if intent_dir.is_dir():
        for d in sorted(p for p in intent_dir.iterdir() if p.is_dir()):
            if d.name.startswith((".", "_")):
                continue
            states: dict[str, str | None] = {}
            title = d.name
            for kind in ARTIFACTS:
                f = d / f"{kind}.md"
                if f.exists():
                    header = read_header(f)
                    states[kind] = header.get("status") or "no-status"
                    title = header.get("title") or title
                else:
                    states[kind] = None
            changes.append({"id": d.name, "title": title, **states, "next": next_step(states)})

    ready = readiness(repo)
    if args.json:
        print(json.dumps({
            "repo": str(repo),
            "readiness": [{"check": c, "ok": ok, "detail": d} for c, ok, d in ready],
            "changes": changes,
        }, indent=2, ensure_ascii=False))
        return 0

    print(f"Repository: {repo}\n")
    print("Setup")
    for check, ok, detail in ready:
        mark = "yes" if ok else "no "
        print(f"  [{mark}] {check}" + (f": {detail}" if detail else ""))

    print("\nChanges")
    if not changes:
        print("  none yet. Start one with: sdlc.py new <repo> \"<title>\"")
    for c in changes:
        print(f"  {c['id']}: {c['title']}")
        parts = [f"{k}={c[k] or '-'}" for k in ARTIFACTS]
        print(f"      {'  '.join(parts)}")
        print(f"      next: {c['next']}")
    return 0


# ------------------------------------------------------------------------------ main

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="install the layout and templates (never overwrites)")
    p.add_argument("repo")
    p.add_argument("--with", dest="with_", default="", help=f"comma list: {','.join(OPTIONAL)}")
    p.add_argument("--all", action="store_true", help="install every component")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("new", help="start a change: create intent/<date>-<slug>/intent.md")
    p.add_argument("repo")
    p.add_argument("title")
    p.add_argument("--slug", help="short ASCII name for the folder (needed for non-Latin titles)")
    p.add_argument("--author")
    p.add_argument("--source", help="ticket, incident or conversation reference")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("add", help="add spec.md or plan.md to an existing change")
    p.add_argument("repo")
    p.add_argument("change")
    p.add_argument("kind", choices=["spec", "plan"])
    p.add_argument("--author")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("status", help="show setup readiness and where every change stands")
    p.add_argument("repo")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_status)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
