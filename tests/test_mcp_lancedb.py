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
    mock_perform_search.assert_called_once_with("test query", top_k=10)

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
    # Mock context
    ctx = MagicMock()
    ctx.request_context.session.client_params.model_extra = {
        "workspaceFolders": [{"uri": "file:///my/custom/workspace"}]
    }
    mock_perform_search.return_value = []
    
    search_lancedb("test query", ctx=ctx)
    
    # Check that LANCE_DB_PATH was set using the custom workspace path
    import lance_backend
    assert lance_backend.LANCE_DB_PATH == "/my/custom/workspace/joshua_os/memory_lance"


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

    def side_effect(query, top_k=10):
        import lance_backend
        if "agent-a" in lance_backend.LANCE_DB_PATH:
            return [{"filename": "a_doc.md", "content": "From A", "score": 0.75}]
        return [{"filename": "b_doc.md", "content": "From B", "score": 0.92}]

    mock_perform_search.side_effect = side_effect

    with patch("mcp_lancedb.os.getcwd", return_value=str(tmp_path)):
        out = search_lancedb("umbrella query", top_k=5)

    assert mock_perform_search.call_count == 2
    assert "[1] Score: 0.9200 | Source: [agent-b] b_doc.md" in out
    assert "[2] Score: 0.7500 | Source: [agent-a] a_doc.md" in out


