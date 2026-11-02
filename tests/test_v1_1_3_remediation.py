"""Unmocked CLI subprocess regression suite for Pass 13 remediation sprint (v1.1.3, Issues #132, #134, #135)."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from unittest.mock import patch


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CORE_DIR = os.path.join(REPO_ROOT, "joshua_os", ".aim_core")
AIM_BIN = os.path.join(REPO_ROOT, "aim.cmd" if os.name == "nt" else "aim")

if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)


def _consumer_launcher(proj: Path) -> str:
    return str(proj / ("aim.cmd" if os.name == "nt" else "aim"))


def _hermetic_env(fake_home: Path) -> dict[str, str]:
    env = os.environ.copy()
    py_dir = os.path.dirname(os.path.abspath(sys.executable))
    env["PATH"] = py_dir + os.pathsep + env.get("PATH", "")
    env["HOME"] = str(fake_home)
    env["USERPROFILE"] = str(fake_home)
    env["XDG_CONFIG_HOME"] = str(fake_home / ".config")
    env["XDG_DATA_HOME"] = str(fake_home / ".local" / "share")
    return env


# ---------------------------------------------------------------------------
# Issue #134 (JOSH-039): Unmocked ./aim health, ./aim clean, ./aim audit, ./aim recall, & aim_config
# ---------------------------------------------------------------------------

def test_issue_134_unmocked_aim_health_and_clean_subprocesses(tmp_path):
    """Real unmocked ./aim health, ./aim clean, and ./aim clean --immediate must exit rc=0."""
    import bootstrap_install

    # 1. If REPO_ROOT already has an initialized memory_lance, live ./aim health must exit rc=0
    if os.path.isdir(os.path.join(REPO_ROOT, "joshua_os", "memory_lance")):
        live_health = subprocess.run(
            [AIM_BIN, "health"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert live_health.returncode == 0, live_health.stdout + live_health.stderr
        assert "LanceDB Engine" in live_health.stdout
        assert "PASS" in live_health.stdout

    # 2. Isolated hermetic consumer workspace health + clean + clean --immediate
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    consumer = tmp_path / "clean-health-app"
    consumer.mkdir()
    bootstrap_install.install_project(
        target_dir=str(consumer),
        mode="clean",
        source_dir=REPO_ROOT,
        skip_deps=True,
        home_dir=str(fake_home),
        skip_shell_rc=True,
    )
    env = _hermetic_env(fake_home)
    launcher = _consumer_launcher(consumer)

    res_health = subprocess.run(
        [launcher, "health"],
        cwd=str(consumer),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_health.returncode == 0, res_health.stdout + res_health.stderr
    assert "LanceDB Engine" in res_health.stdout and "PASS" in res_health.stdout

    res_clean = subprocess.run(
        [launcher, "clean"],
        cwd=str(consumer),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_clean.returncode == 0, res_clean.stdout + res_clean.stderr
    assert "[SUCCESS] LanceDB version history compacted." in res_clean.stdout

    res_clean_imm = subprocess.run(
        [launcher, "clean", "--immediate"],
        cwd=str(consumer),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_clean_imm.returncode == 0, res_clean_imm.stdout + res_clean_imm.stderr
    assert "[SUCCESS] LanceDB version history compacted." in res_clean_imm.stdout


def test_issue_134_unmocked_aim_audit_and_recall_db_errors_exit_nonzero(tmp_path):
    """./aim audit and ./aim recall must exit rc=1 on missing or corrupt history.db; aim_config uses _clear_screen."""
    import bootstrap_install

    cfg_src = Path(CORE_DIR, "aim_config.py").read_text(encoding="utf-8")
    assert "os.system('clear')" not in cfg_src
    assert 'os.system("clear")' not in cfg_src

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    consumer = tmp_path / "audit-recall-app"
    consumer.mkdir()
    bootstrap_install.install_project(
        target_dir=str(consumer),
        mode="clean",
        source_dir=REPO_ROOT,
        skip_deps=True,
        home_dir=str(fake_home),
        skip_shell_rc=True,
    )
    env = _hermetic_env(fake_home)
    launcher = _consumer_launcher(consumer)
    hist_db = consumer / "joshua_os" / "archive" / "history.db"
    assert not hist_db.exists()

    # 1. Missing history.db -> rc=1 for both audit and recall
    miss_audit = subprocess.run(
        [launcher, "audit"],
        cwd=str(consumer),
        env=env,
        capture_output=True,
        text=True,
    )
    assert miss_audit.returncode == 1
    assert "Database not found" in miss_audit.stderr

    miss_recall = subprocess.run(
        [launcher, "recall", "worktree"],
        cwd=str(consumer),
        env=env,
        capture_output=True,
        text=True,
    )
    assert miss_recall.returncode == 1
    assert "Database not found" in miss_recall.stderr

    # 2. Corrupt history.db -> rc=1 for both audit and recall
    hist_db.parent.mkdir(parents=True, exist_ok=True)
    hist_db.write_bytes(b"CORRUPT_NON_SQLITE_BYTES_0000")

    bad_audit = subprocess.run(
        [launcher, "audit"],
        cwd=str(consumer),
        env=env,
        capture_output=True,
        text=True,
    )
    assert bad_audit.returncode == 1
    assert "Error reading database" in bad_audit.stderr

    bad_recall = subprocess.run(
        [launcher, "recall", "worktree"],
        cwd=str(consumer),
        env=env,
        capture_output=True,
        text=True,
    )
    assert bad_recall.returncode == 1
    assert "Error reading database" in bad_recall.stderr


# ---------------------------------------------------------------------------
# Issue #132 (JOSH-037): Unmocked --vessel-root across *-blackbox from separate cwd
# ---------------------------------------------------------------------------

def test_issue_132_unmocked_blackbox_vessel_root_cross_directory_isolation(tmp_path):
    """Running opencode-blackbox and agy-blackbox with --vessel-root <target> from <unrelated_cwd> seals strictly into <target>."""
    import bootstrap_install

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    target_vessel = tmp_path / "target-vessel"
    target_vessel.mkdir()
    unrelated_cwd = tmp_path / "unrelated-caller-cwd"
    unrelated_cwd.mkdir()

    bootstrap_install.install_project(
        target_dir=str(target_vessel),
        mode="clean",
        source_dir=REPO_ROOT,
        skip_deps=True,
        home_dir=str(fake_home),
        skip_shell_rc=True,
    )

    # Seed <target_vessel>/opencode_data/opencode.db (and NO opencode.db in unrelated_cwd!)
    oc_dir = target_vessel / "opencode_data"
    oc_dir.mkdir(parents=True, exist_ok=True)
    oc_db = oc_dir / "opencode.db"
    conn = sqlite3.connect(str(oc_db))
    conn.execute("CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, data TEXT, time_created INTEGER)")
    conn.execute("CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, data TEXT, time_created INTEGER)")
    conn.execute(
        "INSERT INTO message VALUES (?, ?, ?, ?)",
        ("m1", "ses_vessel_target", json.dumps({"role": "user"}), 100),
    )
    conn.execute(
        "INSERT INTO part VALUES (?, ?, ?, ?)",
        ("p1", "m1", json.dumps({"text": "TargetVesselExclusivePayload"}), 101),
    )
    conn.commit()
    conn.close()

    env = _hermetic_env(fake_home)
    env.pop("AIM_OPENCODE_DB", None)
    launcher = _consumer_launcher(target_vessel)

    # Execute opencode-blackbox from cwd=unrelated_cwd pointing --vessel-root at target_vessel
    res_oc = subprocess.run(
        [launcher, "opencode-blackbox", "--session-id", "ses_vessel_target", "--vessel-root", str(target_vessel)],
        cwd=str(unrelated_cwd),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_oc.returncode == 0, res_oc.stdout + res_oc.stderr

    target_enc = target_vessel / "archive" / ".raw_jsonl_blackbox" / "ses_vessel_target.enc"
    target_hist = target_vessel / "joshua_os" / "archive" / "history.db"
    assert target_enc.is_file()
    assert target_hist.is_file()
    assert not (unrelated_cwd / "archive").exists()
    assert not (unrelated_cwd / "joshua_os").exists()

    hconn = sqlite3.connect(str(target_hist))
    sids = {r[0] for r in hconn.execute("SELECT session_id FROM history").fetchall()}
    hconn.close()
    assert "ses_vessel_target" in sids

    # Also verify agy-blackbox --vessel-root from unrelated_cwd
    agy_sid = "11111111-2222-3333-4444-555555555555"
    agy_log = fake_home / ".gemini" / "antigravity" / "brain" / agy_sid / ".system_generated" / "logs" / "transcript.jsonl"
    agy_log.parent.mkdir(parents=True, exist_ok=True)
    agy_log.write_text(
        json.dumps({"type": "USER_INPUT", "content": "AGYVesselRootCheck"}) + "\n",
        encoding="utf-8",
    )

    res_agy = subprocess.run(
        [launcher, "agy-blackbox", "--session-id", agy_sid, "--vessel-root", str(target_vessel)],
        cwd=str(unrelated_cwd),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_agy.returncode == 0, res_agy.stdout + res_agy.stderr
    assert (target_vessel / "archive" / ".raw_jsonl_blackbox" / f"{agy_sid}.enc").is_file()
    assert not (unrelated_cwd / "archive").exists()

    # Verify vault audit --vessel decrypts cleanly from unrelated_cwd
    res_dec = subprocess.run(
        [launcher, "vault", "audit", "ses_vessel_target", "--vessel", str(target_vessel)],
        cwd=str(unrelated_cwd),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_dec.returncode == 0, res_dec.stderr
    assert "TargetVesselExclusivePayload" in res_dec.stdout


# ---------------------------------------------------------------------------
# Issue #135 (JOSH-040): Unmocked Day-0 empty dir, existing repo, unborn HEAD, & 0-byte stubs
# ---------------------------------------------------------------------------

def test_issue_135_unmocked_day0_empty_dir_existing_repo_and_unborn_head_e2e(tmp_path, monkeypatch):
    """Full unmocked E2E for Day-0 fresh folder, existing committed repo with untracked scaffold, and manual 0-commit git init."""
    import aim_init

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    env = _hermetic_env(fake_home)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    bootstrap_script = os.path.join(CORE_DIR, "bootstrap_install.py")

    # (a) Brand-new empty directory (even without global ~/.gitconfig identity!)
    day0 = tmp_path / "day0-empty-app"
    day0.mkdir()
    res_inst_a = subprocess.run(
        [
            sys.executable,
            bootstrap_script,
            "--mode",
            "clean",
            "--target",
            str(day0),
            "--source",
            REPO_ROOT,
            "--skip-deps",
            "--home",
            str(fake_home),
            "--skip-shell-rc",
        ],
        cwd=str(day0),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_inst_a.returncode == 0, res_inst_a.stdout + res_inst_a.stderr

    head_verify = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=str(day0),
        env=env,
        capture_output=True,
        text=True,
    )
    assert head_verify.returncode == 0, "bootstrap_install.py must create an initial commit on newborn main"

    day0_aim = _consumer_launcher(day0)
    res_fix_a = subprocess.run(
        [day0_aim, "fix", "1"],
        cwd=str(day0),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_fix_a.returncode == 0, res_fix_a.stdout + res_fix_a.stderr
    assert "orphan" not in (res_fix_a.stdout + res_fix_a.stderr).lower()

    wt_a = day0 / "workspace" / "issue-1"
    assert (wt_a / "AGENTS.md").is_file()
    (wt_a / "feature_a.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "feature_a.py"], cwd=str(wt_a), env=env, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Dev", "-c", "user.email=dev@example.com", "commit", "-m", "feat: add feature_a"],
        cwd=str(wt_a),
        env=env,
        check=True,
        capture_output=True,
    )

    res_prom_a = subprocess.run(
        [day0_aim, "promote", "--yes"],
        cwd=str(wt_a),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_prom_a.returncode == 0, res_prom_a.stdout + res_prom_a.stderr
    assert (day0 / "feature_a.py").is_file()

    # Uninstall Mode 1 must also prune empty workspace/ directory left after promote
    res_uninst_a = subprocess.run(
        [day0_aim, "uninstall", "--yes"],
        cwd=str(day0),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_uninst_a.returncode == 0, res_uninst_a.stdout + res_uninst_a.stderr
    assert not (day0 / "workspace").exists()
    assert (day0 / "feature_a.py").is_file()

    # (b) Existing committed Git repo with untracked scaffold files left in repo_root
    existing = tmp_path / "existing-host-repo"
    existing.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=str(existing), env=env, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Dev"], cwd=str(existing), env=env, check=True)
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=str(existing), env=env, check=True)
    (existing / "app.py").write_text("v = 1\n", encoding="utf-8")
    (existing / "README.md").write_text("# Host App\n", encoding="utf-8")
    subprocess.run(["git", "add", "app.py", "README.md"], cwd=str(existing), env=env, check=True)
    subprocess.run(["git", "commit", "-m", "initial host commit"], cwd=str(existing), env=env, check=True, capture_output=True)

    res_inst_b = subprocess.run(
        [
            sys.executable,
            bootstrap_script,
            "--mode",
            "clean",
            "--target",
            str(existing),
            "--source",
            REPO_ROOT,
            "--skip-deps",
            "--home",
            str(fake_home),
            "--skip-shell-rc",
        ],
        cwd=str(existing),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_inst_b.returncode == 0, res_inst_b.stdout + res_inst_b.stderr
    # Confirm untracked scaffold files exist in existing root before fix/promote
    porcelain_b = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(existing),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "?? .gitignore" in porcelain_b and "?? AGENTS.md" in porcelain_b

    existing_aim = _consumer_launcher(existing)
    res_fix_b = subprocess.run(
        [existing_aim, "fix", "2"],
        cwd=str(existing),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_fix_b.returncode == 0, res_fix_b.stdout + res_fix_b.stderr
    wt_b = existing / "workspace" / "issue-2"
    (wt_b / "app.py").write_text("v = 2\n", encoding="utf-8")
    subprocess.run(["git", "add", "app.py"], cwd=str(wt_b), env=env, check=True)
    subprocess.run(["git", "commit", "-m", "bump v=2"], cwd=str(wt_b), env=env, check=True, capture_output=True)

    # Verify Safety Gate 2 STILL blocks when a TRACKED root file is modified!
    (existing / "README.md").write_text("# Dirty Tracked Root Edit\n", encoding="utf-8")
    res_prom_dirty_root = subprocess.run(
        [existing_aim, "promote", "--yes"],
        cwd=str(wt_b),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_prom_dirty_root.returncode == 1
    assert "Root repository" in res_prom_dirty_root.stderr

    # Restore tracked root file (leaving ?? .gitignore, ?? AGENTS.md, ?? memory-wiki/ untracked) -> promote succeeds!
    subprocess.run(["git", "checkout", "--", "README.md"], cwd=str(existing), env=env, check=True)
    res_prom_b = subprocess.run(
        [existing_aim, "promote", "--yes"],
        cwd=str(wt_b),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_prom_b.returncode == 0, res_prom_b.stdout + res_prom_b.stderr
    assert (existing / "app.py").read_text(encoding="utf-8") == "v = 2\n"

    # (c) Manual 0-commit git init -> ./aim fix 1 must fail cleanly with rc=1 and never create an orphan worktree
    unborn = tmp_path / "manual-unborn-repo"
    unborn.mkdir()
    res_inst_c = subprocess.run(
        [
            sys.executable,
            bootstrap_script,
            "--mode",
            "clean",
            "--target",
            str(unborn),
            "--source",
            REPO_ROOT,
            "--skip-deps",
            "--home",
            str(fake_home),
            "--skip-shell-rc",
        ],
        cwd=str(unborn),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_inst_c.returncode == 0
    # Simulate a user manually wiping .git and running bare git init -b main with 0 commits
    import shutil

    shutil.rmtree(unborn / ".git")
    subprocess.run(["git", "init", "-b", "main"], cwd=str(unborn), env=env, check=True, capture_output=True)

    unborn_aim = _consumer_launcher(unborn)
    res_fix_c = subprocess.run(
        [unborn_aim, "fix", "1"],
        cwd=str(unborn),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_fix_c.returncode == 1
    assert "unborn HEAD" in res_fix_c.stderr
    assert not (unborn / "workspace" / "issue-1").exists()

    # (d) aim_init.init_workspace no longer drops 0-byte CHANGELOG.md / CONTRIBUTING.md / VERSION stubs
    init_dir = tmp_path / "init-no-stubs"
    init_dir.mkdir()
    monkeypatch.setattr(aim_init, "BASE_DIR", str(init_dir))
    monkeypatch.setattr(aim_init, "OS_DIR", str(init_dir / "joshua_os"))
    with patch.object(aim_init, "register_hooks"):
        aim_init.init_workspace(["aim_init.py", "--headless"])
    for stub in ("CHANGELOG.md", "CONTRIBUTING.md", "VERSION"):
        assert not (init_dir / stub).exists()
    assert (init_dir / "README.md").read_text(encoding="utf-8").startswith("# init-no-stubs")
