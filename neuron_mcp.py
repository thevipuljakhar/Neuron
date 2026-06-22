"""
NEURON MCP — your own fast personal-memory server (P16.3)

Exposes Neuron's MemoryOS (memory.py) over the Model Context Protocol so ANY MCP
client (Claude Desktop, an IDE, another agent) can recall from it. Two scopes
share one fast engine but never mix:
  • scope="neuron" — the RE/energy/geopolitics/trade intelligence Neuron curates.
  • scope="drive"  — YOUR files/works, indexed on demand from folders you choose.

Run:           python neuron_mcp.py                 (stdio transport)
Register it with an MCP client by pointing the client at that command. Secrets
(.env, *.key/*.pem, anything named secret/token/password) are never indexed.

This is intentionally a SEPARATE process from the Neuron dashboard — same DB
(neuron.db), no Flask, no fetchers. It reuses the local bge-small embedder when
fastembed is present (semantic), else the numpy floor embedder (still works).
"""
import sys

try:
    from mcp.server.fastmcp import FastMCP
except Exception:
    print("MCP SDK not installed. Run:  pip install mcp", file=sys.stderr)
    raise SystemExit(1)

import memory as mem

# Wire the real local embedder if available (keeps drive search semantic too).
try:
    from fastembed import TextEmbedding
    _m = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    mem.set_embedder(lambda t: next(iter(_m.embed([t or ""]))),
                     "bge-small-en-v1.5",
                     batch_fn=lambda ts: list(_m.embed([t or "" for t in ts])))
except Exception:
    pass   # floor embedder — recall still works

app = FastMCP("neuron-memory")


@app.tool()
def memory_recall(query: str, k: int = 8, scope: str = "neuron") -> dict:
    """Recall what NEURON knows. scope='neuron' = RE/energy intelligence;
    scope='drive' = your own indexed files. Fuses semantic + keyword + recency."""
    return mem.recall(query, k=k, scope=scope)


@app.tool()
def drive_search(query: str, k: int = 8) -> dict:
    """Semantic search across the files you've indexed into drive memory."""
    return mem.recall(query, k=k, scope="drive")


@app.tool()
def drive_index(path: str, max_files: int = 2000) -> dict:
    """Index a folder of your files/works into drive memory (skips secrets,
    build/dependency dirs, and oversized files). Re-running is idempotent."""
    return mem.index_path(path, scope="drive", max_files=max_files)


@app.tool()
def memory_add(text: str, scope: str = "drive") -> dict:
    """Teach the memory a fact directly (a note, a decision, a preference)."""
    return mem.add_note(text, source="mcp", scope=scope)


@app.tool()
def memory_timeline(entity: str, k: int = 30, scope: str = "neuron") -> dict:
    """Chronological evolution of an entity/topic (oldest→newest)."""
    return mem.timeline(entity, k=k, scope=scope)


@app.tool()
def memory_stats() -> dict:
    """Counts by tier/kind/scope, vector count, and active embedder."""
    return mem.memory_stats()


if __name__ == "__main__":
    app.run()
