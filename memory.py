"""
NEURON v16 — MemoryOS ("living memory")

Completes the owner's memory blueprint (Curation Agent → Dual-Hierarchy Graph →
Multi-Tier Cache → Sleep-Phase Consolidation), which is the MemoryOS design
(Kang et al., EMNLP 2025). P14/P15 already built curation (usefulness scoring +
entity extraction) and the sleep-phase (cognition.run_consolidation). This module
adds the two missing pieces and unifies them:

  • Curation Agent      — distils high-signal articles + ledger entities into
                          atomic MemoryFacts; drops filler.
  • Dual-Hierarchy      — every fact is indexed on a TIMELINE (event_ts +
                          entity link) AND in a SEMANTIC VECTOR space (v16_vectors).
  • Multi-tier (MemoryOS)— STM / MTM / LPM tiers + heat score; recall warms a
                          fact, consolidation promotes the hot / demotes the cold.
  • Unified recall      — ONE entrypoint fusing semantic (vector KNN) + keyword +
                          temporal + structured retrieval (the most robust pattern
                          per 2026 agent-memory benchmarks).

MEMBRANE: imports `sources` only and is **network-free by default** (the floor
embedder is pure-numpy), so cognition.py / neuron.py may import it without ever
reaching an outbound call. A better embedder (fastembed bge-small, or NVIDIA NIM)
is injected from the expression layer via set_embedder(); the vector store can be
moved to sqlite-vec later — both slot in behind recall()'s contract unchanged.

NEVER deletes a fact (no-delete rule): duplicates are MERGED (canonical_id link,
all provenance kept); cold facts are DEMOTED, not dropped.
"""
import hashlib
import json
import math
import re
import sqlite3
import time
from datetime import datetime

import numpy as np

import sources as obs

DB_PATH = obs.DB_PATH

# ── Embedder (pluggable; pure-numpy floor keeps the module network-free) ──────
_DIM = 256
_EMBEDDER = None            # set by set_embedder(); None ⇒ floor hash embedder
_EMBEDDER_NAME = "floor-hash-v1"
_EMBEDDER_BATCH = None      # optional batch embed fn (fastembed yields in order)
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_VEC_CACHE = {}             # scope -> {ids, mat, n, embedder}


def _tokens(text):
    return _TOKEN_RE.findall((text or "").lower())


def _floor_embed(text):
    """Signed char-3gram + word hashing → L2-normalised D-vector. Captures fuzzy
    lexical similarity (commission/-ed/-ing share grams); zero-dependency floor."""
    toks = _tokens(text)
    vec = np.zeros(_DIM, dtype=np.float32)
    if not toks:
        return vec
    s = " ".join(toks)
    feats = toks + [s[i:i + 3] for i in range(max(0, len(s) - 2))]
    for g in feats:
        h = int(hashlib.md5(g.encode("utf-8", "ignore")).hexdigest(), 16)
        vec[h % _DIM] += 1.0 if (h >> 8) & 1 else -1.0
    n = float(np.linalg.norm(vec))
    return (vec / n).astype(np.float32) if n > 0 else vec


def _embed(text):
    if _EMBEDDER is not None:
        try:
            v = np.asarray(_EMBEDDER(text), dtype=np.float32)
            n = float(np.linalg.norm(v))
            return (v / n).astype(np.float32) if n > 0 else v
        except Exception:
            pass
    return _floor_embed(text)


def set_embedder(fn, name, batch_fn=None):
    """Inject a real embedder (fastembed / NVIDIA NIM) from the expression layer.
    New facts embed with it; run reembed_all() to migrate existing vectors.
    `batch_fn(texts)->list[vec]` is an optional fast path for bulk re-embedding."""
    global _EMBEDDER, _EMBEDDER_NAME, _EMBEDDER_BATCH
    _EMBEDDER, _EMBEDDER_NAME, _EMBEDDER_BATCH = fn, name, batch_fn
    _VEC_CACHE.clear()


def embedder_name():
    return _EMBEDDER_NAME


def _embed_many(texts):
    if _EMBEDDER_BATCH is not None:
        try:
            res = []
            for v in _EMBEDDER_BATCH(texts):
                v = np.asarray(v, dtype=np.float32)
                n = float(np.linalg.norm(v))
                res.append((v / n).astype(np.float32) if n > 0 else v)
            if len(res) == len(texts):
                return res
        except Exception:
            pass
    return [_embed(t) for t in texts]


def reembed_all(batch=256):
    """Migrate vectors to the current embedder. Idempotent: only embeds facts
    lacking a current-embedder vector, so a steady-state call is a no-op."""
    init_memory_tables()
    con = sqlite3.connect(DB_PATH, timeout=30)
    rows = con.execute(
        "SELECT fact_id, scope, text FROM v16_facts WHERE fact_id NOT IN "
        "(SELECT fact_id FROM v16_vectors WHERE embedder=?)", (_EMBEDDER_NAME,)).fetchall()
    n = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        vecs = _embed_many([r[2] for r in chunk])
        for (fid, scope, _t), v in zip(chunk, vecs):
            _store_vector(con, fid, scope, v)
            n += 1
        con.commit()
    con.close()
    _VEC_CACHE.clear()
    return {"reembedded": n, "embedder": _EMBEDDER_NAME}


# ── Schema ────────────────────────────────────────────────────────────────────
_FACT_COLS = ("fact_id", "scope", "kind", "text", "entity_id", "state",
              "capacity_mw", "players", "category", "direction", "source_uid",
              "source_id", "event_ts", "created_ts", "tier", "heat",
              "access_count", "last_access", "canonical_id")


def init_memory_tables():
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.execute("""CREATE TABLE IF NOT EXISTS v16_facts(
        fact_id TEXT PRIMARY KEY, scope TEXT, kind TEXT, text TEXT,
        entity_id TEXT, state TEXT, capacity_mw REAL, players TEXT,
        category TEXT, direction TEXT, source_uid TEXT, source_id TEXT,
        event_ts REAL, created_ts REAL, tier TEXT, heat REAL DEFAULT 0,
        access_count INTEGER DEFAULT 0, last_access REAL, canonical_id TEXT)""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_v16_scope ON v16_facts(scope, canonical_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_v16_ts ON v16_facts(scope, event_ts)")
    con.execute("""CREATE TABLE IF NOT EXISTS v16_vectors(
        fact_id TEXT PRIMARY KEY, scope TEXT, dim INTEGER,
        embedder TEXT, vec BLOB)""")
    con.commit(); con.close()


def _fact_id(prefix, key):
    return prefix + hashlib.md5(key.encode("utf-8", "ignore")).hexdigest()[:16]


def _row_to_fact(r):
    d = dict(zip(_FACT_COLS, r))
    try: d["players"] = json.loads(d["players"]) if d["players"] else []
    except Exception: d["players"] = []
    return d


def _store_vector(con, fact_id, scope, vec):
    con.execute("INSERT OR REPLACE INTO v16_vectors(fact_id,scope,dim,embedder,vec) "
                "VALUES (?,?,?,?,?)",
                (fact_id, scope, int(vec.shape[0]), _EMBEDDER_NAME, vec.tobytes()))


def _upsert_fact(con, f, vec=None, replace=False):
    verb = "INSERT OR REPLACE" if replace else "INSERT OR IGNORE"
    cur = con.execute(
        f"{verb} INTO v16_facts({','.join(_FACT_COLS)}) "
        f"VALUES ({','.join('?' for _ in _FACT_COLS)})",
        tuple(json.dumps(f[c]) if c == "players" else f.get(c) for c in _FACT_COLS))
    if (cur.rowcount or replace) and vec is not None:
        _store_vector(con, f["fact_id"], f["scope"], vec)
    return cur.rowcount


# ── Curation Agent (tier 1) ───────────────────────────────────────────────────
def _distil_article(a):
    """Return a MemoryFact dict for a high-signal article, or None (filler)."""
    title = (a.get("title") or "").strip()
    text = (title + " " + (a.get("summary") or "")).lower()
    if not title:
        return None
    status, _ = obs._classify_status(text)
    cap = obs._extract_capacity_mw(text)
    state = obs._extract_state(text)
    players = obs._extract_players(text)
    # Signal gate: a fact needs a real-world anchor (status move, capacity,
    # a state, or a named player). Everything else is filler and is dropped.
    if not (status or cap or state or players):
        return None
    return {
        "fact_id": _fact_id("art_", a.get("uid") or (a.get("link") or "") + title),
        "scope": "neuron", "kind": "signal",
        "text": title[:280], "entity_id": None, "state": state,
        "capacity_mw": cap, "players": players,
        "category": a.get("category"), "direction": None,
        "source_uid": a.get("uid"), "source_id": a.get("source_id"),
        "event_ts": a.get("fetched_ts") or time.time(),
        "created_ts": time.time(), "tier": "MTM", "heat": 1.0,
        "access_count": 0, "last_access": None, "canonical_id": None,
    }


def _entity_facts(con):
    """Promote every living-memory entity to a durable LPM fact (instant recall
    even before any article is curated)."""
    rows = con.execute(
        "SELECT entity_id,entity_type,title,last_seen,status,state,capacity_mw,"
        "key_players,last_source_uid FROM v14_entity_ledger").fetchall()
    out = []
    for (eid, etype, title, last_seen, status, state, cap, players_json, uid) in rows:
        try: players = json.loads(players_json) if players_json else []
        except Exception: players = []
        cap_s = f"{cap:.0f} MW" if cap else ""
        txt = " · ".join(x for x in (
            (state or "India"), cap_s, etype, f"status:{status}",
            ("players: " + ", ".join(players)) if players else "",
            (title or "")[:140]) if x)
        out.append({
            "fact_id": "ent_" + eid, "scope": "neuron", "kind": "entity",
            "text": txt[:280], "entity_id": eid, "state": state,
            "capacity_mw": cap, "players": players, "category": etype,
            "direction": None, "source_uid": uid, "source_id": "v14_entity_ledger",
            "event_ts": last_seen or time.time(), "created_ts": time.time(),
            "tier": "LPM", "heat": 2.0, "access_count": 0,
            "last_access": None, "canonical_id": None})
    return out


def ingest_recent(article_limit=800):
    """Curation pass (pull-model — no push from sources.py ⇒ no circular import).
    Refresh entity facts + distil new high-signal India articles since a cursor."""
    init_memory_tables()
    con = sqlite3.connect(DB_PATH, timeout=20)
    n_ent = n_art = 0
    # 1. Entity ledger → LPM facts (always refreshed; cheap, ~dozens of rows)
    for f in _entity_facts(con):
        _upsert_fact(con, f, _embed(f["text"]), replace=True)
        n_ent += 1
    # 2. New India articles since cursor (bounded), oldest-first so cursor advances
    cursor = obs.kv_get("mem_curate_cursor")
    cursor = float(cursor) if cursor else (time.time() - 14 * 86400)
    rows = con.execute(
        "SELECT uid,source_id,region,category,title,link,summary,published_dt,tone,fetched_ts "
        "FROM v11_articles WHERE region='india' AND fetched_ts > ? "
        "ORDER BY fetched_ts ASC LIMIT ?", (cursor, article_limit)).fetchall()
    max_ts = cursor
    for r in rows:
        a = {"uid": r[0], "source_id": r[1], "region": r[2], "category": r[3],
             "title": r[4], "link": r[5], "summary": r[6], "fetched_ts": r[9]}
        max_ts = max(max_ts, r[9] or max_ts)
        f = _distil_article(a)
        if f and _upsert_fact(con, f, _embed(f["text"])):
            n_art += 1
    con.commit(); con.close()
    if rows:
        obs.kv_set("mem_curate_cursor", str(max_ts))
    _VEC_CACHE.clear()
    return {"entity_facts": n_ent, "article_facts_new": n_art,
            "scanned": len(rows), "cursor": max_ts}


def _maybe_seed():
    init_memory_tables()
    con = sqlite3.connect(DB_PATH, timeout=15)
    n = con.execute("SELECT COUNT(*) FROM v16_facts").fetchone()[0]
    con.close()
    if n == 0:
        ingest_recent(article_limit=300)


def add_note(text, source="owner", scope="neuron"):
    """Manual fact — the owner teaching Neuron something directly."""
    init_memory_tables()
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "empty"}
    now = time.time()
    f = {"fact_id": _fact_id("note_", text + str(now)), "scope": scope,
         "kind": "note", "text": text[:280], "entity_id": None,
         "state": obs._extract_state(text.lower()),
         "capacity_mw": obs._extract_capacity_mw(text.lower()),
         "players": obs._extract_players(text.lower()), "category": "note",
         "direction": None, "source_uid": None, "source_id": source,
         "event_ts": now, "created_ts": now, "tier": "STM", "heat": 3.0,
         "access_count": 0, "last_access": None, "canonical_id": None}
    con = sqlite3.connect(DB_PATH, timeout=15)
    _upsert_fact(con, f, _embed(f["text"]), replace=True)
    con.commit(); con.close()
    _VEC_CACHE.clear()
    return {"ok": True, "fact_id": f["fact_id"], "text": f["text"]}


# ── Vector matrix (in-process cache; rebuilt when fact count changes) ─────────
def _load_matrix(con, scope):
    n = con.execute("SELECT COUNT(*) FROM v16_vectors WHERE scope=? AND embedder=?",
                    (scope, _EMBEDDER_NAME)).fetchone()[0]
    c = _VEC_CACHE.get(scope)
    if c and c["n"] == n and c["embedder"] == _EMBEDDER_NAME:
        return c["ids"], c["mat"]
    rows = con.execute("SELECT fact_id,vec FROM v16_vectors WHERE scope=? AND embedder=?",
                       (scope, _EMBEDDER_NAME)).fetchall()
    ids = [r[0] for r in rows]
    mat = (np.vstack([np.frombuffer(r[1], dtype=np.float32) for r in rows])
           if rows else np.zeros((0, _DIM), dtype=np.float32))
    _VEC_CACHE[scope] = {"ids": ids, "mat": mat, "n": n, "embedder": _EMBEDDER_NAME}
    return ids, mat


# ── Unified recall (semantic + keyword + temporal + structured) ───────────────
def recall(query, k=8, when=None, scope="neuron"):
    """The single 'what do I know about X' entrypoint. Fuses vector similarity,
    keyword overlap and recency; respects an optional temporal filter; warms the
    heat of returned facts. Returns ranked facts with full provenance."""
    _maybe_seed()
    query = (query or "").strip()
    con = sqlite3.connect(DB_PATH, timeout=15)
    ids, mat = _load_matrix(con, scope)
    qv = _embed(query)
    sims = (mat @ qv) if len(ids) else np.zeros(0)
    sim_by_id = {ids[i]: float(sims[i]) for i in range(len(ids))}
    rows = con.execute(
        f"SELECT {','.join(_FACT_COLS)} FROM v16_facts "
        f"WHERE scope=? AND canonical_id IS NULL", (scope,)).fetchall()
    qtoks = set(_tokens(query))
    now = time.time()
    scored = []
    for r in rows:
        f = _row_to_fact(r)
        if when and not (datetime.fromtimestamp(f["event_ts"] or 0)
                         .strftime("%Y-%m-%d").startswith(when)):
            continue
        cos = sim_by_id.get(f["fact_id"], 0.0)
        ftoks = set(_tokens(f["text"] + " " + (f["state"] or "") + " "
                            + " ".join(f["players"] or [])))
        kw = (len(qtoks & ftoks) / len(qtoks)) if qtoks else 0.0
        age_d = max(0.0, (now - (f["event_ts"] or now)) / 86400.0)
        rec = math.exp(-age_d / 30.0)
        score = 0.55 * cos + 0.25 * kw + 0.20 * rec
        scored.append((score, cos, kw, rec, f))
    scored.sort(key=lambda x: -x[0])
    top = scored[:k]
    # Warm the recalled facts (visitation heat — MemoryOS).
    for _, _, _, _, f in top:
        con.execute("UPDATE v16_facts SET heat=heat+1.0, access_count=access_count+1, "
                    "last_access=? WHERE fact_id=?", (now, f["fact_id"]))
    con.commit(); con.close()
    return {
        "query": query, "scope": scope, "count": len(top),
        "embedder": _EMBEDDER_NAME, "pool": len(rows),
        "results": [{
            "text": f["text"], "kind": f["kind"], "tier": f["tier"],
            "state": f["state"], "capacity_mw": f["capacity_mw"],
            "players": f["players"], "category": f["category"],
            "event_ts": f["event_ts"], "source_id": f["source_id"],
            "source_uid": f["source_uid"], "heat": round(f["heat"], 2),
            "score": round(sc, 4), "semantic": round(cos, 4),
            "keyword": round(kw, 4), "recency": round(rec, 4),
        } for sc, cos, kw, rec, f in top],
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


# ── Sleep-phase consolidation hook (dedup + decay + promotion) ────────────────
def consolidate(scope="neuron", dedup_window=1500, dup_threshold=0.93):
    """Called from the nightly cycle. Merges near-duplicate facts (canonical
    link, NOTHING deleted), decays heat, promotes hot/entity facts to LPM."""
    init_memory_tables()
    con = sqlite3.connect(DB_PATH, timeout=30)
    # 1. Semantic dedup over the most-recent canonical facts (bounded for O(n²)).
    rows = con.execute(
        "SELECT f.fact_id, f.event_ts, v.vec FROM v16_facts f "
        "JOIN v16_vectors v ON v.fact_id=f.fact_id "
        "WHERE f.scope=? AND f.canonical_id IS NULL AND v.embedder=? "
        "ORDER BY f.event_ts DESC LIMIT ?", (scope, _EMBEDDER_NAME, dedup_window)).fetchall()
    merged = 0
    if len(rows) > 1:
        ids = [r[0] for r in rows]
        ts = {r[0]: (r[1] or 0) for r in rows}
        mat = np.vstack([np.frombuffer(r[2], dtype=np.float32) for r in rows])
        sims = mat @ mat.T
        assigned = {}
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                if sims[i, j] >= dup_threshold:
                    a, b = ids[i], ids[j]
                    # First sighting (older event_ts) wins as canonical.
                    canon, dup = (a, b) if ts[a] <= ts[b] else (b, a)
                    canon = assigned.get(canon, canon)   # resolve chains to root
                    if dup != canon and dup not in assigned:
                        assigned[dup] = canon
        for dup, canon in assigned.items():
            con.execute("UPDATE v16_facts SET canonical_id=? WHERE fact_id=?", (canon, dup))
            merged += 1
    # 2. Heat decay + tier promotion (never delete — demotion only).
    con.execute("UPDATE v16_facts SET heat=heat*0.9 WHERE scope=?", (scope,))
    con.execute("UPDATE v16_facts SET tier='LPM' WHERE scope=? AND "
                "(heat>=3.0 OR kind='entity') AND canonical_id IS NULL", (scope,))
    con.execute("UPDATE v16_facts SET tier='MTM' WHERE scope=? AND tier='STM' "
                "AND created_ts < ?", (scope, time.time() - 2 * 86400))
    con.commit(); con.close()
    _VEC_CACHE.clear()
    return {"merged_duplicates": merged, "scope": scope}


# ── P16.3 — Generic curation for the portable drive memory (scope='drive') ────
# Lets the MCP server index the owner's own files/works into the same engine,
# kept in a separate `scope` so personal/work knowledge never mixes with Neuron's
# RE intelligence. Secrets are never indexed.
_TEXT_EXTS = {".md", ".txt", ".py", ".js", ".ts", ".json", ".rst", ".csv",
              ".yaml", ".yml", ".html", ".css", ".sql", ".sh", ".bat"}
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist",
              "build", ".next", "target", "graphify-out", ".idea", ".vscode"}
_SECRET_HINTS = ("secret", "token", "password", "credential", "id_rsa", ".env")
_SECRET_EXTS = (".key", ".pem", ".pfx", ".p12", ".crt")


def _chunks(text, size=500):
    out, buf = [], ""
    for para in re.split(r"\n\s*\n", text or ""):
        para = para.strip()
        if not para:
            continue
        if len(buf) + len(para) + 1 <= size:
            buf = (buf + " " + para).strip()
        else:
            if buf:
                out.append(buf)
            buf = para[:size] if len(para) > size else para
    if buf:
        out.append(buf)
    return out


def index_text(text, source, scope="drive", kind="doc", event_ts=None, max_chunks=200):
    """Curate arbitrary text into scoped memory facts (chunked + embedded)."""
    init_memory_tables()
    now = time.time()
    ev = event_ts or now
    con = sqlite3.connect(DB_PATH, timeout=30)
    n = 0
    for i, ch in enumerate(_chunks(text)[:max_chunks]):
        f = {"fact_id": _fact_id("doc_", source + "|" + str(i) + "|" + ch[:64]),
             "scope": scope, "kind": kind, "text": ch, "entity_id": None,
             "state": None, "capacity_mw": None, "players": [], "category": None,
             "direction": None, "source_uid": None, "source_id": source,
             "event_ts": ev, "created_ts": now, "tier": "MTM", "heat": 1.0,
             "access_count": 0, "last_access": None, "canonical_id": None}
        if _upsert_fact(con, f, _embed(ch)):
            n += 1
    con.commit(); con.close()
    _VEC_CACHE.clear()
    return n


def _is_secret(name):
    low = name.lower()
    return low.endswith(_SECRET_EXTS) or any(h in low for h in _SECRET_HINTS)


def index_path(root, scope="drive", exts=None, max_files=2000, max_bytes=200_000):
    """Walk a folder and curate its text/code/doc files into 'drive' memory.
    Skips build/dep dirs and anything that looks like a secret. Returns counts."""
    import os
    exts = set(e.lower() for e in exts) if exts else _TEXT_EXTS
    files = facts = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if files >= max_files:
                break
            ext = os.path.splitext(fn)[1].lower()
            if ext not in exts or _is_secret(fn):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(fp) > max_bytes:
                    continue
                with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                    txt = fh.read()
                if not txt.strip():
                    continue
                facts += index_text(txt, source=fp, scope=scope,
                                    event_ts=os.path.getmtime(fp))
                files += 1
            except Exception:
                continue
    return {"indexed_files": files, "facts": facts, "scope": scope, "root": root}


def timeline(query, k=30, scope="neuron"):
    """Chronological facts matching an entity/topic (oldest→newest) — the
    timeline half of the dual-hierarchy, for 'how did this evolve' questions."""
    init_memory_tables()
    q = (query or "").strip().lower()
    con = sqlite3.connect(DB_PATH, timeout=15)
    rows = con.execute(
        f"SELECT {','.join(_FACT_COLS)} FROM v16_facts WHERE scope=? AND "
        f"canonical_id IS NULL AND lower(text) LIKE ? ORDER BY event_ts ASC LIMIT ?",
        (scope, f"%{q}%", k)).fetchall()
    con.close()
    return {"query": query, "scope": scope,
            "events": [{"text": (f := _row_to_fact(r))["text"], "kind": f["kind"],
                        "event_ts": f["event_ts"], "source_id": f["source_id"]}
                       for r in rows]}


def memory_stats(scope=None):
    init_memory_tables()
    con = sqlite3.connect(DB_PATH, timeout=15)
    where = "" if scope is None else " WHERE scope=?"
    args = () if scope is None else (scope,)
    total = con.execute("SELECT COUNT(*) FROM v16_facts" + where, args).fetchone()[0]
    canon = con.execute("SELECT COUNT(*) FROM v16_facts" + (where + " AND" if where else " WHERE")
                        + " canonical_id IS NULL", args).fetchone()[0]
    by_tier = dict(con.execute("SELECT tier,COUNT(*) FROM v16_facts" + where
                               + " GROUP BY tier", args).fetchall())
    by_kind = dict(con.execute("SELECT kind,COUNT(*) FROM v16_facts" + where
                               + " GROUP BY kind", args).fetchall())
    by_scope = dict(con.execute("SELECT scope,COUNT(*) FROM v16_facts GROUP BY scope").fetchall())
    vecs = con.execute("SELECT COUNT(*) FROM v16_vectors").fetchone()[0]
    cur = obs.kv_get("mem_curate_cursor")
    con.close()
    return {"total_facts": total, "canonical_facts": canon,
            "merged_duplicates": total - canon, "vectors": vecs,
            "by_tier": by_tier, "by_kind": by_kind, "by_scope": by_scope,
            "embedder": _EMBEDDER_NAME, "dim": _DIM,
            "curate_cursor": float(cur) if cur else None,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
