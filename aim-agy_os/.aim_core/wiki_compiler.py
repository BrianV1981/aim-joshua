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


WIKI_SCHEMA_VERSION = 2  # must match <!-- Schema-Version: N --> in template


def _wiki_agents_template_path() -> Path:
    return Path(__file__).resolve().parent / "templates" / "memory_wiki_AGENTS.md"


def _default_wiki_agents_text() -> str:
    """Packaged schema (LLM Wiki Schema-Version 2). Single source for init/scaffold."""
    template = _wiki_agents_template_path()
    if template.is_file():
        return template.read_text(encoding="utf-8")
    return (
        f"<!-- Schema-Version: {WIKI_SCHEMA_VERSION} -->\n"
        "# A.I.M. Memory Wiki Schema\n\n"
        "Process `_ingest/` one file at a time into index.md, log.md, and pages/.\n"
        "Read this file and index.md first. Stay sandboxed to memory-wiki/.\n"
    )


def schema_version_from_text(text: str) -> int:
    m = re.search(r"Schema-Version:\s*(\d+)", text or "")
    if m:
        return int(m.group(1))
    # 1-interim or unversioned thin templates
    if "1-interim" in (text or ""):
        return 1
    return 0


def ensure_wiki_scaffold(paths: dict, upgrade_schema: bool = False) -> None:
    """
    Ensure wiki dirs + index/log + AGENTS.md schema.
    upgrade_schema: if True, overwrite AGENTS.md when packaged version is newer.
    Also honors env AIM_WIKI_SCHEMA_UPGRADE=1.
    """
    if os.environ.get("AIM_WIKI_SCHEMA_UPGRADE", "").strip() in ("1", "true", "yes"):
        upgrade_schema = True

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

    agents = paths.get("agents") or (paths["wiki"] / "AGENTS.md")
    packaged = _default_wiki_agents_text()
    packaged_ver = schema_version_from_text(packaged)

    if not agents.is_file():
        agents.write_text(packaged, encoding="utf-8")
        return

    if upgrade_schema:
        current_ver = schema_version_from_text(agents.read_text(encoding="utf-8", errors="replace"))
        if packaged_ver > current_ver:
            agents.write_text(packaged, encoding="utf-8")


def upgrade_wiki_schema(paths: Optional[dict] = None) -> str:
    """Force-install packaged schema. Returns status string."""
    paths = paths or wiki_paths()
    ensure_wiki_scaffold(paths, upgrade_schema=True)
    agents = paths.get("agents") or (paths["wiki"] / "AGENTS.md")
    ver = schema_version_from_text(agents.read_text(encoding="utf-8", errors="replace"))
    return f"wiki schema installed path={agents} Schema-Version={ver}"


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


# --- Stage 0 multi-page integrate (deterministic, schema-aligned) ---

# Concept keywords → page slugs (A.I.M. domain)
_CONCEPT_KEYWORDS = {
    "reincarnation": ("concept-reincarnation", "Reincarnation & handoff"),
    "memory-wiki": ("concept-memory-wiki", "Memory Wiki (LLM Wiki)"),
    "wiki schema": ("concept-memory-wiki", "Memory Wiki (LLM Wiki)"),
    "lockstep": ("concept-fleet-lockstep", "Fleet lockstep (vessels)"),
    "vessel": ("concept-fleet-lockstep", "Fleet lockstep (vessels)"),
    "gitops": ("concept-gitops", "GitOps & promote HITL"),
    "promote": ("concept-gitops", "GitOps & promote HITL"),
    "engram": ("concept-engram", "Engram / Lance memory"),
    "lancedb": ("concept-engram", "Engram / Lance memory"),
    "session_summarizer": ("concept-memory-wiki", "Memory Wiki (LLM Wiki)"),
    "headless": ("concept-headless-install", "Headless install & aliases"),
    "install-agent": ("concept-headless-install", "Headless install & aliases"),
    "opencode": ("entity-aim-opencode", "aim-opencode vessel"),
    "aim-agy": ("entity-aim-agy", "aim-agy (soul)"),
    "aim-grok": ("entity-aim-grok", "aim-grok vessel"),
}


def _noise_filter_lines(text: str) -> List[str]:
    drop_sub = (
        "system-reminder",
        "skill.md",
        "available tools",
        "function call",
        "tool_call",
        "esc to cancel",
        "prioritizing tool usage",
        "click to expand",
    )
    keep = []
    for line in text.splitlines():
        low = line.lower()
        if any(d in low for d in drop_sub):
            continue
        if line.strip().startswith("{") and len(line) > 180:
            continue
        keep.append(line)
    return keep


def stage0_multi_page_integrate(
    source_path: Path,
    source_id: Optional[str] = None,
    max_source_chars: int = 8000,
) -> List[str]:
    """
    Deterministic multi-page Stage 0 aligned with Schema-Version 2:
    - source-* page from cleaned extract
    - concept/entity stub updates when keywords hit
    - index + log
    Does not require an LLM agent.
    """
    paths = wiki_paths()
    ensure_wiki_scaffold(paths)
    results: List[str] = []
    source_path = Path(source_path)
    if not source_path.is_file():
        return [f"ERROR missing source {source_path}"]

    sid = source_id or _slug(source_path.stem)
    raw = source_path.read_text(encoding="utf-8", errors="replace")
    cleaned = "\n".join(_noise_filter_lines(raw))
    if len(cleaned.strip()) < 80:
        return [f"ERROR noise-only or empty after filter: {source_path.name}"]

    summary = extractive_summary_from_markdown(source_path, max_chars=max_source_chars)
    # Prefer cleaned body if extractive is too thin
    if len(summary) < 200:
        summary = f"# Source: {sid}\n\n{_excerpt(cleaned, max_chars=max_source_chars)}\n"

    # 1) source page
    src_slug = f"source-{_slug(sid)}"
    src_page = paths["pages"] / f"{src_slug}.md"
    title = _first_heading(summary, f"Source {sid}")
    body = (
        f"# {title}\n\n"
        f"*Stage 0 multi-page integrate · source_id=`{sid}` · file=`{source_path}` · "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}*\n\n"
        f"{_excerpt(summary, max_chars=max_source_chars)}\n\n"
        f"---\n[← Wiki index](../index.md)\n"
    )
    if src_page.is_file():
        prev = src_page.read_text(encoding="utf-8")
        src_page.write_text(
            prev.rstrip()
            + f"\n\n## Update {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            + _excerpt(summary, max_chars=3000)
            + "\n",
            encoding="utf-8",
        )
        results.append(f"updated {src_slug}.md")
    else:
        src_page.write_text(body, encoding="utf-8")
        results.append(f"created {src_slug}.md")
    update_index_entry(paths, title, f"pages/{src_slug}.md", f"Source {sid}")

    # 2) concept/entity stubs for keyword hits
    low = cleaned.lower()
    hit_slugs = {}
    for key, (slug, ctitle) in _CONCEPT_KEYWORDS.items():
        if key in low:
            hit_slugs[slug] = ctitle
    for slug, ctitle in hit_slugs.items():
        page = paths["pages"] / f"{slug}.md"
        blurb = f"Mentioned in source `{sid}` ({source_path.name})."
        section = (
            f"\n\n## From source [{sid}]({src_slug}.md)\n\n"
            f"{blurb}\n\n"
            f"See also: [{title}]({src_slug}.md)\n"
        )
        if page.is_file():
            existing = page.read_text(encoding="utf-8")
            if sid in existing and source_path.name in existing:
                results.append(f"skip {slug}.md (already linked)")
                continue
            page.write_text(existing.rstrip() + section + "\n", encoding="utf-8")
            results.append(f"updated {slug}.md")
        else:
            page.write_text(
                f"# {ctitle}\n\n"
                f"*Auto-stub from Stage 0 multi-page integrate.*\n"
                f"{section}\n---\n[← Wiki index](../index.md)\n",
                encoding="utf-8",
            )
            results.append(f"created {slug}.md")
        update_index_entry(paths, ctitle, f"pages/{slug}.md", blurb[:100])

    # 3) log (schema-compatible prefix)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    with paths["log"].open("a", encoding="utf-8") as f:
        f.write(f"## [{ts}] ingest | {title[:60]} | {sid}\n")
    results.append(f"log ingest | {sid}")
    return results


def stage0_from_archive(archive_path: str, source_id: Optional[str] = None) -> List[str]:
    """CLI/helper entry: multi-page integrate one archive markdown."""
    return stage0_multi_page_integrate(Path(archive_path), source_id=source_id)


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
