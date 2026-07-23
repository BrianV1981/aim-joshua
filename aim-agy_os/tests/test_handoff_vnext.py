"""Unit + integration tests for handoff vNext three pipelines."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

# aim-agy_os on path
import sys

OS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(OS))
sys.path.insert(0, str(OS / ".aim_core"))

from handoff.adapters.fixture import FixtureAdapter
from handoff.blackbox_cron import run_blackbox_cron
from handoff.handoff_core import run_handoff
from handoff.packet import build_packet, validate_packet
from handoff.models import Turn
from handoff.wiki_batch import run_wiki_batch


FIX = OS / "tests" / "fixtures" / "handoff_vnext"
MARKER = "E2E_HANDOFF_VNEXT_MARKER_7f3a"


class TestPacket(unittest.TestCase):
    def test_build_and_validate(self):
        turns = [
            Turn("user", f"Hello {MARKER} MANDATE: do the thing"),
            Turn("assistant", "OK TODO: finish"),
            Turn("user", "[[KEEP]] never false green"),
        ]
        md, marker = build_packet(
            session_id="s1",
            vessel="aim-grok",
            turns=turns,
            source_path="/tmp/x",
            marker=MARKER,
        )
        self.assertEqual(marker, MARKER)
        self.assertEqual(validate_packet(md), [])
        self.assertIn(MARKER, md)


class TestThreePipelines(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="handoff_vnext_"))
        # minimal vessel shape
        (self.tmp / "aim-agy_os" / ".aim_core").mkdir(parents=True)
        (self.tmp / "aim-agy_os" / "setup.sh").write_text("#!/bin/bash\n")
        # copy fixtures
        shutil.copytree(FIX, self.tmp / "fixtures")
        self.adapter = FixtureAdapter(self.tmp / "fixtures")
        # patch meta cwd to tmp vessel
        for sid_dir in (self.tmp / "fixtures").iterdir():
            if sid_dir.is_dir():
                (sid_dir / "meta.json").write_text(
                    json.dumps({"cwd": str(self.tmp)}) + "\n"
                )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_handoff_ok(self):
        res = run_handoff(
            adapter=self.adapter,
            session_id="e2e-vnext-session-alpha",
            cwd=self.tmp,
            root=self.tmp,
            vessel="test-vessel",
            marker=MARKER,
        )
        self.assertEqual(res.status, "ok", res.errors)
        cur = Path(res.paths["continuity"])
        self.assertTrue(cur.is_file())
        self.assertIn(MARKER, cur.read_text())

    def test_handoff_empty_fails(self):
        empty = self.tmp / "fixtures" / "empty-sess"
        empty.mkdir()
        (empty / "updates.jsonl").write_text("{}\n")
        (empty / "meta.json").write_text(json.dumps({"cwd": str(self.tmp)}))
        res = run_handoff(
            adapter=self.adapter,
            session_id="empty-sess",
            cwd=self.tmp,
            root=self.tmp,
            marker=MARKER,
        )
        self.assertIn(res.status, ("empty", "error"))
        self.assertNotEqual(res.code, "OK")

    def test_wiki_batch_fr_embed(self):
        res = run_wiki_batch(
            adapter=self.adapter,
            root=self.tmp,
            project_root=self.tmp,
            since_mtime=0.0,
            limit=10,
        )
        self.assertIn(res.status, ("ok", "partial"), res.errors)
        fr = self.tmp / "continuity" / "flight_records" / "e2e-vnext-session-alpha.md"
        self.assertTrue(fr.is_file(), "FR missing")
        self.assertIn("Operator", fr.read_text())
        pages = list((self.tmp / "aim-agy_os" / "memory-wiki" / "pages").glob("source-*.md"))
        self.assertTrue(pages, "wiki pages missing")
        db = self.tmp / "aim-agy_os" / "memory_lance" / "handoff_vnext"
        jsonls = list(db.glob("*.jsonl"))
        self.assertTrue(jsonls, "embed jsonl missing")

    def test_blackbox_cron(self):
        res = run_blackbox_cron(
            adapter=self.adapter, root=self.tmp, since_mtime=0.0, limit=10
        )
        self.assertIn(res.status, ("ok", "partial"), res.errors)
        box = self.tmp / "archive" / ".raw_jsonl_blackbox"
        encs = list(box.glob("*.enc"))
        self.assertTrue(encs, "no sealed blobs")
        man = box / "manifest.jsonl"
        self.assertTrue(man.is_file())


if __name__ == "__main__":
    unittest.main()
