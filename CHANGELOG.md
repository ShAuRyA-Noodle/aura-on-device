# Changelog

All notable changes to Aura are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-05-07

Public launch in parallel with the Samsung EnnovateX 2026 submission.

### Added

- Working Phi-3-mini orchestrator with a seven-state LangGraph machine, typed JSON tool schemas, ranking policy, Reasoning Trace emitter, and tests under `orchestrator/`.
- Four agent reference implementations under `agents/` — Comms, Calendar, Finance, Wellness — plus shared `agents/core`.
- Memory graph at `memory/` — SQLite + sqlite-vss + SQLCipher AES-256 layer, hash-chained audit log, daily Merkle root, migrations, store, tests.
- Wizard-of-Oz pilot kit at `pilot/` — consent forms, qualitative and quantitative protocols, recruitment poster, raw-data templates, five analysis notebooks, operator script.
- iOS reference build at `apps/ios/Aura/` — Swift Package, Xcode project from `project.yml`, Morning Brief view, Reasoning Trace drawer, Memory tab, HealthKit, EventKit, Gmail, Silence Budget services.
- LoRA training pipeline at `models/` for Gemma 2B Q4 adapters, eval harness, GGUF / MLX export configs.
- HuggingFace Space — `Caramel_Coin`, Gradio on the free CPU tier, synthetic-data showcase only.
- GitHub Pages site rebuild at `docs/site/` — bento landing page with all 22 generated images, About, Install (free Apple ID sideload), Privacy, sitemap, robots.
- Press kit at `press_kit/` — fact sheet, build script, brand identity board, four hero screenshots, founder bios, one-paragraph about, 60-second elevator script.
- Launch posts under `_trust/launch/` — Show HN, X thread, LinkedIn long-form, Instagram carousel, Reddit r/India narrative.
- Security disclosure — `.well-known/security.txt` (RFC 9116), top-level `SECURITY.md`.
- Machine-readable citation file `CITATION.cff`.
- v1.0.0 release notes at `docs/release_notes/v1.0.0.md`.
- Top-level `CHANGELOG.md` (this file).

### Changed

- Top-level `README.md` rewritten for the launch — locked tagline, five-wedge gallery, architecture diagram, Get-the-demo and Get-the-source paths, Pilot study summary, privacy promises, team, license, BibTeX citation.
- `docs/site/index.html` rebuilt from a placeholder grid into a full bento layout that uses real images for every visual, with lazy-loading, alt text, semantic HTML5, and a mobile-responsive grid.
- `docs/site/style.css` extended with subpage layout, hero figure styling, wedge-image grid, team figure, and trace two-column layout while keeping the locked palette.

### Documentation

- All eleven Architecture Decision Records carried forward. No rescoping.
- All five privacy promises carried forward, now linked from the site privacy page.
- Threat model carried forward, now linked from `SECURITY.md`.

## [0.1.0] — 2026-05-21 (target — Phase 1 blueprint cut)

Initial blueprint submission for Samsung EnnovateX 2026 Phase 1.

### Added

- Eleven-slide Phase 1 deck (`deck/phase1_blueprint/`).
- Three-layer architecture document (`docs/architecture.md`).
- Three numbered data-flow walkthroughs (`docs/data_flow.md`).
- Threat model (`docs/threat_model.md`).
- Five privacy promises (`docs/privacy_promises.md`).
- Eleven ADRs at `docs/decisions/`.
- Repository skeleton across `apps/`, `agents/`, `orchestrator/`, `memory/`, `models/`, `datasets/`, `pilot/`, `design/`.
- Pilot protocol — quantitative 30-user, qualitative 8-user, six pre-registered KPIs.

[1.0.0]: https://github.com/ShAuRyA-Noodle/Combobulating/releases/tag/v1.0.0
[0.1.0]: https://github.com/ShAuRyA-Noodle/Combobulating/releases/tag/v0.1.0
