# ADR-0002 — Orchestrator Model: Phi-3-mini, with Device-Capability Matrix

## Status

Accepted (2026-05-07). Source: `plan.md` §13, `technical_spec.md` §4 and §8.2.

## Context

The orchestrator runs a LangGraph state machine on every tick that reaches the `Deliberating` state. Its job is to take typed JSON tool outputs from the four agents, rank candidate actions, decide whether to surface, and emit a Reasoning Trace. The model's job is small — short rationale prose, occasional natural-language slot suggestions, occasional tool-call planning when no rule path resolves. It is not a chat partner.

Constraints:

- On-device only (ADR-0005). No cloud LLM call on the hot path.
- Phase 1+2 reference build is iOS (ADR-0006). Production target is Galaxy ecosystem.
- Latency budget for the stress-driven mute reference flow is 3000 ms wall-clock; LLM token generation must fit in ~1800 ms (`technical_spec.md` §2).
- Memory: orchestrator and agent LLM cannot both be RAM-resident on a 6 GB device.
- Tool-use behaviour matters more than open-ended reasoning quality.

Forces:

- Phi-3-mini reports strong tool-use performance per its release paper (https://arxiv.org/abs/2404.14219).
- Gemma 2B is already in the system as the agent-side model (Comms, Finance LoRA). Reusing one binary saves disk and cognitive load but conflates orchestrator with agent.
- Llama-3-8B Q4 is feasible only on Tier A devices (≥8 GB) with charge above 50% (`technical_spec.md` §8.1).

## Decision

The orchestrator runs **Phi-3-mini-4k-instruct, Q4 quantised**, as the default model on all supported devices. Heavy fallback to Llama-3-8B Q4 is permitted only on Tier A devices when `is_charging && battery > 50% && device_ram >= 8GB`.

A device-capability matrix governs which model is loaded for which role:

| Tier | RAM | Orchestrator | Agent LLM | Heavy fallback |
|---|---|---|---|---|
| A | ≥8 GB (iPhone 14 Pro, S22 Ultra, S23+, Pixel 8) | Llama-3-8B Q4 (gated) else Phi-3-mini | Gemma 2B Q4 + LoRA | Enabled |
| B | 6–8 GB (iPhone 14, S22 base, A55) | Phi-3-mini Q4 | Gemma 2B Q4 + LoRA (hot-swap) | Disabled |
| C | 4–6 GB (mid-range Galaxy A, older Pixel) | Gemma 2B Q4 | Rule + DistilBERT | Disabled |
| D | <4 GB | Unsupported | — | Block install |

Tier detection at first launch via `ProcessInfo.processInfo.physicalMemory` (iOS) or `ActivityManager.getMemoryInfo()` (Android), persisted to `settings`.

On Tier B and below, orchestrator and agent LLM share the model store on disk only; in RAM, the orchestrator is unloaded while a Gemma + LoRA pass executes, then reloaded. Cost: ~600 ms model load on every orchestrator invocation (`technical_spec.md` §8.1, [TEAM TO VERIFY]).

## Consequences

Positive:

- Phi-3-mini's reported tool-use behaviour is a closer fit for the orchestrator's typed-JSON tool-call planning than open-instruction Gemma 2B.
- Q4 quant brings the model to ~2.3 GB on disk, ~3.0 GB peak RAM, fitting Tier B with hot-swap.
- The matrix gives a clean way to gate Llama-3-8B promotion behind charge and RAM checks, preventing thermal degradation on weaker devices.

Negative / costs:

- Two LLM families on one device (Phi-3 + Gemma) doubles the runtime maintenance surface (MLX + llama.cpp on iOS; MediaPipe LLM Inference on Android). Mitigated by sharing GGUF / MLX conversion scripts.
- Tier C downgrade to Gemma 2B as orchestrator means a measurable quality drop for slot suggestions and rationale prose. Mitigated by template-fallback rationale on the hot path (`technical_spec.md` §2).
- Hot-swap on Tier B costs ~600 ms per orchestrator invocation. [TEAM TO VERIFY in Week 6 whether keeping both models RAM-resident at ~5 GB total beats the swap cost on a real iPhone 14.]

## Alternatives

- **Gemma 2B as orchestrator (single-model build).** Halves disk and RAM, simplifies the runtime story. Rejected because Phi-3-mini's tool-use performance is materially better, and the orchestrator's job is exactly tool-call planning. ADR may be revisited after Phase 2 evals.
- **Llama-3-8B Q4 as default orchestrator.** Higher quality rationale, but ~6 GB peak RAM rules out Tier B and below. Rejected as default; retained as gated fallback on Tier A.
- **Cloud LLM via API.** Rejected by ADR-0005 (no cloud egress) and by latency budget (network round-trip alone exceeds 1800 ms target on Indian mobile data).
- **TinyLlama / Phi-2 / SmolLM.** Smaller, faster, but tool-use quality drops sharply below 3B parameters in our internal smoke tests. Rejected for the orchestrator role; retained for the speculative-decoding draft model exploration in `technical_spec.md` §2 (mitigation #2).

End of ADR-0002.
