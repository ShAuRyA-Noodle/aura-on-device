"""WellnessAgent — Load Score + intervention selection.

Implements technical_spec.md §3.4.

The agent is a thin shell around :class:`LoadScoreModel` plus a deterministic
``intervention_select`` that picks among the spec's intervention kinds:
``MUTE_GROUP_30``, ``BREATHE_478``, ``NAP_15``, ``PERMIT_LEISURE``, ``DO_NOTHING``.
The orchestrator's ranker re-scores these against state / cost / DND.

State enum (spec §3.4):
- BASELINE: load < 50.
- STRESSED: load >= 70 — surface a safety candidate.
- RECOVERING: 60-min cooldown after a recent STRESSED bucket where score has
  fallen by ≥ 10 points; orchestrator zeros proactive surfaces.
- FOCUSED: user is in a focus block (passed via UserState.in_focus_block).
- UNKNOWN: insufficient signal (cold-start, <7d history).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agents.core.agent_base import Agent
from agents.core.types import (
    AgentInput,
    AgentName,
    AgentOutput,
    Candidate,
    Surface,
    ToolCall,
    ToolResult,
    TraceFragment,
    WellnessState,
)

from .load_score import LoadScoreModel, WellnessFeatures


_RECOVERY_DROP = 10  # spec §3.4 — load drop >= 10 to trigger recovery state.


class WellnessAgent(Agent):
    """Per technical_spec.md §3.4."""

    name = AgentName.WELLNESS
    latency_budget_ms = 60

    TOOLS = (
        "compute_load_score",
        "intervention_select",
        "correlation_check",
        "recovery_check",
    )

    def __init__(self, model: Optional[LoadScoreModel] = None) -> None:
        # Production runs through the trained XGBoost booster; the linear
        # fallback is used only when the artefact is missing on disk. Tests
        # may pass an explicit model to keep the suite fast and deterministic.
        self.model = model if model is not None else LoadScoreModel.load_default()
        self._history: List[Dict[str, Any]] = []  # rolling list of {ts, score}
        self._last_recovery_ts: Optional[datetime] = None

    # ----- core public API -----------------------------------------------

    def tick(self, input: AgentInput) -> AgentOutput:
        payload = input.payload or {}
        baseline = payload.get("personal_baseline", {})
        # Hour from tick_ts (best-effort; fall back to noon).
        hour = self._hour_of(input.tick_ts)
        feats = WellnessFeatures.from_payload(payload, baseline=baseline, hour=hour)

        hrv_unavailable = feats.rmssd_ms is None
        score = int(round(self.model.predict_score(feats, hrv_unavailable=hrv_unavailable)))
        drivers = self.model.driver_breakdown(feats)

        # State machine
        state = self._classify_state(score, in_focus=input.user_state.in_focus_block)
        # Cold-start confidence cap (§7.5). Lifted when score crosses 70 with
        # strong multi-signal evidence — stress is unambiguous, low-conf would
        # silently kill the safety candidate at the orchestrator's threshold.
        cold_start = bool(payload.get("cold_start", False)) or len(self._history) < 7
        strong_signal = (
            score >= 70
            and feats.app_switch_rate >= 10
            and feats.typing_entropy >= 4.5
        )
        if cold_start and not strong_signal:
            confidence = 0.40
        elif cold_start and strong_signal:
            confidence = 0.65
        else:
            confidence = round(min(0.85, 0.50 + 0.05 * len(self._history) / 7), 2)

        # Intervention selection
        intervention = self._select_intervention(score, state, payload, input)

        candidates: List[Candidate] = []
        if intervention and intervention["kind"] != "DO_NOTHING":
            candidates.append(
                Candidate(
                    kind=intervention["kind"],
                    agent=self.name,
                    confidence=confidence,
                    agent_priority=1.0,  # safety-class
                    confirm_required=intervention.get("confirm_required", True),
                    surface=Surface(intervention.get("surface", "WATCH")),
                    args=intervention.get("args", {}),
                    rationale_seed=intervention.get("rationale_seed", ""),
                )
            )

        frag = TraceFragment(
            agent=self.name,
            inputs_summary={
                "rmssd_ms": feats.rmssd_ms,
                "rmssd_z": round(feats.rmssd_z, 2) if feats.rmssd_z is not None else None,
                "switch_rate": feats.app_switch_rate,
                "entropy": feats.typing_entropy,
                "hrv_unavailable": hrv_unavailable,
            },
            decision=intervention["kind"].lower() if intervention else "do_nothing",
            drivers=[f"{d['feature']}={d['value']}" for d in drivers],
            model_low_conf=cold_start,
        )

        # Push to rolling history.
        self._history.append({"ts": input.tick_ts, "score": score})
        if len(self._history) > 96:
            self._history.pop(0)

        out_payload = {
            "load_score": score,
            "drivers": drivers,
            "suggested_intervention": intervention,
            "confidence": confidence,
            "state": state.value,
        }

        return AgentOutput(
            agent=self.name,
            tick_ts=input.tick_ts,
            candidates=candidates,
            payload=out_payload,
            trace_fragment=frag,
        )

    def tools(self) -> List[Dict[str, Any]]:
        feature_schema = {
            "type": "object",
            "properties": {
                name: {"type": ["number", "null"] if name in ("rmssd_ms", "rmssd_z") else "number"}
                for name in WellnessFeatures.feature_names()
            },
        }
        return [
            {
                "name": "compute_load_score",
                "description": "Run the XGBoost regressor on a feature vector.",
                "parameters": {
                    "type": "object",
                    "required": ["features"],
                    "properties": {"features": feature_schema, "hrv_unavailable": {"type": "boolean"}},
                },
            },
            {
                "name": "intervention_select",
                "description": "Pick MUTE_GROUP_30 / BREATHE_478 / NAP_15 / PERMIT_LEISURE.",
                "parameters": {
                    "type": "object",
                    "required": ["score", "context"],
                    "properties": {
                        "score": {"type": "integer", "minimum": 0, "maximum": 100},
                        "context": {"type": "object"},
                    },
                },
            },
            {
                "name": "correlation_check",
                "description": "Spearman ρ between load_score and self_rated_stress.",
                "parameters": {
                    "type": "object",
                    "required": ["samples"],
                    "properties": {
                        "samples": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": [{"type": "number"}, {"type": "integer"}],
                                "minItems": 2,
                                "maxItems": 2,
                            },
                        },
                    },
                },
            },
            {
                "name": "recovery_check",
                "description": "True if load score has dropped >=10 in the recent window.",
                "parameters": {
                    "type": "object",
                    "required": ["history"],
                    "properties": {
                        "history": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["ts", "score"],
                                "properties": {"ts": {"type": "string"}, "score": {"type": "number"}},
                            },
                        },
                    },
                },
            },
        ]

    def handle_tool_call(self, call: ToolCall) -> ToolResult:
        t0 = time.perf_counter()
        try:
            if call.tool == "compute_load_score":
                f = call.args["features"]
                feats = WellnessFeatures(
                    rmssd_ms=f.get("rmssd_ms"),
                    rmssd_z=f.get("rmssd_z"),
                    sleep_debt_min=float(f.get("sleep_debt_min", 0.0)),
                    typing_entropy=float(f.get("typing_entropy", 3.0)),
                    app_switch_rate=int(f.get("app_switch_rate", 4)),
                    notif_dismiss_rate=float(f.get("notif_dismiss_rate", 0.3)),
                    screen_on_min=int(f.get("screen_on_min", 20)),
                    hour_of_day_sin=float(f.get("hour_of_day_sin", 0.0)),
                    hour_of_day_cos=float(f.get("hour_of_day_cos", 1.0)),
                )
                score = self.model.predict_score(feats, hrv_unavailable=bool(call.args.get("hrv_unavailable", False)))
                return self._ok(call, {
                    "load_score": int(round(score)),
                    "drivers": self.model.driver_breakdown(feats),
                }, t0)

            if call.tool == "intervention_select":
                score = int(call.args["score"])
                ctx = call.args.get("context") or {}
                state = self._classify_state(score, in_focus=bool(ctx.get("in_focus_block", False)))
                # Synthesize a payload-like dict to reuse logic.
                fake_input = AgentInput(
                    tick_ts=ctx.get("tick_ts", "2026-05-07T00:00:00+00:00"),
                    agent=self.name,
                    user_state=ctx.get("user_state") or {"load_score": score},
                ) if False else None
                intervention = self._select_intervention(
                    score, state, ctx, _surrogate_user_state(ctx)
                )
                return self._ok(call, intervention or {"kind": "DO_NOTHING"}, t0)

            if call.tool == "correlation_check":
                samples = [(float(s[0]), int(s[1])) for s in call.args["samples"]]
                rho = LoadScoreModel.spearman_rho(samples)
                return self._ok(call, {"rho": round(rho, 3), "n": len(samples)}, t0)

            if call.tool == "recovery_check":
                history = call.args["history"]
                recovered = self._recovery_check_internal(history)
                return self._ok(call, {"recovered": recovered}, t0)

            return ToolResult(call_id=call.call_id, ok=False, error=f"unknown tool: {call.tool}", latency_ms=(time.perf_counter() - t0) * 1000.0)

        except Exception as exc:  # pragma: no cover - defensive
            return ToolResult(
                call_id=call.call_id,
                ok=False,
                error=f"{type(exc).__name__}: {exc}",
                latency_ms=(time.perf_counter() - t0) * 1000.0,
            )

    # ----- internals -----------------------------------------------------

    def _ok(self, call: ToolCall, result: Dict[str, Any], t0: float) -> ToolResult:
        return ToolResult(
            call_id=call.call_id,
            ok=True,
            result=result,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
        )

    @staticmethod
    def _hour_of(tick_ts: str) -> int:
        try:
            dt = datetime.fromisoformat(tick_ts.replace("Z", "+00:00"))
            return dt.hour
        except Exception:
            return 12

    def _classify_state(self, score: int, in_focus: bool) -> WellnessState:
        if in_focus:
            return WellnessState.FOCUSED
        if score >= 70:
            return WellnessState.STRESSED
        if score < 50:
            # check for recent recovery
            if self._is_recovery():
                return WellnessState.RECOVERING
            return WellnessState.BASELINE
        if 50 <= score < 70:
            return WellnessState.BASELINE
        return WellnessState.UNKNOWN

    def _is_recovery(self) -> bool:
        if len(self._history) < 4:
            return False
        recent = [h["score"] for h in self._history[-6:]]
        return max(recent) - min(recent) >= _RECOVERY_DROP and recent[-1] < recent[0]

    def _recovery_check_internal(self, history: List[Dict[str, Any]]) -> bool:
        if len(history) < 4:
            return False
        scores = [float(h["score"]) for h in history[-6:]]
        return max(scores) - min(scores) >= _RECOVERY_DROP and scores[-1] < scores[0]

    def _select_intervention(
        self,
        score: int,
        state: WellnessState,
        payload: Dict[str, Any],
        input: AgentInput,
    ) -> Optional[Dict[str, Any]]:
        # Recovery -> permit leisure (no surface unless asked).
        if state == WellnessState.RECOVERING:
            return {
                "kind": "PERMIT_LEISURE",
                "surface": "PHONE_CARD",
                "confirm_required": False,
                "rationale_seed": "load dropped, recovery confirmed",
                "args": {"window_min": 90},
            }
        if score >= 70:
            # MUTE_GROUP_30 if there's an active group context.
            target_channel = (payload.get("active_channel")
                              or (payload.get("notif_events") or [{}])[0].get("channel"))
            if target_channel:
                return {
                    "kind": "MUTE_GROUP_30",
                    "surface": "WATCH",
                    "confirm_required": True,
                    "rationale_seed": "spike with active group context",
                    "args": {"target_channel": target_channel, "ttl_seconds": 1800},
                }
            return {
                "kind": "BREATHE_478",
                "surface": "WATCH",
                "confirm_required": True,
                "rationale_seed": "stress spike, no active group",
                "args": {"cycles": 4},
            }
        if score >= 60 and (payload.get("sleep_last_night", {}) or {}).get("asleep_min", 420) < 360:
            return {
                "kind": "NAP_15",
                "surface": "PHONE_CARD",
                "confirm_required": True,
                "rationale_seed": "moderate load + short sleep",
                "args": {"duration_min": 15},
            }
        return {"kind": "DO_NOTHING", "surface": "SILENT", "confirm_required": False, "rationale_seed": "below threshold", "args": {}}


def _surrogate_user_state(ctx: Dict[str, Any]) -> AgentInput:
    """Build a stripped AgentInput so _select_intervention can sip from a dict.

    This is a tiny adapter for tool calls — they pass a `context` dict, not a
    full UserState.
    """
    from agents.core.types import UserState

    us = UserState(
        load_score=int(ctx.get("load_score", 50)),
        in_focus_block=bool(ctx.get("in_focus_block", False)),
    )
    return AgentInput(
        tick_ts=ctx.get("tick_ts", "2026-05-07T00:00:00+00:00"),
        agent=AgentName.WELLNESS,
        user_state=us,
        payload={},
    )
