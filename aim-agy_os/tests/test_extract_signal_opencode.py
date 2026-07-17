#!/usr/bin/env python3
"""OpenCode session JSON extract (single-file messages[])."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".aim_core"))
from extract_signal import (  # noqa: E402
    conversational_turn_count,
    detect_jsonl_kind,
    extract_signal,
)


class OpencodeExtractTests(unittest.TestCase):
    def test_session_blob_extract(self):
        payload = {
            "sessionId": "oc-test-1",
            "kind": "operator_e2e",
            "messages": [
                {"type": "user", "content": [{"text": "OPERATOR_DIRECTIVE_1: COPPER_MOTH"}]},
                {"type": "assistant", "content": [{"text": "ack"}]},
                {"type": "user", "content": [{"text": "reincarnate now"}]},
                {"type": "assistant", "content": [{"text": "handoff"}]},
            ],
        }
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "session-e2e-oc-test.json"
            p.write_text(json.dumps(payload))
            self.assertEqual(detect_jsonl_kind(str(p)), "opencode_session")
            sig = extract_signal(str(p))
            self.assertIsInstance(sig, list)
            self.assertGreaterEqual(conversational_turn_count(sig), 4)
            blob = " ".join(t.get("text") or "" for t in sig)
            self.assertIn("COPPER_MOTH", blob)


if __name__ == "__main__":
    unittest.main()
