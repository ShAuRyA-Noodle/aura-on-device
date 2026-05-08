"""CalendarAgent — interval-tree conflicts + travel-aware leave-by alerts.

Implements technical_spec.md §3.2.

Design notes
------------
- Conflict detection is a pure interval-tree-style sweep — O(n log n) sort then
  linear scan. We never use Phi-3 for conflict detection; it would be both
  overkill and a precision risk. Spec target: P=1.00, R>=0.95.
- Travel time uses a `local_heuristic` by default: ``dist_km / mode_speed``.
  Production wires up Google Distance Matrix; this stub is identical-shape
  so the iOS / Android port can swap providers.
- ``parse_ics_attachment`` is a thin parser tolerant of CRLF / LF, single VEVENT
  blocks. Multi-event ICS is supported but rare for calendar invites.
- The agent emits a single high-value Candidate per tick: either
  ``LEAVE_BY_ALERT`` if the next event has a non-trivial commute, or
  ``SHOW_BRIEF`` if there are useful conflicts / suggestions. Both default
  to auto-execute (passive surfaces) per spec §4.4.
"""

from __future__ import annotations

import math
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

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
)


# ---------------------------------------------------------------------------
# Helpers — datetime parsing and travel heuristic
# ---------------------------------------------------------------------------


def _parse_iso(s: str) -> datetime:
    """Parse ISO-8601, accepting ``Z`` and naive timestamps (assume UTC)."""
    s = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Great-circle distance in kilometres; tolerable for sub-50km city hops."""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


# Mode speeds in km/h. Tuned for Bangalore / Patiala traffic (matches spec §3.2).
_MODE_SPEED_KMH = {"walk": 4.5, "metro": 28.0, "bike": 18.0, "cab": 22.0, "car": 22.0}


def _travel_minutes(
    from_loc: Optional[Tuple[float, float]],
    to_loc: Optional[Tuple[float, float]],
    mode: str = "cab",
    explicit_min: Optional[int] = None,
) -> int:
    """Estimate travel time. Provider-agnostic local heuristic."""
    if explicit_min is not None:
        return int(explicit_min)
    if not from_loc or not to_loc:
        return 0
    km = _haversine_km(from_loc, to_loc)
    speed = _MODE_SPEED_KMH.get(mode, 22.0)
    return int(round((km / speed) * 60))


# ---------------------------------------------------------------------------
# ICS parsing
# ---------------------------------------------------------------------------


_ICS_VEVENT = re.compile(r"BEGIN:VEVENT(.*?)END:VEVENT", re.DOTALL | re.IGNORECASE)
_ICS_FIELD = re.compile(
    r"^([A-Z\-]+)(?:;[^:]*)?:(.+)$", re.MULTILINE
)


def _ics_dt(value: str) -> datetime:
    """Parse ``20260507T090000`` or ``20260507T090000Z`` style stamps.

    Hand-rolled because ``datetime.strptime`` triggers locale init via
    ``_strptime`` which in turn ``import calendar`` — and our package name
    ``agents.calendar`` shadows the stdlib ``calendar`` when pytest inserts
    ``agents/calendar/`` onto ``sys.path``.
    """
    s = value.strip().rstrip("Z")
    if "T" in s:
        date_part, time_part = s.split("T", 1)
    else:
        date_part, time_part = s, "000000"
    if len(date_part) != 8 or not date_part.isdigit():
        raise ValueError(f"bad ICS date: {value!r}")
    if len(time_part) < 6 or not time_part[:6].isdigit():
        raise ValueError(f"bad ICS time: {value!r}")
    y, mo, d = int(date_part[:4]), int(date_part[4:6]), int(date_part[6:8])
    h, mi, se = int(time_part[:2]), int(time_part[2:4]), int(time_part[4:6])
    return datetime(y, mo, d, h, mi, se, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class CalendarAgent(Agent):
    """Per technical_spec.md §3.2."""

    name = AgentName.CALENDAR
    latency_budget_ms = 350

    TOOLS = (
        "detect_conflicts",
        "suggest_slots",
        "auto_decline",
        "travel_aware_alert",
        "parse_ics_attachment",
    )

    # ---- core public API ------------------------------------------------

    def tick(self, input: AgentInput) -> AgentOutput:
        events = list(input.payload.get("events_today", []))
        user_loc = input.payload.get("user_loc")
        prefs = input.payload.get("preferences", {}) or {}
        buffer_min = int(prefs.get("buffer_minutes", 15))

        # Sort by start.
        events_sorted = sorted(events, key=lambda e: _parse_iso(e["start"]))

        # Conflicts.
        conflicts = self._detect_conflicts_internal(events_sorted)

        # Next event leave-by.
        now = _parse_iso(input.tick_ts)
        next_event = next(
            (e for e in events_sorted if _parse_iso(e["end"]) > now),
            None,
        )

        next_event_out: Optional[Dict[str, Any]] = None
        leave_by_alert: Optional[Dict[str, Any]] = None
        travel_min = 0
        if next_event is not None:
            ev_loc = next_event.get("loc_coords")
            travel_min = _travel_minutes(
                user_loc and (user_loc.get("lat"), user_loc.get("lon")),
                ev_loc and (ev_loc.get("lat"), ev_loc.get("lon")),
                mode=next_event.get("mode", "cab"),
                explicit_min=next_event.get("travel_min"),
            )
            start = _parse_iso(next_event["start"])
            leave_by = start - timedelta(minutes=travel_min + buffer_min)
            next_event_out = {
                "id": next_event["id"],
                "leave_by": leave_by.isoformat(),
                "travel_min": travel_min,
            }
            # Alert ~15 min before leave_by.
            leave_by_alert = {
                "event_id": next_event["id"],
                "alert_at": (leave_by - timedelta(minutes=15)).isoformat(),
            }

        # Suggestions: free 30-minute slots after a conflict.
        suggestions: List[Dict[str, Any]] = []
        if conflicts:
            suggestions = self._suggest_slots_internal(events_sorted, duration_min=30)

        payload = {
            "next_event": next_event_out,
            "conflicts": conflicts,
            "suggestions": suggestions,
            "leave_by_alert": leave_by_alert,
        }

        # Build candidates.
        candidates: List[Candidate] = []
        if next_event_out and travel_min >= 10:
            candidates.append(
                Candidate(
                    kind="LEAVE_BY_ALERT",
                    agent=self.name,
                    confidence=0.85,
                    agent_priority=0.8,
                    confirm_required=False,
                    surface=Surface.PHONE_CARD,
                    args={"event_id": next_event_out["id"], "leave_by": next_event_out["leave_by"], "travel_min": travel_min},
                    rationale_seed=f"travel_{travel_min}min next event",
                )
            )
        if conflicts:
            candidates.append(
                Candidate(
                    kind="SHOW_BRIEF",
                    agent=self.name,
                    confidence=0.75,
                    agent_priority=0.8,
                    confirm_required=False,
                    surface=Surface.PHONE_CARD,
                    args={"conflict_count": len(conflicts), "first_pair": conflicts[0]["pair"]},
                    rationale_seed=f"{len(conflicts)} conflict(s)",
                )
            )

        decision = "leave_by_alert" if leave_by_alert else (
            "flag_conflict_with_slot" if conflicts else "do_nothing"
        )
        drivers: List[str] = []
        if next_event_out:
            drivers.append(f"travel_{travel_min}min")
            drivers.append(f"buffer_{buffer_min}min")
        if conflicts:
            drivers.append(f"conflict_count_{len(conflicts)}")
        if not drivers:
            drivers.append("no_events")

        frag = TraceFragment(
            agent=self.name,
            inputs_summary={"event_count": len(events), "has_user_loc": bool(user_loc)},
            decision=decision,
            drivers=drivers,
        )

        return AgentOutput(
            agent=self.name,
            tick_ts=input.tick_ts,
            candidates=candidates,
            payload=payload,
            trace_fragment=frag,
        )

    def tools(self) -> List[Dict[str, Any]]:
        event_schema = {
            "type": "object",
            "required": ["id", "start", "end"],
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "start": {"type": "string", "format": "date-time"},
                "end": {"type": "string", "format": "date-time"},
                "loc": {"type": "string"},
                "loc_coords": {
                    "type": "object",
                    "properties": {
                        "lat": {"type": "number"},
                        "lon": {"type": "number"},
                    },
                },
                "attendees": {"type": "integer", "minimum": 0},
                "mode": {"enum": ["walk", "metro", "bike", "cab", "car"]},
                "travel_min": {"type": "integer", "minimum": 0},
            },
        }
        return [
            {
                "name": "detect_conflicts",
                "description": "Return overlapping pairs in a list of events.",
                "parameters": {
                    "type": "object",
                    "required": ["events"],
                    "properties": {"events": {"type": "array", "items": event_schema}},
                },
            },
            {
                "name": "suggest_slots",
                "description": "Suggest free slots given constraints.",
                "parameters": {
                    "type": "object",
                    "required": ["events", "duration_min"],
                    "properties": {
                        "events": {"type": "array", "items": event_schema},
                        "duration_min": {"type": "integer", "minimum": 5, "maximum": 240},
                        "after": {"type": "string", "format": "date-time"},
                    },
                },
            },
            {
                "name": "auto_decline",
                "description": "Draft a polite decline reason for an event.",
                "parameters": {
                    "type": "object",
                    "required": ["event", "reason_template"],
                    "properties": {
                        "event": event_schema,
                        "reason_template": {"enum": ["conflict", "travel", "focus"]},
                    },
                },
            },
            {
                "name": "travel_aware_alert",
                "description": "Compute leave-by time given user_loc and event.",
                "parameters": {
                    "type": "object",
                    "required": ["event"],
                    "properties": {
                        "event": event_schema,
                        "user_loc": {
                            "type": "object",
                            "properties": {
                                "lat": {"type": "number"},
                                "lon": {"type": "number"},
                            },
                        },
                        "buffer_min": {"type": "integer", "minimum": 0, "maximum": 120},
                    },
                },
            },
            {
                "name": "parse_ics_attachment",
                "description": "Parse a single VEVENT ICS payload and return events.",
                "parameters": {
                    "type": "object",
                    "required": ["ics_text"],
                    "properties": {"ics_text": {"type": "string"}},
                },
            },
        ]

    def handle_tool_call(self, call: ToolCall) -> ToolResult:
        t0 = time.perf_counter()
        try:
            if call.tool == "detect_conflicts":
                events = call.args["events"]
                conflicts = self._detect_conflicts_internal(
                    sorted(events, key=lambda e: _parse_iso(e["start"]))
                )
                return self._ok(call, {"conflicts": conflicts}, t0)

            if call.tool == "suggest_slots":
                events = sorted(call.args["events"], key=lambda e: _parse_iso(e["start"]))
                slots = self._suggest_slots_internal(
                    events,
                    duration_min=int(call.args.get("duration_min", 30)),
                    after=call.args.get("after"),
                )
                return self._ok(call, {"slots": slots}, t0)

            if call.tool == "auto_decline":
                event = call.args["event"]
                reason = call.args.get("reason_template", "conflict")
                draft = {
                    "conflict": f"Conflict with another commitment at {event.get('start','')}.",
                    "travel": f"Travel doesn't permit attending {event.get('title','this')} on time.",
                    "focus": "Holding a focus block this hour. Can we reschedule?",
                }[reason]
                return self._ok(call, {"draft": draft, "subject": "RE: " + event.get("title", "Decline")}, t0)

            if call.tool == "travel_aware_alert":
                event = call.args["event"]
                user_loc = call.args.get("user_loc")
                ev_loc = event.get("loc_coords")
                travel_min = _travel_minutes(
                    user_loc and (user_loc.get("lat"), user_loc.get("lon")),
                    ev_loc and (ev_loc.get("lat"), ev_loc.get("lon")),
                    mode=event.get("mode", "cab"),
                    explicit_min=event.get("travel_min"),
                )
                buffer_min = int(call.args.get("buffer_min", 15))
                start = _parse_iso(event["start"])
                leave_by = start - timedelta(minutes=travel_min + buffer_min)
                return self._ok(
                    call,
                    {
                        "event_id": event["id"],
                        "leave_by": leave_by.isoformat(),
                        "travel_min": travel_min,
                    },
                    t0,
                )

            if call.tool == "parse_ics_attachment":
                events = self._parse_ics_internal(call.args["ics_text"])
                return self._ok(call, {"events": events}, t0)

            return ToolResult(call_id=call.call_id, ok=False, error=f"unknown tool: {call.tool}", latency_ms=(time.perf_counter() - t0) * 1000.0)

        except Exception as exc:  # pragma: no cover - defensive
            return ToolResult(
                call_id=call.call_id,
                ok=False,
                error=f"{type(exc).__name__}: {exc}",
                latency_ms=(time.perf_counter() - t0) * 1000.0,
            )

    # ---- internals ------------------------------------------------------

    def _ok(self, call: ToolCall, result: Dict[str, Any], t0: float) -> ToolResult:
        return ToolResult(
            call_id=call.call_id,
            ok=True,
            result=result,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
        )

    @staticmethod
    def _detect_conflicts_internal(events_sorted: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """O(n log n) sweep. Two events conflict if their [start,end) overlap."""
        conflicts: List[Dict[str, Any]] = []
        active: List[Dict[str, Any]] = []
        for ev in events_sorted:
            ev_start = _parse_iso(ev["start"])
            ev_end = _parse_iso(ev["end"])
            # purge active where end <= ev_start
            active = [a for a in active if _parse_iso(a["end"]) > ev_start]
            for a in active:
                a_start = _parse_iso(a["start"])
                a_end = _parse_iso(a["end"])
                # genuine overlap
                if a_start < ev_end and ev_start < a_end:
                    overlap_min = int(
                        (min(a_end, ev_end) - max(a_start, ev_start)).total_seconds() / 60
                    )
                    conflicts.append({"pair": [a["id"], ev["id"]], "overlap_min": overlap_min})
            active.append(ev)
        return conflicts

    @staticmethod
    def _suggest_slots_internal(
        events_sorted: List[Dict[str, Any]],
        duration_min: int = 30,
        after: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Free slots = gaps >= duration_min. Bounded to one slot today."""
        slots: List[Dict[str, Any]] = []
        if not events_sorted:
            return slots
        floor = _parse_iso(after) if after else _parse_iso(events_sorted[0]["start"])
        for i in range(len(events_sorted) - 1):
            cur_end = _parse_iso(events_sorted[i]["end"])
            nxt_start = _parse_iso(events_sorted[i + 1]["start"])
            slot_start = max(floor, cur_end)
            if (nxt_start - slot_start).total_seconds() >= duration_min * 60:
                slots.append({
                    "slot_start": slot_start.isoformat(),
                    "slot_end": (slot_start + timedelta(minutes=duration_min)).isoformat(),
                    "reason": "first free gap after conflict",
                })
                break
        if not slots:
            last_end = _parse_iso(events_sorted[-1]["end"])
            slots.append({
                "slot_start": last_end.isoformat(),
                "slot_end": (last_end + timedelta(minutes=duration_min)).isoformat(),
                "reason": "after last event",
            })
        return slots

    @staticmethod
    def _parse_ics_internal(ics_text: str) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        for block in _ICS_VEVENT.findall(ics_text):
            fields = {m.group(1).upper(): m.group(2).strip() for m in _ICS_FIELD.finditer(block)}
            if "DTSTART" not in fields or "DTEND" not in fields:
                continue
            try:
                start = _ics_dt(fields["DTSTART"])
                end = _ics_dt(fields["DTEND"])
            except ValueError:
                continue
            events.append({
                "id": fields.get("UID", f"ics_{len(events):03d}"),
                "title": fields.get("SUMMARY", "(untitled)"),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "loc": fields.get("LOCATION", ""),
                "attendees": int(fields.get("ATTENDEES", "1") or 1) if fields.get("ATTENDEES", "").isdigit() else 1,
            })
        return events
