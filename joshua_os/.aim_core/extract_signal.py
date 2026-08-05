#!/usr/bin/env python3
"""
Session signal extraction for reincarnation / flight recorder / memory-wiki.

Supports:
  - Grok chat_history.jsonl (type: user|assistant|system|reasoning)
  - Grok updates.jsonl (method: session/update with user_message_chunk / agent_*)
  - AGY-style role/type message JSONL
  - OpenCode archive/raw session-*.json (single JSON messages[])
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Union


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


def _is_grok_updates_line(msg: dict) -> bool:
    return msg.get("method") == "session/update" and isinstance(msg.get("params"), dict)


def extract_signal_from_grok_updates(json_path: str) -> Signal:
    """
    Coalesce Grok durable stream chunks into conversational turns.
    Keeps user_message_chunk + agent_message_chunk (+ thoughts). Skips tool spam.
    """
    signal: Signal = []
    user_parts: List[str] = []
    agent_parts: List[str] = []
    thought_parts: List[str] = []
    last_ts: Any = "Unknown"
    user_ts: Any = "Unknown"
    agent_ts: Any = "Unknown"

    def flush_user() -> None:
        nonlocal user_parts, user_ts
        text = "".join(user_parts).strip()
        if text:
            signal.append({"role": "user", "timestamp": user_ts, "text": text})
        user_parts = []

    def flush_agent() -> None:
        nonlocal agent_parts, thought_parts, agent_ts
        text = "".join(agent_parts).strip()
        thoughts = [{"text": t} for t in thought_parts if t.strip()]
        if text or thoughts:
            frag: Dict[str, Any] = {
                "role": "assistant",
                "timestamp": agent_ts,
                "text": text,
                "thoughts": thoughts,
                "actions": [],
            }
            signal.append(frag)
        agent_parts = []
        thought_parts = []

    with open(json_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(msg, dict) or not _is_grok_updates_line(msg):
                continue

            last_ts = msg.get("timestamp", last_ts)
            update = msg.get("params", {}).get("update") or {}
            if not isinstance(update, dict):
                continue
            su = update.get("sessionUpdate") or ""

            if su == "user_message_chunk":
                # New user turn: flush prior agent first
                if agent_parts or thought_parts:
                    flush_agent()
                content = update.get("content")
                chunk = _process_content(content)
                if not user_parts:
                    user_ts = last_ts
                if chunk:
                    user_parts.append(chunk)

            elif su == "agent_message_chunk":
                if user_parts:
                    flush_user()
                content = update.get("content")
                chunk = _process_content(content)
                if not agent_parts and not thought_parts:
                    agent_ts = last_ts
                if chunk:
                    agent_parts.append(chunk)

            elif su == "agent_thought_chunk":
                if user_parts:
                    flush_user()
                content = update.get("content")
                chunk = _process_content(content)
                if not agent_parts and not thought_parts:
                    agent_ts = last_ts
                if chunk:
                    thought_parts.append(chunk[:2000])

            elif su == "turn_completed":
                if user_parts:
                    flush_user()
                if agent_parts or thought_parts:
                    flush_agent()

            elif su in ("tool_call", "tool_call_update"):
                # Optional: record tool name as action on current agent turn
                if user_parts:
                    flush_user()
                title = update.get("title") or update.get("kind") or ""
                if title and (agent_parts or thought_parts or True):
                    # attach later via lightweight action-only fragment only if we have open agent
                    if not agent_parts and not thought_parts:
                        agent_ts = last_ts
                    # stash as mini action by ensuring agent fragment exists at flush
                    # (actions collected on next flush if we store temporarily)
                    pass

            # ignore plan, compaction, task_* noise

    if user_parts:
        flush_user()
    if agent_parts or thought_parts:
        flush_agent()

    return signal


def extract_signal_from_chat_style(json_path: str) -> Signal:
    """chat_history.jsonl / AGY-style message rows."""
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
            # Skip Grok updates stream rows if mixed
            if _is_grok_updates_line(msg):
                continue
            if "$set" in msg or msg.get("kind") == "session":
                continue

            m_role = msg.get("type") or msg.get("role")
            if not m_role:
                continue
            ts = msg.get("timestamp", "Unknown")
            fragment: Dict[str, Any] = {"role": m_role, "timestamp": ts}
            content = msg.get("content")
            tokens = msg.get("tokens", {})
            if tokens:
                fragment["tokens"] = tokens

            if m_role in ("user", "system"):
                fragment["text"] = _process_content(content)
            elif m_role in ("agy", "model", "assistant"):
                text = _process_content(content)
                thoughts_arr = msg.get("thoughts", [])
                if (
                    not thoughts_arr
                    and "\n\n" in text
                    and len(text) > 500
                    and any(
                        k in text.lower()
                        for k in ("investigating", "thinking", "objective")
                    )
                ):
                    parts = text.rsplit("\n\n", 1)
                    thoughts_arr = [
                        {"text": line.strip()}
                        for line in parts[0].split("\n")
                        if line.strip()
                    ]
                    text = parts[1].strip()
                fragment["text"] = text
                fragment["thoughts"] = thoughts_arr or []
                fragment["actions"] = []
                tool_calls = msg.get("toolCalls", []) or msg.get("tool_calls", [])
                for call in tool_calls:
                    if not isinstance(call, dict):
                        continue
                    name = call.get("name") or call.get("function", {}).get("name")
                    args = call.get("args") or call.get("function", {}).get(
                        "arguments"
                    )
                    fragment["actions"].append(
                        {"tool": name, "intent": str(args)[:200]}
                    )
            elif m_role == "reasoning":
                fragment["role"] = "assistant"
                fragment["text"] = ""
                fragment["thoughts"] = [
                    {"text": _process_content(content)[:2000]}
                ]
                fragment["actions"] = []
            else:
                continue

            signal.append(fragment)
    return signal


def extract_signal_from_opencode_session(json_path: str) -> Signal:
    """
    OpenCode vessel session export (single JSON, not JSONL)::

        {"sessionId": "...", "messages": [{"type":"user"|"assistant", "content":[{"text":...}]}, ...]}

    Also accepts a bare list of message objects.
    """
    signal: Signal = []
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw = f.read()
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return signal

    messages: List[Any] = []
    if isinstance(data, dict):
        messages = data.get("messages") or data.get("turns") or []
    elif isinstance(data, list):
        messages = data
    if not isinstance(messages, list):
        return signal

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        m_role = (msg.get("type") or msg.get("role") or "").lower()
        if m_role in ("human",):
            m_role = "user"
        if m_role in ("ai", "model", "bot"):
            m_role = "assistant"
        if m_role not in ("user", "assistant", "system", "agy", "model"):
            continue
        text = _process_content(msg.get("content"))
        if not text.strip() and isinstance(msg.get("text"), str):
            text = msg["text"]
        if not text.strip():
            continue
        if m_role == "model":
            m_role = "assistant"
        fragment: Dict[str, Any] = {
            "role": m_role,
            "timestamp": msg.get("timestamp", "Unknown"),
            "text": text,
        }
        if m_role in ("assistant", "agy"):
            fragment["thoughts"] = []
            fragment["actions"] = []
        signal.append(fragment)
    return signal



def extract_signal_from_agy_transcript(json_path: str) -> Signal:
    """
    Antigravity brain transcript.jsonl:
      USER_INPUT, PLANNER_RESPONSE, tool events, EPHEMERAL_MESSAGE, ...
    """
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
            mtype = msg.get("type") or ""
            ts = msg.get("created_at") or msg.get("timestamp") or "Unknown"
            if mtype == "USER_INPUT":
                text = _process_content(msg.get("content"))
                # strip wrapper noise lightly
                signal.append({"role": "user", "timestamp": ts, "text": text})
            elif mtype == "PLANNER_RESPONSE":
                text = _process_content(msg.get("content"))
                thoughts = []
                thinking = msg.get("thinking")
                if thinking:
                    thoughts = [{"text": str(thinking)[:2000]}]
                signal.append(
                    {
                        "role": "assistant",
                        "timestamp": ts,
                        "text": text,
                        "thoughts": thoughts,
                        "actions": [],
                    }
                )
            # skip tools / ephemeral / checkpoints
    return signal


# Antigravity brain event types that are NOT chat_style roles.
# Real logs often lead with GENERIC/tool rows before USER_INPUT — must not
# short-circuit detect_jsonl_kind to chat_style on those.
_AGY_DIALOGUE_TYPES = frozenset(
    {
        "USER_INPUT",
        "PLANNER_RESPONSE",
        "EPHEMERAL_MESSAGE",
        "CONVERSATION_HISTORY",
    }
)
_AGY_TOOLISH_TYPES = frozenset(
    {
        "GENERIC",
        "RUN_COMMAND",
        "VIEW_FILE",
        "CODE_ACTION",
        "GREP_SEARCH",
        "LIST_DIRECTORY",
        "SEARCH_WEB",
        "INVOKE_SUBAGENT",
        "ASK_QUESTION",
        "CHECKPOINT",
        "ERROR_MESSAGE",
        "SYSTEM_MESSAGE",
        "NOTIFY_USER",
        "BROWSER_ACTION",
        "EDIT_FILE",
        "WRITE_TO_FILE",
        "TASK_BOUNDARY",
    }
)
_AGY_SOURCES = frozenset({"MODEL", "USER_EXPLICIT", "SYSTEM", "USER"})


def _codex_payload_text(content: Any) -> str:
    """Flatten Codex content arrays or plain strings."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or ""))
            else:
                parts.append(str(item))
        return "\n".join(p for p in parts if p).strip()
    if isinstance(content, dict):
        return str(content.get("text") or content.get("message") or "").strip()
    return str(content).strip()


def extract_signal_from_codex_rollout(json_path: str) -> Signal:
    """
    Codex CLI rollout-*.jsonl under ~/.codex/sessions/YYYY/MM/.

    Outer rows: {timestamp, type, payload}
    Dialogue from:
      - response_item + payload.type=message + role user|assistant
      - event_msg + payload.type user_message|agent_message
    Skips tools, reasoning, token_count, developer system injections when huge.
    """
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
            ts = msg.get("timestamp") or "Unknown"
            outer = msg.get("type") or ""
            pl = msg.get("payload")
            if not isinstance(pl, dict):
                continue

            if outer == "response_item" and pl.get("type") == "message":
                role = (pl.get("role") or "").lower()
                if role not in ("user", "assistant"):
                    continue
                text = _codex_payload_text(pl.get("content"))
                # skip AGENTS.md injection / developer blobs
                if role == "user" and text.lstrip().startswith("# AGENTS.md"):
                    continue
                if not text:
                    continue
                signal.append({"role": role, "timestamp": ts, "text": text})
                continue

            if outer == "event_msg":
                et = pl.get("type") or ""
                if et == "user_message":
                    text = (pl.get("message") or pl.get("text") or "").strip()
                    if text and not text.lstrip().startswith("# AGENTS.md"):
                        signal.append(
                            {"role": "user", "timestamp": ts, "text": text}
                        )
                elif et == "agent_message":
                    text = (pl.get("message") or pl.get("text") or "").strip()
                    if text:
                        signal.append(
                            {
                                "role": "assistant",
                                "timestamp": ts,
                                "text": text,
                                "thoughts": [],
                                "actions": [],
                            }
                        )
    return signal


def _looks_like_opencode_session_blob(path: str) -> bool:
    """True if path is a single-JSON OpenCode session export."""
    base = os.path.basename(path)
    norm = path.replace("\\", "/")
    if base.startswith("session-") and base.endswith(".json"):
        return True
    if "/archive/raw/" in norm and base.endswith(".json") and not base.endswith(".jsonl"):
        return True
    # Peek: whole-file JSON with messages[]
    try:
        with open(path, "r", encoding="utf-8") as f:
            head = f.read(4096).lstrip()
        if not head.startswith("{"):
            return False
        # cheap heuristic before full parse
        if '"messages"' in head or '"sessionId"' in head:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return isinstance(data, dict) and isinstance(data.get("messages"), list)
    except (OSError, json.JSONDecodeError, ValueError):
        return False
    return False



def detect_jsonl_kind(json_path: str) -> str:
    if _looks_like_opencode_session_blob(json_path):
        return "opencode_session"
    """Return 'grok_updates' | 'codex_rollout' | 'agy_transcript' | 'chat_style' | 'unknown'.

    Scan enough leading rows: AGY brain transcripts frequently start with
    GENERIC/tool events (still have ``type``), which must not be labeled
    chat_style before USER_INPUT appears.
    """
    saw_agy_toolish = False
    saw_chat_role = False
    saw_codex = False
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            for _ in range(200):
                line = f.readline()
                if not line:
                    break
                if not line.strip():
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(msg, dict):
                    continue
                if _is_grok_updates_line(msg):
                    return "grok_updates"
                t = msg.get("type") or ""
                # Codex rollout envelope
                if t in (
                    "session_meta",
                    "response_item",
                    "event_msg",
                    "turn_context",
                    "world_state",
                ) and isinstance(msg.get("payload"), (dict, type(None))):
                    saw_codex = True
                    if t == "session_meta":
                        return "codex_rollout"
                    continue
                src = msg.get("source") or ""
                if t in _AGY_DIALOGUE_TYPES:
                    return "agy_transcript"
                if t in _AGY_TOOLISH_TYPES or src in _AGY_SOURCES:
                    saw_agy_toolish = True
                    continue
                role = (msg.get("role") or "").lower()
                # Grok / classic chat rows
                if role in ("user", "assistant", "system", "model", "agy") or t in (
                    "user",
                    "assistant",
                    "system",
                    "model",
                    "agy",
                    "reasoning",
                ):
                    saw_chat_role = True
                    # keep scanning a bit — AGY dialogue types win if seen later
                    continue
                if msg.get("type") or msg.get("role"):
                    # unknown typed row: do not commit yet
                    continue
    except OSError:
        pass
    if saw_codex:
        return "codex_rollout"
    if saw_agy_toolish:
        return "agy_transcript"
    if saw_chat_role:
        return "chat_style"
    base = os.path.basename(json_path)
    if base.startswith("rollout-") and base.endswith(".jsonl"):
        return "codex_rollout"
    if json_path.endswith("transcript.jsonl"):
        return "agy_transcript"
    return "unknown"


def extract_signal(json_path: str) -> ExtractResult:
    """
    Surgically extracts conversational signal from a session JSONL.
    Returns a list of turn fragments, or an error string.
    """
    try:
        kind = detect_jsonl_kind(json_path)
        if kind == "opencode_session":
            return extract_signal_from_opencode_session(json_path)
        if kind == "codex_rollout" or (
            kind == "unknown"
            and os.path.basename(json_path).startswith("rollout-")
        ):
            return extract_signal_from_codex_rollout(json_path)
        if kind == "grok_updates" or (
            kind == "unknown" and json_path.endswith("updates.jsonl")
        ):
            signal = extract_signal_from_grok_updates(json_path)
            if not signal:
                chat = json_path.replace("updates.jsonl", "chat_history.jsonl")
                if chat != json_path and os.path.isfile(chat):
                    signal = extract_signal_from_chat_style(chat)
            return signal
        if kind == "agy_transcript":
            return extract_signal_from_agy_transcript(json_path)
        signal = extract_signal_from_chat_style(json_path)
        # Recover: misdetect as chat_style but file is AGY brain transcript
        if (
            (not signal or conversational_turn_count(signal) < 1)
            and (
                json_path.endswith("transcript.jsonl")
                or "antigravity-cli/brain" in json_path.replace("\\", "/")
            )
        ):
            agy_sig = extract_signal_from_agy_transcript(json_path)
            if conversational_turn_count(agy_sig) > conversational_turn_count(
                signal if isinstance(signal, list) else []
            ):
                return agy_sig
        # Recover Codex
        if not signal or conversational_turn_count(signal) < 1:
            if "codex/sessions" in json_path.replace("\\", "/") or os.path.basename(
                json_path
            ).startswith("rollout-"):
                return extract_signal_from_codex_rollout(json_path)
        if not signal or conversational_turn_count(signal) < 1:
            oc_sig = extract_signal_from_opencode_session(json_path)
            if conversational_turn_count(oc_sig) > 0:
                return oc_sig
        return signal
    except Exception as e:
        return f"Extraction Error: {e}"


def conversational_turn_count(skeleton: Any) -> int:
    """Count turns with real dialogue text (user/assistant)."""
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
    """
    Converts a JSON signal skeleton into Markdown dialogue.
    """
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
        role = turn.get("role", "unknown").upper()
        text = turn.get("text", "").strip()
        ts = turn.get("timestamp", "")

        if role == "USER" or role == "SYSTEM":
            label = "USER" if role == "USER" else "SYSTEM"
            md += f"## 👤 {label} ({ts})\n"
            if text:
                md += f"{text}\n\n"
        elif role in ("GEMINI", "MODEL", "ASSISTANT", "AGY"):
            md += f"## 🤖 A.I.M. ({ts})\n"
            thoughts = turn.get("thoughts", [])
            if thoughts:
                md += "> **Internal Monologue:**\n"
                for thought in thoughts:
                    if isinstance(thought, dict):
                        desc = thought.get("description", "") or thought.get(
                            "text", ""
                        )
                        md += f"> * {desc}\n"
                    else:
                        md += f"> * {thought}\n"
                md += "\n"
            if text:
                md += f"{text}\n\n"
            actions = turn.get("actions", [])
            if actions:
                md += "**Tools Executed:**\n"
                for action in actions:
                    tool = action.get("tool", "unknown")
                    intent = action.get("intent", "")
                    md += f"- `{tool}`: {intent}\n"
                md += "\n"
        else:
            if text:
                md += f"## {role} ({ts})\n{text}\n\n"

        md += "---\n\n"
    return md


# late import for fallback path
import os  # noqa: E402


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 extract_signal.py <path_to_jsonl>")
        sys.exit(1)

    result = extract_signal(sys.argv[1])
    if isinstance(result, list):
        print(f"turns={len(result)} conversational={conversational_turn_count(result)}")
    print(json.dumps(result if not isinstance(result, list) else result[:5], indent=2)[:4000])
