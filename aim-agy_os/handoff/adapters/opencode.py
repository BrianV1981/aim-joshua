from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional

from handoff.models import TranscriptRef, Turn


class OpenCodeAdapter:
    name = "opencode"

    def __init__(self, sessions_root: Optional[Path] = None):
        pass

    def _export_json_for(self, session_id: str) -> Path | None:
        archive = Path(os.getcwd()) / "archive" / "raw"
        archive.mkdir(parents=True, exist_ok=True)
        out = archive / f"session-{session_id}.json"
        if out.is_file() and out.stat().st_size > 100:
            raw = out.read_text(encoding="utf-8", errors="replace")
            if raw.strip().startswith("{"):
                return out
        try:
            result = subprocess.run(
                ["opencode", "export", session_id],
                capture_output=True, text=True, timeout=30,
            )
            stdout = result.stdout.strip()
            if not stdout.startswith("{"):
                idx = stdout.find("{")
                if idx >= 0:
                    stdout = stdout[idx:]
            if stdout.startswith("{"):
                out.write_text(stdout, encoding="utf-8")
                return out
        except Exception:
            pass
        return None

    def resolve(self, session_id: Optional[str], cwd: Path) -> TranscriptRef:
        if not session_id:
            raise FileNotFoundError("session_id required for opencode adapter")
        path = self._export_json_for(session_id)
        if not path:
            raise FileNotFoundError(f"Cannot export session: {session_id}")
        return TranscriptRef(
            session_id=session_id,
            path=path,
            host=self.name,
            cwd=str(cwd.resolve()),
        )

    def iter_turns(self, ref: TranscriptRef) -> Iterable[Turn]:
        if not ref.path.is_file():
            return
        with ref.path.open("r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
        idx = raw.find("{")
        if idx > 0:
            raw = raw[idx:]
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return
        if not isinstance(data, dict) or "messages" not in data:
            return
        for msg in data.get("messages") or []:
            parts = msg.get("parts") or []
            for part in parts:
                if not isinstance(part, dict) or part.get("type") != "text":
                    continue
                role = part.get("role", "user")
                if not role or role == "?":
                    role = "user"  # fallback for unlabeled turns
                if role not in ("user", "assistant"):
                    role = "assistant"
                text = str(part.get("text") or "")
                if text.strip():
                    yield Turn(
                        role=role,
                        text=text.strip(),
                        timestamp=str(msg.get("info", {}).get("timestamp", "")),
                    )

    def list_sessions(
        self, cwd: Optional[Path] = None, since_mtime: float = 0.0
    ) -> List[TranscriptRef]:
        out: List[TranscriptRef] = []
        archive = Path(os.getcwd()) / "archive" / "raw"
        if not archive.is_dir():
            return out
        for f in sorted(archive.glob("session-*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                mtime = f.stat().st_mtime
            except OSError:
                continue
            if mtime < since_mtime:
                continue
            sid = f.stem.replace("session-", "")
            out.append(TranscriptRef(session_id=sid, path=f, host=self.name, cwd=""))
        return out
