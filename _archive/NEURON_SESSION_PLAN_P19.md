# NEURON Phase 19 — "The Mind, Made Legible" (frontend↔backend synergy)

## Context
Backend evolved to a reasoning/decision engine (v14–18); the frontend was still a
v1–13 data-display dashboard. The cognition (ranked decisions w/ conviction +
falsifiers, semantic memory recall, beliefs, chokepoints, self-calibration) was
barely surfaced. Ran an LLM council (5 advisors + peer review): unanimous to make
**the decision the unit of the UI**, **evolve not replace** the Celestial Archive,
make **motion encode state**, and — the peer-review blind spot — render
**conviction WITH its uncertainty** (sample size, cold-start, misses shown). Owner
authorized lifting the v13 theme seal. North star: *the interface is where you and
NEURON think together — contestable, honest.*

## 19.1 — The Decision Briefing home — EXECUTED 2026-06-17 ✅ (verified in-browser)
New default tab **◉ Briefing** (`#tab-briefing`), a from-scratch surface consuming
EXISTING endpoints (zero churn lost). Built in `templates/index.html` (new `<style
id="p19-briefing">` scoped under `#tab-briefing` + markup + JS `loadBriefing()` &
helpers; `switchTab`/`init` wired). Sections:
- **Verdict header** — regime + active-call counts + timestamp.
- **Recall omnibox** — `/api/memory/recall` (seed of the command surface).
- **Honest self-calibration strip** — `/api/decisions/scorecard`; shows logged/
  open/resolved and a prominent "⚠ Unproven — N calls haven't reached horizon;
  treat conviction as a hypothesis" cold-start state. The council's non-negotiable.
- **Decision cards** — `/api/decisions`: conviction chip (semantic ramp
  STRONG/HIGH/MOD/LOW, STRONG pulses), action·ticker·horizon, an "unproven/N% hit"
  per-band proof badge, serif thesis headline, **"Wrong if:"** falsifier, faculty
  chips + corroboration, expandable memory-citation evidence.
- **Rails** — attention anomalies (`/api/attention`) + "what changed" (`/api/delta/today`).
Design: evolves the Archive (keeps masthead/gold/dark), legible semantic color,
serif headlines, motion-encodes-state (cards settle by rank; STRONG dot pulses);
`prefers-reduced-motion` fallback. No `impeccable` bans (no side-stripes, gradient
text, glass, over-round). Verified: 10 cards, honest calib, zero console errors.

## Open finding → top of 19.2
- **`/api/decisions` cold-start > 180s** (synchronous cold faculties: yfinance +
  GDELT + intel engine). Home hangs on "Consulting…" on a fresh boot. Fix: kv-cache
  the decision synthesis (~10 min TTL) + pre-warm in the nightly/boot worker so the
  Briefing is instant; show "as of <time>" + a manual refresh.

## Next phases (await owner feedback at each step)
- **19.2 — Perf + craft pass:** decision-cache fix (above); then the design-system
  craft pass — demote the animated cosmos globally to a calm scrim, semantic motion
  on belief-shift/anomaly/self-score, masthead iris reacts to top conviction/misses,
  contrast/typography audit across the app (via `impeccable`/taste).
- **19.3 — Command omnibox (Cmd-K)** routing recall + ask + decisions; tabs become
  the evidence/drill-down layer; decision → cognition-chain unfold.
- **19.4 — Ambient + living map** (gated behind honest calibration): overnight
  "what changed" briefing, chokepoint geography, lead-lag causal graph.

## Constraints
- Additive surfaces; existing endpoints/tabs/churn preserved (tabs become evidence
  layer, not deleted). Backend untouched in 19.1.
- Theme seal deliberately LIFTED with owner authorization (see NEURON_DEV_PROTOCOL).
- Verify each phase in-browser (preview) + keep smoke GREEN.
