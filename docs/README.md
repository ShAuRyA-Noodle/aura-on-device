# Aura — Documentation Index

Engineering governance and reference material for Aura, the on-device multi-agent empathetic intelligence layer submitted to Samsung EnnovateX 2026.

Repo: https://github.com/ShAuRyA-Noodle/Combobulating
Team: Galaxy Brain — Shaurya Punj, Shorya Gupta — Thapar Institute of Engineering and Technology

---

## Start here

- [`architecture.md`](architecture.md) — Authoritative architecture summary. Three layers, four agents, orchestrator, memory graph, Reasoning Trace, Silence Budget. Includes Mermaid diagram. Cross-references `plan.md` §10–§14 and `technical_spec.md` §1–§6.
- [`data_flow.md`](data_flow.md) — Numbered walkthroughs with timestamps for the three reference flows: Morning Brief, Quiet Group Chat, Spend Mirror.
- [`glossary.md`](glossary.md) — Defined terms.

## Decisions

- [`decisions/README.md`](decisions/README.md) — How to add an ADR. MADR format.
- [`decisions/ADR-0001-product-name.md`](decisions/ADR-0001-product-name.md) — Product name: Aura.
- [`decisions/ADR-0002-orchestrator-model.md`](decisions/ADR-0002-orchestrator-model.md) — Orchestrator: Phi-3-mini with device-capability matrix.
- [`decisions/ADR-0003-silence-budget.md`](decisions/ADR-0003-silence-budget.md) — Silence Budget as named state variable. **Critical.**
- [`decisions/ADR-0004-glass-box-trace.md`](decisions/ADR-0004-glass-box-trace.md) — Reasoning Trace schema, storage, UI rule.
- [`decisions/ADR-0005-on-device-only.md`](decisions/ADR-0005-on-device-only.md) — No cloud egress; export is user-initiated.
- [`decisions/ADR-0006-platform-strategy.md`](decisions/ADR-0006-platform-strategy.md) — Apple-only Phase 1+2; Galaxy production target.
- [`decisions/ADR-0007-memory-encryption.md`](decisions/ADR-0007-memory-encryption.md) — Secure Enclave / Keystore + SQLCipher.
- [`decisions/ADR-0008-langgraph-state-machine.md`](decisions/ADR-0008-langgraph-state-machine.md) — Deterministic state machine over free-form chat.
- [`decisions/ADR-0009-typed-tool-calls.md`](decisions/ADR-0009-typed-tool-calls.md) — Typed JSON tool calls; no NL inter-agent.
- [`decisions/ADR-0010-pilot-protocol.md`](decisions/ADR-0010-pilot-protocol.md) — 8 qualitative + 30 quantitative, unpaid, IRB-style consent.

## Privacy and security

- [`threat_model.md`](threat_model.md) — STRIDE per surface, five named adversaries, panic-wipe gesture spec.
- [`privacy_promises.md`](privacy_promises.md) — Five plain-English promises, tested against the threat model.

## Engineering

- [`runbook.md`](runbook.md) — Local orchestrator bring-up, iOS app, RTX 4080 LoRA training, GGUF / MLX export, test suite, demo replay.
- [`contributing.md`](contributing.md) — Code style, Conventional Commits, branch naming, 2-person PR process.

## Reference

- [`references.md`](references.md) — Numbered citation list. Matches deck inline citations.

## Releases

- [`release_notes/v0.1.0.md`](release_notes/v0.1.0.md) — Phase 1 submission cut.

---

## Adjacent documents (one level up)

- `../../plan.md` — Master build plan.
- `../../technical_spec.md` — Build-ready technical specification.
- `../../competitive.md` — Competitive landscape.
- `../../deck_spec.md` — Phase 1 deck specification.

---

End of `README.md`.
