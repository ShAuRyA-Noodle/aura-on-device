"""CalendarAgent unit tests.

Covers technical_spec.md §3.2 worked examples:
- A: Morning Brief (Rohan) — leave-by alert at 08:15.
- B: Conflict at 4pm — detect overlap, suggest slot.

Plus:
- Conflict precision (no false positives).
- ICS parser.
- Travel heuristic against explicit-minute pass-through.
- Latency budget (350 ms).
- Output schema strict-shape.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

import pytest

from agents.calendar.agent import CalendarAgent
from agents.core.types import (
    AgentInput,
    AgentName,
    AgentOutput,
    Surface,
    ToolCall,
    UserState,
    now_iso,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> Dict[str, Any]:
    with (FIXTURES / name).open() as f:
        return json.load(f)


def _build_input(fx: Dict[str, Any]) -> AgentInput:
    return AgentInput(
        tick_ts=fx["tick_ts"],
        agent=AgentName.CALENDAR,
        user_state=UserState(),
        payload={
            "events_today": fx["events_today"],
            "user_loc": fx.get("user_loc"),
            "preferences": fx.get("preferences", {}),
        },
    )


# --------------------------------------------------------------------------
# Worked example A — Morning Brief
# --------------------------------------------------------------------------


def test_travel_aware_emits_leave_by_alert():
    fx = _load("travel_aware.json")
    out = CalendarAgent().tick_timed(_build_input(fx))
    assert isinstance(out, AgentOutput)
    assert out.payload["next_event"] is not None
    assert out.payload["next_event"]["travel_min"] == fx["expected"]["travel_min"]
    assert out.payload["leave_by_alert"]["event_id"] == fx["expected"]["next_event_id"]
    assert any(c.kind == "LEAVE_BY_ALERT" for c in out.candidates)
    assert out.trace_fragment.decision == "leave_by_alert"


# --------------------------------------------------------------------------
# Worked example B — conflicts at 4pm
# --------------------------------------------------------------------------


def test_conflict_3_detected_and_slot_suggested():
    fx = _load("conflict_3.json")
    out = CalendarAgent().tick_timed(_build_input(fx))
    assert len(out.payload["conflicts"]) == fx["expected"]["conflict_count"]
    assert out.payload["suggestions"]
    assert out.trace_fragment.decision in ("flag_conflict_with_slot", "leave_by_alert")


def test_no_false_positive_conflicts():
    fx = _load("no_conflict.json")
    out = CalendarAgent().tick_timed(_build_input(fx))
    assert out.payload["conflicts"] == []
    assert all(c.kind != "SHOW_BRIEF" or "conflict" not in c.rationale_seed for c in out.candidates)


# --------------------------------------------------------------------------
# Tool surface
# --------------------------------------------------------------------------


def test_tools_listed():
    tools = CalendarAgent().tools()
    names = {t["name"] for t in tools}
    assert names == {
        "detect_conflicts",
        "suggest_slots",
        "auto_decline",
        "travel_aware_alert",
        "parse_ics_attachment",
    }


def test_handle_detect_conflicts_tool():
    fx = _load("conflict_3.json")
    agent = CalendarAgent()
    call = ToolCall(
        call_id="t_" + "a" * 10,
        agent=AgentName.CALENDAR,
        tool="detect_conflicts",
        args={"events": fx["events_today"]},
        ts=now_iso(),
        confirm_required=False,
        expected_surface=Surface.SILENT,
    )
    res = agent.handle_tool_call(call)
    assert res.ok
    assert len(res.result["conflicts"]) == fx["expected"]["conflict_count"]


def test_handle_travel_aware_alert_tool():
    fx = _load("travel_aware.json")
    agent = CalendarAgent()
    call = ToolCall(
        call_id="t_" + "b" * 10,
        agent=AgentName.CALENDAR,
        tool="travel_aware_alert",
        args={"event": fx["events_today"][0], "user_loc": fx["user_loc"], "buffer_min": 15},
        ts=now_iso(),
        confirm_required=False,
    )
    res = agent.handle_tool_call(call)
    assert res.ok
    assert res.result["travel_min"] == 22
    assert res.result["event_id"] == "e_12"


def test_parse_ics_attachment_tool():
    ics = (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "BEGIN:VEVENT\n"
        "UID:invite-001\n"
        "SUMMARY:Project sync with Manish\n"
        "DTSTART:20260507T140000Z\n"
        "DTEND:20260507T150000Z\n"
        "LOCATION:Lab 4\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    agent = CalendarAgent()
    call = ToolCall(
        call_id="t_" + "c" * 10,
        agent=AgentName.CALENDAR,
        tool="parse_ics_attachment",
        args={"ics_text": ics},
        ts=now_iso(),
        confirm_required=False,
    )
    res = agent.handle_tool_call(call)
    assert res.ok
    events = res.result["events"]
    assert len(events) == 1
    assert events[0]["title"] == "Project sync with Manish"


def test_suggest_slots_tool():
    fx = _load("conflict_3.json")
    agent = CalendarAgent()
    call = ToolCall(
        call_id="t_" + "d" * 10,
        agent=AgentName.CALENDAR,
        tool="suggest_slots",
        args={"events": fx["events_today"], "duration_min": 30},
        ts=now_iso(),
        confirm_required=False,
    )
    res = agent.handle_tool_call(call)
    assert res.ok
    assert len(res.result["slots"]) >= 1


def test_auto_decline_tool():
    agent = CalendarAgent()
    event = {"id": "e_5", "title": "Optional sync", "start": "2026-05-07T15:00:00+05:30", "end": "2026-05-07T15:30:00+05:30"}
    call = ToolCall(
        call_id="t_" + "e" * 10,
        agent=AgentName.CALENDAR,
        tool="auto_decline",
        args={"event": event, "reason_template": "focus"},
        ts=now_iso(),
        confirm_required=True,
    )
    res = agent.handle_tool_call(call)
    assert res.ok
    assert "focus" in res.result["draft"].lower() or "block" in res.result["draft"].lower()


# --------------------------------------------------------------------------
# Latency
# --------------------------------------------------------------------------


def test_tick_latency_budget():
    fx = _load("conflict_3.json")
    inp = _build_input(fx)
    agent = CalendarAgent()
    samples = []
    for _ in range(5):
        t0 = time.perf_counter()
        agent.tick(inp)
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples.sort()
    median = samples[len(samples) // 2]
    assert median < 350.0, f"median tick latency {median:.1f}ms exceeds 350ms"


def test_output_round_trip_json():
    fx = _load("travel_aware.json")
    out = CalendarAgent().tick_timed(_build_input(fx))
    serialized = out.model_dump_json()
    rebuilt = AgentOutput.model_validate_json(serialized)
    assert rebuilt.payload["next_event"]["travel_min"] == 22
