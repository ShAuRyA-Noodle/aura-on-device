# ADR-0009 — Inter-Agent Communication: Typed JSON Tool Calls, No Natural Language

## Status

Accepted (2026-05-07). Source: `plan.md` §10.2; `technical_spec.md` §3, §4.5.

## Context

The four agents (Comms, Calendar, Finance, Wellness) coordinate via the orchestrator. Two paradigms are available:

1. **Typed JSON tool calls.** Each agent exposes a catalogue of tools with input and output schemas validated by `jsonschema`. The orchestrator dispatches typed calls and consumes typed results.
2. **Natural-language inter-agent traffic.** Each agent emits free-form prose; downstream agents parse the prose; the orchestrator parses the chat thread.

The free-form path is enticing because it lets agents "compose" novel reasoning without explicit schema work. It is also where multi-agent systems hallucinate, drift, and become unauditable.

Constraints:

- The Reasoning Trace must be machine-validatable (ADR-0004); fields must come from typed sources.
- Latency budget (`technical_spec.md` §2): each agent `tick()` median 300 ms, p95 700 ms. Free-form prose generation adds an LLM call and parser pass per agent, blowing the budget.
- Tests must run on synthetic fixtures with golden outputs (`plan.md` §12.5). Golden outputs require schemas.
- The privacy invariant ("never persist message bodies") is easier to enforce when agent outputs are structured: redact a known field rather than scrub a prose string.

## Decision

All inter-agent and orchestrator-to-agent communication is via **typed JSON tool calls** validated against per-tool JSON Schema. No agent receives natural-language input from another agent. No agent emits natural-language output for consumption by another agent.

The schema for a tool call is fixed (`technical_spec.md` §4.5):

```json
{
  "$id": "https://aura.local/schemas/toolcall.v1.json",
  "type": "object",
  "required": ["call_id","agent","tool","args","ts","confirm_required"],
  "properties": {
    "call_id":     {"type":"string","pattern":"^t_[a-z0-9]{10}$"},
    "agent":       {"enum":["comms","calendar","finance","wellness","orchestrator"]},
    "tool":        {"type":"string"},
    "args":        {"type":"object"},
    "ts":          {"type":"string","format":"date-time"},
    "confirm_required": {"type":"boolean"},
    "expected_surface": {"enum":["WATCH","PHONE_CARD","EARBUD_TTS","SILENT"]},
    "deadline_ms": {"type":"integer","minimum":50,"maximum":10000}
  },
  "additionalProperties": false
}
```

Per-agent input and output schemas are declared in each agent's spec (`technical_spec.md` §3.1–§3.4). Each tool's signature is enforced at call time via the `jsonschema==4.23.0` library.

The **only** natural-language strings in the system are:

- The `rationale` field on a Reasoning Trace (≤500 chars), produced by the orchestrator from a template or, for novel cases, from Phi-3-mini under a bounded prompt.
- User-visible card text, generated from the `chosen` action and the `signals[]` list using a fixed template per action kind.
- Draft replies in CommsAgent's `draft_reply` tool, which are user-facing artefacts not consumed by another agent.

**Validation.** Every tool call passes `jsonschema` validation before dispatch. Validation failure raises `SchemaError`, the orchestrator logs the offending JSON to `errors/quarantine_calls.jsonl`, and the call is dropped (the agent times out from the orchestrator's perspective).

**Catalogue locking.** The set of (agent, tool) pairs is enumerated in code; the orchestrator refuses to dispatch a call to an unknown tool. Adding a tool requires a code change plus an ADR or a referenced doc update.

## Consequences

Positive:

- Trace fields are typed; redaction is field-level, not regex-on-prose.
- Latency stays inside budget — no LLM calls between agents.
- The Reasoning Trace renders cleanly in the five-section UI (ADR-0004).
- `jsonschema` validation catches drift at the boundary, not in production.
- Unit tests assert on typed outputs.

Negative / costs:

- Adding a new agent capability is a multi-step change: add tool to agent spec, add schema, add unit test fixture, plumb in orchestrator's tool catalogue. This is intentional friction.
- The orchestrator cannot ask an agent an open-ended question. Mitigated by the fact that Aura's design rejects open-ended cross-agent queries; every cross-agent need is a concrete tool call.

## Alternatives

- **Free-form natural-language inter-agent traffic.** Rejected: hallucination, latency, no clean trace rendering, no testability.
- **Protocol Buffers / Cap'n Proto.** Considered. Trades JSON readability for binary throughput. Throughput is not the bottleneck on a single-device service. JSON wins on debuggability and aligns with `jsonschema` validation already in the toolchain.
- **In-process function calls without a schema layer.** Rejected: collapses the agent boundary into a Python module call and loses the trace observability.

End of ADR-0009.
