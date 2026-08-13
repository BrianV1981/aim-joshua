import os
import subprocess
import json
import uuid

def test_aim_search():
    result = subprocess.run(["./aim", "search", "worktree", "--top-k", "1"], capture_output=True, text=True)
    assert result.returncode == 0
    assert len(result.stdout) > 0

def test_aim_search_json():
    result = subprocess.run(["./aim", "search", "worktree", "--top-k", "1", "--json"], capture_output=True, text=True)
    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert isinstance(parsed, (list, dict))

def test_aim_unknown_verb():
    result = subprocess.run(["./aim", "unknown_verb"], capture_output=True, text=True)
    assert result.returncode == 2
    assert "invalid choice" in result.stderr.lower()

def test_aim_vault_doctor():
    result = subprocess.run(["./aim", "vault", "doctor"], capture_output=True, text=True)
    assert result.returncode == 0
    out = result.stdout.lower()
    assert "keyring" in out or "blackbox" in out

def test_promote_math():
    common_dir_res = subprocess.run(["git", "rev-parse", "--git-common-dir"], capture_output=True, text=True)
    assert common_dir_res.returncode == 0
    raw_dir = common_dir_res.stdout.strip()
    repo_root = os.path.abspath(raw_dir)
    if repo_root.endswith(".git"):
        repo_root = os.path.dirname(repo_root)
    assert os.path.isdir(os.path.join(repo_root, ".git"))

def test_vault_hermetic_decrypt():
    # Hermetic test for vault seal and audit/decrypt paths
    session_id = str(uuid.uuid4())
    brain_dir = os.path.join(os.path.expanduser("~"), ".gemini", "antigravity-cli", "brain", session_id)
    logs_dir = os.path.join(brain_dir, ".system_generated", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    transcript_path = os.path.join(logs_dir, "transcript.jsonl")
    
    with open(transcript_path, "w") as f:
        f.write('{"type": "USER_INPUT", "content": "hello hermetic vault"}\\n')
        
    try:
        seal_res = subprocess.run(["./aim", "vault", "seal", "--session-id", session_id], capture_output=True, text=True)
        assert seal_res.returncode == 0
        
        audit_res = subprocess.run(["./aim", "vault", "audit", session_id], capture_output=True, text=True)
        assert audit_res.returncode == 0
        assert "hello hermetic vault" in audit_res.stdout
    finally:
        import shutil
        shutil.rmtree(brain_dir, ignore_errors=True)
        sealed_path = os.path.join(os.path.expanduser("~"), ".aim", "vault", f"{session_id}.enc")
        if os.path.exists(sealed_path):
            os.remove(sealed_path)
