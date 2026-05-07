# Aura Screen 04 — Spend Mirror

Generated via the `imagegen-frontend-mobile` skill, conformed to plan.md §7 (Journey D) + §12.3 + deck_spec.md §0/§1 locks. This screen materialises the FinanceAgent surface: a parsed UPI SMS becoming a proactive, glanceable trajectory card.

Render target: 1920 × 1080, single iPhone-style line-art phone frame centred on warm off-white. Recommended tool: Nano Banana. Fallback: ChatGPT image gen, Midjourney v7. Paste the prompt below verbatim.

---

## Prompt — paste verbatim

> A premium, editorial single-screen mobile app mockup for the **Spend Mirror** screen of a product called **Aura**. The screen is rendered inside a NEUTRAL line-art phone frame — a generic abstract iPhone-style outline drawn as a single 1.5-px ink-black stroke around a rectangular display, soft 24-px corner radius, a small notch cut at the top, one thin button on each side, head-on flat front view, no 3D tilt, no isometric, no glow, no drop shadow, no Apple chrome, no Galaxy chrome, no manufacturer logo, no real device branding, no lock-screen wallpaper. The frame sits centred on a warm off-white background hex **#FAF8F5** with a faint paper-grain texture. Aspect ratio 1920×1080.
>
> Inside the screen, render the **Aura Spend Mirror** screen. Background of the screen content is the same warm off-white #FAF8F5. Ink black hex **#0E0E0E** for type and rules. One single warm accent hex **#FF5B2E** sunset orange, used exactly twice on this screen: (a) underline beneath the over-budget hero number, (b) the small dot marking the over-budget bar in the weekly chart. Nowhere else.
>
> Type system: **Fraunces** Regular for the title and the hero spend numeral; **Inter Tight** Regular for body, suggestion text, and pill labels; **JetBrains Mono** for the SMS quote and all numeric tags.
>
> Layout, top to bottom, screen edge padding 20 px:
>
> Status row at the top: the time "**21:14**" in JetBrains Mono 14 pt left-aligned. Right-aligned, three small ink-black status glyphs — a generic signal bar, a generic Wi-Fi arc, a battery rectangle — drawn as flat 1-px line-art icons, no fills, no colour. No carrier name.
>
> Title block: a Inter Tight tracked +40 kicker reading "TAB 03 · FINANCE · TUESDAY 07 MAY" in 12 pt at 60% ink. Immediately below, the title "**Spend mirror**" set in Fraunces 40 pt left-aligned dark ink. Below the title, in Inter Tight 14 pt at 60% ink, a one-line subhead: "One UPI text. One reality check."
>
> Card 1 — parsed SMS card. A clean rectangular card with a 1-px ink hairline rule above and below, no fill, no shadow. Inside the card, two stacked rows. Row 1 in Inter Tight tracked +40 12 pt at 60% ink: "PARSED FROM SMS · HDFC · 21:11". Row 2 in JetBrains Mono 14 pt dark ink, rendered as a single quoted line with proper monospace tracking: `"INR 450.00 debited from a/c XX4512 to ZOMATO via UPI/...    "`. Beneath that mono line, a thin 1-px ink hairline guide. Below the guide, a small 12 pt sans label at 60% ink: "Parsed locally. SMS body not stored." No bank logo, no Zomato logo, no payment-app chrome.
>
> Card 2 — today's spend hero card. A taller card with a 1-px ink hairline above and below, no fill. Inside, a vertically stacked layout. Top row, Inter Tight tracked +40 12 pt at 60% ink: "TODAY · ALL UPI + CARDS". Middle row, the hero numeral set in Fraunces 88 pt left-aligned: "**₹2,450**". The rupee glyph rendered as a real Unicode ₹, dark ink, same weight as the digits. Below the numeral, on a single line in Inter Tight 16 pt: "₹600 over your weekday average · ₹2,400 over weekly budget." The phrase "₹2,400 over weekly budget" is underlined with a 4-px hand-drawn-feel sunset-orange #FF5B2E underline — this is the only sunset-orange line on the screen. To the right of the numeral, a tiny inline horizontal bar chart in 1-px ink-black bars showing seven days Mon through Sun, six bars dark ink, the seventh bar (today, Tuesday) markedly taller and capped with a small solid 6-px sunset-orange #FF5B2E dot at its top — the only orange dot on the screen. JetBrains Mono 10 pt day labels "M T W T F S S" beneath the bars. No fills inside the bars beyond the 1-px stroke.
>
> Card 3 — top category card. A row card with 1-px hairline below. Inside, two stacked lines. Line 1 in Inter Tight 16 pt: "Zomato · 3 orders this week · ₹1,140". Line 2 in Inter Tight 14 pt at 60% ink: "Last week · 1 order · ₹420." No restaurant logos, no app marks, type only.
>
> Card 4 — projection card. A row card with 1-px hairline below. Inside, two stacked lines. Line 1 in Inter Tight 16 pt: "If this rate continues · projected weekly ₹4,800". Line 2 in JetBrains Mono 14 pt at 60% ink: "vs budget ₹2,400 · over by 2.0×".
>
> Suggestion block — the ask. A taller block with a 1-px ink hairline above and below, no fill. Two stacked rows. Row 1 in Inter Tight tracked +40 12 pt at 60% ink: "AURA SUGGESTS". Row 2 in Fraunces 28 pt regular dark ink: "**Cook tomorrow?**" Below those rows, a small 14 pt sans line at 60% ink: "Skips one Zomato order. Saves about ₹380. Confirm or dismiss." To the far right of the block, two small pill buttons stacked vertically, each 1-px ink-stroke outline, no fill: "Confirm" (filled solid ink, label in warm off-white) and "Dismiss" (outline only). The Confirm pill is the only filled button on the screen.
>
> Footer strip pinned at the bottom: a thin bar reading "**Silence Budget · 2 of 3 left today**" set in JetBrains Mono 14 pt at 60% ink, with two small filled square dots in dark ink and one outlined empty square to its right indicating one surface used today. The bar has a 1-px ink hairline above it. A thin neutral home-indicator line below.
>
> Strict English on every label. Real artefacts named naturally — UPI, HDFC, Zomato, ₹ — never as a stereotype, never as Hinglish.
>
> Strictly forbidden — must not appear anywhere on the screen: glassmorphism, frosted glass, gradient backgrounds, gradient blobs, neon glows, drop shadows on cards, glowing brain or neuron graphics, AI hand-of-god illustrations, light-bulb icons, generic robot or chatbot mascots, isometric phones, 3D phones, blue tech-gradient aesthetic, real Apple device chrome, real Galaxy device chrome, manufacturer logos, real bank logos, real Zomato or Swiggy logos, app icon grids that mimic iOS or Android home screens, lock-screen wallpapers, stock photography of food or restaurants, the words empower, leverage, seamless, revolutionary, paradigm, holistic, robust, cutting-edge, AI-powered, transformative, exclamation marks, decorative emojis. No more than two sunset-orange elements anywhere on the screen.
>
> Reference vocabulary: Linear product UI, Things 3 cards, Apple Human Interface Guidelines list pages, Stripe Dashboard transaction rows, Cred app's quieter pages, Splitwise list views. Calm, generous, editorial, slightly serious. The screen should look like one frame from a finished indie finance-aware product, not a concept render.
