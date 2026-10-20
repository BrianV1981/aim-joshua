#!/usr/bin/env python3
import traceback
import sys
import os
import json
from fastmcp import FastMCP, Context

# Create the MCP server
mcp = FastMCP("LanceDB Search Server")

@mcp.tool()
def search_lancedb(query: str, top_k: int = 10, ctx: Context = None) -> str:
    """Search the LanceDB vector database for architectural context, code snippets, and mandates."""
    workspace_path = None
    
    # Extract workspace URI dynamically from the initialize payload as per mandate
    if ctx and hasattr(ctx, "request_context"):
        client_params = getattr(ctx.request_context.session, "client_params", None)
        if client_params:
            extra = getattr(client_params, "model_extra", {})
            if extra:
                folders = extra.get("workspaceFolders", [])
                if folders and len(folders) > 0:
                    uri = folders[0].get("uri", "")
                    if uri.startswith("file://"):
                        workspace_path = uri[7:]
                    else:
                        workspace_path = uri
                        
    if not workspace_path:
        workspace_path = os.getcwd()

    db_path = os.path.join(workspace_path, "joshua_os", "memory_lance")
    
    # Dynamically locate .aim_core (prefer workspace, fall back to script directory for umbrella folders)
    core_path = os.path.join(workspace_path, "joshua_os", ".aim_core")
    if not os.path.isdir(core_path):
        core_path = os.path.dirname(os.path.abspath(__file__))
    if core_path not in sys.path:
        sys.path.insert(0, core_path)
        
    try:
        import lance_backend
        from retriever import perform_search

        # Rule 1 (Strict Project Isolation): If local DB exists, never scan subfolders.
        # Rule 2 (Umbrella Fallback): If no local DB exists in an existing parent directory, scan immediate */joshua_os/memory_lance subfolders.
        subfolder_dbs = []
        if not os.path.isdir(db_path) and os.path.isdir(workspace_path):
            for entry in sorted(os.listdir(workspace_path)):
                sub_db = os.path.join(workspace_path, entry, "joshua_os", "memory_lance")
                if os.path.isdir(sub_db):
                    subfolder_dbs.append((entry, sub_db))

        if subfolder_dbs:
            results = []
            for sub_name, sub_db in subfolder_dbs:
                lance_backend.LANCE_DB_PATH = sub_db
                sub_hits = perform_search(query, top_k=top_k) or []
                for hit in sub_hits:
                    hit_copy = dict(hit)
                    orig_src = hit_copy.get('filename') or hit_copy.get('source_db') or hit_copy.get('session_id') or 'Unknown'
                    hit_copy['filename'] = f"[{sub_name}] {orig_src}"
                    results.append(hit_copy)
            results.sort(key=lambda r: r.get('score', 0.0), reverse=True)
            results = results[:top_k]
        else:
            lance_backend.LANCE_DB_PATH = db_path
            results = perform_search(query, top_k=top_k)
        
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
