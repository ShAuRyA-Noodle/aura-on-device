# Aura — Recording Setup

The 90-second backup video and any social cuts (twitter / linkedin / leave-behind QR landing) come from the same setup. This file is the recipe so anyone on the team can re-shoot a clean take.

## Hardware

| Item | Spec | Notes |
|---|---|---|
| iPhone 15 Pro | Cinematic mode OFF, 4K @ 30 fps | Both face cam **and** screen capture run on this device. We do not introduce a second camera body — fewer moving parts. |
| Lavalier microphone | Boya BY-M1 (3.5 mm) → iPhone via Lightning/USB-C → 3.5 mm dongle, OR Rode Wireless ME if available | Clip on the third button. Levels at -12 dBFS peak in QuickTime. |
| Reflector | 80 cm 5-in-1, silver side facing talent | Camera-left, ~1.2 m from talent, fills the off-side. |
| Window | Single north-facing window, talent angled 30° to it | Soft natural light. Shoot between 10 am and 2 pm only. |
| Tripod | Phone tripod with Bluetooth shutter | Phone in landscape. Lens at talent's eye height. |
| Mac | MacBook Pro M1+ | Used only for screen-mirroring during shot 4 (group chat storm) and for editing. |
| Cable | USB-C → USB-C (Mac to iPhone) | For screen mirror via QuickTime — see below. |

We do NOT use a second-camera face cam in the final cut. The brief asks for one on-screen presenter (deck §9.1). If a B-cam is wanted for behind-the-scenes social, shoot on a second iPhone or any DSLR you have — we do not buy one.

## Audio

- Lavalier mic only. No on-board iPhone mic for the final cut.
- Record 30 s of room tone before talent rolls. Used as the bed under shot 1 (the title card).
- Loudness target: -16 LUFS integrated (the YouTube / X spec).
- No music bed.

## Lighting

- Single window + reflector. That is the entire kit.
- Talent T-shirt is solid neutral, no logos, no orange (the orange must come from the prop notebook). White-balance to 5500 K manually in the iPhone Pro app or fix in DaVinci.

## Screen mirror via QuickTime

For shots 3, 4, 5, 6 (phone-screen captures) we use QuickTime's iPhone movie-recording feature, not third-party software:

1. Connect the iPhone to the Mac with a USB-C cable.
2. On the Mac, open **QuickTime Player → File → New Movie Recording**.
3. Click the small arrow next to the record button. Under **Camera**, select the iPhone. Under **Microphone**, select the iPhone.
4. The iPhone's screen now appears in the QuickTime window in real time. Tap the red record button when ready.
5. Export at **1080p H.264**, 30 fps.

Tested on macOS Sequoia + iOS 17. No additional drivers, no purchases, no third-party app.

## Edit pipeline

- **iMovie** (free, default) — sufficient for the 90 s cut. Use for first pass.
- **DaVinci Resolve** (free) — used if we need finer colour control. Drop the iMovie XML into Resolve via FCPXML export.
- **No paid tooling.** Premiere, Final Cut, Capcut Pro — none of these are required, and we do not pay.

## Final export specs

| Field | Value |
|---|---|
| Container | MP4 |
| Video codec | H.264 (High profile, level 4.1) |
| Resolution | 1920×1080 |
| Frame rate | 30 fps (constant) |
| Bitrate | 8 Mbps target, 12 Mbps max |
| Audio codec | AAC LC stereo |
| Audio bitrate | 192 kbps |
| Loudness | -16 LUFS integrated |
| Captions | Burned-in `.srt` at 30 pt Inter Tight, 80% white, 1 px shadow |
| File size | ≤ 100 MB so it embeds cleanly in the Phase 1 portal |

Export filename convention: `90s_aura_demo_v{N}.mp4` where `N` is the take number. Keep the last 3 takes; delete older.

## Storage

Final cuts and source rushes go to `aura/demo/exports/` (gitignored). Source rushes are the largest files — keep them on the team's Google Drive folder rather than in the repo.

## Re-shoot trigger list

Re-shoot if any of these are true:

- [ ] Audio peaks above -3 dBFS at any point.
- [ ] Background reveals a person, a window with bright sky, or a logo we don't own.
- [ ] Any phone-screen capture shows real names, real phone numbers, or real account numbers (these must come from the synthetic JSONLs).
- [ ] Run-time deviates from 1:30 by more than ±2 s.
- [ ] Captions wrap to 3+ lines on any single shot.
