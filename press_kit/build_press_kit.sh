#!/usr/bin/env bash
# build_press_kit.sh — assemble aura_press_kit.zip for press, sponsors, and partners.
#
# Run from the repository root or from `aura/`. The script resolves paths
# relative to its own location, so it does not matter which directory you
# call it from.
#
# Output: press_kit/aura_press_kit.zip
# Contents:
#   - brand_identity_board.png
#   - hero_01_morning_brief.png
#   - hero_02_reasoning_trace.png
#   - hero_03_spend_mirror.png
#   - hero_04_load_score.png
#   - team_portrait.png
#   - leave_behind_a4.png
#   - founders_bio.md
#   - one_paragraph_about.md
#   - elevator_60s.md
#   - fact_sheet.md
#   - phase1_deck.pdf (placeholder if not built)
#   - screencast.txt (placeholder pointer)
#   - README.txt (kit manifest)

set -euo pipefail

# Resolve script directory and aura root.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AURA_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
KIT_DIR="${SCRIPT_DIR}"
STAGING="${KIT_DIR}/_staging"
ZIP_OUT="${KIT_DIR}/aura_press_kit.zip"

IMG_DIR="${AURA_ROOT}/img"
TRUST_PRESS_DIR="${AURA_ROOT}/_trust/press_kit"
DECK_PDF="${AURA_ROOT}/deck/phase1_blueprint/build/aura_phase1_blueprint_v1.pdf"
ELEVATOR="${AURA_ROOT}/deck/phase1_blueprint/elevator_60s.md"

echo "==> Aura press-kit builder"
echo "    aura root : ${AURA_ROOT}"
echo "    kit dir   : ${KIT_DIR}"

# Clean and recreate the staging area.
rm -rf "${STAGING}"
mkdir -p "${STAGING}"

# 1. Brand identity board.
cp "${IMG_DIR}/aura_01_brand_identity_board.png" "${STAGING}/brand_identity_board.png"

# 2. Four hero screenshots.
cp "${IMG_DIR}/aura_02_screen_morning_brief.png"          "${STAGING}/hero_01_morning_brief.png"
cp "${IMG_DIR}/aura_03_screen_reasoning_trace_drawer.png" "${STAGING}/hero_02_reasoning_trace.png"
cp "${IMG_DIR}/aura_05_screen_spend_mirror.png"           "${STAGING}/hero_03_spend_mirror.png"
cp "${IMG_DIR}/aura_07_screen_load_score_panel.png"       "${STAGING}/hero_04_load_score.png"

# 3. Team portrait + leave-behind A4 handout.
cp "${IMG_DIR}/aura_22_press_kit_team_portrait.png" "${STAGING}/team_portrait.png"
cp "${IMG_DIR}/aura_17_leave_behind_a4.png"         "${STAGING}/leave_behind_a4.png"

# 4. Founder bios + one-paragraph about.
cp "${TRUST_PRESS_DIR}/founders_bio.md"        "${STAGING}/founders_bio.md"
cp "${TRUST_PRESS_DIR}/one_paragraph_about.md" "${STAGING}/one_paragraph_about.md"

# 5. 60-second elevator script (if present).
if [[ -f "${ELEVATOR}" ]]; then
  cp "${ELEVATOR}" "${STAGING}/elevator_60s.md"
else
  cat > "${STAGING}/elevator_60s.md" <<'EOF'
# 60-second elevator — placeholder

Source script lives at deck/phase1_blueprint/elevator_60s.md.
Regenerate the press kit after the deck build to ship the real script.
EOF
fi

# 6. Fact sheet.
cp "${KIT_DIR}/fact_sheet.md" "${STAGING}/fact_sheet.md"

# 7. Deck PDF — copy if it has been built, otherwise drop a pointer.
if [[ -f "${DECK_PDF}" ]]; then
  cp "${DECK_PDF}" "${STAGING}/phase1_deck.pdf"
else
  cat > "${STAGING}/phase1_deck.pdf.txt" <<EOF
Phase 1 deck PDF not yet built.
Build it from deck/phase1_blueprint/, then re-run build_press_kit.sh.
EOF
fi

# 8. Screencast placeholder.
cat > "${STAGING}/screencast.txt" <<'EOF'
Screencast placeholder.

The 90-second product screencast will live at:
  https://shaurya-noodle.github.io/Combobulating/screencast.mp4

It is recorded against the Wizard-of-Oz pilot rig on iPhone 13 (iOS 17),
following the storyboard in demo/storyboard_90s.md.

Until the recording is finalised, point press queries at the live Gradio
demo: https://huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin
EOF

# 9. Manifest / README inside the kit.
cat > "${STAGING}/README.txt" <<EOF
Aura — Press Kit
================

Galaxy Brain — Shaurya Punj, Shorya Gupta.
Thapar Institute of Engineering and Technology, Patiala.
Samsung EnnovateX 2026. v1.0.0.

Contents
--------
brand_identity_board.png   Hero brand-identity board.
hero_01_morning_brief.png  Morning Brief screen.
hero_02_reasoning_trace.png Reasoning Trace drawer.
hero_03_spend_mirror.png   Spend Mirror screen (Indian context wedge).
hero_04_load_score.png     Load Score panel (biometric loop wedge).
team_portrait.png          Galaxy Brain team portrait.
leave_behind_a4.png        Leave-behind A4 handout.
founders_bio.md            ~75 words per founder.
one_paragraph_about.md     100-word boilerplate, reusable in press copy.
elevator_60s.md            60-second elevator script.
fact_sheet.md              Five numbers, five wedges, one architecture line.
phase1_deck.pdf            Phase 1 blueprint deck (or .txt placeholder).
screencast.txt             Screencast pointer until the MP4 lands.

Contact
-------
Shaurya Punj — spunj_be23@thapar.edu
Shorya Gupta — sgupta9_be24@thapar.edu
Repository    — https://github.com/ShAuRyA-Noodle/Combobulating
Live demo     — https://huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin
Site          — https://shaurya-noodle.github.io/Combobulating

License
-------
MIT for code. CC BY 4.0 for press-kit imagery. Credit Galaxy Brain on use.
EOF

# Build the zip.
rm -f "${ZIP_OUT}"
( cd "${STAGING}" && zip -qr "${ZIP_OUT}" . )

# Sanity-check the result.
SIZE_BYTES=$(wc -c < "${ZIP_OUT}" | tr -d ' ')
FILE_COUNT=$(unzip -Z1 "${ZIP_OUT}" | wc -l | tr -d ' ')

echo
echo "==> Built ${ZIP_OUT}"
echo "    file count : ${FILE_COUNT}"
echo "    bytes      : ${SIZE_BYTES}"
echo

# Clean staging.
rm -rf "${STAGING}"
