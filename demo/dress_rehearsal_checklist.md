# Aura — Dress Rehearsal Checklist

Three full dry runs before stage day. No exceptions.

| Run | When | Goal |
|---|---|---|
| Run 1 | T-7 days, in Shaurya's room | Get through the whole 5 minutes once without stopping. Identify the longest stalls. |
| Run 2 | T-3 days, in a Thapar lecture theatre we can borrow | Real projector, real audio cable, real distance from the audience. Time everything to the second. |
| Run 3 | T-1 day, on-site at Taj Yeshwanthpur | Final config-lock. After this, no script changes. |

## What to time

Run a stopwatch on Shorya's Mac (open a tab to `time.is`). Note these timestamps every run:

| Beat | Target | Run 1 | Run 2 | Run 3 |
|---|---|---|---|---|
| Opening line ends | 0:20 |  |  |  |
| Morning Brief tap | 1:20 |  |  |  |
| Storm fires | 1:25 |  |  |  |
| Trace drawer opens | 1:50 |  |  |  |
| Whisper plays | 2:50 |  |  |  |
| Spend Mirror SMS | 3:25 |  |  |  |
| Memory tab opens | 4:25 |  |  |  |
| Closing line ends | 5:00 |  |  |  |

After each run, Shorya types the four numbers into the table above and we compare drift across runs.

## Fix-list between runs

After every run, force a 10-minute postmortem with this template:

```
Beat:
What broke / felt wrong:
Fix (concrete, in <50 words):
Owner:
Verified in next run? Y/N
```

A run is not "complete" until the postmortem is filled in.

## Kill switches

Conditions under which we stop the live demo and cut to the 90-second backup video instantly. Shaurya makes the call; Shorya executes.

| Trigger | Kill action |
|---|---|
| Phone fails to unlock within 5 s of stage start | Cut. Shaurya: *"Live demo just refused. Watch the 90-second cut instead."* |
| Storm trigger fails to fire on first attempt | Try once more. If still nothing, cut. |
| Bluetooth whisper does not route to PA | Do NOT cut. Shaurya reads the whisper aloud as the model would have said it. |
| Projector loses signal mid-demo | Do NOT cut. Continue on phone-screen-up to the audience. Shorya power-cycles HDMI in the background. |
| Wi-Fi drops on the venue network | No effect. Aura is fully offline by design. |
| Internet drops on Mac (deck only) | Use the offline PDF backup of the deck on the Mac desktop. |
| Battery on iPhone < 30% at T-5 minutes | Plug iPhone into the Mac via USB-C — it charges + screen-mirrors at the same time. |
| Battery on iPhone < 15% at any point during demo | Cut. Switch to backup video. |

## Pre-stage gate (T-30 minutes)

This is the same list as in `live_5min_script.md`, repeated here so you only carry one checklist on the day.

- [ ] iPhone fully charged (≥ 80%), Low Power Mode OFF, Do Not Disturb OFF.
- [ ] Aura test build installed, signed-in, all permissions granted.
- [ ] WhatsApp test group `Thapar-DSA-Project` populated with 47 pre-loaded messages.
- [ ] Synthetic UPI SMS injection test run on the iPhone via the dev menu.
- [ ] Apple Watch on Shaurya's wrist, HRV reading captured 5 minutes before stage time.
- [ ] AirPods paired to the iPhone AND to the stage PA mixer (route via aux out).
- [ ] Mac with deck open at slide 1, slide 4, slide 5, slide 9 cached in tabs.
- [ ] Backup video `90s_aura_demo.mp4` open in QuickTime, paused at frame 1, fullscreen-ready on `Cmd+F`.
- [ ] USB-C → HDMI dongle tested in this exact projector port.
- [ ] Stopwatch ready on the Mac (`time.is`).
- [ ] Phones in airplane mode for the demo network is NOT required — Aura is offline either way; we keep airplane mode off so the AirPods stay paired through normal Bluetooth.
- [ ] Phone is in **Silent** but **NOT** Do Not Disturb (we want notifications to render, just not chime).

## Day-of emotional kit

- Water bottle each, before stage.
- Two printed copies of `qa_anticipated.md`.
- One printed copy of this checklist.
- One spare USB-C → HDMI dongle in Shorya's bag.
- One spare lightning / USB-C cable for charging.
- One spare AirPods case, charged.

We do not bring a backup iPhone. We bring the backup *video*.
