# Aura

**Anticipate. Act. Stay quiet.**

Galaxy Brain — Shaurya Punj, Shorya Gupta. Thapar Institute of Engineering and Technology.
Samsung EnnovateX 2026 submission.

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

## Repository layout

```
apps/         iOS (primary), Android (port), Watch
agents/       Per-agent Python reference implementations
orchestrator/ LangGraph state machine, tool schemas, ranking policy
memory/       SQLite + sqlite-vss schema, migrations, audit log
models/       LoRA training, eval harness, quantised exports
datasets/     LSApp, Tsinghua, pilot collected
pilot/        Consent forms, qual + quant protocols, analysis
design/       Figma exports, deck assets
deck/         Phase 1 blueprint, Phase 3 pitch
docs/         Plan, architecture, threat model, decisions
```

## Key documents

- Master plan: `docs/plan.md`
- Technical spec: `docs/technical_spec.md`
- Architecture: `docs/architecture.md`
- Threat model: `docs/threat_model.md`
- Phase 1 deck: `deck/phase1_blueprint/`
- Demo video: `deck/phase3_pitch/demo.mp4`

## Getting started

iOS reference build: see `apps/ios/README.md`.
Python orchestrator: `pip install -r requirements.txt && python -m orchestrator.cli --help`.

## Team

Galaxy Brain — Thapar Institute of Engineering and Technology.

- Shaurya Punj — architecture, Wellness agent, KPI study, pitch.
- Shorya Gupta — iOS app, Comms / Calendar / Finance agents, memory graph.

EnnovateX: https://www.ennovatex.io

## License

MIT. See `LICENSE`.
