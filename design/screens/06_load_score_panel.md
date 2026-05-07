# Aura Screen 06 — Load Score Panel

Generated via the `imagegen-frontend-mobile` skill, conformed to plan.md §11 + §12.4 + deck_spec.md §0/§1 locks. This screen materialises the WellnessAgent's closed-loop biometric-to-action surface: a Load Score crossing threshold, drivers exposed, and a single intervention proposed.

Render target: 1920 × 1080, single iPhone-style line-art phone frame centred on warm off-white. Recommended tool: Nano Banana. Fallback: ChatGPT image gen, Midjourney v7. Paste the prompt below verbatim.

---

## Prompt — paste verbatim

> A premium, editorial single-screen mobile app mockup for the **Load Score panel** of a product called **Aura**. The screen is rendered inside a NEUTRAL line-art phone frame — a generic abstract iPhone-style outline drawn as a single 1.5-px ink-black stroke around a rectangular display, soft 24-px corner radius, a small notch cut at the top, one thin button on each side, head-on flat front view, no 3D tilt, no isometric, no glow, no drop shadow, no Apple chrome, no Galaxy chrome, no manufacturer logo, no real device branding, no lock-screen wallpaper. The frame sits centred on a warm off-white background hex **#FAF8F5** with a faint paper-grain texture. Aspect ratio 1920×1080.
>
> Inside the screen, render the **Aura Load Score** panel. Background of the screen content is the same warm off-white #FAF8F5. Ink black hex **#0E0E0E** for type and rules. One single warm accent hex **#FF5B2E** sunset orange, used twice on this screen: (a) on the "78" hero numeral's right-most digit slope or as a 4-px hand-drawn-feel underline beneath the score, (b) on the 4-px left edge accent of the intervention card. Nowhere else.
>
> Type system: **Fraunces** Regular for the title, the hero score numeral, and the intervention headline; **Inter Tight** Regular for body, driver labels, and pill labels; **JetBrains Mono** for the metric values, timestamps, and the small threshold tag.
>
> Layout, top to bottom, screen edge padding 20 px:
>
> Status row at the top: the time "**22:33**" in JetBrains Mono 14 pt left-aligned. Right-aligned, three small ink-black status glyphs — a generic signal bar, a generic Wi-Fi arc, a battery rectangle — drawn as flat 1-px line-art icons, no fills, no colour. No carrier name.
>
> Title block: a Inter Tight tracked +40 kicker reading "WELLNESS · LIVE · TUESDAY 07 MAY" in 12 pt at 60% ink. Immediately below, the title "**Load**" set in Fraunces 40 pt left-aligned dark ink. Below the title, in Inter Tight 14 pt at 60% ink, a one-line subhead: "Your body is louder than your inbox right now."
>
> Hero score card: a tall rectangular card with 1-px ink hairlines above and below, no fill, no shadow. Inside the card, a left-aligned vertical stack. Top row in Inter Tight tracked +40 12 pt at 60% ink: "LOAD SCORE · 5-MIN ROLLING". Below the kicker, the hero numeral "**78**" set in Fraunces 200 pt left-aligned dark ink, with the suffix "/100" in Inter Tight 32 pt at 60% ink set in-line to the bottom-right of the numeral. Beneath the numeral, a 4-px hand-drawn-feel sunset-orange **#FF5B2E** underline runs the width of the "78" only — this is the first orange element on the screen. Below the underline, in JetBrains Mono 14 pt at 60% ink: "threshold · 70 · last 5 min · +12". To the far right of the card, a tiny inline ribbon line chart in 1-px ink-black stroke showing a 30-minute trace climbing from roughly 38 at the left to 78 at the right, with a thin 1-px dashed horizontal threshold line at "70" labelled in JetBrains Mono 10 pt. The right end of the trace caps with a small 6-px ink-black dot, no fill changes, no colour beyond ink. JetBrains Mono 10 pt time labels "22:00" and "22:30" sit at the chart's left and right ends.
>
> Drivers row — three driver cells side by side, evenly spaced, separated by 1-px ink hairline dividers vertical between them. Each cell holds three stacked lines:
>
> Cell 1 — top line in Inter Tight tracked +40 12 pt at 60% ink: "DRIVER 1". Middle line in Fraunces 24 pt regular: "**HRV**". Bottom line in JetBrains Mono 14 pt: "RMSSD 28 ms · −1.4 SD".
>
> Cell 2 — top line "DRIVER 2". Middle line Fraunces 24 pt: "**Typing entropy**". Bottom line JetBrains Mono 14 pt: "+0.8 SD · last 12 min".
>
> Cell 3 — top line "OTHER". Middle line Inter Tight 16 pt at 60% ink: "App switch rate · sleep debt · notif dismiss." Bottom line JetBrains Mono 12 pt at 60% ink: "below threshold contribution".
>
> Intervention card — the ask. A taller card with a 4-px sunset-orange **#FF5B2E** left edge accent — the second and final orange element on the screen — no fill, 1-px ink hairlines top and bottom. Inside the card, a stacked layout. Top row in Inter Tight tracked +40 12 pt at 60% ink: "AURA SUGGESTS · ONE INTERVENTION". Middle row in Fraunces 32 pt regular dark ink: "**Mute project group · 30 min.**" Below the headline, in Inter Tight 14 pt at 60% ink: "You're in flow. WhatsApp DBMS group is the noisiest channel right now. Aura will surface a digest at 23:03." To the far right of the card, two small pill buttons stacked vertically: a "Confirm" pill (filled solid ink, label in warm off-white, Inter Tight 14 pt regular — the only filled button on the screen) and a "Dismiss" pill (1-px ink stroke outline, no fill). A third tiny pill below in Inter Tight 12 pt reads "Tell me when not to", outlined.
>
> Reasoning Trace teaser link: a single line below the intervention card, set in JetBrains Mono 12 pt at 60% ink, with a small 1.5-px ink chevron glyph at the right end: "why this card · open trace ›". A typographic affordance only, no button frame.
>
> Footer strip pinned at the bottom: a thin bar reading "**Silence Budget · 2 of 3 left today**" set in JetBrains Mono 14 pt at 60% ink, with two small filled square dots in dark ink and one outlined empty square to its right indicating one surface used today. The bar has a 1-px ink hairline above it. A thin neutral home-indicator line below.
>
> Strict English on every label. Real artefacts named naturally — RMSSD, HRV, WhatsApp as a context word, DBMS — never as a stereotype, never as Hinglish.
>
> Strictly forbidden — must not appear anywhere on the screen: glassmorphism, frosted glass, gradient backgrounds, gradient blobs, neon glows, drop shadows on cards, glowing brain or neuron graphics, heart-rate ECG illustrations with glow, AI hand-of-god illustrations, light-bulb icons, generic robot or chatbot mascots, meditation lotus icons, isometric phones, 3D phones, blue tech-gradient aesthetic, real Apple device chrome, real Galaxy device chrome, real Apple Watch UI, real Galaxy Watch UI, real Samsung Health chrome, manufacturer logos, app icon grids, lock-screen wallpapers, stock photography of stressed people, the words empower, leverage, seamless, revolutionary, paradigm, holistic, robust, cutting-edge, AI-powered, transformative, exclamation marks, decorative emojis. No more than two sunset-orange elements on the screen.
>
> Reference vocabulary: Linear product UI, Things 3 panel detail views, Apple Human Interface Guidelines stat pages, Stripe Dashboard live metrics, Whoop's quieter screens (without the saturated brand colour), Oura's stat panels (without the brand teal). Calm, generous, editorial, slightly serious. The screen should look like one frame from a finished indie wellness-aware product, not a concept render.
