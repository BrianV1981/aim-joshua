"""Expanded E2E / chaos tests for Handoff vNext three pipelines."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

OS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(OS))
sys.path.insert(0, str(OS / ".aim_core"))

from handoff.adapters.fixture import FixtureAdapter
from handoff.blackbox_cron import run_blackbox_cron
from handoff.handoff_core import run_handoff
from handoff.models import Turn
from handoff.packet import build_packet, validate_packet
from handoff.wiki_batch import run_wiki_batch

FIX_SRC = OS / "tests" / "fixtures" / "handoff_vnext"
MARKER = "E2E_HANDOFF_VNEXT_MARKER_7f3a"
PY = OS / "venv" / "bin" / "python3"
if not PY.is_file():
    PY = Path(sys.executable)


def _write_session(root: Path, sid: str, turns: list, cwd: str) -> Path:
    d = root / sid
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(json.dumps({"cwd": cwd}) + "\n", encoding="utf-8")
    lines = []
    for role, text in turns:
        kind = "user_message_chunk" if role == "user" else "agent_message_chunk"
        lines.append(
            json.dumps(
                {
                    "timestamp": time.time(),
                    "method": "session/update",
                    "params": {
                        "sessionId": sid,
                        "update": {
                            "sessionUpdate": kind,
                            "content": {"type": "text", "text": text},
                        },
                    },
                }
            )
        )
    (d / "updates.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return d


class VesselE2EBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hvnext_e2e_"))
        (self.tmp / "aim-agy_os" / ".aim_core").mkdir(parents=True)
        (self.tmp / "aim-agy_os" / "setup.sh").write_text("#!/bin/bash\n")
        self.fix = self.tmp / "fixtures"
        self.fix.mkdir()
        # seed alpha-like session
        _write_session(
            self.fix,
            "e2e-alpha",
            [
                ("user", f"Wake. {MARKER} MANDATE: pipeline A."),
                ("assistant", "Ack. TODO: run tests."),
                ("user", "[[KEEP]] no agent spin-up for handoff"),
                ("assistant", "Understood."),
            ],
            str(self.tmp),
        )
        self.adapter = FixtureAdapter(self.fix)
        os.environ["AIM_BLACKBOX_ALLOW_CRON"] = "1"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestHandoffE2E(VesselE2EBase):
    def test_happy_path_packet_and_result_json(self):
        res = run_handoff(
            adapter=self.adapter,
            session_id="e2e-alpha",
            cwd=self.tmp,
            root=self.tmp,
            vessel="e2e-vessel",
            marker=MARKER,
        )
        self.assertEqual(res.status, "ok", res.to_dict())
        self.assertEqual(res.code, "OK")
        for g in ("G0", "G1", "G2", "G3", "G4", "G5"):
            self.assertTrue(res.gates.get(g), f"gate {g} false: {res.gates}")
        cur = Path(res.paths["continuity"])
        body = cur.read_text(encoding="utf-8")
        self.assertIn(MARKER, body)
        self.assertIn("Schema-Version: 1", body)
        self.assertIn("## Do Not Forget", body)
        result = self.tmp / "continuity" / "handoff_result.json"
        self.assertTrue(result.is_file())
        data = json.loads(result.read_text())
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["session_id"], "e2e-alpha")

    def test_wrong_session_id_fails_loud(self):
        res = run_handoff(
            adapter=self.adapter,
            session_id="does-not-exist-uuid",
            cwd=self.tmp,
            root=self.tmp,
            marker=MARKER,
        )
        self.assertEqual(res.status, "error")
        self.assertEqual(res.code, "RESOLVE_FAIL")
        self.assertFalse(res.gates.get("G0"))

    def test_empty_session_no_false_success(self):
        _write_session(self.fix, "empty-sess", [], str(self.tmp))
        # empty updates file
        (self.fix / "empty-sess" / "updates.jsonl").write_text("{}\n")
        res = run_handoff(
            adapter=self.adapter,
            session_id="empty-sess",
            cwd=self.tmp,
            root=self.tmp,
            marker=MARKER,
        )
        self.assertIn(res.status, ("empty", "error"))
        self.assertNotEqual(res.code, "OK")
        # must not claim SUCCESS
        self.assertNotEqual(res.status, "ok")

    def test_double_handoff_updates_current_keeps_history(self):
        run_handoff(
            adapter=self.adapter,
            session_id="e2e-alpha",
            cwd=self.tmp,
            root=self.tmp,
            marker=MARKER,
        )
        # second user turn appended
        path = self.fix / "e2e-alpha" / "updates.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": time.time(),
                        "method": "session/update",
                        "params": {
                            "sessionId": "e2e-alpha",
                            "update": {
                                "sessionUpdate": "user_message_chunk",
                                "content": {
                                    "type": "text",
                                    "text": f"Second pass {MARKER} KEEP going",
                                },
                            },
                        },
                    }
                )
                + "\n"
            )
        res2 = run_handoff(
            adapter=self.adapter,
            session_id="e2e-alpha",
            cwd=self.tmp,
            root=self.tmp,
            marker=MARKER,
        )
        self.assertEqual(res2.status, "ok")
        cur = Path(res2.paths["continuity"]).read_text()
        self.assertIn("Second pass", cur)
        hist = self.tmp / "continuity" / "history" / "e2e-alpha.md"
        self.assertTrue(hist.is_file())

    def test_marker_must_appear_in_self_check(self):
        res = run_handoff(
            adapter=self.adapter,
            session_id="e2e-alpha",
            cwd=self.tmp,
            root=self.tmp,
            marker="CUSTOM_MARKER_XYZ",
        )
        self.assertEqual(res.status, "ok")
        body = Path(res.paths["continuity"]).read_text()
        self.assertIn("- marker: CUSTOM_MARKER_XYZ", body)


class TestWikiBatchE2E(VesselE2EBase):
    def test_fr_then_wiki_then_db(self):
        res = run_wiki_batch(
            adapter=self.adapter,
            root=self.tmp,
            project_root=self.tmp,
            since_mtime=0.0,
            limit=10,
        )
        self.assertIn(res.status, ("ok", "partial"), res.to_dict())
        fr = self.tmp / "continuity" / "flight_records" / "e2e-alpha.md"
        self.assertTrue(fr.is_file())
        fr_text = fr.read_text()
        self.assertIn("Operator", fr_text)
        self.assertIn(MARKER, fr_text)
        pages = list((self.tmp / "aim-agy_os" / "memory-wiki" / "pages").glob("source-*.md"))
        self.assertTrue(pages)
        page_text = pages[0].read_text()
        self.assertIn("e2e-alpha", page_text)
        self.assertIn("Flight record", page_text)
        dbj = self.tmp / "aim-agy_os" / "memory_lance" / "handoff_vnext" / "e2e-alpha.jsonl"
        self.assertTrue(dbj.is_file())
        rows = [json.loads(l) for l in dbj.read_text().splitlines() if l.strip()]
        self.assertGreaterEqual(len(rows), 1)
        self.assertEqual(rows[0]["session_id"], "e2e-alpha")

    def test_watermark_second_run_empty_or_ok_no_dup_fail(self):
        r1 = run_wiki_batch(
            adapter=self.adapter,
            root=self.tmp,
            project_root=self.tmp,
            since_mtime=0.0,
        )
        self.assertIn(r1.status, ("ok", "partial"))
        # second run uses watermark → no sessions
        r2 = run_wiki_batch(
            adapter=self.adapter,
            root=self.tmp,
            project_root=self.tmp,
            since_mtime=None,  # load watermark
        )
        self.assertIn(r2.status, ("empty", "ok", "partial"))

    def test_project_root_isolation(self):
        other = self.tmp / "other_project"
        other.mkdir()
        _write_session(
            self.fix,
            "other-root-sess",
            [
                ("user", "Wrong project MUST NOT land in main vessel wiki"),
                ("assistant", "ok"),
            ],
            str(other),
        )
        res = run_wiki_batch(
            adapter=self.adapter,
            root=self.tmp,
            project_root=self.tmp,
            since_mtime=0.0,
        )
        self.assertIn(res.status, ("ok", "partial", "empty"))
        # pages should not be only other-root if alpha processed
        pages = list((self.tmp / "aim-agy_os" / "memory-wiki" / "pages").glob("source-*.md"))
        for p in pages:
            text = p.read_text()
            if "other-root-sess" in text:
                # if listed, cwd in page should not claim self.tmp as only root wrongly
                # isolation: other session cwd is other project — should not appear when filtering by project_root
                self.fail(f"other project session leaked into vessel wiki: {p}")


class TestBlackboxE2E(VesselE2EBase):
    def test_seal_every_session(self):
        res = run_blackbox_cron(
            adapter=self.adapter, root=self.tmp, since_mtime=0.0, limit=20
        )
        self.assertIn(res.status, ("ok", "partial"), res.to_dict())
        box = self.tmp / "archive" / ".raw_jsonl_blackbox"
        enc = box / "e2e-alpha.enc"
        self.assertTrue(enc.is_file(), f"missing {enc}")
        man = box / "manifest.jsonl"
        self.assertTrue(man.is_file())
        lines = [json.loads(l) for l in man.read_text().splitlines() if l.strip()]
        sids = {x.get("session_id") for x in lines}
        self.assertIn("e2e-alpha", sids)

    def test_seal_idempotent_same_hash(self):
        r1 = run_blackbox_cron(adapter=self.adapter, root=self.tmp, since_mtime=0.0)
        r2 = run_blackbox_cron(adapter=self.adapter, root=self.tmp, since_mtime=0.0)
        self.assertIn(r1.status, ("ok", "partial"))
        self.assertIn(r2.status, ("ok", "partial"))
        # still one blob
        encs = list((self.tmp / "archive" / ".raw_jsonl_blackbox").glob("e2e-alpha.enc"))
        self.assertEqual(len(encs), 1)


class TestFullStackE2E(VesselE2EBase):
    def test_all_three_in_order(self):
        h = run_handoff(
            adapter=self.adapter,
            session_id="e2e-alpha",
            cwd=self.tmp,
            root=self.tmp,
            marker=MARKER,
        )
        b = run_blackbox_cron(adapter=self.adapter, root=self.tmp, since_mtime=0.0)
        w = run_wiki_batch(
            adapter=self.adapter,
            root=self.tmp,
            project_root=self.tmp,
            since_mtime=0.0,
        )
        self.assertEqual(h.status, "ok", h.to_dict())
        self.assertIn(b.status, ("ok", "partial"), b.to_dict())
        self.assertIn(w.status, ("ok", "partial"), w.to_dict())
        # cross-check artifacts
        self.assertIn(MARKER, Path(h.paths["continuity"]).read_text())
        self.assertTrue((self.tmp / "archive" / ".raw_jsonl_blackbox" / "e2e-alpha.enc").is_file())
        self.assertTrue(
            (self.tmp / "continuity" / "flight_records" / "e2e-alpha.md").is_file()
        )
        self.assertTrue(
            (self.tmp / "aim-agy_os" / "memory_lance" / "handoff_vnext" / "e2e-alpha.jsonl").is_file()
        )

    def test_cli_e2e_staged_exit_0(self):
        # use package fixtures against real vessel root is heavy; run module e2e on self.tmp
        # plant into FIX_SRC style under tmp and invoke cli
        env = os.environ.copy()
        env["PYTHONPATH"] = str(OS) + os.pathsep + str(OS / ".aim_core")
        env["AIM_BLACKBOX_ALLOW_CRON"] = "1"
        # copy seed to look like standard fixture root
        fr = self.tmp / "staged"
        shutil.copytree(self.fix, fr)
        proc = subprocess.run(
            [
                str(PY),
                "-m",
                "handoff.cli",
                "e2e-staged",
                "--adapter",
                "fixture",
                "--fixture-root",
                str(fr),
                "--vessel-root",
                str(self.tmp),
                "--marker",
                MARKER,
            ],
            cwd=str(self.tmp),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        start = proc.stdout.rfind("{")
        self.assertGreaterEqual(start, 0, proc.stdout)
        data = json.loads(proc.stdout[start:])
        self.assertTrue(data.get("ok"), data)


class TestPacketChaos(unittest.TestCase):
    def test_validate_rejects_missing_sections(self):
        bad = "# Continuity Packet\nSchema-Version: 1\nTurn-Count: 1\n"
        errs = validate_packet(bad)
        self.assertTrue(errs)

    def test_build_includes_keep_lines(self):
        turns = [
            Turn("user", "[[KEEP]] secret constraint"),
            Turn("assistant", "ok"),
        ]
        md, _ = build_packet(
            session_id="s", vessel="v", turns=turns, source_path="/x", marker="m"
        )
        self.assertIn("secret constraint", md)


class TestMultiSessionBatch(VesselE2EBase):
    def test_batch_processes_multiple_sessions(self):
        for i in range(3):
            _write_session(
                self.fix,
                f"batch-sess-{i}",
                [
                    ("user", f"Session {i} {MARKER}"),
                    ("assistant", f"Reply {i}"),
                ],
                str(self.tmp),
            )
        res = run_wiki_batch(
            adapter=self.adapter,
            root=self.tmp,
            project_root=self.tmp,
            since_mtime=0.0,
            limit=20,
        )
        self.assertEqual(res.status, "ok", res.to_dict())
        self.assertGreaterEqual(res.turn_count, 3)  # processed count
        frs = list((self.tmp / "continuity" / "flight_records").glob("batch-sess-*.md"))
        self.assertGreaterEqual(len(frs), 3)


if __name__ == "__main__":
    unittest.main()
