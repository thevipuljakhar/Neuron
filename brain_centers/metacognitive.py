"""
Master Meta-Cognitive Space — the central cortex governing all Brain Centers.

Analogy: like the cell wall in biology — a closed, protected space that
holds all centres together and decides which centre handles each need.
The Meta-Cognitive Space is NOT a passive aggregator: it routes queries,
weighs center health, identifies system-wide gaps, and emits a unified
brain-state view protected by the master key.

Access: all /api/brain routes require header X-Neuron-Key equal to the
value of NEURON_MASTER_KEY in your .env file.
"""
import sys, os, time, sqlite3, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import sources as _obs

# ── Master Key — loaded from environment, never hardcoded ────────────────────
# Set NEURON_MASTER_KEY in your .env file (same directory as neuron.py).
# Falls back to a random token on first run — set a real value in .env.
def _load_master_key() -> str:
    key = os.environ.get("NEURON_MASTER_KEY", "").strip()
    if key:
        return key
    # Try loading .env manually (mirrors neuron.py _load_dotenv)
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("NEURON_MASTER_KEY="):
                    return line.split("=", 1)[1].strip()
    return ""   # no key → all brain routes return 401

MASTER_KEY = _load_master_key()

# ── Import all centers ────────────────────────────────────────────────────────
# Each import is guarded so a broken center never crashes the meta space.
def _safe_import(name):
    try:
        return __import__(f"brain_centers.{name}", fromlist=[name])
    except Exception as e:
        return None

_ic  = None  # intelligence_center
_cc  = None  # cognitive_center
_ac  = None  # analyst_center
_dc  = None  # designer_center
_dev = None  # developer_center
_sc  = None  # security_center
_bc  = None  # backup_center
_cur = None  # curiosity_center

def _load_centers():
    global _ic, _cc, _ac, _dc, _dev, _sc, _bc, _cur
    _ic  = _safe_import("intelligence_center")
    _cc  = _safe_import("cognitive_center")
    _ac  = _safe_import("analyst_center")
    _dc  = _safe_import("designer_center")
    _dev = _safe_import("developer_center")
    _sc  = _safe_import("security_center")
    _bc  = _safe_import("backup_center")
    _cur = _safe_import("curiosity_center")

_load_centers()

# ── Routing map: keywords → center ───────────────────────────────────────────
_ROUTE_MAP = [
    (["signal", "novelty", "gdelt", "synthesis", "chokepoint", "early", "brief",
      "news", "intelligence", "lead", "lag"],               "intelligence_center"),
    (["belief", "attention", "memory", "recall", "fact", "consolidation",
      "delta", "cognition", "anomaly"],                     "cognitive_center"),
    (["decision", "conviction", "strong", "analyst", "scorecard",
      "long", "short", "hedge", "position"],                "analyst_center"),
    (["ui", "design", "template", "react", "surface", "cockpit",
      "css", "component", "theme"],                         "designer_center"),
    (["module", "import", "code", "upgrade", "developer", "fix",
      "error", "proposal", "health"],                       "developer_center"),
    (["security", "injection", "auth", "guard", "audit", "access",
      "key", "threat"],                                     "security_center"),
    (["backup", "restore", "snapshot", "db", "database", "integrity"],
                                                             "backup_center"),
    (["curious", "question", "wonder", "explore", "search", "thought",
      "agenda", "learn", "investigate", "insight", "think", "why", "how"],
                                                             "curiosity_center"),
]

CENTER_META = {
    "intelligence_center": {
        "name": "Intelligence Center",
        "role": "Early signals, novelty radar, synthesis desk, chokepoints",
        "module": _ic,
    },
    "cognitive_center": {
        "name": "Cognitive Center",
        "role": "Belief state, memory OS, attention, consolidation",
        "module": _cc,
    },
    "analyst_center": {
        "name": "Analyst Center",
        "role": "Conviction-scored decisions, scorecard, STRONG-call push",
        "module": _ac,
    },
    "designer_center": {
        "name": "Designer Center",
        "role": "UI surfaces, cockpit health, React/Flask audit",
        "module": _dc,
    },
    "developer_center": {
        "name": "Developer Center",
        "role": "Module health, upgrade proposals, self-improvement",
        "module": _dev,
    },
    "security_center": {
        "name": "Security Center",
        "role": "Prompt guard, auth log, threat level",
        "module": _sc,
    },
    "backup_center": {
        "name": "Backup Center",
        "role": "DB snapshots, restore, integrity checks",
        "module": _bc,
    },
    "curiosity_center": {
        "name": "Curiosity Center",
        "role": "Autonomous thinking — observations, questions, searches, insights, father communication",
        "module": _cur,
    },
}


# ── Core API ──────────────────────────────────────────────────────────────────

def verify_key(key: str) -> bool:
    """Constant-time key comparison."""
    import hmac
    return hmac.compare_digest(str(key), MASTER_KEY)


def route_query(query: str) -> dict:
    """
    Given a natural-language query, determine which center(s) should handle it.
    Returns ranked list with the primary center first.
    """
    q = query.lower()
    scores = {}
    for keywords, center in _ROUTE_MAP:
        hit = sum(1 for kw in keywords if kw in q)
        if hit:
            scores[center] = scores.get(center, 0) + hit

    if not scores:
        return {
            "query": query,
            "primary_center": "cognitive_center",
            "all_centers": [],
            "note": "No keywords matched — defaulting to Cognitive Center",
        }

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary = ranked[0][0]
    meta = CENTER_META.get(primary, {})

    return {
        "query": query,
        "primary_center": primary,
        "center_name": meta.get("name", primary),
        "center_role": meta.get("role", ""),
        "all_centers": [{"center": c, "relevance_score": s} for c, s in ranked],
    }


def center_health() -> dict:
    """Lightweight status from every center — no network calls, no heavy computation."""
    results = {}
    for key, meta in CENTER_META.items():
        mod = meta["module"]
        if mod is None:
            results[key] = {"center": meta["name"], "ok": False, "error": "module not loaded"}
            continue
        try:
            results[key] = mod.status()
        except Exception as e:
            results[key] = {"center": meta["name"], "ok": False, "error": str(e)[:120]}
    return results


def metacognitive_assessment(health: dict) -> dict:
    """
    The Meta-Cognitive Space evaluates overall brain health and emits
    a unified assessment: which centers are healthy, degraded, or critical.
    """
    healthy = degraded = critical = 0
    flags = []

    for key, h in health.items():
        if not h.get("ok", False):
            critical += 1
            flags.append({"center": h.get("center", key), "severity": "CRITICAL",
                          "note": h.get("error", "center unhealthy")})
        else:
            # Center-specific degradation checks
            if key == "cognitive_center" and h.get("belief_conflicts", 0) > 0:
                degraded += 1
                flags.append({"center": h["center"], "severity": "DEGRADED",
                              "note": f"{h['belief_conflicts']} belief conflict(s) unresolved"})
            elif key == "security_center" and h.get("threat_level") in ("ELEVATED", "HIGH"):
                degraded += 1
                flags.append({"center": h["center"], "severity": "DEGRADED",
                              "note": f"Threat level: {h['threat_level']}"})
            else:
                healthy += 1

    total = healthy + degraded + critical
    if critical > 0:
        overall = "CRITICAL"
    elif degraded > 1:
        overall = "DEGRADED"
    elif degraded == 1:
        overall = "CAUTION"
    else:
        overall = "NOMINAL"

    return {
        "overall_status": overall,
        "healthy_centers": healthy,
        "degraded_centers": degraded,
        "critical_centers": critical,
        "total_centers": total,
        "flags": flags,
    }


def full_brain_state() -> dict:
    """
    The complete view through the Master Meta-Cognitive Space.
    Returns: center health, meta assessment, latest SWOT, and DB stats.
    """
    ts = time.time()
    health = center_health()
    assessment = metacognitive_assessment(health)

    # Latest SWOT from swot_engine
    swot = {}
    try:
        import swot_engine
        swot = swot_engine.get_latest_swot()
    except Exception as e:
        swot = {"error": str(e)}

    # Quick DB telemetry
    db_info = {}
    try:
        con = sqlite3.connect(_obs.DB_PATH, timeout=10)
        tables = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        con.close()
        db_info = {
            "tables": tables,
            "size_kb": round(os.path.getsize(_obs.DB_PATH) / 1024, 1),
        }
    except Exception:
        pass

    return {
        "meta_cognitive_space": "Neuron 2.0 — Master Brain State",
        "ts": ts,
        "assessment": assessment,
        "center_health": health,
        "swot": swot,
        "db": db_info,
        "routing_hint": "POST /api/brain/route?q=<query> to identify which center handles your question",
    }


def brain_report(center_key: str) -> dict:
    """Get the full detailed report from a specific center."""
    meta = CENTER_META.get(center_key)
    if not meta:
        return {"error": f"Unknown center: {center_key}",
                "available": list(CENTER_META.keys())}
    mod = meta["module"]
    if mod is None:
        return {"center": meta["name"], "error": "center module not loaded"}
    try:
        return mod.report()
    except Exception as e:
        return {"center": meta["name"], "error": str(e)}
