"""Abstract base class for every Aura specialist agent.

Spec contract (technical_spec.md §3, §12.5):
- `tick(input)` returns an AgentOutput in <300 ms median, <700 ms p95.
- `tools()` returns a list of JSON Schema dicts that the orchestrator validates
  every ToolCall against.
- `handle_tool_call(call)` is called once per dispatch; it must be deterministic
  for a given (state, args).
- The agent never persists raw user content — only structured metadata.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .types import AgentInput, AgentOutput, AgentName, ToolCall, ToolResult


class Agent(ABC):
    """Abstract spec for the four Aura agents.

    Sub-classes set `name` and override `tick`, `tools`, `handle_tool_call`.
    """

    name: AgentName
    # p50 budget per spec §3 (300 ms). Used by tick_timed() to flag slow ticks.
    latency_budget_ms: int = 300

    # ---------- public surface ----------

    @abstractmethod
    def tick(self, input: AgentInput) -> AgentOutput:
        """One reasoning cycle. Pure-ish: depends only on `input` and self state."""

    @abstractmethod
    def tools(self) -> List[Dict[str, Any]]:
        """List of JSON Schema dicts, one per tool this agent exposes.

        Each dict matches the OpenAI tool-call shape::

            {"name": "...", "description": "...",
             "parameters": {"type":"object","properties":{...},"required":[...]}}
        """

    @abstractmethod
    def handle_tool_call(self, call: ToolCall) -> ToolResult:
        """Execute a single tool. Must be schema-validated upstream."""

    # ---------- helpers ----------

    def tick_timed(self, input: AgentInput) -> AgentOutput:
        """Wrap `tick` with monotonic latency measurement and a `slow` flag."""

        start = time.perf_counter()
        try:
            out = self.tick(input)
        except Exception as exc:  # pragma: no cover - defensive
            out = AgentOutput(
                agent=self.name,
                tick_ts=input.tick_ts,
                candidates=[],
                payload={},
                trace_fragment=None,
                latency_ms=(time.perf_counter() - start) * 1000.0,
                error=f"{type(exc).__name__}: {exc}",
            )
            return out

        out.latency_ms = (time.perf_counter() - start) * 1000.0
        if out.trace_fragment is not None and out.latency_ms > self.latency_budget_ms:
            # Spec §3: any synchronous call >300 ms is flagged.
            out.trace_fragment.slow = True
        return out
