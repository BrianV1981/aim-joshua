#!/usr/bin/env python3
"""
aim projects — GitHub Projects (v2) board integration for J.O.S.H.U.A. agents.

Thin GitOps layer over `gh project` so agents share one kanban SoT:

  aim projects board
  aim projects board --status "In Progress"
  aim projects in-progress 206
  aim projects done 206
  aim projects ready 206
  aim projects blocked 206
  aim projects set 206 "In Progress"
  aim projects list
  aim projects doctor

Config (first match wins for each key):
  env  AIM_PROJECTS_OWNER / AIM_PROJECTS_NUMBER / AIM_PROJECTS_STATUS_FIELD / AIM_PROJECTS_REPO
  CONFIG.json settings.github_projects.{owner,number,status_field,repo}
  defaults: owner=@me, status_field=Status, number=required
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import Any, Optional


# Canonical agent aliases → preferred Status option name (fuzzy-matched)
STATUS_ALIASES = {
    "in-progress": ["In Progress", "In progress", "Doing", "Active", "Working"],
    "in_progress": ["In Progress", "In progress", "Doing", "Active", "Working"],
    "progress": ["In Progress", "In progress", "Doing", "Active"],
    "done": ["Done", "Complete", "Completed", "Closed", "Finished"],
    "complete": ["Done", "Complete", "Completed"],
    "todo": ["Todo", "To Do", "To do", "Backlog", "Ready", "Open"],
    "ready": ["Ready", "Todo", "To Do", "Backlog", "Open"],
    "backlog": ["Backlog", "Todo", "To Do", "Ready"],
    "blocked": ["Blocked", "Block", "On Hold", "Waiting", "Hold"],
}


def _eprint(*a: Any) -> None:
    print(*a, file=sys.stderr)


def _run_gh(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["gh"] + args
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=check)
    except FileNotFoundError:
        _eprint("[ERROR] GitHub CLI ('gh') is not installed.")
        sys.exit(1)


def _gh_json(args: list[str]) -> Any:
    proc = _run_gh(args + ["--format", "json"], check=False)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        if "project" in err.lower() and ("scope" in err.lower() or "403" in err or "401" in err):
            _eprint(
                "[ERROR] gh lacks Projects access. Run:\n"
                "  gh auth refresh -h github.com -s project,read:project\n"
                f"Detail: {err}"
            )
        else:
            _eprint(f"[ERROR] gh {' '.join(args)} failed:\n{err}")
        sys.exit(proc.returncode or 1)
    raw = (proc.stdout or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        _eprint(f"[ERROR] Invalid JSON from gh: {e}\n{raw[:500]}")
        sys.exit(1)


def _load_config_settings() -> dict:
    try:
        from config_utils import CONFIG  # type: ignore

        cfg = CONFIG if isinstance(CONFIG, dict) else {}
        settings = cfg.get("settings") or {}
        gp = settings.get("github_projects") or {}
        return gp if isinstance(gp, dict) else {}
    except Exception:
        # Fallback: read CONFIG.json next to this module
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "CONFIG.json")
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return (data.get("settings") or {}).get("github_projects") or {}
            except Exception:
                pass
        return {}


def resolve_project_config(
    owner: Optional[str] = None,
    number: Optional[int] = None,
    status_field: Optional[str] = None,
    repo: Optional[str] = None,
) -> dict:
    file_cfg = _load_config_settings()
    o = (
        owner
        or os.environ.get("AIM_PROJECTS_OWNER")
        or file_cfg.get("owner")
        or "@me"
    )
    n_raw = (
        number
        if number is not None
        else os.environ.get("AIM_PROJECTS_NUMBER")
        or file_cfg.get("number")
    )
    if n_raw is None or n_raw == "":
        n = None
    else:
        try:
            n = int(n_raw)
        except (TypeError, ValueError):
            _eprint(f"[ERROR] Invalid project number: {n_raw!r}")
            sys.exit(1)
    sf = (
        status_field
        or os.environ.get("AIM_PROJECTS_STATUS_FIELD")
        or file_cfg.get("status_field")
        or "Status"
    )
    r = (
        repo
        or os.environ.get("AIM_PROJECTS_REPO")
        or file_cfg.get("repo")
        or _detect_repo()
    )
    return {"owner": str(o), "number": n, "status_field": str(sf), "repo": r}


def _detect_repo() -> Optional[str]:
    proc = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip()
    return None


def require_project_number(cfg: dict) -> int:
    if cfg.get("number") is None:
        _eprint(
            "[ERROR] GitHub Project number not set.\n"
            "  export AIM_PROJECTS_NUMBER=5\n"
            "  # or CONFIG.json settings.github_projects.number\n"
            "  # list boards: aim projects list"
        )
        sys.exit(1)
    return int(cfg["number"])


def get_project_meta(owner: str, number: int) -> dict:
    data = _gh_json(["project", "view", str(number), "--owner", owner])
    if not isinstance(data, dict):
        _eprint("[ERROR] Unexpected project view payload")
        sys.exit(1)
    return data


def get_status_field(owner: str, number: int, field_name: str) -> dict:
    """Return {id, name, options: [{id, name}, ...]} for the Status single-select field."""
    data = _gh_json(["project", "field-list", str(number), "--owner", owner, "-L", "50"])
    fields = data
    if isinstance(data, dict):
        fields = data.get("fields") or data.get("items") or data.get("nodes") or []
    if not isinstance(fields, list):
        _eprint("[ERROR] Unexpected field-list payload")
        sys.exit(1)

    target = field_name.lower().strip()
    for f in fields:
        if not isinstance(f, dict):
            continue
        name = (f.get("name") or "").strip()
        if name.lower() != target:
            continue
        opts = f.get("options") or []
        # Some gh versions nest options differently
        if not opts and isinstance(f.get("dataType"), str):
            pass
        return {
            "id": f.get("id"),
            "name": name,
            "options": [
                {"id": o.get("id"), "name": o.get("name")}
                for o in opts
                if isinstance(o, dict) and o.get("id") and o.get("name")
            ],
        }

    names = [str((f or {}).get("name")) for f in fields if isinstance(f, dict)]
    _eprint(
        f"[ERROR] Status field {field_name!r} not found on project {number}.\n"
        f"  Available fields: {', '.join(names) or '(none)'}\n"
        f"  Hint: aim projects fields"
    )
    sys.exit(1)


def resolve_status_option(field: dict, wanted: str) -> dict:
    """Map alias or exact name to option {id, name}."""
    options = field.get("options") or []
    if not options:
        _eprint(
            f"[ERROR] Field {field.get('name')!r} has no single-select options "
            "(is it a Status field?)."
        )
        sys.exit(1)

    key = wanted.strip().lower().replace(" ", "-")
    # Exact / case-insensitive on option names
    for o in options:
        if o["name"].lower() == wanted.strip().lower():
            return o
        if o["name"].lower().replace(" ", "-") == key:
            return o

    # Alias table
    candidates = STATUS_ALIASES.get(key) or STATUS_ALIASES.get(wanted.strip().lower()) or []
    for cand in candidates:
        for o in options:
            if o["name"].lower() == cand.lower():
                return o

    # Fuzzy contains
    for o in options:
        if key in o["name"].lower().replace(" ", "-"):
            return o

    avail = ", ".join(o["name"] for o in options)
    _eprint(
        f"[ERROR] Cannot map status {wanted!r} to a board option.\n"
        f"  Available: {avail}\n"
        f"  Use: aim projects set <issue> \"<exact Status name>\""
    )
    sys.exit(1)


def list_items(owner: str, number: int, limit: int = 100, query: Optional[str] = None) -> list:
    args = [
        "project",
        "item-list",
        str(number),
        "--owner",
        owner,
        "-L",
        str(limit),
        "--format",
        "json",
    ]
    if query:
        args.extend(["--query", query])
    proc = _run_gh(args, check=False)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        if "project" in err.lower() and ("scope" in err.lower() or "403" in err):
            _eprint(
                "[ERROR] gh lacks Projects access. Run:\n"
                "  gh auth refresh -h github.com -s project,read:project\n"
                f"Detail: {err}"
            )
        else:
            _eprint(f"[ERROR] item-list failed:\n{err}")
        sys.exit(proc.returncode or 1)
    raw = (proc.stdout or "").strip()
    if not raw:
        return []
    data = json.loads(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("items") or data.get("nodes") or []
    return []


def normalize_item(item: dict) -> dict:
    """Flatten gh project item JSON into agent-friendly fields."""
    content = item.get("content") if isinstance(item.get("content"), dict) else {}
    title = (
        item.get("title")
        or content.get("title")
        or item.get("Body")
        or "(no title)"
    )
    number = content.get("number") or item.get("number")
    repo = None
    if isinstance(content.get("repository"), dict):
        repo = content["repository"].get("nameWithOwner") or content["repository"].get("name")
    elif content.get("repository"):
        repo = str(content.get("repository"))
    status = None
    # Prefer explicit status fields from various gh shapes
    for key in ("status", "Status"):
        if isinstance(item.get(key), dict):
            status = item[key].get("name") or item[key].get("option")
        elif isinstance(item.get(key), str):
            status = item[key]
    if not status and isinstance(item.get("fieldValues"), dict):
        nodes = item["fieldValues"].get("nodes") or []
        for n in nodes:
            if not isinstance(n, dict):
                continue
            fname = ((n.get("field") or {}).get("name") or "").lower()
            if fname == "status":
                status = n.get("name") or n.get("text")
    return {
        "id": item.get("id"),
        "title": title,
        "number": number,
        "repository": repo,
        "status": status or "—",
        "type": content.get("type") or item.get("type") or "Issue",
        "url": content.get("url") or item.get("url"),
        "raw": item,
    }


def find_item_by_issue(items: list, issue_number: int, repo: Optional[str] = None) -> Optional[dict]:
    for it in items:
        n = normalize_item(it) if "raw" not in it else it
        # list_items returns raw; normalize always
        n = normalize_item(it)
        if n.get("number") is None:
            continue
        if int(n["number"]) != int(issue_number):
            continue
        if repo and n.get("repository"):
            # allow short repo name or full nameWithOwner
            r = n["repository"]
            if repo.lower() not in r.lower() and r.lower() not in repo.lower():
                # still accept if number unique
                pass
        return n
    return None


def set_issue_status(
    cfg: dict,
    issue_number: int,
    status_wanted: str,
) -> None:
    number = require_project_number(cfg)
    owner = cfg["owner"]
    meta = get_project_meta(owner, number)
    project_id = meta.get("id")
    if not project_id:
        _eprint("[ERROR] Could not resolve project id from gh project view")
        sys.exit(1)

    field = get_status_field(owner, number, cfg["status_field"])
    if not field.get("id"):
        _eprint("[ERROR] Status field missing id")
        sys.exit(1)
    option = resolve_status_option(field, status_wanted)

    items = list_items(owner, number, limit=200)
    match = find_item_by_issue(items, issue_number, cfg.get("repo"))
    if not match or not match.get("id"):
        # Try adding the issue to the project first
        repo = cfg.get("repo")
        if not repo:
            _eprint(
                f"[ERROR] Issue #{issue_number} not on project {number}, "
                "and AIM_PROJECTS_REPO / settings.github_projects.repo not set to auto-add."
            )
            sys.exit(1)
        print(f"[*] Issue #{issue_number} not on board — adding via gh project item-add...")
        url_or_ref = f"https://github.com/{repo}/issues/{issue_number}"
        add = _run_gh(
            [
                "project",
                "item-add",
                str(number),
                "--owner",
                owner,
                "--url",
                url_or_ref,
                "--format",
                "json",
            ],
            check=False,
        )
        if add.returncode != 0:
            _eprint(f"[ERROR] item-add failed:\n{(add.stderr or add.stdout or '').strip()}")
            sys.exit(add.returncode or 1)
        items = list_items(owner, number, limit=200)
        match = find_item_by_issue(items, issue_number, repo)
        if not match or not match.get("id"):
            _eprint(f"[ERROR] Issue #{issue_number} still not found after item-add.")
            sys.exit(1)

    item_id = match["id"]
    edit = _run_gh(
        [
            "project",
            "item-edit",
            "--project-id",
            project_id,
            "--id",
            item_id,
            "--field-id",
            field["id"],
            "--single-select-option-id",
            option["id"],
        ],
        check=False,
    )
    if edit.returncode != 0:
        _eprint(f"[ERROR] item-edit failed:\n{(edit.stderr or edit.stdout or '').strip()}")
        sys.exit(edit.returncode or 1)

    repo_s = match.get("repository") or cfg.get("repo") or ""
    label = f"{repo_s}#{issue_number}" if repo_s else f"#{issue_number}"
    print(f"[SUCCESS] {label} → Status: {option['name']}")
    print(f"  title: {match.get('title')}")
    print(f"  project: {owner}/{number} ({meta.get('title') or ''})")


def print_board(cfg: dict, status_filter: Optional[str], limit: int, as_json: bool) -> None:
    number = require_project_number(cfg)
    owner = cfg["owner"]
    query = None
    if status_filter:
        # Projects filter syntax: status:Name — quote multi-word
        if " " in status_filter:
            query = f'status:"{status_filter}"'
        else:
            query = f"status:{status_filter}"

    items = list_items(owner, number, limit=limit, query=query)
    normalized = [normalize_item(i) for i in items]

    if as_json:
        # Drop raw for cleaner agent JSON
        out = [{k: v for k, v in n.items() if k != "raw"} for n in normalized]
        print(json.dumps(out, indent=2))
        return

    meta = get_project_meta(owner, number)
    title = meta.get("title") or f"Project {number}"
    print(f"=== {title} ({owner} #{number}) ===")
    if status_filter:
        print(f"Filter: status = {status_filter}")
    print(f"Items: {len(normalized)} (limit {limit})\n")

    # Group by status
    groups: dict[str, list] = {}
    for n in normalized:
        groups.setdefault(n["status"] or "—", []).append(n)

    # Prefer known order
    order = ["In Progress", "Todo", "To Do", "Ready", "Backlog", "Blocked", "Done", "—"]
    seen = set()
    keys = []
    for o in order:
        for g in groups:
            if g.lower() == o.lower() and g not in seen:
                keys.append(g)
                seen.add(g)
    for g in sorted(groups.keys()):
        if g not in seen:
            keys.append(g)

    for g in keys:
        rows = groups[g]
        print(f"## {g} ({len(rows)})")
        for n in rows:
            num = f"#{n['number']}" if n.get("number") is not None else "—"
            repo = n.get("repository") or ""
            left = f"{repo}{num}" if repo else num
            print(f"  - {left:<28} {n['title'][:80]}")
        print()


def cmd_list_projects(owner: str) -> None:
    data = _gh_json(["project", "list", "--owner", owner, "-L", "50"])
    projects = data
    if isinstance(data, dict):
        projects = data.get("projects") or data.get("nodes") or data.get("items") or []
    if not isinstance(projects, list):
        print(json.dumps(data, indent=2))
        return
    print(f"=== GitHub Projects for {owner} ===\n")
    for p in projects:
        if not isinstance(p, dict):
            continue
        num = p.get("number")
        title = p.get("title") or "(untitled)"
        closed = " [closed]" if p.get("closed") else ""
        url = p.get("url") or ""
        print(f"  #{num:<4} {title}{closed}")
        if url:
            print(f"         {url}")
    print(
        "\nSet default:\n"
        "  export AIM_PROJECTS_OWNER=BrianV1981\n"
        "  export AIM_PROJECTS_NUMBER=5"
    )


def cmd_fields(cfg: dict) -> None:
    number = require_project_number(cfg)
    data = _gh_json(
        ["project", "field-list", str(number), "--owner", cfg["owner"], "-L", "50"]
    )
    fields = data if isinstance(data, list) else (data or {}).get("fields") or []
    print(f"=== Fields on project {cfg['owner']} #{number} ===\n")
    for f in fields:
        if not isinstance(f, dict):
            continue
        name = f.get("name")
        fid = f.get("id")
        opts = f.get("options") or []
        print(f"  {name}  id={fid}")
        for o in opts:
            if isinstance(o, dict):
                print(f"      - {o.get('name')}  ({o.get('id')})")


def cmd_doctor(cfg: dict) -> None:
    print("--- aim projects doctor ---\n")
    # gh present
    ver = _run_gh(["--version"], check=False)
    if ver.returncode != 0:
        print("[FAIL] gh not available")
        sys.exit(1)
    print(f"[OK] gh: {(ver.stdout or '').splitlines()[0] if ver.stdout else 'ok'}")

    auth = _run_gh(["auth", "status"], check=False)
    print("[*] auth status (see scopes below):")
    print(auth.stdout or auth.stderr or "(no output)")
    blob = (auth.stdout or "") + (auth.stderr or "")
    if "project" not in blob.lower():
        print(
            "\n[WARN] Token may lack 'project' scope. If board commands fail, run:\n"
            "  gh auth refresh -h github.com -s project,read:project\n"
        )
    else:
        print("[OK] project-related scope mentioned in auth status")

    print("\n[*] resolved config:")
    for k, v in cfg.items():
        print(f"  {k}: {v}")

    if cfg.get("number") is None:
        print("\n[WARN] AIM_PROJECTS_NUMBER not set — board/status commands need it.")
        print("  aim projects list")
        print("\n[PARTIAL] doctor complete (set project number to fully validate)")
        return

    # Use non-exiting gh call for reachability so doctor always finishes
    proc = _run_gh(
        [
            "project",
            "view",
            str(int(cfg["number"])),
            "--owner",
            cfg["owner"],
            "--format",
            "json",
        ],
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        print(f"\n[FAIL] cannot reach project {cfg['owner']} #{cfg['number']}:\n{err}")
        if "scope" in err.lower() or "403" in err or "401" in err:
            print(
                "\n[ACTION] Active gh account needs project scope:\n"
                "  gh auth refresh -h github.com -s project,read:project\n"
                "  # ensure BrianV1981 (or board owner) is the active account:\n"
                "  gh auth switch --user <owner>"
            )
        sys.exit(1)

    try:
        meta = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        meta = {}
    print(f"\n[OK] project reachable: {meta.get('title')} id={meta.get('id')}")
    try:
        field = get_status_field(cfg["owner"], int(cfg["number"]), cfg["status_field"])
        print(f"[OK] status field {field.get('name')!r} options:")
        for o in field.get("options") or []:
            print(f"      - {o['name']}")
    except SystemExit:
        print("[FAIL] could not load Status field (see above)")
        sys.exit(1)
    print("\n[OK] doctor complete")

def main(argv: Optional[list[str]] = None) -> None:
    import argparse

    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="aim projects",
        description="GitHub Projects (kanban) GitOps for J.O.S.H.U.A. agents",
    )
    parser.add_argument("--owner", default=None, help="Project owner (login or @me)")
    parser.add_argument("--number", type=int, default=None, help="Project number")
    parser.add_argument(
        "--status-field",
        default=None,
        help="Single-select field name (default: Status)",
    )
    parser.add_argument("--repo", default=None, help="nameWithOwner for issue add (e.g. BrianV1981/aim-ld)")

    sub = parser.add_subparsers(dest="action")

    p_board = sub.add_parser("board", help="Print kanban snapshot (grouped by Status)")
    p_board.add_argument("--status", default=None, help='Filter e.g. "In Progress"')
    p_board.add_argument("-L", "--limit", type=int, default=100)
    p_board.add_argument("--json", action="store_true", help="JSON output for agents")

    p_list = sub.add_parser("list", help="List GitHub Projects for owner")

    p_fields = sub.add_parser("fields", help="List project fields and Status options")

    p_doctor = sub.add_parser("doctor", help="Validate gh auth, scopes, and project config")

    for name, help_ in [
        ("in-progress", "Set issue Status → In Progress (alias)"),
        ("done", "Set issue Status → Done (alias)"),
        ("ready", "Set issue Status → Ready/Todo (alias)"),
        ("todo", "Set issue Status → Todo (alias)"),
        ("blocked", "Set issue Status → Blocked (alias)"),
    ]:
        p = sub.add_parser(name, help=help_)
        p.add_argument("issue", type=int, help="GitHub issue number")

    p_set = sub.add_parser("set", help="Set issue Status to an exact or alias name")
    p_set.add_argument("issue", type=int)
    p_set.add_argument("status", help='Status name or alias (e.g. "In Progress", done)')

    p_view = sub.add_parser("view", help="Show one issue's board row + gh issue view summary")
    p_view.add_argument("issue", type=int)

    args = parser.parse_args(argv)
    cfg = resolve_project_config(
        owner=args.owner,
        number=args.number,
        status_field=args.status_field,
        repo=args.repo,
    )

    if not args.action:
        parser.print_help()
        print(
            "\nExamples:\n"
            "  aim projects doctor\n"
            "  aim projects list\n"
            "  export AIM_PROJECTS_NUMBER=5 AIM_PROJECTS_OWNER=BrianV1981\n"
            "  aim projects board\n"
            "  aim projects in-progress 206\n"
            "  aim projects done 206\n"
        )
        sys.exit(0)

    if args.action == "list":
        cmd_list_projects(cfg["owner"])
    elif args.action == "doctor":
        cmd_doctor(cfg)
    elif args.action == "fields":
        cmd_fields(cfg)
    elif args.action == "board":
        print_board(cfg, args.status, args.limit, args.json)
    elif args.action in ("in-progress", "done", "ready", "todo", "blocked"):
        set_issue_status(cfg, args.issue, args.action)
    elif args.action == "set":
        set_issue_status(cfg, args.issue, args.status)
    elif args.action == "view":
        number = require_project_number(cfg)
        items = list_items(cfg["owner"], number, limit=200)
        match = find_item_by_issue(items, args.issue, cfg.get("repo"))
        if not match:
            print(f"[!] #{args.issue} not found on project {number}")
        else:
            print(json.dumps({k: v for k, v in match.items() if k != "raw"}, indent=2))
        repo = cfg.get("repo")
        if repo:
            print("\n--- gh issue view ---")
            subprocess.run(["gh", "issue", "view", str(args.issue), "-R", repo], check=False)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
