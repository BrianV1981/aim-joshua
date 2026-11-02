from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, List, Optional

from handoff.models import TranscriptRef, Turn


class AgyAdapter:
    name = "agy"

    def __init__(self, brain_root: Optional[Path] = None):
        if brain_root is not None:
            resolved = Path(brain_root)
            self.brain_roots = [resolved]
            self.brain_root = resolved
        else:
            home = Path(os.path.expanduser("~"))
            self.brain_roots = [
                home / ".gemini" / "antigravity" / "brain",
                home / ".gemini" / "antigravity-cli" / "brain",
            ]
            self.brain_root = next((p for p in self.brain_roots if p.is_dir()), self.brain_roots[0])

    def resolve(self, session_id: Optional[str], cwd: Path) -> TranscriptRef:
        if session_id:
            for root in self.brain_roots:
                path = root / session_id / ".system_generated" / "logs" / "transcript.jsonl"
                if path.is_file():
                    return TranscriptRef(
                        session_id=session_id,
                        path=path,
                        host=self.name,
                        cwd=str(cwd.resolve()),
                    )
            searched = ", ".join(str(r) for r in self.brain_roots)
            raise FileNotFoundError(
                f"AGY session not found: {session_id} under [{searched}]"
            )

        # If no session_id is provided, find the most recently modified transcript.jsonl across AGY roots
        existing_roots = [r for r in self.brain_roots if r.is_dir()]
        if not existing_roots:
            raise FileNotFoundError(
                f"No AGY brain root found under [{', '.join(str(r) for r in self.brain_roots)}]"
            )

        all_candidates: List[Path] = []
        for root in existing_roots:
            all_candidates.extend(root.glob("*/.system_generated/logs/transcript.jsonl"))
        candidates = sorted(
            all_candidates,
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            raise FileNotFoundError(
                f"No transcript.jsonl found under [{', '.join(str(r) for r in existing_roots)}]"
            )

        path = candidates[0]
        # path is brain/<session_id>/.system_generated/logs/transcript.jsonl
        sid = path.parent.parent.parent.name
        return TranscriptRef(
            session_id=sid, path=path, host=self.name, cwd=str(cwd.resolve())
        )

    def iter_turns(self, ref: TranscriptRef) -> Iterable[Turn]:
        with ref.path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                source = msg.get("source")
                msg_type = msg.get("type")
                
                if source == "USER_EXPLICIT" and msg_type == "USER_INPUT":
                    text = msg.get("content", "")
                    if text and text.strip():
                        yield Turn(
                            role="user",
                            text=text.strip(),
                            timestamp=msg.get("created_at", ""),
                        )
                elif source == "MODEL" and msg_type == "PLANNER_RESPONSE":
                    text = msg.get("content", "")
                    if text and text.strip():
                        yield Turn(
                            role="assistant",
                            text=text.strip(),
                            timestamp=msg.get("created_at", ""),
                        )

    def list_sessions(
        self, cwd: Optional[Path] = None, since_mtime: float = 0.0
    ) -> List[TranscriptRef]:
        out: List[TranscriptRef] = []
        seen_sids: set[str] = set()
        for root in self.brain_roots:
            if not root.is_dir():
                continue
            for updates in root.glob("*/.system_generated/logs/transcript.jsonl"):
                try:
                    mtime = updates.stat().st_mtime
                except OSError:
                    continue
                if mtime < since_mtime:
                    continue

                sid = updates.parent.parent.parent.name
                if sid in seen_sids:
                    continue
                seen_sids.add(sid)
                out.append(
                    TranscriptRef(
                        session_id=sid,
                        path=updates,
                        host=self.name,
                        cwd=str(cwd) if cwd else None,
                    )
                )

        out.sort(key=lambda r: r.path.stat().st_mtime, reverse=True)
        return out
