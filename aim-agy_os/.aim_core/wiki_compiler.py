#!/usr/bin/env python3
"""
Deterministic Memory Wiki compiler for aim-grok (no AGY/Grok agent required).

Pipeline:
  archive/history/*.md  →  (optional) extractive summary → _ingest/
  _ingest/*             →  pages/*.md + index.md + log.md  →  delete ingest file
"""
from __future__ import annotations

import os
import re
import glob
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple


def find_os_root() -> Path:
    current = Path(os.getcwd()).resolve()
    for p in [current, *current.parents]:
        candidate = p / "aim-agy_os"
        if (candidate / "setup.sh").is_file():
            return candidate
        if (p / "setup.sh").is_file() and (p / ".aim_core").is_dir():
            return p
    return Path(__file__).resolve().parents[1]


def wiki_paths(os_root: Optional[Path] = None) -> dict:
    root = os_root or find_os_root()
    wiki = root / "memory-wiki"
    return {
        "os_root": root,
        "wiki": wiki,
        "ingest": wiki / "_ingest",
        "raw": wiki / "_raw_logs",
        "pages": wiki / "pages",
        "index": wiki / "index.md",
        "log": wiki / "log.md",
        "agents": wiki / "AGENTS.md",
    }


def _slug(text: str, max_len: int = 48) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return (s[:max_len] or "note").strip("-")


def _first_heading(content: str, fallback: str) -> str:
    for line in content.splitlines():
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m:
            return m.group(1).strip()
    return fallback


def _excerpt(content: str, max_chars: int = 1200) -> str:
    # Drop very noisy JSON-like blocks
    lines = []
    for line in content.splitlines():
        if line.strip().startswith("{") and len(line) > 200:
            continue
        lines.append(line)
    text = "\n".join(lines).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit("\n", 1)[0] + "\n\n*(truncated for wiki)*\n"


def _default_wiki_agents_text() -> str:
    """Interim schema (lockstep B). Full LLM-Wiki v2 schema is a later PR."""
    template = Path(__file__).resolve().parent / "templates" / "memory_wiki_AGENTS.md"
    if template.is_file():
        return template.read_text(encoding="utf-8")
    return (
        "<!-- Schema-Version: 1-interim -->\n"
        "# Wiki Maintainer\n\n"
        "Process `_ingest/` one file at a time into index.md, log.md, and pages/.\n"
        "Read this file and index.md before writing. Stay sandboxed to memory-wiki/.\n"
    )


def ensure_wiki_scaffold(paths: dict) -> None:
    paths["wiki"].mkdir(parents=True, exist_ok=True)
    paths["ingest"].mkdir(parents=True, exist_ok=True)
    paths["raw"].mkdir(parents=True, exist_ok=True)
    paths["pages"].mkdir(parents=True, exist_ok=True)
    if not paths["index"].is_file():
        paths["index"].write_text(
            "# A.I.M. Wiki Index\n\nPersistent project lore.\n\n## Pages\n\n",
            encoding="utf-8",
        )
    if not paths["log"].is_file():
        paths["log"].write_text("# Wiki Log\n\n", encoding="utf-8")
    # Always ensure AGENTS schema exists (install/init/reincarnate lockstep)
    agents = paths.get("agents") or (paths["wiki"] / "AGENTS.md")
    if not agents.is_file():
        agents.write_text(_default_wiki_agents_text(), encoding="utf-8")


def append_log(paths: dict, message: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with paths["log"].open("a", encoding="utf-8") as f:
        f.write(f"- [{ts}] {message}\n")


def update_index_entry(paths: dict, title: str, rel_path: str, blurb: str) -> None:
    index = paths["index"].read_text(encoding="utf-8")
    link = f"- [{title}]({rel_path}) — {blurb.strip()[:120]}"
    if f"]({rel_path})" in index:
        return
    if "## Pages" not in index:
        index = index.rstrip() + "\n\n## Pages\n\n"
    # Append link after the Pages heading (first line after heading)
    head, tail = index.split("## Pages", 1)
    rest = tail.lstrip("\n")
    if rest.startswith("#"):
        # unexpected
        new_index = head + "## Pages\n\n" + link + "\n" + rest
    else:
        new_index = head + "## Pages\n\n" + link + "\n" + rest
    if not new_index.endswith("\n"):
        new_index += "\n"
    paths["index"].write_text(new_index, encoding="utf-8")


def process_ingest_file(paths: dict, filepath: Path) -> str:
    content = filepath.read_text(encoding="utf-8", errors="replace")
    if len(content.strip()) < 40:
        filepath.unlink(missing_ok=True)
        return f"skipped empty {filepath.name}"

    title = _first_heading(content, filepath.stem.replace("_", " ").title())
    slug = _slug(filepath.stem)
    page_path = paths["pages"] / f"{slug}.md"
    body = _excerpt(content, max_chars=4000)

    page_md = (
        f"# {title}\n\n"
        f"*Ingested from `{filepath.name}` on "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}*\n\n"
        f"{body}\n\n"
        f"---\n"
        f"[← Wiki index](../index.md)\n"
    )
    if page_path.is_file():
        # append section rather than clobber
        existing = page_path.read_text(encoding="utf-8")
        page_path.write_text(
            existing.rstrip()
            + f"\n\n## Update {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}\n\n"
            + body
            + "\n",
            encoding="utf-8",
        )
        action = "updated"
    else:
        page_path.write_text(page_md, encoding="utf-8")
        action = "created"

    blurb = re.sub(r"\s+", " ", body)[:100]
    update_index_entry(paths, title, f"pages/{slug}.md", blurb)
    append_log(paths, f"{action} page `{slug}.md` from `{filepath.name}`")
    filepath.unlink(missing_ok=True)
    return f"{action} {slug}.md from {filepath.name}"


def process_ingest(paths: Optional[dict] = None) -> List[str]:
    paths = paths or wiki_paths()
    ensure_wiki_scaffold(paths)
    results = []
    files = sorted(
        [Path(p) for p in glob.glob(str(paths["ingest"] / "*.*"))],
        key=lambda p: p.stat().st_mtime,
    )
    # skip keep files
    files = [f for f in files if f.name not in (".gitkeep", ".keep")]
    if not files:
        results.append("No files in _ingest/")
        return results
    for f in files:
        try:
            results.append(process_ingest_file(paths, f))
        except Exception as e:
            results.append(f"ERROR {f.name}: {e}")
    return results


def extractive_summary_from_markdown(md_path: Path, max_chars: int = 6000) -> str:
    text = md_path.read_text(encoding="utf-8", errors="replace")
    # Prefer USER / MODEL conversational lines
    keep = []
    for line in text.splitlines():
        u = line.upper()
        if any(k in u for k in ("USER", "MODEL", "ASSISTANT", "OPERATOR", "ORCHESTRAT", "STATUS", "PHASE", "WIKI", "MERGE", "AUDIT")):
            keep.append(line)
        elif line.startswith("#") or line.startswith("##"):
            keep.append(line)
        elif line.startswith("- ") or line.startswith("* "):
            keep.append(line)
    if not keep:
        keep = text.splitlines()[:80]
    summary = "\n".join(keep)
    summary = _excerpt(summary, max_chars=max_chars)
    title = _first_heading(text, md_path.stem)
    return f"# Summary: {title}\n\nSource: `{md_path.name}`\n\n{summary}\n"


def stage_history_to_ingest(history_glob: Optional[str] = None, limit: int = 20) -> List[str]:
    """Copy extractive summaries of archive history into _ingest for wiki process."""
    paths = wiki_paths()
    ensure_wiki_scaffold(paths)
    os_root = paths["os_root"]
    pattern = history_glob or str(os_root / "archive" / "history" / "*.md")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)[:limit]
    out = []
    for fp in files:
        p = Path(fp)
        digest = hashlib.sha1(p.name.encode()).hexdigest()[:8]
        dest = paths["ingest"] / f"history_{digest}_{_slug(p.stem)}.md"
        if dest.exists():
            out.append(f"skip existing {dest.name}")
            continue
        dest.write_text(extractive_summary_from_markdown(p), encoding="utf-8")
        out.append(f"staged {dest.name}")
    return out


def seed_vessel_docs_to_ingest() -> List[str]:
    """Seed high-value vessel docs into _ingest once."""
    paths = wiki_paths()
    ensure_wiki_scaffold(paths)
    vessel = paths["os_root"].parent
    candidates = [
        vessel / "SOURCE.md",
        vessel / "TOOL_MAP.md",
        vessel / "SYNC_FROM_AIM_AGY.md",
        vessel / "README.md",
        vessel / "AGENTS.md",
        paths["os_root"] / "planning-artifacts" / "PHASE0_COMPLETE.md",
        paths["os_root"] / "planning-artifacts" / "PHASE1_COMPLETE.md",
        paths["os_root"] / "planning-artifacts" / "PHASE2_PROGRESS.md",
        paths["os_root"] / "planning-artifacts" / "SYNC_2026-07-12.md",
        paths["os_root"] / "planning-artifacts" / "GROK_CLI_ADAPTATION_PLAN.md",
    ]
    out = []
    for c in candidates:
        if not c.is_file():
            continue
        dest = paths["ingest"] / f"seed_{_slug(c.stem)}.md"
        if dest.exists() or (paths["pages"] / f"{_slug(c.stem)}.md").exists():
            # still allow re-seed with content hash name
            dest = paths["ingest"] / f"seed_{_slug(c.stem)}_{hashlib.sha1(c.read_bytes()).hexdigest()[:6]}.md"
            if dest.exists():
                out.append(f"skip {c.name}")
                continue
        content = c.read_text(encoding="utf-8", errors="replace")
        dest.write_text(
            f"# {c.stem}\n\n*Seeded from `{c}`*\n\n{content}\n",
            encoding="utf-8",
        )
        out.append(f"seeded {dest.name}")
    return out


def process_raw_logs_to_ingest() -> List[str]:
    paths = wiki_paths()
    ensure_wiki_scaffold(paths)
    out = []
    for fp in sorted(glob.glob(str(paths["raw"] / "*.md"))):
        p = Path(fp)
        dest = paths["ingest"] / f"rawsum_{_slug(p.stem)}.md"
        dest.write_text(extractive_summary_from_markdown(p), encoding="utf-8")
        p.unlink(missing_ok=True)
        out.append(f"raw→ingest {dest.name}")
    return out


def bootstrap_wiki(include_history: bool = True, history_limit: int = 10) -> None:
    paths = wiki_paths()
    ensure_wiki_scaffold(paths)
    print("--- WIKI BOOTSTRAP (deterministic) ---")
    for line in seed_vessel_docs_to_ingest():
        print(" ", line)
    if include_history:
        for line in stage_history_to_ingest(limit=history_limit):
            print(" ", line)
    for line in process_raw_logs_to_ingest():
        print(" ", line)
    for line in process_ingest(paths):
        print(" ", line)
    print(f"[DONE] index={paths['index']} pages={len(list(paths['pages'].glob('*.md')))}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Deterministic memory-wiki compiler")
    ap.add_argument("command", choices=["bootstrap", "process", "seed", "stage-history"])
    ap.add_argument("--history-limit", type=int, default=10)
    args = ap.parse_args()
    if args.command == "bootstrap":
        bootstrap_wiki(history_limit=args.history_limit)
    elif args.command == "process":
        for line in process_ingest():
            print(line)
    elif args.command == "seed":
        for line in seed_vessel_docs_to_ingest():
            print(line)
    elif args.command == "stage-history":
        for line in stage_history_to_ingest(limit=args.history_limit):
            print(line)
