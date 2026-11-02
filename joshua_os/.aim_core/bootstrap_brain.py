#!/usr/bin/env python3
from datetime import datetime, timezone
import glob
import hashlib
import json
import os
import shutil
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
aim_root = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.append(current_dir)
if aim_root not in sys.path:
    sys.path.append(aim_root)

from config_utils import AIM_ROOT, CONFIG, PROJECT_ROOT
from lance_backend import VectorBackend, list_lance_tables
from plugins.datajack.forensic_utils import chunk_text, get_embedding


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


def _is_nonzero_vector(vec) -> bool:
    if not vec or len(vec) != 768:
        return False
    return any(float(v) != 0.0 for v in vec)


def _load_existing_vector_map(backend) -> dict:
    """
    Build a lookup of existing non-zero 768-dim vectors keyed by `(session_id, sha256)`
    and `(session_id, content)` so unchanged chunks skip redundant Ollama HTTP calls
    and offline `aim index` runs never overwrite real embeddings with zero vectors (Issue #130).
    """
    cache = {}
    try:
        db = getattr(backend, "db", None)
        table_name = getattr(backend, "table_name", "fragments")
        if db is None or table_name not in list_lance_tables(db):
            return cache
        rows = db.open_table(table_name).to_arrow().to_pylist()
    except Exception:
        return cache

    for row in rows:
        vec = row.get("vector")
        if not _is_nonzero_vector(vec):
            continue
        sid = str(row.get("session_id") or "")
        content = str(row.get("content") or "")
        vec_f = [float(x) for x in vec]
        if sid and content:
            chunk_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
            cache[(sid, chunk_sha)] = vec_f
            cache[(sid, content)] = vec_f
        try:
            meta = json.loads(row.get("metadata") or "{}")
            if isinstance(meta, dict) and meta.get("sha256") and sid:
                cache[(sid, str(meta["sha256"]))] = vec_f
        except Exception:
            pass
    return cache


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

    prefix = "foundation" if frag_type == "foundation_knowledge" else "expert"
    return f"{prefix}-{rel_key}", rel_key


def bootstrap_foundation(target_dir=None, *, db_path=None, seed_default_lance=False):
    embeddings_active = False if seed_default_lance else verify_embedding_engine()
    print("\n--- A.I.M. BRAIN BOOTSTRAP ---")

    if seed_default_lance:
        default_dir = db_path or os.path.join(AIM_ROOT, "assets", "default_lance")
        if os.path.exists(default_dir):
            shutil.rmtree(default_dir)
        os.makedirs(default_dir, exist_ok=True)
        backend = VectorBackend(path=default_dir)
        existing_vectors = {}
    else:
        backend = VectorBackend(path=db_path) if db_path else VectorBackend()
        existing_vectors = _load_existing_vector_map(backend)

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
                existing_vectors=existing_vectors,
            )

        if pending_fragments:
            backend.upsert_fragments(
                pending_fragments,
                purge_predicate=lambda row, incoming: row.get("session_id") in incoming,
                compact_immediate=seed_default_lance,
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
                    existing_vectors=existing_vectors,
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
                            existing_vectors=existing_vectors,
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
            backend.upsert_fragments(
                pending_fragments,
                purge_predicate=_full_refresh_purge,
                compact_immediate=seed_default_lance,
            )

    try:
        table = backend.get_table()
        total_in_db = table.count_rows()
    except Exception:
        total_in_db = 0

    if seed_default_lance:
        lock_path = os.path.join(backend.path, ".lance.lock")
        if os.path.exists(lock_path):
            try:
                os.unlink(lock_path)
            except OSError:
                pass

    print("\n[SUCCESS] Bootstrap complete.")
    print(f"      -> New Fragments:   {new_fragments}")
    print(f"      -> Total Brain Size: {total_in_db} fragments")


def index_file(
    backend,
    file_path,
    frag_type,
    ingest_only=False,
    use_embeddings=True,
    collector=None,
    base_dir=None,
    existing_vectors=None,
):
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
    if existing_vectors is None:
        existing_vectors = _load_existing_vector_map(backend)

    try:
        with open(file_path, "r", errors="ignore", encoding="utf-8") as f:
            content = f.read()

        chunks = chunk_text(content)
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        fragments = []
        for i, chunk in enumerate(chunks):
            chunk_sha = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
            cached_vec = existing_vectors.get((session_id, chunk_sha)) or existing_vectors.get((session_id, chunk))
            if _is_nonzero_vector(cached_vec):
                vec = cached_vec
            elif use_embeddings:
                vec = get_embedding(chunk)
            else:
                vec = None

            fragments.append({
                "session_id": session_id,
                "type": frag_type,
                "content": chunk,
                "timestamp": now_iso,
                "metadata": json.dumps(
                    {
                        "source": rel_key,
                        "filename": filename,
                        "chunk": i,
                        "total": len(chunks),
                        "sha256": chunk_sha,
                    }
                ),
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
    parser.add_argument(
        "--seed-default-lance",
        action="store_true",
        help="Rebuild joshua_os/assets/default_lance from universal OS docs",
    )
    args = parser.parse_args()
    bootstrap_foundation(target_dir=args.dir, seed_default_lance=args.seed_default_lance)
