# Aura

**Anticipate. Act. Stay quiet.**

Galaxy Brain — Shaurya Punj, Shorya Gupta. Thapar Institute of Engineering and Technology.
Samsung EnnovateX 2026 submission.

[![Free-tier-only — Total Cost ₹2,000](https://img.shields.io/badge/Build-%E2%82%B92%2C000%20total-FF5B2E)](docs/decisions/ADR-0011-no-apple-developer-program.md)
[![Live Demo — Caramel Coin](https://img.shields.io/badge/Live%20Demo-Caramel__Coin-FF5B2E)](https://huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin)
[![Audit — AUDIT_REPORT.md](https://img.shields.io/badge/Audit-AUDIT__REPORT.md-green)](AUDIT_REPORT.md)
[![Audit — PLAN_COMPLETION_AUDIT.md](https://img.shields.io/badge/Audit-PLAN__COMPLETION__AUDIT.md-green)](../PLAN_COMPLETION_AUDIT.md)

> Live Demo deployed at https://huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin
> (Gradio app, free CPU tier, synthetic-data showcase only — no user PII).

---

## Status

| Phase | State |
|---|---|
| Phase 1 — Blueprint deck | **Ready** (11 / 11 slides shipped; 5 small fixes per `AUDIT_REPORT.md` before upload) |
| Phase 2 — Prototype + 30-user pilot | **Scaffolded** at `phase2/` — awaiting shortlist email |
| Phase 3 — Bangalore finals | **Scaffolded** at `phase3/` — awaiting Phase 2 shortlist |

---

## Problem

Designing Empathetic Intelligence User Experience for Everyday Life.

Indian Gen Z and Gen Alpha users live inside a notification flood. The phone buzzes
two hundred times a day; almost none of those buzzes serve the user. Existing
assistants are reactive, cloud-bound, and have no view of biometrics, no
understanding of UPI or IRCTC or WhatsApp project groups, and no way to show
their work. Aura is the layer that closes the loop from on-device signal to
transparent autonomous action, and stays silent the rest of the time.

## What this is

- An on-device, multi-agent empathetic intelligence layer.
- Four specialist agents — Communications, Calendar, Finance, Wellness —
  coordinated by a Phi-3-mini orchestrator.
- A user-owned memory graph with one-tap export, time-range delete, and a
  tamper-evident audit log.
- A Reasoning Trace, visible for every action, that lets the user inspect,
  edit, or reject any decision.
- A daily Silence Budget that caps proactive surfaces at three.

## What this is not

- Not a chatbot. No personality, no voice, no face.
- Not a screen-time optimiser. We measure success in fewer taps, not more.
- Not cloud inference by default. No byte leaves the device without an
  explicit user-initiated action.
- Not a Samsung-only product. iOS reference build first; Galaxy is the
  production target.
- Not a wellness gamifier.

## Project Phases

| Directory | Phase | Contents |
|---|---|---|
| `deck/phase1_blueprint/` | Phase 1 — Blueprint | 11 slides, deck.md, anti_cliché audit, judges memo, citation map, elevator-60s, production checklist, build/`aura_phase1_blueprint_v1.pptx` |
| `phase2/` | Phase 2 — Prototype + Pilot | README, checklist, 5 deliverable scaffolds (pilot report, LoRA adapters, Galaxy emulator demo, threat model validation, Silence Budget KPI) |
| `phase3/` | Phase 3 — Finals | README, travel logistics, stage kit, judge research, post-event followups, contingency kit |

The Phase 3 pitch deck itself lives at `deck/phase3_pitch/`
(scaffolded; deck content owned by the Phase 3 deck agent).

## Repository layout

```
apps/         iOS (primary), Android (port — Phase 2), Watch (Phase 2)
agents/       Per-agent Python reference implementations (comms, calendar, finance, wellness, core)
orchestrator/ LangGraph state machine, tool schemas, ranking policy, trace, tests
memory/       SQLite + sqlite-vss schema, migrations, audit log, store, tests
models/       LoRA training, eval harness, quantised exports, configs
datasets/     comms + finance synthetic training corpora
pilot/        Consent forms, qual + quant protocols, recruitment, raw_data templates, analysis (5 notebooks, charts)
design/       Brand kit, screens, architecture, charts, QR pack, leave-behind, anti-cliché audit
deck/         phase1_blueprint/ (shipped), phase3_pitch/ (scaffolded)
demo/         5-min live script, 90s storyboard, Q&A anticipated, recording setup, dress rehearsal
docs/         plan, architecture, threat model, runbook, references, glossary, privacy promises, decisions, release notes, site
phase2/       Phase 2 deliverable scaffolds (README, checklist, 5 deliverables)
phase3/       Phase 3 finals scaffolds (README, travel, stage kit, judges, follow-ups, contingency)
e2e/          End-to-end pytest scaffolds (Monday Brief, Quiet Group Chat)
hf_space/     Live HuggingFace Space — Caramel Coin (deployed)
web/          Local FastAPI + React fallback for venue-stage demo
_trust/       Press kit, social posts, slide-9 evidence block, risk-recovery brief, site copy
```

## Key documents

- Master plan: `../plan.md` (root level — single source of truth)
- Technical spec: `../technical_spec.md`
- Competitive: `../competitive.md`
- Deck spec: `../deck_spec.md`
- Architecture: `docs/architecture.md`
- Threat model: `docs/threat_model.md`
- Privacy promises: `docs/privacy_promises.md`
- Glossary: `docs/glossary.md`
- References (citation aggregate): `docs/references.md`
- Runbook: `docs/runbook.md`
- ADR index: `docs/decisions/` (ADR-0001 through ADR-0011)
- Phase 1 deck: `deck/phase1_blueprint/`
- Phase 1 audit: `AUDIT_REPORT.md`
- Plan-completion audit: `../PLAN_COMPLETION_AUDIT.md`

## Getting started

iOS reference build: see `apps/ios/README.md`.
Python orchestrator: `pip install -r agents/core/requirements.txt && python -m orchestrator --help`.
Pilot analysis: `pip install -r pilot/analysis/requirements.txt && jupyter lab pilot/analysis/notebooks/`.

## Team

Galaxy Brain — Thapar Institute of Engineering and Technology.

- Shaurya Punj — architecture, Wellness agent, KPI study, pitch.
- Shorya Gupta — iOS app, Comms / Calendar / Finance agents, memory graph.

EnnovateX: https://www.ennovatex.io

## License

MIT. See `LICENSE`.
