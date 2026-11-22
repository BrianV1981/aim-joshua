#!/usr/bin/env python3
import os
import sys

print("--- A.I.M. DOCTOR ---")
print("Validating environment...")

has_errors = False

v = sys.version_info
print(f"Python Version: {v.major}.{v.minor}.{v.micro}")
if v.major < 3 or (v.major == 3 and v.minor < 10):
    print("[ERROR] J.O.S.H.U.A. requires Python 3.10+")
    has_errors = True
else:
    print("[OK] Python Version")

core_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(core_dir)

if os.path.exists(os.path.join(root_dir, "memory_lance")):
    print("[OK] Memory Subsystem")
elif os.path.exists(os.path.join(root_dir, "assets", "default_lance")):
    print("[OK] Memory Subsystem (default_lance seed ready)")
else:
    print("[WARNING] memory_lance directory not found! Run './aim index'.")

for pkg_name, import_name in (
    ("lancedb", "lancedb"),
    ("pandas", "pandas"),
    ("cryptography", "cryptography"),
    ("fastmcp", "fastmcp"),
):
    try:
        __import__(import_name)
        print(f"[OK] {pkg_name} installed")
    except ImportError:
        print(f"[ERROR] {pkg_name} not installed. Run: pip install -r joshua_os/requirements.txt")
        has_errors = True

venv_bin = os.path.join(root_dir, "venv", "bin")
if os.name != "nt" and os.path.isdir(venv_bin):
    stale_scripts = []
    for fname in sorted(os.listdir(venv_bin)):
        fpath = os.path.join(venv_bin, fname)
        if os.path.islink(fpath) or not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, "rb") as fh:
                head = fh.read(512)
        except OSError:
            continue
        if not head.startswith(b"#!") or b"\x00" in head:
            continue
        line1 = head.splitlines()[0][2:].decode("utf-8", errors="ignore").strip()
        if not line1 or line1.startswith("/usr/bin/env"):
            continue
        interp = line1[1 : line1.index('"', 1)] if (line1.startswith('"') and '"' in line1[1:]) else line1.split()[0]
        if os.path.basename(interp).lower().startswith("python") and not os.path.isfile(interp):
            stale_scripts.append(fname)
    if stale_scripts:
        print(
            f"[WARNING] Stale venv script shebangs ({', '.join(stale_scripts[:5])}). "
            "Run './aim update' to repair."
        )
    else:
        print("[OK] Virtualenv Entrypoints")

print("--- DOCTOR COMPLETE ---")
sys.exit(1 if has_errors else 0)
