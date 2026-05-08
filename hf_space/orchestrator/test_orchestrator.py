"""Orchestrator end-to-end tests.

Covers:
- Plan §11 stress-driven mute: load >= 70 + active channel -> MUTE_GROUP_30 chosen.
- Spec §4.3 hard caps: 4 surfaces in a day -> 4th becomes do_nothing with `cap_daily`.
- DND policy: surfaces during DND drop except WATCH safety candidates.
- Trace schema validation against trace.v1.json.
- Tool schema validation rejects malformed ToolCalls.
- Monday Brief replay (replays/monday_brief.replay.json).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pytest

from agents.calendar.agent import CalendarAgent
from agents.comms.agent import CommsAgent
from agents.core.types import (
    AgentName,
    Surface,
    ToolCall,
    UserState,
    WellnessState,
    now_iso,
)
from agents.wellness.agent import WellnessAgent
from orchestrator.graph import Orchestrator, OrchestratorState
from orchestrator.policy import ActionHistory, DNDWindow, Policy
from orchestrator.tools import (
    TOOLCALL_ENVELOPE_SCHEMA,
    ToolValidationError,
    build_tool_registry,
    validate_tool_call,
)
from orchestrator.trace import TRACE_V1_SCHEMA, emit_trace, pretty_render, validate_trace


REPLAYS = Path(__file__).parent / "replays"


# ---------------------------------------------------------------------------
# Plan §11 stress-driven mute
# ---------------------------------------------------------------------------


def test_stress_driven_mute_ranks_top():
    orch = Orchestrator(agents=[CommsAgent(), CalendarAgent(), WellnessAgent()])
    user_state = UserState(
        load_score=78,
        wellness_state=WellnessState.STRESSED,
        in_focus_block=False,
    )
    payloads = {
        "comms": {
            "notif_events": [
                {"id": f"n_{i:03d}", "app_pkg": "com.whatsapp", "channel": "group:Thapar-DSA-Project", "sender_hash": f"h_{i}", "preview": "lol", "ts": "2026-05-07T22:30:00+05:30"}
                for i in range(45)
            ]
            + [
                {"id": "n_999", "app_pkg": "com.whatsapp", "channel": "group:Thapar-DSA-Project", "sender_hash": "h_anu", "preview": "@you can you confirm the schema diagram", "ts": "2026-05-07T22:30:00+05:30"},
            ],
            "gmail_threads": [],
        },
        "calendar": {"events_today": []},
        "wellness": {
            "hrv_window": {"rmssd_ms": 28.4, "samples": 12, "window_min": 5},
            "sleep_last_night": {"asleep_min": 312},
            "typing_entropy_60s": 4.91,
            "app_switch_rate_60s": 14,
            "notif_dismiss_rate_60m": 0.78,
            "screen_on_min_60m": 47,
            "personal_baseline": {"rmssd_p50": 38.2, "rmssd_p10": 22.1},
            "active_channel": "group:Thapar-DSA-Project",
        },
    }
    res = orch.tick(user_state=user_state, agent_payloads=payloads, tick_ts="2026-05-07T22:31:47+05:30")
    assert res.final_state == OrchestratorState.COOLDOWN
    assert res.chosen_kind == "MUTE_GROUP_30"
    # Trace schema valid
    validate_trace(res.trace)


# ---------------------------------------------------------------------------
# Spec §4.3 daily cap
# ---------------------------------------------------------------------------


def test_daily_cap_blocks_fourth_surface():
    from datetime import timedelta as _td

    history = ActionHistory()
    now = datetime(2026, 5, 7, 12, 0, tzinfo=timezone.utc)
    # 3 non-safety surfaces already today, spread over the day so the
    # 30-min window cap doesn't fire first.
    history.append(now - _td(hours=6), "BATCH_DIGEST")
    history.append(now - _td(hours=4), "LEAVE_BY_ALERT")
    history.append(now - _td(hours=2), "SURFACE_ANOMALY")
    policy = Policy(silence_budget_total=3)
    from agents.core.types import Candidate

    cand = Candidate(
        kind="SHOW_BRIEF",
        agent=AgentName.COMMS,
        confidence=0.9,
        agent_priority=0.7,
        confirm_required=False,
        surface=Surface.PHONE_CARD,
    )
    decision = policy.decide([cand], UserState(), history, DNDWindow(), now)
    assert decision.chosen is None
    assert decision.cap_reason == "cap_daily"


def test_safety_actions_uncapped():
    history = ActionHistory()
    now = datetime(2026, 5, 7, 12, 0, tzinfo=timezone.utc)
    for _ in range(3):
        history.append(now, "SHOW_BRIEF")
    policy = Policy(silence_budget_total=3)
    from agents.core.types import Candidate

    cand = Candidate(
        kind="MUTE_GROUP_30",
        agent=AgentName.WELLNESS,
        confidence=0.85,
        agent_priority=1.0,
        confirm_required=True,
        surface=Surface.WATCH,
    )
    decision = policy.decide([cand], UserState(wellness_state=WellnessState.STRESSED), history, DNDWindow(), now)
    assert decision.chosen is not None
    assert decision.chosen.kind == "MUTE_GROUP_30"


# ---------------------------------------------------------------------------
# DND
# ---------------------------------------------------------------------------


def test_dnd_drops_phone_card_keeps_watch():
    history = ActionHistory()
    now = datetime(2026, 5, 7, 23, 30, tzinfo=timezone.utc)
    dnd = DNDWindow(active=True)
    policy = Policy()
    from agents.core.types import Candidate

    phone = Candidate(
        kind="SHOW_BRIEF",
        agent=AgentName.COMMS,
        confidence=0.9,
        agent_priority=0.7,
        confirm_required=False,
        surface=Surface.PHONE_CARD,
    )
    watch_safety = Candidate(
        kind="MUTE_GROUP_30",
        agent=AgentName.WELLNESS,
        confidence=0.9,
        agent_priority=1.0,
        confirm_required=True,
        surface=Surface.WATCH,
    )
    decision = policy.decide([phone, watch_safety], UserState(wellness_state=WellnessState.STRESSED), history, dnd, now)
    assert decision.chosen is not None
    assert decision.chosen.kind == "MUTE_GROUP_30"


# ---------------------------------------------------------------------------
# Trace schema validation
# ---------------------------------------------------------------------------


def test_trace_v1_schema_validates_emitted_trace():
    trace = emit_trace(
        trigger={"source": "phone_unlock", "value": {"hour": 7.75}},
        signals=[{"k": "next_event", "v": "DSA Quiz"}],
        scored=[],
        chosen_action=None,
        rationale="no candidate",
    )
    validate_trace(trace)
    rendered = pretty_render(trace)
    assert "Trace tr_" in rendered
    assert "Why now:" in rendered


def test_trace_schema_top_level_shape():
    assert TRACE_V1_SCHEMA["required"] == [
        "trace_id", "ts", "trigger", "signals", "candidates", "chosen", "rationale", "confirm_required", "outcome"
    ]


# ---------------------------------------------------------------------------
# Tool schema
# ---------------------------------------------------------------------------


def test_toolcall_envelope_validates():
    registry = build_tool_registry([CommsAgent(), CalendarAgent(), WellnessAgent()])
    call = ToolCall(
        call_id="t_" + "a" * 10,
        agent=AgentName.COMMS,
        tool="snooze",
        args={"item_id": "n_1", "ttl_seconds": 1800},
        ts=now_iso(),
        confirm_required=True,
    )
    validate_tool_call(call, registry)


def test_toolcall_with_bad_args_rejected():
    registry = build_tool_registry([CommsAgent()])
    bad = ToolCall(
        call_id="t_" + "b" * 10,
        agent=AgentName.COMMS,
        tool="snooze",
        args={"item_id": "n_1"},  # missing ttl_seconds
        ts=now_iso(),
        confirm_required=True,
    )
    with pytest.raises(ToolValidationError):
        validate_tool_call(bad, registry)


def test_toolcall_unknown_tool_rejected():
    registry = build_tool_registry([CommsAgent()])
    bad = ToolCall(
        call_id="t_" + "c" * 10,
        agent=AgentName.COMMS,
        tool="not_a_real_tool",
        args={},
        ts=now_iso(),
        confirm_required=True,
    )
    with pytest.raises(ToolValidationError):
        validate_tool_call(bad, registry)


def test_envelope_schema_canonical_shape():
    assert TOOLCALL_ENVELOPE_SCHEMA["required"] == [
        "call_id", "agent", "tool", "args", "ts", "confirm_required"
    ]


# ---------------------------------------------------------------------------
# Monday Brief replay
# ---------------------------------------------------------------------------


def test_monday_brief_replay_chooses_calendar_or_comms():
    fx = json.loads((REPLAYS / "monday_brief.replay.json").read_text())
    user_state = UserState(**fx["user_state"])
    orch = Orchestrator(agents=[CommsAgent(), CalendarAgent(), WellnessAgent()])
    res = orch.tick(
        user_state=user_state,
        agent_payloads=fx["agent_payloads"],
        tick_ts=fx["tick_ts"],
        trigger={"source": "phone_unlock", "value": {"hour": 7.75}},
    )
    assert res.chosen_kind in fx["expected"]["chosen_in"]
    assert res.chosen_kind not in fx["expected"]["must_not_choose"]
    validate_trace(res.trace)


# ---------------------------------------------------------------------------
# Recovering state blocks proactive
# ---------------------------------------------------------------------------


def test_recovering_state_blocks_proactive():
    history = ActionHistory()
    now = datetime(2026, 5, 7, 14, 0, tzinfo=timezone.utc)
    policy = Policy()
    from agents.core.types import Candidate

    cand = Candidate(
        kind="SHOW_BRIEF",
        agent=AgentName.COMMS,
        confidence=0.9,
        agent_priority=0.7,
        confirm_required=False,
        surface=Surface.PHONE_CARD,
    )
    decision = policy.decide(
        [cand],
        UserState(wellness_state=WellnessState.RECOVERING),
        history,
        DNDWindow(),
        now,
        recovering_since=now,
    )
    assert decision.chosen is None
    assert decision.cap_reason == "cap_recovering"
