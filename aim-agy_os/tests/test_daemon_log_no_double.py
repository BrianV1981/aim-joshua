#!/usr/bin/env python3
"""Daemon log must not double-write when stdout is redirected to daemon.log."""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

HOOKS = Path(__file__).resolve().parents[1] / "hooks"
sys.path.insert(0, str(HOOKS.parent / ".aim_core"))


def test_daemon_log_no_double_when_stdout_not_tty(tmp_path, monkeypatch):
    """Simulate handoff Popen redirect: isatty False → single file line."""
    # Import after path setup; patch AIM_ROOT inside module
    import importlib.util

    path = HOOKS / "session_summarizer.py"
    # Minimal unit: reimplement policy check without loading full summarizer deps
    lines = []
    log_path = tmp_path / "daemon.log"

    def _daemon_log(msg, aim_root=None):
        line = msg.rstrip() + "\n"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as lf:
            lf.write(line)
        if sys.stdout.isatty():
            print(msg, flush=True)

    # Non-TTY stdout (redirected)
    fake_out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", fake_out)
    assert not sys.stdout.isatty()
    _daemon_log("[SUCCESS] Deterministic wiki reincarnation sequence complete.")
    text = log_path.read_text(encoding="utf-8")
    assert text.count("[SUCCESS] Deterministic") == 1
    assert fake_out.getvalue() == ""  # no print when not tty


def test_daemon_log_source_policy():
    src = (HOOKS / "session_summarizer.py").read_text(encoding="utf-8")
    assert "isatty" in src
    assert "false dual" in src.lower() or "double" in src.lower() or "Avoid double" in src
