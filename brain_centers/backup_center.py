"""
Backup Center — DB snapshot, restore, and data integrity
Governs: timestamped SQLite backups, backup history, table-count integrity
         checks, and safe restore with confirmation gate.
"""
import sys, os, sqlite3, shutil, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import sources as _obs

CENTER_NAME = "Backup Center"
CENTER_ROLE = "Creates timestamped SQLite backups, verifies data integrity, and provides safe restore with a confirmation token. No data is ever permanently deleted — backups are append-only."

_ROOT    = os.path.dirname(os.path.dirname(__file__))
_BKP_DIR = os.path.join(_ROOT, "backups")
_BKP_TABLE = "v23_backup_log"


def _init():
    os.makedirs(_BKP_DIR, exist_ok=True)
    con = sqlite3.connect(_obs.DB_PATH, timeout=10)
    con.execute(f"""CREATE TABLE IF NOT EXISTS {_BKP_TABLE} (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        ts        REAL    NOT NULL,
        filename  TEXT    NOT NULL,
        size_kb   REAL,
        tables_n  INTEGER,
        note      TEXT
    )""")
    con.commit()
    con.close()


def _db_table_count() -> int:
    try:
        con = sqlite3.connect(_obs.DB_PATH, timeout=10)
        n = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        con.close()
        return n
    except Exception:
        return -1


def status() -> dict:
    """Lightweight backup health check."""
    _init()
    db_size_kb = 0
    try:
        db_size_kb = round(os.path.getsize(_obs.DB_PATH) / 1024, 1)
    except Exception:
        pass

    last_backup = None
    backup_count = 0
    try:
        con = sqlite3.connect(_obs.DB_PATH, timeout=10)
        row = con.execute(f"SELECT ts, filename FROM {_BKP_TABLE} ORDER BY ts DESC LIMIT 1").fetchone()
        backup_count = con.execute(f"SELECT COUNT(*) FROM {_BKP_TABLE}").fetchone()[0]
        con.close()
        if row:
            last_backup = {"ts": row[0], "file": row[1]}
    except Exception:
        pass

    return {
        "center": CENTER_NAME,
        "ok": True,
        "db_size_kb": db_size_kb,
        "table_count": _db_table_count(),
        "total_backups": backup_count,
        "last_backup": last_backup,
        "backup_dir": _BKP_DIR,
    }


def backup(note: str = "manual") -> dict:
    """Create a timestamped copy of neuron.db. Always additive — never removes old backups."""
    _init()
    ts_str = time.strftime("%Y%m%d_%H%M%S")
    filename = f"neuron_backup_{ts_str}.db"
    dest = os.path.join(_BKP_DIR, filename)

    try:
        shutil.copy2(_obs.DB_PATH, dest)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    size_kb  = round(os.path.getsize(dest) / 1024, 1)
    tables_n = _db_table_count()

    con = sqlite3.connect(_obs.DB_PATH, timeout=10)
    con.execute(
        f"INSERT INTO {_BKP_TABLE}(ts, filename, size_kb, tables_n, note) VALUES(?,?,?,?,?)",
        (time.time(), filename, size_kb, tables_n, note[:200])
    )
    con.commit()
    con.close()

    return {
        "ok": True,
        "filename": filename,
        "path": dest,
        "size_kb": size_kb,
        "tables": tables_n,
    }


def restore(filename: str, confirm_token: str) -> dict:
    """
    Restore neuron.db from a backup file.
    Requires confirm_token == "RESTORE_CONFIRMED" as a safety gate.
    Current DB is backed up before restore.
    """
    if confirm_token != "RESTORE_CONFIRMED":
        return {
            "ok": False,
            "error": "Safety gate: pass confirm_token='RESTORE_CONFIRMED' to proceed",
        }

    src = os.path.join(_BKP_DIR, filename)
    if not os.path.exists(src):
        return {"ok": False, "error": f"Backup file not found: {filename}"}

    # Back up current state first
    pre_backup = backup(note=f"pre-restore-of-{filename}")

    try:
        shutil.copy2(src, _obs.DB_PATH)
        return {
            "ok": True,
            "restored_from": filename,
            "pre_restore_backup": pre_backup.get("filename"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def report() -> dict:
    """Full backup report — history + integrity check."""
    _init()
    out = {"center": CENTER_NAME, "role": CENTER_ROLE}

    con = sqlite3.connect(_obs.DB_PATH, timeout=10)
    try:
        rows = con.execute(
            f"SELECT ts, filename, size_kb, tables_n, note FROM {_BKP_TABLE} ORDER BY ts DESC LIMIT 20"
        ).fetchall()
        out["backup_history"] = [
            {"ts": r[0], "file": r[1], "size_kb": r[2], "tables": r[3], "note": r[4]}
            for r in rows
        ]
    except Exception as e:
        out["backup_history"] = {"error": str(e)}
    con.close()

    # Integrity: list backup files vs log
    try:
        disk_files = sorted(os.listdir(_BKP_DIR)) if os.path.isdir(_BKP_DIR) else []
        out["backup_files_on_disk"] = len(disk_files)
    except Exception:
        out["backup_files_on_disk"] = -1

    out["status"] = status()
    return out
