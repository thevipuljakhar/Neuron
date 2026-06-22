"""
Cognitive Center — wraps cognition.py + memory.py
Governs: belief state, attention/anomaly scoring, daily delta,
         nightly consolidation, MemoryOS recall and ingestion.
"""
import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import sources as _obs

CENTER_NAME = "Cognitive Center"
CENTER_ROLE = "Maintains belief state (India RE GW totals), scores anomalies, tracks daily deltas, runs nightly consolidation, and manages the MemoryOS dual-hierarchy fact store."


def status() -> dict:
    """Lightweight health check — only DB reads, no computation."""
    con = sqlite3.connect(_obs.DB_PATH, timeout=10)

    belief_count = fact_count = conflict_count = 0
    last_consolidation = None
    try:
        belief_count  = con.execute("SELECT COUNT(*) FROM v15_beliefs").fetchone()[0]
        conflict_count = con.execute("SELECT COUNT(*) FROM v15_beliefs WHERE conflict=1").fetchone()[0]
    except Exception:
        pass
    try:
        fact_count = con.execute("SELECT COUNT(*) FROM v16_facts").fetchone()[0]
    except Exception:
        pass
    try:
        row = con.execute("SELECT date FROM v15_daily_delta ORDER BY date DESC LIMIT 1").fetchone()
        if row:
            last_consolidation = row[0]
    except Exception:
        pass
    con.close()

    return {
        "center": CENTER_NAME,
        "ok": True,
        "belief_count": belief_count,
        "belief_conflicts": conflict_count,
        "memory_facts": fact_count,
        "last_consolidation": last_consolidation,
    }


def report() -> dict:
    """Full cognitive state — beliefs, attention, memory stats."""
    import cognition as _cog
    import memory as _mem

    out = {"center": CENTER_NAME, "role": CENTER_ROLE}

    try:
        out["beliefs"] = _cog.beliefs_view()
    except Exception as e:
        out["beliefs"] = {"error": str(e)}

    try:
        out["attention"] = _cog.compute_attention()
    except Exception as e:
        out["attention"] = {"error": str(e)}

    try:
        out["delta"] = _cog.get_today_delta(auto=False)
    except Exception as e:
        out["delta"] = {"error": str(e)}

    try:
        out["memory_stats"] = _mem.memory_stats()
    except Exception as e:
        out["memory_stats"] = {"error": str(e)}

    out["status"] = status()
    return out
