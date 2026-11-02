#!/usr/bin/env python3
import glob
import json
import os
import shutil
import sys
from datetime import datetime, timezone

current_dir = os.path.dirname(os.path.abspath(__file__))
aim_root = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.append(current_dir)
if aim_root not in sys.path:
    sys.path.append(aim_root)

from config_utils import CONFIG, AIM_ROOT, PROJECT_ROOT
from plugins.datajack.forensic_utils import get_embedding, chunk_text
from lance_backend import VectorBackend


def verify_embedding_engine():
    test_text = "Establishing foundation knowledge."
    try:
        vec = get_embedding(test_text)
        if vec:
            return True
    except Exception as e:
        print(f"\n[DEBUG] Embedding test failed: {e}", file=sys.stderr)
    print("\n[NOTICE] Semantic Engine Offline (Ollama/Nomic not found).")
    return False


def compute_doc_session_id(file_path, frag_type, *, base_dir=None, project_root=None):
    """Build a collision-free, host-path-free session_id and rel_key from repo-relative path."""
    fp_abs = os.path.abspath(file_path)
    proj_abs = os.path.abspath(project_root or PROJECT_ROOT)
    rel_key = None

    try:
        if os.path.commonpath([fp_abs, proj_abs]) == proj_abs:
            rel_key = os.path.relpath(fp_abs, proj_abs).replace("\\", "/")
    except ValueError:
        rel_key = None

    if not rel_key and base_dir:
        base_abs = os.path.abspath(base_dir)
        try:
            if os.path.commonpath([fp_abs, base_abs]) == base_abs:
                sub_rel = os.path.relpath(fp_abs, base_abs).replace("\\", "/")
                root_label = os.path.basename(base_abs.rstrip("/\\")) or "docs"
                rel_key = f"{root_label}/{sub_rel}" if sub_rel != "." else os.path.basename(fp_abs)
        except ValueError:
            rel_key = None

    if not rel_key:
        rel_key = os.path.basename(fp_abs)

    safe_rel = rel_key.replace("'", "_")
    prefix = "foundation" if frag_type == "foundation_knowledge" else "expert"
    return f"{prefix}-{safe_rel}", safe_rel


def bootstrap_foundation(target_dir=None, *, db_path=None, seed_default_lance=False):
    embeddings_active = False if seed_default_lance else verify_embedding_engine()
    print("\n--- A.I.M. BRAIN BOOTSTRAP ---")

    if seed_default_lance:
        default_dir = db_path or os.path.join(AIM_ROOT, "assets", "default_lance")
        if os.path.exists(default_dir):
            shutil.rmtree(default_dir)
        os.makedirs(default_dir, exist_ok=True)
        backend = VectorBackend(path=default_dir)
    else:
        backend = VectorBackend(path=db_path) if db_path else VectorBackend()

    pending_fragments = []
    new_fragments = 0

    if target_dir:
        print(f"[1/1] Syncing Custom Target Directory: {target_dir}...")
        pattern = os.path.join(target_dir, "**", "*.md")
        seen_custom = set()
        for file_path in sorted(glob.glob(pattern, recursive=True)):
            abs_fp = os.path.abspath(file_path)
            if abs_fp in seen_custom or "memory/archive" in file_path:
                continue
            seen_custom.add(abs_fp)
            new_fragments += index_file(
                backend,
                file_path,
                "expert_knowledge",
                ingest_only=False,
                use_embeddings=embeddings_active,
                collector=pending_fragments,
                base_dir=target_dir,
            )

        if pending_fragments:
            backend.upsert_fragments(
                pending_fragments,
                purge_predicate=lambda row, incoming: row.get("session_id") in incoming,
            )
    else:
        if seed_default_lance:
            foundation_targets = [
                os.path.join(PROJECT_ROOT, "AGENTS.md"),
                os.path.join(AIM_ROOT, "joshua_os_docs", "**", "*.md"),
            ]
        else:
            foundation_targets = [
                os.path.join(PROJECT_ROOT, "AGENTS.md"),
                os.path.join(PROJECT_ROOT, "artifacts", "AUDIT_*.md"),
                os.path.join(PROJECT_ROOT, "memory-wiki", "**", "*.md"),
                os.path.join(AIM_ROOT, "joshua_os_docs", "**", "*.md"),
                os.path.join(AIM_ROOT, "memory-wiki", "**", "*.md"),
            ]

        foundry_dir = os.path.join(AIM_ROOT, "foundry")

        print("[1/2] Syncing Foundation Knowledge...")
        seen_files = set()
        for pattern in foundation_targets:
            for file_path in sorted(glob.glob(pattern, recursive=True)):
                abs_fp = os.path.abspath(file_path)
                if abs_fp in seen_files or "memory/archive" in file_path:
                    continue
                seen_files.add(abs_fp)
                new_fragments += index_file(
                    backend,
                    file_path,
                    "foundation_knowledge",
                    ingest_only=False,
                    use_embeddings=embeddings_active,
                    collector=pending_fragments,
                )

        print("[2/2] Melting down Foundry materials into Engrams...")
        if os.path.exists(foundry_dir):
            for root, _, files in sorted(os.walk(foundry_dir)):
                for file in sorted(files):
                    if file.endswith((".md", ".markdown", ".txt", ".py", ".rs", ".js", ".ts", ".rst")):
                        file_path = os.path.join(root, file)
                        new_fragments += index_file(
                            backend,
                            file_path,
                            "expert_knowledge",
                            ingest_only=True,
                            use_embeddings=embeddings_active,
                            collector=pending_fragments,
                        )

        def _full_refresh_purge(row, incoming):
            if row.get("type") == "foundation_knowledge":
                return True
            sid = str(row.get("session_id") or "")
            if sid in incoming:
                return True
            if sid.startswith("expert-joshua_os/foundry/") or sid.startswith("expert-foundry/"):
                return True
            if sid == "expert-README.md" and row.get("source_db") == "live_session":
                return True
            return False

        if pending_fragments:
            backend.upsert_fragments(pending_fragments, purge_predicate=_full_refresh_purge)

    try:
        table = backend.get_table()
        total_in_db = table.count_rows()
    except Exception:
        total_in_db = 0

    print("\n[SUCCESS] Bootstrap complete.")
    print(f"      -> New Fragments:   {new_fragments}")
    print(f"      -> Total Brain Size: {total_in_db} fragments")


def index_file(backend, file_path, frag_type, ingest_only=False, use_embeddings=True, collector=None, base_dir=None):
    filename = os.path.basename(file_path)
    try:
        fsize = os.path.getsize(file_path)
    except Exception:
        return 0

    if fsize == 0:
        if not ingest_only:
            print(f"  [SKIP] {filename} (Empty file)")
        return 0

    session_id, rel_key = compute_doc_session_id(file_path, frag_type, base_dir=base_dir)
    print(f"  -> {rel_key} ({fsize / 1024:.1f} KB)")
    try:
        with open(file_path, "r", errors="ignore", encoding="utf-8") as f:
            content = f.read()

        chunks = chunk_text(content)
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        fragments = []
        for i, chunk in enumerate(chunks):
            vec = get_embedding(chunk) if use_embeddings else None
            fragments.append({
                "session_id": session_id,
                "type": frag_type,
                "content": chunk,
                "timestamp": now_iso,
                "metadata": json.dumps({"source": rel_key, "filename": filename, "chunk": i, "total": len(chunks)}),
                "source_db": rel_key,
                "vector": vec if vec and len(vec) == 768 else ([0.0] * 768),
            })

        if fragments:
            if collector is not None:
                collector.extend(fragments)
            else:
                backend.upsert_fragments(
                    fragments,
                    purge_predicate=lambda row, incoming: row.get("session_id") in incoming,
                )
        return len(fragments)
    except Exception as e:
        print(f"    [SKIP] {rel_key}: {e}")
        return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="A.I.M. Brain Bootstrap")
    parser.add_argument("--dir", type=str, help="Target directory to ingest into the brain")
    parser.add_argument("--seed-default-lance", action="store_true", help="Rebuild joshua_os/assets/default_lance from universal OS docs")
    args = parser.parse_args()
    bootstrap_foundation(target_dir=args.dir, seed_default_lance=args.seed_default_lance)
