# NEURON Phase 17 — "Executive Function: The Decider"

## Context
Neuron now senses superbly but each faculty is a **silo**: beliefs (v15),
attention (v15), chokepoints (16.4), lead-lag/novelty (v11), regime/implications/
forecast (v7), MemoryOS recall (v16). A god-tier, *decision-capable* intelligence
needs the missing executive layer (the prefrontal cortex the original arch review
flagged as "rudimentary"): one engine that **fuses** all faculties into ranked,
**conviction-scored, falsifiable DECISIONS**, and a **self-scoring loop** that
tracks its own calls to outcomes so it learns which judgments to trust. That
metacognition is the literal "self decision with self intelligence."

Outcome: `/api/decisions` (ranked actionable judgments with conviction +
rationale chain + falsifier + memory citations) and `/api/decisions/scorecard`
(calibration: "when Neuron says STRONG, how often is it right?").

## Approach — `decisions.py` (NEW, pure reasoning module)
Membrane: imports `cognition`, `intelligence`, `memory`, `sources` (all lower
layers — no cycle) and **never** `neuron`. Neuron passes market-derived context
(regime/implications/forecast/fear_greed/quote-prices) as a dict, since those use
yfinance fetchers that belong to the expression layer.

### Decision generation (heuristic core — always works; LLM optional)
Modular **generators**, each reads one faculty and emits candidate decisions
`{key, thesis, action, ticker?, direction?, horizon_days, base_conviction,
faculty, falsifier, terms}`:
- **implications** (`context["implications"]`): each rule → POSITION on its ticker.
- **chokepoints** (`intelligence.chokepoint_monitor`): ELEVATED/DISRUPTED → HEDGE/WATCH with India-exposure thesis.
- **attention** (`cognition.compute_attention`): status-cluster/actor-burst → WATCH momentum.
- **beliefs** (`cognition.beliefs_view`): conflicts/large revisions → EXPECT structural shift.
- **lead-lag** (`intelligence.early_signals`): NOT-YET-IN-INDIA → ANTICIPATE with the causal chain.

### Fusion → conviction (the "high-IQ" part)
- Group candidates by `key`; fused base = max(base) + corroboration bonus
  `8×(distinct faculties−1)`.
- **Cross-corroboration**: a ticker thesis backed by other faculties referencing
  the same ticker gets `+5` each (cap +15) — independent agreement = conviction.
- **Regime alignment** (`context["regime"]`): direction with the regime bias `+5`,
  against `−8`.
- conviction clamped 0–97 → band LOW/MODERATE/HIGH/STRONG.
- **Memory citations**: `memory.recall(terms, k=3)` attaches durable supporting
  facts to each decision (provenance, not vibes).
- Optional `narrative=True` → `intelligence._nv_chat` writes a sharp executive
  summary over the top decisions (inputs sanitized via `sanitize_for_prompt`);
  default OFF so the route is fast and never LLM-blocked (degrade-never-break).

### Self-scoring / metacognition — `v17_decision_ledger`
- `record_decisions(decisions, prices)`: INSERT OR IGNORE one row per decision
  per day (id = hash(date+key) → idempotent), storing `entry_price` for ticker
  decisions, conviction, band, horizon, falsifier, rationale(json), status OPEN.
- `resolve_decisions(prices)`: for OPEN decisions past horizon — ticker ones
  scored on realized price direction vs entry (CONFIRMED/INVALIDATED/EXPIRED on a
  ±2% band, SHORT inverse); thematic ones EXPIRE (not price-verifiable).
- `decision_scorecard()`: counts by status + **hit-rate by conviction band** =
  Neuron's calibration curve. This is the self-intelligence: it grades itself.

## neuron.py (expression layer)
- `_decision_context()` gathers regime/implications/forecast/fear_greed + a
  `{ticker: price}` map from `fetch_all_quotes()`.
- `GET /api/decisions` → `decisions.synthesize_decisions(context)`;
  `GET /api/decisions/scorecard` → `decisions.decision_scorecard()`.
- Nightly consolidation worker: `record_decisions(...)` + `resolve_decisions(...)`
  so the ledger accrues a real track record over time.
- Mark `/api/decisions` "slow" in smoke (gathers several cached faculties).

## Reused (do not rebuild)
- `cognition.beliefs_view`, `cognition.compute_attention`
- `intelligence.chokepoint_monitor`, `intelligence.early_signals`, `intelligence._nv_chat`, `intelligence.sanitize_for_prompt`
- `memory.recall`
- `neuron.fetch_re_implications/fetch_re_regime/fetch_re_forecast/compute_fear_greed/fetch_all_quotes`
- `sources.kv_get/kv_set`; v12 signal-ledger self-scoring pattern (the model for v17)

## Verification
1. AST on `decisions.py`, `neuron.py`, `smoke_test.py`.
2. Restart ritual → `/api/health`.
3. `GET /api/decisions` — ranked decisions, each with conviction+band, rationale
   chain (multiple faculties), falsifier, memory citations; cross-corroborated
   ones rank highest. `GET /api/decisions/scorecard` — structurally valid.
4. `python smoke_test.py` → GREEN (+ decision invariants).
5. graphify + docs (Guide endpoints/phase row, this plan, memory).

## Out of scope (follow-ons)
- Proactive Telegram push of STRONG decisions (touches alert path).
- UI decision panel (theme sealed).
- LLM narrative on by default (cost/latency — keep opt-in).

## Constraints (NEURON_DEV_PROTOCOL.md)
- Additive; new `v17_decision_ledger` only; never delete. Backend-only.
- Membrane: `decisions.py` imports lower layers, never `neuron`.
- Degrade-never-break (heuristic core; LLM optional). New routes get smoke
  invariants; full GREEN before done.
