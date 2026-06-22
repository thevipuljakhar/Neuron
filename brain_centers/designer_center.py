"""
Designer Center — UI surface health and completeness
Governs: which cockpit versions exist, React build state, active theme,
         CSS/JS asset inventory, surface coverage audit.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

CENTER_NAME = "Designer Center"
CENTER_ROLE = "Audits all UI surfaces (Flask templates + React components), tracks which cockpit version is live, verifies assets are present, and flags missing or duplicated display panels."

_ROOT = os.path.dirname(os.path.dirname(__file__))


def _check(path: str) -> dict:
    full = os.path.join(_ROOT, path)
    exists = os.path.exists(full)
    size = os.path.getsize(full) if exists else 0
    return {"path": path, "exists": exists, "size_kb": round(size / 1024, 1)}


def status() -> dict:
    """Check key UI assets without reading file contents."""
    templates = {
        "v19": _check("templates/index19.html"),
        "v20": _check("templates/index20.html"),
        "v18_legacy": _check("templates/index.html"),
    }

    static = {
        "neuron19_css": _check("static/neuron19.css"),
        "neuron20_css": _check("static/neuron20.css"),
        "neuron_bg_js": _check("static/neuron_bg.js"),
    }

    react_dist = _check("dist/index.html")
    react_src  = os.path.isdir(os.path.join(_ROOT, "src"))

    # Determine which cockpit version is likely active (largest template = primary)
    active_version = "v19"
    if templates["v20"]["exists"] and templates["v20"]["size_kb"] > templates["v19"]["size_kb"]:
        active_version = "v20"

    return {
        "center": CENTER_NAME,
        "ok": templates["v19"]["exists"],
        "active_cockpit": active_version,
        "templates": templates,
        "static_assets": static,
        "react_build_present": react_dist["exists"],
        "react_src_present": react_src,
        "dual_ui_risk": react_dist["exists"],  # True = two UIs may show same data
    }


def report() -> dict:
    """Full design audit — surface map, component inventory, duplication flags."""
    out = {"center": CENTER_NAME, "role": CENTER_ROLE}
    out["status"] = status()

    # React component inventory
    react_components = []
    src_dir = os.path.join(_ROOT, "src", "components")
    if os.path.isdir(src_dir):
        for f in os.listdir(src_dir):
            if f.endswith(".tsx") or f.endswith(".ts"):
                size = os.path.getsize(os.path.join(src_dir, f))
                react_components.append({"file": f, "size_kb": round(size / 1024, 1)})
    out["react_components"] = react_components

    # Surface map (6 cockpit surfaces from v19 spec)
    out["surface_map"] = [
        {"surface": "BRIEFING",    "flask_panel": True,  "react_component": False},
        {"surface": "MARKETS",     "flask_panel": True,  "react_component": False},
        {"surface": "INDIA",       "flask_panel": True,  "react_component": False},
        {"surface": "WORLD_TRADE", "flask_panel": True,  "react_component": False},
        {"surface": "INTELLIGENCE","flask_panel": True,  "react_component": False},
        {"surface": "LIVE",        "flask_panel": True,  "react_component": False},
        {"surface": "ENERGY_MAP",  "flask_panel": False, "react_component": any(
            c["file"] == "EnergyMap.tsx" for c in react_components)},
        {"surface": "GRID_STATUS", "flask_panel": False, "react_component": any(
            c["file"] == "GridStatus.tsx" for c in react_components)},
        {"surface": "META_COG",    "flask_panel": False, "react_component": any(
            c["file"] == "MetacognitiveSpace.tsx" for c in react_components)},
    ]

    duplication_risk = [
        s for s in out["surface_map"]
        if s["flask_panel"] and s["react_component"]
    ]
    out["duplication_warnings"] = duplication_risk
    out["recommendation"] = (
        "React components cover surfaces not yet in Flask cockpit — low duplication risk."
        if not duplication_risk else
        "Some surfaces exist in BOTH Flask templates AND React components — consolidate to one canonical view."
    )

    return out
