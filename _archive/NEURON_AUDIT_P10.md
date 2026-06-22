# NEURON — Full Audit & Forward Plan (P10 Handoff)
**Audited:** 2026-06-11 · neuron.py ~3200 lines · index.html ~6000 lines · against live server
**Verdict:** Feature-rich and impressive, but it has grown faster than its foundations. The bugs below are mostly *consistency* bugs — the same fact computed differently in different places. That is the #1 systemic disease.

---

## P0 — CRITICAL BUGS (fix first, in this order)

### BUG-1: MNRE total is 4× inflated in World tab + Export §1  ⚠ INTRODUCED LAST SESSION
- `/api/mnre_live` returns rows including **aggregates**: `Sub Total (Exc. Large Hydro)`, `Total Non-Fossil`, `Total RE`, plus `Nuclear Power`.
- `loadWorldTab()` and Export §1 sum **all** `cumulative_mw` → **1,096.6 GW** displayed instead of **279.3 GW**.
- Export §1 chart also plots aggregate rows as if they were technologies.
- **Fix:** backend should tag rows (`is_aggregate: true`) or frontend must read the `Total RE` row directly, never sum. Exclude `Nuclear Power` from RE displays (it's non-fossil, not RE).

### BUG-2: user_data Excel cached 6 hours — README promises live reads
- `fetch_pm_kusum()` → `get_cache("pm_kusum", 21600)`. README.txt says "Neuron reads these files on every request."
- **This is why Vipul's xlsx edits "didn't show up"** — root cause of a real user complaint we mis-diagnosed as a frontend issue.
- **Fix:** for user_data reads, key the cache on file `mtime` (or drop cache — local xlsx read is ~50ms). Same check for `fetch_pm_surya_ghar()`.

### BUG-3: One fact, many values — no single source of truth
| Fact | Sources found | Values |
|---|---|---|
| India total RE | CEA col 11 (statewise) / MNRE live sum / hardcoded "279 GW", "282 GW" in HTML | 279.3 / 1096.6(!) / 279 / 282 |
| US RE capacity | World tab "~380 GW" / old export "262 GW" | static, contradictory |
| China RE | "~1500 GW" / "887 GW" | static, contradictory |
| EU carbon | static 65.0 in energy_prices | stale "2025 ref" |
- **Fix:** one `/api/canonical` block (or constants module) — every tab reads the same key. Static world figures: either fetch IRENA API or label "(static, IRENA 2025)" consistently.

### BUG-4: Hardcoded Telegram bot token + chat_id in source AND in context .md files
- Token `8990151330:AAEY...` is committed in neuron.py, CONTEXT files, and has now passed through chat logs.
- **Fix:** rotate the token via @BotFather (it is burned), then env-var only, never a default in code.

---

## P1 — HIGH (correctness / reliability)

1. **Cache stampede:** global `cache = {}` dict, no locks. Two concurrent calls to a cold `/api/almm/modules` → two 280-page PDF parses (2-5 min each). Fix: per-key `threading.Lock` or "fetching" sentinel.
2. **Undated articles score as fresh:** `_parse_pub_dt` fallback returns `days_old=0.0` → recency-weighted scoring promotes undated junk. Fix: fallback `days_old=3.0` (penalty) instead.
3. **MW extraction regex:** `18 GWh` parsed as `18 MW` (known since v6, never fixed). Affects intel entity extraction and action flags.
4. **`/api/iex_power` is not power data** — it returns USD/INR as "proxy". UI labels it as power market. Either label honestly or remove panel.
5. **requirements.txt lists 5 of ~11 deps** (missing pandas, beautifulsoup4, openpyxl, pdfplumber, playwright, urllib3-pin). start.bat installs even fewer. Fresh machine = broken boot.
6. **start.bat runs `pip install` on every launch** — slow, fails offline. Move install to a one-time setup.bat.
7. **Duplicate `id="tab-global"`** (lines ~1625 full panel + ~2057 empty). The 1625 panel ("Global Markets") has no tab button — unreachable dead content (~50 panels of HTML). Content was *moved* to Overview in P9, original never deleted. Remove both.
8. **`switchTab` maps tab names to buttons by array index** — one added/reordered button silently mis-highlights everything. Use `data-tab` attributes.
9. **Race on shared globals** — `SEEN_ALERTS`, `SOURCE_HEALTH`, `_TERM_FREQ` mutated from request threads + daemon thread without locks. Low-probability corruption, but the daily-brief thread and request threads do collide on Telegram cooldown state.

---

## P2 — MEDIUM

- `verify=False` on all gov-site requests + warnings disabled. Accepted tradeoff (gov TLS is broken), but isolate it to a helper `gov_get()` so it's one place, not 15.
- Flask dev server in "production" daily use. Fine locally; if it ever serves beyond localhost, switch to waitress (`pip install waitress`, 2-line change).
- `_exportLoaded` guard: export tab snapshot is from first open; refresh button exists but stale-by-default surprises. Auto-refresh if >10 min old.
- Frontend boot fires ~25 API calls at once → yfinance burst → throttling cascades. Stagger or batch via `/api/dashboard`.
- `fetch_energy_prices` EUA static row has `"static": True` — good pattern; apply it to every static figure in HTML too.
- Dead files: `write_neuron.py`, `make_snapshot.py`, `NEURON_V2_SNAPSHOT.md` (88KB), `neuron_v4.log`, `neuron_v6_boot.log`, `server_err.log`. Archive or delete.
- 3 generations of CONTEXT files across `D:\Neu_ron\` + current — consolidate to ONE living doc.
- graphify graph not updated after recent edits (`graphify update .`).

---

## CONNECT-THE-DOTS MAP (same data, who shows it)

```
India RE total ──► CANONICAL: /api/statewise national.re_total_mw (CEA col 11 = 279.3 GW)
                   consumers: Overview brief · India tab · World tab India panel ·
                              Export §1 · NDC tracker · PDF exportPDF()
Solar/Wind GW  ──► CANONICAL: statewise national (CEA summary sheet)
                   MNRE live = per-tech detail + monthly additions ONLY (never totals)
Tender pipeline ─► CANONICAL: /api/seci_tenders total_mw
                   consumers: Trade&Policy · Intel SECI panel · Overview strip · Export §5
Pulse score ─────► CANONICAL: /api/intel_engine (single compute)
Saatvik price ───► /api/quotes (5-min) — focus_stock uses slower .info, can disagree
                   by minutes with stock card. Display "as of" timestamps.
```
**Rule going forward: a number appears in N places = it is fetched in 1 place.**

---

## PAST MISTAKES — PATTERN ANALYSIS (honest)

1. **Additive development, no deletion.** v3→v9: features added every session, old code rarely removed (dead Global Markets tab, dead routes' functions, 3 snapshot/log files). Codebase = sediment layers.
2. **Fixing symptoms at the display layer.** CEA col10/col11 bug, the "279 GW hardcoded" — patched where seen, not where caused. BUG-1 above is the same class: I patched the World tab by summing an API whose semantics I didn't verify. *Verify data shape before aggregating it.*
3. **Promises in docs that code doesn't keep.** README "reads on every request" vs 6-hr cache. CONTEXT files describe ideal, not actual.
4. **No tests, no verification harness.** Every regression found by Vipul's eyes. A 30-line `smoke_test.py` (hit all routes, assert key invariants like `re_total between 250-400 GW`) would have caught BUG-1 instantly.
5. **Secrets in source** because "it's local". It leaked into 4 markdown files.
6. **Single 162KB neuron.py + 6000-line index.html** — every edit is a needle-in-haystack; cost per change is rising every session.

---

## INTENT · EXPECTATIONS · VISION

- **Intent (unchanged):** free, local, daily-use intelligence monitor for Indian RE — capacity, equities, tenders, policy, schemes — for Vipul's sector work. "No replacement for 10 years."
- **What it actually is today:** an impressive *breadth* machine (60+ routes, 8 tabs) with *trust* problems — when one number is 4× wrong, every number becomes suspect. For an intelligence tool, **trust is the product.**
- **Vision forward:** fewer, harder numbers. v10 should make NEURON *auditable*: every figure traceable to source + timestamp, every static figure labeled, one smoke test that proves the dashboard before Vipul opens it.

---

## PROPOSED ROADMAP

### Phase 10.0 — TRUST (next session, ~1 sitting)
1. Fix BUG-1 (MNRE aggregates: backend tags + frontend uses Total RE row) — both tabs + export.
2. Fix BUG-2 (mtime-based cache for user_data xlsx) — closes Vipul's actual complaint.
3. Rotate + env-var Telegram token.
4. `smoke_test.py`: hits every route, asserts ~10 sanity invariants (totals in range, no empty critical feeds, xlsx national == sum of states). Run at session start, every session.
5. Fix requirements.txt + split start.bat/setup.bat.

### Phase 10.1 — CONSISTENCY
6. Canonical data contract: `/api/canonical` or shared constants; replace every hardcoded GW figure in HTML.
7. Delete dead tab-global panels, dead files; `data-tab` attribute tab switching.
8. Cache locks (stampede) + `days_old` penalty + GWh regex fix.

### Phase 10.2 — MAINTAINABILITY (only after 10.0/10.1)
9. Split neuron.py into modules (fetchers / intel / routes) — mechanical, no behavior change.
10. Extract index.html JS into static/*.js files.
11. One living CONTEXT doc; retire the other three.

### Explicitly NOT now
- New data sources, new tabs, new features — **feature freeze until trust phase done.**
- No framework rewrites. Flask + vanilla JS stays (non-negotiable list respected).

---

## OPTIMIZATION NOTES
- First paint: serve cached `/api/dashboard` snapshot instantly, hydrate live after.
- ALMM: pre-warm cache at boot in background thread instead of first-visitor pays 5 min.
- yfinance: one `yf.Tickers` batch call instead of 14 singles where possible.
- SQLite: enable WAL mode (one PRAGMA) — removes daemon/request write contention.

## VERIFICATION INVARIANTS (for smoke_test.py)
```
250 < re_total_gw < 400          solar < re_total       wind < re_total
mnre "Total RE" row ≈ statewise re_total (±5%)
kusum national == sum(states) per component (±1)
len(quotes) >= 12                pulse 0-100
no route returns 500             every static figure has "static" flag
```
