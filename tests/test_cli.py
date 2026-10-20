import subprocess
import os

def test_aim_help():
    # Ensure the wrapper script can run --help successfully
    result = subprocess.run(["./aim", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower() or "options:" in result.stdout.lower()

def test_aim_doctor():
    result = subprocess.run(["./aim", "doctor"], capture_output=True, text=True)
    assert result.returncode == 0
    out = result.stdout.lower()
    assert "doctor" in out or "diagnostic" in out or "status" in out

def test_aim_swarm_removed():
    # Deprecated swarm subcommand must not be exposed on the CLI router
    help_res = subprocess.run(["./aim", "--help"], capture_output=True, text=True)
    assert help_res.returncode == 0
    assert "Manage co-agent swarms" not in help_res.stdout
    swarm_res = subprocess.run(["./aim", "swarm"], capture_output=True, text=True)
    assert swarm_res.returncode == 2

def test_readme_ecosystem_block():
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()
    assert "<!-- AIM_ECOSYSTEM_START -->" in readme
    assert "https://github.com/BrianV1981/aim-ecosystem" in readme
    assert "<!-- AIM_ECOSYSTEM_END -->" in readme

def test_cmd_update_preserves_coagent_blueprint_and_config(tmp_path):
    import json
    import shutil
    import sys

    # Build a synthetic co-agent node in tmp_path
    node_dir = tmp_path / "aim-mock-node"
    node_os = node_dir / "joshua_os"
    node_core = node_os / ".aim_core"
    node_core.mkdir(parents=True)

    # Seed co-agent blueprint and tenant artifacts that MUST be preserved
    (node_dir / "AGENTS.md").write_text("# Custom Co-Agent Blueprint", encoding="utf-8")
    (node_dir / "TOOLS.md").write_text("# Custom Tools", encoding="utf-8")
    (node_dir / "manifest.json").write_text('{"name": "aim-mock-node"}', encoding="utf-8")
    (node_dir / "memory-wiki").mkdir()
    (node_dir / "memory-wiki" / "index.md").write_text("# Node Wiki", encoding="utf-8")
    (node_dir / "artifacts").mkdir()
    (node_dir / "artifacts" / "AUDIT_TEST.md").write_text("# Living Audit", encoding="utf-8")

    # Seed a custom CONFIG.json and an outdated dummy aim_cli.py in the mock node
    custom_cfg = {"settings": {"github_projects": {"number": 99}}}
    (node_core / "CONFIG.json").write_text(json.dumps(custom_cfg), encoding="utf-8")
    for fname in ("config_utils.py", "cli_vault.py", "cli_memory.py", "aim_cli.py"):
        shutil.copy2(f"joshua_os/.aim_core/{fname}", node_core / fname)

    res = subprocess.run(
        [sys.executable, str(node_core / "aim_cli.py"), "update", "--source", os.getcwd(), "--skip-deps"],
        cwd=str(node_dir),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    assert "Sovereign Engine Update Complete" in res.stdout
    assert (node_dir / "AGENTS.md").read_text(encoding="utf-8") == "# Custom Co-Agent Blueprint"
    assert (node_dir / "TOOLS.md").read_text(encoding="utf-8") == "# Custom Tools"
    assert (node_dir / "manifest.json").read_text(encoding="utf-8") == '{"name": "aim-mock-node"}'
    assert (node_dir / "memory-wiki" / "index.md").read_text(encoding="utf-8") == "# Node Wiki"
    assert (node_dir / "artifacts" / "AUDIT_TEST.md").read_text(encoding="utf-8") == "# Living Audit"
    assert json.loads((node_core / "CONFIG.json").read_text(encoding="utf-8")) == custom_cfg
    assert (node_os / "handoff").is_dir()
    assert (node_os / "hooks").is_dir()


def test_legacy_modules_import_without_relative_import_error():
    import importlib
    import sys

    core_dir = os.path.abspath("joshua_os/.aim_core")
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)

    for mod_name in ("audit_tools", "recall_tools", "sovereign_sync", "cli_vault", "cli_memory", "aim_cli"):
        mod = importlib.import_module(mod_name)
        assert mod is not None


def test_cmd_clean_defined_and_dispatches():
    import sys
    from unittest.mock import patch

    core_dir = os.path.abspath("joshua_os/.aim_core")
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)

    import aim_cli
    import cli_memory

    assert hasattr(aim_cli, "cmd_clean")
    with patch.object(cli_memory, "_run_script") as mock_run:
        aim_cli.cmd_clean(object())
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0].endswith("maintenance.py")


def test_cmd_bug_requires_commanders_intent():
    res = subprocess.run(["./aim", "bug", "Missing flags test"], capture_output=True, text=True)
    assert res.returncode == 1
    assert "Commander's Intent Required" in res.stdout


def test_cmd_bug_dispatches_to_gh_with_intent():
    import argparse
    import sys
    from unittest.mock import patch

    core_dir = os.path.abspath("joshua_os/.aim_core")
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)

    import aim_cli

    args = argparse.Namespace(
        title="Feature: Add unit tests",
        context="Testing cmd_bug",
        failure="Need coverage",
        intent="1. Mock gh CLI",
    )
    with patch("aim_cli.subprocess.run") as mock_run:
        aim_cli.cmd_bug(args)
        mock_run.assert_called_once()
        called_cmd = mock_run.call_args[0][0]
        assert called_cmd[:3] == ["gh", "issue", "create"]
        assert "--label" in called_cmd
        assert "enhancement" in called_cmd


def test_cmd_status_reads_current_pulse(tmp_path, capsys):
    import sys
    from unittest.mock import patch

    core_dir = os.path.abspath("joshua_os/.aim_core")
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)

    import aim_cli

    pulse_dir = tmp_path / ".aim_core" / "temp"
    pulse_dir.mkdir(parents=True)
    (pulse_dir / "CURRENT_PULSE.md").write_text("# Pulse Active\nStatus: Green", encoding="utf-8")

    with patch.object(aim_cli, "OS_DIR", str(tmp_path)):
        aim_cli.cmd_status(object())
        captured = capsys.readouterr()
        assert "Pulse Active" in captured.out


def test_cmd_fix_creates_worktree_and_copies_config(tmp_path):
    import argparse
    import sys
    from unittest.mock import patch

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
    (repo_dir / "README.md").write_text("init", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, capture_output=True)

    cfg_dir = repo_dir / ".aim_core"
    cfg_dir.mkdir()
    (cfg_dir / "CONFIG.json").write_text('{"test": true}', encoding="utf-8")

    core_dir = os.path.abspath("joshua_os/.aim_core")
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    import aim_cli

    with patch.object(aim_cli, "BASE_DIR", str(repo_dir)), patch.object(aim_cli, "PROJECT_ROOT", str(repo_dir)):
        aim_cli.cmd_fix(argparse.Namespace(id="999"))

    wt = repo_dir / "workspace" / "issue-999"
    assert wt.is_dir()
    assert (wt / ".aim_core" / "CONFIG.json").read_text(encoding="utf-8") == '{"test": true}'


def test_vault_subparser_missing_verb_exits_2():
    res = subprocess.run(["./aim", "vault"], capture_output=True, text=True)
    assert res.returncode == 2
    assert "Usage: aim vault" in res.stdout


def test_installers_have_home_guard_and_clean_readme_onboarding():
    with open("joshua_os/install.sh", "r", encoding="utf-8") as f:
        install_sh = f.read()
    with open("joshua_os/install-agent.sh", "r", encoding="utf-8") as f:
        install_agent_sh = f.read()
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    assert 'if [ "$CURRENT_DIR" = "$HOME" ]' in install_sh
    assert "cp -a joshua_os ../" in install_sh
    assert "cp -a * ../" not in install_sh
    assert 'for entry in "joshua_os/" "aim" "workspace/" "archive/"; do' in install_sh
    assert 'if [ "$CURRENT_DIR" = "$HOME" ]' in install_agent_sh
    assert 'for entry in "joshua_os/" "aim" "workspace/" "archive/"; do' in install_agent_sh
    assert "mkdir -p ~/my-project && cd ~/my-project" in readme
    assert "Customizing J.O.S.H.U.A. for Your New Project" in readme


def test_ensure_consumer_gitignore_populates_and_skips_upstream(tmp_path):
    import sys

    core_dir = os.path.abspath("joshua_os/.aim_core")
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    import aim_cli

    consumer_dir = tmp_path / "aim-consumer"
    consumer_dir.mkdir()
    assert aim_cli.ensure_consumer_gitignore(str(consumer_dir)) is True
    gi_text = (consumer_dir / ".gitignore").read_text(encoding="utf-8")
    assert "joshua_os/" in gi_text
    assert "aim" in gi_text
    assert "workspace/" in gi_text
    assert "archive/" in gi_text

    # Second run is idempotent
    assert aim_cli.ensure_consumer_gitignore(str(consumer_dir)) is False

    # Upstream engine repo is skipped
    upstream_dir = tmp_path / "aim-joshua"
    upstream_dir.mkdir()
    assert aim_cli.ensure_consumer_gitignore(str(upstream_dir)) is False
    assert not (upstream_dir / ".gitignore").exists()


def test_git_push_changes_pure_python_and_untracked_warning(tmp_path, capsys):
    import sys

    core_dir = os.path.abspath("joshua_os/.aim_core")
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    import aim_cli

    origin_dir = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(origin_dir)], check=True, capture_output=True)

    repo_dir = tmp_path / "repo"
    subprocess.run(["git", "clone", str(origin_dir), str(repo_dir)], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)

    (repo_dir / "VERSION").write_text("v0.7.5", encoding="utf-8")
    (repo_dir / "tracked.txt").write_text("v1", encoding="utf-8")
    subprocess.run(["git", "add", "VERSION", "tracked.txt"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo_dir, check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=repo_dir, check=True, capture_output=True)

    # Modify tracked file and create an untracked file
    (repo_dir / "tracked.txt").write_text("v2", encoding="utf-8")
    (repo_dir / "untracked.txt").write_text("new file", encoding="utf-8")

    aim_cli.git_push_changes("Fix: pure python push", cwd=str(repo_dir), include_untracked=False)
    captured = capsys.readouterr()
    assert "Successfully pushed A.I.M. version: v0.7.5" in captured.out
    assert "untracked.txt" in captured.err

    # Now push with include_untracked=True
    aim_cli.git_push_changes("Feat: stage untracked", cwd=str(repo_dir), include_untracked=True)
    status_out = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo_dir, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert status_out == ""


def test_cross_platform_windows_launchers_and_venv_resolution(tmp_path):
    import sys
    from unittest.mock import patch

    assert os.path.isfile("aim.ps1")
    assert os.path.isfile("aim.cmd")

    core_dir = os.path.abspath("joshua_os/.aim_core")
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    import config_utils

    win_os_root = tmp_path / "joshua_os"
    win_py = win_os_root / "venv" / "Scripts" / "python.exe"
    win_py.parent.mkdir(parents=True)
    win_py.write_text("", encoding="utf-8")

    with patch.object(config_utils.os, "name", "nt"):
        resolved = config_utils.resolve_venv_python(str(win_os_root))
        assert resolved == str(win_py)







