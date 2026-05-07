# ADR-0008 — Orchestrator: Deterministic LangGraph State Machine over Free-Form Chat

## Status

Accepted (2026-05-07). Source: `plan.md` §13; `technical_spec.md` §4.1.

## Context

The orchestrator coordinates four agents and emits actions to the Experience Layer. Two designs exist for this kind of system:

1. A **deterministic state machine** with named states, guarded transitions, explicit timeouts, and typed inputs and outputs.
2. A **free-form chat** loop where the orchestrator LLM "talks to" agent LLMs in natural language until consensus is reached.

The free-form chat design is on display in early multi-agent frameworks (e.g. AutoGen, https://arxiv.org/abs/2308.08155). It is flexible but introduces infinite-loop risk, observability gaps, hallucinated tool calls, and uneven latency.

Constraints:

- Latency budget: 3000 ms wall-clock for the stress-driven mute reference flow (`technical_spec.md` §2).
- The Reasoning Trace must be reproducible from the trace JSON alone (ADR-0004). Free-form chat traces are hard to render in the five-section drawer.
- Hard caps (3 surfaces/day, 1 per 30 min, 0 in `RECOVERING`) must be enforced before scoring (`technical_spec.md` §4.3). State-machine guards make this trivial; free-form chat makes it fragile.
- The system must be testable with synthetic input fixtures (`plan.md` §12.5). Deterministic state machines are unit-testable; free-form chat is not.

## Decision

The orchestrator is implemented as a **LangGraph state machine** (https://langchain-ai.github.io/langgraph/) with seven states:

`Idle → Listening → Deliberating → AwaitingConfirm | Executing → LoggingTrace → Cooldown → Idle`

Each state has a typed entry action, a typed exit guard, and an explicit timeout (`technical_spec.md` §4.1). On timeout the machine takes a defined transition rather than an undefined behaviour:

- `Listening` 2000 ms → proceed with received agent outputs only.
- `Deliberating` 1500 ms → force `do_nothing`.
- `AwaitingConfirm` 60 s phone / 8 s watch → log dismiss.
- `Executing` 5000 ms → mark `tool_failed`, no retry this tick.
- `LoggingTrace` 1000 ms → fall back to a raw-file trace path.

The orchestrator LLM (Phi-3-mini, ADR-0002) does **not** drive the state machine. It is invoked from inside specific states (`Deliberating` for novel candidate sets, `LoggingTrace` for LLM-sourced rationale) with bounded prompts and bounded output token counts.

Inter-agent communication is via typed JSON tool calls (ADR-0009), not chat. The orchestrator exposes each agent's tool catalogue and dispatches calls programmatically.

## Consequences

Positive:

- Deterministic execution means every trace is reproducible from the trace JSON.
- Hard caps and DND policy enforce as guards before any scoring runs.
- Unit tests can drive the machine through every state with synthetic fixtures (`plan.md` §12.5).
- Latency budget is achievable because rule-only paths skip the LLM entirely (`technical_spec.md` §2 mitigation #1).
- Failure modes are named: timeout in `Deliberating` → `do_nothing`; agent timeout → proceed with received outputs; tool failure → log + no retry.

Negative / costs:

- LangGraph is a young framework; pinning version 0.2.30 (`technical_spec.md` §13.3) is necessary to avoid breaking changes.
- A state machine has a higher initial implementation cost than a chat loop. Acceptable: the cost is paid once, the observability gain is permanent.
- "Novel" decision archetypes that do not fit existing rule scaffolds require LLM invocation inside `Deliberating`, with a 1500 ms budget and a fallback to template rationale.

## Alternatives

- **AutoGen-style multi-agent chat (https://arxiv.org/abs/2308.08155).** Rejected: infinite-loop risk, no clean trace rendering, hard to enforce hard caps, hard to test.
- **CrewAI-style role-based agents (https://docs.crewai.com/).** Rejected: similar issues with chat-driven coordination; less explicit about state.
- **Hand-rolled state machine without LangGraph.** Considered. LangGraph buys typed states, edge guards, and a community-maintained library at the cost of one dependency. Net positive.
- **Single-agent LLM with all tools attached (no orchestrator).** Rejected: collapses the four-agent specialisation into one prompt and removes the wedge of agent-specific LoRAs.

End of ADR-0008.
