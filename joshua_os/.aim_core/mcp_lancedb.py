#!/usr/bin/env python3
"""LanceDB MCP server with strict per-project isolation (Issue #141).

The server *code* may live in one shared, versioned engine
(``~/.aim/engine``), but the *database* is always resolved from the active
workspace and the call fails closed when that project has no index. It never
borrows another project's memory.
"""
import traceback
import subprocess
import sys
import os
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


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def _resolve_workspace(ctx: Context = None) -> str:
    """Resolve the active project workspace from the MCP payload, env, or cwd."""
    workspace_path = None

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
                if not workspace_path and extra.get("rootUri"):
                    workspace_path = _uri_to_local_path(str(extra["rootUri"]))

    if not workspace_path:
        env_ws = os.environ.get("AIM_WORKSPACE_ROOT", "").strip()
        if env_ws:
            workspace_path = _uri_to_local_path(env_ws)
        else:
            workspace_path = os.getcwd()

    return workspace_path


def _discover_subfolder_dbs(workspace_path: str) -> list[tuple[str, str]]:
    subfolder_dbs: list[tuple[str, str]] = []
    if not workspace_path or not os.path.isdir(workspace_path):
        return subfolder_dbs
    for entry in sorted(os.listdir(workspace_path)):
        sub_db = os.path.join(workspace_path, entry, "joshua_os", "memory_lance")
        if os.path.isdir(sub_db):
            subfolder_dbs.append((entry, sub_db))
    return subfolder_dbs


def _resolve_db_path(workspace_path: str) -> tuple[str | None, list[tuple[str, str]], str | None]:
    """Return ``(db_path, subfolder_dbs, error)`` with strict project isolation."""
    explicit = os.environ.get("AIM_MEMORY_DB", "").strip()
    if explicit:
        db_path = os.path.abspath(os.path.expanduser(explicit))
        if os.path.isdir(db_path):
            return db_path, [], None
        return None, [], f"AIM_MEMORY_DB points to a missing directory: {db_path}"

    if not workspace_path or _is_home_or_fs_root(workspace_path):
        return (
            None,
            [],
            f"No project workspace detected (resolved to '{workspace_path}', which is $HOME or a filesystem root).",
        )

    local_db = os.path.join(workspace_path, "joshua_os", "memory_lance")
    if os.path.isdir(local_db):
        return local_db, [], None

    if _env_flag("AIM_UMBRELLA_SCAN"):
        subfolder_dbs = _discover_subfolder_dbs(workspace_path)
        if subfolder_dbs:
            return None, subfolder_dbs, None

    return None, [], f"No project memory DB found at {local_db}"


def _fail_closed(workspace_path: str | None, reason: str) -> str:
    expected = (
        os.path.join(workspace_path, "joshua_os", "memory_lance")
        if workspace_path
        else "<project>/joshua_os/memory_lance"
    )
    return (
        "[NO PROJECT MEMORY DB]\n"
        f"Reason:    {reason}\n"
        f"Workspace: {workspace_path or '(none)'}\n"
        f"Expected:  {expected}\n"
        "This server never borrows another project's database.\n"
        "Fix: cd into the project and run `./aim init` or `./aim index`, "
        "or set AIM_MEMORY_DB=/absolute/path/to/joshua_os/memory_lance."
    )


@mcp.tool()
def search_lancedb(query: str, top_k: int = 10, ctx: Context = None) -> str:
    """Search this project's LanceDB vector database for architectural context, code snippets, and mandates."""
    workspace_path = _resolve_workspace(ctx)
    db_path, subfolder_dbs, error = _resolve_db_path(workspace_path)
    if error:
        return _fail_closed(workspace_path, error)

    # One shared engine: always import the code that is actually running this server.
    if _current_dir not in sys.path:
        sys.path.insert(0, _current_dir)

    try:
        from retriever import perform_search

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
            db_label = "[umbrella] " + ", ".join(name for name, _ in subfolder_dbs)
        else:
            results = perform_search(query, top_k=top_k, db_path=db_path)
            db_label = db_path

        if not results:
            return f"No fragments found for query: '{query}' (DB: {db_label})"

        output = f"--- LanceDB Search Results for: '{query}' ---\nDB: {db_label}\n\n"
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
