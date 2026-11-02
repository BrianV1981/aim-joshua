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

print("--- DOCTOR COMPLETE ---")
sys.exit(1 if has_errors else 0)
