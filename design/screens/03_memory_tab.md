# Aura Screen 03 — Memory Tab

Generated via the `imagegen-frontend-mobile` skill, conformed to plan.md §14 + deck_spec.md §0/§1 locks. This screen is the user-owned memory graph view — the visible proof of the §9.5 wedge.

Render target: 1920 × 1080, single iPhone-style line-art phone frame centred on warm off-white. Recommended tool: Nano Banana. Fallback: ChatGPT image gen, Midjourney v7. Paste the prompt below verbatim.

---

## Prompt — paste verbatim

> A premium, editorial single-screen mobile app mockup for the **Memory** tab of a product called **Aura**. The screen is rendered inside a NEUTRAL line-art phone frame — a generic abstract iPhone-style outline drawn as a single 1.5-px ink-black stroke around a rectangular display, soft 24-px corner radius, a small notch cut at the top, one thin button on each side, head-on flat front view, no 3D tilt, no isometric, no glow, no drop shadow, no Apple chrome, no Galaxy chrome, no manufacturer logo, no real device branding, no lock-screen wallpaper. The frame sits centred on a warm off-white background hex **#FAF8F5** with a faint paper-grain texture. Aspect ratio 1920×1080.
>
> Inside the screen, render the **Aura Memory** tab. Background of the screen content is the same warm off-white #FAF8F5. Ink black hex **#0E0E0E** for type and rules. One single warm accent hex **#FF5B2E** sunset orange, applied only to (a) the 4-px left edge of the audit-log Merkle hash badge, and (b) the small dot inside the "Action" node of the graph. Two orange touches total, no more.
>
> Type system: **Fraunces** Regular for the screen title and section headings; **Inter Tight** Regular for body, button labels, and node captions; **JetBrains Mono** for hashes, hex strings, and node IDs.
>
> Layout, top to bottom, screen edge padding 20 px:
>
> Status row at the top: the time "**14:02**" in JetBrains Mono 14 pt left-aligned. Right-aligned, three small ink-black status glyphs — a generic signal bar, a generic Wi-Fi arc, a battery rectangle — drawn as flat 1-px line-art icons, no fills, no colour. No carrier name.
>
> Title block: a Inter Tight tracked +40 kicker reading "TAB 04 · YOUR DATA" in 12 pt at 60% ink, then immediately below it the title "**Memory**" set in Fraunces 40 pt left-aligned dark ink. Below the title, a one-line subhead in Inter Tight 14 pt at 60% ink: "Local. Encrypted. Yours to export or erase."
>
> Graph viewport — the hero of the screen, ~52% of vertical space. A clean rectangular viewport with a 1-px ink hairline rule above and below, no fill, no shadow. Inside the viewport, render an exportable on-device memory-graph illustration drawn entirely in 1-px ink hairlines: seven small circular nodes laid out in a calm asymmetric constellation — never a perfect grid, never a perfect circle. Each node is a 28-px ink-stroke ring with no fill, the node label set in Inter Tight 12 pt directly below the ring, and a JetBrains Mono 10-pt count tag in dark ink at 60% opacity below the label (e.g. "412"). The seven nodes, in this order around the viewport: "User · 1" (centre-left), "Event · 412" (upper centre), "Person · 87" (upper right), "Place · 34" (right), "Transaction · 1,204" (lower right), "Health · 2,910" (lower centre), "Action · 18". Connect the nodes with thin 1-px ink straight lines — never curved beziers, never glowing — only orthogonal or 45-degree segments, with small empty circle terminals at each end. The "Action" node sits slightly larger at 32 px and carries a tiny solid 6-px sunset-orange #FF5B2E dot at its centre — that is the only orange in the graph. To the upper-right corner of the viewport, set a JetBrains Mono 10 pt label "scope · last 90 days" at 60% ink. No icons inside nodes, no avatars, no thumbnails.
>
> Action row: directly below the graph, three pill buttons set side by side, evenly spaced, each 1-px ink-stroke outline, no fill, label in Inter Tight 14 pt regular dark ink. Labels left to right: "Export to JSON", "Delete by time range", "Audit log". 16-px gap between pills. No icons inside the pills.
>
> Range scrubber row: a thin horizontal 1-px hairline track spanning the full content width. Two small ink-stroke handle dots sit on the track at roughly 30% and 80% positions, each 8 px diameter, no fill. Above the track, in JetBrains Mono 12 pt at 60% ink, the labels "from · 2026-02-06" left-aligned and "to · 2026-05-07" right-aligned. Below the track, in Inter Tight 12 pt at 60% ink: "147 nodes in range · tap Delete by time range to remove."
>
> Audit log preview block: a single rectangular block with a 4-px sunset-orange **#FF5B2E** left edge accent — the only orange edge on the screen — no fill, 1-px ink hairlines top and bottom. Inside the block, two stacked rows. Row 1 in Inter Tight tracked +40 12 pt: "AUDIT LOG · TAMPER-EVIDENT". Row 2 in JetBrains Mono 14 pt dark ink: "today · merkle sha256 9c4f8e2b…b21a · 23 reads · 6 writes". Below those rows, a tiny Inter Tight 12 pt italic line at 60% ink: "Each day's root chains to yesterday's. Any tamper breaks the chain."
>
> Footer strip pinned at the bottom: a thin bar in JetBrains Mono 12 pt at 60% ink reading "**local · encrypted · 0 bytes leave without your tap**", centred. A thin neutral home-indicator line below.
>
> Strict English on every label. The screen names real artefacts naturally — sha256, JSON, RMSSD where relevant — never as a stereotype, never as Hinglish.
>
> Strictly forbidden — must not appear anywhere on the screen: glassmorphism, frosted glass, gradient backgrounds, gradient blobs, neon glows, drop shadows on cards, glowing brain or neuron graphics, AI hand-of-god illustrations, light-bulb icons, generic robot or chatbot mascots, isometric phones, 3D phones, blue tech-gradient aesthetic, real Apple device chrome, real Galaxy device chrome, manufacturer logos, app icon grids that mimic iOS or Android home screens, lock-screen wallpapers, stock photography, the words empower, leverage, seamless, revolutionary, paradigm, holistic, robust, cutting-edge, AI-powered, transformative, exclamation marks, decorative emojis. No more than two sunset-orange elements anywhere on the screen, both on load-bearing elements named above.
>
> Reference vocabulary: Linear product UI, Things 3 list pages, Apple Human Interface Guidelines reference views, Stripe Dashboard data tables, GitHub repo Insights tabs, Notion database views. Calm, generous, editorial, slightly serious. The screen should look like one frame from a finished indie privacy-first product, not a concept render.
