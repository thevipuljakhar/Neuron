"""
Curiosity Center — wraps curiosity_engine.py
The child's window in the Meta-Cognitive Space.
Shows what Neuron is thinking, questioning, discovering, and still wondering about.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

CENTER_NAME = "Curiosity Center"
CENTER_ROLE = (
    "Neuron's autonomous thinking engine. Observes everything, develops its own questions, "
    "searches for answers, reasons first-principles, and tells its father what it found. "
    "Every conversation with the father becomes a learning opportunity."
)


def status() -> dict:
    try:
        import curiosity_engine as ce
        stats = ce.curiosity_stats()
        return {
            "center": CENTER_NAME,
            "ok": True,
            **stats,
        }
    except Exception as e:
        return {"center": CENTER_NAME, "ok": False, "error": str(e)[:120]}


def report() -> dict:
    try:
        import curiosity_engine as ce
        return {
            "center": CENTER_NAME,
            "role": CENTER_ROLE,
            "status": status(),
            "today_thoughts": ce.get_today_thoughts(limit=10),
            "open_curiosities": ce.get_open_curiosities(limit=10),
            "recent_insights": ce.get_recent_insights(limit=5),
            "self_improve": ce.self_improve(),
        }
    except Exception as e:
        return {"center": CENTER_NAME, "error": str(e)}
