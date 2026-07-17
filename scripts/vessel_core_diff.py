#!/usr/bin/env python3
"""
Four-vessel A.I.M. engine core diff.

Compares Python modules across:
  aim-agy      →  aim-agy_os/.aim_core
  aim-grok     →  aim-agy_os/.aim_core
  aim-opencode →  nested aim-agy_os/.aim_core (or legacy flat aim_core/)
  aim-codex    →  aim-agy_os/.aim_core

Default roots (override with env or flags):
  AIM_AGY_ROOT, AIM_GROK_ROOT, AIM_OPENCODE_ROOT, AIM_CODEX_ROOT

Exit codes:
  0  — all compared shared modules identical (rare) OR --report-only
  1  — drift detected among shared modules
  2  — usage / missing path error

Examples:
  python3 scripts/vessel_core_diff.py --report-only
  python3 scripts/vessel_core_diff.py --pair agy,codex
  python3 scripts/vessel_core_diff.py --pair agy,grok --json
  python3 scripts/vessel_core_diff.py --lockstep-checklist
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


DEFAULTS = {
    "agy": Path(os.environ.get("AIM_AGY_ROOT", "/home/kingb/aim-agy")),
    "grok": Path(os.environ.get("AIM_GROK_ROOT", "/home/kingb/aim-grok")),
    "opencode": Path(
        os.environ.get("AIM_OPENCODE_ROOT", "/home/kingb/aim-opencode")
    ),
    "codex": Path(os.environ.get("AIM_CODEX_ROOT", "/home/kingb/aim-codex")),
}

# Relative path from vessel root → engine core
CORE_REL = {
    "agy": Path("aim-agy_os/.aim_core"),
    "grok": Path("aim-agy_os/.aim_core"),
    "opencode": Path("aim_core"),  # migrate → aim-agy_os/.aim_core
    "codex": Path("aim-agy_os/.aim_core"),
}


def _resolve_opencode_core(root: Path) -> Path:
    """Prefer nested soul layout; fall back to legacy flat aim_core/."""
    nested = root / "aim-agy_os" / ".aim_core"
    flat = root / "aim_core"
    if nested.is_dir():
        return nested
    return flat


SKIP_DIR_PARTS = {
    "__pycache__",
    "temp",
    "workspace",
    ".git",
    "venv",
    "memory",
    "memory_lance",
    "archive",
}

# Known intentional vessel overlays (not “bugs” — still reported, tagged)
KNOWN_OVERLAYS = {
    "grok": {
        "vessel_paths.py",
        "wiki_compiler.py",
        "agent_session_names.py",
        "reincarnation/session_naming.py",
        "session_naming.py",
        "reincarnation/teleport_engine.py",
        "handoff_pulse_generator.py",
    },
    "opencode": {
        "aim_crash.py",
        "daemon.py",
        "session_bridge.py",
        "aim_opencode_update.py",
        "forensic_utils.py",
        "reincarnation/teleport_engine.py",
        "handoff_pulse_generator.py",
        "session_naming.py",
    },
    "codex": {
        "vessel_paths.py",
        "session_naming.py",
        "reincarnation/session_naming.py",
        "reincarnation/teleport_engine.py",
        "handoff_pulse_generator.py",
    },
    "agy": set(),
}

# Modules that should exist on all vessels for lockstep (health bar)
LOCKSTEP_REQUIRED = [
    "aim_cli.py",
    "aim_reincarnate.py",
    "wiki_tools.py",
    "config_utils.py",
    "lance_backend.py",
    "extract_signal.py",
    "handoff_pulse_generator.py",
    "session_porter.py",
    "blackbox_vault.py",
]


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def collect_py_modules(core: Path) -> dict[str, Path]:
    """Map relative posix path → absolute Path for *.py under core."""
    out: dict[str, Path] = {}
    if not core.is_dir():
        return out
    core = core.resolve()
    for p in core.rglob("*.py"):
        try:
            rel_parts = p.resolve().relative_to(core).parts
        except ValueError:
            continue
        if any(part in SKIP_DIR_PARTS for part in rel_parts[:-1]):
            continue
        rel = Path(*rel_parts).as_posix() if rel_parts else p.name
        out[rel] = p
    return out


def resolve_core(vessel: str, root: Path) -> Path:
    if vessel == "opencode":
        return _resolve_opencode_core(root).resolve()
    return (root / CORE_REL[vessel]).resolve()


def pair_diff(
    name_a: str,
    mods_a: dict[str, Path],
    name_b: str,
    mods_b: dict[str, Path],
) -> dict:
    shared = sorted(set(mods_a) & set(mods_b))
    only_a = sorted(set(mods_a) - set(mods_b))
    only_b = sorted(set(mods_b) - set(mods_a))
    identical: list[str] = []
    differ: list[dict] = []
    for rel in shared:
        da, db = file_digest(mods_a[rel]), file_digest(mods_b[rel])
        if da == db:
            identical.append(rel)
        else:
            differ.append(
                {
                    "path": rel,
                    f"{name_a}_sha": da,
                    f"{name_b}_sha": db,
                    "overlay_hint": _overlay_hint(name_a, name_b, rel),
                }
            )
    return {
        "pair": f"{name_a}↔{name_b}",
        "identical": len(identical),
        "differ": differ,
        "differ_count": len(differ),
        "only_a": only_a,
        "only_b": only_b,
        "only_a_count": len(only_a),
        "only_b_count": len(only_b),
        "identical_list": identical,
    }


def _overlay_hint(a: str, b: str, rel: str) -> str:
    tags = []
    for v in (a, b):
        overlays = KNOWN_OVERLAYS.get(v, set())
        if rel in overlays or any(rel.endswith(x) for x in overlays):
            tags.append(f"known-{v}-overlay")
    return ",".join(tags) if tags else ""


def lockstep_checklist(modules: dict[str, dict[str, Path]]) -> list[dict]:
    rows = []
    for rel in LOCKSTEP_REQUIRED:
        row = {"module": rel}
        for v, mods in modules.items():
            row[v] = "present" if rel in mods else "MISSING"
        digests = {}
        for v, mods in modules.items():
            if rel in mods:
                digests[v] = file_digest(mods[rel])
        row["in_sync"] = len(set(digests.values())) <= 1 and len(digests) == len(
            modules
        )
        row["digests"] = digests
        rows.append(row)
    return rows


def read_source_pin(root: Path) -> str:
    pin = root / "SOURCE.md"
    if not pin.is_file():
        return "(no SOURCE.md)"
    text = pin.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if "Commit" in line and "`" in line:
            return line.strip()
    return text[:200]


def print_human(report: dict) -> None:
    print("=== A.I.M. VESSEL CORE DIFF (4 pillars) ===")
    print(f"Grok SOURCE pin: {report.get('source_pin_grok', '')}")
    print(f"Codex SOURCE pin: {report.get('source_pin_codex', '')}")
    print()
    for v, info in report["vessels"].items():
        status = "OK" if info["exists"] else "MISSING"
        print(f"  [{status}] {v:8} root={info['root']}")
        print(f"           core={info['core']}  modules={info['module_count']}")
    print()
    for p in report["pairs"]:
        print(f"--- {p['pair']} ---")
        print(
            f"  identical={p['identical']}  differ={p['differ_count']}  "
            f"only_{p['pair'].split('↔')[0]}={p['only_a_count']}  "
            f"only_{p['pair'].split('↔')[1]}={p['only_b_count']}"
        )
        if p["differ"]:
            print("  DIFFER:")
            for d in p["differ"][:50]:
                hint = f"  ({d['overlay_hint']})" if d.get("overlay_hint") else ""
                print(f"    ~ {d['path']}{hint}")
            if p["differ_count"] > 50:
                print(f"    ... +{p['differ_count'] - 50} more")
        a_name, b_name = p["pair"].split("↔")
        if p["only_a"][:20]:
            print(f"  ONLY {a_name} (sample):")
            for x in p["only_a"][:20]:
                print(f"    + {x}")
            if p["only_a_count"] > 20:
                print(f"    ... +{p['only_a_count'] - 20} more")
        if p["only_b"][:20]:
            print(f"  ONLY {b_name} (sample):")
            for x in p["only_b"][:20]:
                print(f"    + {x}")
            if p["only_b_count"] > 20:
                print(f"    ... +{p['only_b_count'] - 20} more")
        print()

    if report.get("lockstep"):
        print("--- LOCKSTEP REQUIRED MODULES ---")
        for row in report["lockstep"]:
            flag = "SYNC" if row["in_sync"] else "DRIFT"
            parts = " ".join(
                f"{k}={v}" for k, v in row.items() if k in DEFAULTS
            )
            print(f"  [{flag}] {row['module']:28} {parts}")
        print()

    print("--- ORCHESTRATION HINTS ---")
    for line in report.get("orchestration_hints", []):
        print(f"  • {line}")
    print()
    print(f"Drift exit signal: {'YES' if report['has_drift'] else 'NO'}")


def build_orchestration_hints(report: dict) -> list[str]:
    hints = [
        "Soul = aim-agy. Sync agy→grok/codex via SYNC_FROM_AIM_AGY.md; pin SOURCE.md.",
        "Four pillars: agy · grok · opencode · codex. Host overlays only for CLI spawn/paths.",
        "Host-agnostic features: implement on agy first, then sync vessels.",
        "extract_signal should include codex_rollout + opencode_session on all vessels.",
    ]
    lock = report.get("lockstep") or []
    for vessel in ("opencode", "codex", "grok"):
        missing = [r["module"] for r in lock if r.get(vessel) == "MISSING"]
        if missing:
            hints.append(
                f"aim-{vessel} MISSING lockstep modules: "
                + ", ".join(missing)
                + " — port from agy."
            )
    for p in report.get("pairs", []):
        if p["pair"] == "agy↔codex" and p["differ_count"] > 0:
            non_overlay = [d for d in p["differ"] if not d.get("overlay_hint")]
            if non_overlay:
                hints.append(
                    "agy↔codex unexpected diffs: "
                    + ", ".join(d["path"] for d in non_overlay[:8])
                )
            else:
                hints.append(
                    f"agy↔codex: {p['differ_count']} known-overlay diffs only — OK"
                )
        if p["pair"] == "agy↔opencode" and p["differ_count"] > 20:
            hints.append(
                f"agy↔opencode has {p['differ_count']} differing shared modules — "
                "schedule deliberate re-sync sprint, not drive-by edits."
            )
        if p["pair"] == "agy↔grok" and p["differ_count"] > 0:
            non_overlay = [d for d in p["differ"] if not d.get("overlay_hint")]
            if non_overlay:
                hints.append(
                    "agy↔grok unexpected diffs (not tagged overlay): "
                    + ", ".join(d["path"] for d in non_overlay[:8])
                )
    return hints


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agy", type=Path, default=DEFAULTS["agy"])
    parser.add_argument("--grok", type=Path, default=DEFAULTS["grok"])
    parser.add_argument("--opencode", type=Path, default=DEFAULTS["opencode"])
    parser.add_argument("--codex", type=Path, default=DEFAULTS["codex"])
    parser.add_argument(
        "--pair",
        action="append",
        default=[],
        help="Limit pairs, e.g. agy,codex (repeatable). Default: all pairs.",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--lockstep-checklist", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--list-identical", action="store_true")
    args = parser.parse_args(argv)

    roots = {
        "agy": args.agy.expanduser().resolve(),
        "grok": args.grok.expanduser().resolve(),
        "opencode": args.opencode.expanduser().resolve(),
        "codex": args.codex.expanduser().resolve(),
    }

    vessels_info = {}
    modules: dict[str, dict[str, Path]] = {}
    for name, root in roots.items():
        core = resolve_core(name, root)
        mods = collect_py_modules(core) if core.is_dir() else {}
        modules[name] = mods
        vessels_info[name] = {
            "root": str(root),
            "core": str(core),
            "exists": core.is_dir(),
            "module_count": len(mods),
        }
        if not core.is_dir():
            print(f"[ERROR] Missing core for {name}: {core}", file=sys.stderr)

    if not any(v["exists"] for v in vessels_info.values()):
        return 2

    names = list(roots.keys())
    default_pairs = [
        (names[i], names[j])
        for i in range(len(names))
        for j in range(i + 1, len(names))
    ]
    # Prefer soul-centric pairs first for readability
    preferred = [
        ("agy", "grok"),
        ("agy", "opencode"),
        ("agy", "codex"),
        ("grok", "opencode"),
        ("grok", "codex"),
        ("opencode", "codex"),
    ]
    default_pairs = [p for p in preferred if p in default_pairs or True]
    # keep preferred order only
    default_pairs = preferred

    pairs_req: list[tuple[str, str]] = []
    if args.pair:
        for spec in args.pair:
            parts = [p.strip() for p in spec.replace("↔", ",").split(",")]
            if len(parts) != 2 or parts[0] not in roots or parts[1] not in roots:
                print(f"[ERROR] bad --pair {spec!r}", file=sys.stderr)
                return 2
            pairs_req.append((parts[0], parts[1]))
    else:
        pairs_req = default_pairs

    pair_reports = []
    has_drift = False
    for a, b in pairs_req:
        if not vessels_info[a]["exists"] or not vessels_info[b]["exists"]:
            has_drift = True
            pair_reports.append(
                {
                    "pair": f"{a}↔{b}",
                    "identical": 0,
                    "differ": [],
                    "differ_count": 0,
                    "only_a": [],
                    "only_b": [],
                    "only_a_count": 0,
                    "only_b_count": 0,
                    "error": "missing core",
                }
            )
            continue
        pr = pair_diff(a, modules[a], b, modules[b])
        if not args.list_identical:
            pr.pop("identical_list", None)
        if pr["differ_count"]:
            has_drift = True
        pair_reports.append(pr)

    report: dict = {
        "source_pin_grok": read_source_pin(roots["grok"]),
        "source_pin_codex": read_source_pin(roots["codex"]),
        "vessels": vessels_info,
        "pairs": pair_reports,
        "has_drift": has_drift,
    }

    present = {k: v for k, v in modules.items() if vessels_info[k]["exists"]}
    report["lockstep"] = lockstep_checklist(present)
    if any(not r["in_sync"] for r in report["lockstep"]):
        report["has_drift"] = True

    report["orchestration_hints"] = build_orchestration_hints(report)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_human(report)

    if args.report_only:
        return 0
    return 1 if report["has_drift"] else 0


if __name__ == "__main__":
    sys.exit(main())
