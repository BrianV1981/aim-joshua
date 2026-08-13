import os
import subprocess
import pytest
from pathlib import Path

def test_promote_e2e(tmp_path):
    # 1. Setup a bare "origin" repo
    origin_dir = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(origin_dir)], check=True)

    # 2. Setup the local repo clone
    repo_dir = tmp_path / "repo"
    subprocess.run(["git", "clone", str(origin_dir), str(repo_dir)], check=True)

    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_dir, check=True)

    # 3. Create initial commit on main
    (repo_dir / "README.md").write_text("initial")
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo_dir, check=True)
    
    # Need to push to origin main so 'git fetch origin' in promote won't fail
    subprocess.run(["git", "push", "origin", "main"], cwd=repo_dir, check=True)

    # 4. Create a worktree for the dev branch
    worktree_dir = tmp_path / "repo" / "workspace" / "issue-64"
    worktree_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "worktree", "add", "-b", "fix/issue-64", str(worktree_dir), "main"], cwd=repo_dir, check=True)

    # 5. Make a change in the worktree
    (worktree_dir / "README.md").write_text("updated in worktree")
    subprocess.run(["git", "add", "README.md"], cwd=worktree_dir, check=True)
    subprocess.run(["git", "commit", "-m", "fix in worktree"], cwd=worktree_dir, check=True)

    # 6. Run cmd_promote from the worktree
    import sys
    aim_core_path = Path(__file__).parent.parent / "joshua_os" / ".aim_core"
    sys.path.insert(0, str(aim_core_path))
    from aim_cli import cmd_promote
    
    original_getcwd = os.getcwd
    def mock_getcwd():
        return str(worktree_dir)
    os.getcwd = mock_getcwd
    
    import builtins
    original_input = builtins.input
    builtins.input = lambda prompt: 'yes'
    
    try:
        class DummyArgs:
            pass
        cmd_promote(DummyArgs())
    finally:
        os.getcwd = original_getcwd
        builtins.input = original_input
        
    # 7. Verify promotion
    assert not worktree_dir.exists()
    
    branches = subprocess.run(["git", "branch"], cwd=repo_dir, capture_output=True, text=True).stdout
    branch_list = [b.strip("* ") for b in branches.splitlines()]
    assert "fix/issue-64" not in branch_list
    
    subprocess.run(["git", "checkout", "main"], cwd=repo_dir, check=True)
    assert (repo_dir / "README.md").read_text() == "updated in worktree"
    
    remotes = subprocess.run(["git", "ls-remote", "origin"], cwd=repo_dir, capture_output=True, text=True).stdout
    assert "refs/heads/archive-fix/issue-64-" in remotes
