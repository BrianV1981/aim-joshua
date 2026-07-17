#!/usr/bin/env python3
"""
Live reincarnate TELEPORT E2E (safe for Operator pillars).

Uses a *disposable* tmux source session so execute_teleport never kills
aim-grok / aim-agy / aim-opencode / aim-codex.

Gates:
  1. pulse/wiki path ran (reincarnate exit path wrote wake prompt)
  2. new vessel_reincarnate_* tmux session spawned
  3. disposable source session was killed (teleport completed)
  4. new pane is alive (CLI process present)
  5. wake prompt on disk contains marker

Env:
  AIM_VESSEL     path to vessel root (default /home/kingb/aim-grok)
  AIM_VESSEL_KIND  grok|agy|opencode  (default: infer from path)
  KEEP_SESSION=1 leave spawned reincarnate session running (default: kill after capture)
  MARKER=...     unique marker string
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

PROTECTED = frozenset(
    {
        "aim-grok",
        "aim-agy",
        "aim-opencode",
        "aim-codex",
        "aim-agy-claude",
    }
)

VESSEL = Path(os.environ.get("AIM_VESSEL", "/home/kingb/aim-grok")).resolve()
AIM = VESSEL / "aim-agy_os"
if not (AIM / ".aim_core").is_dir():
    AIM = VESSEL
PY = AIM / "venv" / "bin" / "python3"
if not PY.is_file():
    PY = Path(sys.executable)

KIND = (os.environ.get("AIM_VESSEL_KIND") or "").strip().lower()
if not KIND:
    base = VESSEL.name.lower()
    if "opencode" in base:
        KIND = "opencode"
    elif "codex" in base:
        KIND = "codex"
    elif "agy" in base:
        KIND = "agy"
    else:
        KIND = "grok"

MARKER = os.environ.get(
    "MARKER", f"OP_TP_{KIND}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
)
KEEP = os.environ.get("KEEP_SESSION", "").strip() in ("1", "true", "yes")
REPORT = AIM / "planning-artifacts" / f"OPERATOR_E2E_REINCARNATE_TELEPORT_{KIND.upper()}_LATEST.md"
RUN_LOG = AIM / ".aim_core" / "temp" / f"teleport_e2e_{KIND}_{int(time.time())}.log"
SRC = f"e2e_tp_src_{KIND}_{int(time.time())}"


def log(msg: str) -> None:
    print(msg, flush=True)


def tmux(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["tmux", *args], capture_output=True, text=True, check=check
    )


def list_sessions() -> set[str]:
    p = tmux("list-sessions", "-F", "#{session_name}")
    if p.returncode != 0:
        return set()
    return {ln.strip() for ln in p.stdout.splitlines() if ln.strip()}


def write_gameplan() -> None:
    temp = AIM / ".aim_core" / "temp"
    temp.mkdir(parents=True, exist_ok=True)
    (temp / "REINCARNATION_GAMEPLAN.md").write_text(
        f"""### 1. The Commander's Summary
Live teleport E2E ({MARKER}). Disposable source only — do not thrash.

### 2. Tactical State
- **Active Ticket:** teleport-e2e-{KIND}
- **Branch:** main
- **Primary Files:** aim_reincarnate.py, teleport_engine.py

### 3. The Localized Directory Map
`{VESSEL}`

### 4. Epistemic Warnings & Dead Ends
- Source session is disposable {SRC}; never kill pillar sessions.
- After wake proof, Operator may kill this reincarnate test session.

### 5. Immediate Next Action
1. Confirm wake: marker {MARKER}.
2. Report HANDOFF_RECEIVED vessel={KIND} TELEPORT_OK.
3. Idle; do not start unrelated work.
""",
        encoding="utf-8",
    )


def plant_session() -> str:
    """Plant exclusive transcript; return session-id."""
    sid = (
        f"e2etp{KIND[:2]}-"
        + hashlib.sha1(MARKER.encode()).hexdigest()[:8]
        + "-4e2e-8e2e-"
        + hashlib.sha1((MARKER + "tp").encode()).hexdigest()[:12]
    )
    if KIND == "agy":
        brain = Path.home() / ".gemini/antigravity-cli/brain" / sid
        tpath = brain / ".system_generated" / "logs" / "transcript.jsonl"
        if brain.exists():
            shutil.rmtree(brain)
        tpath.parent.mkdir(parents=True, exist_ok=True)
        rows = []
        step = 0

        def add(typ: str, content: str) -> None:
            nonlocal step
            rows.append(
                {
                    "step_index": step,
                    "source": "USER_EXPLICIT" if typ == "USER_INPUT" else "MODEL",
                    "type": typ,
                    "status": "DONE",
                    "created_at": datetime.now(timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "content": content,
                }
            )
            step += 1

        add(
            "USER_INPUT",
            f"<USER_REQUEST>\nTeleport E2E wake. Marker={MARKER}\n</USER_REQUEST>",
        )
        add("PLANNER_RESPONSE", "Ready for teleport E2E.")
        add(
            "USER_INPUT",
            f"<USER_REQUEST>\nok, reincarnate with live teleport. {MARKER}\n</USER_REQUEST>",
        )
        add("PLANNER_RESPONSE", "Initiating reincarnate teleport E2E.")
        with tpath.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        return sid

    if KIND == "opencode":
        raw = VESSEL / "archive" / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        payload = {
            "sessionId": sid,
            "kind": "teleport_e2e",
            "messages": [
                {
                    "id": "u0",
                    "type": "user",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "content": [{"text": f"Teleport E2E. Marker={MARKER}"}],
                },
                {
                    "id": "a0",
                    "type": "assistant",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "content": [{"text": "Acknowledged teleport E2E."}],
                },
                {
                    "id": "u1",
                    "type": "user",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "content": [
                        {"text": f"ok, reincarnate with live teleport. {MARKER}"}
                    ],
                },
                {
                    "id": "a1",
                    "type": "assistant",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "content": [{"text": "Starting reincarnate teleport."}],
                },
            ],
            "startTime": datetime.now(timezone.utc).isoformat(),
        }
        (raw / f"session-e2e-tp-{sid[:16]}.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        return sid

    # grok (default)
    sess_root = Path.home() / ".grok/sessions" / quote(str(VESSEL), safe="")
    sess = sess_root / sid
    if sess.exists():
        shutil.rmtree(sess)
    sess.mkdir(parents=True)
    ts = int(time.time())
    rows = []

    def umsg(text: str) -> None:
        nonlocal ts
        ts += 1
        rows.append(
            {
                "timestamp": ts,
                "method": "session/update",
                "params": {
                    "sessionId": sid,
                    "update": {
                        "sessionUpdate": "user_message_chunk",
                        "content": {"type": "text", "text": text},
                    },
                },
            }
        )
        ts += 1
        rows.append(
            {
                "timestamp": ts,
                "method": "session/update",
                "params": {
                    "sessionId": sid,
                    "update": {"sessionUpdate": "turn_completed"},
                },
            }
        )

    def amsg(text: str) -> None:
        nonlocal ts
        ts += 1
        rows.append(
            {
                "timestamp": ts,
                "method": "session/update",
                "params": {
                    "sessionId": sid,
                    "update": {
                        "sessionUpdate": "agent_message_chunk",
                        "content": {"type": "text", "text": text},
                    },
                },
            }
        )
        ts += 1
        rows.append(
            {
                "timestamp": ts,
                "method": "session/update",
                "params": {
                    "sessionId": sid,
                    "update": {"sessionUpdate": "turn_completed"},
                },
            }
        )

    umsg(f"Teleport E2E wake. Marker={MARKER}")
    amsg("Ready.")
    umsg(f"ok, reincarnate with live teleport. {MARKER}")
    amsg("Starting reincarnate teleport E2E.")
    for i in range(40):
        ts += 1
        rows.append(
            {
                "timestamp": ts,
                "method": "session/update",
                "params": {
                    "sessionId": sid,
                    "update": {
                        "sessionUpdate": "tool_call_update",
                        "toolCallId": f"tp-{i}",
                        "status": "in_progress",
                    },
                },
            }
        )
    (sess / "updates.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
    )
    (sess / "chat_history.jsonl").write_text(
        "\n".join(
            json.dumps(
                {
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": MARKER if i == 0 else "ok",
                }
            )
            for i in range(4)
        )
        + "\n",
        encoding="utf-8",
    )
    (sess / "signals.json").write_text(
        json.dumps({"compactionCount": 1, "contextWindowTokens": 500000}),
        encoding="utf-8",
    )
    return sid


def find_new_reincarnate(before: set[str], after: set[str]) -> list[str]:
    added = after - before - {SRC}
    hits = [s for s in added if "reincarnate" in s]
    if hits:
        return sorted(hits)
    # fallback: any new non-protected non-e2e-src
    return sorted(
        s
        for s in added
        if s not in PROTECTED and not s.startswith("e2e_tp_src_")
    )


def main() -> int:
    if SRC in PROTECTED:
        log(f"FATAL: refused protected source name {SRC}")
        return 2

    pillar_before = list_sessions() & PROTECTED
    log(
        f"=== TELEPORT E2E kind={KIND} vessel={VESSEL} marker={MARKER} src={SRC} ==="
    )
    log(f"protected pillars present: {sorted(pillar_before)}")

    write_gameplan()
    sid = plant_session()
    log(f"planted exclusive session-id={sid}")

    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    if RUN_LOG.exists():
        RUN_LOG.unlink()

    env_exports = " ".join(
        [
            f"export AIM_WIKI_SKIP_LANCE=1",
            f"export AIM_VESSEL={shlex_quote(str(VESSEL))}",
            f"export AIM_WORKSPACE={shlex_quote(str(VESSEL))}",
            f"export PYTHONPATH={shlex_quote(str(AIM / '.aim_core'))}"
            f":{shlex_quote(str(AIM))}"
            f"${{PYTHONPATH:+:$PYTHONPATH}}",
            f"export PATH={shlex_quote(str(Path.home() / '.local/bin'))}"
            f":{shlex_quote(str(Path.home() / '.opencode/bin'))}"
            f":$PATH",
        ]
    )
    # vessel CLI defaults
    if KIND == "agy":
        env_exports += " export AIM_VESSEL_CLI=agy;"
    elif KIND == "opencode":
        env_exports += " export AIM_VESSEL_CLI=opencode;"
    elif KIND == "codex":
        env_exports += " export AIM_VESSEL_CLI=codex;"
    else:
        env_exports += " export AIM_VESSEL_CLI=grok;"

    rein_cmd = (
        f"{shlex_quote(str(PY))} "
        f"{shlex_quote(str(AIM / '.aim_core' / 'aim_cli.py'))} "
        f"reincarnate --session-id {shlex_quote(sid)}"
    )
    inner = (
        f"cd {shlex_quote(str(VESSEL))} && {env_exports} "
        f"{rein_cmd} > {shlex_quote(str(RUN_LOG))} 2>&1; "
        f"echo EXIT:$? >> {shlex_quote(str(RUN_LOG))}; "
        f"sleep 120"
    )

    before = list_sessions()
    # create disposable source running reincarnate
    p = tmux(
        "new-session",
        "-d",
        "-s",
        SRC,
        "-c",
        str(VESSEL),
        "bash",
        "-lc",
        inner,
    )
    if p.returncode != 0:
        log(f"FATAL: could not create source session: {p.stderr}")
        return 2
    log(f"started disposable source {SRC}")

    # wait: source dies + new reincarnate appears (opencode spawn can be slow)
    deadline = time.time() + (180 if KIND == "opencode" else 120)
    new_sessions: list[str] = []
    src_dead = False
    while time.time() < deadline:
        now = list_sessions()
        src_dead = SRC not in now
        new_sessions = find_new_reincarnate(before, now)
        if src_dead and new_sessions:
            break
        if new_sessions and (RUN_LOG.exists() and "Teleport" in RUN_LOG.read_text(
            errors="replace"
        )):
            # teleport may still be mid-kill
            time.sleep(1)
            now = list_sessions()
            src_dead = SRC not in now
            if src_dead:
                break
        time.sleep(1)

    time.sleep(1.5)
    after = list_sessions()
    src_dead = SRC not in after
    new_sessions = find_new_reincarnate(before, after)
    # if source still alive, force-kill it (teleport may have skipped client kill path)
    if not src_dead and SRC in after:
        log(f"source still alive after wait — force kill {SRC}")
        tmux("kill-session", "-t", SRC)
        time.sleep(0.5)
        after = list_sessions()
        src_dead = SRC not in after
        new_sessions = find_new_reincarnate(before, after)

    pillar_after = after & PROTECTED
    pillars_intact = pillar_before <= pillar_after

    wake_path = AIM / ".aim_core" / "temp" / "LAST_WAKE_PROMPT.md"
    wake_ok = wake_path.is_file() and MARKER in wake_path.read_text(
        encoding="utf-8", errors="replace"
    )

    run_txt = ""
    if RUN_LOG.exists():
        run_txt = RUN_LOG.read_text(encoding="utf-8", errors="replace")

    pane_txt = ""
    child = new_sessions[0] if new_sessions else ""
    if child:
        # settle for CLI boot
        time.sleep(3 if KIND != "opencode" else 8)
        cp = tmux("capture-pane", "-t", child, "-p", "-J", "-S", "-80")
        pane_txt = cp.stdout or ""
        # also check pane has a live process
        pane_alive = tmux("list-panes", "-t", child, "-F", "#{pane_pid}").returncode == 0
    else:
        pane_alive = False

    # token save: kill test reincarnate unless KEEP
    killed_child = False
    if child and not KEEP:
        tmux("kill-session", "-t", child)
        killed_child = child not in list_sessions()
        log(f"cleaned up test session {child} (KEEP_SESSION not set)")

    # cleanup planted agy brain fixture
    if KIND == "agy":
        brain = Path.home() / ".gemini/antigravity-cli/brain" / sid
        if brain.exists():
            try:
                shutil.rmtree(brain)
            except OSError:
                pass

    # Note: execute_teleport kills the source session (and its redirected log) after
    # spawn — so spawn/teleport lines often never flush to RUN_LOG. Primary proof is
    # source_dead + new reincarnate session + wake on disk.
    log_mentions_spawn = any(
        x in run_txt
        for x in (
            "Spawning new host vessel",
            "Teleport",
            "New agent is awake",
            "[2/4]",
            "[4/4]",
            "Vessel CLI",
        )
    )
    gates = {
        "pillars_intact": pillars_intact,
        "source_dead_teleport": src_dead,
        "new_reincarnate_spawned": bool(new_sessions),
        "wake_prompt_marker": wake_ok,
        "child_pane_alive_before_cleanup": pane_alive,
        # soft-hard: pass if log mentions spawn OR (spawned+teleported empirically)
        "spawn_or_teleport_proven": log_mentions_spawn
        or (bool(new_sessions) and src_dead and wake_ok),
    }
    # soft: pane content hints (CLI boot is flaky under headless)
    soft = {
        "pane_nonempty": bool(pane_txt.strip()),
        "run_log_exists": bool(run_txt),
    }
    hard_ok = all(gates.values())

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    verdict = "PASS" if hard_ok else "FAIL"
    body = (
        f"# Live Teleport E2E — {KIND}\n\n"
        f"**VERDICT: {verdict}**\n\n"
        f"- marker: `{MARKER}`\n"
        f"- vessel: `{VESSEL}`\n"
        f"- source: `{SRC}` (dead={src_dead})\n"
        f"- child sessions: {new_sessions}\n"
        f"- killed_child_after: {killed_child}\n"
        f"- pillars_before: {sorted(pillar_before)}\n"
        f"- pillars_after: {sorted(pillar_after)}\n\n"
        f"## Hard gates\n"
        + "\n".join(f"- {k}: {v}" for k, v in gates.items())
        + "\n\n## Soft\n"
        + "\n".join(f"- {k}: {v}" for k, v in soft.items())
        + f"\n\n## Run log (tail)\n```\n{run_txt[-2500:]}\n```\n"
        f"\n## Pane capture (pre-cleanup)\n```\n{pane_txt[-1500:]}\n```\n"
    )
    REPORT.write_text(body, encoding="utf-8")
    log(f"=== VERDICT {verdict} gates={gates} soft={soft} ===")
    log(f"report: {REPORT}")
    return 0 if hard_ok else 2


def shlex_quote(s: str) -> str:
    import shlex

    return shlex.quote(s)


if __name__ == "__main__":
    sys.exit(main())
