#!/usr/bin/env python3
"""Unit tests for vessel black box (issue #12)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".aim_core"))

from blackbox_vault import (  # noqa: E402
    vault_session,
    audit_vault,
    verify_manifest,
    blackbox_dir,
)


class BlackboxVaultTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".aim_core").mkdir()
        (self.root / ".aim_core" / "CONFIG.json").write_text(
            json.dumps(
                {
                    "settings": {
                        "blackbox_enabled": True,
                        "blackbox_on_reincarnate_only": True,
                        "blackbox_key_path": str(self.root / "blackbox.key"),
                    }
                }
            )
        )
        self.sid = "019fbbbb-test-4e2e-8e2e-blackbox0001"
        # path layout .../sid/updates.jsonl for id recovery
        sess = self.root / "sess" / self.sid
        sess.mkdir(parents=True)
        self.src = sess / "updates.jsonl"
        payload = b'{"type":"user","content":"OPERATOR_DIRECTIVE vault test"}\n'
        self.src.write_bytes(payload)

    def tearDown(self):
        self.tmp.cleanup()

    def test_seal_roundtrip_and_verify(self):
        ok = vault_session(
            str(self.src),
            session_id=self.sid,
            vessel_root=str(self.root),
            reason="reincarnate",
        )
        self.assertTrue(ok)
        box = blackbox_dir(str(self.root))
        self.assertTrue((box / f"{self.sid}.enc").is_file())
        man = (box / "manifest.jsonl").read_text(encoding="utf-8")
        self.assertIn(self.sid, man)
        self.assertIn("sha256_plaintext", man)

        plain = audit_vault(self.sid, vessel_root=str(self.root), to_stdout=False)
        self.assertIsNotNone(plain)
        self.assertIn(b"OPERATOR_DIRECTIVE", plain)

        self.assertTrue(
            verify_manifest(
                self.sid, vessel_root=str(self.root), live_path=str(self.src)
            )
        )

    def test_non_reincarnate_reason_skips(self):
        ok = vault_session(
            str(self.src),
            session_id=self.sid,
            vessel_root=str(self.root),
            reason="pulse",
        )
        self.assertFalse(ok)
        box = blackbox_dir(str(self.root))
        self.assertFalse((box / f"{self.sid}.enc").is_file())

    def test_disabled_skips(self):
        (self.root / ".aim_core" / "CONFIG.json").write_text(
            json.dumps({"settings": {"blackbox_enabled": False}})
        )
        ok = vault_session(
            str(self.src),
            session_id=self.sid,
            vessel_root=str(self.root),
            reason="reincarnate",
        )
        self.assertFalse(ok)

    def test_missing_source_nonfatal(self):
        ok = vault_session(
            str(self.root / "nope.jsonl"),
            session_id=self.sid,
            vessel_root=str(self.root),
            reason="reincarnate",
        )
        self.assertFalse(ok)

    def test_key_failure_is_warn_not_fatal(self):
        import blackbox_vault

        def boom(*_a, **_k):
            raise RuntimeError("No recommended backend was available")

        original = blackbox_vault.get_or_create_key
        blackbox_vault.get_or_create_key = boom  # type: ignore
        try:
            ok = vault_session(
                str(self.src),
                session_id=self.sid,
                vessel_root=str(self.root),
                reason="reincarnate",
            )
            self.assertFalse(ok)
        finally:
            blackbox_vault.get_or_create_key = original


if __name__ == "__main__":
    unittest.main()
