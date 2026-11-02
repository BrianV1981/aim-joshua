#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys
import traceback


def find_aim_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


AIM_ROOT = find_aim_root()
if AIM_ROOT not in sys.path:
    sys.path.append(AIM_ROOT)
src_dir = os.path.join(AIM_ROOT, ".aim_core")
if src_dir not in sys.path:
    sys.path.append(src_dir)


def get_active_aim_root(db_path=None):
    """Return the active joshua_os root from explicit `db_path` (preferred) or `lance_backend.LANCE_DB_PATH`."""
    if db_path:
        return os.path.dirname(os.path.abspath(db_path))
    try:
        import lance_backend

        configured_path = getattr(lance_backend, "LANCE_DB_PATH", None)
        if configured_path:
            return os.path.dirname(os.path.abspath(configured_path))
    except Exception:
        pass
    return AIM_ROOT


from config_utils import CONFIG
from plugins.datajack.forensic_utils import get_embedding


def get_fragment_hash(res):
    content = res.get("content", "")
    f_type = res.get("type", "")
    session = res.get("session_id") or res.get("sessionId") or "Global"
    return hashlib.md5(f"{f_type}:{session}:{content[:500]}".encode()).hexdigest()


def get_aggregated_knowledge_map(db_path=None):
    k_map = {
        "foundation_knowledge": [],
        "expert_knowledge": [],
        "session_history": [],
    }

    from lance_backend import VectorBackend

    # 1. Query RAM (memory_lance)
    try:
        table = VectorBackend(path=db_path).get_table()
        df = table.search().limit(1000000).to_pandas()
        for t in ["foundation_knowledge", "expert_knowledge", "session_history"]:
            sub_df = df[df["type"] == t]
            for sess_id, group in sub_df.groupby("session_id"):
                k_map[t].append({
                    "id": sess_id,
                    "filename": group.iloc[0].get("source_db", "live_session"),
                    "fragments": len(group),
                })
    except Exception:
        pass

    # 2. Query ROM (Parquet Cartridges)
    cartridges_dir = os.path.join(get_active_aim_root(db_path=db_path), "archive", "cartridges")
    if os.path.exists(cartridges_dir):
        import glob
        import pyarrow.dataset as ds

        for parquet_file in glob.glob(os.path.join(cartridges_dir, "*.parquet")):
            try:
                dataset = ds.dataset(parquet_file)
                df = dataset.to_table().to_pandas()
                for t in ["foundation_knowledge", "expert_knowledge", "session_history"]:
                    if t not in df["type"].values:
                        continue
                    sub_df = df[df["type"] == t]
                    for sess_id, group in sub_df.groupby("session_id"):
                        k_map[t].append({
                            "id": sess_id,
                            "filename": os.path.basename(parquet_file),
                            "fragments": len(group),
                        })
            except Exception:
                pass

    return k_map


def print_knowledge_map(db_path=None):
    k_map = get_aggregated_knowledge_map(db_path=db_path)

    print("\n--- A.I.M. KNOWLEDGE MAP (Index of Keys) ---")

    def print_category(title, items):
        if not items:
            return
        print(f"\n## {title}")
        for item in items:
            print(f"  - {item['filename']} [{item['fragments']} fragments] (ID: {item['id']})")

    print_category("FOUNDATION KNOWLEDGE (Mandates)", k_map["foundation_knowledge"])
    print_category("EXPERT KNOWLEDGE (Synapse)", k_map["expert_knowledge"])

    if k_map["session_history"]:
        print("\n## SESSION HISTORY")
        print(f"  - {len(k_map['session_history'])} historical sessions indexed.")
        print("    (Use './aim search' with --session to narrow down specific events)")

    print("\nUse './aim search \"<filename>\" --full' to surgically recall specific keys.")


def expand_sandwich_context(results, db_path=None):
    expanded_results = []
    seen_ids = set()

    import lancedb
    import pyarrow.dataset as ds
    from lance_backend import VectorBackend, list_lance_tables, sql_quote

    backend = VectorBackend(path=db_path)
    try:
        table = backend.get_table()
    except Exception:
        table = None

    mem_db = lancedb.connect("memory://")
    active_aim_root = get_active_aim_root(db_path=db_path)

    def query_fragments(source_db, cond_str):
        if source_db and source_db.endswith(".parquet"):
            parquet_path = os.path.join(active_aim_root, "archive", "cartridges", source_db)
            if not os.path.exists(parquet_path):
                return []
            try:
                table_name = os.path.basename(parquet_path)
                if table_name not in list_lance_tables(mem_db):
                    dataset = ds.dataset(parquet_path)
                    t = mem_db.create_table(table_name, data=dataset)
                else:
                    t = mem_db.open_table(table_name)
                return t.search().where(cond_str).to_list()
            except Exception:
                return []
        else:
            if table is None:
                return []
            try:
                return table.search().where(cond_str).to_list()
            except Exception:
                return []

    for res in results:
        frag_id = int(res["id"])
        session_id = str(res["session_id"])
        quoted_sid = sql_quote(session_id)
        parent_id = res["parent_id"]
        source_db = res.get("filename") or res.get("source", "")

        uid = f"{session_id}_{frag_id}"
        if uid in seen_ids:
            continue

        if res["type"] not in ("session_history", "expert_knowledge", "foundation_knowledge"):
            expanded_results.append(res)
            seen_ids.add(uid)
            continue

        if parent_id is not None:
            pid = int(parent_id)
            cond_parent = f"session_id = {quoted_sid} AND fragment_id = {pid}"
            parent_rows = query_fragments(source_db, cond_parent)
            if not parent_rows:
                cond_parent = f"session_id = {quoted_sid} AND sqlite_id = {pid}"
                parent_rows = query_fragments(source_db, cond_parent)

            parent_content = parent_rows[0]["content"] if parent_rows else ""

            cond_adj = (
                f"session_id = {quoted_sid} AND parent_id = {pid} "
                f"AND fragment_id >= {frag_id - 1} AND fragment_id <= {frag_id + 1}"
            )
            adjacent = query_fragments(source_db, cond_adj)
            if not adjacent:
                cond_adj = (
                    f"session_id = {quoted_sid} AND parent_id = {pid} "
                    f"AND sqlite_id >= {frag_id - 1} AND sqlite_id <= {frag_id + 1}"
                )
                adjacent = query_fragments(source_db, cond_adj)

            adjacent.sort(key=lambda x: x.get("fragment_id", x.get("sqlite_id", 0)))

            combined = []
            if parent_content:
                combined.append(f"[OVERARCHING PARENT SUMMARY]\n{parent_content}")
            for r in adjacent:
                combined.append(r["content"])
                row_id = r.get("fragment_id", r.get("sqlite_id"))
                seen_ids.add(f"{session_id}_{row_id}")

            res["content"] = "\n\n---\n\n".join(combined)
            expanded_results.append(res)
        else:
            cond_adj = (
                f"session_id = {quoted_sid} "
                f"AND fragment_id >= {frag_id - 1} AND fragment_id <= {frag_id + 1}"
            )
            adjacent = query_fragments(source_db, cond_adj)
            if not adjacent:
                cond_adj = (
                    f"session_id = {quoted_sid} "
                    f"AND sqlite_id >= {frag_id - 1} AND sqlite_id <= {frag_id + 1}"
                )
                adjacent = query_fragments(source_db, cond_adj)

            adjacent = [r for r in adjacent if r.get("parent_id") is None]
            adjacent.sort(key=lambda x: x.get("fragment_id", x.get("sqlite_id", 0)))

            combined = []
            for r in adjacent:
                combined.append(r["content"])
                row_id = r.get("fragment_id", r.get("sqlite_id"))
                seen_ids.add(f"{session_id}_{row_id}")

            res["content"] = "\n\n---\n\n".join(combined)
            expanded_results.append(res)

    return expanded_results


def perform_search_internal(query, top_k=10, session_filter=None, db_path=None):
    from lance_backend import VectorBackend

    try:
        query_vec = get_embedding(query, task_type="RETRIEVAL_QUERY")
    except Exception:
        query_vec = None

    if not query_vec:
        print(
            "[NOTICE] Semantic Engine Offline: Falling back to exact-keyword (Lexical) search.",
            file=sys.stderr,
        )
        print(
            "         Run './aim config' to configure local embeddings for deep semantic recall.",
            file=sys.stderr,
        )

    try:
        backend = VectorBackend(path=db_path)
        results = backend.search(query_vec, query, top_k=top_k, session_filter=session_filter)
    except Exception as e:
        traceback.print_exc()
        print(f"\n[!] LanceDB Search Error: {e}", file=sys.stderr)
        results = []

    results = expand_sandwich_context(results, db_path=db_path)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results[:top_k]


def perform_search(query, top_k=10, show_context=False, db_path=None):
    return perform_search_internal(query, top_k=top_k, db_path=db_path)


def main():
    parser = argparse.ArgumentParser(description="A.I.M. Autonomous Knowledge Retriever (Native LanceDB/Parquet)")
    parser.add_argument("query", nargs="*", help="The search query")
    parser.add_argument("--full", action="store_true", help="Retrieve full fragments")
    parser.add_argument("--session", help="Filter by specific session ID")
    parser.add_argument("--map", action="store_true", help="Print the knowledge map")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results to retrieve")
    parser.add_argument("--json", action="store_true", help="Output raw JSON array")

    args = parser.parse_args()

    if args.map:
        print_knowledge_map()
        sys.exit(0)

    query = " ".join(args.query)
    if not query:
        print("[ERROR] No query provided.", file=sys.stderr)
        sys.exit(1)

    results = perform_search_internal(query, top_k=args.top_k, session_filter=args.session)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\n--- SEARCH RESULTS: {' '.join(args.query)} ---\n")
        if not results:
            print("No matches found.")
        for i, r in enumerate(results):
            score = r.get("score", 0)
            score_str = f"{score:.4f}" if isinstance(score, float) else str(score)
            source = r.get("filename") or r.get("source_db") or r.get("session_id")
            print(f"[{i+1}] Source: {source} | Score: {score_str}")
            print(f"{r.get('content', '').strip()}\n")
            print("-" * 40 + "\n")


if __name__ == "__main__":
    main()
