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
    
    # verify that glob was called with recursive=True and includes PROJECT_ROOT/memory-wiki and artifacts/AUDIT_*.md
    assert mock_glob.call_args[1].get('recursive') is True
    globbed_patterns = [call[0][0] for call in mock_glob.call_args_list]
    assert any(os.path.join("memory-wiki", "**", "*.md") in p and "joshua_os" not in p for p in globbed_patterns)
    assert any(os.path.join("artifacts", "AUDIT_*.md") in p for p in globbed_patterns)
    
    # verify that index_file was called
    assert mock_index_file.call_count > 0

def test_local_ollama_uses_fast_connect_timeout():
    from plugins.datajack import forensic_utils
    with patch.object(forensic_utils, "PROVIDER_TYPE", "local"), \
         patch.object(forensic_utils.requests, "post") as mock_post:
        mock_post.side_effect = forensic_utils.requests.exceptions.ConnectionError("refused")
        res = forensic_utils.get_embedding("test query")
        assert res is None
        assert mock_post.call_args[1].get("timeout") == (0.5, 15)

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


def test_bootstrap_foundation_idempotent_two_runs_and_no_basename_collision(tmp_path, monkeypatch):
    """Issue #122 (JOSH-W06 + JOSH-028): Two consecutive runs must keep count_rows() identical, avoid index.md collisions, and preserve session_history."""
    import bootstrap_brain
    from lance_backend import VectorBackend

    proj_root = tmp_path / "proj"
    os_root = proj_root / "joshua_os"
    (proj_root / "memory-wiki").mkdir(parents=True)
    (os_root / "memory-wiki").mkdir(parents=True)
    (os_root / "joshua_os_docs").mkdir(parents=True)
    (os_root / "foundry").mkdir(parents=True)

    (proj_root / "AGENTS.md").write_text("# Root Constitution Mandate\nAlways test empirically.\n", encoding="utf-8")
    (proj_root / "memory-wiki" / "index.md").write_text("# Root Wiki Index\nUniqueTokenRootWikiAlpha\n", encoding="utf-8")
    (os_root / "memory-wiki" / "index.md").write_text("# Engine Wiki Index\nUniqueTokenEngineWikiBeta\n", encoding="utf-8")
    (os_root / "joshua_os_docs" / "README.md").write_text("# OS Docs Readme\nUniqueTokenOsDocsGamma\n", encoding="utf-8")
    (os_root / "foundry" / "README.md").write_text("# Foundry Readme\nUniqueTokenFoundryDelta\n", encoding="utf-8")

    db_dir = os_root / "memory_lance"
    vb = VectorBackend(path=str(db_dir))
    # Seed a historical session fragment that MUST survive full foundation re-indexing
    vb.add_fragments([
        {
            "session_id": "hist-session-001",
            "type": "session_history",
            "content": "Preserved historical session turn UniqueTokenHistoryOmega",
            "source_db": "live_session",
            "vector": [0.0] * 768,
        }
    ])
    assert vb.get_table().count_rows() == 1

    monkeypatch.setattr(bootstrap_brain, "PROJECT_ROOT", str(proj_root))
    monkeypatch.setattr(bootstrap_brain, "AIM_ROOT", str(os_root))
    monkeypatch.setattr(bootstrap_brain, "verify_embedding_engine", lambda: False)

    bootstrap_brain.bootstrap_foundation(db_path=str(db_dir))
    rows_after_run1 = vb.get_table().count_rows()
    assert rows_after_run1 == 6  # 1 session_history + 5 distinct markdown files

    # Second run must NOT append duplicate rows
    bootstrap_brain.bootstrap_foundation(db_path=str(db_dir))
    rows_after_run2 = vb.get_table().count_rows()
    assert rows_after_run2 == rows_after_run1

    all_rows = vb.get_table().to_arrow().to_pylist()
    sids = {r["session_id"] for r in all_rows}
    assert sids == {
        "hist-session-001",
        "foundation-AGENTS.md",
        "foundation-memory-wiki/index.md",
        "foundation-joshua_os/memory-wiki/index.md",
        "foundation-joshua_os/joshua_os_docs/README.md",
        "expert-joshua_os/foundry/README.md",
    }

    # Both colliding basenames (index.md and README.md) are searchable via Tantivy FTS
    assert len(vb.search(None, "UniqueTokenRootWikiAlpha", top_k=5)) == 1
    assert len(vb.search(None, "UniqueTokenEngineWikiBeta", top_k=5)) == 1
    assert len(vb.search(None, "UniqueTokenHistoryOmega", top_k=5)) == 1

    # Custom --dir ingestion also upserts idempotently without basename collisions
    custom_docs = proj_root / "docs"
    (custom_docs / "nested").mkdir(parents=True)
    (custom_docs / "index.md").write_text("# Custom Docs Root\nCustomDocsRootToken\n", encoding="utf-8")
    (custom_docs / "nested" / "index.md").write_text("# Custom Docs Nested\nCustomDocsNestedToken\n", encoding="utf-8")

    bootstrap_brain.bootstrap_foundation(target_dir=str(custom_docs), db_path=str(db_dir))
    rows_custom_1 = vb.get_table().count_rows()
    assert rows_custom_1 == rows_after_run2 + 2

    bootstrap_brain.bootstrap_foundation(target_dir=str(custom_docs), db_path=str(db_dir))
    rows_custom_2 = vb.get_table().count_rows()
    assert rows_custom_2 == rows_custom_1


