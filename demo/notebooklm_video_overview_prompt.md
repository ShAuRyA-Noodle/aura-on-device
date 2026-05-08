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

### Step 3 — Paste this focus prompt verbatim

```
This is a 90-second demo video for Samsung EnnovateX 2026 Phase 1
submission. Total spoken word count target: 215 to 235 words. Default
narration cadence is around 2.4 words per second; do not exceed it.
Cut anything that pushes the runtime past 90 seconds.

Open with the locked micro-story exactly as written in the source
"OPENING MICRO-STORY — DO NOT REPHRASE". Do not paraphrase the first
two sentences. Speak them as the cold open.

Then move directly into three demo beats, in this exact order, each
beat exactly 20 seconds spoken:

Beat 1 (0:18 to 0:38) — Morning Brief.
Show the Morning Brief screen. Name three things on it: sleep five-
point-two hours pushed gym to evening, nine AM DSA quiz with the
professor's slides already summarised, leave-by alert at eight
fifteen. State that none of these were asked for. Aura anticipated
all three.

Beat 2 (0:38 to 0:58) — Quiet Group Chat plus Reasoning Trace.
Show the WhatsApp project group flooding with 137 messages in twelve
minutes. Aura batches them. Three actionable surface, 134 muted. Then
open the Reasoning Trace drawer. Read aloud the JSON keys: chosen,
rationale, confirm-required. Say one short line: every action shows
its work.

Beat 3 (0:58 to 1:18) — Spend Mirror plus Silence Budget.
Show the Spend Mirror card. Name HDFC bank, name Zomato, name the
rupee figure ₹2,400 over weekly average. State that this came from
SMS parsed on the device. Then show the Silence Budget meter at two
of three surfaces remaining today. State that Aura caps proactive
nudges at three a day.

Close 1:18 to 1:30 — twelve-second wrap.
State three closing facts with no embellishment. One: zero bytes
left the device. Two: the entire memory graph is exportable to JSON
in one tap with a tamper-evident audit log. Three: this was built by
a two-person team at Thapar Institute on a two-thousand-rupee total
budget. End with the locked tagline spoken at normal cadence:
Anticipate. Act. Stay quiet.

Visual rules — strict.
Use only the loaded screen mockups and the architecture diagram as
visuals. Do not generate stock-photo overlays of phones in hands,
glowing brains, neural networks, isometric devices in space, or
gradient blobs. Backgrounds throughout must be a warm off-white. The
single accent colour permitted is sunset orange. No neon, no
glassmorphism, no drop shadows, no glow.

Voice rules — strict.
Use one narrator. No two-host podcast back-and-forth. Tone is
confident, observational, dry, slightly self-aware — like a smart
21-year-old engineer, not a brand. Do not use these words: empower,
leverage, seamless, revolutionary, paradigm, holistic, robust,
cutting-edge, AI-powered, transformative, game-changing, harness,
synergy.

Indian context rule.
Name real artefacts only — UPI, IRCTC, BMTC, HDFC, Zomato, Swiggy,
Blinkit, WhatsApp, Gmail. Do not use stereotypes about Indian
college life, festivals, food, or family. The hostel and the project
group and the prof and the DBMS quiz are the texture.

Hard exclusions.
Do not show or claim a Galaxy device. The team did not buy one — say
so explicitly only if the visual budget allows it; otherwise stay
silent on the platform. Do not show or claim Apple chrome or Galaxy
chrome on any phone screen — frames must read as neutral line-art.
Do not invent KPI numbers. The Phase 2 user study has not run yet.

Caption rule.
Burn legible captions at 24 pt minimum on every spoken line. The
video must be watchable without sound on a phone screen at 50%
volume in a noisy room.
```

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
