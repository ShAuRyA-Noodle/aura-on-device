# Production Checklist — Aura Phase 1 Blueprint

Pre-submission gates from deck_spec.md §10. Run top-to-bottom. Every box checked or marked [TEAM TO VERIFY]. Live-tracked in this file.

Snapshot date: 2026-05-07. Phase 1 freeze target: 2026-06-01 (assumed; team has ample time per plan.md §0).

---

## Verbatim title checks

- [x] Slide 1 title verbatim "Team Details".
- [x] Slide 2 title verbatim "Problem Statement".
- [x] Slide 3 title verbatim "Proposed Solution".
- [x] Slide 4 title verbatim "Proposed Solution – Technical Details" (en-dash, not hyphen).
- [x] Slide 4a title verbatim "Plausibility & Constraints (extended)".
- [x] Slide 5 title verbatim "Novelty & Innovation".
- [x] Slide 6 title verbatim "Open Datasets planned to be used / published".
- [x] Slide 7 title verbatim "Open Models planned to be used / developed / trained / fine-tuned".
- [x] Slide 8 title verbatim "AI / GenAI / Agentic tools used / developed".
- [x] Slide 8a title verbatim "Best Practices & Creative AI Use (extended)".
- [x] Slide 9 title verbatim "Optional supporting".
- [x] Total slide count = 11 (template ceiling).

## Team data

- [x] Slide 1 Shaurya verified — name, roll 102486013, dept ECE, year 3, email spunj_be23@thapar.edu.
- [x] Slide 1 Shorya verified — name, roll 1024037521 (locked by team), dept CompE, year 2, email sgupta9_be24@thapar.edu.
- [x] Team name set: Galaxy Brain.
- [x] Tagline set: "Anticipate. Act. Stay quiet."

## Citations and numbers

- [x] "237 notifications" cited Common Sense Media 2023 "Constant Companion"; no [TEAM TO VERIFY] tag.
- [x] Every numerical claim on slides 2–8 has a citation tag pointing to plan.md §37.1 or carries [TEAM TO VERIFY] (see citation_map.md).
- [ ] [TEAM TO VERIFY] Tsinghua App Usage Trace exact source URL (slide 6).
- [ ] [TEAM TO VERIFY] Melbourne Context Query Logs exact source URL (slide 6).
- [ ] [TEAM TO VERIFY] iOS DeviceActivity exact docs URL (slide 4a).
- [ ] [TEAM TO VERIFY] Llama-3 license terms (slide 7).
- [ ] [TEAM TO VERIFY] PEFT and sqlite-vss exact upstream URLs (slide 8).

## Visual and rendering

- [ ] Architecture diagram on slide 4 legible at 1920×1080 projector resolution; every label readable from 6 m audience distance.
- [x] Slide 5 names Gemini, Apple Intelligence, Bixby, Pixel verbatim in row labels (plus Rabbit, Humane, ChatGPT for completeness — 7 SOTA total, exceeds the 4-minimum from plan.md §36).
- [x] Slide 6 lists 6 datasets with role and access.
- [x] Slide 7 lists 8 models with role, size, quantization, license, training plan (exceeds 6-minimum).
- [x] Slide 8 lists 6 tools grouped by purpose.
- [x] Slide 9 includes KPI table, pilot methodology paragraph, repo + QR placeholder.

## Audit and copy hygiene

- [x] Anti-cliché audit (deck_spec.md §7) clean for all 11 slides — see anti_cliche_audit.md.
- [x] Banned-word scan run; zero hits (grep verified 2026-05-07).
- [ ] Banned-visual scan run on the rendered Figma file (cannot verify until designer renders the deck).
- [x] Single-accent rule honoured — sunset orange ≤ 3 places per slide on load-bearing elements; slide 5 explicit exemption per deck_spec.md §12.2.
- [x] Body copy ≤ 30 words per slide on all 11 slides (counts: 24, 24, 20, 20, 24, 21, 19, 22, 23, 20, 19).
- [ ] All citations resolved to entries in `docs/references.md`; no dangling [n] superscripts. (Pending: create `docs/references.md` from citation_map.md numbered list.)

## Files and versioning

- [ ] Backup PDF saved at `deck/phase1_blueprint/aura_phase1_blueprint_v{N}.pdf`. (Pending Figma render.)
- [ ] Editable PPTX saved at `deck/phase1_blueprint/aura_phase1_blueprint_v{N}.pptx`. (Pending Figma export.)
- [ ] Source Figma at `deck/phase1_blueprint/aura_phase1_blueprint_v{N}.fig`. (Pending designer recruit per plan.md §25 or self-build.)
- [ ] File naming: `aura_phase1_blueprint_v{N}.pptx` — `{N}` increments from v1 on each freeze.

## Process and external

- [x] Faculty mentor not required — locked per plan.md §35 row 3.
- [x] Phase 1 deadline ample per team — no rush per plan.md §0.
- [ ] Three internal critique passes complete: engineer-led, design-led, story-led (deck_spec.md §11). [TEAM TO VERIFY after Week 2.]
- [ ] Brand identity board generated via Claude `brandkit` skill, saved to `design/brand/`. [TEAM TO VERIFY.]
- [ ] Six app-screen mockups generated via Claude `imagegen-frontend-mobile` skill: Morning Brief, Reasoning Trace drawer, Memory tab, Spend Mirror card, Quiet Group Chat card, Load Score panel. [TEAM TO VERIFY.]

## Asset checklist (deck_spec.md §3)

22 deliverable assets. State as of 2026-05-07: 0/22 done. Tracked separately in `aura/design/asset_checklist.md` once that file is created. [TEAM TO VERIFY: open this file at start of Week 2.]

---

End of production checklist. Re-run end-to-end on every freeze.
