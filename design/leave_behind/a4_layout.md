# Aura — Printable A4 Leave-Behind Layout

Build-ready layout spec for `aura_leavebehind_v1.pdf`. Conformed to deck_spec.md §9.2 (Exhibit Pack — One-Page Printable Leave-Behind) and plan.md §26 (₹2,000 budget — print quantity 60 for Phase 3 finals only). At Phase 1 the file is designed but not printed; print run happens at Phase 3 if shortlisted.

---

## 0. Locks recap

| Lock | Value |
|---|---|
| Format | A4 landscape, 297 × 210 mm |
| Bleed | 3 mm full bleed all sides |
| Resolution | 300 dpi (3508 × 2480 px at trim) |
| Sides | Single-sided |
| Stock | 300 gsm warm off-white card preferred; 100 gsm standard fine |
| Background | `#FAF8F5` warm off-white, full bleed |
| Ink | `#0E0E0E` ink black |
| Accent | `#FF5B2E` sunset orange — at most three elements |
| Display serif | Fraunces |
| Body sans | Inter Tight |
| Mono | JetBrains Mono |
| Banned | gradients, glows, drop shadows, glassmorphism, blue tech-gradient, isometric phones, light-bulb metaphors, robot icons, brain motifs, stock photos of people on phones, real device chrome, manufacturer logos, university crests, flag motifs, Hinglish |

---

## 1. Print specifications

- **Paper**: warm off-white card stock (Munken Lynx or similar) at 300 gsm if budget allows; else 100 gsm matte uncoated. Avoid coated / glossy stock — the warm off-white reads cooler when coated.
- **Bleed**: 3 mm on all four sides. Trim line at 297 × 210 mm. Safe area 6 mm inside trim.
- **Colour profile**: convert to CMYK at export. Sunset orange `#FF5B2E` ≈ CMYK 0 / 78 / 87 / 0 — request a colour proof at the printer if budget allows; the orange shifts to muddy under generic offset.
- **Resolution**: 300 dpi at 297 × 210 mm = 3508 × 2480 px raster equivalent. All assets exported at this density.
- **Bind**: none — single sheet, A4 landscape, no fold.

---

## 2. Layout — three zones

The leave-behind is divided into three zones across the A4 landscape canvas. All measurements below are at trim (excluding the 3 mm bleed on each edge).

```
┌──────────────────────────────────────────────────────────────────────┐
│  ZONE 1 — TOP STRIP · width 297 mm × height 60 mm                    │
│  (lockup + tagline + sunset-orange underline)                        │
├───────────────────────────────────────┬──────────────────────────────┤
│                                       │                              │
│  ZONE 2 — LEFT HALF                   │  ZONE 3 — RIGHT HALF         │
│  width 130 mm × height 130 mm         │  width 130 mm × height 130 mm│
│                                       │                              │
│  five hero numbers stacked            │  slide-4 architecture diagram│
│  (Fraunces 88 pt + caption)           │  at 60% scale                │
│                                       │                              │
├───────────────────────────────────────┴──────────────────────────────┤
│  ZONE 4 — BOTTOM STRIP · width 297 mm × height 25 mm                 │
│  (repo URL + QR + team line)                                         │
└──────────────────────────────────────────────────────────────────────┘
```

Page margins: 15 mm outer (left, right, bottom), 12 mm top. Inter-zone gutter: 12 mm vertical between zone 1 and zones 2–3, 14 mm vertical between zones 2–3 and zone 4. Inter-zone gutter horizontal between zone 2 and zone 3: 14 mm.

---

## 3. Zone 1 — top strip (297 × 60 mm)

- Full bleed.
- Background: `#FAF8F5` solid.
- Lockup, left-aligned, starting 15 mm in from the left trim edge:
  - Wordmark "**Aura**" set in **Fraunces Regular 200 pt** in `#0E0E0E`. Vertical baseline 38 mm from top of page.
  - Hand-drawn-feel sunset-orange `#FF5B2E` underline beneath the wordmark — 4 mm thick, runs the width of the wordmark plus 4 mm right overhang. **This is sunset-orange element #1 of three on the leave-behind.**
  - Tagline "**Anticipate. Act. Stay quiet.**" set in **Inter Tight Regular 22 pt** directly under the underline, 6 mm below underline baseline.
- Right side of strip, set right-aligned 15 mm in from the right trim edge:
  - Kicker "EnnovateX 2026 · Phase 1 Blueprint" in **Inter Tight 14 pt tracked +40** at 60% ink. Vertical centre aligned to the wordmark vertical centre.

---

## 4. Zone 2 — left half (130 × 130 mm)

Five hero numbers stacked vertically, each row ~24 mm tall with a 1-mm hairline separator at `#0E0E0E` 20% opacity between rows. Each row is a number-plus-caption pair.

| Row | Number (Fraunces 88 pt) | Caption (Inter Tight 14 pt regular, 60% ink) |
|---|---|---|
| 1 | **237 → 4** | "notifications a day, signal extracted (Common Sense Media 2023)" |
| 2 | **30%** | "effort reduction target across five standardised tasks" |
| 3 | **3** | "proactive surfaces per day, capped, learnable down to zero" |
| 4 | **0** | "bytes leave the device without a user-initiated export" |
| 5 | **₹199** | "willingness-to-pay anchor; ≥ 60% target across n=30 pilot" |

Number alignment: left-aligned. Caption alignment: left-aligned, hard left edge of caption = hard left edge of number. Caption sits 4 mm below the number's baseline. Use Fraunces lining figures, not oldstyle, so the numerals align flush.

The `→` glyph in row 1 is set in Inter Tight at the same vertical centre as the surrounding digits, with 6 mm of tracking on each side — a deliberate typographic break to signal the reduction.

The `₹` glyph in row 5 is the real Unicode character (U+20B9), rendered in Fraunces. If Fraunces does not carry the rupee glyph at this weight, fall back to Inter Tight Regular at the same optical size — never a synthesised glyph.

No icons in this zone. No charts. No imagery. Type only.

---

## 5. Zone 3 — right half (130 × 130 mm)

The slide-4 architecture diagram at **60% scale** — i.e. the 1700 × 720 px Figma frame downscaled to 130 × ~55 mm at trim. The diagram fills the full width of the zone with vertical centring.

Visual treatment is identical to the slide-4 export per `aura/design/architecture/aura_architecture_styling.md`:
- Three lanes, equal width, divided by 1-px ink hairlines.
- Lane kickers in Inter Tight 14 pt tracked +40 in `#FF5B2E` sunset orange. **These are sunset-orange elements #2 of three** (counted as a single element regardless of how many kickers — "lane kicker treatment" is one design decision).
- Orchestrator left edge in 4 px sunset orange. **This is sunset-orange element #3 of three.**
- All other strokes ink black.

If the diagram at 60% scale becomes illegible in print, the fallback is to trim the lanes to **only the four agent boxes + orchestrator + one phone surface** (a "core" view) — and add a note "full architecture in deck slide 4 · github.com/ShAuRyA-Noodle/Combobulating".

Below the diagram, in the bottom 8 mm of zone 3, set a single line in **JetBrains Mono 11 pt** at 60% ink: `Sense → Intelligence → Experience · 4 agents · 1 orchestrator · 1 trace`.

---

## 6. Zone 4 — bottom strip (297 × 25 mm)

Three elements, in a single row:

- **Left** (15 mm in from left trim, vertical centre of strip): team line, "Shaurya Punj · Shorya Gupta · Thapar IET" in **Inter Tight 14 pt** at 100% ink. No university crest, no logo.
- **Centre-right** (~80 mm in from right trim): repo URL "github.com/ShAuRyA-Noodle/Combobulating" in **JetBrains Mono 22 pt** at 100% ink. Vertical centre of strip.
- **Right** (15 mm in from right trim, top-aligned to strip top): QR code, **60 × 60 mm**, ink-on-warm. Renders the URL above. No coloured QR module, no stylised QR with a logo in the centre — a clean black-on-`#FAF8F5` matrix, error correction level M.

A single 0.5-mm hairline at `#0E0E0E` 20% opacity runs the full page width 4 mm above the strip — the only horizontal divider on the page outside zone 2's row separators.

---

## 7. Sunset-orange budget — strict three

The leave-behind allows exactly three sunset-orange elements. No more.

1. The hand-drawn underline beneath "Aura" in zone 1.
2. The lane-kicker treatment in zone 3 (`SENSE`, `INTELLIGENCE`, `EXPERIENCE` set in `#FF5B2E`).
3. The orchestrator left-edge accent inside zone 3.

If the printed proof shows the orange muddy or shifted, re-spec the print run with a Pantone match request — Pantone 165 C is the closest off-the-shelf match to `#FF5B2E`. Do not compensate by adding more orange elsewhere.

---

## 8. Type system — strict three-tier hierarchy

Identical to the deck:

| Element | Font | Size | Weight | Colour |
|---|---|---|---|---|
| Wordmark | Fraunces | 200 pt | Regular | `#0E0E0E` |
| Tagline | Inter Tight | 22 pt | Regular | `#0E0E0E` |
| Hero numbers | Fraunces | 88 pt | Regular | `#0E0E0E` |
| Captions | Inter Tight | 14 pt | Regular | `#0E0E0E` 60% |
| Diagram tier titles | Fraunces | 12 pt at 60% scale | Regular | `#0E0E0E` |
| Diagram component names | Inter Tight | 9 pt at 60% scale | Regular | `#0E0E0E` 60% |
| Diagram API names + repo URL | JetBrains Mono | 11–22 pt | Regular | `#0E0E0E` |

Lining figures throughout. No swashes on Fraunces (the WONK and SOFT axes stay at default neutral). No tracking changes outside the kickers.

---

## 9. Body copy — banned-word scan

The only running prose on the leave-behind is the five row captions in zone 2 and the diagram's component names. Run the deck-level banned-word list against them before commit:

- empower, leverage, seamless, revolutionary, game-changing, paradigm, unleash, harness, synergy, holistic, robust, cutting-edge, AI-powered, transformative

If any caption fails, rewrite. Keep captions ≤ 16 words each. The five row captions above are the canonical drafts — they pass.

---

## 10. File and export

- Source: `deck/phase1_blueprint/source_assets/aura_leavebehind_v1.fig` (Figma) or `aura_leavebehind_v1.afdesign` (Affinity).
- Export: **`aura_leavebehind_v1.pdf`** at PDF/X-1a:2003, CMYK, fonts embedded, 300 dpi, 3 mm bleed, crop marks on. Save to `aura/design/leave_behind/`.
- Also export a screen-resolution **`aura_leavebehind_v1@web.png`** at 1754 × 1240 px, RGB, transparent background optional — for the GitHub README and for slide 9 of the deck if a thumbnail is needed.
- Re-export rule: re-render any time the slide-4 architecture diagram updates. The leave-behind reads the same architecture image so the two stay in sync.

---

## 11. Print cost (Phase 3 only)

60 copies × ₹25 each at a Bangalore digital print shop (Pixel Tag, Kshetra, etc.) on 300 gsm = **₹1,500**. This is the entire `Print` line of the ₹2,000 plan.md §26 budget. Buffer line covers any reprint due to colour shift.

---

## 12. Anti-cliché checklist before commit

- [ ] Exactly three sunset-orange elements: zone 1 underline, zone 3 lane kickers, zone 3 orchestrator left edge. No fourth.
- [ ] No gradients, no glows, no drop shadows, no glassmorphism.
- [ ] No university crest, no flag, no festival motif, no chai cup, no street-food cliché.
- [ ] No isometric phone, no 3D phone, no real device chrome, no manufacturer logo.
- [ ] No stock photo, no robot, no brain, no light-bulb, no neuron.
- [ ] All numerals lining figures. ₹ glyph rendered as Unicode U+20B9.
- [ ] All captions pass the banned-word scan.
- [ ] QR code resolves to `https://github.com/ShAuRyA-Noodle/Combobulating` — verify by scanning before print run.

If all pass, export to PDF/X-1a and ship to print.
