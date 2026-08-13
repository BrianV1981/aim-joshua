"""A+ acceptance: exercise the real ./aim wrapper (no mocked cmd_*)."""
import json
import os
import subprocess
import uuid
from pathlib import Path


def _aim(*args):
    return subprocess.run(["./aim", *args], capture_output=True, text=True)


def _json_from_stdout(stdout: str):
    text = stdout.strip()
    for i, ch in enumerate(text):
        if ch in "[{":
            return json.loads(text[i:])
    return json.loads(text)


def test_aim_search():
    result = _aim("search", "worktree", "--top-k", "1")
    assert result.returncode == 0, result.stderr
    assert "SEARCH RESULTS" in result.stdout


def test_aim_search_json():
    result = _aim("search", "worktree", "--top-k", "1", "--json")
    assert result.returncode == 0, result.stderr
    parsed = _json_from_stdout(result.stdout)
    assert isinstance(parsed, (list, dict))
    # NOTICE must not live on stdout (GHA has no embeddings)
    assert "[NOTICE]" not in result.stdout


def test_aim_unknown_verb():
    result = _aim("unknown_verb")
    assert result.returncode == 2
    assert "invalid choice" in result.stderr.lower()


def test_aim_vault_doctor():
    result = _aim("vault", "doctor")
    assert result.returncode == 0, result.stderr
    out = result.stdout.lower()
    assert "keyring" in out or "blackbox" in out


def test_aim_map_footer_uses_aim_search():
    result = _aim("map")
    assert result.returncode == 0, result.stderr
    assert "./aim search" in result.stdout
    assert "joshua_os search" not in result.stdout


def test_promote_math():
    common = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    repo_root = os.path.dirname(os.path.abspath(os.path.join(os.getcwd(), common)))
    assert os.path.isdir(os.path.join(repo_root, ".git"))


def test_vault_hermetic_decrypt(tmp_path):
    marker = f"hello hermetic vault {uuid.uuid4().hex[:8]}"
    transcript = tmp_path / "raw.jsonl"
    transcript.write_text(json.dumps({"type": "USER_INPUT", "content": marker}) + "\n")
    sid = f"hermetic-{uuid.uuid4().hex[:8]}"
    vessel = os.getcwd()
    try:
        seal = _aim(
            "vault",
            "seal",
            "--path",
            str(transcript),
            "--session-id",
            sid,
            "--vessel",
            vessel,
        )
        assert seal.returncode == 0, seal.stdout + seal.stderr
        audit = _aim("vault", "audit", sid, "--vessel", vessel)
        assert audit.returncode == 0, audit.stdout + audit.stderr
        assert marker in audit.stdout
    finally:
        blob = Path(vessel) / "archive" / ".raw_jsonl_blackbox" / f"{sid}.enc"
        if blob.is_file():
            blob.unlink()
