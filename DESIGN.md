# DESIGN.md — NEURON visual system ("The Celestial Archive", v13 — SEALED)

> **This theme is final.** v13 layered the Celestial Archive over the v10 system:
> anime × star-atlas engraving × cosmology × psychology × magic circles.
> - **Grand Circle backdrop**: three stacked SVG layers behind everything (zodiac ring
>   300s clockwise, alchemical ring 240s counter, static survey ring + the Fool's star).
>   Rings are whole-`<svg>` HTML layers, never internal `<g>` transforms (compositing).
> - **The Observer**: masthead reads NEUR⊙N; the iris breathes (irisGaze 7s).
> - **Star-atlas plate corners** on every panel (gold L-brackets, brighten on hover);
>   panel titles carry a ✦ seal that turns when the panel wakes.
> - **Anime accents**: loader block-cursor ▮, breaking-banner cut-in notch,
>   active-tab breathing underline, CRT scanlines (pre-existing).
> - **The Maker's Seal** (footer): rotating orbit text "DEVELOPED BY VIPUL JAKHAR ·
>   ABOVE THE GRAY FOG", VJ monogram in Spectral, GitHub/LinkedIn links, italic motto.
> - All ambient motion dies under `prefers-reduced-motion`; light-mode parchment adapts.
> Do not extend this layer. Content changes only.

(v10 base system below — still authoritative for tokens, components, z-scale.)

## Theme
Dark intelligence terminal. Deep indigo night sky, antique gold instrumentation, violet mist. A private observatory for one analyst. Light mode exists as a parchment variant (`body.light-mode`).

## Color (CSS variables, dark default)
- `--bg` #060412 — body / night
- `--bg2` #0d0920 — panel surface
- `--border` #1e1535 — hairlines
- `--base01` #9486b8 — secondary text (raised from #8878a8 for contrast)
- `--base0` #cdbee0 — body text
- `--base1` #f0e8d8 — primary text / numbers (warm parchment)
- `--gold` / `--cyan` #c4922a — THE accent: titles, active states, key data. (Legacy var name `--cyan` is gold; do not repurpose.)
- `--gold2` #f0c878 — gold highlight
- `--violet` #8b5cf6 — mist accent, secondary data viz
- Semantic: `--green` #6a9a3a (up), `--red` #c23535 (down), `--yellow` #e8a030 (hold/warn), `--blue` #4a9eff, `--orange` #d4642a, `--magenta` #9b4d8a
- Category chips use `<color>22` bg + `<color>44` border + color text.

## Typography
- Data, numbers, labels, chrome: `'JetBrains Mono', monospace` (`--font`).
- Prose (news titles, summaries, briefs): `'Inter', system-ui, sans-serif` (`--font-prose`) — mono is identity, sans is readability.
- Brand masthead: serif display (`--font-display`: 'Spectral', Georgia) — the one signature flourish.
- Scale: 9/10/11/12/13/15/18/22/28px fixed (product register: no fluid clamp).
- Uppercase tracked labels: letter-spacing 1–2px, never below 9px font size.

## Components
- `.panel` — surface `--bg2` tint, 1px gold-tinted border, 4px radius. Hover: border brightens. NO backdrop-filter on panels (perf); blur reserved for header/drawer/modal.
- `.metric-card`, `.stock-card`, `.tech-card` — quiet inset cards; gold glow only on hover/selected.
- Chips/badges (`.signal`, `.intel-cat`, `.sig-badge`…) — tint background + 1px border, full radius 2px.
- State accents via background tint + leading dot, never `border-left` stripes.
- Buttons `.btn-sm` — outline gold, fill on hover; `.btn-danger` red.
- Focus: 1px `--gold` border + 0 0 0 3px gold at 18% ring on inputs/buttons.

## Motion
- Micro-interactions 150–250 ms, `cubic-bezier(.22,.61,.36,1)` (ease-out-quart family). No bounce/elastic.
- Tab content: 280 ms rise+fade on activation (animation, not gated transition).
- Bars fill with 800 ms ease-out (no overshoot).
- Ambiance allowed: masthead heartbeat glow, ticker scroll (pauses on hover), live dots.
- `@media (prefers-reduced-motion: reduce)` kills all animation/transition to near-instant.

## Z-index scale
1 content · 200 sticky header · 500 drawer · 600 modal · 899 fs-overlay · 900 fullscreen panel · 1000 toast

## Layout
- `#app` padding 16–20px; grids `grid2/3/4` collapse to 1 col under 768px.
- Newspaper export tab (`#tab-export`) is print-styled (Georgia serif, white) and isolated — never themed dark.

## Hard rules
- No gradient text, no side-stripe accents, no glassmorphism-by-default, no 999/9999 z-index.
- Every loading state is a labeled shimmer/pulse, not bare "Loading…" where avoidable.
- Class names are API: JS queries them — restyle, never rename.
