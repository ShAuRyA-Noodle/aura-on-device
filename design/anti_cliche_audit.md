# Aura — Anti-Cliché Audit

One row per slide × six checks per row. A slide ships to the deck only when every check is "yes" or a recorded "n/a" with a one-line reason. Any "no" blocks the slide.

The six checks are the canonical deck_spec.md §7 list, rendered here as a per-slide ledger. Run before every commit to `deck/phase1_blueprint/aura_phase1_blueprint_v{N}.{pdf,pptx}`. Logged failures live in `deck/phase1_blueprint/audit.md` with date, slide, and rule.

---

## 0. The six checks

1. **Banned-word scan.** Every word on the slide checked against: *empower, leverage, seamless, revolutionary, game-changing, paradigm, unleash, harness, synergy, holistic, robust, cutting-edge, AI-powered, transformative*. **Y/N**
2. **Banned-visual scan.** Zero stock photos of happy people on phones, glowing brains, neurons, gradient blobs, glassmorphism, neon glows, generic robots, isometric phones in space, light-bulb metaphors, blue-gradient tech aesthetic, generic flag motifs, generic chai/festival imagery. **Y/N**
3. **Indian context honesty.** If the slide claims Indian context, it names a real artefact (UPI, IRCTC, BMTC, Namma Metro, Zomato, Swiggy, Blinkit, HDFC, Gmail receipt, etc.) rather than a stereotype. **Y/N/N/A**
4. **Citation hygiene.** Every numerical claim, named SOTA system, dataset, model, or API has either an inline citation `[n]` linked to a source in plan.md §37.1 / `docs/references.md`, or a `[TEAM TO VERIFY]` tag. **Y/N**
5. **Body-copy length.** Visible-on-slide body copy ≤ 30 words. Speaker notes do not count. **Y/N**
6. **Single-accent rule.** Sunset orange `#FF5B2E` used in ≤ 3 places on the slide and only on load-bearing elements (the answer, the wedge, the trace, the Aura row, the orchestrator edge). Zero gradients, glows, shadows in any element. **Y/N**

---

## 1. Per-slide audit ledger

| Slide | Title | (1) Banned word | (2) Banned visual | (3) India honest | (4) Citation | (5) ≤30 words | (6) Single accent | Pass? |
|---|---|---|---|---|---|---|---|---|
| 1 | Team Details | ☐ | ☐ | n/a | ☐ | ☐ | ☐ | ☐ |
| 2 | Problem Statement | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 3 | Proposed Solution | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4 | Technical Details | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4a | Plausibility (extended) | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5 | Novelty & Innovation | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 6 | Open Datasets | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 7 | Open Models | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 8 | AI / GenAI / Agentic Tools | ☐ | ☐ | n/a | ☐ | ☐ | ☐ | ☐ |
| 8a | Best Practices (extended) | ☐ | ☐ | n/a | ☐ | ☐ | ☐ | ☐ |
| 9 | Optional Supporting (KPI) | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

Tick every box (`Y` or `N/A` with reason recorded below) before flipping the **Pass?** column to `☑`. Any unchecked or `N` box keeps **Pass?** at `☐` and blocks the slide.

---

## 2. Per-slide quick-reference — what to look for

### Slide 1 — Team Details
- **(1)** Roll numbers, names, "co-founder, systems / build" labels — none of these are banned. Watch for "leveraging" creeping into a future bio.
- **(2)** No headshots. No university crest. No flag.
- **(3)** N/A — no Indian-context claim on this slide.
- **(4)** No citation needed; team data is self-verified.
- **(5)** Body copy is the four-line block. ~30 words. Verify with a counter.
- **(6)** Single sunset-orange underline beneath "Aura" in the bottom-left lockup. One element. Pass.

### Slide 2 — Problem Statement
- **(1)** Watch for "AI-powered" sneaking into "today's AI-powered assistants react". Replace with "today's assistants react".
- **(2)** No glowing brain. No neuron. No phone-with-gradient-screen.
- **(3)** Indian context appears only in speaker notes (HDFC, IRCTC, Zomato references). On-slide is universal — fine.
- **(4)** "237 notifications" cites Common Sense Media 2023. Pew + WHO secondary cites.
- **(5)** Body copy ~29 words. Verify.
- **(6)** Sunset orange on: 4 dots in the dot grid + 1 arrow + 3 square bullets = potentially 8 orange elements. **Watch this.** Reduce by treating the dot-grid orange and arrow orange as a single design system (one accent treatment), and dropping the square bullets to 60% ink. **Re-audit after the asset lands.**

### Slide 3 — Proposed Solution
- **(1)** "On-device, multi-agent, empathetic intelligence layer" — "empathetic" is fine. "Multi-agent" is fine. None banned.
- **(2)** Pixel/Galaxy phone frame must be neutral line-art, no manufacturer chrome.
- **(3)** Morning Brief screenshot names BMTC, DSA, LT-3 — real artefacts. Pass.
- **(4)** Health Connect [3], Phi-3-mini [4] cited. UPI/IRCTC/Zomato are named artefacts, not citation-required claims.
- **(5)** Body copy ~26 words.
- **(6)** Sunset orange on: three annotation arrows + the "leave by 8:15" underline inside the screenshot = 4. **Reduce annotations to ink black with orange only on arrowheads, or drop annotation count to 2.**

### Slide 4 — Technical Details
- **(1)** Architecture labels ("Sense", "Intelligence", "Experience", "Orchestrator") — clean.
- **(2)** No isometric phones in space. No glow on the orchestrator. Diagram is line-art only.
- **(3)** APIs are universal; iOS/Android, not Indian-specific. N/A on this slide.
- **(4)** Health Connect [3], UsageStatsManager [5], NotificationListenerService [6], Phi-3-mini [4], LangGraph [7], Gemma [8], HealthKit [9] all cited.
- **(5)** Body copy ~27 words.
- **(6)** Sunset orange on: orchestrator left edge + one trace arrow + lane kickers (3 kickers count as one design choice). 3 elements max. Pass if the lane kickers stay in `#FF5B2E`.

### Slide 4a — Plausibility (extended)
- **(1)** "Production target", "reference build" — none banned.
- **(2)** Table only, no visuals. Pass.
- **(3)** Mentions iOS limits explicitly — honest. Pass.
- **(4)** Same citations as slide 4. iOS DeviceActivity tagged `[TEAM TO VERIFY]` until docs URL added.
- **(5)** Body copy ~28 words.
- **(6)** Sunset orange on: header underline + 3 warning triangles (assuming 3 limit cells) = 4. **Reduce to underline + 1 grouped warning treatment, or drop the underline.**

### Slide 5 — Novelty & Innovation
- **(1)** "Indian context depth, biometric closed loop, glass-box reasoning, silence, owned memory" — clean.
- **(2)** Comparison table only. No visuals.
- **(3)** Indian context wedge names UPI, IRCTC, Zomato in speaker notes — pass.
- **(4)** Gemini [10], Apple Intelligence [11], Galaxy AI/Bixby [12], Knox [13], Health Connect [3], HealthKit [9], UPI [14] all cited.
- **(5)** Body copy ~22 words.
- **(6)** Sunset orange on: Aura row glyphs (7) + Aura row left edge + Aura row top/bottom rules. **Per deck_spec.md §5.4 this row is the deck's single signature moment — the per-row accent is the load-bearing exception. Counts as one design decision (the Aura row treatment), not as 9 separate orange elements.** Pass.

### Slide 6 — Open Datasets
- **(1)** "Anonymised CSV", "training corpus" — clean.
- **(2)** No visuals beyond list rows.
- **(3)** "Indian SMS / Gmail receipt parser corpus" names real artefacts. Pass.
- **(4)** LSApp [15], Pew [16], WHO [17], Kantar [18], Health Connect [3], HealthKit [9] cited. Tsinghua + Melbourne tagged `[TEAM TO VERIFY URLs]`.
- **(5)** Body copy ~27 words.
- **(6)** Sunset orange on: right-column 4-px top edge of the "Data we will publish" block. 1 element. Pass.

### Slide 7 — Open Models
- **(1)** "Off-the-shelf", "fallback", "trained by us" — clean.
- **(2)** Table only.
- **(3)** "Indian email and notification corpus", "UPI SMS samples" named in speaker notes — pass.
- **(4)** Phi-3 [4], Gemma [8], MediaPipe [10], llama.cpp [19], ExecuTorch [20] cited. Llama-3 license tagged `[TEAM TO VERIFY]`.
- **(5)** Body copy ~28 words.
- **(6)** Sunset orange on: 2 license-warning squares (Gemma terms, Llama license) + "Owned weights" dots (3 — Comms LoRA, Finance LoRA, LSTM). 5 elements. **Reduce to 1 license-warning glyph treatment + 1 owned-weights glyph treatment = 2 design decisions. Pass.**

### Slide 8 — Tools
- **(1)** "Deterministic state machine", "vector store" — clean.
- **(2)** Bento tiles only, no glow.
- **(3)** Tools are universal. N/A.
- **(4)** LangGraph [7], MediaPipe [10], llama.cpp [19], ExecuTorch [20], CrewAI [21], AutoGen [22] cited.
- **(5)** Body copy ~29 words.
- **(6)** Sunset orange on: 2 tile top edges (LangGraph, sqlite-vss). 2 elements. Pass.

### Slide 8a — Best Practices (extended)
- **(1)** "Free-form chatter" — fine. "No black box" — fine.
- **(2)** JSON code block + 3 cards. No visuals.
- **(3)** N/A.
- **(4)** LangGraph [7], Phi-3 [4], AutoGen [22] cited.
- **(5)** Body copy ~28 words.
- **(6)** Sunset orange on: 3 JSON keys (`chosen`, `rationale`, `confirm_required`). 3 elements. Pass.

### Slide 9 — Optional Supporting (KPI)
- **(1)** "Raw CSV", "paired bars", "confidence intervals" — clean.
- **(2)** Bar chart + numbers + QR. No visuals.
- **(3)** Pilot recruitment names Thapar campus, Bangalore — pass.
- **(4)** KPI targets cite the brief `[BRIEF]`. Methodology cites plan.md §22–23. All bars currently dashed = `[Phase 2]` tag covers the citation requirement honestly.
- **(5)** Body copy ~26 words.
- **(6)** Sunset orange on: 6 Aura bars + their error bars (when measured) + the QR code's thin border. **The Aura-bars treatment is one design decision (the colour-by-condition rule). The QR border is the second.** 2 design decisions. Pass.

---

## 3. Logging failures

When a check fails, append a single row to `deck/phase1_blueprint/audit.md`:

```
2026-MM-DD · slide N · rule X failed · reason · owner · resolution date
```

Example:
```
2026-05-21 · slide 3 · rule 6 failed · 4 sunset-orange annotations · Shaurya · 2026-05-22
```

Resolved entries get a strikethrough — never deleted. The audit log is the deck's tamper-evidence equivalent of the memory graph's Merkle root: an honest record that we caught the slip and fixed it.

---

## 4. The meta-rule

If a slide passes all six checks but **still** feels generic when reviewed against Linear, Arc, Nothing OS, Things 3, Apple HIG, and Stripe docs as visual references — the audit failed at the meta level. Run a 7th informal check: **"Would Linear or Arc ship this slide?"** If the answer is "no, this looks like every other AI deck", revise. Anti-cliché is the floor. Editorial taste is the ceiling.
