"""
Developer Center — module health, self-improvement, upgrade recommendations
Governs: Python module load status, file sizes, last-modified times, and
         generates structured upgrade proposals based on SWOT + system state.
"""
import sys, os, sqlite3, importlib, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import sources as _obs

CENTER_NAME = "Developer Center"
CENTER_ROLE = "Monitors all Python modules for load health, tracks file sizes and modification times, and generates structured upgrade proposals that feed into the SWOT email loop."

_ROOT = os.path.dirname(os.path.dirname(__file__))

CORE_MODULES = [
    ("neuron",         "neuron.py",         "Main Flask application + all API routes"),
    ("cognition",      "cognition.py",       "Belief state, delta engine, consolidation"),
    ("memory",         "memory.py",          "MemoryOS dual-hierarchy fact store"),
    ("decisions",      "decisions.py",       "Executive function — conviction-scored decisions"),
    ("intelligence",   "intelligence.py",    "Lead-lag, novelty radar, synthesis desk"),
    ("sources",        "sources.py",         "540+ source observatory + ingestion worker"),
    ("tender_intel",   "tender_intel.py",    "First-principles tender intelligence (v21)"),
    ("swot_engine",    "swot_engine.py",     "Self-analysis SWOT + email loop"),
    ("neuron_mcp",     "neuron_mcp.py",      "Model Context Protocol server interface"),
]


def _module_info(module_name: str, filename: str) -> dict:
    path = os.path.join(_ROOT, filename)
    exists = os.path.exists(path)
    size_kb = round(os.path.getsize(path) / 1024, 1) if exists else 0
    mtime = round(os.path.getmtime(path)) if exists else None

    loadable = False
    load_error = None
    try:
        importlib.import_module(module_name)
        loadable = True
    except Exception as e:
        load_error = str(e)[:120]

    return {
        "module": module_name,
        "file": filename,
        "role": next((m[2] for m in CORE_MODULES if m[0] == module_name), ""),
        "exists": exists,
        "size_kb": size_kb,
        "mtime": mtime,
        "loadable": loadable,
        "load_error": load_error,
    }


def status() -> dict:
    """Quick check — can all core modules be imported?"""
    failed = []
    for name, _, _ in CORE_MODULES:
        try:
            importlib.import_module(name)
        except Exception as e:
            failed.append({"module": name, "error": str(e)[:80]})

    return {
        "center": CENTER_NAME,
        "ok": len(failed) == 0,
        "modules_total": len(CORE_MODULES),
        "modules_failed": len(failed),
        "failures": failed,
    }


def _generate_upgrade_proposals() -> list:
    """Reads SWOT ledger and system state to produce structured upgrade proposals."""
    proposals = []
    con = sqlite3.connect(_obs.DB_PATH, timeout=10)

    # Proposal 1: failed sources
    try:
        n = con.execute("SELECT COUNT(*) FROM v11_source_health WHERE ok=0").fetchone()[0]
        if n > 3:
            proposals.append({
                "priority": "HIGH",
                "center": "Intelligence Center",
                "issue": f"{n} RSS/GDELT sources are failing",
                "evidence": "v11_source_health.ok=0",
                "action": "Audit sources.py — check dead RSS URLs and rotate Google News queries",
            })
    except Exception:
        pass

    # Proposal 2: belief conflicts
    try:
        n = con.execute("SELECT COUNT(*) FROM v15_beliefs WHERE conflict=1").fetchone()[0]
        if n > 0:
            proposals.append({
                "priority": "HIGH",
                "center": "Cognitive Center",
                "issue": f"{n} belief(s) in conflict state",
                "evidence": "v15_beliefs.conflict=1",
                "action": "Run /api/delta/run to force consolidation and adjudicate conflicts",
            })
    except Exception:
        pass

    # Proposal 3: memory facts below threshold
    try:
        n = con.execute("SELECT COUNT(*) FROM v16_facts").fetchone()[0]
        if n < 50:
            proposals.append({
                "priority": "MEDIUM",
                "center": "Cognitive Center",
                "issue": f"MemoryOS has only {n} curated facts — below healthy threshold",
                "evidence": "v16_facts COUNT < 50",
                "action": "Ingest more articles via /api/memory/add or run ingestion worker longer",
            })
    except Exception:
        pass

    # Proposal 4: no strong decisions
    try:
        n = con.execute(
            "SELECT COUNT(*) FROM v17_decision_ledger WHERE status='OPEN' AND band='STRONG'"
        ).fetchone()[0]
        if n == 0:
            proposals.append({
                "priority": "MEDIUM",
                "center": "Analyst Center",
                "issue": "No STRONG-conviction decisions currently open",
                "evidence": "v17_decision_ledger band=STRONG count=0",
                "action": "Check if chokepoints, lead-lag, and implication faculties have fresh data",
            })
    except Exception:
        pass

    # Proposal 5: module load failures
    s = status()
    for f in s.get("failures", []):
        proposals.append({
            "priority": "CRITICAL",
            "center": "Developer Center",
            "issue": f"Module '{f['module']}' cannot be imported",
            "evidence": f"ImportError: {f['error']}",
            "action": f"Fix import error in {f['module']}.py before restarting Neuron",
        })

    con.close()
    if not proposals:
        proposals.append({
            "priority": "LOW",
            "center": "All Centers",
            "issue": "No actionable upgrade needed",
            "evidence": "All checks nominal",
            "action": "System is healthy. Consider expanding source coverage or adding new belief metrics.",
        })

    return proposals


def report() -> dict:
    """Full developer report — module map + upgrade proposals."""
    out = {"center": CENTER_NAME, "role": CENTER_ROLE}

    out["modules"] = [_module_info(name, fname) for name, fname, _ in CORE_MODULES]
    out["upgrade_proposals"] = _generate_upgrade_proposals()
    out["status"] = status()
    return out
