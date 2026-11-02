import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure .aim_core is in path so we can import mcp_lancedb
AIM_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AIM_CORE_DIR = os.path.join(AIM_ROOT, "joshua_os", ".aim_core")
if AIM_CORE_DIR not in sys.path:
    sys.path.insert(0, AIM_CORE_DIR)

from mcp_lancedb import search_lancedb

@patch("mcp_lancedb.os.getcwd")
@patch("retriever.perform_search")
def test_search_lancedb_no_results(mock_perform_search, mock_getcwd):
    mock_getcwd.return_value = "/fake/workspace"
    mock_perform_search.return_value = []
    
    result = search_lancedb("test query")
    
    assert "No fragments found" in result
    assert mock_perform_search.call_count == 1
    assert mock_perform_search.call_args[0] == ("test query",)
    assert mock_perform_search.call_args[1]["top_k"] == 10
    assert isinstance(mock_perform_search.call_args[1].get("db_path"), str)

@patch("mcp_lancedb.os.getcwd")
@patch("retriever.perform_search")
def test_search_lancedb_with_results(mock_perform_search, mock_getcwd):
    mock_getcwd.return_value = "/fake/workspace"
    mock_perform_search.return_value = [
        {"filename": "test.md", "content": "This is a test fragment.", "score": 0.95}
    ]
    
    result = search_lancedb("test query")
    
    assert "--- LanceDB Search Results for: 'test query' ---" in result
    assert "Source: test.md" in result
    assert "This is a test fragment." in result

@patch("mcp_lancedb.os.getcwd")
@patch("retriever.perform_search")
def test_search_lancedb_with_context(mock_perform_search, mock_getcwd):
    import lance_backend
    orig_lance_path = lance_backend.LANCE_DB_PATH

    # Mock context
    ctx = MagicMock()
    ctx.request_context.session.client_params.model_extra = {
        "workspaceFolders": [{"uri": "file:///my/custom/workspace"}]
    }
    mock_perform_search.return_value = []
    
    search_lancedb("test query", ctx=ctx)
    
    # Explicit db_path passed without mutating global lance_backend.LANCE_DB_PATH (Issue #130)
    expected_db = os.path.join("/my/custom/workspace", "joshua_os", "memory_lance")
    mock_perform_search.assert_called_once_with("test query", top_k=10, db_path=expected_db)
    assert lance_backend.LANCE_DB_PATH == orig_lance_path


@patch("retriever.perform_search")
def test_search_lancedb_strict_local_isolation_over_subfolders(mock_perform_search, tmp_path):
    """When workspace has its own joshua_os/memory_lance, subfolders must NOT be queried."""
    local_db = tmp_path / "joshua_os" / "memory_lance"
    local_db.mkdir(parents=True)
    sub_db = tmp_path / "subproject" / "joshua_os" / "memory_lance"
    sub_db.mkdir(parents=True)

    mock_perform_search.return_value = [{"filename": "local.md", "content": "Local hit", "score": 0.99}]

    with patch("mcp_lancedb.os.getcwd", return_value=str(tmp_path)):
        out = search_lancedb("isolation test", top_k=5)

    assert mock_perform_search.call_count == 1
    assert "Source: local.md" in out
    assert "[subproject]" not in out


@patch("retriever.perform_search")
def test_search_lancedb_umbrella_subfolder_fallback(mock_perform_search, tmp_path):
    """When workspace is a parent folder with no root DB, immediate */joshua_os/memory_lance DBs are queried and ranked."""
    (tmp_path / "agent-a" / "joshua_os" / "memory_lance").mkdir(parents=True)
    (tmp_path / "agent-b" / "joshua_os" / "memory_lance").mkdir(parents=True)

    def side_effect(query, top_k=10, db_path=None):
        if "agent-a" in (db_path or ""):
            return [{"filename": "a_doc.md", "content": "From A", "score": 0.75}]
        return [{"filename": "b_doc.md", "content": "From B", "score": 0.92}]

    mock_perform_search.side_effect = side_effect

    with patch("mcp_lancedb.os.getcwd", return_value=str(tmp_path)):
        out = search_lancedb("umbrella query", top_k=5)

    assert mock_perform_search.call_count == 2
    assert "[1] Score: 0.9200 | Source: [agent-b] b_doc.md" in out
    assert "[2] Score: 0.7500 | Source: [agent-a] a_doc.md" in out


def test_retriever_active_aim_root_follows_lance_db_path(tmp_path):
    """Issue #99: retriever.get_active_aim_root() must dynamically resolve from lance_backend.LANCE_DB_PATH."""
    import lance_backend
    import retriever

    orig_path = getattr(lance_backend, "LANCE_DB_PATH", None)
    custom_os_root = tmp_path / "sub-agent" / "joshua_os"
    custom_db = custom_os_root / "memory_lance"
    custom_db.mkdir(parents=True)

    try:
        lance_backend.LANCE_DB_PATH = str(custom_db)
        assert retriever.get_active_aim_root() == str(custom_os_root)
    finally:
        if orig_path is not None:
            lance_backend.LANCE_DB_PATH = orig_path


def test_list_lance_tables_zero_deprecation_warnings(tmp_path):
    """Issue #114: VectorBackend.ensure_table() and list_lance_tables() emit zero table_names() DeprecationWarnings."""
    import warnings
    import lance_backend

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        vb = lance_backend.VectorBackend(path=str(tmp_path / "lance_test"))
        vb.ensure_table()
        tables = lance_backend.list_lance_tables(vb.db)

    dep_msgs = [str(w.message) for w in caught if issubclass(w.category, DeprecationWarning) and "table_names" in str(w.message)]
    assert dep_msgs == []
    assert "fragments" in tables

    class LegacyConn:
        def table_names(self):
            return ["legacy_tbl"]

    assert lance_backend.list_lance_tables(LegacyConn()) == ["legacy_tbl"]


def test_uri_to_local_path_windows_and_posix_spaces():
    from mcp_lancedb import _uri_to_local_path

    assert _uri_to_local_path("file:///home/dev/My%20Project") == "/home/dev/My Project"
    assert _uri_to_local_path("file:///C:/Users/Dev%20User/my-app") == "C:/Users/Dev User/my-app"
    assert _uri_to_local_path("file:///c%3A/Users/Brian/aim-project") == "c:/Users/Brian/aim-project"
    assert _uri_to_local_path("/plain/local/path") == "/plain/local/path"


def test_register_mcp_multi_harness_detection_and_self_healing(tmp_path):
    import json
    import register_mcp

    fake_home = tmp_path / "home"
    (fake_home / ".gemini").mkdir(parents=True)
    (fake_home / ".grok").mkdir(parents=True)
    (fake_home / ".codex").mkdir(parents=True)
    (fake_home / ".codex" / "config.toml").write_text('[projects."/demo"]\ntrust_level = "trusted"\n', encoding="utf-8")
    (fake_home / ".config" / "opencode").mkdir(parents=True)
    (fake_home / ".config" / "opencode" / "opencode.json").write_text(
        json.dumps({"$schema": "https://opencode.ai/config.json", "snapshot": False}),
        encoding="utf-8",
    )
    (fake_home / ".cursor").mkdir(parents=True)

    proj_a = tmp_path / "proj-a"
    py_a = proj_a / "joshua_os" / "venv" / "bin" / "python3"
    mcp_a = proj_a / "joshua_os" / ".aim_core" / "mcp_lancedb.py"
    py_a.parent.mkdir(parents=True)
    mcp_a.parent.mkdir(parents=True)
    py_a.write_text("#!/bin/sh\n", encoding="utf-8")
    mcp_a.write_text("# mcp\n", encoding="utf-8")

    updated = register_mcp.register_all_harnesses(
        project_root=str(proj_a),
        home_dir=str(fake_home),
        detect_path_binaries=False,
    )
    assert set(updated) == {"agy", "grok", "codex", "opencode", "cursor"}
    assert not (fake_home / ".claude.json").exists()

    agy_cfg = json.loads((fake_home / ".gemini" / "config" / "mcp_config.json").read_text(encoding="utf-8"))
    assert agy_cfg["mcpServers"]["search_lancedb"] == {"command": str(py_a), "args": [str(mcp_a)]}

    opencode_cfg = json.loads((fake_home / ".config" / "opencode" / "opencode.json").read_text(encoding="utf-8"))
    assert opencode_cfg["snapshot"] is False
    assert opencode_cfg["mcp"]["search_lancedb"] == {
        "type": "local",
        "command": [str(py_a), str(mcp_a)],
        "enabled": True,
    }

    codex_toml = (fake_home / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert '[projects."/demo"]' in codex_toml
    assert "[mcp_servers.search_lancedb]" in codex_toml
    assert str(py_a).replace("\\", "\\\\") in codex_toml

    grok_toml = (fake_home / ".grok" / "config.toml").read_text(encoding="utf-8")
    assert "[mcp_servers.search_lancedb]" in grok_toml
    assert "enabled = true" in grok_toml

    # Second project preserves healthy proj_a entry unless proj_a is removed or force=True
    proj_b = tmp_path / "proj-b"
    py_b = proj_b / "joshua_os" / "venv" / "bin" / "python3"
    mcp_b = proj_b / "joshua_os" / ".aim_core" / "mcp_lancedb.py"
    py_b.parent.mkdir(parents=True)
    mcp_b.parent.mkdir(parents=True)
    py_b.write_text("#!/bin/sh\n", encoding="utf-8")
    mcp_b.write_text("# mcp\n", encoding="utf-8")

    register_mcp.register_all_harnesses(project_root=str(proj_b), home_dir=str(fake_home), detect_path_binaries=False)
    agy_cfg_keep = json.loads((fake_home / ".gemini" / "config" / "mcp_config.json").read_text(encoding="utf-8"))
    assert agy_cfg_keep["mcpServers"]["search_lancedb"]["command"] == str(py_a)

    # Simulate deleting proj_a -> self-heals to proj_b automatically
    py_a.unlink()
    register_mcp.register_all_harnesses(project_root=str(proj_b), home_dir=str(fake_home), detect_path_binaries=False)
    agy_cfg_healed = json.loads((fake_home / ".gemini" / "config" / "mcp_config.json").read_text(encoding="utf-8"))
    assert agy_cfg_healed["mcpServers"]["search_lancedb"]["command"] == str(py_b)


@patch("retriever.perform_search")
def test_search_lancedb_desktop_fallback_to_os_root_when_no_workspace_folders(mock_perform_search, tmp_path):
    """Issue #118 (JOSH-W02): Antigravity 2.0 Desktop omits workspaceFolders and sets cwd to app binary dir or $HOME."""
    import mcp_lancedb
    import lance_backend

    app_bin_dir = tmp_path / "AppData" / "Local" / "Programs" / "Antigravity"
    app_bin_dir.mkdir(parents=True)

    fake_os_root = tmp_path / "registered-project" / "joshua_os"
    installed_db = fake_os_root / "memory_lance"
    installed_db.mkdir(parents=True)

    ctx = MagicMock()
    ctx.request_context.session.client_params.model_extra = {}
    mock_perform_search.return_value = [{"filename": "AGENTS.md", "content": "Desktop fallback hit", "score": 0.97}]

    orig_lance_path = lance_backend.LANCE_DB_PATH
    try:
        with patch.object(mcp_lancedb, "_os_root", str(fake_os_root)), \
             patch("mcp_lancedb.os.getcwd", return_value=str(app_bin_dir)), \
             patch.dict(os.environ, {"AIM_WORKSPACE_ROOT": ""}, clear=False):
            out = search_lancedb("desktop query", top_k=3, ctx=ctx)
            assert mock_perform_search.call_args[1]["db_path"] == str(installed_db)
            assert lance_backend.LANCE_DB_PATH == orig_lance_path
            assert "Desktop fallback hit" in out

        # Also verify $HOME cwd without workspaceFolders does NOT umbrella-scan unrelated $HOME/* projects
        fake_home = tmp_path / "fake_home"
        (fake_home / "unrelated-proj" / "joshua_os" / "memory_lance").mkdir(parents=True)
        with patch.object(mcp_lancedb, "_os_root", str(fake_os_root)), \
             patch("mcp_lancedb.os.getcwd", return_value=str(fake_home)), \
             patch("mcp_lancedb.os.path.expanduser", side_effect=lambda p: str(fake_home) if p == "~" else p), \
             patch.dict(os.environ, {"AIM_WORKSPACE_ROOT": ""}, clear=False):
            out_home = search_lancedb("desktop home query", top_k=3, ctx=ctx)
            assert mock_perform_search.call_args[1]["db_path"] == str(installed_db)
            assert lance_backend.LANCE_DB_PATH == orig_lance_path
            assert "[unrelated-proj]" not in out_home
    finally:
        lance_backend.LANCE_DB_PATH = orig_lance_path






