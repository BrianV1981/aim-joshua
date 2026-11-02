# The DataJack Cartridge Protocol (Local Parquet ROM)

DataJack lets operators compile documentation or reference codebases once into portable Apache Arrow `.parquet` cartridges and mount them across local J.O.S.H.U.A. projects with zero database duplication.

## 1. The ROM vs. RAM Architecture
* **RAM (`joshua_os/memory_lance`):** The live, mutable LanceDB table where project-specific `AGENTS.md`, `memory-wiki/`, and `joshua_os_docs/` are indexed via `./aim index`.
* **ROM (`joshua_os/archive/cartridges/*.parquet`):** Portable, pre-embedded Parquet cartridges queried directly via PyArrow zero-copy reads during `search_lancedb` MCP and `./aim search` calls.

## 2. Compiling a Cartridge (`aim bake`)
`joshua_os/.aim_core/plugins/datajack/aim_bake.py` compiles supported text/code files (`.md`, `.markdown`, `.txt`, `.py`, `.rs`, `.js`, `.ts`, `.rst`) into a `.parquet` cartridge using local Ollama embeddings (`http://127.0.0.1:11434`).

```bash
# Start Ollama locally first (e.g., `ollama serve`), then compile:
./aim bake ./docs/framework-guide framework-guide.parquet \
  --author "Team" \
  --version "1.0.0" \
  --description "Framework reference manual"
```
Each file is split with the Length-Constrained Accumulator (`forensic_utils.chunk_text`), embedded into 768-dim float32 vectors, and written to `<output>.parquet` via `pyarrow.parquet`.

## 3. Mounting, Listing & Unmounting Cartridges
Cartridges are exchanged as standard `.parquet` files (via filesystem copy, Git releases, object storage, or internal artifact shares) and managed locally via `aim_exchange.py`:

```bash
# Mount a local .parquet cartridge into joshua_os/archive/cartridges/
./aim jack-in ./framework-guide.parquet

# List mounted cartridges
./aim exchange list

# Unmount (remove) a mounted cartridge by name or prefix
./aim unplug framework-guide
```
Once mounted, `retriever.py` automatically searches both `joshua_os/memory_lance` and every `.parquet` file in `joshua_os/archive/cartridges/`.
