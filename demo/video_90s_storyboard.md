# Aura — 90-Second Backup Video Storyboard

**Mirror of `deck_spec.md` §9.1 with production detail.** This is the cut that fires if the live demo fails. It must hold up on its own as a Phase 1 walkthrough video.

**Format:** 1080p (1920×1080), 30 fps, H.264, AAC stereo audio. Closed captions burned in (the EnnovateX video panel may watch on mute).

**Talent:** Shaurya on camera, mid-shot, warm off-white wall behind. One sunset-orange object in frame (a notebook on the desk) anchors the colour identity.

**Audio:** Lavalier mic on Shaurya, soft tap SFX over phone-screen captures, a single chat-ping fade in shot 4. No music bed.

**Recorded on:** iPhone 15 Pro for both face cam and screen capture. iMovie or DaVinci Resolve (free) for edit. No paid software.

---

## Shot list

| # | Time | Shot | Description | On-screen text | Audio (Shaurya VO) |
|---|---|---|---|---|---|
| 1 | 0:00–0:08 | Static title | "Aura · Anticipate. Act. Stay quiet." in Fraunces 96 pt on `#FAF8F5`. Hand-drawn orange underline animates left → right over 1.5 s. | "Aura — Phase 1 Blueprint" | silence + ambient room tone |
| 2 | 0:08–0:18 | Talking head, mid-shot | Shaurya, eyes to lens, off-white wall, single orange object in lower-right corner of frame. | callout: "137 → 1" appears at 0:14 | "Eleven-forty-eight on a Tuesday. 137 messages in twelve minutes. None about the assignment due at nine. Aura would have surfaced the one that mattered." |
| 3 | 0:18–0:35 | Phone-screen capture composited over right two-thirds | Slow scroll over Morning Brief card — sleep 5.2 h, DSA quiz 9 am, BMTC ETA, leave 8:15. One-tap accept on the leave-time alert. | callout: "anticipate" | "Sleep from HealthKit. Calendar. BMTC ETA. Leave at eight fifteen. One tap. The user did not ask for any of this." Soft tap SFX on the accept tap. |
| 4 | 0:35–0:55 | Phone capture (Quiet Group Chat) | WhatsApp `Thapar-DSA-Project` lights up with 47 messages in 4 seconds (sped 2×). Aura batches; one card surfaces with 3 actionable items, 44 muted. Drawer slides up — Reasoning Trace JSON visible (`agent: comms, decision: batch_digest, drivers: ...`). | callout: "act + glass box" | "Forty-seven messages. Three actionable. Forty-four muted. The drawer is the Reasoning Trace. Glass box, on-device." Chat ping fade for the first 1 s, then silenced. |
| 5 | 0:55–1:15 | Composite: Apple Watch on left third + phone on right two-thirds | Watch HRV trend climbs; Load Score rises on the phone. AirPods whisper plays through the recording: *"Mute project group 30 min? You're in flow."* Tap accept. Group muted. Trace fragment appears. | callout: "closed loop" | "HRV. Typing entropy. App-switch rate. The whisper is on the AirPods, never a banner. I tap accept. Group muted." Watch haptic SFX on the tap. |
| 6 | 1:15–1:25 | Phone capture (Memory tab) | Tap **Export to JSON**. JSON file appears in Files app. Tap **Delete by time-range** — last 24 h. Confirm. Audit log row animates in. | callout: "your data" | "User-owned. Exportable. Auditable. One tap out, one tap to forget a day." |
| 7 | 1:25–1:30 | Static end card | Same as title card, with QR code to repo bottom-right. | "github.com/ShAuRyA-Noodle/Combobulating" + QR | silence |

Total: 1:30 exactly.

---

## Production checklist

- [ ] Storyboard frames sketched at A6 in pencil with orange annotations for motion (owner: Shorya).
- [ ] Shoot day end of Week 7 (matches `plan.md` §24, week 11 final cut).
- [ ] Shooting location: Shaurya's room, north-facing window, single reflector at camera-left to fill the off-side.
- [ ] Wardrobe: solid neutral T-shirt, no logos, no patterns, no orange (the orange must come from the prop notebook only).
- [ ] B-roll captured: 5 seconds of Apple Watch face on the wrist, 5 seconds of AirPods being inserted, 10 seconds of finger-on-glass scrolling for cutaway.
- [ ] Audio: lav mic clipped at the third button. Levels checked at -12 dBFS peak. Room-tone capture: 30 s before talent rolls.
- [ ] Captions: written in advance, exported as `.srt`, burned in at 30 pt Inter Tight, 80% white, 1 px shadow.
- [ ] Final export: 1080p H.264, 8 Mbps target bitrate, AAC 192 kbps audio. File ≤ 100 MB so it embeds cleanly into the Phase 1 portal.

## Edit guidelines (DaVinci Resolve / iMovie)

1. Lay the talking-head shots on V1 with the screen captures composited at 60–70% width on V2 with 16 px corner radius and a 1 px `#0A0A0B` stroke.
2. Captions on V3, never overlap the phone screen.
3. Cuts on the beat of Shaurya's last syllable in each shot. No fades except shot 7's final 0.3 s dip-to-card.
4. Colour: warm 5500K, slight orange lift in shadows to match the brand palette. No LUT.
5. Loudness: -16 LUFS integrated.

## Post-production deliverables

- `90s_aura_demo.mp4` — final cut.
- `90s_aura_demo.srt` — sidecar captions.
- `90s_aura_demo_thumbnail.png` — frame at 0:08, used as the EnnovateX submission thumbnail.

All three live next to this storyboard at `aura/demo/exports/` (gitignored).
