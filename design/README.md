# Aura — Design Asset System

The visual system for **Aura** (Galaxy Brain — Samsung EnnovateX 2026 Phase 1 Blueprint). This README explains how the asset folders fit together, lists every file in this design tree, names the image-generation tool of choice, and pins resolution targets per artefact class.

Read alongside:
- `/Users/shauryapunj/Desktop/Samsung Hack/plan.md` — master build plan, §5 design principles, §10 architecture, §22 KPIs.
- `/Users/shauryapunj/Desktop/Samsung Hack/deck_spec.md` — Phase 1 blueprint deck spec, §0 lock block, §3 asset checklist, §4 architecture, §6 KPI chart, §7 anti-cliché audit, §9 exhibit pack.

---

## 1. The visual system in one paragraph

Aura's visual system is editorial, anti-corporate, and rigorously single-accent. Every artefact ships on a warm off-white background `#FAF8F5` with ink-black `#0E0E0E` type and exactly one warm accent — sunset orange `#FF5B2E` — used only on load-bearing elements (the answer, the wedge, the trace, the Aura row in the comparison table, the orchestrator's left edge in the architecture diagram). Type is a strict three-tier hierarchy: **Fraunces** (display serif, free) for hero numerals, tier titles, and section headings; **Inter Tight** (body sans, free) for descriptive copy and component names; **JetBrains Mono** for code, JSON, API names, hashes, and timestamps. Reference languages: Linear, Arc, Nothing OS, Teenage Engineering, Things 3, Apple HIG, Stripe docs. Indian context surfaces only as named real artefacts — UPI, IRCTC, BMTC, Namma Metro, Zomato, Swiggy, Blinkit, HDFC, Gmail receipts. The system explicitly rejects: gradients, glows, drop shadows, glassmorphism, neon, blue tech-gradient aesthetics, isometric phones in space, glowing brain or neuron motifs, generic robot or chatbot illustrations, light-bulb metaphors, stock photos, real Apple or Galaxy device chrome, manufacturer logos, university crests, flag motifs, festival imagery, Hinglish.

---

## 2. Folder map

```
aura/design/
├── README.md                                  ← you are here
├── anti_cliche_audit.md                       ← 11 slides × 6 checks ledger
├── architecture/
│   ├── aura_architecture.mmd                  ← Mermaid 3-layer source of truth
│   └── aura_architecture_styling.md           ← Figma re-style instructions
├── brand/
│   └── brandkit_prompt.md                     ← editorial brand-board image prompt
├── charts/
│   └── kpi_chart_spec.md                      ← slide 9 baseline-vs-Aura paired bars
├── leave_behind/
│   └── a4_layout.md                           ← printable A4 leave-behind layout
└── screens/
    ├── 01_morning_brief.md                    ← Brief card surface
    ├── 02_reasoning_trace_drawer.md           ← signature glass-box JSON drawer
    ├── 03_memory_tab.md                       ← exportable memory graph view
    ├── 04_spend_mirror.md                     ← UPI SMS → reality check
    ├── 05_quiet_group_chat.md                 ← 137 → 3 actionable batch
    └── 06_load_score_panel.md                 ← Load Score 78/100 + intervention
```

Total Markdown spec files in this tree: **12** (this README + 11 specs / prompts / layouts / audits).

---

## 3. Every asset file in this design tree

The Markdown specs above are the source of truth. The eventual rendered binaries — PNG mockups, SVG diagrams, the printable PDF — live next to their specs once produced.

### 3.1 Image-prompt specs (paste into image-gen tool)
- `brand/brandkit_prompt.md` — full editorial brand-board, 3840×2160.
- `screens/01_morning_brief.md` — Brief card mobile mockup, 1920×1080.
- `screens/02_reasoning_trace_drawer.md` — Reasoning Trace JSON drawer, 1920×1080. Signature visual.
- `screens/03_memory_tab.md` — Memory tab with Export / Delete-by-time-range / Audit log + Merkle hash badge, 1920×1080.
- `screens/04_spend_mirror.md` — Spend Mirror with UPI HDFC ₹450 to Zomato + weekly ₹2,400 over budget + "Cook tomorrow?" suggestion, 1920×1080.
- `screens/05_quiet_group_chat.md` — Quiet Group Chat with 137 messages, 3 actionable, 134 muted, Silence Budget 2/3, 1920×1080.
- `screens/06_load_score_panel.md` — Load Score 78/100 with HRV + typing entropy drivers and "Mute project group 30 min" intervention, 1920×1080.

### 3.2 Diagram and chart specs
- `architecture/aura_architecture.mmd` — Mermaid 3-layer (Sense → Intelligence → Experience) with 4 agents, orchestrator, memory graph, Reasoning Trace.
- `architecture/aura_architecture_styling.md` — Figma re-style instructions: orthogonal arrows, square corners, sunset-orange edge on orchestrator, Fraunces tier titles, Inter Tight component names, JetBrains Mono API names.
- `charts/kpi_chart_spec.md` — slide 9 baseline-vs-Aura bar chart: 6 paired groups, per-group Y-axes, solid vs dashed, 95% CI error bars on measured bars only, sunset-orange Aura bars only.

### 3.3 Print and audit
- `leave_behind/a4_layout.md` — A4 landscape printable leave-behind, 297×210 mm, 300 dpi, 60 copies for Phase 3 finals.
- `anti_cliche_audit.md` — yes/no audit checklist, one row per slide, six checks per slide, drawn from deck_spec.md §7.

### 3.4 Binaries (produced from the specs above)

These do not exist yet at Phase 1 freeze. Each will land alongside its spec when generated, with the filename convention from deck_spec.md §2 (`s{slide_no}_{element}.{svg,png}`). Expected binaries:

| File | Source spec | Used on |
|---|---|---|
| `brand/aura_brandkit_master.png` | `brand/brandkit_prompt.md` | cover, internal review |
| `screens/01_morning_brief.png` | `screens/01_morning_brief.md` | slide 3 |
| `screens/02_reasoning_trace_drawer.png` | `screens/02_reasoning_trace_drawer.md` | slide 8a, demo video |
| `screens/03_memory_tab.png` | `screens/03_memory_tab.md` | slide 9 footer / demo video |
| `screens/04_spend_mirror.png` | `screens/04_spend_mirror.md` | demo video |
| `screens/05_quiet_group_chat.png` | `screens/05_quiet_group_chat.md` | demo video |
| `screens/06_load_score_panel.png` | `screens/06_load_score_panel.md` | demo video |
| `architecture/s4_architecture.svg` | `architecture/aura_architecture.mmd` + `aura_architecture_styling.md` | slide 4, leave-behind |
| `architecture/s4_architecture@2x.png` | same | slide 4 fallback |
| `charts/s9_kpi_chart.svg` | `charts/kpi_chart_spec.md` | slide 9 |
| `charts/s9_kpi_chart@2x.png` | same | slide 9 fallback |
| `leave_behind/aura_leavebehind_v1.pdf` | `leave_behind/a4_layout.md` | Phase 3 print run |

---

## 4. Image-generation tool of choice

**Primary: Nano Banana** (free, fast iteration, accepts long structured prompts paste-and-run).

**Fallback: ChatGPT image generation** (DALL-E 3 successor inside ChatGPT Plus). Use when Nano Banana hits a content filter or the iteration loop stalls. ChatGPT image gen handles long structured prompts and respects negative-prompt blocks slightly differently — the prompt may need a one-pass clean-up of repeated negatives.

**Tertiary fallback: Midjourney v7** (paid). Use only if both above fail on a specific composition. Midjourney is stronger on cinematic editorial composition but weaker on respecting strict text content inside mockups, so reserve it for the brand-kit master image — never for the per-screen mockups where the JSON, captions, and labels must render verbatim.

Operator notes per asset live inside each individual prompt file. Common notes: render twice and pick the cleaner pass; if the model adds glow / drop shadow / gradient, regenerate with the explicit reminder block; if a different orange appears, paste the hex `#FF5B2E` again at the top of the negative-prompt block; if real device chrome appears, regenerate with "phones must be neutral line-art frames, no Apple, no Samsung, no Galaxy, no Pixel — generic abstract phone outlines only."

---

## 5. Resolution targets

Pinned by artefact class. Every binary in §3.4 must hit its target on first export — no upscaling.

| Artefact class | Target resolution | Aspect | Density | Notes |
|---|---|---|---|---|
| Deck slides (final PPT/PDF render) | **1920 × 1080 px** | 16:9 | 1× | Project at 16:9 native; rendered from Figma source at this size. |
| Brand-kit master image | **3840 × 2160 px** | 16:9 | 4K (effectively 2× of slide canvas) | Hero board for cover use and internal review; deck slides crop or scale from this if needed. |
| Per-screen mobile mockups (screens 01–06) | **1920 × 1080 px** | 16:9 | 1× canvas, phone rendered at ~720 px tall inside | Single phone frame centred on warm off-white. Do NOT render the phone screen at native iPhone resolution — render the composition at slide canvas size with the phone occupying ~60% of vertical space. |
| Architecture diagram (slide 4 hero) | **3400 × 1440 px PNG @ 2×** + **SVG vector master** | ~2.4:1 | 2× | Lives in cols 1–9 of slide 4; scales cleanly. SVG is the primary deliverable; PNG is fallback for any tool that strips the Figma type system on SVG import. |
| KPI chart (slide 9 hero) | **3400 × 760 px PNG @ 2×** + **SVG vector master** | ~4.5:1 | 2× | Lives in slide 9 top zone, 1700 × 380 px on canvas. SVG primary. |
| Printable leave-behind | **3508 × 2480 px** | A4 landscape (297 × 210 mm) | **300 dpi** | PDF/X-1a:2003 export, CMYK, 3 mm bleed, fonts embedded, crop marks on. |
| Demo video frames | **1920 × 1080 px** | 16:9 | 30 fps | 90-second video; per-screen mockups composited at 1× over the warm off-white background. See deck_spec.md §9.1. |

If a render comes back at the wrong resolution, do not stretch — re-prompt at the correct size. Stretching kills the type system at JetBrains Mono 12 pt, which is the smallest legible mono size in the deck.

---

## 6. Build order

The asset generation order, optimised for the deck_spec.md §3 dependency chain:

1. **`brand/brandkit_prompt.md`** → `aura_brandkit_master.png` (3840 × 2160). Locks the visual system in one image.
2. **`screens/01_morning_brief.md`** → `01_morning_brief.png`. Used directly on slide 3.
3. **`screens/02_reasoning_trace_drawer.md`** → `02_reasoning_trace_drawer.png`. Used on slide 8a + demo video. **Signature visual — render this before any other screen.**
4. **`architecture/aura_architecture.mmd`** → Mermaid Live → SVG → Figma re-style per `aura_architecture_styling.md` → `s4_architecture.svg`. Used on slide 4 + leave-behind.
5. **`charts/kpi_chart_spec.md`** → `s9_kpi_chart.svg`. Used on slide 9.
6. **Screens 03, 04, 05, 06** → demo video assets. Render in any order after the signature visual lands.
7. **`leave_behind/a4_layout.md`** → `aura_leavebehind_v1.pdf`. Designed at Phase 1, printed at Phase 3 only.
8. **`anti_cliche_audit.md`** → run before each `aura_phase1_blueprint_v{N}.{pdf,pptx}` freeze.

---

## 7. Do-no-harm checklist for every render

Before committing any binary to this tree, run:

- [ ] Background is `#FAF8F5`. Sample with the colour picker.
- [ ] Ink is `#0E0E0E`. Sample with the colour picker.
- [ ] Sunset orange is `#FF5B2E`. Sample with the colour picker. If the render shows a different orange, regenerate.
- [ ] Sunset orange appears on **load-bearing elements only**. Count the orange elements per asset (per its spec); if the count exceeds the spec's allowance, regenerate or composite-mask in Figma.
- [ ] Zero gradients, zero glows, zero drop shadows, zero glassmorphism in the render.
- [ ] Phone frames are neutral line-art only. No Apple, no Galaxy, no Pixel chrome. No manufacturer logo. No lock-screen wallpaper.
- [ ] Strict English in every visible label. No Hinglish. No festival cliché. No flag.
- [ ] Type system is Fraunces + Inter Tight + JetBrains Mono. No off-system fonts.
- [ ] Banned-word scan passes on every visible string.

If any check fails, the render is rejected. Re-prompt with the specific failure cited inline at the top of the prompt's negative-prompt block.

---

End of README.
