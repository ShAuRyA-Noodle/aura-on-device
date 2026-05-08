# NotebookLM Video Overview — 90-Second Demo Prompt

This document gives the team a paste-ready focus prompt for generating
the Aura Phase 1 / Phase 3 demo video using NotebookLM's
**Video Overview** feature (Studio panel → Video Overview → Customize).

---

## How to use this file

### Step 1 — Load these sources into a fresh NotebookLM notebook

Upload or paste, in this order. Each source goes into a separate
NotebookLM source slot.

1. `aura/deck/phase1_blueprint/deck.md` (the master 11-slide deck)
2. `aura/demo/live_5min_script.md` (the locked stage script)
3. `aura/demo/video_90s_storyboard.md` (the locked shot list)
4. `aura/_trust/site_copy.md` (the public landing copy with the wedges)
5. `aura/design/screens/01_morning_brief.md`
6. `aura/design/screens/02_reasoning_trace_drawer.md`
7. `aura/design/screens/05_quiet_group_chat.md`
8. `aura/design/screens/06_load_score_panel.md`
9. `aura/design/architecture/aura_architecture.svg` (architecture image — upload as image source so NotebookLM picks it up visually)
10. `aura/_trust/risk_recovery_brief.md` (so the model knows what we don't claim)
11. The opening micro-story from `plan.md` §1.1 (paste as a text source titled "OPENING MICRO-STORY — DO NOT REPHRASE").

### Step 2 — Pick the Video Overview tone

In NotebookLM Studio panel, choose **Brief** preset, then click **Customize**.

### Step 3 — Paste a focus prompt

NotebookLM's Customize field has a character cap that varies by
account. Three variants below in increasing length. Try B first; if
your account rejects it as too long, fall back to A. C is for
accounts that allow longer custom instructions.

#### Variant A — 250 characters (works on every account)

```
90-sec demo. 220 words, one narrator, Gen Z dry voice. Open verbatim from "MICRO-STORY" source. 3 beats x 20s: Morning Brief, Quiet Group Chat with Reasoning Trace JSON, Spend Mirror. Close 12s: zero cloud bytes, two-person ₹2,000 budget. Tagline "Anticipate. Act. Stay quiet."
```

#### Variant B — 500 characters (recommended)

```
90-sec demo for Samsung EnnovateX 2026. 220 spoken words, single narrator, Gen Z dry voice. Open verbatim from "MICRO-STORY" source. 3 beats x 20s: Morning Brief (5.2h sleep, 9am DSA quiz, leave 8:15); Quiet Group (137 msgs->3 actionable, Reasoning Trace JSON); Spend Mirror (HDFC ₹2,400 over, Silence Budget 2/3). 12s close: zero cloud bytes, exportable memory, two-person Thapar ₹2,000 budget. Tagline: "Anticipate. Act. Stay quiet." Off-white bg, sunset-orange accent only. No stock photos, no phone chrome.
```

#### Variant C — 800 characters (only if accepted)

```
90-second demo for Samsung EnnovateX 2026 Phase 1. Target 220 spoken words, single narrator, confident Gen Z dry voice (not brand voice). Open verbatim from source titled "MICRO-STORY" — first two sentences spoken word-for-word as cold open. Then three 20-second beats in this order: Beat 1 Morning Brief — sleep 5.2h, 9am DSA quiz, professor's slides summarised, leave by 8:15, three friends going. Beat 2 Quiet Group Chat — WhatsApp project group 137 messages in 12 minutes, Aura batches to 3 actionable + 134 muted, then open Reasoning Trace JSON drawer showing chosen/rationale/confirm_required keys. Beat 3 Spend Mirror — HDFC SMS parsed, ₹2,400 over weekly average, Silence Budget meter at 2/3 today. 12-second close: zero bytes left device, exportable memory graph with audit log, built by two-person Thapar team on ₹2,000 budget. End tagline at normal cadence: "Anticipate. Act. Stay quiet." Off-white background only. Single sunset-orange accent. No stock photos, no Apple chrome, no Galaxy chrome, no glowing brain. Banned words: empower, leverage, seamless, revolutionary, AI-powered, transformative.
```

#### Why three variants

NotebookLM's Customize field cap is not documented and varies by
account tier. The full original prompt at the bottom of this file
(~3,200 chars) does not fit the standard cap. Variant A always
works. Variant B is the sweet spot for most accounts. Variant C
captures more of the locked rules but only fits accounts with the
extended Studio cap.

The locked rules NotebookLM cannot infer from sources alone:
*single narrator, 90 seconds, micro-story verbatim, no Galaxy chrome*.
All three variants enforce these. The shorter variants drop only
the elaborated explanations.

### Step 4 — Generate

Click **Generate**. Initial render takes about 4 to 8 minutes on the
NotebookLM free tier. If the runtime exceeds 100 seconds on the first
attempt, regenerate with the line "STRICTLY 90 SECONDS — TRIM ANY
SCENE THAT PUSHES PAST IT" appended at the very top of the prompt.

### Step 5 — Post-processing checklist

- [ ] Total length 80 to 95 seconds (90s target window).
- [ ] Cold open uses the micro-story verbatim, not paraphrased.
- [ ] Three demo beats appear in the locked order.
- [ ] Reasoning Trace JSON is visible and legible at full resolution.
- [ ] Closing tagline "Anticipate. Act. Stay quiet." spoken cleanly.
- [ ] Captions on every spoken line, ≥24 pt.
- [ ] No banned words audible or visible.
- [ ] No banned visuals (stock photos, brain graphics, gradient blobs).
- [ ] Single sunset-orange accent only.

If any item fails, edit the focus prompt to address that specific
fail (NotebookLM responds well to "do not include X" amendments) and
regenerate.

### Step 6 — Export and place

NotebookLM exports as MP4. Save to `aura/demo/aura_90s_demo_v{N}.mp4`
and bump `{N}` per regeneration. Reference the latest as the primary
backup video for Phase 3 stage demo, per
`aura/demo/fallback_plan.md` Tier 2.

---

## Why this prompt is shaped this way

NotebookLM Video Overview default outputs are 5 to 15 minutes long
with two-host podcast voice. A 90-second demo video requires three
explicit constraints up front that the model otherwise ignores:

1. **Word count target.** 215-235 words. NotebookLM's narration
   cadence is approximately 2.4 wps; this lands inside the 90-second
   window with a small buffer.
2. **Single narrator.** Without this rule the model defaults to a
   two-host conversation, which burns 30-45 seconds on host banter
   that has no role in a demo cut.
3. **Locked micro-story verbatim.** The 11:48pm hook is the team's
   strongest opening; paraphrasing dilutes it. The "DO NOT REPHRASE"
   token in the source name is read by the model as a constraint.

Each beat is 20 seconds because NotebookLM struggles to compress
demo flows below that without dropping artefacts. 20-second beats
fit one screen mockup plus one spoken claim plus one named artefact.

The closing is exactly 12 seconds because the tagline "Anticipate.
Act. Stay quiet." spoken at natural pace is around 2 seconds; 10
seconds of preceding wrap fits three short claims (zero bytes, owned
memory graph, two-person budget).

The "do not show Galaxy chrome" rule is critical. Without it,
NotebookLM's image search will pull stock Galaxy phones, which
contradicts the honest framing in `docs/decisions/ADR-0006-platform-strategy.md`.

---

## Variant — Phase 3 finals 7-minute pitch video

If the team also wants a longer Phase 3 video for the finals pitch
deck, swap the constraints above as follows:

- Word count: 1,400 to 1,600 words.
- Beats: full 14-slide structure from `aura/deck/phase3_pitch/spec.md`.
- Tone: keep single-narrator, but allow micro-stories per persona
  (Aanya, Rohan, Kabir, Mira) in the wedge sections.
- Length: aim 6:30 to 7:00 minutes.

Save the longer version to `aura/demo/aura_phase3_pitch_video_v{N}.mp4`.

---

## What this prompt is not

- It is not a script for a human to read aloud. It is a focus prompt
  that instructs NotebookLM what to do and what not to do. The actual
  spoken words come from NotebookLM synthesising the loaded sources
  under these constraints.
- It is not a substitute for a human-edited cut. After NotebookLM
  exports the MP4, the team should review against the post-processing
  checklist and re-prompt if any item fails. Two regenerations is
  normal.
- It is not the live stage demo. The live stage demo is `aura/demo/live_5min_script.md`
  and uses an iPhone, not the NotebookLM video. The NotebookLM video
  is the venue-fallback Tier-2 backup per `aura/demo/fallback_plan.md`.

---

## File location

This file lives at `aura/demo/notebooklm_video_overview_prompt.md` and
ships with the repo. Update on every locked-context change; bump a
version line below.

| Version | Date | Change |
|---|---|---|
| v1 | 2026-05-08 | Initial prompt for 90-second demo. |
