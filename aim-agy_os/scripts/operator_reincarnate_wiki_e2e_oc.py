#!/usr/bin/env python3
"""OpenCode-native operator reincarnation → memory-wiki E2E."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

VESSEL = Path(os.environ.get("AIM_VESSEL", os.getcwd())).resolve()
AIM = VESSEL / "aim-agy_os"
if not (AIM / ".aim_core").is_dir():
    AIM = VESSEL
RAW = VESSEL / "archive" / "raw"
# Prefer nested engine wiki (monolithic daemon writes here) over stale vessel-root wiki.
if (AIM / "memory-wiki" / "pages").is_dir() or (AIM / "memory-wiki").is_dir():
    WIKI = AIM / "memory-wiki"
elif (VESSEL / "memory-wiki").is_dir():
    WIKI = VESSEL / "memory-wiki"
else:
    WIKI = AIM / "memory-wiki"
REPORT = AIM / "planning-artifacts" / "OPERATOR_E2E_REINCARNATE_WIKI_OC_LATEST.md"
MARKER = os.environ.get(
    "MARKER", f"OP_WIKI_OC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
)
DIRECTIVES = [
    f"OPERATOR_DIRECTIVE_1: Codename COPPER_MOTH for OpenCode. Marker={MARKER}",
    f"OPERATOR_DIRECTIVE_2: Use exclusive session-id pulse. Marker={MARKER}",
    f"OPERATOR_DIRECTIVE_3: Never claim OC wiki works without grepping {MARKER}.",
]


def log(m):
    print(m, flush=True)


def main():
    sid = "oc-e2e-" + hashlib.sha1(MARKER.encode()).hexdigest()[:12]
    session_id = hashlib.sha1(MARKER.encode()).hexdigest()[:8] + "-4e2e-8e2e-" + hashlib.sha1(
        (MARKER + "y").encode()
    ).hexdigest()[:12]
    messages = []
    msgs = [
        "Wake up. OpenCode reincarnation memory test.",
        DIRECTIVES[0],
        DIRECTIVES[1],
        DIRECTIVES[2],
        "ok, reincarnate so memory-wiki keeps these directives.",
    ]
    for i, t in enumerate(msgs):
        messages.append(
            {
                "id": f"u{i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "user",
                "content": [{"text": t}],
            }
        )
        messages.append(
            {
                "id": f"a{i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "assistant",
                "content": [{"text": f"Acknowledged: {t[:100]}"}],
            }
        )
    payload = {
        "sessionId": session_id,
        "kind": "operator_e2e",
        "messages": messages,
        "startTime": datetime.now(timezone.utc).isoformat(),
    }
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"session-e2e-{sid}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log(f"=== OC E2E marker={MARKER} sessionId={session_id} file={path} ===")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(AIM / ".aim_core") + os.pathsep + env.get("PYTHONPATH", "")
    daemon = WIKI / "daemon.log"
    WIKI.mkdir(parents=True, exist_ok=True)
    off = daemon.stat().st_size if daemon.exists() else 0
    cmd = [
        sys.executable,
        str(AIM / ".aim_core" / "handoff_pulse_generator.py"),
        "--session-id",
        session_id,
    ]
    p = subprocess.run(
        cmd, cwd=str(VESSEL), env=env, capture_output=True, text=True, timeout=120
    )
    log(p.stdout or "")
    log(p.stderr or "")
    log(f"pulse exit={p.returncode}")

    daemon_new = ""
    deadline = time.time() + 30
    while time.time() < deadline:
        if daemon.exists():
            daemon_new = daemon.read_bytes()[off:].decode("utf-8", "replace")
            if "[SUCCESS] Deterministic" in daemon_new:
                time.sleep(0.3)
                break
        time.sleep(0.3)
    log("--- daemon ---\n" + (daemon_new[-1500:] if daemon_new else "(empty)"))

    pages = []
    for pg in (WIKI / "pages").glob("*.md") if (WIKI / "pages").is_dir() else []:
        if MARKER in pg.read_text(errors="replace"):
            pages.append(str(pg))
    fr = VESSEL / "continuity" / "LAST_SESSION_FLIGHT_RECORDER.md"
    if not fr.exists():
        fr = AIM / ".aim_core" / "temp" / "LAST_SESSION_FLIGHT_RECORDER.md"
    fr_ok = fr.exists() and MARKER in fr.read_text(errors="replace")
    arch_ok = any(
        MARKER in a.read_text(errors="replace")
        for a in (VESSEL / "archive" / "history").glob("*.md")
    )
    gates = {
        "pulse_exit_0": p.returncode == 0,
        "exclusive_in_stdout": session_id in (p.stdout or ""),
        "archive_marker": arch_ok,
        "flight_marker": fr_ok,
        "daemon_success": "[SUCCESS] Deterministic wiki reincarnation sequence complete."
        in daemon_new,
        "wiki_pages_marker": len(pages) > 0,
    }
    hard = all(gates.values())
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"# OpenCode Operator E2E\n\n**VERDICT: {'PASS' if hard else 'FAIL'}**\n\n"
        f"marker={MARKER}\nsession={session_id}\n\n"
        + "\n".join(f"- {k}: {v}" for k, v in gates.items())
        + "\n\npages:\n"
        + "\n".join(pages)
        + f"\n\nstdout:\n{(p.stdout or '')[-1500:]}\n",
        encoding="utf-8",
    )
    log(f"=== VERDICT {'PASS' if hard else 'FAIL'} {gates} ===")
    try:
        path.unlink()
    except Exception:
        pass
    return 0 if hard else 2


if __name__ == "__main__":
    sys.exit(main())
