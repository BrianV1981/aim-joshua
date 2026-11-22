import os
import json
import keyring
import requests
import sys
import sqlite3
import struct
import math
from google import genai

# --- CONFIGURATION (Dynamic Load) ---
from config_utils import CONFIG, AIM_ROOT, PROJECT_ROOT, CONFIG_PATH

# --- PROVIDER LOGIC ---
TARGET_EMBEDDING_DIM = 768
_DEFAULT_PROVIDER_TYPE = CONFIG['models'].get('embedding_provider', 'local')  # google, local (ollama), openai-compat
_DEFAULT_PROVIDER_MODEL = CONFIG['models'].get('embedding', 'nomic-embed-text')
_DEFAULT_PROVIDER_ENDPOINT = CONFIG['models'].get('embedding_endpoint', 'http://127.0.0.1:11434/api/embeddings')

PROVIDER_TYPE = _DEFAULT_PROVIDER_TYPE
PROVIDER_MODEL = _DEFAULT_PROVIDER_MODEL
PROVIDER_ENDPOINT = _DEFAULT_PROVIDER_ENDPOINT


def _resolve_active_embedding_settings():
    models_cfg = CONFIG.get('models', {}) if isinstance(CONFIG, dict) else {}
    ptype = PROVIDER_TYPE if PROVIDER_TYPE != _DEFAULT_PROVIDER_TYPE else models_cfg.get('embedding_provider', PROVIDER_TYPE)
    pmodel = PROVIDER_MODEL if PROVIDER_MODEL != _DEFAULT_PROVIDER_MODEL else models_cfg.get('embedding', PROVIDER_MODEL)
    pendpoint = (
        PROVIDER_ENDPOINT
        if PROVIDER_ENDPOINT != _DEFAULT_PROVIDER_ENDPOINT
        else models_cfg.get('embedding_endpoint', PROVIDER_ENDPOINT)
    )
    norm_type = (ptype or 'local').strip().lower()
    if norm_type == 'ollama':
        norm_type = 'local'
    return norm_type, pmodel, pendpoint


def _validate_and_normalize_vector(vec, model_label: str, *, l2_normalize: bool = False):
    if vec is None:
        return None
    floats = [float(v) for v in vec]
    if len(floats) != TARGET_EMBEDDING_DIM:
        sys.stderr.write(
            f"Embedding dimension mismatch for '{model_label}': expected {TARGET_EMBEDDING_DIM}, got {len(floats)}.\n"
        )
        return None
    if l2_normalize:
        norm = math.sqrt(sum(v * v for v in floats))
        if norm > 0.0:
            floats = [v / norm for v in floats]
    return floats


def summarize_massive_turn(text, model_name="qwen3.5:4b"):
    import hashlib
    import time
    import json
    import os
    import requests
    from config_utils import AIM_ROOT, PROJECT_ROOT
    CACHE_FILE = os.path.join(AIM_ROOT, "archive", "massive_turn_cache.json")
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
        except Exception:
            pass
            
    if text_hash in cache:
        return cache[text_hash]
        
    print(f"  [RAG 4.0] Extracting Semantic Anchor for massive chunk ({len(text)} chars)...")
    
    prompt = f"Summarize the core technical actions, decisions, and facts in the following massive text block. This summary will be used for semantic vector search, so ensure key nouns and entities are preserved. Do not include conversational filler.\n\nTEXT:\n{text}"
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": 32000
        }
    }
    
    for attempt in range(3):
        try:
            res = requests.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=300)
            if res.status_code == 429:
                print(f"  [API RATE LIMIT HIT] Sleeping for 60 seconds (Attempt {attempt+1}/3)...")
                time.sleep(60)
                continue
            res.raise_for_status()
            summary = res.json().get("response", "").strip()
            
            cache[text_hash] = summary
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache, f)
            time.sleep(3) # Mandatory anti-429 cooldown
            return summary
        except Exception as e:
            print(f"  [ERROR] Summarization failed: {e}")
            time.sleep(5)
            
    return text[:300] + " ... [MASSIVE TEXT OMITTED] ... " + text[-300:]


def get_embedding(text, task_type='RETRIEVAL_DOCUMENT'):
    """
    Unified entry point for 768-dim embeddings. Supports:
    - google: Gemini Embedding API (with output_dimensionality=768 + L2 normalization)
    - local: Ollama Native API (e.g. nomic-embed-text)
    - openai-compat: Standard OpenAI Embedding API (passes dimensions=768 on text-embedding-3-*)
    """
    if not text:
        return None

    provider_type, provider_model, provider_endpoint = _resolve_active_embedding_settings()

    # 1. GOOGLE PROVIDER
    if provider_type == 'google':
        api_key = keyring.get_password("aim-system", "google-api-key")
        if not api_key:
            sys.stderr.write("Error: Google API Key not found in keyring.\n")
            return None
        try:
            client = genai.Client(api_key=api_key)
            embed_model = provider_model or "gemini-embedding-001"
            result = client.models.embed_content(
                model=embed_model,
                contents=text,
                config={
                    'task_type': task_type,
                    'output_dimensionality': TARGET_EMBEDDING_DIM,
                },
            )
            return _validate_and_normalize_vector(
                result.embeddings[0].values,
                embed_model,
                l2_normalize=True,
            )
        except Exception as e:
            sys.stderr.write(f"Google Embedding Error: {e}\n")
            return None

    # 2. OLLAMA PROVIDER (Native)
    elif provider_type == 'local':
        import time
        max_retries = 5
        base_delay = 1
        for attempt in range(max_retries):
            try:
                payload = {"model": provider_model, "prompt": text}
                response = requests.post(provider_endpoint, json=payload, timeout=(0.5, 15))
                response.raise_for_status()
                raw_vec = response.json().get('embedding')
                return _validate_and_normalize_vector(raw_vec, provider_model or "ollama")
            except Exception as e:
                # Fail-fast if the local server is down
                if isinstance(e, requests.exceptions.ConnectionError):
                    sys.stderr.write(f"Ollama server unreachable: {e}\n")
                    return None

                if attempt == max_retries - 1:
                    sys.stderr.write(f"Ollama Embedding Error after {max_retries} attempts: {e}\n")
                    return None
                time.sleep(base_delay * (2 ** attempt))

    # 3. OPENAI-COMPATIBLE PROVIDER
    elif provider_type == 'openai-compat':
        api_key = (
            keyring.get_password("aim-system", "embedding-api-key")
            or keyring.get_password("aim-system", "openai-api-key")
            or ""
        )
        try:
            # Note: Standard OpenAI format is /v1/embeddings
            url = (
                provider_endpoint
                if "/embeddings" in provider_endpoint
                else f"{provider_endpoint.rstrip('/')}/v1/embeddings"
            )
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            payload = {"model": provider_model, "input": text}
            if str(provider_model or "").startswith("text-embedding-3"):
                payload["dimensions"] = TARGET_EMBEDDING_DIM
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            raw_vec = response.json()['data'][0]['embedding']
            return _validate_and_normalize_vector(raw_vec, provider_model or "openai-compat")
        except Exception as e:
            sys.stderr.write(f"OpenAI-Compat Embedding Error: {e}\n")
            return None

    return None

def cosine_similarity(v1, v2):
    if not v1 or not v2 or len(v1) != len(v2): return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = math.sqrt(sum(a * a for a in v1))
    magnitude2 = math.sqrt(sum(b * b for b in v2))
    if magnitude1 == 0 or magnitude2 == 0: return 0.0
    return dot_product / (magnitude1 * magnitude2)

def chunk_text(text, chunk_min=500, chunk_max=1500):
    """
    RAG 5.21 Length-Constrained Accumulator (Markdown/Flight Recorder Aligned).
    Splits long text strictly at block boundaries (double-newlines), ensuring
    chunks stay between chunk_min and chunk_max to prevent semantic dilution while
    preserving speaker headers and complete paragraphs.
    """
    if not text:
        return []
        
    blocks = [b.strip() for b in text.split('\n\n') if b.strip()]
    chunks = []
    current_chunk = []
    current_len = 0
    
    for block in blocks:
        # Include double-newline character in length calculation (except for first block)
        block_len = len(block) + (2 if current_len > 0 else 0)
        
        # If a single block is massive (e.g., base64 string or giant paragraph), we must break it forcibly
        if block_len > chunk_max:
            # Flush what we have so far
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_len = 0
                
            # Chunk the massive block directly
            start = 0
            while start < len(block):
                end = start + chunk_max
                chunks.append(block[start:end])
                start += chunk_max
            continue
            
        # If adding this block exceeds the max, and we have reached minimum density, flush
        if current_len + block_len > chunk_max and current_len >= chunk_min:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = []
            current_len = 0
            # Recalculate without leading double-newline for the new chunk
            block_len = len(block)
            
        current_chunk.append(block)
        current_len += block_len
        
    # Flush remaining
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
        
    return chunks
