"""TDD: Antigravity transcript.jsonl detection + extraction.

Regression (aim-agy-claude reincarnate 2026-07-16):
  Real brain logs often start with GENERIC/tool rows (type set, source=MODEL).
  Old detect_jsonl_kind returned chat_style on first type=*, yielding 0 turns
  and hard-failing handoff_pulse_generator before teleport.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / ".aim_core"
sys.path.insert(0, str(CORE))

from extract_signal import (  # noqa: E402
    conversational_turn_count,
    detect_jsonl_kind,
    extract_signal,
    extract_signal_from_agy_transcript,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
    )


def test_detect_agy_when_generic_tools_precede_user_input(tmp_path):
    p = tmp_path / "transcript.jsonl"
    _write_jsonl(
        p,
        [
            {
                "step_index": 1,
                "source": "MODEL",
                "type": "GENERIC",
                "status": "RUNNING",
                "created_at": "2026-07-16T00:00:00Z",
                "content": "tool noise",
            },
            {
                "step_index": 2,
                "source": "MODEL",
                "type": "RUN_COMMAND",
                "content": "ls",
            },
            {
                "step_index": 3,
                "source": "USER_EXPLICIT",
                "type": "USER_INPUT",
                "created_at": "2026-07-16T00:01:00Z",
                "content": "Hello from Operator",
            },
            {
                "step_index": 4,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "created_at": "2026-07-16T00:01:01Z",
                "content": "Acknowledged.",
            },
        ],
    )
    assert detect_jsonl_kind(str(p)) == "agy_transcript"
    sig = extract_signal(str(p))
    assert isinstance(sig, list)
    assert conversational_turn_count(sig) >= 2
    assert any(t.get("role") == "user" and "Operator" in (t.get("text") or "") for t in sig)


def test_extract_signal_fallback_when_mislabel_chat_style(tmp_path):
    """Even if detect is wrong historically, extract_signal must recover on AGY rows."""
    p = tmp_path / "transcript.jsonl"
    _write_jsonl(
        p,
        [
            {"type": "GENERIC", "source": "MODEL", "content": "noise"},
            {
                "type": "USER_INPUT",
                "source": "USER_EXPLICIT",
                "content": "directive MARKER_AGY_FIX",
            },
            {
                "type": "PLANNER_RESPONSE",
                "source": "MODEL",
                "content": "got it MARKER_AGY_FIX",
            },
        ],
    )
    sig = extract_signal(str(p))
    assert conversational_turn_count(sig) >= 2
    blob = " ".join((t.get("text") or "") for t in sig)
    assert "MARKER_AGY_FIX" in blob


def test_direct_agy_extractor_skips_tools(tmp_path):
    p = tmp_path / "t.jsonl"
    _write_jsonl(
        p,
        [
            {"type": "VIEW_FILE", "source": "MODEL", "content": "x"},
            {"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "hi"},
            {"type": "PLANNER_RESPONSE", "source": "MODEL", "content": "yo"},
            {"type": "CHECKPOINT", "source": "SYSTEM", "content": "{}"},
        ],
    )
    sig = extract_signal_from_agy_transcript(str(p))
    assert len(sig) == 2
    assert sig[0]["role"] == "user"
    assert sig[1]["role"] == "assistant"
