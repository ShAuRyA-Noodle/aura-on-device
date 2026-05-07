# Architecture Decision Records

This directory holds Aura's Architecture Decision Records (ADRs) in MADR format.

## Why we keep ADRs

An ADR captures one non-trivial decision, the context that forced it, the chosen option, the consequences, and the alternatives that were rejected. We write one when a decision will outlive a single sprint, when it constrains future engineering choices, or when reversing it would be expensive.

ADRs let a future contributor (and a Samsung judge in Phase 2) reconstruct why the system is shaped the way it is without reading every commit. They also force clarity at decision time — if the decision can't be written down in five sections it usually isn't a decision yet.

## Format — MADR

Every ADR in this directory uses the MADR template:

- **Status** — one of `Proposed`, `Accepted`, `Superseded by ADR-NNNN`, `Deprecated`.
- **Context** — what problem, what constraints, what forces are in play.
- **Decision** — the choice we are committing to, in active voice.
- **Consequences** — positive and negative, including known costs.
- **Alternatives** — at least two other options considered, why each was not chosen.

Sections are required. Empty sections are not allowed; "no alternatives considered" is itself an answer that has to be defended.

## How to add an ADR

1. Pick the next four-digit number. The current highest is 0010.
2. Create `ADR-NNNN-<short-slug>.md`. Slug is lowercase, hyphen-separated, six words or fewer.
3. Fill the five sections. Keep total length under 800 words. Cite specific lines of `plan.md` or `technical_spec.md` if the decision derives from them.
4. Open a PR titled `docs(adr): NNNN <slug>`. Two reviewers required (`contributing.md`).
5. Once merged, link the ADR from the relevant code or doc surface. Decisions about agent contracts go on the agent's docstring; decisions about UI rules go on the relevant view; decisions about platform strategy go in `architecture.md` §7.3.

## Index

- ADR-0001 — Product name (`Aura`)
- ADR-0002 — Orchestrator model (Phi-3-mini, device-capability matrix)
- ADR-0003 — Silence Budget as named state variable
- ADR-0004 — Glass-box Reasoning Trace schema, storage, UI rule
- ADR-0005 — On-device only, no cloud egress
- ADR-0006 — Apple-only Phase 1+2 platform strategy
- ADR-0007 — Memory graph encryption (Secure Enclave / Keystore + SQLCipher)
- ADR-0008 — LangGraph state machine over free-form chat
- ADR-0009 — Typed JSON tool calls; no natural-language inter-agent traffic
- ADR-0010 — Pilot protocol (8 qualitative + 30 quantitative, unpaid)

## Superseded ADRs

When an ADR is replaced, set its `Status` to `Superseded by ADR-NNNN` and add a one-line forward link at the top. Do not delete superseded ADRs — they explain why the current shape exists.

End.
