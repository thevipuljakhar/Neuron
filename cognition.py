"""
NEURON v15 — Cognition Layer ("the hippocampus")

The architectural north star of P15: give Neuron temporal awareness and belief
revision so it becomes *more certain about fewer things* instead of encyclopedic
and overconfident. This module is the brain's consolidation machinery:

  B1  Diff Engine        — "what changed since yesterday": status transitions,
                           CEA capacity deltas, brand-new tenders, newly-seen
                           companies. Stored per-day in v15_daily_delta.
  B2  Belief State       — v15_beliefs: Neuron's current understanding of a small
                           set of key metrics, sourced from the authoritative CEA
                           snapshot, with confidence, provenance and a revision
                           trail. A large jump raises a BELIEF_CONFLICT.
  B3  Attention          — pure-heuristic unusualness scoring (anomaly clustering,
                           news velocity, repeat-actor co-occurrence). No LLM.
  B4  Consolidation      — the nightly "sleep cycle": run B1+B2+B3, weaken stale
                           memories by *tagging them dormant* (NEVER deleting —
                           the ledger is permanent living memory), and emit a
                           short night_memo the Synthesis Desk reads as context.
  C2  Self-test          — in-process invariant suite, no network, returns a
                           structured pass/fail report for /api/self_test.

MEMBRANE (the security POV's "content isolation", delivered as a module boundary):
this layer reads ONLY shared SQLite + sources.py query helpers. It deliberately
imports neither neuron.py (no fetchers, no Flask) nor intelligence.py (no NVIDIA
key). A bug or a poisoned article here can update a belief or a memo — it can
never reach a raw fetcher or an outbound LLM call. The eventual neuron_think.py
process split (plan B5) lifts this file unchanged.
"""
import json
import sqlite3
import time
from datetime import datetime

import sources as obs

DB_PATH = obs.DB_PATH

# Beliefs are seeded ONLY from data Neuron already persists authoritatively.
# metric -> (cea_national_snap column, unit, human label). Keeping this list
# short is the point: precise and auditable beats broad and shaky.
_BELIEF_DEFS = [
    ("india_re_total_gw", "re_total_mw", "GW", "India total RE installed (incl. large hydro)"),
    ("india_solar_gw",    "solar_mw",    "GW", "India solar installed"),
    ("india_wind_gw",     "wind_mw",     "GW", "India wind installed"),
    ("india_hydro_gw",    "hydro_mw",    "GW", "India hydro installed"),
]
_BELIEF_SOURCE = "CEA national snapshot"
# Revision thresholds (fraction): a move past REVISE logs a revision; a move past
# CONFLICT additionally raises a BELIEF_CONFLICT for the user to adjudicate.
_REVISE_FRAC = 0.005
_CONFLICT_FRAC = 0.10
_DORMANT_DAYS = 60


def init_cognition_tables():
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.execute("""CREATE TABLE IF NOT EXISTS v15_beliefs(
        metric TEXT PRIMARY KEY, value REAL, unit TEXT, label TEXT,
        confidence TEXT, source TEXT, as_of TEXT,
        last_revised TEXT, revision_count INTEGER DEFAULT 0,
        conflict INTEGER DEFAULT 0, note TEXT, updated_ts REAL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS v15_belief_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT, metric TEXT,
        old_value REAL, new_value REAL, delta_pct REAL,
        source TEXT, as_of TEXT, ts REAL, note TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS v15_daily_delta(
        delta_date TEXT PRIMARY KEY, run_ts REAL,
        summary TEXT, night_memo TEXT, payload TEXT)""")
    con.commit(); con.close()


# ── B2 — Belief state ─────────────────────────────────────────────────────────
def _latest_snaps(limit=2):
    """The most-recent CEA national snapshots, newest first (up to `limit`)."""
    con = sqlite3.connect(DB_PATH, timeout=15)
    try:
        rows = con.execute(
            "SELECT snap_date, re_total_mw, solar_mw, wind_mw, hydro_mw, ts "
            "FROM cea_national_snap ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    except Exception:
        rows = []
    con.close()
    cols = ("snap_date", "re_total_mw", "solar_mw", "wind_mw", "hydro_mw", "ts")
    return [dict(zip(cols, r)) for r in rows]


def update_beliefs():
    """Reconcile each tracked belief against the latest CEA snapshot. Returns a
    list of {metric, action, ...} describing seeds / revisions / conflicts."""
    init_cognition_tables()
    snaps = _latest_snaps(1)
    if not snaps:
        return []
    snap = snaps[0]
    as_of = snap.get("snap_date") or ""
    now = time.time()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    events = []
    con = sqlite3.connect(DB_PATH, timeout=15)
    for metric, col, unit, label in _BELIEF_DEFS:
        mw = snap.get(col)
        if mw is None:
            continue
        new_val = round(mw / 1000.0, 2)   # MW -> GW
        row = con.execute(
            "SELECT value, revision_count FROM v15_beliefs WHERE metric=?",
            (metric,)).fetchone()
        if row is None:
            con.execute(
                "INSERT INTO v15_beliefs(metric,value,unit,label,confidence,source,"
                "as_of,last_revised,revision_count,conflict,note,updated_ts) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (metric, new_val, unit, label, "HIGH", _BELIEF_SOURCE, as_of,
                 now_str, 0, 0, "seeded from CEA snapshot", now))
            events.append({"metric": metric, "action": "seeded", "value": new_val})
            continue
        old_val, rev = row[0], row[1] or 0
        frac = abs(new_val - (old_val or 0)) / max(abs(old_val or 0), 1e-9)
        if frac < _REVISE_FRAC:
            # No material change — refresh provenance only, don't bump revisions.
            con.execute("UPDATE v15_beliefs SET as_of=?, updated_ts=? WHERE metric=?",
                        (as_of, now, metric))
            continue
        conflict = 1 if frac >= _CONFLICT_FRAC else 0
        note = (f"revised {old_val}->{new_val} {unit} ({frac*100:.1f}%) from {_BELIEF_SOURCE}"
                + (" — BELIEF_CONFLICT (large jump, verify source)" if conflict else ""))
        con.execute(
            "UPDATE v15_beliefs SET value=?, as_of=?, last_revised=?, "
            "revision_count=?, conflict=?, note=?, updated_ts=? WHERE metric=?",
            (new_val, as_of, now_str, rev + 1, conflict, note, now, metric))
        con.execute(
            "INSERT INTO v15_belief_history(metric,old_value,new_value,delta_pct,"
            "source,as_of,ts,note) VALUES (?,?,?,?,?,?,?,?)",
            (metric, old_val, new_val, round(frac * 100, 2), _BELIEF_SOURCE, as_of, now, note))
        events.append({"metric": metric, "action": "conflict" if conflict else "revised",
                       "old": old_val, "new": new_val, "delta_pct": round(frac * 100, 2)})
    con.commit(); con.close()
    return events


def upsert_belief(metric, value, unit, label, source, as_of, confidence="MEDIUM"):
    """Insert-or-revise an externally-sourced belief (e.g. IMF/EIA macro) with the
    same history + conflict tracking as the CEA-seeded ones. Network-free: the
    expression layer fetches the value and hands it in (membrane preserved)."""
    init_cognition_tables()
    if value is None:
        return {"metric": metric, "action": "skipped"}
    try:
        new_val = round(float(value), 4)
    except (TypeError, ValueError):
        return {"metric": metric, "action": "skipped"}
    now = time.time(); now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    con = sqlite3.connect(DB_PATH, timeout=15)
    row = con.execute("SELECT value, revision_count FROM v15_beliefs WHERE metric=?",
                      (metric,)).fetchone()
    if row is None:
        con.execute(
            "INSERT INTO v15_beliefs(metric,value,unit,label,confidence,source,as_of,"
            "last_revised,revision_count,conflict,note,updated_ts) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (metric, new_val, unit, label, confidence, source, as_of, now_str, 0, 0,
             f"seeded from {source}", now))
        action = "seeded"
    else:
        old_val, rev = row[0], row[1] or 0
        frac = abs(new_val - (old_val or 0)) / max(abs(old_val or 0), 1e-9)
        if frac < _REVISE_FRAC:
            con.execute("UPDATE v15_beliefs SET as_of=?, source=?, updated_ts=? WHERE metric=?",
                        (as_of, source, now, metric))
            action = "refreshed"
        else:
            conflict = 1 if frac >= _CONFLICT_FRAC else 0
            note = (f"revised {old_val}->{new_val} {unit} ({frac*100:.1f}%) from {source}"
                    + (" — BELIEF_CONFLICT (verify source)" if conflict else ""))
            con.execute(
                "UPDATE v15_beliefs SET value=?, as_of=?, last_revised=?, revision_count=?, "
                "conflict=?, note=?, source=?, updated_ts=? WHERE metric=?",
                (new_val, as_of, now_str, rev + 1, conflict, note, source, now, metric))
            con.execute(
                "INSERT INTO v15_belief_history(metric,old_value,new_value,delta_pct,source,"
                "as_of,ts,note) VALUES (?,?,?,?,?,?,?,?)",
                (metric, old_val, new_val, round(frac * 100, 2), source, as_of, now, note))
            action = "conflict" if conflict else "revised"
    con.commit(); con.close()
    return {"metric": metric, "action": action, "value": new_val}


def beliefs_view():
    """All current beliefs + any standing conflicts, for /api/beliefs and health."""
    init_cognition_tables()
    con = sqlite3.connect(DB_PATH, timeout=15)
    rows = con.execute(
        "SELECT metric,value,unit,label,confidence,source,as_of,last_revised,"
        "revision_count,conflict,note FROM v15_beliefs ORDER BY metric").fetchall()
    con.close()
    keys = ("metric", "value", "unit", "label", "confidence", "source", "as_of",
            "last_revised", "revision_count", "conflict", "note")
    beliefs = [dict(zip(keys, r)) for r in rows]
    conflicts = [b for b in beliefs if b.get("conflict")]
    return {"beliefs": beliefs, "conflicts": conflicts,
            "count": len(beliefs), "conflict_count": len(conflicts),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")}


# ── ledger access (read-only here — corrections live in sources.py) ───────────
def _all_entities():
    cols = ("entity_id", "entity_type", "title", "first_seen", "last_seen",
            "status", "status_history", "state", "capacity_mw", "key_players")
    con = sqlite3.connect(DB_PATH, timeout=15)
    try:
        rows = con.execute(
            f"SELECT {','.join(cols)} FROM v14_entity_ledger").fetchall()
    except Exception:
        rows = []
    con.close()
    out = []
    for r in rows:
        d = dict(zip(cols, r))
        try: d["status_history"] = json.loads(d["status_history"]) if d["status_history"] else []
        except Exception: d["status_history"] = []
        try: d["key_players"] = json.loads(d["key_players"]) if d["key_players"] else []
        except Exception: d["key_players"] = []
        out.append(d)
    return out


# ── B1 — Diff engine ──────────────────────────────────────────────────────────
def _status_changes(entities, since_ts):
    """Status transitions recorded since `since_ts`, with the prior status."""
    changes = []
    for e in entities:
        hist = e["status_history"]
        for i, h in enumerate(hist):
            ts = h.get("ts") or 0
            if ts >= since_ts:
                prev = hist[i - 1]["status"] if i > 0 else None
                changes.append({
                    "title": e["title"], "state": e["state"],
                    "capacity_mw": e["capacity_mw"], "entity_type": e["entity_type"],
                    "from": prev, "to": h.get("status"),
                    "players": e["key_players"], "ts": ts})
    changes.sort(key=lambda c: -(c["ts"] or 0))
    return changes


def _cea_delta():
    snaps = _latest_snaps(2)
    if len(snaps) < 2:
        return None
    cur, prev = snaps[0], snaps[1]
    out = {"from": prev.get("snap_date"), "to": cur.get("snap_date"), "metrics": {}}
    for col, label in (("re_total_mw", "RE total"), ("solar_mw", "Solar"),
                       ("wind_mw", "Wind"), ("hydro_mw", "Hydro")):
        a, b = cur.get(col), prev.get(col)
        if a is not None and b is not None:
            out["metrics"][label] = {"delta_mw": round(a - b, 1),
                                     "from_mw": round(b, 1), "to_mw": round(a, 1)}
    return out


def _new_entities(entities, since_ts, etype):
    return [{"title": e["title"], "state": e["state"], "capacity_mw": e["capacity_mw"],
             "status": e["status"], "players": e["key_players"]}
            for e in entities
            if e["entity_type"] == etype and (e["first_seen"] or 0) >= since_ts]


def _new_companies(now):
    """Players appearing in the last 24h India wire that were absent in the prior
    24-72h window. Pure match against the curated player list (no NER)."""
    recent = obs.recent_articles(region="india", hours=24, limit=300)
    prior = obs.recent_articles(region="india", hours=72, limit=600)
    prior_cut = now - 24 * 3600

    def players_in(arts, only_before=None):
        seen = set()
        for a in arts:
            if only_before and (a.get("fetched_ts") or 0) >= only_before:
                continue
            txt = ((a.get("title") or "") + " " + (a.get("summary") or "")).lower()
            for p in obs._RE_PLAYERS:
                if p in txt:
                    seen.add(p.title())
        return seen

    now_players = players_in(recent)
    prior_players = players_in(prior, only_before=prior_cut)
    return sorted(now_players - prior_players)


# ── B3 — Attention / unusualness (pure heuristic, no LLM) ─────────────────────
def compute_attention():
    """Score what is *unusual*, not what is average — the thing a brain attends
    to. Reads the ledger + article velocity only. Each flag is auditable."""
    init_cognition_tables()
    now = time.time()
    entities = _all_entities()
    week_changes = _status_changes(entities, now - 7 * 86400)
    flags = []

    # 1. Status clustering: many entities moving to the same status in one state.
    cluster = {}
    for c in week_changes:
        key = (c["state"] or "India", c["to"])
        cluster.setdefault(key, []).append(c)
    for (state, status), items in cluster.items():
        if len(items) >= 3:
            flags.append({
                "type": "status_cluster", "score": min(100, 50 + 12 * len(items)),
                "text": f"{len(items)} {state} entities moved to '{status}' in 7 days",
                "evidence": [i["title"][:90] for i in items[:5]]})

    # 2. Repeat actor: one player driving several status changes this week.
    actor = {}
    for c in week_changes:
        for p in (c["players"] or []):
            actor.setdefault(p, []).append(c)
    for player, items in actor.items():
        if len(items) >= 3:
            flags.append({
                "type": "actor_burst", "score": min(100, 45 + 10 * len(items)),
                "text": f"{player} in {len(items)} pipeline status changes this week",
                "evidence": [f"{i['to']}: {i['title'][:70]}" for i in items[:5]]})

    # 3. News velocity: India wire running hot vs its trailing 7-day baseline.
    try:
        rv = obs.region_velocity().get("india", {})
        ratio = rv.get("ratio")
        if ratio and ratio >= 2.0:
            flags.append({
                "type": "velocity", "score": min(100, int(40 * ratio)),
                "text": f"India RE news velocity {ratio}x its 7-day baseline "
                        f"({rv.get('last24h')} articles/24h)",
                "evidence": []})
    except Exception:
        pass

    # 4. Fresh tender burst in the last 24h.
    new_t = _new_entities(entities, now - 86400, "tender")
    if len(new_t) >= 3:
        flags.append({
            "type": "tender_surge", "score": min(100, 50 + 10 * len(new_t)),
            "text": f"{len(new_t)} new tenders entered the pipeline in 24h",
            "evidence": [t["title"][:90] for t in new_t[:5]]})

    flags.sort(key=lambda f: -f["score"])
    return {"flags": flags, "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "engine": "unusualness heuristic v1 (ledger + velocity, no LLM)"}


def _dormant_entities(entities, now):
    """Memories with no fresh signal in _DORMANT_DAYS. We TAG and report these —
    we never delete them. The ledger is permanent; sleep only de-emphasises."""
    cut = now - _DORMANT_DAYS * 86400
    return [e for e in entities if (e["last_seen"] or 0) < cut]


# ── B1+B4 — Consolidation (the sleep cycle) ───────────────────────────────────
def _compose_memo(date_str, changes, cea, new_t, new_c, conflicts, attention, dormant_n):
    bits = [f"NIGHT MEMO {date_str}"]
    if changes:
        awarded = sum(1 for c in changes if c["to"] == "awarded")
        comm = sum(1 for c in changes if c["to"] == "commissioned")
        bits.append(f"{len(changes)} status change(s) in 24h"
                    + (f" ({awarded} awarded, {comm} commissioned)" if (awarded or comm) else ""))
    else:
        bits.append("no pipeline status changes in 24h")
    if cea and cea.get("metrics", {}).get("RE total"):
        d = cea["metrics"]["RE total"]["delta_mw"]
        bits.append(f"CEA RE total {('+' if d >= 0 else '')}{d:.0f} MW since {cea['from']}")
    if new_t:
        bits.append(f"{len(new_t)} new tender(s)")
    if new_c:
        bits.append("new in wire: " + ", ".join(new_c[:4]))
    if conflicts:
        bits.append(f"{len(conflicts)} BELIEF_CONFLICT(s) — verify")
    top = (attention.get("flags") or [])
    if top:
        bits.append("attention: " + top[0]["text"])
    if dormant_n:
        bits.append(f"{dormant_n} entity memory(ies) now dormant (>60d, retained)")
    return " · ".join(bits) + "."


def run_consolidation(force=False):
    """The sleep/consolidation pass (plan B4). Idempotent per calendar day unless
    `force`. Writes one v15_daily_delta row, refreshes beliefs, publishes the
    night_memo for the Synthesis Desk, and records a self-test result (C1)."""
    init_cognition_tables()
    now = time.time()
    date_str = datetime.now().strftime("%Y-%m-%d")

    if not force:
        con = sqlite3.connect(DB_PATH, timeout=15)
        existing = con.execute(
            "SELECT payload FROM v15_daily_delta WHERE delta_date=?", (date_str,)).fetchone()
        con.close()
        if existing:
            try:
                return json.loads(existing[0])
            except Exception:
                pass

    belief_events = update_beliefs()
    conflicts = [e for e in belief_events if e.get("action") == "conflict"]
    entities = _all_entities()
    changes = _status_changes(entities, now - 86400)
    cea = _cea_delta()
    new_t = _new_entities(entities, now - 86400, "tender")
    new_c = _new_companies(now)
    attention = compute_attention()
    dormant = _dormant_entities(entities, now)

    memo = _compose_memo(date_str, changes, cea, new_t, new_c, conflicts,
                         attention, len(dormant))
    summary = (f"{len(changes)} status changes · {len(new_t)} new tenders · "
               f"{len(new_c)} new companies · {len(conflicts)} belief conflicts · "
               f"{len(attention.get('flags', []))} attention flags")
    payload = {
        "delta_date": date_str, "run_ts": now,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "summary": summary, "night_memo": memo,
        "status_changes": changes, "cea_delta": cea,
        "new_tenders": new_t, "new_companies": new_c,
        "belief_events": belief_events, "belief_conflicts": conflicts,
        "attention": attention.get("flags", []),
        "dormant_entities": {"count": len(dormant),
                             "titles": [e["title"][:90] for e in dormant[:20]]},
    }

    con = sqlite3.connect(DB_PATH, timeout=15)
    con.execute(
        "INSERT OR REPLACE INTO v15_daily_delta(delta_date,run_ts,summary,night_memo,payload) "
        "VALUES (?,?,?,?,?)", (date_str, now, summary, memo, json.dumps(payload)))
    con.commit(); con.close()

    # Publish the memo where the Synthesis Desk reads it (sources.kv, no import
    # of intelligence.py needed — communication is through the shared store).
    obs.kv_set("night_memo", memo)
    obs.kv_set("last_consolidation", str(now))

    # C1 — fold a self-test into the nightly cycle so a quiet regression is
    # caught without anyone running smoke_test by hand.
    try:
        st = self_test()
        obs.kv_set("last_self_test", json.dumps(
            {"ts": now, "passed": st["passed"], "failed": st["failed"],
             "warned": st["warned"]}))
    except Exception:
        pass
    return payload


def get_today_delta(auto=True):
    """Return today's delta, computing it on first request if the nightly cycle
    hasn't run yet (so the endpoint works even right after a fresh boot)."""
    init_cognition_tables()
    date_str = datetime.now().strftime("%Y-%m-%d")
    con = sqlite3.connect(DB_PATH, timeout=15)
    row = con.execute(
        "SELECT payload FROM v15_daily_delta WHERE delta_date=?", (date_str,)).fetchone()
    con.close()
    if row:
        try:
            return json.loads(row[0])
        except Exception:
            pass
    if auto:
        return run_consolidation()
    return {"delta_date": date_str, "note": "not computed yet"}


def consolidation_status():
    last = obs.kv_get("last_consolidation")
    age = (time.time() - float(last)) if last else None
    return {"last_consolidation_ts": float(last) if last else None,
            "age_seconds": round(age) if age is not None else None,
            "stale": (age is None or age > 30 * 3600)}


# ── C2 — In-process self-test (no network) ────────────────────────────────────
def self_test():
    """Structured invariant suite for /api/self_test and the nightly cycle.
    Network-free: it exercises the DB, the registry and the cognition layer, so
    it can run from the worker thread without hammering the live routes."""
    checks = []

    def add(name, status, detail=""):
        checks.append({"name": name, "status": status, "detail": detail})

    # Belief sanity — refresh first so the suite reflects current data.
    try:
        update_beliefs()
        bv = beliefs_view()
        bm = {b["metric"]: b["value"] for b in bv["beliefs"]}
        re_gw = bm.get("india_re_total_gw")
        solar = bm.get("india_solar_gw")
        wind = bm.get("india_wind_gw")
        if re_gw is None:
            add("beliefs seeded", "warn", "no CEA snapshot yet")
        else:
            add("belief india_re_total_gw in 250-400", "pass" if 250 < re_gw < 400 else "fail",
                f"{re_gw} GW")
            add("belief solar < re_total", "pass" if (solar or 0) < re_gw else "fail",
                f"{solar} < {re_gw}")
            add("belief wind < re_total", "pass" if (wind or 0) < re_gw else "fail",
                f"{wind} < {re_gw}")
        add("belief conflicts surfaced", "pass",
            f"{bv['conflict_count']} standing conflict(s)")
    except Exception as e:
        add("beliefs", "fail", str(e)[:80])

    # Living-memory integrity — no impossible lifecycle regressions.
    try:
        st = obs.entity_ledger_stats()
        add("entity ledger: no orphan status jumps",
            "pass" if st.get("orphan_status_jumps", 0) == 0 else "fail",
            f"{st.get('orphan_status_jumps')} jumps / {st.get('total')} entities")
    except Exception as e:
        add("entity ledger", "fail", str(e)[:80])

    # Corpus present.
    try:
        con = sqlite3.connect(DB_PATH, timeout=15)
        n = con.execute("SELECT COUNT(*) FROM v11_articles").fetchone()[0]
        con.close()
        add("article corpus non-empty", "pass" if n > 0 else "fail", f"{n} articles")
    except Exception as e:
        add("article corpus", "fail", str(e)[:80])

    # Registry breadth invariant (matches smoke_test's contract).
    try:
        rc = obs.registry_counts()
        ok = rc.get("india", 0) >= 180 and rc.get("total", 0) >= 540
        add("source registry >= 540 (india >= 180)", "pass" if ok else "fail",
            f"india={rc.get('india')} total={rc.get('total')}")
    except Exception as e:
        add("source registry", "fail", str(e)[:80])

    # Worker heartbeat freshness (warn, not fail — it can be cold right after boot).
    try:
        hb = obs.kv_get("worker_heartbeat")
        age = (time.time() - float(hb)) if hb else None
        if age is None:
            add("ingestion heartbeat", "warn", "no heartbeat yet")
        else:
            add("ingestion heartbeat < 5 min", "pass" if age < 300 else "warn",
                f"{age:.0f}s old")
    except Exception as e:
        add("ingestion heartbeat", "warn", str(e)[:80])

    passed = sum(1 for c in checks if c["status"] == "pass")
    failed = sum(1 for c in checks if c["status"] == "fail")
    warned = sum(1 for c in checks if c["status"] == "warn")
    return {"checks": checks, "passed": passed, "failed": failed, "warned": warned,
            "verdict": "GREEN" if failed == 0 else "RED",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
