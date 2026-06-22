# NEURON — Complete Developer Guide
**Emergency Rebuild Reference · v19 "Cockpit of a Mind" · June 2026**

> **v19 front door:** `/` (and `/v19`) now serve the rebuilt 6-surface cockpit
> (`templates/index19.html` + `static/neuron19.css` + `static/neuron_bg.js`,
> dual light/dark, 3D parallax background). The complete pre-P19 app is preserved
> at **`/legacy`** (and `/v18`) — every endpoint, panel and feature intact.

> This guide is the **descriptive** reference (what exists). For the
> **prescriptive** rules every future edit must follow — the additive-only data
> discipline, the module membrane, the security rules, versioning conventions,
> and the release checklist — see **`NEURON_DEV_PROTOCOL.md`**. Read the Protocol
> before changing code.

---

## 1. What Is Neuron

NEURON is a **private, local, daily-use intelligence terminal** for Indian renewable energy. It is a single Flask app that fuses:

- Live government data (MNRE, CEA, SECI, ALMM PDFs)
- Stock market data via Yahoo Finance (NSE RE stocks, global ETFs, commodities, Forex)
- News from 12+ RSS feeds + 540+ background-ingested sources via `sources.py`
- IRENA public API (installed capacity by country — no key needed)
- World Bank API (macroeconomic indicators)
- GDELT API (global event volume timelines)
- An optional NVIDIA LLM key for the analyst synthesis desk

**Brand:** Gold on deep indigo. Private observatory, not a SaaS product. Never regress the World tab, RE Components tab, or v13 theme.

---

## 2. File Structure

```
neuron/
├── neuron.py            # Flask app: all routes, fetchers, intel engine, boot diagnostics
├── sources.py           # 540+ source registry + ingestion worker + entity ledger/correction
├── intelligence.py      # Lead-Lag, Novelty Radar, Synthesis Desk, Stories, prompt sanitizer
├── cognition.py         # v15 think layer (DB-only): beliefs, diff engine, attention, consolidation, self-test
├── memory.py            # v16 MemoryOS (DB-only): curation, dual-hierarchy, multi-tier recall
├── neuron_mcp.py        # v16.3 portable MCP server (FastMCP) over memory.py — neuron + drive scopes
├── decisions.py         # v17 executive function: fuses all faculties → ranked, conviction-scored, falsifiable decisions + self-scoring
├── templates/
│   └── index.html       # Single-page app (all tabs — India, World, RE Components, etc.)
├── static/
│   ├── neuron.css       # v13 gold/indigo theme — NEVER regress
│   └── india_states.geojson
├── user_data/
│   ├── pm_kusum.xlsx    # User-maintained PM-KUSUM data (read on every request)
│   ├── pm_surya_ghar.xlsx
│   └── README.txt
├── neuron.db            # SQLite: alerts, ALMM, news archive, pulse history, entity ledger
├── watchlist.json       # Custom stocks (merged with RE_STOCKS_DEFAULT on boot)
├── requirements.txt
├── .env                 # Secrets — NEVER commit
├── .env.example         # Template
├── setup.bat            # Windows one-shot setup script
└── start.bat            # Windows start script
```

---

## 3. Setup from Zero

### 3.1 Prerequisites

- Python 3.11+ (tested on 3.14)
- Windows (PowerShell) or Linux/macOS
- No Docker needed — purely local

### 3.2 Install

```powershell
# 1. Clone / copy the neuron/ folder
cd "D:\Polygon\Git Projects\neuron"

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # Linux/Mac

# 3. Install dependencies
pip install flask yfinance feedparser numpy pandas requests beautifulsoup4 openpyxl pdfplumber playwright urllib3 waitress

# 4. Install Playwright browser (needed for PM Surya Ghar / PM KUSUM live scraping)
playwright install chromium

# 5. Create .env from template
copy .env.example .env
# Edit .env — add TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, NVIDIA_API_KEY_MAIN, NVIDIA_API_KEY_RERANK
```

### 3.3 Run

```powershell
python neuron.py
# Server starts at http://localhost:5000
```

Or use `start.bat` on Windows (handles venv activation automatically).

---

## 4. Environment Variables (`.env`)

```env
# Telegram bot — optional; enables push alerts
TELEGRAM_BOT_TOKEN=<from @BotFather>
TELEGRAM_CHAT_ID=<your chat ID — auto-discovered on first send or set manually>

# NVIDIA NIM — optional; enables LLM synthesis brief + rerank
NVIDIA_API_KEY_MAIN=<key for qwen/qwen3.5-122b-a10b>
NVIDIA_API_KEY_RERANK=<key for nv-rerank-qa-mistral-4b:1>

# OpenWeatherMap — optional (P18); adds current cloud/temp/wind to RE-hub weather
OPENWEATHER_API_KEY=<from home.openweathermap.org/api_keys>
```

**Without NVIDIA keys**: Neuron falls back to heuristic brief and keyword retrieval — fully functional, just less sophisticated.  
**Without Telegram**: Alerts still show in the UI; push notifications simply don't fire.

---

## 5. Data Sources & APIs

### 5.1 Market Data — Yahoo Finance (no key)

| What | Tickers |
|---|---|
| India RE stocks (default 14) | ADANIGREEN.NS, NHPC.NS, NTPC.NS, SUZLON.NS, SWSOLAR.NS, IREDA.NS, SJVN.NS, WAAREEENER.NS, PREMIERENE.NS, TATAPOWER.NS, TORNTPOWER.NS, INOXWIND.NS, BORORENEW.NS, SAATVIKGL.NS |
| Commodities | GC=F (Gold), CL=F (Crude), SI=F (Silver), NG=F (Nat Gas), ALI=F (Aluminium) |
| Forex | USDINR=X, EURINR=X |
| Global RE ETFs & stocks | ICLN, QCLN, NEE, ENPH, SEDG, FSLR, BEP, TAN, RNW, CSIQ |
| World indices | ^GSPC (S&P500), MCHI (China), EWJ (Japan) |
| India indices | ^NSEI (Nifty50), ^CNXENERGY, ^CNX100 |
| Energy prices | NG=F (Henry Hub), CL=F (Brent), MTF=F (Thermal Coal), TTF=F (TTF Gas) |

Library: `yfinance`. No API key. Rate limit: liquid stocks parallel (6 workers), illiquid sequential with 3 s gap. Retry logic: 5d → 1mo period fallback.

### 5.2 IRENA PxWeb — Installed Capacity (no key)

```
URL: https://pxweb.irena.org/api/v1/en/IRENASTAT/Power Capacity and Generation/Country_ELECCAP_2026_H1_v-PX 1.px
Method: POST with JSON-Stat2 query
Tech codes: "0"=Total RE, "2"=Solar PV, "4"=Wind, "5"=Onshore Wind, "6"=Offshore Wind
Response: JSON-Stat2 format
Cache: 24 h + kv_store fallback
```

Used for: World tab country ranking, India solar history, Wind technology mix.

### 5.3 Government Portals (no key, `verify=False`)

All government HTTP goes through `gov_get()` — a single choke point that sets `verify=False` (NIC/gov TLS chains are broken) and a Chrome UA.

| Source | URL | Method | Cache |
|---|---|---|---|
| MNRE Physical Progress | `https://mnre.gov.in/en/physical-progress/` | BS4 scrape | 1 h |
| MNRE State-wise PDF | `https://cdnbbsr.s3waas.gov.in/...pdf` (auto-discovered) | pdfplumber | 24 h |
| MNRE Notifications | `https://mnre.gov.in/notifications/` | BS4 scrape | 1 h |
| CEA Installed Capacity | `https://cea.nic.in/wp-content/uploads/installed/YYYY/MM/Website.xlsx` | pandas Excel | 24 h |
| CEA Generation | `https://cea.nic.in/wp-content/uploads/generation/...` | pandas Excel | 24 h |
| SECI Tenders | `https://seci.co.in/tenders/` | BS4 scrape | 4 h |
| SECI Auction Results | `https://seci.co.in/auction-results/` | BS4 scrape | 4 h |
| NTPC Tenders | `https://www.ntpc.co.in/en/tenders` | BS4 scrape | 4 h |
| SJVN Tenders | `https://www.sjvn.nic.in/tenders-1` | BS4 scrape | 4 h |
| PM Surya Ghar | `https://pmsuryaghar.gov.in/` | user_data xlsx (primary), Playwright (fallback) | mtime-keyed |
| PM KUSUM | `https://pmkusum.mnre.gov.in/landing.html` | user_data xlsx (primary), Playwright (fallback) | mtime-keyed |
| ALMM List-I | MNRE site PDF | pdfplumber | on-change |
| ALMM Modules List-II | MNRE site PDF | pdfplumber | on-change |
| PV Insights (module prices) | `https://pvinsights.com/` | BS4 scrape | 24 h |

**CEA URL Discovery**: `_cea_url()` first scrapes the page for an xlsx link, then tries months N to N-4, then falls back to a hardcoded April 2026 URL.

**MNRE State PDF Discovery**: `_mnre_state_cap_url()` scrapes `mnre.gov.in` for the latest PDF link, falls back to a hardcoded URL.

### 5.4 World Bank (no key)

```
Base: https://api.worldbank.org/v2/country/IN/indicator/
Indicators used:
  EG.ELC.RNEW.ZS — Renewable electricity output (% of total)
  NY.GDP.MKTP.KD.ZG — GDP growth
  FP.CPI.TOTL.ZG — CPI inflation
Cache: 24 h
```

### 5.5 RSS Feeds (no key)

12 primary feeds parsed by `feedparser`:

| Name | URL |
|---|---|
| Mercom India | `https://mercomindia.com/feed/` |
| SAU Energy | `https://www.saurenergy.com/feed` |
| Solar Quarter | `https://solarquarter.com/feed/` |
| REGlobal | `https://reglobal.co/feed/` |
| EQ Mag | `https://www.eqmagpro.com/feed/` |
| ET Energy | `https://economictimes.indiatimes.com/industry/energy/rssfeeds/13357270.cms` |
| Mint Energy | `https://www.livemint.com/rss/energy` |
| PV Tech | `https://www.pv-tech.org/feed/` |
| CleanTechnica | `https://cleantechnica.com/feed/` |
| Energy Monitor | `https://www.energymonitor.ai/feed/` |
| Reuters Energy | `https://feeds.reuters.com/reuters/businessNews` |
| BBC World | `http://feeds.bbci.co.uk/news/world/rss.xml` |

Global wire sources (Reuters, BBC) are hard-gated — must contain at least one RE keyword before display.

### 5.6 Background Source Ingestion (sources.py — 540+ sources)

A daemon thread cycles through tiers:
- **Tier 1** (T1): every 15 min — SECI, PIB, core RSS
- **Tier 2** (T2): every 1 h — state-level Google News, major themes
- **Tier 3** (T3): every 6 h — long-tail depth queries

Source types:
- `rss` — direct feed
- `gnews` — Google News RSS: `https://news.google.com/rss/search?q=<query>&hl=en-IN&gl=IN&ceid=IN:en`
- `gdelt` — GDELT 2.0 Doc API: `https://api.gdeltproject.org/api/v2/doc/doc?query=<query>&mode=artlist&maxrecords=30&format=json&timespan=3d`
- `api` — structured fetchers in neuron.py (counted, not ingested here)

Region counts: India ≥180, Asia ≥60, Europe ≥60, Africa ≥60, North America ≥60, South America ≥60, Oceania ≥60.

Articles stored in `v11_articles` SQLite table. Retention: 30 days. Pruned every 6 h.

### 5.7 NVIDIA NIM (optional, key in .env)

```
Chat:   https://integrate.api.nvidia.com/v1/chat/completions
Rerank: https://ai.api.nvidia.com/v1/retrieval/nvidia/reranking
Models:
  NVIDIA_API_KEY_MAIN  → qwen/qwen3.5-122b-a10b (primary), fallback: qwen/qwen3-next-80b-a3b-instruct, meta/llama-3.3-70b-instruct
  NVIDIA_API_KEY_RERANK → nv-rerank-qa-mistral-4b:1
```

Used for: Synthesis brief (`/api/intel/synthesis`) and Ask NEURON (`/api/ask`). Heuristic fallback always available.

### 5.8 GDELT (no key)

```
Volume timeline: https://api.gdeltproject.org/api/v2/doc/doc?query=<q>&mode=timelinevol&format=json&timespan=14d
Article list:   https://api.gdeltproject.org/api/v2/doc/doc?query=<q>&mode=artlist&maxrecords=30&format=json&timespan=3d
```

Used in Novelty Radar to detect global spikes not yet in Indian press.

### 5.9 Telegram Bot API (optional)

```
Send: https://api.telegram.org/bot<TOKEN>/sendMessage
Body: {"chat_id": ..., "text": ..., "parse_mode": "HTML"}
```

Alerts fire on: Intel pulse ≥80 (4 h cooldown), term spikes ≥3× ratio, SECI new tenders.

### 5.10 YouTube (no key)

```
Live check: https://www.youtube.com/channel/<channel_id>/live
  — looks for '"isLive":true' in HTML, extracts videoId via regex
RSS fallback: https://www.youtube.com/feeds/videos.xml?channel_id=<channel_id>
Cache: 5 min
```

11 live news channels: WION, ET Now, CNBC TV18, India TV, Bloomberg, CNBC, Sky News, DW News, DD News, NewsX, Al Jazeera.

---

## 6. Database Schema (SQLite — `neuron.db`)

```sql
-- Alert tracking
alerts_seen        (uid TEXT PK, ts REAL)
alerts_log         (uid TEXT PK, title, source, category, keywords, link, ts)

-- ALMM
almm_meta          (id PK, pdf_url, pub_date, parsed_at, record_count)
almm_list          (id AUTOINCREMENT, mfr, model, capacity_wp, efficiency, technology, validity_date, parent_company, meta_id)
almm_modules_meta  (id PK, pdf_url, pub_date, parsed_at, record_count)
almm_modules       (id AUTOINCREMENT, mfr, model, capacity_mw_yr, efficiency, module_type, module_wp, validity_from, validity_to, parent_company, meta_id)

-- News
news_archive       (uid PK, source, title, link, summary, published_dt, days_old, ts)

-- CEA capacity snapshots (historical growth chart)
cea_statewise_snap (id AUTOINCREMENT, ts, date, region, state, cumulative_mw, monthly_mw)
cea_national_snap  (id AUTOINCREMENT, ts, snap_date, re_total_mw, solar_mw, wind_mw, hydro_mw, grand_total_mw)

-- Sector breadth / sentiment history
pulse_history      (id AUTOINCREMENT, ts, date, pulse, label, hot_topics, articles_processed, bullish_count, bearish_count, neutral_count)
breadth_history    (id AUTOINCREMENT, ts, snap_date, breadth_20, breadth_50, breadth_200)
fear_greed_history (id AUTOINCREMENT, ts, snap_date, score, label, breadth, pulse_dir, rsi_nifty, brent_dir)

-- Key-value store (Telegram chat_id, IRENA cache, synthesis cache, etc.)
kv_store           (key TEXT PK, value TEXT)

-- v11 Observatory (background ingestion)
v11_articles       (uid PK, source_id, region, category, title, link, summary, published_dt, tone, fetched_ts)
v11_source_health  (source_id PK, region, tier, ok, err, last_ok, last_err, last_msg, last_items)
v11_kv             (key PK, value, ts)

-- v12
v12_fts            VIRTUAL TABLE fts5(uid UNINDEXED, title, summary)  -- full-text search
v12_signal_ledger  (rule_id, fired_at, confirm_by, status, resolved_at)  -- lead-lag self-scoring

-- v14 Living Memory
v14_entity_ledger  (entity_id PK, entity_type, title, first_seen, last_seen, status, status_history JSON, state, capacity_mw, key_players JSON, last_source_uid)

-- v15 Nervous System (cognition layer + security audit; all additive)
v15_beliefs        (metric PK, value, unit, label, confidence, source, as_of, last_revised, revision_count, conflict, note, updated_ts)
v15_belief_history (id AUTOINCREMENT, metric, old_value, new_value, delta_pct, source, as_of, ts, note)
v15_daily_delta    (delta_date PK, run_ts, summary, night_memo, payload JSON)  -- one row/day, "what changed since yesterday"
v15_prompt_guard_log (id AUTOINCREMENT, ts, source, pattern, snippet)          -- neutralised prompt-injection attempts
v15_entity_audit   (id AUTOINCREMENT, entity_id, op, before_json, after_json, reason, ts)  -- ledger corrections (delete=archive)

-- v16 MemoryOS (living memory; additive)
v16_facts          (fact_id PK, scope, kind, text, entity_id, state, capacity_mw, players JSON, category, direction, source_uid, source_id, event_ts, created_ts, tier, heat, access_count, last_access, canonical_id)
v16_vectors        (fact_id PK, scope, dim, embedder, vec BLOB)  -- semantic tier; floor embedder = numpy char-3gram hash (D=256)

-- v17 Executive function (decision ledger + self-scoring; additive)
v17_decision_ledger (decision_id PK, created_ts, created_date, dkey, thesis, action, ticker, direction, conviction, band, horizon_days, falsifier, entry_price, rationale JSON, status, resolved_ts, exit_price, outcome_note)
```

---

## 7. All API Endpoints

All return JSON. Cache-busting: most endpoints serve from an in-memory cache dict with TTL.

### Core Data

| Endpoint | TTL | Description |
|---|---|---|
| `GET /` | — | Renders `index.html` |
| `GET /api/health` | real-time | Source health map + server uptime |
| `GET /api/quotes` | 5 min | All RE stock quotes with sparklines |
| `GET /api/news` | 30 min | RSS news, scored/filtered |
| `GET /api/news/archive` | — | 5–15 day old articles from SQLite |
| `GET /api/news/region/<region>` | 30 min | Articles by region from v11 (india/asia/europe/africa/etc.) |
| `GET /api/commodities` | 5 min | Gold, Crude, Silver, Nat Gas, Aluminium + Forex |
| `GET /api/energy_prices` | 30 min | Henry Hub, TTF, Brent, Thermal Coal, EU ETS |
| `GET /api/global_re` | 5 min | Global RE ETFs + world indices |
| `GET /api/india_indices` | 15 min | Nifty50, Nifty Energy, Nifty 100 |
| `GET /api/global_capacity` | 24 h | IRENA installed RE capacity by country (Top 25) |
| `GET /api/solar_capacity_history` | 24 h | IRENA India solar PV history + CAGR projection to 2030 |
| `GET /api/wind_tech_mix` | 24 h | IRENA India onshore/offshore wind breakdown |

### India Government Data

| Endpoint | TTL | Description |
|---|---|---|
| `GET /api/mnre_live` | 1 h | MNRE physical progress table (monthly + cumulative MW) |
| `GET /api/mnre_notifications` | 1 h | MNRE policy notifications |
| `GET /api/mnre_state_capacity` | 24 h | MNRE state-wise RE installed capacity PDF |
| `GET /api/statewise` | 24 h | CEA IC sheet — region + state-level RE capacity |
| `GET /api/cea_history` | 24 h | CEA national capacity snapshots for historical chart |
| `GET /api/seci_tenders` | 4 h | Active SECI tenders with MW/tech classification |
| `GET /api/seci_results` | 4 h | SECI auction results |
| `GET /api/pm_surya_ghar` | mtime-keyed | PM Surya Ghar state data (Excel → Playwright fallback) |
| `GET /api/pm_kusum` | mtime-keyed | PM KUSUM state data (Excel → Playwright fallback) |

### ALMM

| Endpoint | TTL | Description |
|---|---|---|
| `GET /api/almm` | on-change | ALMM List-I (approved cells+wafers) |
| `GET /api/almm/check_update` | — | Check if new ALMM PDF exists |
| `GET /api/almm/force_reparse` | — | Force re-parse of ALMM PDF |
| `GET /api/almm/modules` | on-change | ALMM List-II (approved module manufacturers) |
| `GET /api/almm/modules/force_reparse` | — | Force re-parse of modules PDF |
| `GET /api/almm/modules/search?q=` | — | Search ALMM modules |
| `GET /api/almm/tech_mix` | on-change | Module technology mix chart (Mono/Poly/Bifacial) |

### Intelligence & Analytics

| Endpoint | TTL | Description |
|---|---|---|
| `GET /api/brief` | 5 min | Daily intelligence brief (stocks + MNRE + SECI + signals) |
| `GET /api/signal_score` | — | Signal Intelligence Score (CRITICAL/HIGH/MEDIUM/LOW) |
| `GET /api/intel_engine` | 30 min | Full intel engine: pulse, action flags, term spikes, sentiment |
| `GET /api/intel_engine/refresh` | — | Force-refresh intel engine |
| `GET /api/pulse_history` | — | 30-day pulse history from SQLite |
| `GET /api/alerts` | — | Active alerts by keyword category |
| `GET /api/alerts/history` | — | Last 100 alerts from SQLite |
| `GET /api/correlation` | 1 h | 3-month correlation matrix (RE stocks + USD/INR + Crude + ETFs) |

### Observatory (v11 Background Intelligence)

| Endpoint | TTL | Description |
|---|---|---|
| `GET /api/sources/stats` | — | Registry counts, health by region, articles 24h |
| `GET /api/region_velocity` | — | Articles/hour by region vs 7-day baseline |
| `GET /api/pipeline` | — | Living-memory entity pipeline (recent 80 entities) |
| `GET /api/pipeline/<query>` | — | Pipeline filtered by state/player name |
| `DELETE /api/pipeline/entity/<id>` | — | Correct ledger: archive→remove a false entity (body `{"reason"}`) |
| `PATCH /api/pipeline/entity/<id>` | — | Correct ledger fields: `{"fields": {...}, "reason"}` (whitelisted) |

### Cognition — Nervous System (v15)

| Endpoint | TTL | Description |
|---|---|---|
| `GET /api/delta/today` | per-day | Diff engine: status changes, CEA delta, new tenders/companies since yesterday |
| `POST /api/delta/run` | — | Force a consolidation (sleep-cycle) pass now |
| `GET /api/beliefs` | — | Current belief state (RE/solar/wind/hydro GW) + standing conflicts |
| `GET /api/attention` | — | Unusualness flags (status clusters, actor bursts, velocity, tender surge) |
| `GET /api/self_test` | — | In-process invariant suite (network-free), structured pass/fail |
| `GET /api/decisions` | — | P17 executive function: ranked, conviction-scored, falsifiable decisions fused across all faculties (`?narrative=1` adds an LLM read) |
| `GET /api/decisions/scorecard` | — | P17 self-calibration: hit-rate by conviction band as decisions resolve |

### MemoryOS — Living Memory (v16)

| Endpoint | TTL | Description |
|---|---|---|
| `GET /api/memory/recall?q=&k=&when=&scope=` | — | Unified recall: semantic (vector KNN) + keyword + temporal + structured fusion, ranked with provenance |
| `GET /api/memory/stats` | — | Fact counts by tier/kind/scope, vector count, embedder, curate cursor |
| `POST /api/memory/add` | — | Teach Neuron a fact directly: `{"text": "...", "scope": "neuron"}` |

**Semantic embedder (v16.2):** recall uses `BAAI/bge-small-en-v1.5` (384-dim, local
ONNX via `fastembed`) when installed; otherwise a zero-dependency numpy floor
embedder. Wired at boot by `neuron._init_embedder()` → `memory.set_embedder()`;
existing vectors migrate via `memory.reembed_all()` in a background thread.

### Portable Memory MCP Server (v16.3 — `neuron_mcp.py`)

A separate FastMCP process (`python neuron_mcp.py`, stdio) exposing the SAME
`memory.py` engine to any MCP client (Claude Desktop, IDE). Two scopes share one
DB but never mix: `neuron` (RE intelligence) and `drive` (your own files).
Tools: `memory_recall`, `drive_search`, `drive_index(path)`, `memory_add`,
`memory_timeline`, `memory_stats`. `drive_index` skips build/dep dirs and never
indexes secrets (`.env`, `*.key/*.pem`, names containing secret/token/password).
Needs `pip install mcp`; the dashboard never imports it.

### Synthesis Desk (v12)

| Endpoint | TTL | Description |
|---|---|---|
| `GET /api/intel/early_signals` | 30 min | Lead-lag engine: upstream signals before Indian press |
| `GET /api/intel/novelty` | 1 h | Novelty radar: GDELT spikes vs Indian coverage |
| `GET /api/chokepoints` | 1 h | P16.4 — maritime chokepoint stress (Hormuz/Red Sea/Malacca/Panama) + India energy-import exposure; keyless (GDELT + corpus + lead-lag) |
| `GET /api/intel/synthesis` | 6 h | LLM analyst brief (heuristic fallback) |
| `GET /api/intel/synthesis?force=1` | — | Force-refresh synthesis brief |
| `GET /api/intel/standing` | 6 h | Standing questions answered via rerank |
| `GET /api/stories` | 30 min | TF-IDF clustered story groups |
| `GET /api/archive/search?q=` | — | FTS5 full-text archive search |
| `POST /api/ask` | — | Ask NEURON analyst question: `{"question": "..."}` |

### Sector Metrics (v7)

| Endpoint | TTL | Description |
|---|---|---|
| `GET /api/sector_breadth` | 1 h | % of RE stocks above SMA20/50/200 |
| `GET /api/breadth_history` | — | Historical breadth from SQLite |
| `GET /api/fear_greed` | 1 h | Fear & Greed composite score |
| `GET /api/fear_greed/history` | — | Historical fear/greed |
| `GET /api/sentiment_spread` | 30 min | Bullish/bearish/neutral article counts |
| `GET /api/re_velocity` | — | Article velocity ratio by region |
| `GET /api/re_implications` | 30 min | Policy/macro regime implications |
| `GET /api/re_regime` | 1 h | Current market regime classification |
| `GET /api/re_forecast` | 6 h | Sector growth forecast |

### Company & Market

| Endpoint | TTL | Description |
|---|---|---|
| `GET /api/company_news` | 30 min | yfinance news for each watchlist stock |
| `GET /api/focus_stock` | 1 h | Saatvik deep-dive (52w range, PE, promoter %) |
| `GET /api/sector_history?period=1mo` | 1 h | Normalized sector overlay (6 stocks) |
| `GET /api/history/<symbol>` | — | OHLCV history for any symbol |
| `GET /api/analysis/<symbol>` | — | Technicals (RSI, MACD, Bollinger) + projection |
| `GET /api/pv_prices` | 24 h | PV module/cell/wafer/polysilicon prices (pvinsights.com) |

### Streaming & State

| Endpoint | TTL | Description |
|---|---|---|
| `GET /api/stream` | — | Server-Sent Events stream for live price ticks |
| `GET /api/state/<name>` | — | State-specific generation/capacity data |

### Dashboard (consolidated)

| Endpoint | TTL | Description |
|---|---|---|
| `GET /api/dashboard` | — | Combined payload: quotes + news + MNRE + brief + sector + signals |

### Watchlist Management

| Endpoint | Method | Description |
|---|---|---|
| `/api/watchlist` | GET | Current watchlist |
| `/api/watchlist` | POST | Add/remove ticker: `{"action": "add"/"remove", "symbol": "...", "name": "..."}` |

### Telegram

| Endpoint | Description |
|---|---|
| `GET /api/telegram/setup` | Show setup instructions, token status |
| `POST /api/telegram/test` | Send test message |
| `GET /api/telegram/config` | Current config (token masked) |

### Other

| Endpoint | Description |
|---|---|
| `GET /api/live_channels` | Defined live TV channels list |
| `GET /api/youtube_live/<channel_id>` | Resolve live videoId for a channel |
| `GET /api/worldbank` | World Bank renewable % series |
| `GET /api/india_macro` | GDP growth + CPI from World Bank |
| `GET /api/iex_power` | Power market proxy (PRAAPTI link) |
| `GET /api/mnre_notifications` | MNRE policy notifications |
| `GET /api/observatory/weather` | Open-Meteo irradiance/wind data |
| `GET /api/cea_generation` | CEA generation data |

---

## 8. Core Architecture Patterns

### 8.1 Cache

```python
cache = {}          # in-memory, process-scoped
CACHE_TTL = 300     # 5 min default

get_cache(key, ttl)  # returns None if expired
set_cache(key, data) # stores with current timestamp
```

Two-tier caching for long-lived data: in-memory (fast) + SQLite `kv_store` (survives restart).

### 8.2 NaN-safe JSON

`jsonify()` is monkey-patched via `_fix_nan()` to replace `float('nan')` and `inf` with `None` — browsers reject raw NaN in JSON.

### 8.3 Stampede Guard

`@serialized` decorator: wraps expensive fetchers (ALMM PDF parse, MNRE scrape) with a threading lock so two concurrent cold requests trigger only one parse, not two 280-page PDF parses.

### 8.4 Gov HTTP

```python
gov_get(url, timeout=20, headers=None, method="get")
# verify=False — intentional, NIC TLS chains are broken
# User-Agent: Chrome/124 — gov sites reject Python UA
```

### 8.5 Intel Classification

`classify_article(text)` → `(category, direction)` using 12 category keyword lists in `INTEL_CATEGORIES`. Direction is POSITIVE / NEGATIVE / NEUTRAL per `INTEL_DIRECTION`.

`extract_entities(text)` → `{company, mw, tariff, crore}` using regex + `COMPANY_ENTITIES` map.

### 8.6 Living Memory (v14 Entity Ledger)

When a new article is ingested from India sources, `_record_entity()` in `sources.py`:
1. Extracts status keywords (announced → bid_open → awarded → commissioned, or stalled)
2. Extracts capacity (MW/GW), state, and known RE player names
3. Upserts to `v14_entity_ledger` — status only advances (no regressions), history is append-only JSON

Durable facts survive the 30-day article retention window.

---

## 9. Key Constants

```python
# neuron.py
CACHE_TTL = 300             # default cache TTL (seconds)
ALERT_KEYWORDS = {...}      # 7 alert categories with keyword lists
INTEL_CATEGORIES = {...}    # 12 intel categories
COMPANY_ENTITIES = {...}    # company name → NSE ticker map
LIVE_CHANNELS = [...]       # 11 YouTube channels
RE_STOCKS_DEFAULT = {...}   # 14 core RE stocks

# sources.py
TIER_INTERVAL = {1: 900, 2: 3600, 3: 21600}
RETENTION_DAYS = 30

# intelligence.py
LEAD_LAG_RULES = [...]      # 14 lead-lag rules
NOVELTY_QUERIES = [...]     # 10 GDELT queries for novelty radar
MODEL_MAIN = "qwen/qwen3.5-122b-a10b"
MODEL_RERANK = "nv-rerank-qa-mistral-4b:1"
```

---

## 10. Smoke Test

Run after any rebuild to verify all critical paths:

```powershell
python smoke_test.py
```

Checks:
- All API endpoints return 200
- MNRE data has `total_re_mw` > 0
- IRENA capacity returns top 25 countries
- Entity ledger passes status-progression invariant (no commissioned-before-awarded regressions)
- Observatory tables exist and ingestion is running

---

## 11. User Data Files

**These are live-read on every request** (cache key = file mtime):

| File | Columns | Update frequency |
|---|---|---|
| `user_data/pm_kusum.xlsx` | State_Name, Total_Sanction_MW, Total_Installed_MW | When MNRE releases new data |
| `user_data/pm_surya_ghar.xlsx` | State / UT, Applications (No.), Installations (No.), Households Covered (No.), Installation Capacity (MW), Subsidy Released (Cr) | When PM Surya Ghar portal updates |

Edit → save → refresh dashboard. No server restart needed.

---

## 12. Adding a New Stock

Option A — `watchlist.json`:
```json
{"SYMBOL.NS": "Display Name"}
```

Option B — `POST /api/watchlist`:
```json
{"action": "add", "symbol": "SYMBOL.NS", "name": "Display Name"}
```

The new stock is immediately merged into `RE_STOCKS` and fetched on next quote refresh.

---

## 13. Adding a New Data Source

**RSS/Google News (background):** Add to `sources.py` `_add(...)` calls. It's picked up by the daemon automatically on next boot.

**New API endpoint:**
1. Write a `fetch_xyz()` function with `get_cache / set_cache` and `mark_health(...)` calls.
2. Add `@app.route("/api/xyz")` that returns `jsonify(fetch_xyz())`.
3. Wire the data into `index.html` via a new `fetch('/api/xyz').then(...)` call.

---

## 14. Deployment Notes

- Neuron is designed for **local use** — no auth, no HTTPS, no rate limiting.
- For remote access: run behind nginx with basic auth.
- `waitress` is installed for production-grade WSGI if Flask dev server isn't enough.
- The app is stateful (in-memory cache, background threads) — only one instance per DB.
- `neuron.db` uses WAL journal mode to allow concurrent reads during writes.

---

## 15. Phase History (context for future rebuilds)

| Phase | Theme | Key additions |
|---|---|---|
| v1–v3 | Foundation | Basic Flask, news, stock cards |
| v4 | Intel Engine | Signal score, daily brief, SECI, Telegram |
| v5 | ALMM | List-I/II PDF parsing, module tech mix |
| v6 | Intelligence v1 | Intel categories, pulse, lead-lag (basic), company signals |
| v7 | Sector Metrics | Fear & Greed, breadth, sentiment, sector overlay |
| v8–v9 | Observatory | 540+ source registry, background ingestion worker |
| v10 | Audit & Hardening | Dependency audit, NaN-safe JSON, @serialized guard |
| v11 | Observatory full | v11_articles, v11_source_health, full GDELT integration |
| v12 | Intelligence v2 | TF-IDF stories, FTS5 archive, lead-lag self-scoring, Ask NEURON |
| v13 | Theme + World tab | Sealed gold/indigo theme, World tab (global capacity, IRENA) |
| v14 | Living Memory | IRENA PxWeb backbone, v14_entity_ledger, solar history CAGR, Wind tech mix, IEA investment stamp |
| v15 | Nervous System | `cognition.py` (DB-only membrane): beliefs/diff/attention/consolidation; prompt-injection sanitizer; worker watchdog + heartbeat; entity correction+audit; boot diagnostics; `/api/self_test`. Additive + backend-only. See `NEURON_DEV_PROTOCOL.md`. |
| v16 | God-Tier Memory | `memory.py` MemoryOS (DB-only, network-free): Curation Agent → Dual-Hierarchy (timeline + semantic vector) → multi-tier STM/MTM/LPM + heat → unified `recall()` fusion. 16.2: fastembed bge-small embedder. 16.3: `neuron_mcp.py` FastMCP drive server. 16.4: `/api/chokepoints` India import-exposure tracker. Plan: `NEURON_SESSION_PLAN_P16.md`. |
| v17 | Executive Function | `decisions.py` (DB-only reasoning, imports lower layers, never neuron): fuses implications+chokepoints+attention+beliefs+lead-lag into ranked, conviction-scored, falsifiable decisions with memory citations; STRONG requires cross-faculty corroboration. `v17_decision_ledger` self-scores calls to outcomes → `/api/decisions/scorecard` calibration. Plan: `NEURON_SESSION_PLAN_P17.md`. |
| v19 | Cockpit of a Mind | Complete frontend rebuild (from scratch, all endpoints/data preserved). `/` → new 6-surface IA grouped by cognitive function (Briefing · Markets · India · World&Trade · Intelligence · Live), dual light/dark, 3D parallax BG (`neuron_bg.js`), motion-encodes-state, decisions-with-calibration. `ALCM/` ownership atlas (`/api/alcm/atlas`, mtime-keyed group-level HHI/CR4 — fixes naive entity-level ALMM calc). Deep-Read Agent (`/api/deep_read` → Top-1% one-pager). Legacy app preserved at `/legacy`. Files: `index19.html`, `neuron19.css`, `neuron_bg.js`, `decisions.py`, `ALCM/`. |
| v18 | Data & Export Fixes | PM Surya Ghar new 6-col schema (State/UT · Applications · Installations · Households · Capacity MW · Subsidy Cr); KUSUM `Total`-row double-count fixed (total-row-safe `_split_total_rows`/`_clean_num` helpers); both India panels auto-load real xlsx data (generic placeholders removed); OpenWeatherMap current conditions enrich RE-hub weather (keyless-degrading); **PDF export redesigned** — print-only `@media print` strips the animated backdrop (was rasterizing to a 7.8MB/76-image file) for a clean editorial light document with selectable text + disciplined pagination. Backend + print-CSS only; on-screen v13 theme untouched. |
| v20 | Reach & Voice | IMF macro/trade beliefs (keyless IMF DataMapper → v15 belief layer; GDP/CPI/CAD/debt 2026; `/api/india_macro_plus`). Polymarket forecast cross-check (keyless Gamma API, energy/geo filtered; `/api/forecast_markets`). Proactive STRONG-decision Telegram push (`push_strong_decisions`, gated band==STRONG & corroboration≥2 & deduped; `POST /api/decisions/push`). New cockpit frontend (`index20.html` + `neuron20.css` + `neuron_bg20.js`) serving at `/`; v19 shell preserved at `/cockpit`. |
| v21 | Source Expansion | `sources.py` 540 → **1,149 sources** (+609 net, all `p21_` prefixed): 73 RSS feeds, 414 gnews queries, 56 GDELT queries, 20 API sources. Regional coverage: India 308, Asia 135, Europe 126, Africa 118, NA 118, SA 105, Oceania 87, Global 152. `/api/observatory/weather` parallelised (ThreadPoolExecutor ×5) — cold fetch 75s → 5.8s. Smoke test v20 assertion fixed. smoke GREEN 100/100 checks. |
