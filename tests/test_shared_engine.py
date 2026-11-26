import json
import os
import subprocess
import sys

import pytest

AIM_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AIM_CORE_DIR = os.path.join(AIM_ROOT, "joshua_os", ".aim_core")
if AIM_CORE_DIR not in sys.path:
    sys.path.insert(0, AIM_CORE_DIR)

import aim_engine
import register_mcp


def _fake_engine_source(tmp_path, version="v1.1.5"):
    src = tmp_path / "src" / "joshua_os"
    core = src / ".aim_core"
    (core / "plugins" / "datajack").mkdir(parents=True)
    (core / "mcp_lancedb.py").write_text("# fake mcp\n", encoding="utf-8")
    (core / "retriever.py").write_text("# fake retriever\n", encoding="utf-8")
    (core / "CONFIG.json").write_text('{"paths": {"project_root": "/host/specific"}}\n', encoding="utf-8")
    (core / "__pycache__").mkdir()
    (core / "__pycache__" / "junk.pyc").write_bytes(b"junk")
    (src / "requirements.txt").write_text("fastmcp\n", encoding="utf-8")
    (src / "VERSION").write_text(version + "\n", encoding="utf-8")
    return src


def _fake_installed_engine(tmp_path, version="v9.9.9"):
    root = tmp_path / "engine"
    os_dir = root / "joshua_os"
    (os_dir / ".aim_core").mkdir(parents=True)
    (os_dir / ".aim_core" / "mcp_lancedb.py").write_text("# engine mcp\n", encoding="utf-8")
    (os_dir / "VERSION").write_text(version + "\n", encoding="utf-8")
    if os.name == "nt":
        venv_py = os_dir / "venv" / "Scripts" / "python.exe"
    else:
        venv_py = os_dir / "venv" / "bin" / "python3"
    venv_py.parent.mkdir(parents=True)
    venv_py.write_text("#!/bin/sh\n", encoding="utf-8")
    venv_py.chmod(0o755)
    return root


def test_engine_root_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("AIM_ENGINE_ROOT", str(tmp_path / "custom-engine"))
    assert aim_engine.engine_root() == str(tmp_path / "custom-engine")


def test_install_engine_copies_code_records_version_and_excludes_host_config(tmp_path):
    src = _fake_engine_source(tmp_path)
    root = tmp_path / "engine"

    info = aim_engine.install_engine(str(src), root=str(root), build=False)

    assert info["version"] == "v1.1.5"
    assert info["root"] == str(root)
    dest_core = root / "joshua_os" / ".aim_core"
    assert (dest_core / "mcp_lancedb.py").is_file()
    assert (dest_core / "retriever.py").is_file()
    assert not (dest_core / "CONFIG.json").exists(), "host CONFIG.json must never leak into the shared engine"
    assert not (dest_core / "__pycache__").exists(), "__pycache__ must be excluded"
    assert aim_engine.installed_version(str(root)) == "v1.1.5"
    metadata = json.loads((root / "engine.json").read_text(encoding="utf-8"))
    assert metadata["version"] == "v1.1.5"
    assert metadata["source"] == str(src)


def test_install_engine_refuses_downgrade_without_force(tmp_path):
    root = tmp_path / "engine"
    newer = _fake_engine_source(tmp_path / "newer", version="v2.0.0")
    older = _fake_engine_source(tmp_path / "older", version="v1.0.0")

    aim_engine.install_engine(str(newer), root=str(root), build=False)
    with pytest.raises(RuntimeError, match="Refusing to downgrade"):
        aim_engine.install_engine(str(older), root=str(root), build=False)

    info = aim_engine.install_engine(str(older), root=str(root), build=False, force=True)
    assert info["version"] == "v1.0.0"


def test_install_engine_rejects_invalid_source(tmp_path):
    broken = tmp_path / "broken" / "joshua_os"
    (broken / ".aim_core").mkdir(parents=True)
    with pytest.raises(ValueError, match="missing .aim_core/mcp_lancedb.py"):
        aim_engine.install_engine(str(broken), root=str(tmp_path / "engine"), build=False)


def test_register_harnesses_uses_shared_engine_paths(tmp_path):
    root = _fake_installed_engine(tmp_path)
    home = tmp_path / "home"
    for rel in (".grok", ".codex", ".config/opencode", ".cursor"):
        (home / rel).mkdir(parents=True, exist_ok=True)

    touched = register_mcp.register_all_harnesses(
        engine_root=str(root),
        home_dir=str(home),
        harnesses=["agy", "grok", "codex", "opencode", "cursor"],
        detect_path_binaries=False,
    )

    expected_script = str(root / "joshua_os" / ".aim_core" / "mcp_lancedb.py")
    expected_python = aim_engine.venv_python_path(str(root))
    assert touched == ["agy", "grok", "codex", "opencode", "cursor"]

    agy = json.loads((home / ".gemini" / "config" / "mcp_config.json").read_text(encoding="utf-8"))
    assert agy["mcpServers"]["search_lancedb"] == {
        "command": expected_python,
        "args": [expected_script],
    }
    opencode = json.loads((home / ".config" / "opencode" / "opencode.json").read_text(encoding="utf-8"))
    assert opencode["mcp"]["search_lancedb"]["command"] == [expected_python, expected_script]
    codex = (home / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert json.dumps(expected_script) in codex
    grok = (home / ".grok" / "config.toml").read_text(encoding="utf-8")
    assert json.dumps(expected_script) in grok

    marker = json.loads((root / "registration.json").read_text(encoding="utf-8"))
    assert marker["version"] == "v9.9.9"
    assert marker["mcp_script"] == expected_script


def test_register_harnesses_engine_not_installed_raises(tmp_path):
    with pytest.raises(RuntimeError, match="not installed"):
        register_mcp.register_all_harnesses(
            engine_root=str(tmp_path / "missing-engine"),
            home_dir=str(tmp_path / "home"),
            harnesses=["agy"],
            detect_path_binaries=False,
        )


def test_cli_engine_status_reports_missing_engine(tmp_path):
    env = os.environ.copy()
    env["AIM_ENGINE_ROOT"] = str(tmp_path / "no-engine")
    result = subprocess.run(
        [sys.executable, os.path.join(AIM_CORE_DIR, "aim_cli.py"), "engine", "status"],
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
    )
    assert result.returncode == 0, result.stderr
    assert "SHARED MCP ENGINE" in result.stdout
    assert "NOT INSTALLED" in result.stdout
    assert "./aim engine sync" in result.stdout
