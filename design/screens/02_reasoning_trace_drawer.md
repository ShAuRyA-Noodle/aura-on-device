# Aura Screen 02 — Reasoning Trace Drawer

Generated via the `imagegen-frontend-mobile` skill, conformed to plan.md §13 + technical_spec.md §4.6/§5 + deck_spec.md §1 (Slide 8a) locks. This is the **signature visual of the product**.

Render target: 1920 × 1080, single iPhone-style line-art phone frame centred on warm off-white. Recommended tool: Nano Banana. Fallback: ChatGPT image gen, Midjourney v7. Paste the prompt below verbatim.

---

## Prompt — paste verbatim

> A premium, editorial single-screen mobile app mockup for the **Reasoning Trace drawer** screen of a product called **Aura**. The screen is rendered inside a NEUTRAL line-art phone frame — a generic abstract iPhone-style outline drawn as a single 1.5-px ink-black stroke, soft 24-px corner radius, a small notch cut at the top, head-on flat front view, no 3D tilt, no isometric, no glow, no drop shadow, no Apple chrome, no Galaxy chrome, no manufacturer logo. The frame sits centred on a warm off-white background hex **#FAF8F5** with a faint paper-grain texture. Aspect ratio 1920×1080.
>
> Inside the screen, render the **Reasoning Trace** drawer. Background of the screen content is the same warm off-white #FAF8F5. Ink black hex **#0E0E0E** for type and rules. One single warm accent hex **#FF5B2E** sunset orange, applied only to the JSON keys `chosen`, `rationale`, and `confirm_required` and to one thin left-edge accent on the trigger card. The screen's visual reference is **Stripe API documentation** — clean, type-led, generous negative space, monospace-led code rendering with sparse, deliberate accent colour.
>
> Type system: **Fraunces** Regular for the screen title; **Inter Tight** Regular for section labels and body; **JetBrains Mono** at 16 pt for the entire JSON block.
>
> Layout, top to bottom, screen edge padding 20 px:
>
> Top bar: a small back chevron drawn as a 1.5-px ink stroke at the left edge, the title "**Why this card**" set in Fraunces 24 pt centred, and a small "Edit" outlined pill at the right edge in Inter Tight 12 pt.
>
> Section label row: in Inter Tight tracked +40 12 pt, the kicker "REASONING TRACE · v1" left-aligned in dark ink at 60% opacity.
>
> Trigger card: a thin rectangular card with a 4-px sunset-orange **#FF5B2E** left edge accent (the only orange edge on the screen), no fill, 1-px ink hairline above and below. Inside: a single line set in Inter Tight 14 pt — "Trigger · comms_burst · 47 messages in 8 min".
>
> JSON block — the hero of the screen, ~80% of vertical space. The block is rendered as a clean monospace code listing in JetBrains Mono 16 pt, ink black on warm off-white, line-height generous, with subtle 1-px ink-grey 20%-opacity guide rules between major sections. The block is NOT in a dark-mode terminal panel and has NO syntax-highlight rainbow — only ink black for everything except three keys, which are coloured in sunset orange #FF5B2E. The orange keys are exactly: `"chosen"`, `"rationale"`, and `"confirm_required"`. Their string values are dark ink, not orange. Quotation marks, braces, brackets, commas, and colons are all dark ink. The visible JSON is exactly this content, formatted as a pretty-printed object with indented two-space sub-objects and arrays:
>
> ```
> {
>   "trace_id": "tr_b1d77ef33c20",
>   "ts": "2026-05-07T22:31:47+05:30",
>   "trigger": {
>     "source": "comms_burst",
>     "value": { "count": 47, "window_min": 8 }
>   },
>   "signals": [
>     { "k": "channel", "v": "<group_id_h_88a>" },
>     { "k": "actionable_count", "v": 3 },
>     { "k": "social_count", "v": 44 },
>     { "k": "rmssd_ms", "v": 28 },
>     { "k": "load_score", "v": 78 }
>   ],
>   "candidates": [
>     { "kind": "MUTE_GROUP_30", "score": 0.78, "confirm_required": true },
>     { "kind": "BATCH_DIGEST",  "score": 0.62, "confirm_required": false },
>     { "kind": "BREATHE_478",   "score": 0.55, "confirm_required": true },
>     { "kind": "do_nothing",    "score": 0.30 }
>   ],
>   "chosen": "MUTE_GROUP_30",
>   "rationale": "HRV down 1.4 SD, 47 messages in 8 min, 3 actionable. Mute 30 min, digest after.",
>   "rationale_source": "llm",
>   "confirm_required": true,
>   "outcome": "confirmed"
> }
> ```
>
> Render the JSON exactly as above, every comma, brace, bracket, and quotation mark in place. Coloured keys: only `"chosen"`, `"rationale"`, and `"confirm_required"` are sunset orange #FF5B2E. Every other token is dark ink #0E0E0E.
>
> Below the JSON block, a thin 1-px ink hairline separator and four small outlined pill buttons in a row, each in Inter Tight 14 pt, no fill, 1-px ink stroke, in this order: "Confirm", "Dismiss", "Edit", "Tell me when not to". The "Confirm" pill is filled with solid ink black and its label in warm off-white — this is the only filled button.
>
> Footer strip pinned at the bottom: a single mono line in JetBrains Mono 12 pt — "local · encrypted · retention 30 days" — at 60% ink opacity, centred. A thin neutral home-indicator line below.
>
> Strict English on every label. Real artefact names appear naturally — RMSSD, MUTE_GROUP_30, BREATHE_478 — never as a stereotype.
>
> Strictly forbidden — must not appear: glassmorphism, frosted glass, dark-mode terminal panels, syntax-highlight rainbow colours, gradient backgrounds, neon glows, drop shadows, glowing brain or neuron motifs, AI hand-of-god illustrations, light-bulb icons, generic robot or chatbot mascots, isometric phones, 3D phones, blue tech-gradient aesthetic, real Apple device chrome, real Galaxy device chrome, manufacturer logos, the words empower, leverage, seamless, revolutionary, paradigm, holistic, robust, cutting-edge, AI-powered, transformative, decorative emojis. The only colour other than ink black on the screen is the three keys plus the trigger card's left-edge accent.
>
> Reference vocabulary: Stripe API documentation pages (the JSON example panes), Linear API reference, Vercel API docs, Apple Human Interface Guidelines reference tables, GitHub Markdown code block on a light theme. The screen should read like a serious developer-facing reference page, not a concept render.
