"""TDD regression suite for v1.1.4 audit remediation sprint (Issues #137, #138, #139)."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CORE_DIR = os.path.join(REPO_ROOT, "joshua_os", ".aim_core")

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
    env["PYTHON_KEYRING_BACKEND"] = "keyring.backends.null.Keyring"
    return env


# ---------------------------------------------------------------------------
# Issue #137: reasoning_utils model routing, keyring alignment, & synthesis rc=1
# ---------------------------------------------------------------------------

def test_issue_137_reasoning_utils_respects_configured_models_and_maps_gemini_rest():
    """generate_reasoning must never clobber configured models with agy-3.1-flash-lite-preview."""
    import reasoning_utils

    # 1. OpenRouter receives exact configured model
    cfg_or = {
        "models": {
            "tiers": {
                "default_reasoning": {
                    "provider": "openrouter",
                    "model": "anthropic/claude-3.5-sonnet",
                    "endpoint": "https://openrouter.ai/api/v1",
                    "auth_type": "API Key",
                }
            }
        }
    }
    with patch.object(reasoning_utils, "execute_openrouter", return_value="OK") as mock_or:
        out = reasoning_utils.generate_reasoning("Ping", config=cfg_or)
        assert out == "OK"
        assert mock_or.call_args[0][2] == "anthropic/claude-3.5-sonnet"

    # 2. Local (ollama) normalization + exact model forwarded
    cfg_ollama = {
        "models": {
            "default_reasoning": {
                "provider": "local (ollama)",
                "model": "qwen2.5-coder:14b",
                "endpoint": "http://127.0.0.1:11434/api/generate",
            }
        },
        "settings": {"ollama_num_ctx": 16384},
    }
    with patch.object(reasoning_utils, "execute_ollama", return_value="OK") as mock_ol:
        out = reasoning_utils.generate_reasoning("Ping", config=cfg_ollama)
        assert out == "OK"
        assert mock_ol.call_args[0][2] == "qwen2.5-coder:14b"
        assert mock_ol.call_args[0][4] == 16384

    # 3. Google REST maps agy-* CLI aliases to valid gemini-* REST model IDs while preserving explicit gemini-* IDs
    assert reasoning_utils.resolve_gemini_rest_model("agy-flash-latest") == "gemini-2.5-flash"
    assert reasoning_utils.resolve_gemini_rest_model("agy-3.1-pro-preview") == "gemini-2.5-pro"
    assert reasoning_utils.resolve_gemini_rest_model("gemini-2.5-pro") == "gemini-2.5-pro"

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"candidates": [{"content": {"parts": [{"text": "OK"}]}}]}
    with patch.object(reasoning_utils.keyring, "get_password", return_value="test-google-key"), patch.object(
        reasoning_utils.requests, "post", return_value=mock_resp
    ) as mock_post:
        res = reasoning_utils.execute_google("Ping", "Sys", "agy-3.1-pro-preview", auth_type="API Key")
        assert res == "OK"
        called_url = mock_post.call_args[0][0]
        assert "/models/gemini-2.5-pro:generateContent" in called_url

    # 4. OpenAI-compat reads openai-api-key saved by aim_config.py and normalizes /v1/chat/completions
    mock_oa_resp = MagicMock()
    mock_oa_resp.raise_for_status.return_value = None
    mock_oa_resp.json.return_value = {"choices": [{"message": {"content": "OK"}}]}

    def _fake_keyring(service, key):
        return "sk-openai-test" if key == "openai-api-key" else None

    with patch.object(reasoning_utils.keyring, "get_password", side_effect=_fake_keyring), patch.object(
        reasoning_utils.requests, "post", return_value=mock_oa_resp
    ) as mock_oa_post:
        res_oa = reasoning_utils.execute_openai("Ping", "Sys", "gpt-4o-mini", "https://api.example.com")
        assert res_oa == "OK"
        assert mock_oa_post.call_args[0][0] == "https://api.example.com/v1/chat/completions"
        assert mock_oa_post.call_args[1]["headers"]["Authorization"] == "Bearer sk-openai-test"
        assert mock_oa_post.call_args[1]["json"]["model"] == "gpt-4o-mini"


def test_issue_137_unmocked_audit_and_recall_fail_closed_on_synthesis_error(tmp_path):
    """When history.db is populated but LLM provider fails (e.g. missing API key), ./aim audit & ./aim recall must exit rc=1 without writing bogus WEEKLY_SITREP.md."""
    import bootstrap_install

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    consumer = tmp_path / "synth-err-app"
    consumer.mkdir()
    bootstrap_install.install_project(
        target_dir=str(consumer),
        mode="clean",
        source_dir=REPO_ROOT,
        skip_deps=True,
        home_dir=str(fake_home),
        skip_shell_rc=True,
    )

    # Seed valid history.db + history_fts row and force an unreachable local endpoint
    hist_db = consumer / "joshua_os" / "archive" / "history.db"
    hist_db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(hist_db))
    conn.execute("CREATE TABLE history (session_id TEXT PRIMARY KEY, timestamp TEXT, content TEXT)")
    conn.execute("CREATE VIRTUAL TABLE history_fts USING fts5(session_id, timestamp, content)")
    conn.execute(
        "INSERT INTO history VALUES (?, ?, ?)",
        ("sess-1", "2026-11-21T00:00:00Z", "Implemented worktree isolation gate."),
    )
    conn.execute(
        "INSERT INTO history_fts VALUES (?, ?, ?)",
        ("sess-1", "2026-11-21T00:00:00Z", "Implemented worktree isolation gate."),
    )
    conn.commit()
    conn.close()

    cfg_file = consumer / "joshua_os" / ".aim_core" / "CONFIG.json"
    cfg_file.write_text(
        json.dumps(
            {
                "models": {
                    "default_reasoning": {
                        "provider": "openai-compat",
                        "model": "local-test",
                        "endpoint": "",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    env = _hermetic_env(fake_home)
    launcher = _consumer_launcher(consumer)

    res_audit = subprocess.run([launcher, "audit"], cwd=str(consumer), env=env, capture_output=True, text=True)
    assert res_audit.returncode == 1
    assert "Error generating strategic synthesis" in res_audit.stderr
    assert not (consumer / "joshua_os" / "WEEKLY_SITREP.md").exists()

    res_recall = subprocess.run(
        [launcher, "recall", "worktree"], cwd=str(consumer), env=env, capture_output=True, text=True
    )
    assert res_recall.returncode == 1
    assert "Error generating memory recall" in res_recall.stderr


# ---------------------------------------------------------------------------
# Issue #138: 768-dim provider embeddings, aim_bake UTC, & Tantivy query parsing
# ---------------------------------------------------------------------------

def test_issue_138_embedding_providers_enforce_768_dim_and_reject_mismatches(capsys):
    """Google and OpenAI-compat embeddings request 768 dims and reject incompatible dimensions cleanly."""
    from plugins.datajack import forensic_utils

    # 1. Google passes output_dimensionality=768 and L2-normalizes output
    fake_client = MagicMock()
    fake_client.models.embed_content.return_value = SimpleNamespace(
        embeddings=[SimpleNamespace(values=[3.0, 4.0] + [0.0] * 766)]
    )
    with patch.object(forensic_utils, "PROVIDER_TYPE", "google"), patch.object(
        forensic_utils, "PROVIDER_MODEL", "gemini-embedding-001"
    ), patch.object(forensic_utils.keyring, "get_password", return_value="gkey"), patch.object(
        forensic_utils.genai, "Client", return_value=fake_client
    ):
        vec = forensic_utils.get_embedding("hello world", task_type="RETRIEVAL_QUERY")
        assert vec is not None and len(vec) == 768
        assert math.isclose(math.sqrt(sum(v * v for v in vec)), 1.0, rel_tol=1e-5)
        call_cfg = fake_client.models.embed_content.call_args[1]["config"]
        assert call_cfg["output_dimensionality"] == 768
        assert call_cfg["task_type"] == "RETRIEVAL_QUERY"

    # 2. OpenAI-compat passes dimensions=768 for text-embedding-3-* and falls back to openai-api-key
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"data": [{"embedding": [0.1] * 768}]}
    with patch.object(forensic_utils, "PROVIDER_TYPE", "openai-compat"), patch.object(
        forensic_utils, "PROVIDER_MODEL", "text-embedding-3-small"
    ), patch.object(forensic_utils, "PROVIDER_ENDPOINT", "https://api.openai.com"), patch.object(
        forensic_utils.keyring,
        "get_password",
        side_effect=lambda _s, k: "sk-oa" if k == "openai-api-key" else None,
    ), patch.object(
        forensic_utils.requests, "post", return_value=mock_resp
    ) as mock_post:
        vec_oa = forensic_utils.get_embedding("hello world")
        assert vec_oa is not None and len(vec_oa) == 768
        sent_payload = mock_post.call_args[1]["json"]
        assert sent_payload["dimensions"] == 768
        assert mock_post.call_args[1]["headers"]["Authorization"] == "Bearer sk-oa"

    # 3. Wrong-dimension custom model returns None with explicit stderr diagnostic
    bad_resp = MagicMock()
    bad_resp.raise_for_status.return_value = None
    bad_resp.json.return_value = {"embedding": [0.5] * 1024}
    with patch.object(forensic_utils, "PROVIDER_TYPE", "local"), patch.object(
        forensic_utils, "PROVIDER_MODEL", "mxbai-embed-large"
    ), patch.object(forensic_utils.requests, "post", return_value=bad_resp):
        bad_vec = forensic_utils.get_embedding("hello world")
        assert bad_vec is None
        err = capsys.readouterr().err
        assert "expected 768, got 1024" in err


def test_issue_138_tantivy_capitalized_and_alphanumeric_lexical_search(tmp_path):
    """Sentence-initial capitalized queries ('Explain worktree') and alphanumeric tokens ('FTS5', '#135') must match in offline BM25 search."""
    from lance_backend import VectorBackend, generate_tantivy_query

    fts_q, nouns = generate_tantivy_query("Explain LanceDB FTS5 #135")
    assert "+" not in fts_q
    assert "explain*" in fts_q
    assert "lancedb*" in fts_q
    assert "fts5*" in fts_q
    assert "135" in fts_q
    # Sentence-initial plain verb 'Explain' is not treated as a proper noun, while LanceDB and FTS5 are
    assert "Explain" not in nouns
    assert "LanceDB" in nouns
    assert "FTS5" in nouns

    db_dir = tmp_path / "tantivy_lance"
    vb = VectorBackend(path=str(db_dir))
    vb.add_fragments(
        [
            {
                "session_id": "doc-1",
                "type": "foundation_knowledge",
                "content": "Always isolate code inside a git worktree and query SQLite FTS5 session logs from issue #135.",
                "source_db": "operations.md",
                "vector": [0.0] * 768,
            }
        ]
    )

    # Previously 'Explain worktree' generated '+explain* worktree*' and returned [] because 'explain' wasn't in the doc!
    hits_cap = vb.search(None, "Explain worktree", top_k=5)
    assert len(hits_cap) == 1
    assert hits_cap[0]["session_id"] == "doc-1"

    hits_num = vb.search(None, "FTS5 #135", top_k=5)
    assert len(hits_num) == 1
    assert hits_num[0]["session_id"] == "doc-1"


# ---------------------------------------------------------------------------
# Issue #139: Relocated venv shebang self-healing & archive-* branch pruning
# ---------------------------------------------------------------------------

def test_issue_139_repair_venv_shebangs_and_prune_remote_local_archives(tmp_path):
    """repair_venv_shebangs fixes broken moved shebangs on POSIX, and cmd_prune_remote handles archive-* + --include-local."""
    import aim_cli
    import bootstrap_install

    if os.name != "nt":
        os_dir = tmp_path / "moved_proj" / "joshua_os"
        bin_dir = os_dir / "venv" / "bin"
        bin_dir.mkdir(parents=True)
        real_py = bin_dir / "python3"
        real_py.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        real_py.chmod(0o755)

        broken_pytest = bin_dir / "pytest"
        broken_pytest.write_text(
            "#!/nonexistent/old/clone/venv/bin/python3\nimport sys\nprint('ok')\n",
            encoding="utf-8",
        )
        broken_pytest.chmod(0o755)

        shell_helper = bin_dir / "activate_helper"
        shell_helper.write_text("#!/bin/sh\necho keep\n", encoding="utf-8")
        shell_helper.chmod(0o755)

        repaired = bootstrap_install.repair_venv_shebangs(str(os_dir))
        assert repaired == 1
        assert broken_pytest.read_text(encoding="utf-8").splitlines()[0] == f"#!{real_py}"
        assert shell_helper.read_text(encoding="utf-8").splitlines()[0] == "#!/bin/sh"
        # Second pass is a no-op
        assert bootstrap_install.repair_venv_shebangs(str(os_dir)) == 0

    # Test cmd_prune_remote with origin/archive-feature/* and --include-local in a real git repo + bare remote
    bare_remote = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(bare_remote)], check=True, capture_output=True)

    repo = tmp_path / "prune_repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=str(repo), check=True, capture_output=True)
    (repo / "README.md").write_text("# Prune Test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@localhost",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            "init",
        ],
        cwd=str(repo),
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "remote", "add", "origin", str(bare_remote)], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=str(repo), check=True, capture_output=True)

    for bname in ("archive-fix/issue-1-20261121-0100", "archive-feature/ui-20261121-0105", "fix/issue-99"):
        subprocess.run(["git", "branch", bname], cwd=str(repo), check=True, capture_output=True)
        subprocess.run(["git", "push", "origin", bname], cwd=str(repo), check=True, capture_output=True)

    # Also create an active worktree branch fix/issue-100 that MUST NOT be deleted locally
    wt_dir = repo / "workspace" / "issue-100"
    subprocess.run(
        ["git", "worktree", "add", str(wt_dir), "-b", "fix/issue-100"],
        cwd=str(repo),
        check=True,
        capture_output=True,
    )

    real_run = subprocess.run

    def _run_with_mock_gh(cmd, *a, **kw):
        if isinstance(cmd, list) and cmd and cmd[0] == "gh":
            return subprocess.CompletedProcess(cmd, 0, stdout='[{"headRefName": "fix/issue-99"}]', stderr="")
        return real_run(cmd, *a, **kw)

    with patch.object(aim_cli, "BASE_DIR", str(repo)), patch.object(
        aim_cli.subprocess, "run", side_effect=_run_with_mock_gh
    ):
        aim_cli.cmd_prune_remote(argparse.Namespace(confirm=True, include_local=True))

    rem_after = subprocess.run(["git", "branch", "-r"], cwd=str(repo), capture_output=True, text=True, check=True).stdout
    assert "origin/archive-fix/issue-1-20261121-0100" not in rem_after
    assert "origin/archive-feature/ui-20261121-0105" not in rem_after
    # Open PR branch fix/issue-99 is protected!
    assert "origin/fix/issue-99" in rem_after

    loc_after = subprocess.run(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads/"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert "archive-fix/issue-1-20261121-0100" not in loc_after
    assert "archive-feature/ui-20261121-0105" not in loc_after
    assert "fix/issue-99" in loc_after
    assert "fix/issue-100" in loc_after
    assert "main" in loc_after
