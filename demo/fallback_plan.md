# Phase-3 stage fallback matrix

The Phase-3 finals are venue-dependent and we cannot trust any single demo
surface. This document is the **runbook** the operator follows from the
moment the prior team hands the stage off. Practice every tier in dress
rehearsal — not just the preferred one.

> **Locked context.** Aura is on-device, no cloud egress for personal data.
> Every fallback below uses synthetic data only. The venue is *not* getting
> our pilot users' logs.

## Tier matrix

| Tier | What it is | When to use | Setup time on stage | Internet needed |
|:----:|------------|-------------|--------------------:|:---------------:|
| 1 | Live iPhone demo | Default. iPhone is on, paired, brief card opens within 10s of `Hey Aura, brief me` | <10 s | No |
| 2 | Pre-recorded 90 s video | iPhone misbehaves (stuck on splash, watch unpaired, dock mirror fails) | <30 s | No |
| 3 | Local FastAPI + browser on Mac | iPhone *and* video both fail | 30–45 s | **No** |
| 4 | HuggingFace Space (Gradio) | Mac dies, but venue Wi-Fi is up | ~20 s + page load | **Yes** |
| 5 | Deck-only walkthrough | All hardware fails | Instant | No |

## Tier 1 — live iPhone (preferred)

Operator: Aarav. Backup: Riya.

1. Phone on stage table, screen up, brightness 100%, do-not-disturb OFF.
2. Apple Watch on the operator's wrist, paired, watch face = Aura modular.
3. Lightning -> HDMI dock pre-connected to the venue projector (test in
   afternoon rehearsal).
4. Voice: `Hey Aura, brief me`. Card materialises. Open Reasoning Trace.
5. Tap: Mute Group, Breathe, Spend Mirror.
6. Time budget: 4:30 of the 5-minute slot.

**Failure cues**: card takes >5 s, Reasoning Trace empty, watch shows the
old face. Switch to Tier 2.

## Tier 2 — pre-recorded video

Operator: Riya. Backup: anyone.

1. Open the local copy at `aura/demo/recording_setup.md` -> the produced
   `aura_90s_v3.mp4` (we re-cut after each rehearsal).
2. Play in QuickTime, full-screen, no system audio chime (mute Mac speakers,
   plug into venue 3.5mm).
3. Narrate live over the video — the script is in
   `aura/demo/live_5min_script.md`.

**Failure cues**: file missing, projector AVI rejection, audio drift. Switch
to Tier 3.

## Tier 3 — local FastAPI + React on Mac (venue-independent, no internet)

Operator: Riya. Backup: Aarav.

1. Open Terminal on the team's MacBook.
2. ```bash
   cd "/Users/shauryapunj/Desktop/Samsung Hack/aura"
   bash web/run_local.sh
   ```
3. Browser auto-opens `http://localhost:8080/index.html`.
4. Click through tabs in order:
   - Morning Brief — slide RMSSD down, watch the card switch.
   - Quiet Group Chat — paste the canned 50-line group chat.
   - Spend Mirror — paste the canned 4-bank UPI SMS blob.
   - Load Score — slide HRV down, watch the intervention switch from
     `DO_NOTHING` to `BREATHE_478`.

**Pre-stage check** (must run during dress rehearsal):

- [ ] `web/web/vendor/*.js` exists (`ls web/web/vendor/*.js`).
- [ ] FastAPI deps installed (`python3 -c "import fastapi, uvicorn"`).
- [ ] Wi-Fi *off* — confirm the demo still boots.
- [ ] HDMI mirror tested at 1920x1080.

**Failure cues**: pip can't resolve, port 8000/8080 already in use, browser
extension blocks localhost. Switch to Tier 4.

## Tier 4 — HuggingFace Space

Operator: Aarav. Backup: Sid.

1. Open Safari (avoids Chrome extension surprises).
2. Navigate to `https://huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin`.
3. Wait for the Space to wake (cold start ~25 s on free CPU tier).
4. Click through the same 5 tabs as Tier 3, plus the Memory Graph tab.

**Required for this tier**: venue Wi-Fi must be working *and* not blocking
HuggingFace. We do **not** rely on this being available.

**Failure cues**: 503 on the Space, captive portal interception, projector
fails to render Gradio dark-on-light contrast. Switch to Tier 5.

## Tier 5 — deck only

Last resort. The deck (`aura/deck/`) is self-contained: every screenshot in
the slides is captured from a working build. Walk slides 4–11 in narration
mode, point at the static screenshots, take the questions.

## Dress-rehearsal protocol

The night before the finals, run **every** tier end-to-end on the venue
stack:

1. 19:00 — Tier 1 walkthrough on stage with venue projector.
2. 19:30 — kill the iPhone Wi-Fi, switch to Tier 2 on the same projector.
3. 19:45 — turn off venue Wi-Fi at the panel, switch to Tier 3.
4. 20:00 — turn Wi-Fi back on but wipe the team Mac's cache, switch to Tier 4.
5. 20:15 — hand the laptop to a teammate and run the slide-only Tier 5 in 90 s.

If any tier takes >60 s to recover from the prior tier's failure, **drop the
slowest tier** and rehearse the gap.

## Operator tools

- `aura/demo/dress_rehearsal_checklist.md` — line-item gate.
- `aura/demo/recording_setup.md` — recording protocol for Tier 2.
- `aura/demo/live_5min_script.md` — narration timing.
- `aura/demo/qa_anticipated.md` — judge questions + canned answers.
