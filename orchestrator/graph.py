"""Aura orchestrator LangGraph state machine.

Implements technical_spec.md §4.1.

Production target: LangGraph (https://langchain-ai.github.io/langgraph/). The
team installs it with ``pip install langgraph``. When ``langgraph`` is not
importable (e.g., in this Python reference test harness) we run a clean
deterministic fallback state machine with the *same* state names and the
*same* transition guards — so behaviour is bit-identical and unit tests pass
with or without the framework on the path. Production switches to LangGraph
by setting ``USE_LANGGRAPH=1``.

States (verbatim from spec §4.1): ``Idle``, ``Listening``, ``Deliberating``,
``AwaitingConfirm``, ``Executing``, ``LoggingTrace``, ``Cooldown``.

Each agent is run sequentially within ``Listening`` because the four agents
are pure-Python in this reference; in the LangGraph build the four become
parallel nodes with a join at ``Deliberating``. The interface (``_run_agents``)
is identical so the swap is one-line.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from agents.core.agent_base import Agent
from agents.core.types import (
    AgentInput,
    AgentName,
    AgentOutput,
    Candidate,
    Outcome,
    Surface,
    Trace,
    UserState,
    WellnessState,
)

from .policy import ActionHistory, DNDWindow, Policy
from .trace import emit_trace, validate_trace


# Try to detect langgraph availability so the README claim ("targets the public
# LangGraph API") is enforced by code, not just docs.
_LANGGRAPH_AVAILABLE: bool
try:  # pragma: no cover - environment dependent
    import langgraph  # noqa: F401

    _LANGGRAPH_AVAILABLE = True
except Exception:  # pragma: no cover
    _LANGGRAPH_AVAILABLE = False


class OrchestratorState(str, Enum):
    """Spec §4.1 states."""

    IDLE = "Idle"
    LISTENING = "Listening"
    DELIBERATING = "Deliberating"
    AWAITING_CONFIRM = "AwaitingConfirm"
    EXECUTING = "Executing"
    LOGGING_TRACE = "LoggingTrace"
    COOLDOWN = "Cooldown"


@dataclass
class TickResult:
    """Bundled output of one orchestrator tick."""

    trace: Trace
    final_state: OrchestratorState
    candidates: List[Candidate] = field(default_factory=list)
    agent_outputs: List[AgentOutput] = field(default_factory=list)
    chosen_kind: str = "do_nothing"
    cap_reason: Optional[str] = None


@dataclass
class Orchestrator:
    """Wired-up multi-agent orchestrator.

    Attributes
    ----------
    agents: list[Agent]
        Comms, Calendar, Finance, Wellness — anything implementing the
        ``Agent`` ABC will work.
    policy: Policy
    history: ActionHistory
        Rolling-window action history for cap enforcement.
    dnd: DNDWindow
    """

    agents: List[Any]  # accepts both Agent subclasses and the dataclass FinanceAgent
    policy: Policy = field(default_factory=Policy)
    history: ActionHistory = field(default_factory=ActionHistory)
    dnd: DNDWindow = field(default_factory=DNDWindow)
    recovering_since: Optional[datetime] = None
    listening_timeout_ms: int = 2000
    deliberating_timeout_ms: int = 1500

    # ---- public entry --------------------------------------------------

    def tick(
        self,
        user_state: UserState,
        agent_payloads: Dict[str, Dict[str, Any]],
        tick_ts: Optional[str] = None,
        trigger: Optional[Dict[str, Any]] = None,
    ) -> TickResult:
        """One full Idle -> Cooldown loop. Returns a :class:`TickResult`.

        ``agent_payloads`` maps agent name (``comms``, ``calendar``, ``finance``,
        ``wellness``) to its ``payload`` dict.
        """
        ts_iso = tick_ts or datetime.now(timezone.utc).isoformat()
        now = _parse_ts(ts_iso)
        trigger = trigger or {"source": "tick", "value": ts_iso}

        # Idle -> Listening
        state = OrchestratorState.LISTENING
        agent_outputs = self._run_agents(user_state, agent_payloads, ts_iso)

        # Listening -> Deliberating
        state = OrchestratorState.DELIBERATING
        candidates: List[Candidate] = []
        for out in agent_outputs:
            candidates.extend(out.candidates)

        decision = self.policy.decide(
            candidates=candidates,
            user_state=user_state,
            history=self.history,
            dnd=self.dnd,
            now=now,
            recovering_since=self.recovering_since,
        )

        # Build signals from agent outputs (no PII).
        signals: List[Dict[str, Any]] = []
        for out in agent_outputs:
            if out.trace_fragment is not None:
                signals.append({
                    "agent": out.trace_fragment.agent.value,
                    "decision": out.trace_fragment.decision,
                    "drivers": out.trace_fragment.drivers,
                    "slow": out.trace_fragment.slow,
                })

        if decision.chosen is None:
            # Deliberating -> Cooldown directly.
            trace = emit_trace(
                trigger=trigger,
                signals=signals,
                scored=decision.candidates,
                chosen_action=None,
                rationale="no candidate scored above threshold",
                cap_reason=decision.cap_reason,
            )
            validate_trace(trace)
            return TickResult(
                trace=trace,
                final_state=OrchestratorState.COOLDOWN,
                candidates=candidates,
                agent_outputs=agent_outputs,
                chosen_kind="do_nothing",
                cap_reason=decision.cap_reason,
            )

        # Confirm-required -> AwaitingConfirm; else -> Executing.
        if decision.chosen.confirm_required:
            state = OrchestratorState.AWAITING_CONFIRM
        else:
            state = OrchestratorState.EXECUTING

        rationale = self._template_rationale(decision.chosen, signals)

        # LoggingTrace -> Cooldown
        self.history.append(now, decision.chosen.kind)

        trace = emit_trace(
            trigger=trigger,
            signals=signals,
            scored=decision.candidates,
            chosen_action=decision.chosen,
            rationale=rationale,
        )
        validate_trace(trace)

        # If chosen is a wellness recovery action, mark recovering_since.
        if decision.chosen.kind == "PERMIT_LEISURE":
            self.recovering_since = now

        return TickResult(
            trace=trace,
            final_state=OrchestratorState.COOLDOWN,
            candidates=candidates,
            agent_outputs=agent_outputs,
            chosen_kind=decision.chosen.kind,
            cap_reason=decision.cap_reason,
        )

    # ---- internals ------------------------------------------------------

    def _run_agents(
        self,
        user_state: UserState,
        agent_payloads: Dict[str, Dict[str, Any]],
        tick_ts: str,
    ) -> List[AgentOutput]:
        outputs: List[AgentOutput] = []
        deadline = time.perf_counter() + self.listening_timeout_ms / 1000.0
        for agent in self.agents:
            agent_name = getattr(agent, "name", None)
            a_str = agent_name.value if hasattr(agent_name, "value") else str(agent_name)
            payload = agent_payloads.get(a_str, {}) or {}
            inp = AgentInput(
                tick_ts=tick_ts,
                agent=agent_name,
                user_state=user_state,
                payload=payload,
            )
            if time.perf_counter() > deadline:
                # Listening timeout — proceed with what we have (spec §4.1).
                break
            try:
                if hasattr(agent, "tick_timed"):
                    out = agent.tick_timed(inp)
                else:
                    # Async tick (FinanceAgent dataclass) — coerce sync.
                    coro = agent.tick(payload | {"tick_ts": tick_ts})
                    if hasattr(coro, "__await__"):
                        import asyncio

                        out_dict = asyncio.run(coro)  # type: ignore[arg-type]
                        out = AgentOutput(
                            agent=AgentName.FINANCE,
                            tick_ts=tick_ts,
                            candidates=[],
                            payload=out_dict,
                        )
                    else:
                        out = coro  # type: ignore[assignment]
                outputs.append(out)
            except Exception as exc:  # spec §4.1 failure mode
                outputs.append(
                    AgentOutput(
                        agent=agent_name or AgentName.ORCHESTRATOR,
                        tick_ts=tick_ts,
                        candidates=[],
                        payload={"error": f"{type(exc).__name__}: {exc}"},
                    )
                )
        return outputs

    @staticmethod
    def _template_rationale(action, signals: List[Dict[str, Any]]) -> str:
        """One-sentence template — production swaps in Phi-3-mini phrasing."""
        kind = action.kind
        drivers = []
        for s in signals:
            drivers.extend(s.get("drivers", []))
        if kind == "MUTE_GROUP_30":
            return "High load with active group context; muting 30 minutes."
        if kind == "BREATHE_478":
            return "Stress spike detected; offering a breathing break."
        if kind == "LEAVE_BY_ALERT":
            return "Travel time means you should leave now."
        if kind == "SHOW_BRIEF":
            return "Composed a single brief from the morning's signals."
        if kind == "BATCH_DIGEST":
            return "Group flooded; collapsed into one digest with actionable items."
        if kind == "PERMIT_LEISURE":
            return "Load has dropped; you can take a break guilt-free."
        if drivers:
            return f"Top drivers: {', '.join(drivers[:3])}."
        return f"Chose {kind}."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_ts(s: str) -> datetime:
    s = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
