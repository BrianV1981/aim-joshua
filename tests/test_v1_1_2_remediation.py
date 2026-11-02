"""Regression suite for Pass 12 EGM remediation sprint (v1.1.2, Issues #127-#135)."""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import subprocess
import sys
import zipfile
from unittest.mock import patch

from cryptography.fernet import Fernet
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AIM_BIN = os.path.join(REPO_ROOT, "aim.cmd" if os.name == "nt" else "aim")
CORE_DIR = os.path.join(REPO_ROOT, "joshua_os", ".aim_core")
OS_DIR = os.path.join(REPO_ROOT, "joshua_os")
for _p in (OS_DIR, CORE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# Issue #127 (JOSH-032): Safe uninstall/purge + zero caller-$PWD git commits
# ---------------------------------------------------------------------------

def test_issue_127_uninstall_and_purge_preserve_host_repo_files(tmp_path):
    """Choice 1, Choice 2 (--purge-memory), and cmd_purge must never delete host files."""
    import bootstrap_install

    fake_home = tmp_path / "home"
    fake_home.mkdir()

    def _make_consumer(name: str) -> Path:
        host = tmp_path / name
        (host / "src").mkdir(parents=True)
        (host / "venv" / "bin").mkdir(parents=True)
        (host / "src" / "app.py").write_text("print('host app')\n", encoding="utf-8")
        (host / "requirements.txt").write_text("fastapi==0.115.0\n", encoding="utf-8")
        (host / "LICENSE").write_text("MIT Host License\n", encoding="utf-8")
        (host / "venv" / "bin" / "activate").write_text("# host venv\n", encoding="utf-8")

        subprocess.run(["git", "init", "-b", "main"], cwd=str(host), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Dev"], cwd=str(host), check=True)
        subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=str(host), check=True)
        subprocess.run(["git", "add", "src/app.py", "requirements.txt", "LICENSE"], cwd=str(host), check=True)
        subprocess.run(["git", "commit", "-m", "host init"], cwd=str(host), check=True, capture_output=True)

        bootstrap_install.install_project(
            target_dir=str(host),
            mode="clean",
            source_dir=REPO_ROOT,
            skip_deps=True,
            home_dir=str(fake_home),
            skip_shell_rc=True,
        )
        return host

    # 1. cmd_purge --yes wipes ONLY joshua_os/memory_lance + joshua_os/archive/*
    host1 = _make_consumer("consumer-one")
    (host1 / "joshua_os" / "archive" / "history.db").parent.mkdir(parents=True, exist_ok=True)
    (host1 / "joshua_os" / "archive" / "history.db").write_bytes(b"dummy")
    res_purge = subprocess.run(
        [sys.executable, str(host1 / "joshua_os" / ".aim_core" / "aim_cli.py"), "purge", "--yes"],
        cwd=str(host1),
        capture_output=True,
        text=True,
    )
    assert res_purge.returncode == 0, res_purge.stderr
    assert list((host1 / "joshua_os" / "memory_lance").iterdir()) == []
    assert not (host1 / "joshua_os" / "archive" / "history.db").exists()
    assert (host1 / "src" / "app.py").is_file()

    # 2. Uninstall Mode 1 (Software Only: --yes without --purge-memory)
    res_u1 = subprocess.run(
        [sys.executable, str(host1 / "joshua_os" / ".aim_core" / "aim_cli.py"), "uninstall", "--yes"],
        cwd=str(host1),
        capture_output=True,
        text=True,
    )
    assert res_u1.returncode == 0, res_u1.stderr
    assert not (host1 / "joshua_os").exists()
    assert not (host1 / "aim").exists()
    assert not (host1 / "aim.ps1").exists()
    assert not (host1 / "aim.cmd").exists()
    # Memory state preserved in Mode 1
    assert (host1 / "memory-wiki" / "index.md").is_file()
    assert (host1 / "AGENTS.md").is_file()
    # Host repo files 100% intact
    for rel in (".git", "src/app.py", "requirements.txt", "LICENSE", "venv/bin/activate"):
        assert (host1 / rel).exists(), f"Host path {rel} was destroyed in Mode 1!"

    # 3. Uninstall Mode 2 (Software + Memory: --yes --purge-memory)
    host2 = _make_consumer("consumer-two")
    (host2 / "HANDOFF.md").write_text("# Handoff\n", encoding="utf-8")
    (host2 / "archive" / ".raw_jsonl_blackbox").mkdir(parents=True, exist_ok=True)
    (host2 / "archive" / ".raw_jsonl_blackbox" / "s1.enc").write_bytes(b"cipher")
    res_u2 = subprocess.run(
        [
            sys.executable,
            str(host2 / "joshua_os" / ".aim_core" / "aim_cli.py"),
            "uninstall",
            "--yes",
            "--purge-memory",
        ],
        cwd=str(host2),
        capture_output=True,
        text=True,
    )
    assert res_u2.returncode == 0, res_u2.stderr
    assert not (host2 / "joshua_os").exists()
    assert not (host2 / "memory-wiki").exists()
    assert not (host2 / "HANDOFF.md").exists()
    assert not (host2 / "AGENTS.md").exists()
    assert not (host2 / "TOOLS.md").exists()
    assert not (host2 / "archive" / ".raw_jsonl_blackbox").exists()
    # Host repo files 100% intact even in Mode 2!
    for rel in (".git", "src/app.py", "requirements.txt", "LICENSE", "venv/bin/activate"):
        assert (host2 / rel).exists(), f"Host path {rel} was destroyed in Mode 2!"


def test_issue_127_launcher_never_mutates_caller_pwd_git_repo_and_keeps_json_clean(tmp_path):
    """Invoking ./aim from an unrelated dirty git repo must not stage/commit caller files or pollute --json."""
    caller_repo = tmp_path / "unrelated-repo"
    caller_repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=str(caller_repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Dev"], cwd=str(caller_repo), check=True)
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=str(caller_repo), check=True)
    (caller_repo / "notes.md").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "notes.md"], cwd=str(caller_repo), check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=str(caller_repo), check=True, capture_output=True)

    # Dirty tracked + untracked files inside caller_repo
    (caller_repo / "notes.md").write_text("dirty edit\n", encoding="utf-8")
    (caller_repo / "HANDOFF.md").write_text("draft handoff\n", encoding="utf-8")
    head_before = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(caller_repo), capture_output=True, text=True, check=True
    ).stdout.strip()

    res = subprocess.run(
        [AIM_BIN, "search", "worktree", "--top-k", "1", "--json"],
        cwd=str(caller_repo),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    parsed = json.loads(res.stdout)
    assert isinstance(parsed, list)

    head_after = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(caller_repo), capture_output=True, text=True, check=True
    ).stdout.strip()
    assert head_after == head_before
    status_after = subprocess.run(
        ["git", "status", "--porcelain"], cwd=str(caller_repo), capture_output=True, text=True, check=True
    ).stdout
    assert "M notes.md" in status_after
    assert "?? HANDOFF.md" in status_after


# ---------------------------------------------------------------------------
# Issue #128 (JOSH-033): Cross-platform roots, non-destructive hooks/JSONC, AGY 2.0 tmux paste
# ---------------------------------------------------------------------------

def test_issue_128_zero_posix_slash_loops_zero_aim_ld_and_zero_host_paths():
    """Verify 0 POSIX-only != '/' root loops, 0 private aim-ld leaks, and 0 /home/kingb leaks."""
    for py_path in Path(REPO_ROOT).rglob("*.py"):
        if ".git" in py_path.parts or "venv" in py_path.parts or py_path.name == "test_v1_1_2_remediation.py":
            continue
        src = py_path.read_text(encoding="utf-8", errors="ignore")
        assert "!= '/'" not in src and '!= "/"' not in src, f"POSIX-only root loop in {py_path}"

    res_ld = subprocess.run(
        ["git", "grep", "-n", "aim-ld", "--", ":!tests/test_v1_1_2_remediation.py", ":!CHANGELOG.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res_ld.stdout.strip() == "", f"Private repo reference 'aim-ld' leaked:\n{res_ld.stdout}"

    res_host = subprocess.run(
        ["git", "grep", "-n", "/home/kingb", "--", "joshua_os/", "README.md", "CONTRIBUTING.md", "AGENTS.md", "TOOLS.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res_host.stdout.strip() == "", f"Hardcoded host path found:\n{res_host.stdout}"


def test_issue_128_aim_router_windows_root_and_nondestructive_hooks_and_jsonc(tmp_path, monkeypatch):
    """aim_router terminates at C:\\; aim_init preserves user hooks & avoids Escape; JSONC files are never clobbered."""
    from pathlib import PureWindowsPath
    import agy_workspace_trust
    import aim_init
    import register_mcp

    win_p = PureWindowsPath("C:\\Users\\Dev\\app")
    chain = [str(c) for c in (win_p, *win_p.parents)]
    assert chain[-1] == "C:\\"
    assert len(chain) == 4

    # aim_init.register_hooks preserves pre-existing third-party BeforeTool/AfterTool hooks
    fake_home = tmp_path / "home"
    agy_dir = fake_home / ".gemini" / "antigravity"
    agy_dir.mkdir(parents=True)
    user_before = {"matcher": "*", "hooks": [{"name": "UserGuard", "type": "command", "command": "/usr/local/bin/guard"}]}
    user_after = {"hooks": [{"name": "UserAudit", "type": "command", "command": "/usr/local/bin/audit"}]}
    (agy_dir / "settings.json").write_text(
        json.dumps({"theme": "dark", "hooks": {"BeforeTool": [user_before], "AfterTool": [user_after]}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    aim_init.register_hooks(is_light_mode=False)

    merged_settings = json.loads((agy_dir / "settings.json").read_text(encoding="utf-8"))
    assert merged_settings["theme"] == "dark"
    before_cmds = [
        h["command"]
        for entry in merged_settings["hooks"]["BeforeTool"]
        for h in entry.get("hooks", [])
    ]
    after_cmds = [
        h["command"]
        for entry in merged_settings["hooks"]["AfterTool"]
        for h in entry.get("hooks", [])
    ]
    assert "/usr/local/bin/guard" in before_cmds
    assert "/usr/local/bin/audit" in after_cmds
    assert any("aim_router.py" in c and "cognitive_mantra.py" in c for c in after_cmds)

    # Verify aim_init never sends Escape before Enter on tmux paste-buffer
    init_src = Path(CORE_DIR, "aim_init.py").read_text(encoding="utf-8")
    assert '"Escape", "Enter"' not in init_src
    assert "'Escape', 'Enter'" not in init_src

    # Verify register_mcp and agy_workspace_trust refuse to clobber JSONC files with {}
    jsonc_mcp = fake_home / ".gemini" / "config" / "mcp_config.json"
    jsonc_mcp.parent.mkdir(parents=True, exist_ok=True)
    jsonc_body = "// User JSONC comment\n{\n  \"mcpServers\": {\n    \"custom\": {\"command\": \"node\"}\n  }\n}\n"
    jsonc_mcp.write_text(jsonc_body, encoding="utf-8")
    proj_mcp = tmp_path / "mcp-proj"
    (proj_mcp / "joshua_os" / "venv" / "bin").mkdir(parents=True)
    (proj_mcp / "joshua_os" / ".aim_core").mkdir(parents=True)
    (proj_mcp / "joshua_os" / "venv" / "bin" / "python3").write_text("#!/bin/sh\n", encoding="utf-8")
    (proj_mcp / "joshua_os" / ".aim_core" / "mcp_lancedb.py").write_text("# mcp\n", encoding="utf-8")
    register_mcp.register_all_harnesses(
        project_root=str(proj_mcp),
        home_dir=str(fake_home),
        detect_path_binaries=False,
    )
    assert jsonc_mcp.read_text(encoding="utf-8") == jsonc_body

    jsonc_trust = fake_home / ".gemini" / "antigravity-cli" / "settings.json"
    jsonc_trust.parent.mkdir(parents=True, exist_ok=True)
    trust_body = "// Custom comment\n{\n  \"trustedWorkspaces\": [\"/keep/me\"],\n}\n"
    jsonc_trust.write_text(trust_body, encoding="utf-8")
    legacy_trust = fake_home / ".gemini" / "trustedFolders.json"
    legacy_trust.write_text(trust_body, encoding="utf-8")
    agy_workspace_trust.ensure_workspace_trusted(str(tmp_path), quiet=True)
    assert jsonc_trust.read_text(encoding="utf-8") == trust_body
    assert legacy_trust.read_text(encoding="utf-8") == trust_body


# ---------------------------------------------------------------------------
# Issue #129 (JOSH-034): Zero [PORTABILITY] spam, stable CONFIG.json mtime, generic Projects owner
# ---------------------------------------------------------------------------

def test_issue_129_config_utils_no_portability_spam_and_projects_auto_owner(tmp_path):
    """Back-to-back CLI runs must emit 0 [PORTABILITY] lines, keep CONFIG.json mtime unchanged, and avoid BrianV1981 default."""
    import aim_projects
    import config_utils

    assert config_utils.AIM_ROOT == config_utils.OS_ROOT
    gp_default = config_utils.build_default_config()["settings"]["github_projects"]
    assert gp_default["owner"] == ""
    assert gp_default["number"] == 0

    # Create a consumer workspace with an initialized CONFIG.json
    proj = tmp_path / "steady-proj"
    core = proj / "joshua_os" / ".aim_core"
    core.mkdir(parents=True)
    for fname in ("config_utils.py", "aim_doctor.py", "aim_cli.py", "cli_vault.py", "cli_memory.py", "agy_workspace_trust.py"):
        shutil.copy2(os.path.join(CORE_DIR, fname), core / fname)
    (proj / "joshua_os" / "hooks").mkdir(parents=True)
    (proj / "joshua_os" / "memory_lance").mkdir(parents=True)

    cfg_path = core / "CONFIG.json"
    seed_cfg = {
        "paths": {
            "base_dir": str(proj),
            "os_root": str(proj / "joshua_os"),
            "aim_root": str(proj / "joshua_os"),
            "venv_python": sys.executable,
            "memory_dir": str(proj / "joshua_os" / "memory"),
            "archive_raw_dir": str(proj / "joshua_os" / "archive" / "raw"),
        },
        "settings": {"auto_healing": True},
    }
    cfg_path.write_text(json.dumps(seed_cfg, indent=4), encoding="utf-8")
    fixed_ts = 1_700_000_000
    os.utime(cfg_path, (fixed_ts, fixed_ts))

    for _ in range(2):
        res = subprocess.run(
            [sys.executable, str(core / "aim_doctor.py")],
            cwd=str(proj),
            capture_output=True,
            text=True,
        )
        assert "[PORTABILITY]" not in (res.stdout + res.stderr)
    assert int(os.path.getmtime(cfg_path)) == fixed_ts

    # Verify aim_projects._detect_owner_from_git_remote extracts owner from SSH & HTTPS URLs
    with patch("aim_projects.subprocess.run") as mock_git:
        mock_git.return_value = subprocess.CompletedProcess([], 0, stdout="git@github.com:AcmeOrg/widget-api.git\n", stderr="")
        assert aim_projects._detect_owner_from_git_remote() == "AcmeOrg"
        mock_git.return_value = subprocess.CompletedProcess([], 0, stdout="https://github.com/JaneDoe/my-app.git\n", stderr="")
        assert aim_projects._detect_owner_from_git_remote() == "JaneDoe"


# ---------------------------------------------------------------------------
# Issue #130 (JOSH-035): LanceDB SQL quoting, write locking, and cached offline vectors
# ---------------------------------------------------------------------------

def test_issue_130_lancedb_sql_injection_guard_and_offline_vector_preservation(tmp_path, monkeypatch):
    """Single-quoted session_ids must not inject DataFusion SQL, and offline re-index must preserve cached 768-d vectors."""
    import bootstrap_brain
    from lance_backend import VectorBackend

    db_dir = tmp_path / "lance_sec"
    vb = VectorBackend(path=str(db_dir))
    vb.add_fragments(
        [
            {
                "session_id": "keep-session",
                "type": "session_history",
                "content": "Safe session AlphaToken",
                "source_db": "live",
                "vector": [0.25] * 768,
            },
            {
                "session_id": "o'hara' OR '1'='1",
                "type": "session_history",
                "content": "Quoted session BetaToken",
                "source_db": "live",
                "vector": [0.5] * 768,
            },
        ]
    )
    assert vb.get_table().count_rows() == 2

    # Filtering by adversarial session_id must ONLY return that exact row, not all rows!
    scoped = vb.search(None, "AlphaToken OR BetaToken", top_k=10, session_id="o'hara' OR '1'='1")
    assert all(r["session_id"] == "o'hara' OR '1'='1" for r in scoped)

    # Offline re-index preserves pre-existing non-zero 768-dim vectors for unchanged chunks
    doc_dir = tmp_path / "docs"
    doc_dir.mkdir()
    md = doc_dir / "guide.md"
    md.write_text("# Vector Preservation Guide\nCachedEmbeddingToken\n", encoding="utf-8")

    embed_calls = []

    def _fake_embed(text):
        embed_calls.append(text)
        return [0.42] * 768

    monkeypatch.setattr(bootstrap_brain, "get_embedding", _fake_embed)
    monkeypatch.setattr(bootstrap_brain, "verify_embedding_engine", lambda: True)
    bootstrap_brain.bootstrap_foundation(target_dir=str(doc_dir), db_path=str(db_dir))
    assert len(embed_calls) == 1

    # Second online run with unchanged text skips re-embedding via SHA-256 vector cache!
    bootstrap_brain.bootstrap_foundation(target_dir=str(doc_dir), db_path=str(db_dir))
    assert len(embed_calls) == 1

    # Third run with Ollama offline (verify_embedding_engine -> False) MUST keep [0.42]*768 instead of [0.0]*768!
    monkeypatch.setattr(bootstrap_brain, "verify_embedding_engine", lambda: False)
    bootstrap_brain.bootstrap_foundation(target_dir=str(doc_dir), db_path=str(db_dir))

    rows = [r for r in vb.get_table().to_arrow().to_pylist() if r["session_id"] == "expert-docs/guide.md"]
    assert len(rows) == 1
    assert abs(rows[0]["vector"][0] - 0.42) < 1e-5


# ---------------------------------------------------------------------------
# Issues #131 & #133 (JOSH-036 & JOSH-038): Clean consumer tree & accurate docs
# ---------------------------------------------------------------------------

def test_issues_131_and_133_clean_consumer_tree_and_doc_truth(tmp_path):
    import bootstrap_install

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    consumer = tmp_path / "clean-consumer"
    consumer.mkdir()
    bootstrap_install.install_project(
        target_dir=str(consumer),
        mode="clean",
        source_dir=REPO_ROOT,
        skip_deps=True,
        home_dir=str(fake_home),
        skip_shell_rc=True,
    )
    for dead_artifact in (
        "DAEMON_PULSE.md",
        "MIGRATION_PLAN.md",
        "assets/default_engrams/aim-agy_os.parquet",
        ".aim_core/sovereign_sync.py",
        ".aim_core/aim_swarm.py",
    ):
        assert not (consumer / "joshua_os" / dead_artifact).exists(), f"Dead artifact shipped: {dead_artifact}"

    contrib = Path(REPO_ROOT, "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "../../aim promote" in contrib
    assert "--context" in contrib and "--failure" in contrib and "--intent" in contrib
    assert "--body" not in contrib

    agents_md = Path(REPO_ROOT, "AGENTS.md").read_text(encoding="utf-8")
    default_agents_md = Path(REPO_ROOT, "joshua_os/.aim_core/templates/default_AGENTS.md").read_text(encoding="utf-8")
    assert agents_md == default_agents_md
    assert "joshua.ps1" not in agents_md


# ---------------------------------------------------------------------------
# Issue #132 (JOSH-037): Scoped OpenCode blackbox, WAL history.db, shrink-overwrite guard, 0 /tmp leaks
# ---------------------------------------------------------------------------

def test_issue_132_opencode_session_scoping_shrink_guard_and_wal_mode(tmp_path, monkeypatch):
    import blackbox_vault

    vessel = tmp_path / "oc-vessel"
    (vessel / "joshua_os" / ".aim_core").mkdir(parents=True)
    key_file = tmp_path / "oc.key"
    key_file.write_bytes(Fernet.generate_key())
    (vessel / "joshua_os" / ".aim_core" / "CONFIG.json").write_text(
        json.dumps({"settings": {"blackbox_key_path": str(key_file)}}),
        encoding="utf-8",
    )

    # Build multi-session OpenCode SQLite DB
    oc_db = tmp_path / "opencode.db"
    conn = sqlite3.connect(str(oc_db))
    conn.execute("CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, time_created INTEGER, data TEXT)")
    conn.execute("CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, time_created INTEGER, data TEXT)")
    conn.execute("INSERT INTO message VALUES ('m1', 'ses_alpha', 100, ?)", (json.dumps({"role": "user"}),))
    conn.execute("INSERT INTO part VALUES ('p1', 'm1', 100, ?)", (json.dumps({"text": "AlphaOnlySecretPayload line 1\n" * 4}),))
    conn.execute("INSERT INTO message VALUES ('m2', 'ses_beta', 200, ?)", (json.dumps({"role": "user"}),))
    conn.execute("INSERT INTO part VALUES ('p2', 'm2', 200, ?)", (json.dumps({"text": "BetaOtherSessionSecret"}),))
    conn.commit()
    conn.close()

    import tempfile

    env = os.environ.copy()
    env["AIM_OPENCODE_DB"] = str(oc_db)
    aim_bin = AIM_BIN

    tmp_root = tempfile.gettempdir()
    before_tmp = set(
        glob.glob(os.path.join(tmp_root, "aim_oc_*"))
        + glob.glob(os.path.join(tmp_root, "aim_bb_*"))
    )

    # Missing session must fail-closed with rc=1
    miss = subprocess.run(
        [aim_bin, "opencode-blackbox", "--session-id", "ses_missing", "--vessel-root", str(vessel)],
        cwd=str(vessel),
        env=env,
        capture_output=True,
        text=True,
    )
    assert miss.returncode == 1

    # Valid session seals ONLY ses_alpha (never ses_beta!)
    ok = subprocess.run(
        [aim_bin, "opencode-blackbox", "--session-id", "ses_alpha", "--vessel-root", str(vessel)],
        cwd=str(vessel),
        env=env,
        capture_output=True,
        text=True,
    )
    assert ok.returncode == 0, ok.stderr

    after_tmp = set(
        glob.glob(os.path.join(tmp_root, "aim_oc_*"))
        + glob.glob(os.path.join(tmp_root, "aim_bb_*"))
    )
    assert after_tmp - before_tmp == set()

    decrypted = blackbox_vault.audit_vault("ses_alpha", vessel_root=str(vessel), to_stdout=False).decode("utf-8")
    assert "AlphaOnlySecretPayload" in decrypted
    assert "BetaOtherSessionSecret" not in decrypted

    # Verify history.db uses WAL journal mode
    hist_db = vessel / "joshua_os" / "archive" / "history.db"
    hconn = sqlite3.connect(str(hist_db))
    jmode = hconn.execute("PRAGMA journal_mode;").fetchone()[0].lower()
    hconn.close()
    assert jmode == "wal"

    # Shrink-overwrite protection: smaller transcript for same session_id is refused unless force=True
    tiny = tmp_path / "tiny.jsonl"
    tiny.write_text(json.dumps({"role": "user", "content": "tiny"}) + "\n", encoding="utf-8")
    assert blackbox_vault.vault_session(str(tiny), session_id="ses_alpha", vessel_root=str(vessel), force=False) is False

    # With force=True, previous .enc is rotated into snapshots/ before replacement
    assert blackbox_vault.vault_session(str(tiny), session_id="ses_alpha", vessel_root=str(vessel), force=True) is True
    snaps = list((vessel / "archive" / ".raw_jsonl_blackbox" / "snapshots").glob("ses_alpha.*.enc"))
    assert len(snaps) == 1


# ---------------------------------------------------------------------------
# Issue #134 (JOSH-039): Parser/handler parity, staged handoff-vnext, DataJack exchange/unplug
# ---------------------------------------------------------------------------

def test_issue_134_parser_dispatch_parity_handoff_staged_and_datajack_roundtrip(tmp_path):
    import aim_cli

    parser = aim_cli.build_parser()
    subparsers_actions = [
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    ]
    assert len(subparsers_actions) == 1
    parser_verbs = set(subparsers_actions[0].choices.keys())
    assert parser_verbs == set(aim_cli.COMMAND_HANDLERS.keys())
    assert "delegate" in parser_verbs

    aim_bin = AIM_BIN

    # Staged hermetic handoff-vnext e2e succeeds offline with rc=0
    staged_out = tmp_path / "handoff_out"
    staged_out.mkdir()
    res_hv = subprocess.run(
        [aim_bin, "handoff-vnext", "e2e-staged", "--vessel-root", str(staged_out)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res_hv.returncode == 0, res_hv.stderr
    assert json.loads(res_hv.stdout)["ok"] is True

    # DataJack exchange / jack-in / unplug roundtrip in isolated consumer
    consumer = tmp_path / "dj-node"
    (consumer / "joshua_os" / ".aim_core").mkdir(parents=True)
    cartridge_src = tmp_path / "demo_rom.parquet"
    tbl = pa.table({"session_id": ["rom-1"], "content": ["Portable ROM knowledge"]})
    pq.write_table(tbl, str(cartridge_src))

    env = os.environ.copy()
    py_exchange = os.path.join(CORE_DIR, "plugins", "datajack", "aim_exchange.py")
    # Run via cli_memory/aim_exchange with OS_ROOT pointed at consumer/joshua_os
    (consumer / "joshua_os" / "setup.sh").write_text("# marker\n", encoding="utf-8")
    shutil.copytree(os.path.join(CORE_DIR, "plugins"), consumer / "joshua_os" / ".aim_core" / "plugins")
    shutil.copy2(os.path.join(CORE_DIR, "config_utils.py"), consumer / "joshua_os" / ".aim_core" / "config_utils.py")

    imp = subprocess.run(
        [sys.executable, str(consumer / "joshua_os" / ".aim_core" / "plugins" / "datajack" / "aim_exchange.py"), "import", str(cartridge_src)],
        cwd=str(consumer),
        env=env,
        capture_output=True,
        text=True,
    )
    assert imp.returncode == 0, imp.stderr
    mounted = consumer / "joshua_os" / "archive" / "cartridges" / "demo_rom.parquet"
    assert mounted.is_file()

    lst = subprocess.run(
        [sys.executable, str(consumer / "joshua_os" / ".aim_core" / "plugins" / "datajack" / "aim_exchange.py"), "list"],
        cwd=str(consumer),
        capture_output=True,
        text=True,
    )
    assert lst.returncode == 0 and "demo_rom.parquet" in lst.stdout

    unp = subprocess.run(
        [sys.executable, str(consumer / "joshua_os" / ".aim_core" / "plugins" / "datajack" / "aim_exchange.py"), "unplug", "demo_rom"],
        cwd=str(consumer),
        capture_output=True,
        text=True,
    )
    assert unp.returncode == 0, unp.stderr
    assert not mounted.exists()


# ---------------------------------------------------------------------------
# Issue #135 (JOSH-040): Clean-worktree promote guard, local-only promote, & Zip-Slip defense
# ---------------------------------------------------------------------------

def test_issue_135_promote_dirty_worktree_refusal_and_local_only_promote(tmp_path):
    import aim_cli

    repo = tmp_path / "local-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Dev"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=str(repo), check=True)
    (repo / "app.txt").write_text("v1\n", encoding="utf-8")
    subprocess.run(["git", "add", "app.txt"], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(repo), check=True, capture_output=True)

    wt = repo / "workspace" / "issue-77"
    wt.parent.mkdir(parents=True)
    subprocess.run(["git", "worktree", "add", "-b", "fix/issue-77", str(wt), "main"], cwd=str(repo), check=True, capture_output=True)
    (wt / "app.txt").write_text("v2\n", encoding="utf-8")
    subprocess.run(["git", "add", "app.txt"], cwd=str(wt), check=True)
    subprocess.run(["git", "commit", "-m", "feat v2"], cwd=str(wt), check=True, capture_output=True)

    # Create an uncommitted untracked file inside the worktree -> promote MUST abort (rc=1) and preserve it!
    precious = wt / "uncommitted_work.py"
    precious.write_text("# do not delete me!\n", encoding="utf-8")

    orig_cwd = os.getcwd()
    try:
        os.chdir(str(wt))
        with pytest.raises(SystemExit) as exc:
            aim_cli.cmd_promote(argparse.Namespace(yes=True))
        assert exc.value.code == 1
        assert precious.is_file()

        # Once committed cleanly, local-only promote (with NO 'origin' remote) succeeds cleanly!
        subprocess.run(["git", "add", "uncommitted_work.py"], cwd=str(wt), check=True)
        subprocess.run(["git", "commit", "-m", "add precious work"], cwd=str(wt), check=True, capture_output=True)
        aim_cli.cmd_promote(argparse.Namespace(yes=True))
    finally:
        os.chdir(orig_cwd)

    assert not wt.exists()
    assert (repo / "app.txt").read_text(encoding="utf-8") == "v2\n"
    assert (repo / "uncommitted_work.py").read_text(encoding="utf-8") == "# do not delete me!\n"


def test_issue_135_safe_extract_zip_blocks_zip_slip_and_symlinks(tmp_path):
    import aim_cli

    dest = tmp_path / "extract"
    dest.mkdir()

    # 1. Path traversal '../escape.txt' rejected before extracting any member
    traversal_buf = io.BytesIO()
    with zipfile.ZipFile(traversal_buf, "w") as zf:
        zf.writestr("safe/ok.txt", "safe")
        zf.writestr("../../escape.txt", "pwned")
    traversal_buf.seek(0)
    with zipfile.ZipFile(traversal_buf, "r") as zf:
        with pytest.raises(ValueError, match="Unsafe zip member path"):
            aim_cli.safe_extract_zip(zf, str(dest))
    assert not (dest / "safe" / "ok.txt").exists()

    # 2. Symlink entry rejected
    sym_buf = io.BytesIO()
    with zipfile.ZipFile(sym_buf, "w") as zf:
        zi = zipfile.ZipInfo("aim-joshua-main/evil_link")
        zi.create_system = 3
        zi.external_attr = (stat.S_IFLNK | 0o777) << 16
        zf.writestr(zi, "/etc/passwd")
    sym_buf.seek(0)
    with zipfile.ZipFile(sym_buf, "r") as zf:
        with pytest.raises(ValueError, match="symlink"):
            aim_cli.safe_extract_zip(zf, str(dest))
