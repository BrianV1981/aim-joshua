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
    
    # We must dynamically override the hardcoded LANCE_DB_PATH in lance_backend
    core_path = os.path.join(workspace_path, "joshua_os", ".aim_core")
    if core_path not in sys.path:
        sys.path.insert(0, core_path)
        
    try:
        import lance_backend
        lance_backend.LANCE_DB_PATH = db_path
        
        from retriever import perform_search
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
