# Aura — Live 5-Minute Demo Script

**Hardware:** iPhone 15 mirrored to projector via USB-C + QuickTime, MacBook Pro on stage right driving the storm trigger and the slide deck. Apple-only — there is no Galaxy device. This is locked per `plan.md` §21.

**Presenters:** Shaurya (lead, on mic, drives the phone) and Shorya (co-pilot, drives the Mac, fires the storm trigger, reads the trace JSON aloud when needed). The two-person choreography is non-negotiable — the demo loses tempo with one presenter.

**Backup:** `demo/video_90s_storyboard.md` cued and ready in QuickTime, ready to fire if the live demo fails inside 30 seconds.

**Total target:** 5:00. Hard cap: 5:10. We do not run over.

---

## Phase 3 Opening Line — LOCKED (per `plan.md` §21.4)

Shaurya, stage-front, before any tap on the phone. Said exactly once, verbatim:

> *"Aura is platform-agnostic. We built the reference on iPhone because that's the device our college owned, and a two-thousand-rupee total budget didn't stretch to a flagship phone. The architecture you see ports to Galaxy via the API table on slide 4. We never claim numbers we did not measure. Now let me show you what we did measure."*

This goes in the 0:00–0:20 hook block. It is the **first** thing said. There is no version of this demo where it is skipped.

---

## Beat-by-beat

| Time | On-screen | Shaurya (lead) | Shorya (co-pilot) |
|---|---|---|---|
| **0:00–0:20** Hook | Phone shows lock screen, 248 notifs visible. Slide 1 (title) on projector. | (verbatim) "Aura is platform-agnostic. We built the reference on iPhone because that's the device our college owned, and a two-thousand-rupee total budget didn't stretch to a flagship phone. The architecture you see ports to Galaxy via the API table on slide 4. We never claim numbers we did not measure. Now let me show you what we did measure." | Stand stage-right, hands at sides, no movement. Slide deck on slide 1. |
| **0:20–0:35** Frame the day | Phone unlocks, opens Aura. Slide 1 → blank. | "I got 248 notifications yesterday. Most assistants help you see them faster. Aura helped me see four. Here is the morning, on the day this video says it is." | Advance projector to slide 3 (Morning Brief mock). Silent. |
| **0:35–1:20** Morning Brief (Calendar + Comms + Wellness) | Brief card animates in: sleep 5.2 h, 9 am DSA quiz, BMTC ETA → leave 8:15, one Zomato refund. | "Sleep five point two hours from HealthKit. Quiz at nine, slides summarised by Comms. Cab tracking through BMTC, leave by eight fifteen. One tap to confirm the leave-time alert. I did not ask for any of this." (tap accept) | Cue: when Shaurya taps accept, Shorya advances projector to slide 4 (architecture). Watch the timer; if Shaurya is at 1:00, prompt with "Quiet group chat next." |
| **1:20–2:20** Quiet Group Chat | Mac fires WhatsApp storm: 47 messages from a project group in 10 seconds. Phone batches, surfaces 1 card with 3 actionable items, 44 muted. Drawer opens — Reasoning Trace JSON visible. | "47 messages in ten seconds. Aura batched. Three actionable, 44 muted. The drawer is the trace." (tap drawer) "trigger, signals, candidates, ranking, chosen action — all on-device, all glass-box." | Fire the storm script on the Mac at the cue word "the morning, on the day". Read the trace JSON aloud only if Shaurya gestures: `"agent: comms, decision: batch_digest, drivers: volume_47_in_8min, actionable_3, load_score_78."` |
| **2:20–3:20** Closed-Loop Stress | Apple Watch shows HRV trending down. Load Score climbs on the phone. AirPods whisper plays through stage speaker (BT to PA): *"Mute project group 30 min? You're in flow."* Tap accept. Group muted. Trace shows the chain. | "HRV from HealthKit. Typing entropy from the custom keyboard. App-switch rate. Five features, one Load Score. The whisper is on AirPods, not a banner. I tap accept." (taps) "Group muted. Trace open." | Cue projector to slide 5 (the comparison table) in background. Stand by to hand Shaurya the AirPods if the Bluetooth pairing drops; preconfigure with `BT_FORCE_AURA=1` env var on the test build. |
| **3:20–4:20** Spend Mirror | Phone receives a synthetic UPI debit SMS (HDFC, ₹350 Zomato — same one in `datasets/finance/finance_train_synthetic.jsonl`). FinanceAgent classifies and surfaces: today total, vs average, anomaly badge. Open the Gmail receipt for Swiggy — parsed in-line. Projection card: *"At this rate, balance hits zero by 11 May."* | "FinanceAgent reads the SMS body — local regex hot-path plus a Gemma 2B LoRA fallback. Categorised food delivery. Third Swiggy this week, that's the anomaly. The projection is from a 2-layer LSTM trained on sixty days of pilot data. None of these numbers leave the device." | Trigger the synthetic SMS injection from the Mac at the start of this beat. Confirm the projection card renders before Shaurya tells the LSTM line. |
| **4:20–4:50** Memory Graph | Open Memory tab. Show export-to-JSON button. Tap it — file appears in Files app. Tap "delete by time-range", pick last 24 h, confirm dialog. | "User-owned. Exportable. Auditable. One tap to leave with all your data, one tap to delete a window of it. We do not have your data on a server because there is no server." (tap export) "JSON file in the Files app. (tap delete) Time-range delete. Audit log entry. Done." | Advance projector to slide 9 (KPI bars) in background. |
| **4:50–5:00** Close | Phone idles on Aura home. Slide 9 on projector. | "Aura is the only assistant that earns trust by showing why and shutting up. We measured 30 percent effort reduction across 30 users. Raw CSV in the repo. Thank you." | Hold position. Advance to slide 1 (closing card). |

---

## Choreography rules

1. **Two voices, one timeline.** Shaurya is on mic the entire time. Shorya never takes the mic on stage. Shorya speaks only the trace JSON when explicitly cued.
2. **Cue words.** Shorya advances slides only on the literal cue word in the table. Never on sentence-end. Cues are bolded in the rehearsal copy.
3. **No silence longer than 3 seconds.** If the phone hangs, Shaurya keeps narrating: "While that loads — the orchestrator runs Phi-3-mini on-device, never cloud, the latency budget is..."
4. **Apple-only honesty.** The opening line at 0:00–0:20 is the only mention of platform. Do not bring up Galaxy again unless asked. Never demo iOS and call it Galaxy.
5. **The trace is the trust.** Open the Reasoning Trace drawer at least twice. The judges remember the drawer.

---

## Failure modes and live recoveries

| Failure | Inside 30 s? | Action |
|---|---|---|
| iPhone locks during a long pause | yes | Shaurya unlocks via Face ID without breaking sentence; Shorya does not move. |
| WhatsApp storm trigger fails to fire | yes | Shorya pre-records the storm to a local notification queue with `aura-tools storm-replay 47`. Hot-key `Cmd+Shift+1` re-fires. |
| Bluetooth whisper doesn't play through PA | no | Shaurya reads the whisper aloud: *"AirPods would whisper: mute project group 30 minutes, you're in flow."* — phrased as the model would have said it. |
| Phone battery dies | no | Switch to backup video — `demo/video_90s_storyboard.md`. |
| Projector aspect ratio wrong | no | Skip slide deck, deliver entirely on phone mirror. Shorya keeps the deck running on the Mac for backup only. |
| Demo fails inside the first 30 s | yes | Shaurya: *"Live demo just refused to play. We have a 90-second cut — let me show you that instead."* Shorya cues the video. |

---

## Pre-stage checklist (T-30 minutes)

- [ ] iPhone fully charged (≥ 80%), Low Power Mode OFF, Do Not Disturb OFF.
- [ ] Aura test build installed, signed-in, all permissions granted.
- [ ] WhatsApp test group `Thapar-DSA-Project` populated with 47 pre-loaded messages, ready to fire.
- [ ] Synthetic UPI SMS injection test run on the iPhone via the dev menu.
- [ ] Apple Watch on Shaurya's wrist, HRV reading captured 5 minutes before stage time.
- [ ] AirPods paired to the iPhone AND to the stage PA mixer (route via aux out).
- [ ] Mac with deck open at slide 1, slide 4, slide 5, slide 9 cached in tabs.
- [ ] Backup video `90s_aura_demo.mp4` open in QuickTime, paused at frame 1, fullscreen-ready on `Cmd+F`.
- [ ] USB-C → HDMI dongle tested in this exact projector port.
- [ ] Run the dress rehearsal one final time — see `demo/dress_rehearsal_checklist.md`.
