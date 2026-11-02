#!/usr/bin/env python3
import traceback
import subprocess
import sys
import os
import json
import re
import urllib.parse

# --- VENV SELF-BOOTSTRAP ---
_current_dir = os.path.dirname(os.path.abspath(__file__))
_os_root = os.path.dirname(_current_dir)
_venv_py = (
    os.path.join(_os_root, "venv", "Scripts", "python.exe")
    if os.name == "nt"
    else os.path.join(_os_root, "venv", "bin", "python3")
)
if (
    __name__ == "__main__"
    and os.path.isfile(_venv_py)
    and os.path.abspath(sys.executable) != os.path.abspath(_venv_py)
):
    if os.name == "nt":
        sys.exit(subprocess.call([_venv_py] + sys.argv))
    else:
        os.execv(_venv_py, [_venv_py] + sys.argv)

from fastmcp import FastMCP, Context

# Create the MCP server
mcp = FastMCP("LanceDB Search Server")


def _uri_to_local_path(uri: str) -> str:
    """Convert a file:// URI (including Windows drive letters and %20 escapes) into a local filesystem path."""
    if not uri:
        return ""
    if not uri.startswith("file://"):
        return uri
    parsed = urllib.parse.urlparse(uri)
    path = urllib.parse.unquote(parsed.path or "")
    if parsed.netloc and parsed.netloc.lower() != "localhost":
        path = f"//{parsed.netloc}{path}"
    if re.match(r"^/[A-Za-z]:(/|$)", path):
        path = path[1:]
    return path


def _is_home_or_fs_root(path_str: str) -> bool:
    """Return True if path_str resolves to the user's HOME directory or a filesystem/drive root."""
    if not path_str:
        return True
    norm = os.path.abspath(os.path.expanduser(path_str)).rstrip("/\\")
    if not norm or re.match(r"^[A-Za-z]:$", norm):
        return True
    home_norm = os.path.abspath(os.path.expanduser("~")).rstrip("/\\")
    if (norm.lower() == home_norm.lower()) if os.name == "nt" else (norm == home_norm):
        return True
    abs_raw = os.path.abspath(path_str)
    return os.path.dirname(abs_raw) == abs_raw


@mcp.tool()
def search_lancedb(query: str, top_k: int = 10, ctx: Context = None) -> str:
    """Search the LanceDB vector database for architectural context, code snippets, and mandates."""
    workspace_path = None
    from_ctx = False

    # Extract workspace URI dynamically from the initialize payload as per mandate
    if ctx and hasattr(ctx, "request_context"):
        session = getattr(ctx.request_context, "session", None)
        client_params = getattr(session, "client_params", None) if session else None
        if client_params:
            extra = getattr(client_params, "model_extra", None) or {}
            if isinstance(extra, dict):
                folders = extra.get("workspaceFolders") or []
                if folders and len(folders) > 0:
                    first = folders[0]
                    uri = first.get("uri", "") if isinstance(first, dict) else getattr(first, "uri", "")
                    if uri:
                        workspace_path = _uri_to_local_path(uri)
                        from_ctx = True
                if not workspace_path and extra.get("rootUri"):
                    workspace_path = _uri_to_local_path(str(extra["rootUri"]))
                    from_ctx = True

    if not workspace_path:
        env_ws = os.environ.get("AIM_WORKSPACE_ROOT", "").strip()
        if env_ws:
            workspace_path = _uri_to_local_path(env_ws)
            from_ctx = True
        else:
            workspace_path = os.getcwd()

    db_path = os.path.join(workspace_path, "joshua_os", "memory_lance")

    # Dynamically locate .aim_core (prefer workspace, fall back to script directory for umbrella/Desktop launches)
    core_path = os.path.join(workspace_path, "joshua_os", ".aim_core")
    if not os.path.isdir(core_path):
        core_path = _current_dir
    if core_path not in sys.path:
        sys.path.insert(0, core_path)

    try:
        from retriever import perform_search

        # Rule 1 (Strict Project Isolation): If local DB exists, never scan subfolders.
        # Rule 2 (Umbrella Fallback): Scan immediate */joshua_os/memory_lance subfolders when workspace_path
        # came from an explicit workspace context (or a non-HOME/non-root cwd).
        subfolder_dbs = []
        allow_umbrella_scan = from_ctx or not _is_home_or_fs_root(workspace_path)
        if not os.path.isdir(db_path) and allow_umbrella_scan and os.path.isdir(workspace_path):
            for entry in sorted(os.listdir(workspace_path)):
                sub_db = os.path.join(workspace_path, entry, "joshua_os", "memory_lance")
                if os.path.isdir(sub_db):
                    subfolder_dbs.append((entry, sub_db))

        # Rule 3 (Desktop / Non-IDE Fallback, Issue #118): When the MCP host omits workspaceFolders
        # (e.g. Antigravity 2.0 Desktop) and cwd is an app binary dir or $HOME, fall back to the
        # registered installation's own _os_root/memory_lance (or default_lance seed).
        if not from_ctx and not os.path.isdir(db_path) and not subfolder_dbs:
            installed_db = os.path.join(_os_root, "memory_lance")
            seed_db = os.path.join(_os_root, "assets", "default_lance")
            if os.path.isdir(installed_db):
                db_path = installed_db
            elif os.path.isdir(seed_db):
                db_path = seed_db

        # Pass explicit db_path to perform_search without mutating module-global LANCE_DB_PATH (Issue #130)
        if subfolder_dbs:
            results = []
            for sub_name, sub_db in subfolder_dbs:
                sub_hits = perform_search(query, top_k=top_k, db_path=sub_db) or []
                for hit in sub_hits:
                    hit_copy = dict(hit)
                    orig_src = hit_copy.get("filename") or hit_copy.get("source_db") or hit_copy.get("session_id") or "Unknown"
                    hit_copy["filename"] = f"[{sub_name}] {orig_src}"
                    results.append(hit_copy)
            results.sort(key=lambda r: r.get("score", 0.0), reverse=True)
            results = results[:top_k]
        else:
            results = perform_search(query, top_k=top_k, db_path=db_path)
        
        if not results:
            return f"No fragments found for query: '{query}'"
            
        output = f"--- LanceDB Search Results for: '{query}' ---\n\n"
        for i, res in enumerate(results, 1):
            source = res.get('filename') or res.get('source_db') or res.get('session_id') or 'Unknown'
            content = res.get('content', '')
            score = res.get('score', 0.0)
            output += f"[{i}] Score: {score:.4f} | Source: {source}\n{content}\n"
            output += "-" * 45 + "\n"
            
        return output
    except Exception as e:
        traceback.print_exc()
        return f"Retrieval Error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
