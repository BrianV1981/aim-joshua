#!/usr/bin/env python3
"""
Session signal extraction for OpenCode vessel (+ AGY/Grok fallbacks).
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Dict, List, Union

Signal = List[Dict[str, Any]]
ExtractResult = Union[Signal, str]


def _process_content(c: Any) -> str:
    if isinstance(c, list):
        text = " ".join(
            [
                str(item.get("text", ""))
                for item in c
                if isinstance(item, dict) and "text" in item
            ]
        )
    elif isinstance(c, dict):
        text = str(c.get("text", ""))
    else:
        text = str(c) if c is not None else ""
    return re.sub(r"\n{3,}", "\n\n", text)


def detect_format(json_path: str) -> str:
    ext = os.path.splitext(json_path)[1].lower()
    if ext == ".jsonl":
        # peek for grok updates
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                for _ in range(5):
                    line = f.readline()
                    if not line.strip():
                        continue
                    msg = json.loads(line)
                    if isinstance(msg, dict) and msg.get("method") == "session/update":
                        return "grok_updates"
                    if isinstance(msg, dict) and msg.get("type") in (
                        "USER_INPUT",
                        "PLANNER_RESPONSE",
                    ):
                        return "agy_transcript"
                    return "gemini"
        except Exception:
            return "gemini"
        return "gemini"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "messages" in data:
            return "opencode"
    except Exception:
        pass
    return "unknown"


def _extract_opencode(json_path: str) -> Signal:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    messages = data.get("messages") or []
    signal: Signal = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        # Flat archive shape: {type, content, timestamp}
        if msg.get("type") in ("user", "assistant", "system", "model") and "content" in msg:
            role = msg["type"]
            if role == "model":
                role = "assistant"
            frag = {
                "role": role,
                "timestamp": msg.get("timestamp", "Unknown"),
                "text": _process_content(msg.get("content")),
            }
            if role == "assistant":
                frag["thoughts"] = []
                frag["actions"] = []
            signal.append(frag)
            continue
        # Nested OpenCode export shape: {info: {role}, parts: [...]}
        info = msg.get("info") or {}
        if not isinstance(info, dict):
            continue
        m_role = info.get("role")
        if not m_role:
            continue
        ts_raw = info.get("time", {})
        ts = (
            ts_raw.get("created", "Unknown")
            if isinstance(ts_raw, dict)
            else "Unknown"
        )
        fragment: Dict[str, Any] = {"role": m_role, "timestamp": ts}
        parts = msg.get("parts") or []
        texts = [
            p.get("text", "")
            for p in parts
            if isinstance(p, dict) and p.get("type") == "text" and p.get("text")
        ]
        fragment["text"] = " ".join(texts)
        if m_role in ("assistant", "model", "gemini"):
            fragment["role"] = "assistant"
            fragment["thoughts"] = [
                {"text": p.get("text", "")}
                for p in parts
                if isinstance(p, dict)
                and p.get("type") == "reasoning"
                and p.get("text")
            ]
            fragment["actions"] = []
        signal.append(fragment)
    return signal


def _extract_gemini(json_path: str) -> Signal:
    signal: Signal = []
    with open(json_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(msg, dict):
                continue
            m_role = msg.get("type") or msg.get("role")
            if not m_role:
                continue
            frag: Dict[str, Any] = {
                "role": m_role,
                "timestamp": msg.get("timestamp", "Unknown"),
            }
            if m_role in ("user", "system"):
                frag["text"] = _process_content(msg.get("content"))
            elif m_role in ("gemini", "model", "assistant"):
                frag["role"] = "assistant"
                frag["text"] = _process_content(msg.get("content"))
                frag["thoughts"] = msg.get("thoughts") or []
                frag["actions"] = []
            else:
                continue
            signal.append(frag)
    return signal


def extract_signal(json_path: str) -> ExtractResult:
    try:
        fmt = detect_format(json_path)
        if fmt == "opencode":
            return _extract_opencode(json_path)
        if fmt == "gemini":
            return _extract_gemini(json_path)
        # try opencode then gemini
        try:
            sk = _extract_opencode(json_path)
            if sk:
                return sk
        except Exception:
            pass
        return _extract_gemini(json_path)
    except Exception as e:
        return f"Extraction Error: {e}"


def conversational_turn_count(skeleton: Any) -> int:
    if not isinstance(skeleton, list):
        return 0
    n = 0
    for turn in skeleton:
        if not isinstance(turn, dict):
            continue
        role = (turn.get("role") or "").lower()
        text = (turn.get("text") or "").strip()
        if role in ("user", "assistant", "model", "agy", "gemini") and text:
            n += 1
    return n


def skeleton_to_markdown(skeleton, session_id):
    if isinstance(skeleton, str):
        return (
            f"---\nSession: {session_id}\nType: Error\n---\n\n"
            f"# Extraction failed\n\n{skeleton}\n"
        )
    md = (
        f"---\nSession: {session_id}\nType: Raw Backup\n---\n\n"
        f"# A.I.M. Signal Skeleton\n\n"
    )
    if not isinstance(skeleton, list) or not skeleton:
        md += "*No conversational turns extracted.*\n"
        return md
    for turn in skeleton:
        if not isinstance(turn, dict):
            continue
        role = (turn.get("role") or "unknown").upper()
        text = (turn.get("text") or "").strip()
        ts = turn.get("timestamp", "")
        if role in ("USER", "SYSTEM"):
            md += f"## 👤 {role} ({ts})\n"
            if text:
                md += f"{text}\n\n"
        elif role in ("ASSISTANT", "MODEL", "GEMINI", "AGY"):
            md += f"## 🤖 A.I.M. ({ts})\n"
            if text:
                md += f"{text}\n\n"
        elif text:
            md += f"## {role} ({ts})\n{text}\n\n"
        md += "---\n\n"
    return md


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: extract_signal.py <path>")
        sys.exit(1)
    r = extract_signal(sys.argv[1])
    print("turns", conversational_turn_count(r), "n", len(r) if isinstance(r, list) else r)
