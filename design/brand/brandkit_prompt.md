# Aura — Brand Kit Image-Generation Prompt

Generated via the `brandkit` skill, conformed to plan.md §5 + deck_spec.md §0/§1 locks.

Render target: 3840 × 2160 (16:9, 4K). Single editorial brand-board composition. Designed to be exported as one master image suitable for cover use and Phase 1 internal review.

Recommended tool: Nano Banana (free, fast iteration). Fallback: ChatGPT image gen, Midjourney v7, Sora image mode. Paste the prompt below verbatim. No follow-up turn required.

---

## Prompt — paste verbatim

> An editorial, magazine-spread brand-guidelines board for a product called **Aura**, an on-device empathetic intelligence layer for Indian Gen Z. Aspect ratio 16:9, ultra-high resolution 3840×2160. Cinematic, calm, confident composition.
>
> Background: a single warm off-white plane, hex **#FAF8F5**, very faint paper-grain texture, no gradient, no vignette. Ink black hex **#0E0E0E** for type and rules. One single warm accent: sunset orange hex **#FF5B2E**, used sparingly on five load-bearing elements only (named below).
>
> Type system on the board: a display serif **Fraunces** (Regular weight, lining figures, no swashes) for the wordmark, hero numerals, and section titles, and a body sans **Inter Tight** for descriptive captions and small labels, and **JetBrains Mono** at small sizes for code, JSON keys, and API names. No other typefaces appear.
>
> Composition is a strict 12-column grid with 96-px gutters and 80-px outer margins, photographed top-down with even editorial light. Layout is divided into seven labelled zones, like a Linear, Arc, Nothing OS, Teenage Engineering, or Things 3 brand spec board:
>
> Zone 1 — top-left, eight columns wide. A large logotype lockup. The wordmark "**Aura**" set in Fraunces at very large size, dark ink. Directly under it, the locked tagline "Anticipate. Act. Stay quiet." set in Inter Tight at one-tenth the wordmark height, regular weight. A single hand-drawn-feel sunset-orange underline, 4 px stroke, sits beneath the word "Aura". The mark is purely typographic — there is no symbol, no pictogram, no glyph mascot.
>
> Zone 2 — top-right, four columns wide. A vertical column of three small logo concept variants, each labelled in JetBrains Mono caption: (a) wordmark only, (b) wordmark with a small typographic dot accent in sunset orange replacing the dot of a lowercase letter form, (c) a monogram "Au" set in Fraunces with a square 8×8 px sunset-orange dot to its lower-right baseline. Each concept sits in its own bordered cell with a 1-px ink hairline.
>
> Zone 3 — middle-left, six columns wide. A full palette swatch row. Five rectangular swatches, each 320×320 px, butted edge-to-edge with no gap, in this order from left to right: warm off-white **#FAF8F5** (labelled "PAPER"), ink black **#0E0E0E** (labelled "INK"), sunset orange **#FF5B2E** (labelled "ACCENT"), a 60-percent ink tint **#5C5C5C** (labelled "INK 60") for body copy, and a 20-percent ink tint **#CCCCCC** (labelled "RULE 20") for hairlines. Each swatch carries its hex value in JetBrains Mono 16 pt below the swatch and the role label in Inter Tight tracked +40 in 14 pt above.
>
> Zone 4 — middle-right, six columns wide. Type lockups. Three stacked specimen rows. Row A: the alphabet and digits 0–9 set in Fraunces Regular at 96 pt, labelled "DISPLAY · FRAUNCES" in Inter Tight tracked +40. Row B: the alphabet and digits 0–9 set in Inter Tight Regular at 32 pt, labelled "BODY · INTER TIGHT". Row C: a single line of mono code, exactly the string `"chosen": "MUTE_GROUP_30"`, set in JetBrains Mono at 22 pt, labelled "MONO · JETBRAINS MONO". A single 240-pt Fraunces numeral "**237**" anchors the right edge of this zone in dark ink, with the caption "AVERAGE NOTIFICATIONS / DAY" in 14 pt sans tracked +40 below it.
>
> Zone 5 — lower-left, twelve columns wide spanning the bottom half. Three iPhone-style line-art phone frames sitting side by side, evenly spaced. The frames are NEUTRAL — generic line-art chrome only, drawn as 1.5-px ink-black outlines around a rectangular screen with a small notch cut, soft 24-px corner radius, a single thin button on each side, no logos, no Apple chrome, no Galaxy chrome, no manufacturer marks, no bezels rendered as 3D, no glow, no shadow, no isometric tilt, head-on flat front view. Inside each frame, a real Aura app screen mockup is rendered:
>
> Frame A — "Morning Brief" screen. Top of screen: a small status row with "7:45" in mono. A Fraunces display heading "Brief" sits left-aligned. Below it, a stacked card list, each card a clean rectangle with 1-px hairline rule below it, no fills, no shadows. Card 1: the line "Slept 5.2 hours · push gym to evening", with a small ink-black icon to its left. Card 2: "DSA Quiz · 9:00 · LT-3 · leave by 8:15", with the "leave by 8:15" segment underlined in **#FF5B2E**. Card 3: "Prof slides summarised — 11 cards ready." Card 4: "Three friends going — Anu, Manish, Riya." Footer: a thin bar reading "Silence Budget · 3 of 3 left today" in mono. Sunset orange appears once on this screen, on the "leave by 8:15" underline.
>
> Frame B — "Reasoning Trace" screen. Top: a back chevron and the title "Why this card" in Fraunces. Below: a five-section JSON-styled block rendered like a Stripe API documentation page, set in JetBrains Mono at 16 pt. The JSON keys `"chosen"`, `"rationale"`, and `"confirm_required"` are coloured in sunset orange #FF5B2E, while every other key, brace, and value is dark ink. The visible content reads: trace_id "tr_b1d77ef33c20", trigger source "comms_burst" with value count 47 window_min 8, signals listing rmssd_ms 28, load_score 78, actionable_count 3, social_count 44, candidates listing MUTE_GROUP_30 score 0.78, BATCH_DIGEST score 0.62, BREATHE_478 score 0.55, do_nothing 0.30, chosen "MUTE_GROUP_30", rationale "HRV down 1.4 SD, 47 messages in 8 min, 3 actionable. Mute 30 min, digest after.", confirm_required true, outcome "confirmed". Bottom of the screen: two pill buttons, "Confirm" in solid ink and "Dismiss" in outline.
>
> Frame C — "Memory" screen. Title "Memory" in Fraunces at top. Below the title, a small node-graph illustration in 1-px ink hairlines — six small circles connected by short straight lines, each circle labelled in mono caption: "Event", "Person", "Place", "Transaction", "Health", "Action". Below the graph, a row of three pill buttons in 1-px ink outline: "Export to JSON", "Delete by time-range", "View audit log". Below those, a thin badge reading "Audit · today's Merkle root sha256:9c4f…b21a" in JetBrains Mono 14 pt. The badge is the only sunset-orange element on this frame — its left edge is a 4-px sunset orange accent.
>
> Zone 6 — lower-right, four columns wide. A single full-bleed Reasoning Trace hero shot — the same JSON block from Frame B, but rendered at 2× zoom, dominating the cell, set on warm off-white. Above it, a 14-pt sans tracked +40 kicker reads "ONE ACTION · ONE TRACE". This is the signature visual of the product.
>
> Zone 7 — bottom strip, twelve columns wide, height ~200 px. A "Before / After" pair, side by side, separated by a vertical 1-px ink hairline. Left half labelled "STATUS QUO" in tracked sans: a tight grid of forty-one tiny rectangular notification rows, stacked, overlapping, every row a different generic-app label — none using real brand chrome — with the row count "41 buzzes · 0 read" set in Fraunces 56 pt at the top-left of the cluster. Visual feeling: cluttered, anxious, dense. Right half labelled "AURA": almost empty white space, a single calm card centred reading "1 thing for you · Anu — schema diagram for DBMS submission." in Fraunces 32 pt, with one sunset-orange "tap to confirm" pill button below. Visual feeling: calm, deliberate, room to breathe.
>
> Sparse hand-drawn-feel arrows in sunset orange, 1-px stroke, italicised tiny labels in Inter Tight 14 pt italic, point at exactly five elements across the entire board: (1) the underline beneath "Aura" in Zone 1 with the label "the only sunset on the board"; (2) the sunset-orange swatch in Zone 3 with the label "load-bearing accent only"; (3) the highlighted JSON keys in Frame B / Zone 6 with the label "the glass box"; (4) the audit badge in Frame C with the label "tamper-evident"; (5) the calm card on the right of Zone 7 with the label "stay quiet". No other annotations.
>
> Strict English in every label. Real artefact names appear naturally inside the mockups — UPI, IRCTC, BMTC, Zomato, Gmail, HDFC, HealthKit — never as a stereotype. No Hinglish.
>
> Strictly forbidden — must not appear anywhere on the board: glassmorphism, frosted glass, gradient blobs, neon glows, drop shadows on cards, glowing brain or neuron motifs, AI hand-of-god illustrations, light-bulb metaphors, generic robot or chatbot mascots, isometric phones floating in space, blue tech-gradient aesthetic, 3D-rendered phones, real Apple device chrome, real Galaxy device chrome, manufacturer logos, lock-screen wallpapers, stock photography of happy people on phones, Indian flag motifs, festival imagery, chai cups, generic street-food motifs, exclamation marks, emojis (other than where a UI element on a real phone would render as one in context), the words empower, leverage, seamless, revolutionary, paradigm, holistic, robust, cutting-edge, AI-powered, transformative, unleash, harness, synergy, game-changing.
>
> Photography reference vocabulary: Linear product pages, Arc browser release notes, Nothing OS press kit, Teenage Engineering OP-1 manual, Things 3 marketing, Apple Human Interface Guidelines, Stripe documentation, Editorial New magazine spreads. Cinematic top-down editorial composition. Calm, confident, slightly self-aware. Generous negative space. The overall feeling: a brand spec page from a serious indie software company, printed on warm off-white art-paper, photographed once and never retouched.

---

## Operator notes

- Render twice, pick the cleaner pass. Editorial brand boards usually take 2–3 attempts.
- If the model adds glow, drop shadows, or gradients, regenerate with the explicit reminder "no glow, no drop shadow, no gradient — flat warm-paper finish only."
- If a model substitutes a different orange, paste the hex `#FF5B2E` again at the top of the negative-prompt block.
- If real device chrome appears, regenerate with: "phones must be neutral line-art frames, no Apple, no Samsung, no Galaxy, no Pixel — generic abstract phone outlines only."
- Save as `design/brand/aura_brandkit_master.png` once approved. Do not crop.
