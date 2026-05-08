# Slide 9 Evidence Block — Paste-Ready

Drop this block into the bottom-right zone of slide 9 (the repo +
demo block). All URLs verbatim. The QR encodes the repo URL only.

---

## Block content (paste into slide 9, cols 8–12 zone)

```
Repo
github.com/ShAuRyA-Noodle/Combobulating

Live Demo (synthetic data)
huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin

Deck PDF
deck/phase1_blueprint/build/aura_phase1_blueprint_v1.pdf

Demo video (Phase 2)
[TEAM TO VERIFY: link added once 90s video filmed]

Threat model
docs/threat_model.md

ADR index
docs/decisions/README.md

Plan completion audit
PLAN_COMPLETION_AUDIT.md (root)

README
README.md

Pilot raw CSV (Phase 2)
pilot/analysis/raw/  (publishes with Phase 2 submission)
```

QR code: encodes only `https://github.com/ShAuRyA-Noodle/Combobulating`.
320×320 px in #0E0E0E on #FAF8F5 with a 1 px #FF5B2E border. Position
the URL string above the QR in JetBrains Mono 22 pt.

Below the QR, in 14 pt sans:
> Phase 2 raw CSV publishes here.

---

## QR code generation — local Homebrew flow

Homebrew install:
```
brew install qrencode
```

Generate the slide-9 QR PNG at 1280×1280 px (will downscale cleanly
to the 320×320 px slide cell at 2× density):

```
qrencode \
  -o design/social/qr_repo.png \
  -s 32 \
  -m 2 \
  -l H \
  --foreground=0E0E0E \
  --background=FAF8F5 \
  "https://github.com/ShAuRyA-Noodle/Combobulating"
```

Flag notes
- `-s 32` sets pixel size per QR module; 32 px × ~40 modules ≈ 1280 px.
- `-m 2` sets a quiet zone of 2 modules around the code.
- `-l H` selects the highest error-correction level so the QR survives
  print smudge and projection compression.
- `--foreground` and `--background` lock to the deck palette.

Generate the SVG variant for the slide source asset:

```
qrencode \
  -o design/social/qr_repo.svg \
  -t SVG \
  -m 2 \
  -l H \
  --foreground=0E0E0E \
  --background=FAF8F5 \
  "https://github.com/ShAuRyA-Noodle/Combobulating"
```

Then re-style in Figma per `deck_spec.md` §3 row 17:
- Set the 1 px #FF5B2E border rule around the QR cell.
- Mask the QR with a 4 px corner radius.
- Drop into the slide-9 cols 8–12 zone at 320×320 px.

Verify the QR by scanning with an iPhone Camera app from 2 m away on
a 1080p projection. The repo URL must resolve in one tap.

---

## Demo video placeholder

Until `deck/phase3_pitch/demo.mp4` exists, slide 9 carries this
caption beneath the demo line:

> Phase 2 deliverable. 90 s. Captioned. Recorded on iPhone (iOS
> reference build) and Android emulator (Galaxy port). Raw footage
> at deck/phase3_pitch/raw/.

Replace with the raw GitHub URL once committed.

---

## Citations on slide 9 footer

KPI targets all from the EnnovateX 2026 problem brief.
Methodology from `plan.md` §22 and §23.
Pew, WHO, Kantar for context — see `docs/references.md`.

Phase 1 freeze: all KPI bars dashed at submission. Tag
`[TEAM TO VERIFY any baseline measured before deck freeze]` until a
baseline is logged.
