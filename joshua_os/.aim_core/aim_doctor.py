#!/usr/bin/env python3
import sys
import os

print("--- A.I.M. DOCTOR ---")
print("Validating environment...")

has_errors = False

# Check python version
v = sys.version_info
print(f"Python Version: {v.major}.{v.minor}.{v.micro}")
if v.major < 3 or (v.major == 3 and v.minor < 8):
    print("[ERROR] A.I.M. requires Python 3.8+")
    has_errors = True
else:
    print("[OK] Python Version")

# Check required paths
core_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(core_dir)

if not os.path.exists(os.path.join(root_dir, 'memory_lance')):
    print("[WARNING] memory_lance directory not found! Run initialization.")
else:
    print("[OK] Memory Subsystem")

# Check some basic imports
try:
    import lancedb
    print("[OK] lancedb installed")
except ImportError:
    print("[ERROR] lancedb not installed. Run: pip install -r requirements.txt")
    has_errors = True

try:
    import datasets
    print("[OK] datasets installed")
except ImportError:
    print("[ERROR] datasets not installed. Run: pip install -r requirements.txt")
    has_errors = True

try:
    import pandas
    print("[OK] pandas installed")
except ImportError:
    print("[ERROR] pandas not installed. Run: pip install -r requirements.txt")
    has_errors = True

print("--- DOCTOR COMPLETE ---")
if has_errors:
    sys.exit(1)
else:
    sys.exit(0)
