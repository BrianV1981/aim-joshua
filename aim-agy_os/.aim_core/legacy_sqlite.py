import os
import json
import sqlite3
import struct
import math
from config_utils import AIM_ROOT

def cosine_similarity(v1, v2):
    if not v1 or not v2 or len(v1) != len(v2): return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = math.sqrt(sum(a * a for a in v1))
    magnitude2 = math.sqrt(sum(b * b for b in v2))
    if magnitude1 == 0 or magnitude2 == 0: return 0.0
    return dot_product / (magnitude1 * magnitude2)

class ForensicDB:
    def __init__(self, custom_path=None):
        self.db_path = custom_path or os.path.join(AIM_ROOT, "archive/forensic.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._initialize_schema()

    def _initialize_schema(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                mtime REAL NOT NULL,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fragments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT,
                embedding BLOB,
                metadata TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    def _vec_to_blob(self, vec):
        if not vec: return None
        return struct.pack(f'{len(vec)}f', *vec)

    def _blob_to_vec(self, blob):
        if not blob: return None
        n = len(blob) // 4
        return list(struct.unpack(f'{n}f', blob))

    def add_session(self, session_id, filename, mtime):
        self.cursor.execute(
            "INSERT OR REPLACE INTO sessions (id, filename, mtime) VALUES (?, ?, ?)",
            (session_id, filename, mtime)
        )
        self.conn.commit()

    def add_fragments(self, session_id, fragments):
        # Clear existing fragments for this session if re-indexing
        self.cursor.execute("DELETE FROM fragments WHERE session_id = ?", (session_id,))
        
        for frag in fragments:
            embedding_blob = self._vec_to_blob(frag.get('embedding'))
            metadata = json.dumps(frag.get('metadata', {}))
            self.cursor.execute(
                "INSERT INTO fragments (session_id, type, content, timestamp, embedding, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, frag['type'], frag['content'], frag.get('timestamp'), embedding_blob, metadata)
            )
        self.conn.commit()

    def get_session_mtime(self, session_id):
        self.cursor.execute("SELECT mtime FROM sessions WHERE id = ?", (session_id,))
        res = self.cursor.fetchone()
        return res[0] if res else 0

    def search_fragments(self, query_vector, top_k=10, session_filter=None):
        sql = "SELECT f.type, f.content, f.timestamp, f.embedding, s.filename FROM fragments f JOIN sessions s ON f.session_id = s.id"
        params = []
        if session_filter:
            sql += " WHERE f.session_id = ?"
            params.append(session_filter)
        
        self.cursor.execute(sql, params)
        rows = self.cursor.fetchall()
        
        results = []
        for row in rows:
            frag_type, content, timestamp, embedding_blob, filename = row
            embedding = self._blob_to_vec(embedding_blob)
            score = cosine_similarity(query_vector, embedding)
            results.append({
                "score": score,
                "type": frag_type,
                "content": content,
                "timestamp": timestamp,
                "session_file": filename
            })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def close(self):
        self.conn.close()
