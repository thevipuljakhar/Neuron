# NEURON Phase 16 — "God-Tier Memory + Jarvis Reach" session plan

Goal: make Neuron a Jarvis-class intelligence — human-like living memory + deeper
India-concentrated energy/power/RE/economics/geopolitics/trade cognition. Two
thrusts. Governed by `NEURON_DEV_PROTOCOL.md` (additive-only, backend, membrane,
prove-green, never-delete). Theme/World/RE-Components tabs untouched.

Researched against: MemoryOS (EMNLP 2025, arXiv:2506.06326 — the architecture
the owner's diagram is based on); 2026 agent-memory benchmarks (Mem0 / Zep-
Graphiti / Letta / Cognee); sqlite-vec; and four local repos —
OpenBB-develop (provider abstraction + `mcp_server` + EIA/IMF/FRED/OECD/ECB/
TradingEconomics providers), worldmonitor-main (ONNX-MiniLM embeddings +
IndexedDB vector-db worker, supply-chain chokepoint tracker, prediction markets,
command palette, cross-domain correlation worker), open-sustainable-technology
(curated RE/energy OSS + data orgs), public-apis (free API index).

---

## THRUST 1 — Living Memory (MemoryOS for Neuron + portable drive MCP)

The owner's diagram (Curation Agent → Dual-Hierarchy Graph → Multi-Tier Cache
MemoryOS → Sleep-Phase Consolidation) is ~70% already realized by P14+P15. This
phase completes it and makes it portable.

### What Neuron already has (do not rebuild)
- **Curation (tier 1):** `_usefulness_score`, `classify_article`,
  `_record_entity` already drop noise and distil high-signal facts.
- **Timeline half of tier 2:** `v14_entity_ledger.status_history` (lifecycle
  over time) + `v11_articles.fetched_ts` + v12 TF-IDF stories.
- **Multi-tier seed (tier 3):** in-mem `cache` (STM-ish) + `kv_store`/`v11_kv`.
- **Sleep-phase (tier 4):** `cognition.run_consolidation()` (P15) + entity dedup
  (`_find_existing_entity`).

### The gaps this phase closes
1. **Semantic Vector space (tier 2, missing).** No persistent embeddings, no
   KNN. Add it.
2. **Unified recall.** Recall is fragmented (FTS5 vs ledger vs stories). Add one
   multi-strategy entrypoint (semantic + keyword + temporal + structured fusion)
   — the pattern 2026 benchmarks call most robust.
3. **Explicit MemoryOS tiering with heat.** Formalize STM/MTM/LPM + heat-score
   promotion / FIFO-style demotion (MemoryOS) on durable facts.
4. **Portability.** Same engine over the owner's whole drive via a fast MCP
   server — "my own MCP fast server."

### 16.1 — Memory Core (EXECUTE THIS SESSION, zero new deps, GREEN)
New module **`memory.py`** = Neuron's MemoryOS. Membrane: imports `sources`
only, **network-free by default** (so `cognition.py` may import it safely).

- **Curation Agent** — `ingest_recent()`: pull-model (no push from sources.py →
  no circular import). Scans new high-signal `v11_articles` since a kv cursor +
  `v14_entity_ledger` rows, distils atomic **MemoryFacts** into `v16_facts`.
  Reuses existing scorers/extractors. Bounded per cycle (≤500) so first boot
  never blocks; nightly catches up.
- **Dual-Hierarchy index:**
  - *Timeline*: fact `ts` (event time) + `entity_id` link → temporal queries.
  - *Semantic*: one embedding per fact in `v16_vectors` (BLOB float32).
    **Floor embedder** = pure-numpy char-3gram hashed TF-IDF (D=256, L2-norm) —
    zero-dep, network-free, robust to morphology (commission/-ed/-ing share
    n-grams). `set_embedder(fn)` hook lets the expression layer inject a real
    embedder later (see 16.2).
- **Multi-tier (MemoryOS):** `tier` ∈ {STM, MTM, LPM} + `heat` on each fact.
  `recall()` bumps heat (visitation×recency). Consolidation promotes hot/entity-
  linked facts to LPM, decays cold ones. **Never deletes** (no-delete rule):
  "eviction" = demote + heat-decay, fact stays queryable (same spirit as P15
  dormant-not-delete).
- **Unified recall** — `recall(query, k, when=None, scope=)`: union of semantic
  KNN + FTS5 keyword + entity-ledger structured + timeline filter, fused
  (`0.5·cosine + 0.3·kw + 0.2·recency`), reranked (reuse NVIDIA rerank via a
  passed-in ranker, keyword fallback), returns facts with full provenance.
- **Consolidation hook** — `consolidate()`: semantic dedup (merge facts with
  cosine ≥ 0.93 into a `canonical_id`, keep all provenance), heat decay, tier
  promotion, re-embed merged canonicals. Called from the P15 nightly cycle.
- **Routes (neuron.py):** `GET /api/memory/recall?q=`, `GET /api/memory/stats`,
  `POST /api/memory/add` (manual note → fact). `memory.ingest_recent()` +
  `memory.consolidate()` called from the existing consolidation worker.
- **Tables (additive):** `v16_facts`, `v16_vectors`, `v16_mem_kv` (cursor).
- **smoke_test:** facts curated > 0, recall returns ranked list, vector dim
  consistent, no fact lost on dedup (canonical links intact), recall latency
  sane.

### 16.2 — Semantic upgrade (EXECUTED 2026-06-17 ✅)
Installed `fastembed==0.8.0`; bge-small-en-v1.5 (384-dim, local ONNX via the
present onnxruntime) wired as the active embedder (`neuron._init_embedder` →
`memory.set_embedder` with a batch fn). `memory.reembed_all()` migrates existing
vectors in a boot background thread (idempotent — only embeds facts lacking a
current-embedder vector). Recall quality jumped: low-keyword/high-semantic hits
now work (e.g. "overseas shipments of indian panels" → "India to track IMPORTS of
RE components", sem 0.71 / kw 0.2). Smoke GREEN. sqlite-vec still deferred (numpy
KNN is ~ms at this scale; revisit past ~20k facts).

### 16.2 — original note (STAGED — one pip install, documented)
- `pip install fastembed` → bge-small-en-v1.5 ONNX (onnxruntime already present)
  as the real embedder via `set_embedder()`. Re-embed `v16_facts` in background.
- `pip install sqlite-vec` → move `v16_vectors` KNN into a `vec0` virtual table
  (SIMD, scales to 100k+ facts). Floor path stays as fallback if the extension
  can't load. Both are drop-in behind the existing `recall()` contract.

### 16.3 — Portable Drive Memory MCP (EXECUTED 2026-06-17 ✅)
Installed `mcp==1.28.0`. Built `neuron_mcp.py` (FastMCP, stdio) over `memory.py`
with `scope` namespacing ('neuron' vs 'drive'). Tools: memory_recall,
drive_search, drive_index(path), memory_add, memory_timeline, memory_stats. Added
generic curation to memory.py: `index_text` (paragraph chunking + embed),
`index_path` (walks a folder, skips build/dep dirs + secrets, caps file size),
`timeline`. Verified: indexed 10 project docs → 314 drive facts, `.env` skipped
(0 facts), semantic drive search works, scopes separate (drive 314 / neuron
1520), server constructs with all 6 tools. To use: `python neuron_mcp.py` and
register that command with an MCP client; `drive_index("D:/path/to/your/work")`
to ingest your folders. Neuron dashboard never imports mcp.

### 16.3 — original note (STAGED — `pip install mcp`)
- New `neuron_mcp.py` (FastMCP, the MemoryOS-MCP pattern). Tools: `memory_recall`,
  `memory_add`, `memory_timeline`, `drive_index(path)`, `drive_search`. Reuses
  `memory.py` with a `scope` column ('neuron' vs 'drive') so personal/work
  knowledge is namespaced from RE intelligence. `drive_index` walks allowed
  folders, curates text/code/docs into facts (respects an allowlist; never
  indexes secrets/.env). Becomes the owner's "fast personal MCP server" any MCP
  client (Claude, IDE) can query. Guarded import → prints install hint if `mcp`
  absent (dormant until enabled, never breaks Neuron).

---

## THRUST 2 — Jarvis Cognition & Reach (India-first; STAGED, mined from repos)

Each item is additive (new fetcher + route + panel-optional), keyless or using
existing `.env` keys, India-concentrated. Prioritized; execute in later sub-
phases after 16.1 lands.

1. **Supply-chain chokepoint tracker** — EXECUTED 2026-06-17 ✅ (Phase 16.4).
   `intelligence.chokepoint_monitor()` → `/api/chokepoints`. Keyless: GDELT
   volume + 540-source corpus + lead-lag corroboration (NOT AIS — worldmonitor's
   needs a paid feed). Hormuz/Red Sea-Suez/Malacca/Panama cards with stress
   score, status (CALM/WATCH/ELEVATED/DISRUPTED), drivers, and India energy-
   import exposure. Degrades to corpus-only if GDELT down. Smoke GREEN (135s).
   See plan file `~/.claude/plans/sprightly-scribbling-anchor.md`.
2. **India macro/trade deepening** (from OpenBB providers, keyless/free):
   IMF + EIA + TradingEconomics for India CAD, crude import bill, coal/LNG
   imports, INR, policy-rate calendar — strengthen the economics/trade leg.
   Wrap as new `fetch_india_macro_plus()`; beliefs (v15) gain trade/CAD metrics.
3. **Prediction-market signal** (from worldmonitor `polymarket`): energy/geo
   event probabilities → cross-check `re_forecast`. `/api/forecast_markets`.
4. **Cross-domain correlation** (worldmonitor `analysis.worker`): formal
   correlation between commodity/FX/policy streams and RE equities — extend the
   existing correlation route with causal-lag tags from the lead-lag engine.
5. **Command palette / "ask anything"** (worldmonitor command palette): a single
   omnibox that routes to `memory.recall()` + `ask_neuron()` — the Jarvis voice.
   Backend-only contract now (route), UI later within sealed-theme constraints.
6. **Provider abstraction** (OpenBB pattern): if data sources keep growing,
   refactor fetchers behind a thin standardized `provider` contract — deferred,
   only if churn justifies it (Protocol §3: don't smuggle refactors into a phase).

OpenBB also ships an `mcp_server` extension and EIA/FRED/IMF/OECD/ECB providers —
reference implementations for 16.3 and item 2. open-sustainable-technology's
`organizations.csv` is a sourcing list for additional keyless RE/energy datasets.

---

## Execution order
1. **16.1 Memory Core** — this session. Plan→build `memory.py`→wire routes +
   worker hooks→backfill bounded→smoke GREEN→graphify+memory+guide.
2. 16.2 semantic upgrade (owner runs one pip install; re-embed in background).
3. 16.3 drive MCP server (`pip install mcp`).
4. Thrust 2 items 1→5 in priority order, each its own additive sub-phase + smoke.

## Hard constraints (carried from Protocol)
- Additive only; never delete facts/ledger/data (dedup merges, never drops).
- `memory.py` network-free by default; membrane intact (cognition may import it).
- No theme/CSS/HTML-structure edits. No new required dependency (16.1); optional
  deps degrade gracefully.
- Every new route gets a smoke invariant; full GREEN before "done."
