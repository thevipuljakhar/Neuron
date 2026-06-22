# NEURON v3 — Change Log, Bug Fixes & Architecture Notes

**Built:** 2026-06-03  
**Session:** v2 → v3 upgrade + full diagnostic + live verification  
**Verified:** All 14 stocks live, all 19 API routes passing, NSE market hours

---

## 1. What Changed from v2 → v3

### Backend (`neuron.py`) — Key additions

| Change | Why |
|---|---|
| `SAATVIKGL.NS` added as first-class stock | Owner's primary stock — BSE 544526 |
| `sqlite3` — `neuron.db` with `alerts_seen` + `alerts_log` | Alerts persist across server restarts |
| `SOURCE_HEALTH` dict + `mark_health()` on every fetcher | Header health dots, `/api/health` endpoint |
| `fetch_seci_tenders()` — requests+BS4 (no JS needed) | SECI table is static HTML, Playwright not required |
| `_playwright_fetch()` helper — direct `playwright.sync_api` | Replaced broken scrapling for PM scheme pages |
| `fetch_correlation()` — 12×12 matrix with tz-normalization | Cross-sector macro view; IST/EST date alignment fix |
| `FOREX` dict — `USDINR=X`, `EURINR=X` merged into commodities | RE is import-heavy; currency is a hidden driver |
| `GLOBAL_RE` expanded — added FSLR, BEP, TAN, RNW, CSIQ | Better global RE basket |
| `_LIQUID` set + 2-lane fetch strategy | Prevents Yahoo Finance rate-limiting PREMIERENE/BORORENEW |
| `fetch_quote()` — 5d→1mo fallback period | Illiquid tickers occasionally return empty on 5d |
| `load_watchlist()` / `save_watchlist()` + POST `/api/watchlist` | Runtime stock add/remove without server restart |
| `/api/alerts/history` — SQLite read, last 200 | Alert history tab in drawer |

### Frontend (`templates/index.html`) — Key additions

| Change | Why |
|---|---|
| **Portfolio tab** (8th tab) | Track holdings vs CMP, P&L chart, allocation pie |
| **Correlation heatmap** in Analytics | 12×12 Plotly heatmap — diverging red/green colorscale |
| **SECI Live Tenders panel** in News tab | Shows 13 active tenders with deadlines and direct links |
| **Alert History tab** in drawer | Live / History two-tab drawer |
| **Watchlist modal** (⚙ button) | Add/remove NSE tickers from UI |
| **Source health dots** in header | Real-time data source status |
| **USDINR pill** in header | Live forex from commodities feed |
| **Saatvik Green ★** — gold border, first position, default analytics | Owner's focus stock |
| `buildCommTable` → shows forex with ₹ prefix | USDINR, EURINR displayed correctly |
| `showAlertTab()` — Live/History drawer tabs | Alert history accessible from UI |

---

## 2. Bugs Found & Fixed (Diagnostic Session)

### Critical — would prevent startup or crash server

| # | Bug | Fix |
|---|-----|-----|
| 1 | Unicode box-drawing chars in ASCII banner → `UnicodeEncodeError` on Windows cp1252 | Replaced with plain ASCII `=`-border banner |
| 2 | SECI scraper used scrapling (broken) | Rewrote to `requests+BS4` — SECI table is plain HTML |
| 3 | PM Surya Ghar + KUSUM used scrapling (broken) | Rewrote to `playwright.sync_api` directly |

### Data quality — silent failures

| # | Bug | Fix |
|---|-----|-----|
| 4 | Saur Energy RSS → HTTP 404 | Replaced with Solar Quarter (`solarquarter.com/feed/`) |
| 5 | IEEFA RSS → consistently 0 entries | Replaced with EQ Mag (`eqmagpro.com/feed/`) |
| 6 | ET Energy wrong RSS feed ID (`13358393`) | Fixed to `13357270` (50 entries, verified) |
| 7 | `PREMIENERG.NS` → 404 on Yahoo Finance | Corrected to `PREMIERENE.NS` (NSE: Premier Energy) |
| 8 | `BOROSIL.NS` → empty on Yahoo Finance | Corrected to `BORORENEW.NS` (NSE: Borosil Renewables) |
| 9 | `WEBSOL.NS` → genuinely delisted on Yahoo Finance | Removed from watchlist |
| 10 | Stale `watchlist.json` with old tickers surviving server restart | Regenerated with all corrected tickers |

### JavaScript bugs

| # | Bug | Fix |
|---|-----|-----|
| 11 | Dead code: `buildStockGrid` tried to read USDINR from `allQuotes` (wrong dict) | Removed; USDINR set in `buildCommTable` from commodities endpoint |

### Correlation matrix bugs

| # | Bug | Fix |
|---|-----|-----|
| 12 | Correlation matrix: all zeros (NaN from `json.dumps`) | Added `.fillna(0)` before `.values.tolist()` |
| 13 | Correlation matrix: all zeros because `pd.DataFrame(series).dropna()` → 0 rows | NSE timestamps are IST (+05:30), US are EST — normalize all to `date()` before join |
| 14 | Correlation matrix fix: used `fillna(method='ffill')` — invalid in pandas 3.x | Changed to `.ffill()` method call directly on DataFrame |

---

## 3. Architecture Decisions

### Why requests+BS4 for SECI (not Playwright)

Tested live: `seci.co.in/tenders/` returns a complete HTML table in the static response.
Row format: `[blank, TenderID, ETS_ref, TenderRef, Title, PubDate, BidDate, ViewDetails]`
13 tenders returned, links format `/tender-details/<hash>`.
No JavaScript execution needed. Playwright would be overkill and slower.

### Why direct playwright.sync_api for PM schemes (not scrapling)

scrapling's `StealthyFetcher` requires `patchright` (not installed).
scrapling's `Fetcher` requires `browserforge` (not installed).
scrapling's `DynamicFetcher` requires `msgspec` (not installed).
**All scrapling fetchers are broken.** playwright is installed and working.
Use `from playwright.sync_api import sync_playwright` directly.

### Why 2-lane stock fetch

Yahoo Finance rate-limits bulk requests. 12 parallel requests for large-caps work fine.
PREMIERENE.NS and BORORENEW.NS (illiquid) consistently fail in parallel burst.
Solution: `_LIQUID` set defines the 12 fast stocks. Remaining 2 fetch sequentially
with `time.sleep(3)` gap after parallel completion. Both confirmed live when isolated.

### Correlation date normalization

NSE stocks: timestamps like `2026-03-04 00:00:00+05:30` (IST-aware)
US stocks (TAN, ICLN, CL=F, USDINR=X): timestamps like `2026-03-04 00:00:00-05:00`
`pd.DataFrame()` cannot align these — index union has no matches → all NaN → `dropna()` → 0 rows.

**Fix:** `s.index = pd.to_datetime([d.date() for d in s.index])` before building DataFrame.
Then `.ffill().dropna()` fills weekend gaps (NSE/NYSE trading day mismatches).
Result: 66 rows of aligned daily data, diagonal = 1.000, real cross-correlations.

---

## 4. Live Verification Results (2026-06-03, 14:50 IST)

```
STOCK PRICES (NSE OPEN):
  SAATVIKGL.NS    Saatvik Green    Rs 465.8   +4.11%  *** FOCUS STOCK
  BORORENEW.NS    Borosil Ren.     Rs 544.4   +8.59%
  NHPC.NS         NHPC             Rs  75.35  +4.23%
  PREMIERENE.NS   Premier Energy   Rs 1079.9  +0.51%
  NTPC.NS         NTPC             Rs 368.35  +0.26%
  ADANIGREEN.NS   Adani Green      Rs 1432    -1.23%
  ... (14/14 total)

MNRE LIVE (as on 30.04.2026):
  Solar:     154.2 GW
  Wind:       56.4 GW
  Hydro:      51.4 GW
  Total RE:  279.3 GW (55.9% of 500 GW target)

SECI TENDERS: 13 active
  SECI000256 | RfS 12250 kW Rooftop Solar PV (JNV Buildings)  | Deadline 10/07/2026
  SECI000254 | RfS 5500 kW Rooftop Solar PV                   | Deadline 30/06/2026
  SECI000250 | RfS 2000 MW Wind Power Projects                 | Deadline 12/06/2026
  ... (13 total)

CORRELATION (Saatvik vs others, 90d):
  vs Adani Green: 0.80  (high — same sector)
  vs IREDA:       0.87  (high — RE financing)
  vs USD/INR:     0.59  (moderate — import sensitivity)
  vs Crude Oil:   0.24  (low — RE independence ✓)
  vs TAN ETF:     0.42  (moderate — global solar linked)

API ROUTES: 19/19 PASSED
SOURCE HEALTH: 19/19 OK
```

---

## 5. File Checksums / Line Counts

```
neuron.py            ~720 lines
templates/index.html ~1300 lines
watchlist.json       14 stocks
neuron.db            SQLite, tables: alerts_seen, alerts_log
```

---

## 6. How to Start

```bash
cd "D:\Polygon\Git Projects\Neuron"
python neuron.py
# → http://localhost:5000
# First load takes ~15s (stock fetch + retry for illiquid tickers)
# All 14 stocks visible once load completes
```

**If stocks are missing on first load:** wait 5 minutes for cache refresh (5-min TTL).
PREMIERENE and BORORENEW are the two that occasionally need the retry cycle.

---

## 7. Next Steps for V4

See `CONTEXT_FOR_NEW_WINDOW.md` → V4 Ideas section.
Priority order: CEA daily generation → REC price tracker → module ASP → tariff NLP → USDINR overlay.
