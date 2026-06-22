"""
Analyst Center — wraps decisions.py
Governs: conviction-scored decisions, faculty synthesis, decision ledger,
         self-grading scorecard, and Telegram push of STRONG calls.
"""
import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import sources as _obs

CENTER_NAME = "Analyst Center"
CENTER_ROLE = "Fuses intelligence from all faculties into ranked, falsifiable decisions with conviction scores (STRONG/HIGH/MODERATE/LOW). Maintains a self-grading ledger to track which calls were right."


def status() -> dict:
    """Lightweight check — counts from the decision ledger."""
    con = sqlite3.connect(_obs.DB_PATH, timeout=10)
    open_count = strong_count = confirmed = invalidated = 0
    try:
        open_count = con.execute(
            "SELECT COUNT(*) FROM v17_decision_ledger WHERE status='OPEN'"
        ).fetchone()[0]
        strong_count = con.execute(
            "SELECT COUNT(*) FROM v17_decision_ledger WHERE status='OPEN' AND band='STRONG'"
        ).fetchone()[0]
        confirmed = con.execute(
            "SELECT COUNT(*) FROM v17_decision_ledger WHERE status='CONFIRMED'"
        ).fetchone()[0]
        invalidated = con.execute(
            "SELECT COUNT(*) FROM v17_decision_ledger WHERE status='INVALIDATED'"
        ).fetchone()[0]
    except Exception:
        pass
    con.close()

    accuracy = None
    if confirmed + invalidated > 0:
        accuracy = round(confirmed / (confirmed + invalidated) * 100, 1)

    return {
        "center": CENTER_NAME,
        "ok": True,
        "open_decisions": open_count,
        "strong_decisions": strong_count,
        "confirmed": confirmed,
        "invalidated": invalidated,
        "historical_accuracy_pct": accuracy,
    }


def report() -> dict:
    """Full analyst output — top decisions + scorecard."""
    import decisions as _dec

    out = {"center": CENTER_NAME, "role": CENTER_ROLE}

    try:
        out["scorecard"] = _dec.decision_scorecard()
    except Exception as e:
        out["scorecard"] = {"error": str(e)}

    # Top decisions from ledger (no full synthesis — expensive; pull from DB)
    con = sqlite3.connect(_obs.DB_PATH, timeout=10)
    try:
        rows = con.execute(
            """SELECT decision_id, thesis, action, direction, conviction, band,
                      falsifier, created_ts
               FROM v17_decision_ledger
               WHERE status='OPEN'
               ORDER BY conviction DESC LIMIT 10"""
        ).fetchall()
        out["top_decisions"] = [
            {
                "id": r[0], "thesis": r[1], "action": r[2],
                "direction": r[3], "conviction": r[4], "band": r[5],
                "falsifier": r[6], "created_ts": r[7],
            }
            for r in rows
        ]
    except Exception as e:
        out["top_decisions"] = {"error": str(e)}
    finally:
        con.close()

    out["status"] = status()
    return out
