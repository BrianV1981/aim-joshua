"""System B: nightly wiki — FR clean → wiki by cwd → embed → DB."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Protocol

from handoff.embed_store import chunk_text, store_chunks
from handoff.flight_record import turns_to_flight_record, write_flight_record
from handoff.models import JobResult, TranscriptRef
from handoff.paths import cron_state_dir, fr_cache_dir, memory_db_dir, vessel_root, wiki_root


class _Adapter(Protocol):
    name: str

    def list_sessions(
        self, cwd: Optional[Path] = None, since_mtime: float = 0.0
    ) -> List[TranscriptRef]: ...

    def iter_turns(self, ref: TranscriptRef): ...


def run_wiki_batch(
    *,
    adapter: _Adapter,
    root: Optional[Path] = None,
    project_root: Optional[Path] = None,
    since_mtime: Optional[float] = None,
    limit: int = 50,
) -> JobResult:
    root = Path(root) if root else vessel_root()
    project_root = Path(project_root or root).resolve()
    state_dir = cron_state_dir(root)
    wm_path = state_dir / f"wiki_watermark_{adapter.name}.json"
    if since_mtime is None:
        since_mtime = _load_watermark(wm_path)

    gates = {f"N{i}": False for i in range(6)}
    errors: List[str] = []
    processed = []
    max_mtime = since_mtime

    sessions = adapter.list_sessions(cwd=project_root, since_mtime=since_mtime)
    # also accept sessions whose meta cwd matches
    if not sessions:
        sessions = [
            s
            for s in adapter.list_sessions(cwd=None, since_mtime=since_mtime)
            if s.cwd and Path(s.cwd).resolve() == project_root
        ]

    gates["N0"] = True  # resolve path ok even if empty set
    if not sessions:
        res = JobResult(
            system="wiki_batch",
            status="empty",
            code="NO_SESSIONS",
            vessel=root.name,
            gates=gates,
            errors=["no sessions since watermark"],
            extras={"since_mtime": since_mtime, "project_root": str(project_root)},
        )
        _write_job(state_dir / "wiki_batch_result.json", res)
        return res

    wiki = wiki_root(root)
    fr_dir = fr_cache_dir(root)
    db_dir = memory_db_dir(root)
    newest = since_mtime

    for ref in sessions[:limit]:
        try:
            mtime = ref.path.stat().st_mtime
            newest = max(newest, mtime)
            turns = list(adapter.iter_turns(ref))
            if not turns:
                errors.append(f"{ref.session_id}: zero turns")
                continue
            fr_md = turns_to_flight_record(
                ref.session_id, turns, source=str(ref.path), mode="cleaned"
            )
            if len(fr_md.strip()) < 40:
                errors.append(f"{ref.session_id}: FR too short")
                continue
            fr_path = write_flight_record(
                fr_dir / f"{ref.session_id}.md", fr_md
            )
            gates["N1"] = True

            page_name = f"source-{_safe_id(ref.session_id)}.md"
            page_path = wiki / "pages" / page_name
            page_body = _wiki_page(ref, fr_md, project_root)
            page_path.write_text(page_body, encoding="utf-8")
            _append_log(wiki, ref.session_id, page_name)
            _upsert_index(wiki, ref.session_id, page_name)
            gates["N2"] = True

            chunks = chunk_text(fr_md)
            store_info = store_chunks(
                db_dir=db_dir,
                session_id=ref.session_id,
                project_root=str(project_root),
                chunks=chunks,
            )
            gates["N3"] = store_info["chunk_count"] > 0
            gates["N4"] = store_info["chunk_count"] > 0 and (
                store_info["lance_ok"] or Path(store_info["jsonl_path"]).is_file()
            )
            processed.append(
                {
                    "session_id": ref.session_id,
                    "fr": str(fr_path),
                    "wiki": str(page_path),
                    "store": store_info,
                }
            )
        except Exception as e:
            errors.append(f"{ref.session_id}: {e}")

    if processed:
        _save_watermark(wm_path, newest)
        gates["N5"] = True
        status = "ok" if not errors else "partial"
        code = "OK" if status == "ok" else "PARTIAL"
    else:
        status = "error"
        code = "NO_PROCESSED"
        errors.append("no sessions successfully processed")

    res = JobResult(
        system="wiki_batch",
        status=status,
        code=code,
        vessel=root.name,
        turn_count=len(processed),
        gates=gates,
        errors=errors,
        paths={
            "wiki": str(wiki),
            "fr_dir": str(fr_dir),
            "db_dir": str(db_dir),
            "result": str(state_dir / "wiki_batch_result.json"),
        },
        extras={
            "processed": processed,
            "project_root": str(project_root),
            "watermark": newest,
        },
    )
    _write_job(state_dir / "wiki_batch_result.json", res)
    return res


def _safe_id(sid: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", sid)[:80]


def _wiki_page(ref: TranscriptRef, fr_md: str, project_root: Path) -> str:
    now = datetime.now(timezone.utc).isoformat()
    return f"""# Source session {ref.session_id}

- **Session-Id:** `{ref.session_id}`
- **Host:** {ref.host}
- **Project root:** `{project_root}`
- **Source:** `{ref.path}`
- **Ingested:** {now}

## Flight record (cleaned)

{fr_md}
"""


def _append_log(wiki: Path, session_id: str, page_name: str) -> None:
    log = wiki / "log.md"
    if not log.exists():
        log.write_text("# Wiki log\n\n", encoding="utf-8")
    with log.open("a", encoding="utf-8") as f:
        f.write(
            f"- {datetime.now(timezone.utc).date()} | handoff_vnext | {session_id} → pages/{page_name}\n"
        )


def _upsert_index(wiki: Path, session_id: str, page_name: str) -> None:
    idx = wiki / "index.md"
    line = f"- [{session_id}](pages/{page_name})\n"
    if not idx.exists():
        idx.write_text("# Memory wiki index\n\n## Sessions\n\n" + line, encoding="utf-8")
        return
    text = idx.read_text(encoding="utf-8")
    if session_id in text:
        return
    if "## Sessions" not in text:
        text += "\n## Sessions\n\n"
    text += line
    idx.write_text(text, encoding="utf-8")


def _load_watermark(path: Path) -> float:
    if not path.is_file():
        return 0.0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return float(data.get("mtime", 0.0))
    except (json.JSONDecodeError, TypeError, ValueError):
        return 0.0


def _save_watermark(path: Path, mtime: float) -> None:
    path.write_text(
        json.dumps({"mtime": mtime, "updated": datetime.now(timezone.utc).isoformat()})
        + "\n",
        encoding="utf-8",
    )


def _write_job(path: Path, res: JobResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(res.to_dict(), indent=2) + "\n", encoding="utf-8")
