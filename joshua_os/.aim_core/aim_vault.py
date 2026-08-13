#!/usr/bin/env python3
import keyring
import getpass
import sys
import argparse
from rich.console import Console
from rich.table import Table

console = Console()

def set_key(service, key_name, value=None):
    if not value:
        value = getpass.getpass(f"Enter value for {service}:{key_name}: ")
    if not value:
        console.print("[red]Error: Value cannot be empty.[/red]")
        return False
    keyring.set_password(service, key_name, value)
    console.print(f"[green]Success: {service}:{key_name} stored in vault.[/green]")
    return True

def get_key(service, key_name):
    return keyring.get_password(service, key_name)

def list_keys():
    # Keyring doesn't easily list keys, so we track common A.I.M. keys
    common_keys = [
        ("aim-system", "google-api-key"),
        ("aim-system", "openrouter-api-key"),
        ("aim-system", "openai-api-key"),
        ("aim-system", "anthropic-api-key"),
        ("aim-system", "reasoning-api-key")
    ]
    
    table = Table(title="A.I.M. Secret Vault")
    table.add_column("Service", style="cyan")
    table.add_column("Key Name", style="magenta")
    table.add_column("Status", style="green")
    
    for svc, name in common_keys:
        val = get_key(svc, name)
        status = "[bold green]SET[/bold green]" if val else "[red]NOT SET[/red]"
        table.add_row(svc, name, status)
    
    console.print(table)

def vault_doctor():
    import os
    from pathlib import Path
    table = Table(title="A.I.M. Vault Diagnostics")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="green")
    
    # 1. Check OS Keyring
    try:
        keyring.set_password("aim-system", "vault-doctor-test", "test")
        val = keyring.get_password("aim-system", "vault-doctor-test")
        if val == "test":
            table.add_row("OS Keyring", "[green]OK[/green]", "Working properly")
            try:
                keyring.delete_password("aim-system", "vault-doctor-test")
            except:
                pass
        else:
            table.add_row("OS Keyring", "[red]FAIL[/red]", "Could not retrieve test value")
    except Exception as e:
        table.add_row("OS Keyring", "[red]FAIL[/red]", str(e))
        
    # 2. Check Blackbox Fallback Key
    bb_key = Path.home() / ".aim" / "blackbox.key"
    if bb_key.is_file():
        st = bb_key.stat()
        mode = oct(st.st_mode)[-3:]
        if mode == "600":
            table.add_row("Blackbox Key", "[green]OK[/green]", f"{bb_key} (mode 0600)")
        else:
            table.add_row("Blackbox Key", "[yellow]WARN[/yellow]", f"{bb_key} (mode {mode}, should be 0600)")
    else:
        table.add_row("Blackbox Key", "[yellow]MISSING[/yellow]", f"Not found at {bb_key}")
        
    console.print(table)
    console.print("\n[bold]Recovery Information:[/bold]")
    console.print("If your system keyring is wiped or unavailable, Blackbox Vault decryption will fail.")
    console.print(f"By default, a fallback file key is created at [bold cyan]{Path.home() / '.aim' / 'blackbox.key'}[/bold cyan].")
    console.print("Back up this file to a secure location to ensure you can always recover encrypted sessions.")

def main():
    parser = argparse.ArgumentParser(description="A.I.M. Secret Vault Manager")
    subparsers = parser.add_subparsers(dest="command")
    
    set_parser = subparsers.add_parser("set", help="Store a secret")
    set_parser.add_argument("service", help="Service name (e.g., aim-system)")
    set_parser.add_argument("name", help="Key name (e.g., agy-api-key)")
    set_parser.add_argument("--value", help="Value (optional, will prompt if omitted)")
    
    get_parser = subparsers.add_parser("get", help="Retrieve a secret (for testing)")
    get_parser.add_argument("service")
    get_parser.add_argument("name")
    
    subparsers.add_parser("list", help="List status of common keys")
    
    doctor_parser = subparsers.add_parser("doctor", help="Run vault diagnostics and key recovery info")
    
    args = parser.parse_args()
    
    if args.command == "set":
        set_key(args.service, args.name, args.value)
    elif args.command == "get":
        val = get_key(args.service, args.name)
        if val: console.print(f"Value: {val}")
        else: console.print("[red]Not found.[/red]")
    elif args.command == "list":
        list_keys()
    elif args.command == "doctor":
        vault_doctor()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
