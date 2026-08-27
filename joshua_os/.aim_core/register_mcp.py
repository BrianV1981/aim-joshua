#!/usr/bin/env python3
import json
import os

def main():
    config_dir = os.path.expanduser("~/.gemini/config")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "mcp_config.json")

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                data = json.load(f)
            except:
                data = {}
    else:
        data = {}

    if "mcpServers" not in data:
        data["mcpServers"] = {}

    data["mcpServers"]["search_lancedb"] = {
        "command": "python3",
        "args": ["joshua_os/.aim_core/mcp_lancedb.py"]
    }

    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)
    print("    [*] Registered search_lancedb MCP server in ~/.gemini/config/mcp_config.json")

if __name__ == "__main__":
    main()
