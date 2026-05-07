# Contributing to Aura

Two-person team. Direct commits to `main` are fine for now; review-by-PR
becomes standard once a third member joins.

## Adding a new agent

An agent is a typed module that takes structured input, calls one or more
tools, and emits a structured output plus a Reasoning Trace fragment.

1. Create `agents/<name>/` with `__init__.py`, `agent.py`, `tools.py`,
   `schemas.py`, `tests/`.
2. Define the input schema and output schema as Pydantic models in
   `schemas.py`. Match the JSON Schema in `docs/technical_spec.md` §3.
3. Implement `agent.py` with a `tick(input) -> Output` entrypoint. Latency
   target: sub-300 ms median per tick.
4. Register the agent in `orchestrator/registry.py` so the LangGraph state
   machine can route to it.
5. Add a synthetic-input fixture under `agents/<name>/tests/fixtures/` and
   a unit test that runs `tick` on the fixture and asserts shape.
6. The agent must respect the global Do-Not-Disturb window from the user
   settings, and emit a Reasoning Trace fragment for any output that
   triggers an Orchestrator action.

## Adding a new tool

Tools are typed JSON-callable functions exposed to the orchestrator.

1. Add the tool function to the owning agent's `tools.py`.
2. Add the tool's input/output schema to `orchestrator/tools.py` —
   match the tool-call JSON Schema in `docs/technical_spec.md` §4.5.
3. Wire the tool into the orchestrator's allowlist:
   `orchestrator/policy.py:AUTO_EXECUTE_ALLOWLIST` for silent-safe
   tools, otherwise it defaults to `confirm_required: true`.
4. Add a fixture under `tests/tools/` covering at least one happy-path
   and one error-path call.

## Adding a new Reasoning Trace event

Every autonomous or semi-autonomous action must emit a Reasoning Trace
matching the JSON Schema in `docs/technical_spec.md` §4.6.

1. Construct a `Trace` object with `trace_id`, `ts`, `trigger`, `signals`,
   `candidates`, `chosen`, `rationale`, `confirm_required`, `outcome`.
2. Apply the redaction policy from `docs/technical_spec.md` §5.4 before
   the trace is written to the memory graph or rendered in the UI.
3. The orchestrator persists the trace via `memory.write_trace(trace)`;
   never write directly from an agent.
4. The iOS `ReasoningTraceView` and Android equivalent must render every
   field listed in §5.3. If a new field is added to the schema, both
   surfaces must be updated in the same PR.

## Style

- Python: ruff defaults, 4-space indent, type hints required on public
  functions.
- Swift: 4-space tabs (per `.editorconfig`), `swift-format` clean.
- Kotlin: 4-space tabs, ktlint clean.
- Commit messages: Conventional Commits (`feat:`, `fix:`, `chore:`,
  `docs:`, `refactor:`).

## What never goes in the repo

- Raw user data (messages, emails, SMS bodies).
- OAuth tokens or API keys.
- Pilot participant identifying information.
- Model weight binaries — use `models/exports/` (gitignored) and
  publish via GitHub Releases.
