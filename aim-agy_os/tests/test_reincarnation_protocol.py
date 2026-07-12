#!/usr/bin/env python3
"""TDD: Verify Ephemeral Context Injection — no continuity folder, no manual tmux relay."""
import os, sys

AIM_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_tests():
    failures = 0

    # Test 1: aim_reincarnate.py does not reference REINCARNATION_CONNECT.md
    print("Test 1: aim_reincarnate.py excludes REINCARNATION_CONNECT.md")
    with open(os.path.join(AIM_ROOT, "aim_core", "aim_reincarnate.py")) as f:
        content = f.read()
    if "REINCARNATION_CONNECT.md" not in content:
        print("  PASS")
    else:
        print("  FAIL: REINCARNATION_CONNECT.md still referenced in aim_reincarnate.py")
        failures += 1

    # Test 2: AGENTS.md uses Ephemeral Context Injection
    print("Test 2: AGENTS.md uses Ephemeral Context Injection (auto-inject, no continuity folder)")
    with open(os.path.join(AIM_ROOT, "AGENTS.md")) as f:
        content = f.read()
    if "inject your gameplan directly into the new agent's wake-up prompt" in content:
        print("  PASS")
    else:
        print("  FAIL: Missing auto-injection pattern")
        failures += 1
    if "continuity/" in content:
        print("  FAIL: AGENTS.md still references continuity/ folder")
        failures += 1
    else:
        print("  PASS (no continuity/ references)")

    # Test 3: Handoff references wake-up prompt, not file reading
    print("Test 3: AGENTS.md handoff references wake-up prompt injection")
    if "There is no continuity folder for you to read" in content:
        print("  PASS")
    else:
        print("  FAIL: Missing 'no continuity folder' clause")
        failures += 1
    if "Ephemeral Context Injection" in content:
        print("  PASS")
    else:
        print("  FAIL: Missing 'Ephemeral Context Injection'")
        failures += 1

    print()
    print(f"Passed: {5 - failures}/5")
    return failures

if __name__ == "__main__":
    sys.exit(run_tests())
