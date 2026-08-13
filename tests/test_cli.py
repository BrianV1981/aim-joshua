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
