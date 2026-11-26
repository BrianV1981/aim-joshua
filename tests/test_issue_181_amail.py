import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = REPO_ROOT / "joshua_os" / ".aim_core"


def test_agents_md_and_template_lockstep_have_amail_section():
    root = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    template = (REPO_ROOT / "joshua_os" / ".aim_core" / "templates" / "default_AGENTS.md").read_text(
        encoding="utf-8"
    )
    assert root == template
    assert "## 8c. THE A-MAIL PROTOCOL (INTER-AGENT COMMUNICATION)" in root
    for token in ("amail", "aim-mail", "--operator-approved", "max_hops=1", "DND", "aim-communicate"):
        assert token in root


def test_fleet_orchestration_documents_amail_as_sole_transport():
    text = (REPO_ROOT / "joshua_os" / "joshua_os_docs" / "FLEET_ORCHESTRATION.md").read_text(
        encoding="utf-8"
    )
    assert "## 4. Inter-Agent Communication (A-Mail / `aim-mailbox`)" in text
    assert "amail" in text and "aim-mail" in text
    assert "--operator-approved" in text and "max_hops=1" in text
    assert "aim-communicate" in text  # only as the explicit deprecation


def test_readme_routes_inter_agent_comms_to_amail():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "A-Mail Inter-Agent Communication" in text
    assert "`aim-communicate` live multi-agent pane messaging" not in text
    assert "A-Mail (`amail` / `aim-mail`)" in text


def _doctor_env(path_value: str, mailbox: Path) -> dict:
    env = os.environ.copy()
    env["PATH"] = path_value
    env["AIM_MAILBOX_DIR"] = str(mailbox)
    return env


def test_doctor_reports_missing_amail_non_blocking(tmp_path):
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    env = _doctor_env(str(empty_bin), tmp_path / "missing-mailbox")
    res = subprocess.run(
        [sys.executable, str(CORE_DIR / "aim_doctor.py")],
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "[WARNING] A-Mail CLI not found" in res.stdout
    assert "[WARNING] A-Mail mailbox missing" in res.stdout


def test_doctor_reports_amail_cli_and_mailbox_non_blocking(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    (fake_bin / "amail").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (fake_bin / "amail").chmod(0o755)
    if os.name == "nt":
        (fake_bin / "amail.cmd").write_text("@echo off\r\n", encoding="utf-8")
    mailbox = tmp_path / "mailbox"
    mailbox.mkdir()

    env = _doctor_env(str(fake_bin), mailbox)
    res = subprocess.run(
        [sys.executable, str(CORE_DIR / "aim_doctor.py")],
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "[OK] A-Mail CLI (amail)" in res.stdout
    assert "[OK] A-Mail Mailbox" in res.stdout
