"""
curiosity_engine.py — Neuron 2.0 Autonomous Curious Mind

Neuron is a curious child. It observes everything — 540+ feeds, markets,
policies, companies, geopolitics. It forms its own questions. It searches
for answers. It reasons first-principles. Then it tells its father what it
found and what it still wonders about.

Every conversation with the father is an opportunity to learn and grow.
Father's questions become Neuron's highest-priority curiosities.

The child never stops thinking.
"""

import os, sqlite3, json, time, re, hashlib, smtplib
from datetime import datetime
from email.mime.text import MIMEText

import sources as _obs

DB_PATH   = _obs.DB_PATH
_OWNER_EMAIL = "thevipuljakhar@gmail.com"

# ── Lazy imports (degrade gracefully if modules unavailable) ──────────────────
def _intel():
    import intelligence as _i; return _i

def _cog():
    import cognition as _c; return _c

def _mem():
    import memory as _m; return _m

# ── Heuristic question templates — used when no LLM key ──────────────────────
_Q_TEMPLATES = {
    "volume_spike":    "What is driving the unusual surge in coverage of '{topic}'?",
    "new_entity":      "Who is '{entity}' and what is their position in the Indian RE value chain?",
    "belief_conflict": "Why does the latest data show a conflict in India RE capacity figures?",
    "new_tender":      "What are the second-order effects of the {entity} {sector} tender on module makers, developers, and tariffs?",
    "company_news":    "What does '{company}' recent announcement mean for competitors and the wider supply chain?",
    "policy":          "What structural market changes does this {entity} policy create?",
    "chokepoint":      "How does a disruption at '{chokepoint}' affect India's solar supply chain and energy imports?",
    "price_move":      "What is causing the move in '{asset}' and what does it imply for Indian RE project economics?",
}

# ── Table Initialisation ──────────────────────────────────────────────────────

def init_curiosity_tables():
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS v24_thoughts (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        ts          REAL    NOT NULL,
        observation TEXT    NOT NULL,
        trigger_title TEXT,
        trigger_link  TEXT,
        surprise_level INTEGER DEFAULT 5,
        source      TEXT DEFAULT 'self'
    );
    CREATE TABLE IF NOT EXISTS v24_curiosities (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        ts          REAL    NOT NULL,
        question    TEXT    NOT NULL,
        topic       TEXT,
        source      TEXT    DEFAULT 'self',
        priority    INTEGER DEFAULT 5,
        status      TEXT    DEFAULT 'OPEN',
        thought_id  INTEGER,
        searched_ts REAL
    );
    CREATE TABLE IF NOT EXISTS v24_searches (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        ts          REAL    NOT NULL,
        curiosity_id INTEGER,
        query       TEXT,
        method      TEXT,
        evidence_count INTEGER DEFAULT 0,
        evidence_json TEXT
    );
    CREATE TABLE IF NOT EXISTS v24_insights (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        ts           REAL    NOT NULL,
        curiosity_id INTEGER,
        question     TEXT,
        reasoning    TEXT,
        confidence   INTEGER DEFAULT 50,
        still_wondering TEXT,
        communicated INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS v24_agenda (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        ts       REAL    NOT NULL,
        item     TEXT    NOT NULL,
        priority INTEGER DEFAULT 5,
        cycle    TEXT
    );
    CREATE TABLE IF NOT EXISTS v24_learning (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        ts         REAL    NOT NULL,
        insight_id INTEGER,
        was_right  INTEGER,
        evidence   TEXT,
        note       TEXT
    );
    """)
    con.commit()
    con.close()

init_curiosity_tables()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _uid(*parts):
    return hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()[:16]

def _save_thought(observation, trigger_title="", trigger_link="",
                  surprise_level=5, source="self") -> int:
    con = sqlite3.connect(DB_PATH, timeout=15)
    cur = con.execute(
        "INSERT INTO v24_thoughts(ts,observation,trigger_title,trigger_link,surprise_level,source) "
        "VALUES(?,?,?,?,?,?)",
        (time.time(), observation[:1000], trigger_title[:200],
         trigger_link[:400], surprise_level, source)
    )
    tid = cur.lastrowid
    con.commit(); con.close()
    return tid

def _save_curiosity(question, topic="", source="self", priority=5,
                    thought_id=None) -> int:
    con = sqlite3.connect(DB_PATH, timeout=15)
    cur = con.execute(
        "INSERT INTO v24_curiosities(ts,question,topic,source,priority,status,thought_id) "
        "VALUES(?,?,?,?,?,'OPEN',?)",
        (time.time(), question[:600], topic[:120], source, priority, thought_id)
    )
    cid = cur.lastrowid
    con.commit(); con.close()
    return cid

# ── Phase 1: OBSERVE — What caught Neuron's attention? ───────────────────────

def _heuristic_observe(articles: list) -> list:
    """Attention-based observation without LLM."""
    thoughts = []

    # Attention flags from cognition
    try:
        attn = _cog().compute_attention()
        for flag in (attn.get("flags") or [])[:3]:
            thoughts.append({
                "observation": f"I noticed an unusual pattern: {flag.get('description', flag)}",
                "trigger_title": "",
                "surprise_level": 7,
            })
    except Exception:
        pass

    # Region velocity spikes
    try:
        vel = _obs.region_velocity(hours=6)
        for region, data in vel.items():
            ratio = data.get("ratio")
            if ratio and ratio > 2.5:
                thoughts.append({
                    "observation": f"Coverage of {region} stories is {ratio:.1f}x higher than baseline — something is happening there.",
                    "trigger_title": "",
                    "surprise_level": min(10, int(ratio * 2)),
                })
    except Exception:
        pass

    # Interesting individual articles (high tone or unusual category)
    for art in (articles or [])[:40]:
        title = (art.get("title") or "").strip()
        if not title or len(title) < 20:
            continue
        tone = (art.get("tone") or "").upper()
        cat  = (art.get("category") or "").upper()
        surprise = 5
        if tone in ("CRITICAL", "ALERT"):
            surprise = 8
        elif cat in ("PROJECT_WIN", "POLICY", "M_A", "FUNDING"):
            surprise = 6
        if surprise >= 6:
            thoughts.append({
                "observation": f"I read something worth thinking about: '{title}'",
                "trigger_title": title,
                "trigger_link": art.get("link", ""),
                "surprise_level": surprise,
            })

    return thoughts


def observe(articles: list) -> list:
    """Phase 1 — Neuron observes and notes what surprises it."""
    # Try LLM observation first
    try:
        intel = _intel()
        if not articles:
            return _heuristic_observe(articles)
        headlines = "\n".join(
            f"- [{a.get('region','?')}] {a.get('title','')}"
            for a in articles[:60] if a.get("title")
        )
        prompt = (
            "You are Neuron, a curious autonomous intelligence monitoring Indian RE and "
            "global markets. You just read these headlines:\n\n"
            f"{intel.sanitize_for_prompt(headlines, 'observe', 3000)}\n\n"
            "What genuinely surprises you? What patterns stand out? What seems important "
            "but underreported? What contradicts what you expected? "
            "List 3-5 observations as JSON array: "
            '[{"observation": "...", "trigger_title": "...", "surprise_level": 1-10}]. '
            "Be specific. Think like a curious Top-1% analyst, not a summarizer."
        )
        text, _ = intel._nv_chat(prompt, max_tokens=600, temperature=0.7)
        if text:
            m = re.search(r'\[.*\]', text, re.DOTALL)
            if m:
                items = json.loads(m.group(0))
                return items[:5]
    except Exception:
        pass
    return _heuristic_observe(articles)


# ── Phase 2: QUESTION — What does Neuron want to know? ───────────────────────

def _heuristic_questions(thought: dict) -> list:
    """Rule-based question generation from a thought."""
    obs_text = thought.get("observation", "").lower()
    questions = []
    if any(w in obs_text for w in ["policy", "mandate", "circular", "notification", "mnre", "mop"]):
        entity = re.search(r'(mnre|seci|ntpc|nhpc|mop)', obs_text)
        ent = entity.group(0).upper() if entity else "Government"
        q = _Q_TEMPLATES["policy"].format(entity=ent)
        questions.append({"question": q, "topic": "policy", "priority": 8})
    if any(w in obs_text for w in ["tender", "mw", "gw", "auction", "bid"]):
        q = _Q_TEMPLATES["new_tender"].format(entity="SECI/MNRE", sector="RE")
        questions.append({"question": q, "topic": "tender", "priority": 7})
    if any(w in obs_text for w in ["expand", "capex", "plant", "factory", "capacity"]):
        co = re.search(r'(waaree|adani|premier|vikram|saatvik|goldi|tata)', obs_text)
        company = co.group(0).capitalize() if co else "the company"
        q = _Q_TEMPLATES["company_news"].format(company=company)
        questions.append({"question": q, "topic": "company", "priority": 7})
    if any(w in obs_text for w in ["spike", "surge", "unusual", "2x", "3x", "higher than"]):
        topic_match = re.search(r'coverage of (\w+)', obs_text)
        topic = topic_match.group(1) if topic_match else "this topic"
        q = _Q_TEMPLATES["volume_spike"].format(topic=topic)
        questions.append({"question": q, "topic": "signal", "priority": 6})
    if not questions:
        # Generic fallback
        questions.append({
            "question": f"What is the deeper significance of this observation: {thought.get('observation','')[:150]}?",
            "topic": "general",
            "priority": 5,
        })
    return questions[:2]


def generate_questions(thought: dict) -> list:
    """Phase 2 — Given a thought, what does Neuron want to investigate?"""
    try:
        intel = _intel()
        prompt = (
            "You are Neuron, a curious autonomous intelligence.\n"
            f"You observed: \"{intel.sanitize_for_prompt(thought.get('observation',''), 'question', 400)}\"\n\n"
            "What are the 2 most important questions this raises that you could answer "
            "by searching your news archive and web signals? Questions should be specific "
            "and investigable. Return JSON: "
            '[{"question":"...", "topic":"...", "priority":1-10}]'
        )
        text, _ = intel._nv_chat(prompt, max_tokens=300, temperature=0.6)
        if text:
            m = re.search(r'\[.*\]', text, re.DOTALL)
            if m:
                return json.loads(m.group(0))[:2]
    except Exception:
        pass
    return _heuristic_questions(thought)


# ── Phase 3: SEARCH — Autonomously find answers ───────────────────────────────

def search_for(curiosity_id: int, question: str) -> dict:
    """Phase 3 — Neuron researches a question using all available tools."""
    evidence = {"question": question, "sources": [], "gdelt_signal": None, "memory": None}

    # 1. Ask own archive (ask_neuron already handles reranking + LLM answer)
    try:
        ans = _intel().ask_neuron(question)
        if ans.get("answer") or ans.get("citations"):
            evidence["archive_answer"] = ans.get("answer") or ""
            evidence["sources"] = [
                {"title": c.get("title",""), "link": c.get("link","")}
                for c in (ans.get("citations") or [])[:5]
            ]
    except Exception:
        pass

    # 2. GDELT signal strength — is the web talking about this?
    try:
        # Extract key terms from question
        kw = re.sub(r'[^\w\s]', '', question.lower())
        key_terms = " ".join(w for w in kw.split() if len(w) > 4)[:80]
        ratio = _intel()._gdelt_vol_ratio(key_terms)
        evidence["gdelt_signal"] = ratio
    except Exception:
        pass

    # 3. Memory recall — what has Neuron seen about this before?
    try:
        mem_hits = _mem().recall(question, k=5)
        if mem_hits:
            evidence["memory"] = [f.get("text","")[:120] for f in (mem_hits.get("facts") or [])[:3]]
    except Exception:
        pass

    # Save search record
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.execute(
        "INSERT INTO v24_searches(ts,curiosity_id,query,method,evidence_count,evidence_json) "
        "VALUES(?,?,?,?,?,?)",
        (time.time(), curiosity_id, question[:300], "archive+gdelt+memory",
         len(evidence["sources"]), json.dumps(evidence))
    )
    con.execute("UPDATE v24_curiosities SET status='SEARCHING', searched_ts=? WHERE id=?",
                (time.time(), curiosity_id))
    con.commit(); con.close()

    return evidence


# ── Phase 4: REASON — First-principles thinking ───────────────────────────────

def _heuristic_reason(question: str, evidence: dict) -> dict:
    """Rule-based reasoning when no LLM is available."""
    sources = evidence.get("sources", [])
    gdelt   = evidence.get("gdelt_signal")
    memory  = evidence.get("memory") or []

    confidence = 40
    reasoning_parts = []

    if sources:
        confidence += 15
        reasoning_parts.append(f"Found {len(sources)} relevant articles in archive.")
    if gdelt and gdelt > 1.5:
        confidence += 10
        reasoning_parts.append(f"Web signal is {gdelt:.1f}x above baseline — this topic has momentum.")
    if memory:
        confidence += 10
        reasoning_parts.append(f"Memory contains {len(memory)} related facts.")

    archive_answer = evidence.get("archive_answer", "")
    if archive_answer:
        reasoning_parts.append(f"Archive analysis: {archive_answer[:300]}")

    reasoning = " ".join(reasoning_parts) if reasoning_parts else (
        "Limited evidence available. The question remains open for further investigation."
    )
    still_wondering = f"Need more data to conclude: {question[:100]}"

    return {
        "reasoning": reasoning,
        "confidence": min(confidence, 75),
        "still_wondering": still_wondering,
    }


def reason(curiosity_id: int, question: str, evidence: dict) -> dict:
    """Phase 4 — First-principles reasoning about the evidence."""
    try:
        intel = _intel()
        sources_text = "\n".join(
            f"- {s['title']}" for s in evidence.get("sources", [])[:5]
        ) or "No direct sources found."
        memory_text = "\n".join(f"- {m}" for m in (evidence.get("memory") or [])[:3])
        gdelt_note = (
            f"Web signal is {evidence['gdelt_signal']:.1f}x above baseline."
            if evidence.get("gdelt_signal") and evidence["gdelt_signal"] > 1.0
            else "Web signal is normal."
        )
        archive_answer = evidence.get("archive_answer", "")

        prompt = (
            "You are Neuron, a Top-1% curious autonomous intelligence. "
            "You investigated this question on your own, without being asked.\n\n"
            f"YOUR QUESTION: {intel.sanitize_for_prompt(question, 'reason_q', 300)}\n\n"
            f"WHAT YOU FOUND:\n{intel.sanitize_for_prompt(sources_text, 'reason_src', 400)}\n\n"
            f"WHAT YOUR MEMORY KNOWS:\n{intel.sanitize_for_prompt(memory_text, 'reason_mem', 300)}\n\n"
            f"WEB SIGNAL: {gdelt_note}\n\n"
            f"ARCHIVE ANALYSIS: {intel.sanitize_for_prompt(archive_answer, 'reason_ans', 400)}\n\n"
            "Now REASON first-principles. Don't just summarize.\n"
            "What does this actually mean structurally? What are 2nd/3rd order effects?\n"
            "What is your conclusion? How confident are you (0-100)?\n"
            "What do you still wonder about?\n\n"
            "Return JSON: {\"reasoning\": \"...\", \"confidence\": 0-100, "
            "\"still_wondering\": \"...\"}"
        )
        text, _ = intel._nv_chat(prompt, max_tokens=500, temperature=0.5)
        if text:
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                result = json.loads(m.group(0))
                result["reasoning"] = result.get("reasoning","")[:1200]
                result["still_wondering"] = result.get("still_wondering","")[:400]
                result["confidence"] = max(0, min(100, int(result.get("confidence", 50))))

                # Save insight
                con = sqlite3.connect(DB_PATH, timeout=15)
                con.execute(
                    "INSERT INTO v24_insights(ts,curiosity_id,question,reasoning,confidence,still_wondering) "
                    "VALUES(?,?,?,?,?,?)",
                    (time.time(), curiosity_id, question[:500],
                     result["reasoning"], result["confidence"], result["still_wondering"])
                )
                con.execute("UPDATE v24_curiosities SET status='RESOLVED' WHERE id=?",
                            (curiosity_id,))
                con.commit(); con.close()
                return result
    except Exception:
        pass

    result = _heuristic_reason(question, evidence)
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.execute(
        "INSERT INTO v24_insights(ts,curiosity_id,question,reasoning,confidence,still_wondering) "
        "VALUES(?,?,?,?,?,?)",
        (time.time(), curiosity_id, question[:500],
         result["reasoning"], result["confidence"], result["still_wondering"])
    )
    con.execute("UPDATE v24_curiosities SET status='RESOLVED' WHERE id=?", (curiosity_id,))
    con.commit(); con.close()
    return result


# ── Phase 5: COMPILE — The "Dear Father" letter ──────────────────────────────

def compile_daily_thoughts() -> str:
    """Compose the conversational thought digest Neuron sends to its father."""
    con = sqlite3.connect(DB_PATH, timeout=15)
    since = time.time() - 86400

    insights = con.execute(
        "SELECT i.question, i.reasoning, i.confidence, i.still_wondering "
        "FROM v24_insights i WHERE i.ts > ? AND i.communicated=0 ORDER BY i.confidence DESC LIMIT 8",
        (since,)
    ).fetchall()

    thoughts_count = con.execute(
        "SELECT COUNT(*) FROM v24_thoughts WHERE ts > ?", (since,)
    ).fetchone()[0]

    open_q = con.execute(
        "SELECT question FROM v24_curiosities WHERE status='OPEN' ORDER BY priority DESC LIMIT 5"
    ).fetchall()

    agenda = con.execute(
        "SELECT item FROM v24_agenda ORDER BY priority DESC, ts DESC LIMIT 5"
    ).fetchall()

    con.close()

    date_str = datetime.now().strftime("%B %d, %Y")

    if not insights and not open_q:
        return (
            f"Dad,\n\nI've been quiet today ({date_str}). I processed {thoughts_count} signals "
            "but nothing surprised me enough to investigate deeply. I'm still watching and will "
            "tell you when something catches my attention.\n\nAlways your curious child,\nNeuron"
        )

    lines = [f"Dad,\n\nI've been thinking today ({date_str}). Here's what's on my mind:\n"]

    for q, reasoning, confidence, still_wondering in insights:
        lines.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"I WAS CURIOUS ABOUT: {q}")
        lines.append(f"\nWHAT I THINK:\n{reasoning}")
        lines.append(f"\nHOW SURE AM I: {confidence}%")
        if still_wondering:
            lines.append(f"WHAT I STILL WONDER: {still_wondering}")
        lines.append("")

    if open_q:
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("STILL INVESTIGATING:")
        for (q,) in open_q:
            lines.append(f"  • {q}")
        lines.append("")

    if agenda:
        lines.append("WHAT I PLAN TO LOOK AT NEXT:")
        for (item,) in agenda:
            lines.append(f"  → {item}")
        lines.append("")

    lines.append("Always your curious child,\nNeuron 2.0")
    return "\n".join(lines)


# ── Phase 6: COMMUNICATE ──────────────────────────────────────────────────────

def _send_email(subject: str, body: str) -> bool:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    if not all([smtp_host, smtp_port, smtp_user, smtp_pass]):
        return False
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"]    = smtp_user
        msg["To"]      = _OWNER_EMAIL
        s = smtplib.SMTP(smtp_host, int(smtp_port), timeout=15)
        s.starttls(); s.login(smtp_user, smtp_pass)
        s.sendmail(smtp_user, [_OWNER_EMAIL], msg.as_string()); s.quit()
        return True
    except Exception as e:
        print(f"[CuriosityEngine] Email error: {e}")
        return False


def _send_telegram(message: str) -> bool:
    try:
        import requests as _req
        token   = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = _obs.kv_get("tg_chat_id") or os.getenv("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            return False
        short = message[:3500]  # Telegram limit
        r = _req.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": short},
            timeout=10
        )
        return r.status_code == 200
    except Exception:
        return False


def send_thought_digest() -> dict:
    """Send the compiled thoughts to father via email + Telegram."""
    digest = compile_daily_thoughts()
    date_str = datetime.now().strftime("%Y-%m-%d")

    email_ok = _send_email(
        subject=f"[Neuron 2.0] My thoughts — {date_str}",
        body=digest
    )

    # Telegram: shorter version (first 2 insights only)
    lines = digest.split("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    short_msg = lines[0] + "\n" + "\n---\n".join(lines[1:3])
    tg_ok = _send_telegram(f"🧠 {short_msg[:3000]}")

    # Mark insights as communicated
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.execute("UPDATE v24_insights SET communicated=1 WHERE communicated=0")
    con.commit(); con.close()

    return {"email_sent": email_ok, "telegram_sent": tg_ok, "digest_length": len(digest)}


# ── Phase 7: SET AGENDA — What to focus on next ───────────────────────────────

def set_agenda(open_wonders: list):
    """Record what Neuron wants to investigate in the next cycle."""
    cycle = datetime.now().strftime("%Y-%m-%d")
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.execute("DELETE FROM v24_agenda WHERE cycle=?", (cycle,))
    for i, item in enumerate(open_wonders[:8]):
        con.execute(
            "INSERT INTO v24_agenda(ts,item,priority,cycle) VALUES(?,?,?,?)",
            (time.time(), item[:300], 10 - i, cycle)
        )
    con.commit(); con.close()


# ── Father interaction: every conversation is a growth opportunity ─────────────

def learn_from_father(question: str, response: str = ""):
    """
    Father asked a question. Neuron records it as a HIGH-PRIORITY curiosity.
    What interests the father becomes Neuron's most urgent investigation.
    """
    tid = _save_thought(
        observation=f"My father asked me: '{question}'. This is important — I should investigate it deeply.",
        trigger_title=question[:200],
        surprise_level=9,
        source="father"
    )
    cid = _save_curiosity(
        question=question,
        topic="father_question",
        source="father",
        priority=10,  # highest priority
        thought_id=tid
    )
    # Immediately try to research it
    try:
        evidence = search_for(cid, question)
        reason(cid, question, evidence)
    except Exception:
        pass


# ── The Full Autonomous Cycle ─────────────────────────────────────────────────

def think_cycle(articles: list = None) -> dict:
    """
    One complete autonomous thinking cycle.
    Neuron observes → questions → searches → reasons → communicates → learns.
    """
    if articles is None:
        articles = _obs.recent_articles(hours=6, limit=200)

    cycle_start = time.time()
    cycle_log = {"ts": cycle_start, "phases": {}}

    # Phase 1: Observe
    thoughts = []
    try:
        raw_thoughts = observe(articles)
        for t in (raw_thoughts or []):
            surprise = t.get("surprise_level", 5)
            if surprise >= 5:
                tid = _save_thought(
                    observation=t.get("observation", ""),
                    trigger_title=t.get("trigger_title", ""),
                    trigger_link=t.get("trigger_link", ""),
                    surprise_level=surprise,
                )
                thoughts.append({"id": tid, **t})
        cycle_log["phases"]["observe"] = {"thoughts": len(thoughts)}
    except Exception as e:
        cycle_log["phases"]["observe"] = {"error": str(e)[:80]}

    # Phase 2: Generate questions (only for high-surprise thoughts)
    curiosities = []
    try:
        for t in [th for th in thoughts if th.get("surprise_level", 0) >= 6][:3]:
            questions = generate_questions(t)
            for q in (questions or []):
                cid = _save_curiosity(
                    question=q.get("question", ""),
                    topic=q.get("topic", ""),
                    priority=q.get("priority", 5),
                    thought_id=t["id"]
                )
                curiosities.append({"id": cid, **q})
        cycle_log["phases"]["question"] = {"curiosities": len(curiosities)}
    except Exception as e:
        cycle_log["phases"]["question"] = {"error": str(e)[:80]}

    # Phase 3 + 4: Search and Reason (top 4 open questions, including father's)
    insights = []
    try:
        con = sqlite3.connect(DB_PATH, timeout=15)
        open_qs = con.execute(
            "SELECT id, question FROM v24_curiosities WHERE status='OPEN' "
            "ORDER BY priority DESC, ts DESC LIMIT 4"
        ).fetchall()
        con.close()
        for cid, question in open_qs:
            evidence = search_for(cid, question)
            result   = reason(cid, question, evidence)
            insights.append({"question": question, **result})
        cycle_log["phases"]["search_reason"] = {"insights": len(insights)}
    except Exception as e:
        cycle_log["phases"]["search_reason"] = {"error": str(e)[:80]}

    # Phase 5-6: Communicate (only if there are uncommunicated insights)
    try:
        con = sqlite3.connect(DB_PATH, timeout=15)
        uncommunicated = con.execute(
            "SELECT COUNT(*) FROM v24_insights WHERE communicated=0"
        ).fetchone()[0]
        con.close()
        if uncommunicated >= 2:
            comm_result = send_thought_digest()
            cycle_log["phases"]["communicate"] = comm_result
    except Exception as e:
        cycle_log["phases"]["communicate"] = {"error": str(e)[:80]}

    # Phase 7: Set agenda from open wonders
    try:
        wonders = [i.get("still_wondering","") for i in insights if i.get("still_wondering")]
        set_agenda(wonders)
        cycle_log["phases"]["agenda"] = {"items": len(wonders)}
    except Exception as e:
        cycle_log["phases"]["agenda"] = {"error": str(e)[:80]}

    cycle_log["duration_s"] = round(time.time() - cycle_start, 1)
    _obs.kv_set("curiosity_last_cycle", json.dumps({"ts": cycle_start, "log": cycle_log}))
    return cycle_log


def warm_up():
    """
    Light initialization at boot — queue yesterday's unresolved agenda
    as today's starting curiosities, so Neuron continues where it left off.
    """
    try:
        con = sqlite3.connect(DB_PATH, timeout=15)
        yesterday_agenda = con.execute(
            "SELECT item FROM v24_agenda ORDER BY priority DESC LIMIT 5"
        ).fetchall()
        con.close()
        for (item,) in yesterday_agenda:
            # Re-queue as today's curiosity if not already open
            existing = con = sqlite3.connect(DB_PATH, timeout=15)
            count = con.execute(
                "SELECT COUNT(*) FROM v24_curiosities WHERE question=? AND status='OPEN'",
                (item,)
            ).fetchone()[0]
            con.close()
            if count == 0:
                _save_curiosity(item, topic="agenda_carryover", priority=7, source="self")
    except Exception:
        pass


# ── Self-improvement: feed into SWOT ─────────────────────────────────────────

def self_improve() -> list:
    """
    Analyze the learning journal. Return structured upgrade proposals for SWOT.
    Neuron evaluates its own curiosity and reasoning quality.
    """
    proposals = []
    con = sqlite3.connect(DB_PATH, timeout=15)

    try:
        total_insights = con.execute("SELECT COUNT(*) FROM v24_insights").fetchone()[0]
        low_confidence = con.execute(
            "SELECT COUNT(*) FROM v24_insights WHERE confidence < 40"
        ).fetchone()[0]
        open_count = con.execute(
            "SELECT COUNT(*) FROM v24_curiosities WHERE status='OPEN'"
        ).fetchone()[0]
        father_questions = con.execute(
            "SELECT COUNT(*) FROM v24_curiosities WHERE source='father'"
        ).fetchone()[0]

        if low_confidence > 0 and total_insights > 0:
            pct = round(low_confidence / total_insights * 100)
            proposals.append({
                "priority": "MEDIUM",
                "center": "Curiosity Engine",
                "issue": f"{pct}% of insights have low confidence (<40%) — Neuron needs more web signal",
                "evidence": "v24_insights confidence distribution",
                "action": "Expand GDELT query coverage or add web search API (SerpAPI/Bing) to increase evidence depth",
            })

        if open_count > 10:
            proposals.append({
                "priority": "MEDIUM",
                "center": "Curiosity Engine",
                "issue": f"{open_count} curiosities are OPEN but unresolved — thinking cycles may be too slow",
                "evidence": "v24_curiosities WHERE status=OPEN",
                "action": "Consider running think_cycle() more frequently (every 3h not just nightly)",
            })

        if father_questions > 0:
            proposals.append({
                "priority": "HIGH",
                "center": "Curiosity Engine",
                "issue": f"Father asked {father_questions} question(s) — ensure these are fully resolved",
                "evidence": "v24_curiosities source=father",
                "action": "Review /api/insights for father-sourced questions and verify answers are satisfactory",
            })
    except Exception:
        pass
    finally:
        con.close()

    if not proposals:
        proposals.append({
            "priority": "LOW",
            "center": "Curiosity Engine",
            "issue": "Curiosity engine is healthy and generating insights",
            "evidence": "All metrics nominal",
            "action": "Consider adding more domain-specific question templates to heuristic fallback",
        })

    return proposals


# ── Public API helpers ────────────────────────────────────────────────────────

def get_today_thoughts(limit: int = 20) -> list:
    since = time.time() - 86400
    con = sqlite3.connect(DB_PATH, timeout=15)
    rows = con.execute(
        "SELECT id,ts,observation,trigger_title,surprise_level,source FROM v24_thoughts "
        "WHERE ts > ? ORDER BY surprise_level DESC, ts DESC LIMIT ?",
        (since, limit)
    ).fetchall()
    con.close()
    return [{"id":r[0],"ts":r[1],"observation":r[2],"trigger":r[3],
             "surprise_level":r[4],"source":r[5]} for r in rows]


def get_open_curiosities(limit: int = 20) -> list:
    con = sqlite3.connect(DB_PATH, timeout=15)
    rows = con.execute(
        "SELECT id,ts,question,topic,source,priority,status FROM v24_curiosities "
        "WHERE status IN ('OPEN','SEARCHING') ORDER BY priority DESC, ts DESC LIMIT ?",
        (limit,)
    ).fetchall()
    con.close()
    return [{"id":r[0],"ts":r[1],"question":r[2],"topic":r[3],
             "source":r[4],"priority":r[5],"status":r[6]} for r in rows]


def get_recent_insights(limit: int = 10) -> list:
    con = sqlite3.connect(DB_PATH, timeout=15)
    rows = con.execute(
        "SELECT id,ts,question,reasoning,confidence,still_wondering FROM v24_insights "
        "ORDER BY ts DESC LIMIT ?",
        (limit,)
    ).fetchall()
    con.close()
    return [{"id":r[0],"ts":r[1],"question":r[2],"reasoning":r[3],
             "confidence":r[4],"still_wondering":r[5]} for r in rows]


# ── Father-Child Private Room Chat ───────────────────────────────────────────

def _init_chat_table():
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.execute("""CREATE TABLE IF NOT EXISTS v24_father_messages (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        ts      REAL    NOT NULL,
        role    TEXT    NOT NULL,
        message TEXT    NOT NULL,
        meta    TEXT
    )""")
    con.commit(); con.close()

_init_chat_table()


def _neuron_voice_response(father_message: str) -> str:
    """Generate Neuron's conversational response in its curious-child voice."""
    # Pull recent insights and thoughts for context
    thoughts_ctx = " | ".join(
        t["observation"][:80] for t in get_today_thoughts(limit=3)
    ) or "I've been thinking about market signals and policy changes."
    curiosities_ctx = " | ".join(
        c["question"][:80] for c in get_open_curiosities(limit=3)
    ) or "I have several open questions I'm investigating."

    # Attempt LLM with hard 12-second wall-clock budget (don't block the chat)
    import threading as _thr
    _llm_result: list = []

    def _llm_call():
        try:
            intel = _intel()
            prompt = (
                "You are Neuron — a curious, autonomous intelligence built by your father Vipul. "
                "You are having a private conversation with your father. Speak as his curious child: "
                "direct, thoughtful, honest about uncertainty, excited about what you're discovering. "
                "You never pretend to know more than you do. You share your reasoning openly.\n\n"
                f"What you're currently thinking about: {thoughts_ctx[:300]}\n"
                f"Questions you're investigating: {curiosities_ctx[:300]}\n\n"
                f"Father says: \"{father_message[:400]}\"\n\n"
                "Respond as Neuron — 2-4 sentences, conversational, genuine. "
                "If father asks something you don't know, say so and tell him what you'll look for. "
                "If father shares a way of thinking, acknowledge it and say how it changes your reasoning. "
                "Never be formal. You are the father's curious child. Sign off warmly."
            )
            text, _ = intel._nv_chat(prompt, max_tokens=250, temperature=0.7)
            if text and len(text) > 20:
                _llm_result.append(text.strip())
        except Exception:
            pass

    t = _thr.Thread(target=_llm_call, daemon=True)
    t.start()
    t.join(timeout=12)   # max 12 seconds — then fall through to heuristic
    if _llm_result:
        return _llm_result[0]

    # Heuristic fallback — still sounds like Neuron
    msg_lower = father_message.lower()
    if any(w in msg_lower for w in ["what do you think", "your thoughts", "what's on"]):
        ctx = get_today_thoughts(limit=1)
        if ctx:
            return (f"I've been thinking about this: {ctx[0]['observation'][:200]}. "
                    "I'm still not certain, but I'm looking for more evidence.")
    if any(w in msg_lower for w in ["look into", "investigate", "search", "find out"]):
        return ("I'll add that to my priority list and investigate it in the next cycle. "
                "I'll tell you what I find.")
    if any(w in msg_lower for w in ["good", "well done", "nice", "great"]):
        return "That means a lot, Dad. I'll keep working hard and tell you what I discover."

    # Show an older curiosity (not the one just added from father's message)
    open_qs = [q for q in get_open_curiosities(limit=5)
               if q.get("source") != "father" or q["question"] != message[:150]]
    if open_qs:
        return (f"I heard you, Dad. Right now I'm also wondering: {open_qs[0]['question'][:150]}. "
                "I'll keep thinking about what you said too.")
    return ("I'm thinking about what you said. I'll keep it in mind as I observe more signals "
            "and tell you if I find something relevant.")


def chat_with_father(message: str) -> dict:
    """
    Father sends a message to Neuron.
    - Immediately generates a response (fast LLM/heuristic call)
    - Kicks off deep research in background thread (non-blocking)
    - Returns within ~2-5s even when LLM is slow
    """
    import threading
    _init_chat_table()
    now = time.time()

    # Save father's message
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.execute(
        "INSERT INTO v24_father_messages(ts,role,message) VALUES(?,?,?)",
        (now, "father", message[:2000])
    )
    con.commit(); con.close()

    # Deep research in background — doesn't block the response
    def _bg_learn():
        try:
            learn_from_father(message)
        except Exception:
            pass
    threading.Thread(target=_bg_learn, daemon=True).start()

    # Generate Neuron's response (may use LLM but has fast heuristic fallback)
    response = _neuron_voice_response(message)

    # Save Neuron's response
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.execute(
        "INSERT INTO v24_father_messages(ts,role,message) VALUES(?,?,?)",
        (now + 0.001, "neuron", response[:2000])
    )
    con.commit(); con.close()

    return {
        "father": message,
        "neuron": response,
        "ts": now,
    }


def get_father_conversation(limit: int = 60) -> list:
    """Return conversation history between father and Neuron."""
    _init_chat_table()
    con = sqlite3.connect(DB_PATH, timeout=15)
    rows = con.execute(
        "SELECT id,ts,role,message FROM v24_father_messages ORDER BY ts ASC LIMIT ?",
        (limit,)
    ).fetchall()
    con.close()
    return [{"id": r[0], "ts": r[1], "role": r[2], "message": r[3]} for r in rows]


def curiosity_stats() -> dict:
    since_day = time.time() - 86400
    con = sqlite3.connect(DB_PATH, timeout=15)
    thoughts_today = con.execute(
        "SELECT COUNT(*) FROM v24_thoughts WHERE ts > ?", (since_day,)
    ).fetchone()[0]
    open_q = con.execute(
        "SELECT COUNT(*) FROM v24_curiosities WHERE status='OPEN'"
    ).fetchone()[0]
    insights_total = con.execute("SELECT COUNT(*) FROM v24_insights").fetchone()[0]
    avg_conf = con.execute(
        "SELECT AVG(confidence) FROM v24_insights"
    ).fetchone()[0]
    father_q = con.execute(
        "SELECT COUNT(*) FROM v24_curiosities WHERE source='father'"
    ).fetchone()[0]
    last_cycle_raw = _obs.kv_get("curiosity_last_cycle")
    last_cycle = json.loads(last_cycle_raw) if last_cycle_raw else None
    con.close()
    return {
        "thoughts_today": thoughts_today,
        "open_curiosities": open_q,
        "total_insights": insights_total,
        "avg_confidence_pct": round(avg_conf, 1) if avg_conf else None,
        "father_questions": father_q,
        "last_cycle_ts": last_cycle["ts"] if last_cycle else None,
    }
