import subprocess
import os

def test_aim_help():
    # Ensure the wrapper script can run --help successfully
    result = subprocess.run(["./aim", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower() or "options:" in result.stdout.lower()

def test_aim_doctor():
    result = subprocess.run(["./aim", "doctor"], capture_output=True, text=True)
    assert result.returncode == 0
    out = result.stdout.lower()
    assert "doctor" in out or "diagnostic" in out or "status" in out

def test_aim_swarm_removed():
    # Deprecated swarm subcommand must not be exposed on the CLI router
    help_res = subprocess.run(["./aim", "--help"], capture_output=True, text=True)
    assert help_res.returncode == 0
    assert "Manage co-agent swarms" not in help_res.stdout
    swarm_res = subprocess.run(["./aim", "swarm"], capture_output=True, text=True)
    assert swarm_res.returncode == 2

def test_readme_ecosystem_block():
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()
    assert "<!-- AIM_ECOSYSTEM_START -->" in readme
    assert "https://github.com/BrianV1981/aim-ecosystem" in readme
    assert "<!-- AIM_ECOSYSTEM_END -->" in readme

def test_cmd_update_preserves_coagent_blueprint_and_config(tmp_path):
    import json
    import shutil
    import sys

    # Build a synthetic co-agent node in tmp_path
    node_dir = tmp_path / "aim-mock-node"
    node_os = node_dir / "joshua_os"
    node_core = node_os / ".aim_core"
    node_core.mkdir(parents=True)

    # Seed co-agent blueprint and tenant artifacts that MUST be preserved
    (node_dir / "AGENTS.md").write_text("# Custom Co-Agent Blueprint", encoding="utf-8")
    (node_dir / "TOOLS.md").write_text("# Custom Tools", encoding="utf-8")
    (node_dir / "manifest.json").write_text('{"name": "aim-mock-node"}', encoding="utf-8")
    (node_dir / "memory-wiki").mkdir()
    (node_dir / "memory-wiki" / "index.md").write_text("# Node Wiki", encoding="utf-8")
    (node_dir / "artifacts").mkdir()
    (node_dir / "artifacts" / "AUDIT_TEST.md").write_text("# Living Audit", encoding="utf-8")

    # Seed a custom CONFIG.json and an outdated dummy aim_cli.py in the mock node
    custom_cfg = {"settings": {"github_projects": {"number": 99}}}
    (node_core / "CONFIG.json").write_text(json.dumps(custom_cfg), encoding="utf-8")
    shutil.copy2("joshua_os/.aim_core/config_utils.py", node_core / "config_utils.py")
    shutil.copy2("joshua_os/.aim_core/aim_cli.py", node_core / "aim_cli.py")

    res = subprocess.run(
        [sys.executable, str(node_core / "aim_cli.py"), "update", "--source", os.getcwd(), "--skip-deps"],
        cwd=str(node_dir),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    assert "Sovereign Engine Update Complete" in res.stdout
    assert (node_dir / "AGENTS.md").read_text(encoding="utf-8") == "# Custom Co-Agent Blueprint"
    assert (node_dir / "TOOLS.md").read_text(encoding="utf-8") == "# Custom Tools"
    assert (node_dir / "manifest.json").read_text(encoding="utf-8") == '{"name": "aim-mock-node"}'
    assert (node_dir / "memory-wiki" / "index.md").read_text(encoding="utf-8") == "# Node Wiki"
    assert (node_dir / "artifacts" / "AUDIT_TEST.md").read_text(encoding="utf-8") == "# Living Audit"
    assert json.loads((node_core / "CONFIG.json").read_text(encoding="utf-8")) == custom_cfg
    assert (node_os / "handoff").is_dir()
    assert (node_os / "hooks").is_dir()



