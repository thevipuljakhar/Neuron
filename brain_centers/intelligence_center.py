"""
Intelligence Center — wraps intelligence.py
Governs: early signals, novelty radar, synthesis desk, chokepoints,
         stories, standing questions, archive search.
"""
import sys, os, time, sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import sources as _obs

CENTER_NAME = "Intelligence Center"
CENTER_ROLE = "Detects early signals before the mainstream press, monitors global novelty via GDELT, synthesizes analyst briefs, and tracks geopolitical chokepoint risk."


def status() -> dict:
    """Lightweight health check — no network calls."""
    loaded = False
    try:
        import intelligence as _intel
        loaded = True
    except Exception as e:
        return {"center": CENTER_NAME, "ok": False, "error": str(e)}

    con = sqlite3.connect(_obs.DB_PATH, timeout=10)
    article_count = 0
    try:
        article_count = con.execute("SELECT COUNT(*) FROM v11_articles").fetchone()[0]
    except Exception:
        pass
    last_article_ts = None
    try:
        row = con.execute("SELECT ts FROM v11_articles ORDER BY ts DESC LIMIT 1").fetchone()
        if row:
            last_article_ts = row[0]
    except Exception:
        pass
    con.close()

    return {
        "center": CENTER_NAME,
        "ok": loaded,
        "article_count": article_count,
        "last_article_ts": last_article_ts,
        "faculties": ["early_signals", "novelty_radar", "synthesis_desk",
                      "chokepoints", "stories", "standing_questions"],
    }


def report() -> dict:
    """Full intelligence state — may make network calls (cached internally)."""
    import intelligence as _intel
    out = {"center": CENTER_NAME, "role": CENTER_ROLE}

    try:
        out["early_signals"] = _intel.early_signals()
    except Exception as e:
        out["early_signals"] = {"error": str(e)}

    try:
        out["novelty_radar"] = _intel.novelty_radar()
    except Exception as e:
        out["novelty_radar"] = {"error": str(e)}

    try:
        out["chokepoints"] = _intel.chokepoint_monitor()
    except Exception as e:
        out["chokepoints"] = {"error": str(e)}

    try:
        out["synthesis"] = _intel.synthesis_brief()
    except Exception as e:
        out["synthesis"] = {"error": str(e)}

    try:
        out["stories"] = _intel.cluster_stories(hours=24, limit=100)
    except Exception as e:
        out["stories"] = {"error": str(e)}

    out["status"] = status()
    return out
