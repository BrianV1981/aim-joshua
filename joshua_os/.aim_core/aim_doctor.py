#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import sys
import time

try:
    import requests
except Exception:  # pragma: no cover - requests is a core dependency
    requests = None

try:
    from bootstrap_install import repair_venv_shebangs
except Exception:  # pragma: no cover - consumer workspaces may not vendor it
    def repair_venv_shebangs(os_dir):  # noqa: ARG001
        return 0


DEFAULT_EMBEDDING_PROVIDER = "local"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_EMBEDDING_ENDPOINT = "http://127.0.0.1:11434/api/embeddings"
TARGET_EMBEDDING_DIM = 768


def _load_models_config():
    """Read `<core>/CONFIG.json` models block without mutating config state (#173)."""
    core_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(core_dir, "CONFIG.json")
    models = {}
    try:
        with open(cfg_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and isinstance(data.get("models"), dict):
            models = data["models"]
    except Exception:
        models = {}
    return {
        "embedding_provider": models.get("embedding_provider") or DEFAULT_EMBEDDING_PROVIDER,
        "embedding": models.get("embedding") or DEFAULT_EMBEDDING_MODEL,
        "embedding_endpoint": models.get("embedding_endpoint") or DEFAULT_EMBEDDING_ENDPOINT,
    }


def probe_embedding_provider(timeout=2.0):
    """Probe the configured embedding provider for reachability, model, and dimension (#173)."""
    cfg = _load_models_config()
    ptype = str(cfg["embedding_provider"] or "local").strip().lower()
    if ptype == "ollama":
        ptype = "local"
    model = cfg["embedding"]
    endpoint = cfg["embedding_endpoint"]
    info = {
        "status": "unconfigured",
        "provider": ptype,
        "model": model,
        "endpoint": endpoint,
        "dim": 0,
        "latency_ms": 0.0,
        "detail": "",
    }

    if requests is None:
        info["detail"] = "requests library unavailable"
        return info

    timeout = max(0.5, float(timeout))
    read_timeout = (min(1.0, timeout), timeout)

    try:
        if ptype == "local":
            started = time.perf_counter()
            resp = requests.post(
                endpoint,
                json={"model": model, "prompt": "aim doctor embedding probe"},
                timeout=read_timeout,
            )
            resp.raise_for_status()
            vec = resp.json().get("embedding") or []
        elif ptype == "openai-compat":
            url = endpoint if "/embeddings" in endpoint else f"{endpoint.rstrip('/')}/v1/embeddings"
            headers = {"Content-Type": "application/json"}
            api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("AIM_EMBEDDING_API_KEY")
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            payload = {"model": model, "input": "aim doctor embedding probe"}
            if str(model).startswith("text-embedding-3"):
                payload["dimensions"] = TARGET_EMBEDDING_DIM
            started = time.perf_counter()
            resp = requests.post(url, json=payload, headers=headers, timeout=read_timeout)
            resp.raise_for_status()
            data = resp.json().get("data") or [{}]
            vec = data[0].get("embedding") or []
        elif ptype == "google":
            info["status"] = "configured"
            info["detail"] = "Google provider configured; live probe skipped"
            return info
        else:
            info["detail"] = f"unknown embedding_provider '{ptype}'"
            return info
    except Exception as exc:
        info["status"] = "offline"
        info["detail"] = f"{type(exc).__name__}: {exc}"
        return info

    info["latency_ms"] = round((time.perf_counter() - started) * 1000.0, 1)
    info["dim"] = len(vec)
    nonzero = bool(vec) and any(float(v) != 0.0 for v in vec)
    if info["dim"] != TARGET_EMBEDDING_DIM:
        info["status"] = "offline"
        info["detail"] = f"dimension mismatch (expected {TARGET_EMBEDDING_DIM}, got {info['dim']})"
    elif not nonzero:
        info["status"] = "offline"
        info["detail"] = "provider returned a zero vector"
    else:
        info["status"] = "ok"
    return info


def _compute_exit_code(has_errors, warning_count, strict):
    if has_errors:
        return 1
    if strict and warning_count:
        return 1
    return 0


def apply_fixes(root_dir):
    """Repair venv shebangs and create the managed A-Mail mailbox directory (#173)."""
    actions = []
    try:
        repaired = repair_venv_shebangs(root_dir)
    except Exception as exc:
        repaired = 0
        print(f"[WARNING] Venv shebang repair failed: {exc}")
    if repaired:
        actions.append(f"Repaired {repaired} stale venv script shebang(s).")

    mailbox_dir = os.environ.get("AIM_MAILBOX_DIR", "").strip() or os.path.expanduser("~/.aim/mailbox")
    if not os.path.isdir(mailbox_dir):
        try:
            os.makedirs(mailbox_dir, exist_ok=True)
            actions.append(f"Created A-Mail mailbox directory: {mailbox_dir}")
        except Exception as exc:
            print(f"[WARNING] Could not create A-Mail mailbox {mailbox_dir}: {exc}")

    return actions


def run_doctor(argv=None):
    parser = argparse.ArgumentParser(description="A.I.M. environment doctor")
    parser.add_argument("--fix", action="store_true", help="Repair venv shebangs and missing managed directories")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on warnings")
    parser.add_argument("--timeout", type=float, default=2.0, help="Embedding probe timeout in seconds")
    args = parser.parse_args(argv)

    print("--- A.I.M. DOCTOR ---")
    print("Validating environment...")

    has_errors = False
    warning_count = 0

    v = sys.version_info
    print(f"Python Version: {v.major}.{v.minor}.{v.micro}")
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        print("[ERROR] J.O.S.H.U.A. requires Python 3.10+")
        has_errors = True
    else:
        print("[OK] Python Version")

    core_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(core_dir)

    if os.path.exists(os.path.join(root_dir, "memory_lance")):
        print("[OK] Memory Subsystem")
    elif os.path.exists(os.path.join(root_dir, "assets", "default_lance")):
        print("[OK] Memory Subsystem (default_lance seed ready)")
    else:
        print("[WARNING] memory_lance directory not found! Run './aim index'.")
        warning_count += 1

    for pkg_name, import_name in (
        ("lancedb", "lancedb"),
        ("pandas", "pandas"),
        ("cryptography", "cryptography"),
        ("fastmcp", "fastmcp"),
    ):
        try:
            __import__(import_name)
            print(f"[OK] {pkg_name} installed")
        except ImportError:
            print(f"[ERROR] {pkg_name} not installed. Run: pip install -r joshua_os/requirements.txt")
            has_errors = True

    venv_bin = os.path.join(root_dir, "venv", "bin")
    if os.name != "nt" and os.path.isdir(venv_bin):
        stale_scripts = []
        for fname in sorted(os.listdir(venv_bin)):
            fpath = os.path.join(venv_bin, fname)
            if os.path.islink(fpath) or not os.path.isfile(fpath):
                continue
            try:
                with open(fpath, "rb") as fh:
                    head = fh.read(512)
            except OSError:
                continue
            if not head.startswith(b"#!") or b"\x00" in head:
                continue
            line1 = head.splitlines()[0][2:].decode("utf-8", errors="ignore").strip()
            if not line1 or line1.startswith("/usr/bin/env"):
                continue
            interp = line1[1 : line1.index('"', 1)] if (line1.startswith('"') and '"' in line1[1:]) else line1.split()[0]
            if os.path.basename(interp).lower().startswith("python") and not os.path.isfile(interp):
                stale_scripts.append(fname)
        if stale_scripts:
            print(
                f"[WARNING] Stale venv script shebangs ({', '.join(stale_scripts[:5])}). "
                "Run './aim update' or './aim doctor --fix' to repair."
            )
            warning_count += 1
        else:
            print("[OK] Virtualenv Entrypoints")

    # A-Mail inter-agent communication (non-blocking; Issue #181)
    amail_cli = shutil.which("aim-mail") or shutil.which("amail")
    mailbox_dir = os.environ.get("AIM_MAILBOX_DIR", "").strip() or os.path.expanduser("~/.aim/mailbox")
    if amail_cli:
        print(f"[OK] A-Mail CLI ({os.path.basename(amail_cli)})")
    else:
        print("[WARNING] A-Mail CLI not found (install aim-mailbox) — inter-agent mail unavailable")
        warning_count += 1
    if os.path.isdir(mailbox_dir):
        print("[OK] A-Mail Mailbox")
    else:
        print("[WARNING] A-Mail mailbox missing (run 'aim-mail register <agent> ...')")
        warning_count += 1

    # Embedding provider probe (Issue #173): the most common silent degradation.
    probe = probe_embedding_provider(timeout=args.timeout)
    label = f"{probe['provider']}:{probe['model']}"
    if probe["status"] == "ok":
        print(
            f"[OK] Embedding Provider ({label}, {probe['dim']}-dim, {probe['latency_ms']:.0f} ms)"
        )
    elif probe["status"] == "configured":
        print(f"[OK] Embedding Provider ({label}) — {probe['detail']}")
    else:
        reason = probe["detail"] or probe["status"]
        print(
            f"[WARNING] Embedding Provider ({label}) unreachable — semantic search degraded to lexical-only ({reason})."
        )
        warning_count += 1

    if args.fix:
        for action in apply_fixes(root_dir):
            print(f"[FIX] {action}")

    print("--- DOCTOR COMPLETE ---")
    return _compute_exit_code(has_errors, warning_count, args.strict)


def main(argv=None):
    return run_doctor(argv)


if __name__ == "__main__":
    sys.exit(run_doctor())
