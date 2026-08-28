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

