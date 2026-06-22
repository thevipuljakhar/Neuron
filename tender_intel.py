"""
tender_intel.py - Neuron v21 First-Principles Tender Intelligence Engine
by Vipul Jakhar

First-principles reasoning:
  news/feed → classify (sector/entity/capacity) → freshness check →
  record DB → route to surfaces → generate causal chain →
  update watch companies → detect anomalies → push notifications

Tables: v21_tenders, v21_causal_events, v21_watch_companies, v21_anomalies
"""

import sqlite3, json, re, time, os
from datetime import datetime
from typing import Optional

try:
    import sources as obs
    DB_PATH = obs.DB_PATH
except ImportError:
    DB_PATH = os.path.join(os.path.dirname(__file__), "neuron.db")

# ── Schema ────────────────────────────────────────────────────────────────────

def _init_tables():
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS v21_tenders (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        uid           TEXT UNIQUE,
        project_name  TEXT,
        entity        TEXT,
        entity_type   TEXT,
        sector        TEXT,
        capacity_mw   REAL,
        state         TEXT,
        developer     TEXT,
        epc           TEXT,
        notif_no      TEXT,
        announced_date TEXT,
        bid_deadline  TEXT,
        ppa_signed_date TEXT,
        status        TEXT,
        freshness     TEXT,
        source_url    TEXT,
        source_title  TEXT,
        raw_text      TEXT,
        routed_to     TEXT,
        created_at    TEXT,
        updated_at    TEXT
    );

    CREATE TABLE IF NOT EXISTS v21_causal_events (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        uid               TEXT UNIQUE,
        trigger_type      TEXT,
        trigger_entity    TEXT,
        trigger_event     TEXT,
        sector            TEXT,
        causal_chain      TEXT,
        affected_companies TEXT,
        opportunity_flags TEXT,
        risk_flags        TEXT,
        watch_flags       TEXT,
        confidence        REAL,
        created_at        TEXT,
        updated_at        TEXT
    );

    CREATE TABLE IF NOT EXISTS v21_watch_companies (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        name           TEXT UNIQUE,
        group_name     TEXT,
        alcm_mw        REAL DEFAULT 0,
        almm_mw        REAL DEFAULT 0,
        alcm_status    TEXT,
        almm_status    TEXT,
        watch_level    TEXT,
        watch_reason   TEXT,
        latest_signal  TEXT,
        causal_context TEXT,
        news_keywords  TEXT,
        created_at     TEXT,
        updated_at     TEXT
    );

    CREATE TABLE IF NOT EXISTS v21_anomalies (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        uid               TEXT UNIQUE,
        anomaly_type      TEXT,
        title             TEXT,
        description       TEXT,
        severity          TEXT,
        affected_sector   TEXT,
        affected_company  TEXT,
        source_tender_id  INTEGER,
        source_causal_id  INTEGER,
        resolved          INTEGER DEFAULT 0,
        created_at        TEXT
    );
    """)
    con.commit()
    con.close()

_init_tables()

# ── Entity + Sector Classification ───────────────────────────────────────────

ENTITY_PATTERNS = [
    (r'\bMNRE\b|ministry.*new.*renewable',          'MNRE',        'MNRE'),
    (r'\bSECI\b|solar energy corporation',           'SECI',        'SECI'),
    (r'\bNHPC\b',                                    'NHPC',        'NHPC'),
    (r'\bNTPC\b',                                    'NTPC',        'NTPC'),
    (r'\bRECL?\b|rural electrification corp',        'REC',         'REC'),
    (r'\bPFC\b|power finance corp',                  'PFC',         'PFC'),
    (r'rajasthan.*energy|RVUN|RRECL',                'RVUN',        'STATE'),
    (r'gujarat.*energy|GUVNL|GERMI',                 'GUVNL',       'STATE'),
    (r'tamil.*energy|TANGEDCO|STELCO',               'TANGEDCO',    'STATE'),
    (r'karnataka.*energy|KREDL|BESCOM',              'KREDL',       'STATE'),
    (r'andhra.*energy|APEPDCL|APERC',                'APEPDCL',     'STATE'),
    (r'maharashtra.*energy|MSEDCL|MEDA',             'MSEDCL',      'STATE'),
    (r'madhya.*energy|MPPMCL|MPERC',                 'MPPMCL',      'STATE'),
    (r'telangana.*energy|TSECL|TSTRANSCO',           'TSECL',       'STATE'),
    (r'UP.*energy|UPNEDA|UPCL',                      'UPNEDA',      'STATE'),
    (r'\bNHAI\b|\bNHPC\b',                           'NHPC',        'NHPC'),
    (r'electricity.*board|state.*discom|DISCOM',     'State Discom','STATE_DISCOM'),
]

SECTOR_PATTERNS = [
    (r'\bsolar\b|photovoltaic|\bpv\b|rooftop solar|floating solar', 'Solar'),
    (r'\bwind\b|turbine|offshore wind|onshore wind',               'Wind'),
    (r'\bBESS\b|battery.*storage|storage.*battery|LFP|ESS\b|pumped.*storage', 'BESS'),
    (r'\bgreen.?h(ydrogen|2)\b|GH2|electroly[sz]|electrolyz',     'GH'),
    (r'\bhydro(power|electric)?\b|dam|reservoir',                  'Hydro'),
    (r'\bhybrid\b|wind.{1,10}solar|solar.{1,10}wind',             'Hybrid'),
    # ── Added in Parallel Track B ─────────────────────────────────────────────
    (r'\boffshore\s+wind\b|floating\s+wind',                       'Wind_Offshore'),
    (r'\bpumped.{1,10}hydro|pumped.{1,10}storage\b',              'PHES'),
    (r'\bagri.{1,8}solar|solar.{1,8}agri|PM.KUSUM\b',             'AgriSolar'),
    (r'\brooftop\b|\bPM.Surya.Ghar\b|PM.SGY',                     'Rooftop'),
]

def classify_entity(text: str):
    for pattern, name, etype in ENTITY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return name, etype
    return 'Unknown', 'OTHER'

def classify_sector(text: str) -> str:
    for pattern, sector in SECTOR_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return sector
    return 'RE'

def extract_capacity_mw(text: str) -> Optional[float]:
    m = re.search(r'(\d+(?:\.\d+)?)\s*GW\b', text, re.IGNORECASE)
    if m:
        return float(m.group(1)) * 1000
    m = re.search(r'(\d+(?:,\d+)?(?:\.\d+)?)\s*MW\b', text, re.IGNORECASE)
    if m:
        return float(m.group(1).replace(',', ''))
    return None

def extract_notif_no(text: str) -> Optional[str]:
    for p in [r'No\.?\s*[\w/\-]+/\d{4}', r'(?:Notification|Order|Tender)\s*No\.?\s*[\w/\-]+']:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0)[:60]
    return None

def extract_state(text: str) -> Optional[str]:
    STATES = ['Rajasthan','Gujarat','Maharashtra','Tamil Nadu','Andhra Pradesh',
              'Karnataka','Telangana','Uttar Pradesh','Madhya Pradesh','Punjab',
              'Haryana','Kerala','West Bengal','Odisha','Jharkhand','Chhattisgarh',
              'Himachal Pradesh','Uttarakhand','Goa','Assam','Bihar']
    for s in STATES:
        if s.lower() in text.lower():
            return s
    return None

def extract_developer(text: str) -> Optional[str]:
    DEVS = ['Adani Green','Tata Power','ReNew Power','Greenko','ACME Solar',
            'Azure Power','Torrent Power','NTPC Renewable','Avaada','Hero Future',
            # ── Added in Parallel Track B ──────────────────────────────────────
            'Amp Energy','O2 Power','Ayana Renewable','Continuum Green Energy',
            'CleanMax','Sprng Energy','Serentica Renewables','JSW Energy',
            'Schneider Electric','Larsen & Toubro','Shapoorji Pallonji','BHEL',
            'Thermax','KEC International','Sterlite Power','Amp Solar',
            'Avaada Energy','Torrent Renewables','CESC Renewables','Sembcorp India']
    for d in DEVS:
        if d.lower() in text.lower():
            return d
    return None

# ── Freshness Detection ───────────────────────────────────────────────────────

def _uid(entity: str, sector: str, capacity_mw, state, notif_no) -> str:
    parts = [entity or '', sector or '', str(int(capacity_mw or 0)), state or '', notif_no or '']
    return re.sub(r'\W+', '_', '_'.join(parts).lower())[:80]

def check_freshness(uid: str, capacity_mw) -> str:
    con = sqlite3.connect(DB_PATH)
    try:
        row = con.execute("SELECT capacity_mw FROM v21_tenders WHERE uid=?", (uid,)).fetchone()
        if not row:
            return 'NEW'
        existing = row[0] or 0
        if capacity_mw and existing and abs((capacity_mw - existing) / max(existing, 1)) > 0.05:
            return 'UPDATE'
        return 'EXISTING'
    finally:
        con.close()

# ── Surface Routing ───────────────────────────────────────────────────────────

def _route(sector: str, freshness: str) -> list:
    routes = ['tenders', 'trade']
    if freshness in ('NEW', 'UPDATE'):
        routes += ['notifications', 'intel']
    sector_route = {
        'Solar': 'india_solar', 'Wind': 'india_wind',
        'BESS': 'india_bess', 'GH': 'india_gh', 'Hydro': 'india_hydro'
    }
    if sector in sector_route:
        routes.append(sector_route[sector])
    return list(set(routes))

# ── Tender Recording ──────────────────────────────────────────────────────────

def record_tender(project_name, entity, entity_type, sector, capacity_mw,
                  state, notif_no, announced_date, bid_deadline, developer,
                  status, source_url, source_title, raw_text) -> dict:
    uid = _uid(entity, sector, capacity_mw, state, notif_no)
    freshness = check_freshness(uid, capacity_mw)
    now = datetime.utcnow().isoformat()
    con = sqlite3.connect(DB_PATH)
    try:
        if freshness == 'NEW':
            con.execute("""
                INSERT OR IGNORE INTO v21_tenders
                (uid,project_name,entity,entity_type,sector,capacity_mw,state,
                 developer,notif_no,announced_date,bid_deadline,status,freshness,
                 source_url,source_title,raw_text,routed_to,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (uid,project_name,entity,entity_type,sector,capacity_mw,state,
                  developer,notif_no,announced_date,bid_deadline,status,freshness,
                  source_url,source_title,(raw_text or '')[:2000],'[]',now,now))
        elif freshness == 'UPDATE':
            con.execute("""
                UPDATE v21_tenders SET freshness=?,updated_at=?,
                capacity_mw=COALESCE(?,capacity_mw) WHERE uid=?
            """, (freshness,now,capacity_mw,uid))
        routing = _route(sector, freshness)
        con.execute("UPDATE v21_tenders SET routed_to=? WHERE uid=?", (json.dumps(routing),uid))
        con.commit()
        row = con.execute("SELECT id FROM v21_tenders WHERE uid=?", (uid,)).fetchone()
        tender_id = row[0] if row else None
    finally:
        con.close()
    return {'uid':uid,'freshness':freshness,'routing':routing,'tender_id':tender_id}

# ── Causal Chain Engine ───────────────────────────────────────────────────────

CAUSAL_TEMPLATES = {
    'ALCM_MANDATE': {
        'trigger': 'ALCM/ALMM mandate policy announced by MNRE',
        'steps': [
            {'num':1,'text':'MNRE releases ALCM/ALMM mandate — only DCR-listed cells/modules qualify for government tenders','tag':'trigger'},
            {'num':2,'text':'DCR module demand surges; non-DCR module demand collapses in government segment immediately','tag':'risk'},
            {'num':3,'text':'Module makers with large non-DCR capacity face stranded asset risk — 29 GW module capacity at risk (Waaree case)','tag':'risk'},
            {'num':4,'text':'Two strategic options: (1) Export non-DCR modules, (2) Convert module lines to cell lines to meet DCR cell demand','tag':'opportunity'},
            {'num':5,'text':'All module makers need DCR cells — double opportunity for cell makers; cell capacity becomes the choke point','tag':'opportunity'},
            {'num':6,'text':'Leaders will exploit first: watch Waaree, Adani, Premier for export MoUs or cell line capex orders','tag':'watch'},
            {'num':7,'text':'ALCM list expansion accelerates — companies not yet listed will rush to qualify','tag':'watch'},
        ]
    },
    'LARGE_SOLAR_TENDER': {
        'trigger': 'Large solar tender >500 MW announced',
        'steps': [
            {'num':1,'text':'Large tender triggers module procurement planning 12–18 months ahead of commissioning','tag':'trigger'},
            {'num':2,'text':'If DCR mandatory: ALMM-listed module makers see forward order pressure; prices firm 5–10%','tag':'opportunity'},
            {'num':3,'text':'EPC prequalification begins — watch for large EPC consortium announcements','tag':'watch'},
            {'num':4,'text':'State-specific transmission + land risk: check ISTS allocation and substation capacity for this state','tag':'risk'},
            {'num':5,'text':'Tariff discovery at bid deadline will set sector benchmark — monitor competitiveness vs H1FY tariff','tag':'watch'},
        ]
    },
    'BESS_TENDER': {
        'trigger': 'BESS/Storage tender announced',
        'steps': [
            {'num':1,'text':'BESS tender signals policy push for grid stability and RE integration — round-the-clock RE contracts emerging','tag':'trigger'},
            {'num':2,'text':'LFP cell price is the critical input cost — India currently imports ~95% from China; watch China export controls','tag':'risk'},
            {'num':3,'text':'VGF (Viability Gap Funding) component reduces effective capital cost by 15–25% — disbursement timing is key','tag':'opportunity'},
            {'num':4,'text':'Domestic BESS manufacturers (Amara Raja, Exide, Tata Power, JSW) get preferential treatment — watch bid participation','tag':'watch'},
        ]
    },
    'GREEN_H2_TENDER': {
        'trigger': 'Green Hydrogen tender under NGHM/SIGHT',
        'steps': [
            {'num':1,'text':'GH2 tender under SIGHT scheme — bundled electrolyzer + RE + storage + offtake requirement','tag':'trigger'},
            {'num':2,'text':'Electrolyzer supply chain risk: PEM vs ALK — India lacks domestic manufacturing at GW scale','tag':'risk'},
            {'num':3,'text':'RE anchor load implied: large solar/wind capacity is locked in for H2 production — check RE developer pipeline','tag':'opportunity'},
            {'num':4,'text':'Export offtake MoU required for project economics — watch Japan, South Korea, EU H2 import agreements','tag':'watch'},
            {'num':5,'text':'First-mover advantage: NTPC, Adani, ACME are positioning — watch bid prequalification criteria','tag':'watch'},
        ]
    },
    'WIND_TENDER': {
        'trigger': 'Wind power tender announced',
        'steps': [
            {'num':1,'text':'Wind tender triggers turbine OEM order pipeline 18–24 months ahead — Vestas, GE, Siemens, Suzlon watch','tag':'trigger'},
            {'num':2,'text':'Offshore wind: land acquisition not needed but port infrastructure + cable are bottlenecks','tag':'risk'},
            {'num':3,'text':'Hybrid wind+solar gaining preference — watch if this is standalone or hybrid specification','tag':'watch'},
            {'num':4,'text':'Suzlon (domestic leader) gets competitive edge in onshore — watch their order book updates','tag':'opportunity'},
        ]
    },
    'COMPANY_EXPANSION': {
        'trigger': 'Manufacturing company announces capacity expansion',
        'steps': [
            {'num':1,'text':'Expansion signals confidence in forward demand — verify DCR mandate compliance angle','tag':'trigger'},
            {'num':2,'text':'Cross-check ALCM/ALMM listing status: is this company listed? Does expansion change sector HHI concentration?','tag':'watch'},
            {'num':3,'text':'Capital deployment: equity raise or debt? Watch rights issue / QIP / NCD announcements','tag':'watch'},
            {'num':4,'text':'Competitor response: if one leader expands, others face pressure — watch sector-wide capex announcements','tag':'risk'},
            {'num':5,'text':'Supply chain impact: cell + wafer shortage risk if multiple expansions announced simultaneously','tag':'risk'},
        ]
    },
}

def generate_causal_chain(trigger_type: str, trigger_entity: str,
                           trigger_event: str, sector: str, raw_text: str) -> Optional[dict]:
    key = None
    t = raw_text.lower()
    if re.search(r'alcm|almm|mandate|dcr', t):
        key = 'ALCM_MANDATE'
    elif trigger_type == 'COMPANY' and re.search(r'expan|cell.*mfg|manufactur|capac', t):
        key = 'COMPANY_EXPANSION'
    elif sector == 'Solar' and trigger_type == 'TENDER':
        key = 'LARGE_SOLAR_TENDER'
    elif sector == 'BESS':
        key = 'BESS_TENDER'
    elif sector == 'GH':
        key = 'GREEN_H2_TENDER'
    elif sector == 'Wind' and trigger_type == 'TENDER':
        key = 'WIND_TENDER'

    if not key:
        return None

    tmpl = CAUSAL_TEMPLATES[key]
    uid = f"ce_{re.sub(chr(92)+'W+','_',trigger_entity[:20].lower())}_{int(time.time())}"
    now = datetime.utcnow().isoformat()
    affected = _get_affected_companies(sector, raw_text)
    opps  = [s['text'] for s in tmpl['steps'] if s['tag'] == 'opportunity']
    risks = [s['text'] for s in tmpl['steps'] if s['tag'] == 'risk']
    watch = [s['text'] for s in tmpl['steps'] if s['tag'] == 'watch']

    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("""
            INSERT OR IGNORE INTO v21_causal_events
            (uid,trigger_type,trigger_entity,trigger_event,sector,causal_chain,
             affected_companies,opportunity_flags,risk_flags,watch_flags,confidence,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (uid,trigger_type,trigger_entity,trigger_event[:120],sector,
              json.dumps(tmpl['steps']),json.dumps(affected),
              json.dumps(opps),json.dumps(risks),json.dumps(watch),
              0.78,now,now))
        con.commit()
    finally:
        con.close()

    for co in affected:
        _upsert_watch(co, sector, trigger_event, key)

    return {'uid':uid,'template':key,'steps':tmpl['steps'],'affected':affected,
            'opportunities':opps,'risks':risks,'watches':watch}

def _get_affected_companies(sector: str, raw_text: str) -> list:
    KNOWN = ['Waaree','Adani Solar','Tata Power Solar','Vikram Solar','Saatvik',
             'Premier Energies','Goldi Solar','Emmvee','Renewsys','NTPC',
             'NHPC','ReNew Power','Greenko','Avaada','ACME Solar','Azure Power',
             'Torrent Power','Amara Raja','Exide','JSW Energy']
    found = [c for c in KNOWN if c.lower() in raw_text.lower()]
    if not found and sector in ('Solar','RE','Hybrid'):
        con = sqlite3.connect(DB_PATH)
        try:
            tables = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            for t in tables:
                if 'almm' in t.lower() or 'alcm' in t.lower():
                    try:
                        rows = con.execute(
                            f"SELECT DISTINCT parent_company FROM {t} WHERE parent_company IS NOT NULL LIMIT 8"
                        ).fetchall()
                        found = [r[0] for r in rows if r[0]]
                        break
                    except Exception:
                        pass
        finally:
            con.close()
    return found[:8]

def _upsert_watch(name: str, sector: str, trigger: str, template: str):
    con = sqlite3.connect(DB_PATH)
    now = datetime.utcnow().isoformat()
    try:
        if con.execute("SELECT id FROM v21_watch_companies WHERE name=?", (name,)).fetchone():
            con.execute("""
                UPDATE v21_watch_companies SET watch_level='HIGH',latest_signal=?,updated_at=? WHERE name=?
            """, (f"{trigger[:80]} ({template})", now, name))
        else:
            con.execute("""
                INSERT INTO v21_watch_companies
                (name,group_name,watch_level,watch_reason,latest_signal,news_keywords,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?)
            """, (name,name,'HIGH',f"Auto-triggered: {template}",trigger[:80],
                  f"{name},{name.split()[0]}",now,now))
        con.commit()
    finally:
        con.close()

# ── Anomaly Detection ─────────────────────────────────────────────────────────

def detect_anomalies(tender_id: int, sector: str, capacity_mw, entity_type: str) -> list:
    anomalies = []
    now = datetime.utcnow().isoformat()
    con = sqlite3.connect(DB_PATH)
    try:
        if capacity_mw and capacity_mw > 3000:
            uid = f"anm_size_{tender_id}"
            sev = 'HIGH' if capacity_mw > 5000 else 'MEDIUM'
            title = f'{sector} mega-tender: {capacity_mw:.0f} MW'
            desc = f'Capacity {capacity_mw:.0f} MW is {int(capacity_mw/500)}× sector average. Grid absorption and financing risk elevated.'
            con.execute("""
                INSERT OR IGNORE INTO v21_anomalies
                (uid,anomaly_type,title,description,severity,affected_sector,source_tender_id,created_at)
                VALUES(?,?,?,?,?,?,?,?)
            """, (uid,'TENDER_SIZE',title,desc,sev,sector,tender_id,now))
            anomalies.append({'type':'TENDER_SIZE','severity':sev,'title':title})

        today = datetime.utcnow().date().isoformat()
        count = con.execute(
            "SELECT COUNT(*) FROM v21_tenders WHERE sector=? AND DATE(created_at)=?",
            (sector, today)
        ).fetchone()[0]
        if count >= 3:
            uid = f"anm_cluster_{sector}_{today}"
            title = f'{count} {sector} tenders in one session — policy push signal'
            desc = f'Cluster of {count} {sector} tenders today suggests coordinated government acceleration.'
            con.execute("""
                INSERT OR IGNORE INTO v21_anomalies
                (uid,anomaly_type,title,description,severity,affected_sector,created_at)
                VALUES(?,?,?,?,?,?,?)
            """, (uid,'POLICY_SHIFT',title,desc,'MEDIUM',sector,now))
            anomalies.append({'type':'POLICY_SHIFT','severity':'MEDIUM','title':title})

        con.commit()
    finally:
        con.close()
    return anomalies

# ── Scan + Ingest Pipeline ────────────────────────────────────────────────────

def scan_and_ingest(articles: list) -> dict:
    """
    Main pipeline: articles → classify → record → causal chain → anomalies.
    Designed to be called from any context (background worker or on-demand).
    """
    results = {'new':0,'updated':0,'causal_chains':0,'anomalies':0,'skipped':0}

    TENDER_RE = re.compile(
        r'tender|MW\b|GW\b|SECI|MNRE|auction|bid|capacity|mandate|ALCM|ALMM|commission|GH2|electroly',
        re.IGNORECASE
    )

    for art in articles:
        title = (art.get('title') or '')[:200]
        body  = (art.get('summary') or art.get('text') or '')[:1000]
        full  = f"{title} {body}"
        link  = art.get('link') or art.get('url') or ''

        if not TENDER_RE.search(full):
            results['skipped'] += 1
            continue

        sector      = classify_sector(full)
        entity, etype = classify_entity(full)
        cap_mw      = extract_capacity_mw(full)
        state       = extract_state(full)
        notif_no    = extract_notif_no(full)
        developer   = extract_developer(full)
        date_str    = art.get('date') or art.get('published') or datetime.utcnow().date().isoformat()

        ttype = 'TENDER'
        if re.search(r'mandate|policy|notification|circular|order', full, re.IGNORECASE):
            ttype = 'POLICY'
        elif re.search(r'expan|manufactur|cell.*mfg|capacity.*increase|invest', full, re.IGNORECASE):
            ttype = 'COMPANY'

        status = 'OPEN' if ttype == 'TENDER' else 'ANNOUNCED'

        res = record_tender(
            project_name=title, entity=entity, entity_type=etype,
            sector=sector, capacity_mw=cap_mw, state=state,
            notif_no=notif_no, announced_date=date_str[:10], bid_deadline=None,
            developer=developer, status=status,
            source_url=link, source_title=title, raw_text=full
        )

        if res['freshness'] == 'NEW':
            results['new'] += 1
        elif res['freshness'] == 'UPDATE':
            results['updated'] += 1
        else:
            continue  # skip causal chain for EXISTING to avoid spam

        chain = generate_causal_chain(ttype, entity, title, sector, full)
        if chain:
            results['causal_chains'] += 1

        anoms = detect_anomalies(res.get('tender_id') or 0, sector, cap_mw, etype)
        results['anomalies'] += len(anoms)

    return results

# ── Query API ─────────────────────────────────────────────────────────────────

def get_tenders(sector=None, entity_type=None, status=None, limit=100) -> dict:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        clauses, params = [], []
        if sector:      clauses.append("sector=?");      params.append(sector)
        if entity_type: clauses.append("entity_type=?"); params.append(entity_type)
        if status:      clauses.append("status=?");      params.append(status)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = con.execute(
            f"SELECT * FROM v21_tenders {where} ORDER BY created_at DESC LIMIT ?",
            params + [limit]
        ).fetchall()
        tenders = [dict(r) for r in rows]
        total_mw = sum(t.get('capacity_mw') or 0 for t in tenders)
        sectors  = list(set(t['sector'] for t in tenders if t.get('sector')))
        return {'tenders':tenders,'count':len(tenders),'total_mw':total_mw,'sectors':sectors}
    finally:
        con.close()

def get_stats() -> dict:
    con = sqlite3.connect(DB_PATH)
    try:
        total     = con.execute("SELECT COUNT(*) FROM v21_tenders").fetchone()[0]
        new_today = con.execute("SELECT COUNT(*) FROM v21_tenders WHERE DATE(created_at)=DATE('now')").fetchone()[0]
        total_mw  = con.execute("SELECT COALESCE(SUM(capacity_mw),0) FROM v21_tenders").fetchone()[0]
        by_sector = {r[0]:{'count':r[1],'total_mw':r[2] or 0} for r in
                     con.execute("SELECT sector,COUNT(*),SUM(capacity_mw) FROM v21_tenders GROUP BY sector").fetchall()}
        by_entity = {r[0]:r[1] for r in
                     con.execute("SELECT entity_type,COUNT(*) FROM v21_tenders GROUP BY entity_type").fetchall()}
        causal_n  = con.execute("SELECT COUNT(*) FROM v21_causal_events").fetchone()[0]
        watch_hi  = con.execute("SELECT COUNT(*) FROM v21_watch_companies WHERE watch_level='HIGH'").fetchone()[0]
        anomaly_n = con.execute("SELECT COUNT(*) FROM v21_anomalies WHERE resolved=0").fetchone()[0]
        return {'total':total,'new_today':new_today,'total_mw':total_mw,
                'by_sector':by_sector,'by_entity':by_entity,
                'causal_chains':causal_n,'watch_companies':watch_hi,'active_anomalies':anomaly_n}
    finally:
        con.close()

def get_capacity_pipeline() -> dict:
    STATUS_MAP = {'ANNOUNCED':'announced','OPEN':'tendered','UNDER_CONSTRUCTION':'under_construction',
                  'COMMISSIONED':'commissioned','CANCELLED':'cancelled'}
    SECTORS = ['Solar','Wind','BESS','GH','Hydro','Hybrid','RE']
    con = sqlite3.connect(DB_PATH)
    out = {}
    try:
        for s in SECTORS:
            bucket = {'tendered':0,'announced':0,'under_construction':0,'commissioned':0,'cancelled':0}
            for row in con.execute(
                "SELECT status,COALESCE(SUM(capacity_mw),0) FROM v21_tenders WHERE sector=? GROUP BY status", (s,)
            ).fetchall():
                k = STATUS_MAP.get(row[0],'tendered')
                bucket[k] = bucket.get(k,0) + (row[1] or 0)
            if any(bucket.values()):
                out[s] = bucket
        return out
    finally:
        con.close()

def get_causal_chains(limit=20, company=None) -> list:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        if company:
            rows = con.execute("""
                SELECT * FROM v21_causal_events WHERE affected_companies LIKE ?
                ORDER BY created_at DESC LIMIT ?
            """, (f'%{company}%', limit)).fetchall()
        else:
            rows = con.execute(
                "SELECT * FROM v21_causal_events ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            for f in ('causal_chain','affected_companies','opportunity_flags','risk_flags','watch_flags'):
                try:    d[f] = json.loads(d[f] or '[]')
                except: d[f] = []
            result.append(d)
        return result
    finally:
        con.close()

def get_watch_companies() -> list:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute("""
            SELECT * FROM v21_watch_companies
            ORDER BY CASE watch_level WHEN 'HIGH' THEN 0 WHEN 'MEDIUM' THEN 1 ELSE 2 END,
                     updated_at DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()

def get_anomalies(limit=30) -> list:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute("""
            SELECT * FROM v21_anomalies WHERE resolved=0
            ORDER BY CASE severity WHEN 'HIGH' THEN 0 WHEN 'MEDIUM' THEN 1 ELSE 2 END,
                     created_at DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()

# ── Seed Known Watch Companies ────────────────────────────────────────────────

def _seed():
    SEED = [
        ('Waaree Group','Waaree','HIGH',
         'Largest module maker (29 GW) — key DCR policy indicator. Has 5 GW cell capacity. First-mover in ALCM mandate response.',
         'Waaree,Waaree Energies,WREN,waaree export,waaree cell'),
        ('Adani Solar','Adani','HIGH',
         'Vertically integrated cell+module+project developer. 4 GW cells, 10 GW modules. Will be primary DCR beneficiary.',
         'Adani Solar,Adani Green,ADANIGREEN,adani cell,adani module'),
        ('Premier Energies','Premier','HIGH',
         'Dedicated cell maker — direct DCR mandate beneficiary. Watch capacity expansion and new ALCM additions.',
         'Premier Energies,PREMIERENE,premier cell'),
        ('Saatvik Solar','Saatvik','HIGH',
         'Expanding into cell manufacturing — monitor ALCM listing progress and cell line capex.',
         'Saatvik,SAATVIKGL,saatvik cell,saatvik expansion'),
        ('Vikram Solar','Vikram Solar','MEDIUM',
         'Top module exporter — will need cell strategy post DCR. Watch export partnerships.',
         'Vikram Solar,vikram export,vikram cell'),
        ('Tata Power Solar','Tata','MEDIUM',
         'Cell + module + project developer. Integrated play — watch capacity utilization under DCR.',
         'Tata Power Solar,TATAPOWER,tata solar'),
        ('Goldi Solar','Goldi Solar','MEDIUM',
         'Mid-tier module maker — DCR compliance watch. Limited cell capacity.',
         'Goldi Solar,goldi module'),
        ('ReNew Power','ReNew','MEDIUM',
         'Top IPP — large tender winner, will drive module/cell demand. Watch procurement strategy.',
         'ReNew,RENEWPOWER,renew tender,renew solar'),
        ('Greenko Group','Greenko','MEDIUM',
         'Hybrid + storage leader. Key BESS and GH2 tender participant.',
         'Greenko,greenko bess,greenko storage,greenko hydrogen'),
        ('ACME Solar','ACME','MEDIUM',
         'GH2 export pioneer. Watch SIGHT scheme bid participation and offtake MoUs.',
         'ACME Solar,ACME hydrogen,acme gh2'),
    ]
    con = sqlite3.connect(DB_PATH)
    now = datetime.utcnow().isoformat()
    try:
        for (name,group,level,reason,kw) in SEED:
            con.execute("""
                INSERT OR IGNORE INTO v21_watch_companies
                (name,group_name,watch_level,watch_reason,news_keywords,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?)
            """, (name,group,level,reason,kw,now,now))
        con.commit()
    finally:
        con.close()

_seed()
