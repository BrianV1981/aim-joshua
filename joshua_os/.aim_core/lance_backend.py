import traceback
import os
import sqlite3
import struct
import lancedb
import pyarrow as pa
import pandas as pd
from lancedb.rerankers import Reranker
import re

AIM_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Issue #10: Localize LanceDB to the Sandbox
_cwd = os.getcwd()
if "sandboxes" in _cwd:
    LANCE_DB_PATH = os.path.join(_cwd, "memory_lance")
else:
    LANCE_DB_PATH = os.path.join(AIM_ROOT, "memory_lance")

def blob_to_vec(blob):
    if not blob: return None
    n = len(blob) // 4
    return list(struct.unpack(f'{n}f', blob))

def generate_tantivy_query(query):
    stopwords = {"a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same", "she", "should", "so", "some", "such", "t", "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with", "would", "you", "your", "yours", "yourself", "yourselves"}
    
    tokens = re.findall(r"\b[A-Za-z]+\b|\(|\)", query)
    processed = []
    proper_nouns = []
    
    for t in tokens:
        if t in ("(", ")"):
            processed.append(t)
            continue
        if t.upper() in ("AND", "OR"):
            processed.append(t.upper())
            continue
        if t.lower() in stopwords or len(t) <= 1:
            continue
            
        if t[0].isupper():
            proper_nouns.append(t)
            processed.append("+" + t.lower() + "*") # STRICT INCLUSION
        else:
            processed.append(t.lower() + "*")
        
    fts_query = " ".join(processed)
    
    # Cleanup dangling operators
    fts_query = re.sub(r'\(\s*(AND|OR)\b', '(', fts_query)
    fts_query = re.sub(r'\b(AND|OR)\s*\)', ')', fts_query)
    fts_query = re.sub(r'\b(AND|OR)\s+(AND|OR)\b', r'\1', fts_query)
    fts_query = re.sub(r'^\s*(AND|OR)\b', '', fts_query)
    fts_query = re.sub(r'\b(AND|OR)\s*$', '', fts_query)
    
    return fts_query.strip(), proper_nouns


class EntityIntersectionReranker(Reranker):
    def __init__(self, proper_nouns=None):
        super().__init__()
        self.proper_nouns = proper_nouns or []

    def rerank_hybrid(self, query: str, vector_results: pa.Table, fts_results: pa.Table) -> pa.Table:
        vec_df = vector_results.to_pandas() if vector_results.num_rows > 0 else pd.DataFrame()
        fts_df = fts_results.to_pandas() if fts_results.num_rows > 0 else pd.DataFrame()
        
        scores = {}
        fts_ids = set()
        k = 60
        
        if not fts_df.empty:
            for rank, row in fts_df.iterrows():
                idx = f"{row['fragment_id']}_{row['session_id']}"
                fts_ids.add(idx)
                scores[idx] = scores.get(idx, 0) + 1.0 / (k + rank + 1)
                
        if not vec_df.empty:
            for rank, row in vec_df.iterrows():
                idx = f"{row['fragment_id']}_{row['session_id']}"
                scores[idx] = scores.get(idx, 0) + 1.0 / (k + rank + 1)
                
        if vec_df.empty and fts_df.empty:
            return vector_results
            
        combined_df = pd.concat([vec_df, fts_df]).drop_duplicates(subset=['fragment_id', 'session_id'])
        combined_df['_uid'] = combined_df['fragment_id'].astype(str) + "_" + combined_df['session_id'].astype(str)
        
        combined_df = combined_df[combined_df['_uid'].isin(scores.keys())].copy()
        
        combined_df['_relevance_score'] = combined_df['_uid'].map(scores)

        if self.proper_nouns:
            def _boost(row):
                content = str(row.get('content', '')).lower()
                if any(pn.lower() in content for pn in self.proper_nouns):
                    return row['_relevance_score'] * 1.5
                return row['_relevance_score']
            combined_df['_relevance_score'] = combined_df.apply(_boost, axis=1)

        combined_df.sort_values('_relevance_score', ascending=False, inplace=True)
        
        combined_df['score'] = combined_df['_relevance_score']
        
        if combined_df.empty:
            return pa.Table.from_pandas(combined_df)
            
        return pa.Table.from_pandas(combined_df)


def list_lance_tables(db):
    """Forward/backward-compatible LanceDB table listing (supports ListTablesResponse.tables, iterables, and legacy table_names())."""
    if hasattr(db, "list_tables"):
        res = db.list_tables()
        if hasattr(res, "tables"):
            return list(res.tables)
        return list(res)
    return list(db.table_names())


def rebuild_fts_index(table, column="content"):
    """Forward/backward-compatible LanceDB FTS index builder (avoids create_fts_index DeprecationWarning on LanceDB 0.25+)."""
    try:
        from lancedb.index import FTS

        table.create_index(column, config=FTS(with_position=True), replace=True)
        return
    except (ImportError, TypeError, AttributeError):
        pass
    table.create_fts_index(column, replace=True)


FRAGMENT_SCHEMA = pa.schema([
    pa.field("fragment_id", pa.int64()),
    pa.field("session_id", pa.string()),
    pa.field("type", pa.string()),
    pa.field("content", pa.string()),
    pa.field("timestamp", pa.string()),
    pa.field("metadata", pa.string()),
    pa.field("parent_id", pa.int64()),
    pa.field("source_db", pa.string()),
    pa.field("vector", pa.list_(pa.float32(), 768)),
])


class VectorBackend:
    def __init__(self, path=None):
        self.path = path or LANCE_DB_PATH
        self.db = lancedb.connect(self.path)
        self.table_name = "fragments"

    def ensure_table(self):
        if self.table_name not in list_lance_tables(self.db):
            self.db.create_table(self.table_name, schema=FRAGMENT_SCHEMA)
            try:
                t = self.db.open_table(self.table_name)
                rebuild_fts_index(t, "content")
            except Exception:
                pass

    def get_table(self):
        self.ensure_table()
        return self.db.open_table(self.table_name)

    def _normalize_fragments(self, fragments, start_id=1):
        from datetime import datetime, timezone

        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        current_id = start_id
        records = []
        for frag in fragments:
            if "vector" not in frag or not frag["vector"] or len(frag["vector"]) != 768:
                continue
            records.append({
                "fragment_id": int(frag.get("fragment_id", current_id)),
                "session_id": str(frag.get("session_id", "")),
                "type": str(frag.get("type", "session_history")),
                "content": str(frag.get("content", "")),
                "timestamp": str(frag.get("timestamp") or now_iso),
                "metadata": str(frag.get("metadata", "{}")),
                "parent_id": frag.get("parent_id", None),
                "source_db": str(frag.get("source_db", "live_session")),
                "vector": [float(x) for x in frag["vector"]],
            })
            current_id += 1
        return records

    def add_fragments(self, fragments, rebuild_fts=True):
        table = self.get_table()
        current_id = table.count_rows() + 1
        records = self._normalize_fragments(fragments, start_id=current_id)

        if records:
            table.add(records)
            if rebuild_fts:
                rebuild_fts_index(table, "content")
            print(f"[SUCCESS] Added {len(records)} fragments to LanceDB RAM" + (" and rebuilt FTS index." if rebuild_fts else "."))

    def upsert_fragments(self, fragments, *, purge_predicate=None):
        """
        Atomically replace matching fragments in a single batch write, compact LanceDB
        manifest history, and rebuild the Tantivy FTS index once (Issue #122 / JOSH-W06 / JOSH-028).
        """
        from datetime import timedelta

        existing_rows = []
        if self.table_name in list_lance_tables(self.db):
            try:
                existing_rows = self.db.open_table(self.table_name).to_arrow().to_pylist()
            except Exception:
                existing_rows = []

        incoming_sids = {str(f.get("session_id", "")) for f in fragments if f.get("session_id")}
        if purge_predicate is not None:
            surviving = [r for r in existing_rows if not purge_predicate(r, incoming_sids)]
        else:
            surviving = [r for r in existing_rows if r.get("session_id") not in incoming_sids]

        max_existing_id = max((int(r["fragment_id"]) for r in surviving if r.get("fragment_id") is not None), default=0)
        new_records = self._normalize_fragments(fragments, start_id=max_existing_id + 1)
        combined = surviving + new_records

        if combined:
            self.db.create_table(self.table_name, data=combined, schema=FRAGMENT_SCHEMA, mode="overwrite")
        else:
            self.db.create_table(self.table_name, schema=FRAGMENT_SCHEMA, mode="overwrite")

        tbl = self.db.open_table(self.table_name)
        try:
            tbl.optimize(cleanup_older_than=timedelta(seconds=0))
        except Exception:
            pass
        try:
            rebuild_fts_index(tbl, "content")
        except Exception:
            pass
        print(f"[SUCCESS] Upserted {len(new_records)} fragments ({len(combined)} total) and rebuilt FTS index once.")
        return len(new_records)

    def search(self, query_vec, original_query, top_k=10, session_filter=None):
        table = self.get_table()
        
        fts_query, proper_nouns = generate_tantivy_query(original_query)
        reranker = EntityIntersectionReranker(proper_nouns=proper_nouns)
        
        def execute_query(t):
            if query_vec is not None:
                q = t.search(query_type="hybrid").rerank(reranker)
                q = q.vector(query_vec)
                if fts_query:
                    q = q.text(fts_query)
            else:
                if not fts_query:
                    return []
                q = t.search(fts_query, query_type="fts")
            if session_filter:
                q = q.where(f"session_id = '{session_filter}'")
            return q.limit(max(100, top_k * 2)).to_list()
            
        results = execute_query(table)
        
        # Federated Querying against Parquet ROMs
        active_root = os.path.dirname(os.path.abspath(self.path)) if self.path else AIM_ROOT
        cartridges_dir = os.path.join(active_root, "archive", "cartridges")
        if os.path.exists(cartridges_dir):
            import pyarrow.dataset as ds
            import glob
            mem_db = lancedb.connect("memory://")
            for parquet_file in glob.glob(os.path.join(cartridges_dir, "*.parquet")):
                try:
                    table_name = os.path.basename(parquet_file)
                    if table_name not in list_lance_tables(mem_db):
                        dataset = ds.dataset(parquet_file)
                        t = mem_db.create_table(table_name, data=dataset)
                        try:
                            rebuild_fts_index(t, "content")
                        except Exception:
                            pass # If FTS index creation fails on dataset, skip
                    else:
                        t = mem_db.open_table(table_name)
                    
                    rom_results = execute_query(t)
                    results.extend(rom_results)
                except Exception as e:
                    traceback.print_exc()
                    print(f"[WARNING] Failed to search ROM {parquet_file}: {e}")
                    
        # Sort combined results by score
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        results = results[:max(100, top_k * 2)]
        
        # Format results to match what retriever expects
        formatted_results = []
        for r in results:
            formatted_results.append({
                "id": r["fragment_id"],
                "session_id": r["session_id"],
                "type": r["type"],
                "content": r["content"],
                "timestamp": r["timestamp"],
                "metadata": r["metadata"],
                "parent_id": r["parent_id"],
                "score": r.get("score", 0),
                "filename": r.get("source_db", "")
            })
        return formatted_results