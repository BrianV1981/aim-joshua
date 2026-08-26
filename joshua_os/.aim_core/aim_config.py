from config_utils import PROJECT_ROOT
#!/usr/bin/env python3
import os
import json
import sys
import time
import subprocess
import requests
import re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
import questionary

# --- DYNAMIC ROOT DISCOVERY ---
def find_aim_root():
    current = os.path.abspath(os.getcwd())
    while current != '/':
        if os.path.exists(os.path.join(current, "core", "CONFIG.json")) or os.path.exists(os.path.join(current, "setup.sh")):
            return current
        current = os.path.dirname(current)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AIM_ROOT = find_aim_root()
src_dir = os.path.join(AIM_ROOT, ".aim_core")
if src_dir not in sys.path: sys.path.append(src_dir)

from reasoning_utils import generate_reasoning
from aim_vault import get_key, set_key

CONFIG_PATH = os.path.join(PROJECT_ROOT, ".aim_core/CONFIG.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {}

CONFIG = load_config()
console = Console()

tui_style = questionary.Style([
    ('qmark', 'fg:#FF9D00 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#5F819D bold'),
    ('pointer', 'fg:#FF9D00 bold'),
    ('highlighted', 'fg:#FF9D00 bold'),
    ('selected', 'fg:#5F819D'),
    ('separator', 'fg:#6C6C6C'),
    ('instruction', ''),
    ('text', ''),
    ('disabled', 'fg:#858585 italic')
])


def test_provider(provider, model, endpoint, brain_type="default_reasoning", auth_type="API Key"):
    """Validates the provider configuration with a simple prompt."""
    with console.status(f"[bold blue]Testing {provider} ({model})...[/bold blue]"):
        try:
            # We create a temporary config for the test
            temp_config = CONFIG.copy()
            if 'tiers' not in temp_config['models']: temp_config['models']['tiers'] = {}
            temp_config['models']['tiers'][brain_type] = {
                "provider": provider,
                "model": model,
                "endpoint": endpoint,
                "auth_type": auth_type
            }

            # Pass temp_config to generate_reasoning. Use a 60s timeout so health checks for flagship models pass.
            resp = generate_reasoning("Respond with 'OK'", brain_type=brain_type, config=temp_config, timeout=60)            
            if "Error" in resp or "Exception" in resp:
                return False, resp
            # Strict validation: The prompt explicitly asked the model to "Respond with 'OK'".
            # We strictly look for that string to prevent short error messages from falsely passing.
            if "OK" in resp or "ok" in resp.lower() or "Ok" in resp:
                return True, resp
            return False, f"Unexpected response shape: {resp}"
        except Exception as e:
            return False, str(e)

def setup_secrets_menu():
    while True:
        os.system('clear')
        rprint(Panel("[bold cyan]A.I.M. SECRET VAULT[/bold cyan]\nSovereign Credential Management"))
        
        common_keys = [
            ("google", "google-api-key"),
            ("openrouter", "openrouter-api-key"),
            ("openai", "openai-api-key"),
            ("anthropic", "anthropic-api-key")
        ]
        
        table = Table()
        table.add_column("Provider", style="cyan")
        table.add_column("Status", style="green")
        
        for provider, key_name in common_keys:
            val = get_key("aim-system", key_name)
            status = "[bold green]SET[/bold green]" if val else "[red]NOT SET[/red]"
            table.add_row(provider.capitalize(), status)
        
        rprint(table)
        
        choice = questionary.select(
            "Manage Secrets:",
            choices=[f"Set {k.capitalize()} Key" for k, _ in common_keys] + ["Back"]
        ).ask()
        
        if choice == "Back": break
        
        provider = choice.split()[1].lower()
        key_name = next(kn for p, kn in common_keys if p == provider)
        set_key("aim-system", key_name)

def setup_cognitive_tier(tier_name):
    rprint(Panel(f"[bold blue]Tier Configuration: {tier_name.upper()}[/bold blue]"))
    
    provider = questionary.select(
        "Select Provider:",
        choices=["google", "openrouter", "anthropic", "codex-cli", "local (ollama)", "openai-compat"]
    ).ask()
    
    auth_type = "api_key"
    if provider in ["google", "codex-cli"]:
        auth_type = questionary.select(
            "Authentication Method:",
            choices=["API Key", "OAuth (System Default / CLI)"]
        ).ask()
    
    model = ""
    endpoint = ""
    key_name = None

    if provider == "google":
        selection_mode = questionary.select(
            "Select Mode:",
            choices=["All Models (Full List)", "Other (Manual)"]
        ).ask()
        
        if selection_mode == "All Models (Full List)":
            model_choices = [
                "agy-3.1-pro-preview",
                "agy-3-flash-preview",
                "agy-2.5-pro",
                "agy-2.5-flash",
                "agy-2.5-flash-lite"
            ]
            model = questionary.select("Select Google Model:", choices=model_choices).ask()
        else:
            model = questionary.text("Enter Google Model ID (e.g., agy-3.1-pro-preview):").ask()            
        endpoint = "https://generativelanguage.googleapis.com"
        if "API Key" in auth_type:
            key_name = "google-api-key"
        else:
            # REGRESSION GUARD: Do NOT trigger `subprocess.run(["agy", "login"])` here.
            # The Antigravity CLI intercepts it and traps the user in an interactive chat session,
            # requiring a double Ctrl+C to escape back to the TUI. (See Issue #24)
            rprint("[cyan]Delegating authentication natively to the Antigravity CLI...[/cyan]")
            rprint("[yellow]Please ensure you are authenticated by running 'agy login' in a separate terminal.[/yellow]")
            key_name = None
    elif provider == "codex-cli":
        model_choices = ["gpt-5.4", "gpt-5.4-mini", "gpt-5.3-codex", "gpt-5.3-codex-spark", "Other (Manual)"]
        model = questionary.select("Select Codex Model:", choices=model_choices).ask()
        if model == "Other (Manual)":
            model = questionary.text("Enter Codex Model ID (e.g., gpt-5.4):").ask()
        if "OAuth" in auth_type:
            rprint("[cyan]Triggering Codex CLI Login...[/cyan]")
            try: subprocess.run(["codex", "login"], check=True)
            except: rprint("[red]Failed to trigger 'codex login'. Is it installed?[/red]")
        else:
            key_name = "openai-api-key"
    elif provider == "openrouter":
        model_choices = [
            "anthropic/claude-3.5-sonnet", 
            "google/agy-2.0-flash-001",
            "deepseek/deepseek-r1",
            "openai/gpt-4o",
            "meta-llama/llama-3.3-70b-instruct",
            "Other (Manual)"
        ]
        model = questionary.select("Select OpenRouter Model:", choices=model_choices).ask()
        if model == "Other (Manual)":
            model = questionary.text("Enter OpenRouter Model ID (e.g., provider/model):").ask()
        endpoint = "https://openrouter.ai/api/v1"
        key_name = "openrouter-api-key"
    elif provider == "anthropic":
        model_choices = ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229", "Other (Manual)"]
        model = questionary.select("Select Anthropic Model:", choices=model_choices).ask()
        if model == "Other (Manual)":
            model = questionary.text("Enter Anthropic Model ID:").ask()
        endpoint = "https://api.anthropic.com/v1/messages"
        key_name = "anthropic-api-key"
    elif provider == "local (ollama)":
        model = questionary.text("Ollama Model (e.g., gemma4:e4b):", default="gemma4:e4b").ask()
        if not model or not model.strip(): model = "gemma4:e4b"
        endpoint = questionary.text("Ollama Endpoint:", default="http://127.0.0.1:11434/api/generate").ask()
        if not endpoint or not endpoint.strip(): endpoint = "http://127.0.0.1:11434/api/generate"
        
        ctx_val = questionary.text("Ollama Context Window (e.g. 262144 for 256k):", default=str(CONFIG.get('settings', {}).get('ollama_num_ctx', 32768))).ask()
        if ctx_val and ctx_val.isdigit():
            if 'settings' not in CONFIG: CONFIG['settings'] = {}
            CONFIG['settings']['ollama_num_ctx'] = int(ctx_val)
            save_config(CONFIG)
            
        key_name = None
    else: # openai-compat
        model = questionary.text("Model Name:").ask()
        endpoint = questionary.text("Endpoint URL:").ask()
        key_name = "openai-api-key"

    # Verify key exists
    if key_name and not get_key("aim-system", key_name):
        rprint(f"[yellow]Warning: {key_name} is not set in the vault.[/yellow]")
        if questionary.confirm("Set it now?").ask():
            set_key("aim-system", key_name)

    # Test
    success, msg = test_provider(provider.replace(" (ollama)", ""), model, endpoint, tier_name, auth_type)
    if success:
        rprint(f"[green]Test Success: {msg}[/green]")
        
        CONFIG['models'][tier_name] = {
            "provider": provider.replace(" (ollama)", ""),
            "model": model,
            "endpoint": endpoint,
            "auth_type": auth_type
        }
        save_config(CONFIG)
    else:
        rprint(f"[red]Test Failed: {msg}[/red]")
        if questionary.confirm("Save anyway?").ask():
            
            CONFIG['models'][tier_name] = {
                "provider": provider.replace(" (ollama)", ""),
                "model": model,
                "endpoint": endpoint,
                "auth_type": auth_type
            }
            save_config(CONFIG)

def mcp_server_menu():
    while True:
        os.system('clear')
        rprint(Panel("[bold green]A.I.M. MCP SERVER CONTROL[/bold green]\nModel Context Protocol Integration"))
        
        # Check if server is running (rudimentary check via pgrep)
        try:
            subprocess.run(["pgrep", "-f", ".aim_core/mcp_server.py"], check=True, capture_output=True)
            status = "[bold green]ONLINE (Background)[/bold green]"
        except subprocess.CalledProcessError:
            status = "[bold red]OFFLINE[/bold red]"
            
        rprint(f"Server Status: {status}\n")
        rprint("[cyan]Connection String for IDEs (Cursor/VSCode):[/cyan]")
        rprint(f"[yellow]{AIM_ROOT}/venv/bin/python3 {AIM_ROOT}/.aim_core/mcp_server.py[/yellow]\n")
        
        choice = questionary.select(
            "MCP Actions:",
            choices=[
                "1. Launch MCP Inspector (Web UI Test)",
                "2. View MCP Client Setup Instructions",
                "3. Back"
            ]
        ).ask()
        
        if choice == "3. Back": break
        
        if "1." in choice:
            rprint("[cyan]Launching FastMCP Inspector... (Press Ctrl+C to exit)[/cyan]")
            fastmcp_bin = os.path.join(AIM_ROOT, "venv/bin/fastmcp")
            try:
                subprocess.run([fastmcp_bin, "inspector", os.path.join(AIM_ROOT, ".aim_core/mcp_server.py")])
            except KeyboardInterrupt: pass
        elif "2." in choice:
            rprint("\n[bold cyan]--- Claude Desktop Setup ---[/bold cyan]")
            rprint("Add the following to your claude_desktop_config.json:")
            config_example = {
                "mcpServers": {
                    "aim-engram": {
                        "command": os.path.join(AIM_ROOT, "venv/bin/python3"),
                        "args": [os.path.join(AIM_ROOT, ".aim_core/mcp_server.py")]
                    }
                }
            }
            rprint(f"[yellow]{json.dumps(config_example, indent=2)}[/yellow]")
            rprint("\n[bold cyan]--- Cursor / VS Code Setup ---[/bold cyan]")
            rprint("1. Open MCP settings in your IDE.")
            rprint("2. Add a new 'stdio' server.")
            rprint(f"3. Command: [yellow]{os.path.join(AIM_ROOT, 'venv/bin/python3')}[/yellow]")
            rprint(f"4. Args: [yellow]{os.path.join(AIM_ROOT, '.aim_core/mcp_server.py')}[/yellow]")
            input("\nPress Enter to continue...")

def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)



def rag_model_matrix_menu():
    while True:
        os.system('clear')
        rprint(Panel("[bold green]RAG Model Matrix[/bold green]\nDynamically assign models for specialized RAG pipelines."))
        
        matrix_table = Table(title="RAG Model Assignments")
        matrix_table.add_column("Task", style="cyan")
        matrix_table.add_column("Provider", style="magenta")
        matrix_table.add_column("Model", style="yellow")
        
        models_config = CONFIG.get('models', {})
        
        # 1. Embedding
        matrix_table.add_row("1. Embedding (Vector Math)", models_config.get('embedding_provider', 'local'), models_config.get('embedding', 'nomic-embed-text'))
        # 2. Vision
        vision = models_config.get('vision_engine', {"provider": "NOT SET", "model": "N/A"})
        matrix_table.add_row("2. Vision Processing (Images)", vision.get('provider'), vision.get('model'))
        # 3. Coreference
        coref = models_config.get('coreference_engine', {"provider": "NOT SET", "model": "N/A"})
        matrix_table.add_row("3. Query Rewriting (Coreference)", coref.get('provider'), coref.get('model'))
        # 4. Generative
        gen = models_config.get('default_reasoning', {"provider": "NOT SET", "model": "N/A"})
        matrix_table.add_row("4. Generative Reasoning", gen.get('provider'), gen.get('model'))
        
        rprint(matrix_table)
        
        choice = questionary.select(
            "Select a pipeline to configure:",
            choices=["1. Embedding", "2. Vision Processing", "3. Query Rewriting", "4. Generative Reasoning", "5. Back"]
        ).ask()
        
        if not choice or choice.startswith("5."): break
        
        if choice.startswith("1."):
            provider = questionary.select("Provider:", choices=["local", "google", "openai-compat"]).ask()
            if not provider: continue
            model = questionary.text("Model Name (e.g. nomic-embed-text):", default=models_config.get('embedding', "")).ask()
            endpoint = questionary.text("Endpoint URL (if local/compat):", default=models_config.get('embedding_endpoint', "http://localhost:11434/api/embeddings")).ask()
            CONFIG['models']['embedding_provider'] = provider
            CONFIG['models']['embedding'] = model
            CONFIG['models']['embedding_endpoint'] = endpoint
            save_config(CONFIG)
        elif choice.startswith("2."): setup_cognitive_tier("vision_engine")
        elif choice.startswith("3."): setup_cognitive_tier("coreference_engine")
        elif choice.startswith("4."): setup_cognitive_tier("default_reasoning")

def main_menu():
    # Cache for health status: {tier: (status_text, timestamp)}
    health_cache = {}

    while True:
        os.system('clear')
        rprint(Panel("[bold green]A.I.M. SOVEREIGN COCKPIT v2.0[/bold green]\nCognitive Orchestration Layer"))
        
        table = Table(title="Cognitive Status & Health")
        table.add_column("Tier", style="cyan")
        table.add_column("Provider", style="magenta")
        table.add_column("Model", style="yellow")
        table.add_column("Health", justify="center")
        table.add_column("Diagnostics", style="dim")
        
        models_config = CONFIG.get('models', {})
        tiers = ["default_reasoning", "subconscious_daemon"]
        tier_labels = {
            "default_reasoning": "Primary Brain",
            "subconscious_daemon": "Subconscious Wiki Daemon"
        }
        for t in tiers:
            details = models_config.get(t, {"provider": "NOT SET", "model": "N/A"})
            status_indicator, diag_msg = health_cache.get(t, ("[white]○[/white]", ""))
            table.add_row(tier_labels.get(t, t), details['provider'], details['model'], status_indicator, diag_msg)
        rprint(table)
        
        choice = questionary.select(
            "Main Settings:",
            choices=[
                "1. Run Cognitive Health Check",
                "2. Manage Secret Vault",
                "3. Configure Primary Brain",
                "4. Manage MCP Server",
                "5. Archive Retention",
                "6. RAG Model Matrix (Dynamic Config)",
                "7. Exit"
            ],
            style=tui_style
        ).ask()

        if not choice or choice.startswith("7. Exit"): break
        
        if choice.startswith("1."):
            for i, t in enumerate(tiers):
                details = models_config.get(t)
                if not details or details.get('provider') == "NOT SET":
                    health_cache[t] = ("[red]●[/red]", "NOT SET") 
                    continue
                success, msg = test_provider(details['provider'], details['model'], details.get('endpoint'), t, details.get('auth_type', 'API Key'))
                if success:
                    health_cache[t] = ("[bold green]●[/bold green]", "OK")
                elif "[ERROR: CAPACITY_LOCKOUT]" in str(msg):
                    health_cache[t] = ("[bold yellow]⚠[/bold yellow]", "Server Capacity Exhausted (Google-side). Try again later.")
                else:
                    health_cache[t] = ("[bold red]●[/bold red]", str(msg)[:60])
                
                # Prevent API rate limits when testing multiple models back-to-back
                if i < len(tiers) - 1:
                    import time; time.sleep(2)
        elif choice.startswith("2."): setup_secrets_menu()
        elif choice.startswith("3."): setup_cognitive_tier("default_reasoning")
        elif choice.startswith("4."): mcp_server_menu()
        elif choice.startswith("5."):
            rprint("[cyan]Set retention days for raw logs and proposals.[/cyan]")
            rprint("[yellow]Enter '0' to deactivate automatic purge.[/yellow]")
            days = questionary.text("Retention Days:", default=str(CONFIG['settings'].get('archive_retention_days', 0))).ask()
            if days and days.isdigit():
                CONFIG['settings']['archive_retention_days'] = int(days)
                save_config(CONFIG)
        elif choice.startswith("6."):
            rag_model_matrix_menu()

if __name__ == "__main__":
    try: main_menu()
    except KeyboardInterrupt: sys.exit(0)
