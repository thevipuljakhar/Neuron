"""
Security Center — prompt guard, auth tracking, audit trail
Governs: prompt-injection stats, /api/brain access log,
         failed auth attempts, and security health scoring.
"""
import sys, os, sqlite3, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import sources as _obs

CENTER_NAME = "Security Center"
CENTER_ROLE = "Monitors prompt-injection attempts, logs all /api/brain access (success and failure), and maintains an immutable audit trail of security events."

_ACCESS_TABLE = "v23_brain_access_log"


def _init_tables():
    con = sqlite3.connect(_obs.DB_PATH, timeout=10)
    con.execute(f"""CREATE TABLE IF NOT EXISTS {_ACCESS_TABLE} (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        ts        REAL    NOT NULL,
        ip        TEXT,
        endpoint  TEXT,
        granted   INTEGER DEFAULT 0,
        note      TEXT
    )""")
    con.commit()
    con.close()


def log_access(endpoint: str, granted: bool, ip: str = "", note: str = ""):
    """Record every /api/brain call — success or failure. Immutable audit."""
    _init_tables()
    con = sqlite3.connect(_obs.DB_PATH, timeout=10)
    con.execute(
        f"INSERT INTO {_ACCESS_TABLE}(ts, ip, endpoint, granted, note) VALUES(?,?,?,?,?)",
        (time.time(), ip[:64], endpoint[:120], int(granted), note[:200])
    )
    con.commit()
    con.close()


def status() -> dict:
    """Lightweight security health check."""
    _init_tables()
    con = sqlite3.connect(_obs.DB_PATH, timeout=10)

    injection_count = failed_auth = recent_granted = 0
    try:
        injection_count = con.execute("SELECT COUNT(*) FROM v15_prompt_guard_log").fetchone()[0]
    except Exception:
        pass
    try:
        failed_auth = con.execute(
            f"SELECT COUNT(*) FROM {_ACCESS_TABLE} WHERE granted=0"
        ).fetchone()[0]
    except Exception:
        pass
    try:
        since = time.time() - 86400
        recent_granted = con.execute(
            f"SELECT COUNT(*) FROM {_ACCESS_TABLE} WHERE granted=1 AND ts>?", (since,)
        ).fetchone()[0]
    except Exception:
        pass
    con.close()

    threat_level = "NOMINAL"
    if failed_auth > 20:
        threat_level = "ELEVATED"
    if injection_count > 50:
        threat_level = "HIGH"

    return {
        "center": CENTER_NAME,
        "ok": True,
        "threat_level": threat_level,
        "total_injection_attempts": injection_count,
        "total_failed_auth": failed_auth,
        "brain_access_granted_24h": recent_granted,
    }


def report() -> dict:
    """Full security report — recent events, injection hits, auth log."""
    _init_tables()
    out = {"center": CENTER_NAME, "role": CENTER_ROLE}

    con = sqlite3.connect(_obs.DB_PATH, timeout=10)

    # Recent prompt-guard hits
    try:
        rows = con.execute(
            "SELECT ts, source, pattern, snippet FROM v15_prompt_guard_log ORDER BY ts DESC LIMIT 20"
        ).fetchall()
        out["recent_injection_attempts"] = [
            {"ts": r[0], "source": r[1], "pattern": r[2], "snippet": r[3]} for r in rows
        ]
    except Exception as e:
        out["recent_injection_attempts"] = {"error": str(e)}

    # Recent /api/brain access log
    try:
        rows = con.execute(
            f"SELECT ts, ip, endpoint, granted, note FROM {_ACCESS_TABLE} ORDER BY ts DESC LIMIT 30"
        ).fetchall()
        out["brain_access_log"] = [
            {"ts": r[0], "ip": r[1], "endpoint": r[2], "granted": bool(r[3]), "note": r[4]}
            for r in rows
        ]
    except Exception as e:
        out["brain_access_log"] = {"error": str(e)}

    con.close()
    out["status"] = status()
    return out
