import os
import sqlite3
import time
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# Import lower-level query layers
import sources as obs
import cognition as cog
import decisions as dec

DB_PATH = obs.DB_PATH

def init_swot_tables():
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.execute("""CREATE TABLE IF NOT EXISTS v22_swot_ledger(
        swot_date TEXT PRIMARY KEY,
        ts REAL,
        strengths TEXT,
        weaknesses TEXT,
        opportunities TEXT,
        threats TEXT,
        upgrades TEXT,
        emailed INTEGER DEFAULT 0
    )""")
    con.commit()
    con.close()

def generate_daily_swot():
    """Compiles the daily SWOT self-analysis from all internal layers and database tables."""
    init_swot_tables()
    date_str = datetime.now().strftime("%Y-%m-%d")
    now = time.time()

    con = sqlite3.connect(DB_PATH, timeout=15)

    # 1. Gather Telemetry and metrics
    # Strengths calculations
    fact_count = con.execute("SELECT COUNT(*) FROM v16_facts").fetchone()[0]
    belief_count = con.execute("SELECT COUNT(*) FROM v15_beliefs").fetchone()[0]
    confirmed_decisions = con.execute("SELECT COUNT(*) FROM v17_decision_ledger WHERE status='CONFIRMED'").fetchone()[0]
    
    # Weaknesses calculations
    failed_sources = con.execute("SELECT COUNT(*) FROM v11_source_health WHERE ok = 0").fetchone()[0]
    belief_conflicts = con.execute("SELECT COUNT(*) FROM v15_beliefs WHERE conflict = 1").fetchone()[0]
    invalidated_decisions = con.execute("SELECT COUNT(*) FROM v17_decision_ledger WHERE status='INVALIDATED'").fetchone()[0]

    # Opportunities calculations
    new_tenders = con.execute("SELECT COUNT(*) FROM v14_entity_ledger WHERE entity_type='tender' AND first_seen >= ?", (now - 7 * 86400,)).fetchone()[0]

    con.close()

    # Chokepoints (Threats)
    chokepoints_data = obs.kv_get("chokepoint_status")
    disrupted_chokepoints = 0
    if chokepoints_data:
        try:
            cp_json = json.loads(chokepoints_data)
            disrupted_chokepoints = sum(1 for cp in cp_json.get("chokepoints", []) if cp.get("status") in ("ELEVATED", "DISRUPTED"))
        except:
            pass

    # Build Lists
    strengths = [
        f"MemoryOS contains {fact_count} curated energy facts.",
        f"Cognition layer holds {belief_count} active belief values.",
        f"Decision scorecard lists {confirmed_decisions} confirmed historical positions."
    ]

    weaknesses = []
    if failed_sources > 0:
        weaknesses.append(f"Observatory tracks {failed_sources} failing news or ingestion sources.")
    if belief_conflicts > 0:
        weaknesses.append(f"{belief_conflicts} standing belief conflicts need manual consolidation.")
    if invalidated_decisions > 0:
        weaknesses.append(f"Scorecard records {invalidated_decisions} invalidated predictions.")
    if not weaknesses:
        weaknesses.append("No material operational weaknesses recorded today.")

    opportunities = [
        f"{new_tenders} new tenders entered the pipeline in the last 7 days.",
        "Market sector breadth indicates potential investment signals in utility-scale solar."
    ]

    threats = []
    if disrupted_chokepoints > 0:
        threats.append(f"{disrupted_chokepoints} global maritime chokepoint(s) are reporting ELEVATED / DISRUPTED status.")
    else:
        threats.append("No active maritime shipping chokepoint disruptions detected.")

    # Calculate recommendations/upgrades
    upgrades = []
    if failed_sources > 5:
        upgrades.append("Fix source URL ingestion endpoints for blocked RSS feeds in sources.py.")
    if belief_conflicts > 0:
        upgrades.append("Resolve belief conflicts using `/api/beliefs` adjudication console.")
    if fact_count < 10:
        upgrades.append("Index additional market files into MemoryOS vector database to enrich references.")
    if not upgrades:
        upgrades.append("System is functioning within nominal parameters. No emergency updates recommended.")

    payload = {
        "swot_date": date_str,
        "ts": now,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "opportunities": opportunities,
        "threats": threats,
        "upgrades": upgrades
    }

    # Save to SQLite
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.execute("""INSERT OR REPLACE INTO v22_swot_ledger(swot_date, ts, strengths, weaknesses, opportunities, threats, upgrades)
        VALUES (?,?,?,?,?,?,?)""", (
            date_str,
            now,
            json.dumps(strengths),
            json.dumps(weaknesses),
            json.dumps(opportunities),
            json.dumps(threats),
            json.dumps(upgrades)
        ))
    con.commit()
    con.close()

    # Trigger email alert if configured
    email_swot_updates(payload)

    return payload

def email_swot_updates(payload):
    """Sends the SWOT report to developer email if SMTP configuration exists in .env."""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    recipient = "thevipuljakhar@gmail.com"

    if not all([smtp_host, smtp_port, smtp_user, smtp_pass]):
        print("[SWOT Engine] SMTP settings missing in .env. Skipping email report dispatch.")
        return False

    date_str = payload["swot_date"]
    
    # Formulate email body in markdown
    msg_body = f"""# NEURON 2.0 - Autonomous SWOT & Upgrades Report
Date: {date_str}

## Strengths
""" + "\n".join(f"- {s}" for s in payload["strengths"]) + """

## Weaknesses
""" + "\n".join(f"- {w}" for w in payload["weaknesses"]) + """

## Opportunities
""" + "\n".join(f"- {o}" for o in payload["opportunities"]) + """

## Threats
""" + "\n".join(f"- {t}" for t in payload["threats"]) + """

## Upgrades Needed
""" + "\n".join(f"- {u}" for u in payload["upgrades"]) + """
"""

    msg = MIMEText(msg_body, 'plain')
    msg['Subject'] = f"[NEURON 2.0] System SWOT & Upgrade Log - {date_str}"
    msg['From'] = smtp_user
    msg['To'] = recipient

    try:
        print(f"[SMTP] Dispatching SWOT report to {recipient}...")
        server = smtplib.SMTP(smtp_host, int(smtp_port), timeout=15)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [recipient], msg.as_string())
        server.quit()
        
        # Mark as emailed in DB
        con = sqlite3.connect(DB_PATH, timeout=15)
        con.execute("UPDATE v22_swot_ledger SET emailed = 1 WHERE swot_date = ?", (date_str,))
        con.commit()
        con.close()
        print("[SMTP] Dispatch completed successfully.")
        return True
    except Exception as e:
        print(f"[SMTP] Error sending email: {e}")
        return False

def get_latest_swot():
    init_swot_tables()
    con = sqlite3.connect(DB_PATH, timeout=15)
    row = con.execute("SELECT swot_date, ts, strengths, weaknesses, opportunities, threats, upgrades, emailed FROM v22_swot_ledger ORDER BY ts DESC LIMIT 1").fetchone()
    con.close()

    if not row:
        return generate_daily_swot()

    return {
        "swot_date": row[0],
        "ts": row[1],
        "strengths": json.loads(row[2]),
        "weaknesses": json.loads(row[3]),
        "opportunities": json.loads(row[4]),
        "threats": json.loads(row[5]),
        "upgrades": json.loads(row[6]),
        "emailed": row[7]
    }
