# Aura — Phase 1 Blueprint Deck

Samsung EnnovateX 2026, Phase 1 submission.
Team: Galaxy Brain (Shaurya Punj, Shorya Gupta — Thapar Institute of Engineering and Technology).
Tagline: Anticipate. Act. Stay quiet.
Repo: https://github.com/ShAuRyA-Noodle/Combobulating

---

## What is in this directory

```
deck/phase1_blueprint/
├── README.md                    (this file)
├── deck.md                      (single concatenated deck, 11 slides, --- separators, Keynote/PPT import source)
├── slides/
│   ├── slide_01_team_details.md
│   ├── slide_02_problem_statement.md
│   ├── slide_03_proposed_solution.md
│   ├── slide_04_technical_details.md
│   ├── slide_04a_plausibility_constraints.md
│   ├── slide_05_novelty_innovation.md
│   ├── slide_06_open_datasets.md
│   ├── slide_07_open_models.md
│   ├── slide_08_ai_genai_agentic_tools.md
│   ├── slide_08a_best_practices.md
│   └── slide_09_supporting_materials.md
├── elevator_60s.md              (60-second elevator script per deck_spec.md §8)
├── judges_memo.md               (one sentence per judge persona, mapped to target slide)
├── citation_map.md              (every claim on slides 2–8 → source in plan.md §37.1)
├── anti_cliche_audit.md         (six-check audit per slide)
└── production_checklist.md      (final pre-submission gates per deck_spec.md §10)
```

Per-slide format follows `slide_04a_plausibility_constraints.md` exactly: front-matter (slide N, title), then BODY (≤30 words), SPEAKER NOTES, CITATIONS, VISUAL BRIEF, PERSUASION JOB.

---

## How to import `deck.md` into Keynote

`deck.md` is a single Markdown file with `---` separators between slides. Keynote does not import Markdown natively. Use one of these paths:

1. **Pandoc → PPTX → Keynote (recommended).**
   ```
   pandoc deck.md -o aura_phase1_blueprint_v1.pptx
   open aura_phase1_blueprint_v1.pptx   # opens in Keynote on macOS
   ```
   Keynote opens .pptx in place. Save As → Keynote (.key). Layouts will need styling per the spec; treat the PPTX as a content scaffold, not a finished deck. The actual visual styling lives in Figma per `../../design/`.

2. **Deckset (paid app, $30) — Markdown-native.**
   Open `deck.md` directly. Good for rehearsal projection. Not the submission artefact.

3. **Marp / Slidev (free, web-based) — Markdown-native.**
   Convert `deck.md` to a web-rendered deck for review. Not the submission artefact.

## How to import `deck.md` into PowerPoint

Same as Keynote path 1: `pandoc deck.md -o aura_phase1_blueprint_v1.pptx`. PowerPoint opens it directly. Use it as a content scaffold; final styling per `deck_spec.md` §0–§2 must be applied in Figma → re-export, or in PowerPoint with the locked type scale and colour set.

---

## Where the visuals come from

Final styled artefacts live one level up at `aura/design/`. The 22-item asset list is in `deck_spec.md` §3. Highlights:

- `s4_architecture.svg` — the three-layer Sense → Intelligence → Experience diagram, Mermaid source in `deck_spec.md` §4.2, Figma re-style required (orthogonal arrows, square corners, sunset-orange orchestrator left edge).
- `s5_comparison_table.svg` — the seven-system comparison, glyph system per `deck_spec.md` §5.3.
- `s5_aura_row_motion.json` — Lottie animation for the deck's single signature moment (Aura row glyph colour change).
- `s9_kpi_chart.svg` — six paired bars, baseline vs Aura, 95% CI, dashed Phase-2 outlines.
- `aura_screenshot_set_v1.zip` — six app-screen mockups, generated via Claude `imagegen-frontend-mobile` skill: Morning Brief, Reasoning Trace drawer, Memory tab, Spend Mirror card, Quiet Group Chat card, Load Score panel.

Phone frames must be neutral line-art (Pixel 8 or Galaxy S24 generic frame at 1.5 px ink stroke) — never Apple chrome and never Samsung Galaxy chrome with logos. Per `deck_spec.md` §0–§5 visual lock list.

Visual lock list:
- Background #FAF8F5, ink #0E0E0E, single accent sunset-orange #FF5B2E.
- Display serif Fraunces, body sans Inter Tight, mono JetBrains Mono.
- 16:9 1920×1080, 12 columns, 96 px gutters, 80 px outer margin.
- Banned visuals: stock photos, glowing brains/neurons, gradient blobs, glassmorphism, neon glows, generic robots/chatbots, isometric phones, light-bulb metaphors, blue-gradient tech aesthetic, generic flag/festival/chai imagery.

---

## Variant strategy

`deck_spec.md` §11 specifies three variants for internal A/B critique. Default ship is Variant A (Engineer-led). Variants B and C live archived under `deck/phase1_blueprint/variants/` once produced.

- **Variant A — Engineer-led (default ship).** Slide 4 trades visual width for a benchmark table (median tick latency, on-device memory footprint, battery cost). Slide 9 trades the publishing trust beat for a precision-recall curve on the WellnessAgent intervention selector.
- **Variant B — Design-led (held for Phase 3 finals deck).** Slide 3 promotes the Reasoning Trace drawer to the hero. Slide 8a replaces the code block with an interactive-feel state-machine diagram.
- **Variant C — Story-led.** Slide 2 replaces the 237 number with a six-panel storyboard of Aanya's Tuesday. Slide 5 compresses the comparison table to a single Aura-vs-field row plus a Fraunces 56 pt narrative paragraph.

Recommendation per `deck_spec.md` §11.3: ship Variant A for Phase 1 because the EnnovateX rubric weights "verifiable raw evidence" and "technical proof of concept" highest; hold Variant B for the Phase 3 finals deck.

---

## File naming convention

`aura_phase1_blueprint_v{N}.pptx` and `aura_phase1_blueprint_v{N}.pdf`, both saved here. `{N}` increments on every freeze. Source assets in `../../design/phase1/` named `s{slide_no}_{element}.{ext}`.

## Verification before submission

Run the full `production_checklist.md`. Run the banned-word grep:

```
grep -i "empower\|leverage\|seamless\|revolutionary\|paradigm\|holistic\|robust\|cutting-edge\|transformative" slides/*.md
```

Expected output: empty. Last verified: 2026-05-07.

End of README.
