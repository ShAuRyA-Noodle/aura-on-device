"""Aura orchestrator LangGraph state machine.

Implements technical_spec.md §4.1 with a real LangGraph StateGraph runtime.

When ``langgraph`` is importable we build a real ``StateGraph`` with the seven
states (``Idle``, ``Listening``, ``Deliberating``, ``AwaitingConfirm``,
``Executing``, ``LoggingTrace``, ``Cooldown``) and let LangGraph drive the
node transitions per tick. When ``langgraph`` is *not* importable we run a
deterministic fallback with the same node bodies and the same transition
guards — output traces are bit-identical so the 3 replays hash the same in
both modes.

Toggle: set ``AURA_USE_LANGGRAPH=0`` to force the deterministic path even when
the framework is on the path. ``USE_LANGGRAPH=1`` retained for back-compat.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from agents.core.types import (
    AgentInput,
    AgentName,
    AgentOutput,
    Candidate,
    Outcome,
    Surface,
    Trace,
    UserState,
)

from .policy import ActionHistory, DNDWindow, Policy, SilenceBudget
from .trace import emit_trace, validate_trace


# ---------------------------------------------------------------------------
# Optional on-device rationale generator (Phi-3-mini, falls back to Gemma 2B).
#
# Activated when ``AURA_USE_LLM=1``. Produces a single 30-50 word
# sentence used as the trace's ``rationale`` field. If the adapter is
# missing for any reason we keep the deterministic templates from
# :meth:`Orchestrator._template_rationale`.
# ---------------------------------------------------------------------------


_RATIONALE_ADAPTER: Any = None
_RATIONALE_ATTEMPTED = False
_RATIONALE_MODEL_PREFERENCE = ("phi-3-mini-4bit", "gemma-2b-4bit")


def _rationale_llm_enabled() -> bool:
    return os.environ.get("AURA_USE_LLM", "0") == "1"


def _get_rationale_llm() -> Any:
    """Lazy-load Phi-3-mini, falling back to Gemma 2B."""
    global _RATIONALE_ADAPTER, _RATIONALE_ATTEMPTED
    if _RATIONALE_ADAPTER is not None or _RATIONALE_ATTEMPTED:
        return _RATIONALE_ADAPTER
    _RATIONALE_ATTEMPTED = True
    try:
        from models.llm import get_adapter  # type: ignore
    except Exception:
        return None
    for name in _RATIONALE_MODEL_PREFERENCE:
        try:
            _RATIONALE_ADAPTER = get_adapter(name)
            return _RATIONALE_ADAPTER
        except Exception:
            continue
    return _RATIONALE_ADAPTER


def _llm_rationale(
    chosen_kind: str,
    signals: List[Dict[str, Any]],
    user_state: Optional[UserState] = None,
) -> Optional[str]:
    if not _rationale_llm_enabled():
        return None
    adapter = _get_rationale_llm()
    if adapter is None:
        return None
    try:
        from models.llm.prompts import rationale_prompt  # type: ignore

        state_dict: Optional[Dict[str, Any]] = None
        if user_state is not None:
            wellness = getattr(user_state, "wellness_state", "")
            state_dict = {
                "load_score": getattr(user_state, "load_score", None),
                "wellness_state": (
                    wellness.value if hasattr(wellness, "value") else str(wellness)
                ),
                "in_focus_block": getattr(user_state, "in_focus_block", None),
            }
        prompt = rationale_prompt(chosen_kind, signals, state_dict)
        out = adapter.generate(
            prompt,
            max_tokens=80,
            temperature=0.2,
            stop=("\n\n", "<end_of_turn>"),
        )
    except Exception:
        return None
    if not out:
        return None
    sentence = out.strip().split("\n")[0].strip()
    if not sentence:
        return None
    words = sentence.split()
    if len(words) > 55:
        sentence = " ".join(words[:55]).rstrip(",;:") + "."
    return sentence


# ---------------------------------------------------------------------------
# LangGraph availability
# ---------------------------------------------------------------------------

_LANGGRAPH_AVAILABLE: bool
_LANGGRAPH_IMPORT_ERROR: Optional[str] = None
try:
    from langgraph.graph import StateGraph, START, END  # type: ignore

    _LANGGRAPH_AVAILABLE = True
except Exception as _exc:  # pragma: no cover - environment dependent
    _LANGGRAPH_AVAILABLE = False
    _LANGGRAPH_IMPORT_ERROR = f"{type(_exc).__name__}: {_exc}"


def _use_langgraph() -> bool:
    """Per-tick env override. Default: use LangGraph if importable."""
    if not _LANGGRAPH_AVAILABLE:
        return False
    flag = os.environ.get("AURA_USE_LANGGRAPH")
    if flag is None:
        flag = os.environ.get("USE_LANGGRAPH")
    if flag is None:
        return True
    return flag.strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# State enum
# ---------------------------------------------------------------------------


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
    used_langgraph: bool = False
    state_path: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


@dataclass
class Orchestrator:
    """Wired-up multi-agent orchestrator (LangGraph + fallback).

    Attributes
    ----------
    agents: list
        Comms, Calendar, Finance (adapter), Wellness — anything implementing
        the ``Agent`` ABC or exposing a ``tick(payload)`` callable + ``name``.
    policy: Policy
        Candidate ranking + hard caps.
    history: ActionHistory
        Rolling-window action history for cap enforcement.
    dnd: DNDWindow
    budget: SilenceBudget
        Token bucket gating Deliberating -> AwaitingConfirm transition.
    listening_timeout_ms / deliberating_timeout_ms / confirm_timeout_ms /
    executing_timeout_ms: per spec §4.1 row table.
    """

    agents: List[Any]
    policy: Policy = field(default_factory=Policy)
    history: ActionHistory = field(default_factory=ActionHistory)
    dnd: DNDWindow = field(default_factory=DNDWindow)
    budget: SilenceBudget = field(default_factory=lambda: SilenceBudget(total=3, remaining=3))
    recovering_since: Optional[datetime] = None

    # spec §4.1 timeouts
    listening_timeout_ms: int = 2000
    deliberating_timeout_ms: int = 5000  # spec row: 1500 ms; harness allows 5s
    confirm_timeout_ms: int = 30_000  # 30s phone (per task — spec row says 60s phone / 8s watch)
    executing_timeout_ms: int = 5000

    # ---- public entry --------------------------------------------------

    def tick(
        self,
        user_state: UserState,
        agent_payloads: Dict[str, Dict[str, Any]],
        tick_ts: Optional[str] = None,
        trigger: Optional[Dict[str, Any]] = None,
        auto_confirm: bool = True,
    ) -> TickResult:
        """One full Idle -> Cooldown loop. Returns a :class:`TickResult`.

        The state machine is driven by LangGraph when available, otherwise by
        the deterministic fallback below. Both paths read/write the same
        :class:`_TickContext` and produce identical traces.
        """
        ts_iso = tick_ts or datetime.now(timezone.utc).isoformat()
        now = _parse_ts(ts_iso)
        self.budget.maybe_reset(now)
        trigger = trigger or {"source": "tick", "value": ts_iso}

        ctx = _TickContext(
            user_state=user_state,
            agent_payloads=agent_payloads,
            tick_ts=ts_iso,
            now=now,
            trigger=trigger,
            auto_confirm=auto_confirm,
        )

        if _use_langgraph():
            ctx.used_langgraph = True
            self._run_langgraph(ctx)
        else:
            ctx.used_langgraph = False
            self._run_fallback(ctx)

        validate_trace(ctx.trace)
        return TickResult(
            trace=ctx.trace,
            final_state=OrchestratorState.COOLDOWN,
            candidates=ctx.candidates,
            agent_outputs=ctx.agent_outputs,
            chosen_kind=ctx.chosen_kind,
            cap_reason=ctx.cap_reason,
            used_langgraph=ctx.used_langgraph,
            state_path=ctx.state_path,
        )

    # ---- node bodies (shared) -----------------------------------------

    def _node_listening(self, ctx: "_TickContext") -> None:
        ctx.state_path.append(OrchestratorState.LISTENING.value)
        ctx.agent_outputs = self._run_agents(
            ctx.user_state, ctx.agent_payloads, ctx.tick_ts
        )

    def _node_deliberating(self, ctx: "_TickContext") -> None:
        ctx.state_path.append(OrchestratorState.DELIBERATING.value)
        candidates: List[Candidate] = []
        for out in ctx.agent_outputs:
            candidates.extend(out.candidates)
        ctx.candidates = candidates

        for out in ctx.agent_outputs:
            if out.trace_fragment is not None:
                ctx.signals.append(
                    {
                        "agent": out.trace_fragment.agent.value,
                        "decision": out.trace_fragment.decision,
                        "drivers": out.trace_fragment.drivers,
                        "slow": out.trace_fragment.slow,
                    }
                )

        decision = self.policy.decide(
            candidates=candidates,
            user_state=ctx.user_state,
            history=self.history,
            dnd=self.dnd,
            now=ctx.now,
            recovering_since=self.recovering_since,
        )
        ctx.policy_decision = decision

        # Silence Budget gate — if budget is empty AND chosen is non-safety,
        # demote to do_nothing with cap_reason='cap_silence_budget'.
        if decision.chosen is not None:
            from .policy import SAFETY_KINDS

            if decision.chosen.kind not in SAFETY_KINDS and self.budget.remaining <= 0:
                ctx.cap_reason = "cap_silence_budget"
                ctx.policy_decision = type(decision)(
                    chosen=None, candidates=decision.candidates, cap_reason="cap_silence_budget"
                )
        # Snapshot cap_reason for the trace.
        if ctx.policy_decision.chosen is None:
            ctx.cap_reason = ctx.policy_decision.cap_reason or ctx.cap_reason

    def _node_awaiting_confirm(self, ctx: "_TickContext") -> None:
        ctx.state_path.append(OrchestratorState.AWAITING_CONFIRM.value)
        # Auto-confirm for replay determinism. Real device path waits up to
        # confirm_timeout_ms (30s phone / 8s watch).
        if ctx.auto_confirm:
            ctx.confirm_outcome = Outcome.CONFIRMED
        else:
            ctx.confirm_outcome = Outcome.TIMED_OUT

    def _node_executing(self, ctx: "_TickContext") -> None:
        ctx.state_path.append(OrchestratorState.EXECUTING.value)
        # Tool dispatch is tracked here in production; the pure-Python harness
        # treats a chosen action as "dispatched" on entry.
        ctx.executed = True

    def _node_logging_trace(self, ctx: "_TickContext") -> None:
        ctx.state_path.append(OrchestratorState.LOGGING_TRACE.value)
        chosen = ctx.policy_decision.chosen if ctx.policy_decision else None
        if chosen is not None:
            llm_text = _llm_rationale(chosen.kind, ctx.signals, ctx.user_state)
            rationale = llm_text or self._template_rationale(chosen, ctx.signals)
        else:
            rationale = (
                f"blocked by {ctx.cap_reason}"
                if ctx.cap_reason
                else "no candidate scored above threshold"
            )

        ctx.trace = emit_trace(
            trigger=ctx.trigger,
            signals=ctx.signals,
            scored=ctx.policy_decision.candidates if ctx.policy_decision else [],
            chosen_action=chosen,
            rationale=rationale,
            cap_reason=ctx.cap_reason,
            ts=ctx.now,
        )

        # Side-effects: history append + Silence Budget decrement + recovery.
        if chosen is not None:
            self.history.append(ctx.now, chosen.kind)
            self.budget.decrement(chosen.kind)
            ctx.chosen_kind = chosen.kind
            if chosen.kind == "PERMIT_LEISURE":
                self.recovering_since = ctx.now
        else:
            ctx.chosen_kind = "do_nothing"

    def _node_cooldown(self, ctx: "_TickContext") -> None:
        ctx.state_path.append(OrchestratorState.COOLDOWN.value)

    # ---- LangGraph runtime --------------------------------------------

    def _run_langgraph(self, ctx: "_TickContext") -> None:
        """Build + execute the StateGraph for this tick.

        We use a tiny dict-based State (LangGraph requires a mapping/TypedDict
        at the framework level). The actual TickContext lives outside the
        graph and is mutated by node handlers — LangGraph just sequences us
        through the seven states with the spec's transition guards.
        """
        graph = StateGraph(dict)

        # Wrappers — each node runs the shared body and returns the dict
        # state (LangGraph requires a return value).
        def _entry(_state: Dict[str, Any]) -> Dict[str, Any]:
            ctx.state_path.append(OrchestratorState.IDLE.value)
            return _state

        def _listening(_state: Dict[str, Any]) -> Dict[str, Any]:
            self._node_listening(ctx)
            return _state

        def _deliberating(_state: Dict[str, Any]) -> Dict[str, Any]:
            self._node_deliberating(ctx)
            return _state

        def _awaiting(_state: Dict[str, Any]) -> Dict[str, Any]:
            self._node_awaiting_confirm(ctx)
            return _state

        def _executing(_state: Dict[str, Any]) -> Dict[str, Any]:
            self._node_executing(ctx)
            return _state

        def _logging(_state: Dict[str, Any]) -> Dict[str, Any]:
            self._node_logging_trace(ctx)
            return _state

        def _cooldown(_state: Dict[str, Any]) -> Dict[str, Any]:
            self._node_cooldown(ctx)
            return _state

        graph.add_node("Idle", _entry)
        graph.add_node("Listening", _listening)
        graph.add_node("Deliberating", _deliberating)
        graph.add_node("AwaitingConfirm", _awaiting)
        graph.add_node("Executing", _executing)
        graph.add_node("LoggingTrace", _logging)
        graph.add_node("Cooldown", _cooldown)

        graph.add_edge(START, "Idle")
        graph.add_edge("Idle", "Listening")
        graph.add_edge("Listening", "Deliberating")

        # Conditional: Deliberating -> {AwaitingConfirm | Executing | LoggingTrace}
        def _route_after_deliberation(_state: Dict[str, Any]) -> str:
            decision = ctx.policy_decision
            if decision is None or decision.chosen is None:
                return "LoggingTrace"
            return "AwaitingConfirm" if decision.chosen.confirm_required else "Executing"

        graph.add_conditional_edges(
            "Deliberating",
            _route_after_deliberation,
            {"AwaitingConfirm": "AwaitingConfirm", "Executing": "Executing", "LoggingTrace": "LoggingTrace"},
        )

        # Conditional: AwaitingConfirm -> {Executing | LoggingTrace}
        def _route_after_confirm(_state: Dict[str, Any]) -> str:
            return "Executing" if ctx.confirm_outcome == Outcome.CONFIRMED else "LoggingTrace"

        graph.add_conditional_edges(
            "AwaitingConfirm",
            _route_after_confirm,
            {"Executing": "Executing", "LoggingTrace": "LoggingTrace"},
        )

        graph.add_edge("Executing", "LoggingTrace")
        graph.add_edge("LoggingTrace", "Cooldown")
        graph.add_edge("Cooldown", END)

        compiled = graph.compile()
        compiled.invoke({})

    # ---- Deterministic fallback ----------------------------------------

    def _run_fallback(self, ctx: "_TickContext") -> None:
        """Identical control flow to the LangGraph runtime, sans framework."""
        ctx.state_path.append(OrchestratorState.IDLE.value)
        self._node_listening(ctx)
        self._node_deliberating(ctx)

        decision = ctx.policy_decision
        if decision is not None and decision.chosen is not None:
            if decision.chosen.confirm_required:
                self._node_awaiting_confirm(ctx)
                if ctx.confirm_outcome == Outcome.CONFIRMED:
                    self._node_executing(ctx)
            else:
                self._node_executing(ctx)

        self._node_logging_trace(ctx)
        self._node_cooldown(ctx)

    # ---- agent runner (shared) ----------------------------------------

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
                    coro = agent.tick(payload | {"tick_ts": tick_ts})
                    if hasattr(coro, "__await__"):
                        import asyncio

                        out_dict = asyncio.run(coro)  # type: ignore[arg-type]
                        out = AgentOutput(
                            agent=AgentName.FINANCE,
                            tick_ts=tick_ts,
                            candidates=_finance_candidates_from_payload(out_dict, tick_ts),
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
        if kind == "SURFACE_ANOMALY":
            return "Spend velocity is well above your baseline."
        if kind == "PROJECT_BALANCE":
            return "Projected end-of-month balance has crossed your threshold."
        if drivers:
            return f"Top drivers: {', '.join(drivers[:3])}."
        return f"Chose {kind}."


# ---------------------------------------------------------------------------
# Per-tick mutable context
# ---------------------------------------------------------------------------


@dataclass
class _TickContext:
    """All state shared across the seven node bodies for a single tick."""

    user_state: UserState
    agent_payloads: Dict[str, Dict[str, Any]]
    tick_ts: str
    now: datetime
    trigger: Dict[str, Any]
    auto_confirm: bool = True

    agent_outputs: List[AgentOutput] = field(default_factory=list)
    candidates: List[Candidate] = field(default_factory=list)
    signals: List[Dict[str, Any]] = field(default_factory=list)
    policy_decision: Any = None
    confirm_outcome: Any = None
    executed: bool = False
    cap_reason: Optional[str] = None
    chosen_kind: str = "do_nothing"
    trace: Optional[Trace] = None
    used_langgraph: bool = False
    state_path: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _finance_candidates_from_payload(out_dict: Dict[str, Any], tick_ts: str) -> List[Candidate]:
    """Promote FinanceAgent dict output into Candidate(s) for ranking.

    The bare FinanceAgent (dataclass, async tick) returns a dict instead of
    candidates. Translate anomalies + projections into the candidate kinds the
    orchestrator's policy expects.
    """
    candidates: List[Candidate] = []
    anomalies = out_dict.get("anomalies") or []
    if anomalies:
        a0 = anomalies[0]
        severity = a0.get("severity", "low")
        # Severity -> (confidence, priority). Medium/high anomalies get a
        # priority boost so SURFACE_ANOMALY clears the 0.45 threshold even
        # against the WATCH/PHONE_CARD attention tax.
        confidence, priority = {
            "high": (0.90, 0.95),
            "medium": (0.80, 0.90),
            "low": (0.40, 0.60),
        }.get(severity, (0.40, 0.60))
        category = a0.get("category")
        save_amount = _suggested_save_amount(category)
        candidates.append(
            Candidate(
                kind="SURFACE_ANOMALY",
                agent=AgentName.FINANCE,
                confidence=confidence,
                agent_priority=priority,
                confirm_required=False,
                surface=Surface.PHONE_CARD,
                args={
                    "category": category,
                    "reason": a0.get("reason"),
                    "z_score": round(float(a0.get("z_score", 0.0)), 2),
                    "severity": severity,
                    "save_amount_inr": save_amount,
                    "today_total_inr": out_dict.get("today_total"),
                    "vs_avg_pct": out_dict.get("vs_avg_pct"),
                    "suggestion": _cook_tomorrow_copy(category, save_amount),
                },
                rationale_seed=a0.get("reason", "anomaly"),
            )
        )
    proj = out_dict.get("eom_projection")
    if proj and proj.get("hits_zero"):
        candidates.append(
            Candidate(
                kind="PROJECT_BALANCE",
                agent=AgentName.FINANCE,
                confidence=float(proj.get("confidence", 0.5)),
                agent_priority=0.6,
                confirm_required=False,
                surface=Surface.PHONE_CARD,
                args={
                    "balance_eom": proj.get("balance_eom"),
                    "hits_zero": proj.get("hits_zero"),
                },
                rationale_seed=f"balance hits zero {proj.get('hits_zero')}",
            )
        )
    return candidates


def _suggested_save_amount(category: Optional[str]) -> int:
    """Stable per-category save-amount suggestion in INR."""
    table = {
        "food_delivery": 220,
        "transport": 80,
        "shopping": 400,
        "subscriptions": 199,
        "entertainment": 120,
    }
    return int(table.get(category or "", 150))


def _cook_tomorrow_copy(category: Optional[str], save_amount: int) -> str:
    """Per-category nudge copy. food_delivery -> 'Cook tomorrow?'."""
    if category == "food_delivery":
        return f"Cook tomorrow? Typical save Rs.{save_amount}/order."
    if category == "transport":
        return f"Metro / shared auto for sub-5km hops? Typical save Rs.{save_amount}."
    if category == "shopping":
        return f"Add-to-cart cooldown 24h? Typical save Rs.{save_amount}."
    if category == "subscriptions":
        return f"Audit overlapping subscriptions? Typical save Rs.{save_amount}/mo."
    if category == "entertainment":
        return f"Weekday matinee pricing? Typical save Rs.{save_amount}."
    return f"Cap this category tomorrow? Typical save Rs.{save_amount}."


def _parse_ts(s: str) -> datetime:
    s = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def langgraph_status() -> Dict[str, Any]:
    """Diagnostic: returns whether LangGraph is wired and any import error."""
    return {
        "available": _LANGGRAPH_AVAILABLE,
        "import_error": _LANGGRAPH_IMPORT_ERROR,
        "active": _use_langgraph(),
    }
