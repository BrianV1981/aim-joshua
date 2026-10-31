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
    assert 'for entry in "joshua_os/" "aim" "aim.ps1" "aim.cmd" "workspace/" "archive/"; do' in install_sh
    assert 'if [ "$CURRENT_DIR" = "$HOME" ]' in install_agent_sh
    assert 'PERSONA_NAME="${1:-}"' in install_agent_sh
    assert 'for entry in "joshua_os/" "aim" "aim.ps1" "aim.cmd" "workspace/" "archive/"; do' in install_agent_sh
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


def test_agent_memory_exemption_and_handoff_protocol_docs():
    with open("AGENTS.md", "r", encoding="utf-8") as f:
        agents_md = f.read()
    assert "Agent Memory Exemption (Direct-to-`main`)" in agents_md
    assert "git pull --rebase --autostash origin main" in agents_md
    assert "open an issue, branch out, update, and promote" not in agents_md

    with open("joshua_os/joshua_os_docs/PERSISTENT_WIKI.md", "r", encoding="utf-8") as f:
        wiki_doc = f.read()
    assert "Direct-to-`main` Auto-Push (GitOps Exemption)" in wiki_doc

    with open("joshua_os/joshua_os_docs/HANDOFF_PROTOCOL.md", "r", encoding="utf-8") as f:
        handoff_doc = f.read()
    assert "Idempotent Auto-Wiki Delta Check" in handoff_doc
    assert "git add memory-wiki/ HANDOFF.md" in handoff_doc

    with open("memory-wiki/pages/active-memory-protocol.md", "r", encoding="utf-8") as f:
        active_mem = f.read()
    assert "Direct-to-`main` Memory State Exemption" in active_mem
    assert "Under no circumstances should the wiki be updated directly on the `main` branch" not in active_mem

    with open("joshua_os/joshua_os_docs/COGNITIVE_ARCHITECTURE.md", "r", encoding="utf-8") as f:
        cog_arch = f.read()
    assert "Idempotent Auto-Wiki Delta Check" in cog_arch
    assert "REINCARNATION_GAMEPLAN.md" not in cog_arch

    with open("joshua_os/joshua_os_docs/GITOPS_DEPLOYMENT.md", "r", encoding="utf-8") as f:
        gitops_doc = f.read()
    assert "Agent Memory Exemption" in gitops_doc


def test_aim_init_never_truncates_agents_md_to_stub(tmp_path):
    import sys
    from unittest.mock import patch

    core_dir = os.path.abspath("joshua_os/.aim_core")
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    import aim_init

    # 1. Template parity check: default_AGENTS.md matches root AGENTS.md
    with open("AGENTS.md", "r", encoding="utf-8") as f:
        root_agents = f.read()
    with open("joshua_os/.aim_core/templates/default_AGENTS.md", "r", encoding="utf-8") as f:
        tpl_agents = f.read()
    assert root_agents == tpl_agents

    # 2. Restores full 10-section AGENTS.md when missing or truncated stub (<15 lines)
    stub_file = tmp_path / "AGENTS.md"
    stub_file.write_text("# 🤖 Sovereign Co-Agent: Test\n\nThis is a headless background node.\n", encoding="utf-8")
    status = aim_init.provision_agents_md(str(tmp_path), persona_name=None)
    assert status == "restored_default"
    restored = stub_file.read_text(encoding="utf-8")
    assert len(restored.splitlines()) >= 80
    assert "## 9. THE MEMORY WIKI (PERSISTENT KNOWLEDGE)" in restored
    assert "Agent Memory Exemption (Direct-to-`main`)" in restored
    assert "**Spoken Summary (`🔊`):**" in restored
    assert "terminal prompt border" in restored

    # 3. Unknown persona never overwrites a full AGENTS.md with a 7-line stub
    with patch.object(aim_init, "_resolve_persona_blueprint", return_value=None):
        status2 = aim_init.provision_agents_md(str(tmp_path), persona_name="nonexistent-persona")
        assert status2 == "preserved_existing"
        assert len(stub_file.read_text(encoding="utf-8").splitlines()) >= 80

    # 4. BOOTSTRAP.md and installers are aligned with v0.8.4 AGENTS.md
    with open("joshua_os/BOOTSTRAP.md", "r", encoding="utf-8") as f:
        bootstrap_md = f.read()
    assert "- **Operator Name:**" in bootstrap_md
    assert "Reincarnation Pipeline" not in bootstrap_md
    assert "NEVER overwrite the file with `write_file`" in bootstrap_md

    with open("joshua_os/install-clean.sh", "r", encoding="utf-8") as f:
        install_clean_sh = f.read()
    assert 'if [ "$CURRENT_DIR" = "$HOME" ]' in install_clean_sh
    assert 'exec bash "$SCRIPT_DIR/install.sh"' in install_clean_sh

    with open("README.md", "r", encoding="utf-8") as f:
        readme_md = f.read()
    assert "| **Option A (Default)** | `joshua_os/install.sh` |" in readme_md
    assert "Interactive Onboarding Interview (`./aim init`):" in readme_md

    # 5. Pre-baked default_lance contains v0.8.8 AGENTS.md and Direct-to-main rules
    import lance_backend
    lance_backend.LANCE_DB_PATH = os.path.abspath("joshua_os/assets/default_lance")
    vb = lance_backend.VectorBackend()
    assert vb.path == os.path.abspath("joshua_os/assets/default_lance")
    hits = vb.search(None, "Agent Memory Exemption", top_k=5)
    assert len(hits) > 0
    tts_hits = vb.search(None, "Spoken Summary", top_k=5)
    assert len(tts_hits) > 0


def test_aim_init_preserves_existing_gitignore(tmp_path, monkeypatch):
    import sys
    from unittest.mock import patch

    core_dir = os.path.abspath("joshua_os/.aim_core")
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    import aim_init

    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("__pycache__/\n~$*.docx\n", encoding="utf-8")

    monkeypatch.setattr(aim_init, "BASE_DIR", str(tmp_path))
    monkeypatch.setattr(aim_init, "OS_DIR", str(tmp_path / "joshua_os"))
    with patch.object(aim_init, "register_hooks"):
        aim_init.init_workspace(["aim_init.py", "--headless"])

    updated = gitignore.read_text(encoding="utf-8").splitlines()
    assert "__pycache__/" in updated
    assert "~$*.docx" in updated
    assert "joshua_os/" in updated
    assert "aim" in updated
    assert "workspace/" in updated
    assert "archive/" in updated


def test_no_hardcoded_host_paths_in_engine_code():
    import subprocess
    res = subprocess.run(
        ["git", "grep", "-n", "/home/kingb", "--", "joshua_os/", "aim", "aim.ps1", "aim.cmd"],
        capture_output=True,
        text=True,
    )
    assert res.stdout.strip() == "", f"Found hardcoded host paths in engine code:\n{res.stdout}"


def test_blackbox_multi_key_decrypt_and_history_db_indexing(tmp_path, monkeypatch):
    import json
    import sqlite3
    import sys
    from cryptography.fernet import Fernet

    core_dir = os.path.abspath("joshua_os/.aim_core")
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    import blackbox_vault

    vessel = tmp_path / "mock-project"
    (vessel / "joshua_os" / ".aim_core").mkdir(parents=True)
    key_file = tmp_path / "file_blackbox.key"
    file_key = Fernet.generate_key()
    key_file.write_bytes(file_key)

    cfg = {"settings": {"blackbox_key_path": str(key_file)}}
    (vessel / "joshua_os" / ".aim_core" / "CONFIG.json").write_text(json.dumps(cfg), encoding="utf-8")

    # Simulate sealing under file key (keyring unavailable during headless seal)
    monkeypatch.setattr(blackbox_vault, "keyring", None)
    sid = "session-110-alpha"
    raw_file = tmp_path / f"{sid}.jsonl"
    raw_payload = (
        json.dumps({"role": "user", "content": "Verify NotebookLM blackbox indexing for project"}) + "\n"
        + json.dumps({"role": "assistant", "content": "Blackbox indexed into history.db successfully."}) + "\n"
    )
    raw_file.write_text(raw_payload, encoding="utf-8")

    assert blackbox_vault.vault_session(str(raw_file), session_id=sid, vessel_root=str(vessel), reason="reincarnate")

    # Now simulate decrypting when OS keyring returns a DIFFERENT (older) key
    class _MockKeyring:
        @staticmethod
        def get_password(service, account):
            return Fernet.generate_key().decode("utf-8")

    monkeypatch.setattr(blackbox_vault, "keyring", _MockKeyring)
    decrypted = blackbox_vault.audit_vault(sid, vessel_root=str(vessel), to_stdout=False)
    assert decrypted is not None
    assert b"Verify NotebookLM blackbox indexing" in decrypted

    # Verify history.db and archive/history/*.md were automatically populated
    hist_db = vessel / "joshua_os" / "archive" / "history.db"
    assert hist_db.is_file()
    conn = sqlite3.connect(str(hist_db))
    rows = conn.execute("SELECT session_id, turn_count FROM history WHERE session_id = ?", (sid,)).fetchall()
    fts_rows = conn.execute("SELECT session_id FROM history_fts WHERE history_fts MATCH 'NotebookLM'").fetchall()
    conn.close()
    assert rows == [(sid, 2)]
    assert fts_rows == [(sid,)]


def test_sync_vault_to_history_and_cmd_sessions(tmp_path, monkeypatch, capsys):
    import argparse
    import json
    import sys
    from cryptography.fernet import Fernet

    core_dir = os.path.abspath("joshua_os/.aim_core")
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    import blackbox_vault
    import cli_memory

    vessel = tmp_path / "sync-project"
    os_dir = vessel / "joshua_os"
    (os_dir / ".aim_core").mkdir(parents=True)
    key_file = tmp_path / "sync_key.key"
    f_key = Fernet.generate_key()
    key_file.write_bytes(f_key)
    (os_dir / ".aim_core" / "CONFIG.json").write_text(
        json.dumps({"settings": {"blackbox_key_path": str(key_file)}}), encoding="utf-8"
    )

    # Create a pre-existing .enc file without history.db
    bb_dir = vessel / "archive" / ".raw_jsonl_blackbox"
    bb_dir.mkdir(parents=True)
    sid = "backfill-uuid-9999"
    raw_bytes = (
        json.dumps({"role": "user", "content": "Backfill historical vault test"}) + "\n"
        + json.dumps({"role": "assistant", "content": "Indexed via sync_vault_to_history."}) + "\n"
    ).encode("utf-8")
    (bb_dir / f"{sid}.enc").write_bytes(Fernet(f_key).encrypt(raw_bytes))

    monkeypatch.setattr(cli_memory, "BASE_DIR", str(vessel))
    monkeypatch.setattr(cli_memory, "OS_DIR", str(os_dir))

    cli_memory.cmd_sessions(argparse.Namespace())
    out = capsys.readouterr().out
    assert sid in out
    assert "PROJECT SESSIONS: sync-project" in out

    cli_memory.cmd_search_sessions(argparse.Namespace(query=["Backfill"]))
    search_out = capsys.readouterr().out
    assert sid in search_out


def test_semver_ga_posture():
    with open("VERSION", "r", encoding="utf-8") as f:
        version_str = f.read().strip()
    assert version_str.startswith("v")
    major, minor, patch = map(int, version_str[1:].split("."))
    assert major >= 1

    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()
    assert "Alpha, trenches-first." not in readme
    assert "Production-tested, trenches-first." in readme

    with open("CHANGELOG.md", "r", encoding="utf-8") as f:
        changelog = f.read()
    assert "## [v1.0.0]" in changelog


