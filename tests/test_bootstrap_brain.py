import pytest
import sys
import os
from unittest.mock import patch, MagicMock

AIM_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AIM_CORE_DIR = os.path.join(AIM_ROOT, "joshua_os", ".aim_core")
if AIM_CORE_DIR not in sys.path:
    sys.path.insert(0, AIM_CORE_DIR)

from bootstrap_brain import bootstrap_foundation

@patch("bootstrap_brain.index_file")
@patch("bootstrap_brain.verify_embedding_engine")
@patch("bootstrap_brain.glob.glob")
@patch("bootstrap_brain.VectorBackend")
@patch("bootstrap_brain.os.walk")
@patch("bootstrap_brain.os.path.exists")
def test_bootstrap_foundation_default(mock_exists, mock_walk, mock_backend, mock_glob, mock_verify, mock_index_file):
    mock_verify.return_value = False
    
    # Mock exists for foundry_dir
    mock_exists.return_value = True
    
    # Mock glob to return some files
    mock_glob.side_effect = lambda pattern, recursive: ["file1.md", "file2.md"] if "AGENTS.md" in pattern else []
    
    # Mock os.walk for foundry
    mock_walk.return_value = [("/fake/foundry", [], ["test.md"])]
    
    # Mock the backend
    mock_instance = MagicMock()
    mock_backend.return_value = mock_instance
    mock_instance.get_table().count_rows.return_value = 10
    
    bootstrap_foundation()
    
    # verify that glob was called with recursive=True
    assert mock_glob.call_args[1].get('recursive') is True
    
    # verify that index_file was called
    assert mock_index_file.call_count > 0

@patch("bootstrap_brain.index_file")
@patch("bootstrap_brain.verify_embedding_engine")
@patch("bootstrap_brain.glob.glob")
@patch("bootstrap_brain.VectorBackend")
def test_bootstrap_foundation_with_custom_dir(mock_backend, mock_glob, mock_verify, mock_index_file):
    mock_verify.return_value = False
    
    mock_glob.return_value = ["/custom/docs/file.md"]
    
    mock_instance = MagicMock()
    mock_backend.return_value = mock_instance
    mock_instance.get_table().count_rows.return_value = 5
    
    bootstrap_foundation(target_dir="/custom/docs")
    
    # Verify that glob was called with custom target
    called_pattern = mock_glob.call_args[0][0]
    assert "custom/docs" in called_pattern
    assert mock_glob.call_args[1].get('recursive') is True
    
    # Verify that index_file was called for the custom file
    mock_index_file.assert_called_once()
    assert mock_index_file.call_args[0][1] == "/custom/docs/file.md"

