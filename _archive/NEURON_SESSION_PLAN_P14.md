# NEURON Phase 14 — "Living Memory" session plan

Source: Vipul's 5-day usage feedback (2026-06-16) after v13 theme seal. Audited
against current code before writing this plan — see file:line refs below.
Execute top-down, same pattern as P10/P11/P12. **Do not touch theme/motion/
visuals** — v13 is sealed (DESIGN.md). This phase is data + intelligence only.

## PRAISED — DO NOT REGRESS (permanent constraint, also in memory)
- World tab layout/content: "good" — leave UI as-is, only fix data freshness underneath (#7).
- RE Components tab structure (BESS+GH section, tender/news tracking): "perfect" —
  leave the panel as-is; #8 only adds a backing knowledge store, no UI rewrite.
- v13 Celestial Archive theme: sealed, untouched, not in scope.

## Item 1 — Global RE ETFs (TAN etc.) silently dropping
Root cause confirmed: `fetch_quote_generic()` (neuron.py:628-637) has a bare
`except: return None`, no retry/period-fallback (unlike `fetch_quote()` which
retries 5d→1mo, neuron.py:552-560), and `fetch_global_re()` (neuron.py:651-661)
fires 10 parallel threads with no backoff — Yahoo throttles thin tickers (TAN,
CSIQ, RNW) under that load. Failures are invisible: aggregate-only health flag
(line 660), UI just filters out missing keys (index.html:1803).
**Fix:** give `fetch_quote_generic` the same retry/backoff shape as
`fetch_quote` (period fallback + 1 retry with delay); drop `fetch_global_re`
parallelism to match the throttled sequential pattern in `fetch_all_quotes()`
(neuron.py:597-626); add per-symbol health tracking so a dropped ticker is
visible in `/api/sources/stats` instead of silently vanishing.

## Item 2 — Global installation capacity (RE + solar) stale/missing; add GEM + IEA as sources
`/api/global_re` (neuron.py:2262-2263) is a stock-ticker fetcher only — there
is no installed-capacity dataset feeding it. globalenergymonitor.org and
iea.org are not integrated anywhere (only as link hrefs).
**Fix:**
- New `fetch_global_installed_capacity()`: scrape per-country installed
  RE/solar MW from Global Energy Monitor's public trackers (GEM Wiki tables /
  CSV downloads — solar, wind trackers are public, no key needed) and IEA's
  public renewables statistics pages, both English-only. Cache with a long
  TTL (these update monthly/quarterly, not real-time) keyed by
  source-file mtime/ETag where possible so it never looks falsely "fresh."
  Add `globalenergymonitor.org` and `iea.org` (data pages, not link-only) to
  `sources.py` registry as new `api`/`scrape` type entries.
- New route `/api/global_capacity` surfacing country-level totals; World tab
  consumes this for an "Installed Capacity by Country" panel — additive, not
  replacing existing World tab content (per the "World tab is good" praise).
- If a country page fails to parse, fall back to last good cached value and
  flag staleness in the payload (`as_of` date) rather than going empty —
  same trust principle as MNRE/CEA work in v10.

## Item 3 — Solar Leaders panel: remove; surface KUSUM/Surya Ghar in India tab
Confirmed: PM-KUSUM and PM Surya Ghar already render as **live** panels in the
India tab (`kusum-live` index.html:2493/2511, surya panel index.html:2467),
not export-only as originally guessed — so the "why not using that data" part
is already satisfied. The actual ask is panel real estate: drop "Solar
Leaders" (index.html:531-533, stock-price/signal rows — duplicates Overview
tab stock content, adds no India-RE-specific insight) and give that grid slot
to making KUSUM/Surya Ghar more prominent (e.g. state-rank table — top sanctioned/
installed states — instead of just national figures), since they're the
better-aligned content per Vipul's read of the tab's purpose.
**Fix:** delete `#solar-leaders` panel + its JS render block; add a
state-ranking view to the existing KUSUM/Surya Ghar panels using `state_data`
already returned by `/api/pm_kusum` / `/api/pm_surya_ghar`.

## Item 4 — Remove NDC tracker (duplicate of MNRE panel)
Confirmed: NDC panel (index.html:568-589) is the only place with target-vs-
achieved progress-bar framing; MNRE Live Capacity panel (489-492) shows raw
totals only — they're not literally duplicate data, but Vipul considers the
NDC framing redundant once MNRE totals are visible. Respect his call.
**Fix:** delete `#ndc-tracker`-equivalent block and its JS
(`index.html:3463-3466` region) entirely. Optionally fold the single
"target %" stat into the MNRE panel header as a one-line stat if it's cheap —
ask before adding scope back; default to clean removal only.

## Item 5 — Solar Capacity History & Projection is empty/static
Root cause: `drawSolarCharts()` (index.html:2283-2296) draws from **hardcoded
JS arrays** (`yrs/cap/py/pc`, lines 2284-2290) — there is no backing API at
all, so it can never be "live," and apparently renders as empty/stale because
the static years are now out of range of what Vipul expects to see.
**Fix:** new route `/api/solar_capacity_history` built from MNRE historical
cumulative-capacity figures (already-fetched data, just need a time series
persisted — see Item 8's storage layer) + simple linear/CAGR projection
forward 3-5 years (no ML dependency, consistent with project's existing style
e.g. `re_forecast`). Replace the hardcoded arrays with a real fetch.

## Item 6 — Technology Mix: bucket by actual technology, not fuel type
Confirmed: India RE "Technology Mix" panel (index.html:725-730, JS at
2079-2096) buckets by fuel (Solar/Wind/Bio/Hydro) — not technology as Vipul
means it (mono-PERC, TOPCon, HJT for solar; DFIG, PMSG, turbine class for
wind). A real module-tech chart already exists for ALMM
(`almm-tech-mix-chart`, `/api/almm/tech_mix`, neuron.py:3032,
`fetch_almm_modules`) — confirmed correct and should be left alone. **No AL
Wind equivalent exists** (grep confirmed) — wind technology mix is a real gap.
**Fix:**
- Rename/clarify the fuel-bucket panel (it's legitimate, just mislabeled —
  call it "Generation Mix by Source" instead of "Technology Mix" to remove
  the naming collision Vipul flagged).
- Find and parse India's equivalent wind-technology list (MNRE/IWTMA
  publishes an approved wind turbine model list analogous to ALMM — research
  exact public source during implementation) → `fetch_wind_technology_list()`
  mirroring `fetch_almm_modules()`'s shape; new `/api/wind_tech_mix` feeding a
  new chart next to the existing ALMM module-tech chart. If no clean public
  list exists, document the gap honestly rather than fabricating data.

## Item 7 — World tab data looks static day-to-day
Confirmed NOT a long-TTL caching bug — `CACHE_TTL=300` (5 min) is the global
default (neuron.py:94) and nothing world-tab-specific overrides it longer.
The actual cause: the "IEA 2024" investment chart (index.html:2772-2773) is
**hardcoded static JS**, not fetched — it literally cannot change day to day.
**Fix:** either feed that one chart from a real (slow-moving, that's fine —
investment-flow data is genuinely annual) source with an `as_of` stamp shown
in the UI so it's honestly labeled "static, updated annually" rather than
silently identical — OR if no live source is practical, add a visible
"Source: IEA WEI 2024, annual" caption so it doesn't read as a freshness bug.
Confirm with Vipul which (small effort either way) — default to the caption
fix since it's the more honest minimal change matching project philosophy.

## Item 8 — "Living memory" knowledge base (the big one)
Confirmed: no tender-lifecycle tracking exists. `v11_articles` is a 30-day
rolling store; `v12_signal_ledger` only tracks macro lead-lag signal
resolution, not tenders/projects. Nothing currently lets the system improve
its own analysis from accumulated history beyond the 48h story-clustering
window.
**Design (lightweight, SQLite — no new infra, matches project philosophy):**
- New table `v14_entity_ledger`: one row per tracked real-world entity
  (a tender, a project, a policy notification) — `entity_id, entity_type
  (tender|project|policy), title, first_seen, last_seen, status
  (announced|bid_open|awarded|commissioned|stalled), status_history (JSON
  list of {status, ts, source_article_id}), state, capacity_mw, key_players
  (JSON list)`.
- Extraction: when articles are ingested (existing `sources.py` pipeline),
  run lightweight keyword/regex classification (reuse existing
  awarded/commissioned keyword lists, neuron.py:227-228) to detect a
  status-change mention referencing a known entity (fuzzy-match on
  title/capacity/state) or open a new entity row. This is NOT a new ML
  model — pure extension of existing keyword classification, now persisted
  instead of discarded after 30 days.
- Compaction: full article text is never duplicated into the ledger — only
  the structured fact (status, date, capacity, players) is kept indefinitely;
  raw articles still age out at 30 days as today. This keeps storage small
  (the "not much space" requirement) while keeping the durable signal.
- Consumption: `/api/pipeline/<state_or_company>` surfaces an entity's full
  lifecycle timeline; Synthesis Desk and Standing Questions
  (intelligence.py) get a new context source — "known pipeline" facts — so
  LLM/heuristic answers can cite real status history instead of only the
  last 48h of news. This is the literal mechanism for "Neuron learns from
  what it collects" without claiming any actual ML/training — it's durable
  structured memory the existing intelligence layer can query.
- Add `v14_entity_ledger` row counts + a couple of invariants
  (no orphan status jumps e.g. commissioned before awarded) to
  `smoke_test.py`.

## Item 9 — ICED / IEA panels are link-only; show real data inline
Confirmed both ICED (index.html:1150-1180) and World-tab IEA links
(828, 897) are external-link-only, no inline data.
**Fix:** ICED (niti.gov.in) has no public API — confirm during
implementation whether their dashboard exposes a scrapeable JSON endpoint
behind the UI (check network tab); if yes, pull the handful of headline
stats (solar potential, RPO compliance %, climate finance) inline with an
"ICED, NITI Aayog" attribution and keep the link as "View full dashboard."
If genuinely no scrapeable endpoint exists, say so plainly to Vipul rather
than building a fragile scraper against a page with no stable contract —
this is the kind of thing to flag back rather than force.

## Execution order (top-down, same as prior phases)
1. Item 1 (ETF fetch resilience) — quick, isolated, low risk.
2. Item 8 (entity ledger schema + ingestion hook) — foundational; Items 2/5/6
   want a durable store too, build it once.
3. Item 2 (GEM/IEA installed-capacity sources).
4. Item 5 (solar capacity history, now backed by Item 8's persisted series).
5. Item 6 (rename fuel panel + wind tech mix research/build).
6. Items 3 & 4 (India tab panel removals/additions — fast, mechanical).
7. Item 7 (caption fix or live feed for IEA investment chart).
8. Item 9 (ICED inline data, if a stable endpoint exists).
9. Extend smoke_test.py for every new route/invariant; full GREEN run before
   calling the phase done.

## Hard constraints carried over
- No new paid APIs / keys beyond what's already in `.env`.
- English-language sources only (explicit Vipul instruction for item 2).
- Never touch v13 theme/CSS/motion.
- Class names in index.html are API — restyle never, but item 3/4 explicitly
  permit *removing* whole panels (not just restyling).
