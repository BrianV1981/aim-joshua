"""TDD: reincarnation process hygiene (Lane 1) — aim-opencode port.

Locks:
1. Reincarnate background path must NOT double-spawn session_summarizer
2. aim status reads .aim_core/temp/CURRENT_PULSE.md (canonical handoff path)
3. blackbox_vault failure is WARNING, never FATAL
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path
from unittest import mock

import pytest

CORE = Path(__file__).resolve().parents[1] / ".aim_core"
sys.path.insert(0, str(CORE))


def test_background_tasks_does_not_popen_session_summarizer():
    from reincarnation import background_tasks

    src = inspect.getsource(background_tasks.trigger_background_pipelines)
    code_lines = [
        ln
        for ln in src.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    code = "\n".join(code_lines)
    assert "subprocess.Popen" not in code
    assert "handoff_pulse_generator.py" in code
    assert "session_summarizer.py" not in code


def test_background_tasks_runs_pulse_once_with_session_id(tmp_path):
    from reincarnation.background_tasks import trigger_background_pipelines

    runs = []

    def fake_run(args, **kwargs):
        runs.append(list(args))
        return mock.Mock(returncode=0)

    aim_root = tmp_path / "aim-agy_os"
    (aim_root / "venv" / "bin").mkdir(parents=True)
    with mock.patch("subprocess.run", side_effect=fake_run):
        with mock.patch("subprocess.Popen") as popen:
            trigger_background_pipelines(str(aim_root), str(tmp_path), session_id="uuid-abc")
            popen.assert_not_called()

    assert runs
    pulse = runs[0]
    assert any("handoff_pulse_generator.py" in str(a) for a in pulse)
    assert "--session-id" in pulse
    assert "uuid-abc" in pulse
    assert not any("session_summarizer.py" in str(a) for run in runs for a in run)


def test_cmd_status_prefers_temp_current_pulse(tmp_path, monkeypatch, capsys):
    os_dir = tmp_path / "aim-agy_os"
    temp = os_dir / ".aim_core" / "temp"
    cont = os_dir / "continuity"
    temp.mkdir(parents=True)
    cont.mkdir(parents=True)
    (temp / "CURRENT_PULSE.md").write_text("# FROM TEMP\nlast turns\n", encoding="utf-8")
    (cont / "CURRENT_PULSE.md").write_text("# FROM CONTINUITY\n", encoding="utf-8")

    import aim_cli

    monkeypatch.setattr(aim_cli, "BASE_DIR", str(os_dir))
    aim_cli.cmd_status(mock.Mock())
    out = capsys.readouterr().out
    assert "FROM TEMP" in out
    assert "FROM CONTINUITY" not in out


def test_cmd_status_falls_back_to_continuity(tmp_path, monkeypatch, capsys):
    os_dir = tmp_path / "aim-agy_os"
    cont = os_dir / "continuity"
    cont.mkdir(parents=True)
    (cont / "CURRENT_PULSE.md").write_text("# FROM CONTINUITY ONLY\n", encoding="utf-8")

    import aim_cli

    monkeypatch.setattr(aim_cli, "BASE_DIR", str(os_dir))
    aim_cli.cmd_status(mock.Mock())
    assert "FROM CONTINUITY ONLY" in capsys.readouterr().out


def test_vault_session_failure_label_is_warning(capsys, tmp_path, monkeypatch):
    import blackbox_vault

    jsonl = tmp_path / "chat_history.jsonl"
    jsonl.write_bytes(b'{"type":"user"}\n')
    monkeypatch.setattr(blackbox_vault, "BLACKBOX_DIR", str(tmp_path / "box"))

    def boom(*_a, **_k):
        raise RuntimeError("No recommended backend was available")

    monkeypatch.setattr(blackbox_vault, "get_or_create_key", boom)
    ok = blackbox_vault.vault_session(str(jsonl))
    assert ok is False
    err = capsys.readouterr().out
    assert "[WARNING]" in err
    assert "[FATAL]" not in err


def test_vault_session_source_has_no_fatal_label():
    import blackbox_vault

    src = inspect.getsource(blackbox_vault.vault_session)
    assert "[FATAL]" not in src
    assert "[WARNING]" in src
