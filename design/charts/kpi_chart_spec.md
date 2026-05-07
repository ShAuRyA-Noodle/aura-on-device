# Aura KPI Chart — Slide 9 Spec

Build-ready spec for `s9_kpi_chart.svg` (asset 16 in deck_spec.md §3). Read alongside deck_spec.md §6 (KPI Bar Chart Spec for Slide 9) and plan.md §22 (KPI Measurement Protocol).

This chart is a **baseline-versus-Aura paired bar chart** with six KPI groups. It is the closing trust signal of the Phase 1 deck.

---

## 0. Locks recap

| Lock | Value |
|---|---|
| Background | `#FAF8F5` warm off-white |
| Ink | `#0E0E0E` ink black |
| Accent | `#FF5B2E` sunset orange — Aura bars only |
| Body sans | Inter Tight |
| Display serif | Fraunces |
| Mono | JetBrains Mono |
| Canvas | 1700 × 380 px |
| Banned | gradients, glows, drop shadows, glassmorphism, blue tech-gradient, 3D bars, isometric, animated trendlines, light-bulb metaphors |

---

## 1. Geometry

- **Chart canvas**: 1700 × 380 px.
- **Plot area**: 1500 × 280 px, with 100 px left axis area, 80 px right padding, 60 px top padding (for Phase 2 tags + value labels), 40 px bottom (for x-axis labels).
- **Background**: solid `#FAF8F5`. No grid backdrop fill.
- **Horizontal grid**: 4 lines at `#0E0E0E` 10% opacity, 1 px stroke. Lines align to clean tick values per group's Y-axis (see §3).
- **Vertical grid**: none.
- **Axes**:
  - Bottom x-axis: 1 px `#0E0E0E` solid, 100% opacity, full plot-area width.
  - Left y-axis: **omitted as a continuous axis**. Instead, value labels sit directly above each bar in **Inter Tight 12 pt** in `#0E0E0E`. This is intentional — the six KPIs use different units (%, Likert, qualitative), so a single y-axis is dishonest. Each group carries its own implicit scale.

---

## 2. Six paired groups — order locked

Each group renders as a baseline bar (left) and an Aura bar (right). 8 px gap between bars in a pair. 96 px gap between pairs. Bars 36 px wide. Total horizontal footprint of six groups = 6 × (36 + 8 + 36) + 5 × 96 = 6 × 80 + 480 = 960 px, fits comfortably inside the 1500 px plot area with 270 px left and right margin reserved for axis label area + legend.

| # | Group label (x-axis) | Y-axis units (per group) | Target | Phase 1 state |
|---|---|---|---|---|
| 1 | Effort reduction (↓) | % time saved over baseline | ≥ 30% | dashed [Phase 2] |
| 2 | Task completion | % tasks completed | ≥ 90% | dashed [Phase 2] |
| 3 | AI autonomy quality | % rated correct (3-rater Likert + binary) | ≥ 85% | dashed [Phase 2] |
| 4 | Satisfaction | Likert 1–5 | ≥ 4.5 | dashed [Phase 2] |
| 5 | Stress reduction (↓) | normalised HRV trend (z-score) + qualitative | qualitative + HRV | dashed [Phase 2] |
| 6 | Willingness to pay | % yes at ₹199/mo | ≥ 60% | dashed [Phase 2] |

X-axis labels in Inter Tight 14 pt regular `#0E0E0E`, with target value in JetBrains Mono 10 pt at 60% ink on a second line directly below.

---

## 3. Per-group Y-axis behaviour

Because each group has its own units, each group renders its bar heights against a **per-group implicit scale**:

| Group | Scale | Top of plot area = | Notes |
|---|---|---|---|
| 1 — Effort reduction | linear 0–60% | 60% | Direction: down is good. Render bars with their height = % reduction. Dashed Aura bar tagged ≥30%. |
| 2 — Task completion | linear 0–100% | 100% | Direction: up is good. |
| 3 — Autonomy quality | linear 0–100% | 100% | Direction: up is good. |
| 4 — Satisfaction | linear 1–5 | 5.0 | Direction: up is good. Bar floor = 1.0 (Likert minimum). |
| 5 — Stress reduction | normalised −1.0 to +1.0 z-score | render as absolute value of negative shift | Direction: down (negative shift) is good. Bar height = |Δ HRV z-score|. |
| 6 — WTP | linear 0–100% | 100% | Direction: up is good. |

Each group has its own implicit ceiling and floor. Group label includes the unit hint (% / Likert / z) to keep the reader honest.

---

## 4. Bar fill rule (colour-by-condition)

Render rule, applied per bar:

```
if (data_state == "measured" and condition == "baseline"):
    fill = #0E0E0E at 30% opacity
    stroke = none
elif (data_state == "measured" and condition == "aura"):
    fill = #FF5B2E (solid, 100% opacity)
    stroke = none
elif (data_state == "phase2" and condition == "baseline"):
    fill = none
    stroke = 1.5 px #0E0E0E dashed (4-2 dash array)
elif (data_state == "phase2" and condition == "aura"):
    fill = none
    stroke = 1.5 px #FF5B2E dashed (4-2 dash array)
```

A small "[Phase 2]" tag in **JetBrains Mono 10 pt** sits 8 px above each dashed pair, single tag per pair (centred between the two bars in the pair).

**Sunset orange appears only on the Aura bars.** Baseline bars are always ink black. This is the load-bearing accent rule — the colour itself signals "the answer".

---

## 5. Error bars — measured bars only

Render only on **solid (measured)** bars. Phase 2 dashed bars get **no** error bars (drawing CIs on data we don't have is a credibility violation).

Style:
- Vertical line: 1 px `#0E0E0E` for baseline measured, 1 px `#FF5B2E` for Aura measured.
- Cap (I-bar): 12 px wide horizontal segment, same stroke as vertical, both top and bottom.
- Span: full 95% confidence interval computed via `scipy.stats.t.interval(0.95, n-1, loc=mean, scale=sem)` where `sem = sample_std / sqrt(n)`.
- Anchor: vertically centred on the bar's mean (i.e. on the bar top for "up is good" groups, on the bar height for "down is good" groups).

---

## 6. Value labels above each bar

Above each bar, in **Inter Tight 12 pt regular** `#0E0E0E`, render the bar value. Format:

| Group | Format | Example |
|---|---|---|
| 1 — Effort reduction | "−XX%" | "−32%" (Aura), "0%" (baseline reference) |
| 2 — Task completion | "XX%" | "94%" |
| 3 — Autonomy quality | "XX%" | "87%" |
| 4 — Satisfaction | "X.X / 5" | "4.6 / 5" |
| 5 — Stress reduction | "−X.XX z" | "−0.42 z" |
| 6 — WTP | "XX%" | "63%" |

For Phase 2 dashed bars, use the **target value** as a placeholder, prefixed with "≥" — e.g. "≥30%", "≥4.5". The Phase 2 tag above the pair makes the placeholder honest.

---

## 7. Legend

Top-right of the chart canvas, inline, **Inter Tight 14 pt** regular `#0E0E0E`, three glyphs separated by middle-dot:

```
▮ Baseline · ▮ Aura (measured) · ▢ [Phase 2] not yet collected
```

Glyph rules — each glyph is a 14 × 14 px vector swatch matching the bar style:
- Baseline measured: solid filled square in `#0E0E0E` at 30% opacity.
- Aura measured: solid filled square in `#FF5B2E` at 100% opacity.
- Phase 2: empty square with 1.5 px `#0E0E0E` dashed stroke (4-2 dash).

Never use Unicode block characters or emoji for the legend — they vary across renderers. The glyphs are SVG.

---

## 8. Phase 1 reality

At Phase 1 freeze (assumed 2026-06-01), all six pairs render dashed. The chart is honest about this. The slide 9 speaker notes call it out verbatim: "Solid bars are measured. Dashed bars tagged Phase 2 are not yet collected — we are not painting performance we have not earned."

If a baseline measurement exists for any task before deck freeze (W2 dry-run with a single user is feasible — see plan.md §24 W2), promote that bar to solid measured. Single-bar promotion is fine; the chart re-renders any pair where `data_state == "measured"` for at least the baseline.

---

## 9. Animation (deck context)

On slide load:
1. Bars grow up from x-axis over **600 ms ease-out**.
2. **Measured (solid) bars draw first**, with a 200 ms pause before dashed bars draw.
3. **Error bars draw last**, with a 200 ms pause after measured bars settle.
4. The QR code on slide 9 fades in at 0.8 s.

Single-pass entrance only — no looping motion, no pulsing, no hover states (this is a static slide artefact). No 3D rotation. No camera moves.

---

## 10. File and export

- Source: `deck/phase1_blueprint/source_assets/s9_kpi_chart.fig` (Figma component) or `deck/phase1_blueprint/source_assets/s9_kpi_chart.py` (matplotlib + a small custom theme — preferred for reproducibility because the CSV → bar mapping is deterministic).
- Export: `s9_kpi_chart.svg` at 1× and `s9_kpi_chart@2x.png` at 3400 × 760 px, transparent background. Save to `aura/design/charts/`.
- Re-export rule: any time the underlying CSV in `pilot/analysis/` updates, re-run the export. Source CSV path: `pilot/analysis/kpi_results_v{N}.csv`.

---

## 11. Anti-cliché checklist before commit

- [ ] Sunset orange appears **only** on Aura bars (and their error-bar caps), and on the legend's Aura swatch. Nowhere else in the chart.
- [ ] No 3D bars, no shadows, no gradient fills, no glow.
- [ ] Each group has its own per-pair implicit Y-axis. No single shared Y-axis pretending all six KPIs share units.
- [ ] Dashed Phase 2 bars carry the "[Phase 2]" tag. No Phase 2 bar masquerades as measured.
- [ ] Error bars on measured bars only. None on Phase 2 bars.
- [ ] The four banned visuals — gradients, glows, drop shadows, glassmorphism — are absent.

If all pass, commit. Otherwise, revise.
