"""TDD regression suite for Epic #142 P0s: Issue #156 (zero-vector guard) and #173 (doctor probe)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = REPO_ROOT / "joshua_os" / ".aim_core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))


def _seed_project(tmp_path: Path, monkeypatch):
    import bootstrap_brain

    proj = tmp_path / "proj"
    os_root = proj / "joshua_os"
    (proj / "memory-wiki").mkdir(parents=True)
    (os_root / "joshua_os_docs").mkdir(parents=True)
    (os_root / "foundry").mkdir(parents=True)
    (proj / "AGENTS.md").write_text("# Root\nAlways test empirically.\n", encoding="utf-8")
    (proj / "memory-wiki" / "index.md").write_text("# Wiki\nZeroVectorNeedle\n", encoding="utf-8")

    monkeypatch.setattr(bootstrap_brain, "PROJECT_ROOT", str(proj))
    monkeypatch.setattr(bootstrap_brain, "AIM_ROOT", str(os_root))
    monkeypatch.setattr(bootstrap_brain, "verify_embedding_engine", lambda: False)
    return proj, os_root, os_root / "memory_lance"


# ---------------------------------------------------------------------------
# Issue #156: never write zero-vector fragments when embeddings are offline
# ---------------------------------------------------------------------------

def test_offline_index_refuses_zero_vector_writes(tmp_path, monkeypatch):
    import bootstrap_brain
    from lance_backend import VectorBackend

    _, _, db_dir = _seed_project(tmp_path, monkeypatch)

    with pytest.raises(SystemExit) as excinfo:
        bootstrap_brain.bootstrap_foundation(db_path=str(db_dir))

    assert excinfo.value.code == 1
    vb = VectorBackend(path=str(db_dir))
    assert vb.get_table().count_rows() == 0


def test_allow_lexical_only_opt_in_writes_fragments(tmp_path, monkeypatch):
    import bootstrap_brain
    from lance_backend import VectorBackend

    _, _, db_dir = _seed_project(tmp_path, monkeypatch)

    bootstrap_brain.bootstrap_foundation(db_path=str(db_dir), allow_lexical_only=True)

    vb = VectorBackend(path=str(db_dir))
    rows = vb.get_table().to_arrow().to_pylist()
    assert len(rows) > 0
    # Explicit opt-in still writes 768-dim zero vectors so FTS remains usable.
    assert all(len(r["vector"]) == 768 for r in rows)


def test_index_file_drops_chunks_without_embedding(tmp_path, monkeypatch):
    import bootstrap_brain
    from lance_backend import VectorBackend

    doc = tmp_path / "doc.md"
    doc.write_text("# Doc\nalpha beta gamma\n", encoding="utf-8")
    backend = VectorBackend(path=str(tmp_path / "db"))
    stats = {"zero_skipped": 0}
    monkeypatch.setattr(bootstrap_brain, "get_embedding", lambda *a, **k: None)

    written = bootstrap_brain.index_file(
        backend,
        str(doc),
        "expert_knowledge",
        use_embeddings=True,
        stats=stats,
    )

    assert written == 0
    assert stats["zero_skipped"] > 0
    assert backend.get_table().count_rows() == 0


def test_index_cli_exposes_allow_lexical_only_flag():
    res = subprocess.run(
        [sys.executable, str(CORE_DIR / "aim_cli.py"), "index", "--help"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
    )
    assert res.returncode == 0, res.stderr
    assert "--allow-lexical-only" in res.stdout


# ---------------------------------------------------------------------------
# Issue #173: embedding connectivity probe + --fix + --strict
# ---------------------------------------------------------------------------

def test_probe_reports_offline_on_connection_error(monkeypatch):
    import aim_doctor

    monkeypatch.setattr(
        aim_doctor,
        "_load_models_config",
        lambda: {
            "embedding_provider": "local",
            "embedding": "nomic-embed-text",
            "embedding_endpoint": "http://127.0.0.1:9/api/embeddings",
        },
    )
    import requests

    def _boom(*_a, **_k):
        raise requests.exceptions.ConnectionError("refused")

    monkeypatch.setattr(aim_doctor.requests, "post", _boom)

    info = aim_doctor.probe_embedding_provider(timeout=1.0)
    assert info["status"] == "offline"
    assert info["provider"] == "local"


def test_probe_reports_ok_with_dim_and_latency(monkeypatch):
    import aim_doctor

    monkeypatch.setattr(
        aim_doctor,
        "_load_models_config",
        lambda: {
            "embedding_provider": "local",
            "embedding": "nomic-embed-text",
            "embedding_endpoint": "http://127.0.0.1:11434/api/embeddings",
        },
    )

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"embedding": [0.01] * 768}

    monkeypatch.setattr(aim_doctor.requests, "post", lambda *a, **k: _Resp())

    info = aim_doctor.probe_embedding_provider(timeout=1.0)
    assert info["status"] == "ok"
    assert info["dim"] == 768
    assert info["latency_ms"] >= 0


def test_compute_exit_code_strict_semantics():
    import aim_doctor

    assert aim_doctor._compute_exit_code(has_errors=False, warning_count=0, strict=False) == 0
    assert aim_doctor._compute_exit_code(has_errors=False, warning_count=1, strict=False) == 0
    assert aim_doctor._compute_exit_code(has_errors=False, warning_count=1, strict=True) == 1
    assert aim_doctor._compute_exit_code(has_errors=True, warning_count=0, strict=False) == 1


def test_doctor_fix_repairs_environment(monkeypatch):
    import aim_doctor

    calls = {}

    def _fake_repair(os_dir):
        calls["os_dir"] = os_dir
        return 2

    monkeypatch.setattr(aim_doctor, "repair_venv_shebangs", _fake_repair)
    actions = aim_doctor.apply_fixes(str(REPO_ROOT / "joshua_os"))

    assert calls["os_dir"] == str(REPO_ROOT / "joshua_os")
    assert any("shebang" in a.lower() for a in actions)


def test_doctor_cli_exposes_fix_and_strict():
    res = subprocess.run(
        [sys.executable, str(CORE_DIR / "aim_cli.py"), "doctor", "--help"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
    )
    assert res.returncode == 0, res.stderr
    assert "--fix" in res.stdout
    assert "--strict" in res.stdout
