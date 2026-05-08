"""CommsAgent unit tests.

Covers the two worked examples in technical_spec.md §3.1:
- A: Quiet Group Chat (47-message storm, 3 actionable -> BATCH_DIGEST).
- B: Morning Brief inbox triage (12 Gmail threads -> SHOW_BRIEF).

Plus:
- Output schema validation against the AgentOutput / Pydantic model.
- Latency budget assertion (300 ms).
- No-PII-leak in trace fragment.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from agents.comms.agent import CommsAgent, make_call_id
from agents.core.types import (
    AgentInput,
    AgentName,
    AgentOutput,
    Surface,
    ToolCall,
    UserState,
    WellnessState,
    now_iso,
)


FIXTURES = Path(__file__).parent / "fixtures"


def _load_jsonl(name: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Header line is metadata, rest are events. Returns (header, events)."""

    with (FIXTURES / name).open() as f:
        lines = [json.loads(line) for line in f if line.strip()]
    return lines[0], lines[1:]


def _build_input(notif_events, gmail_threads, load_score=50, state=WellnessState.BASELINE) -> AgentInput:
    return AgentInput(
        tick_ts=now_iso(),
        agent=AgentName.COMMS,
        user_state=UserState(load_score=load_score, wellness_state=state),
        payload={"notif_events": notif_events, "gmail_threads": gmail_threads},
    )


# ---------------------------------------------------------------------------
# Worked example A — Quiet Group Chat
# ---------------------------------------------------------------------------


def test_storm_47_yields_batch_digest():
    header, rows = _load_jsonl("storm_47.jsonl")
    notif_events = rows
    inp = _build_input(notif_events, gmail_threads=[], load_score=78, state=WellnessState.STRESSED)

    agent = CommsAgent()
    out = agent.tick_timed(inp)

    assert isinstance(out, AgentOutput)
    assert out.payload["top_suggested_action"] == header["expected"]["top_suggested_action"]
    assert len(out.payload["urgent"]) == header["expected"]["urgent_count"]
    assert out.payload["muted_count"] == header["expected"]["muted_count"]

    # Candidates: BATCH_DIGEST + (because load_score is 78) MUTE_GROUP_30.
    kinds = [c.kind for c in out.candidates]
    assert "BATCH_DIGEST" in kinds
    assert "MUTE_GROUP_30" in kinds

    # Trace fragment exists and contains drivers.
    assert out.trace_fragment is not None
    assert any("volume_47" in d for d in out.trace_fragment.drivers)


# ---------------------------------------------------------------------------
# Worked example B — Morning Brief inbox triage
# ---------------------------------------------------------------------------


def test_gmail_batch_yields_show_brief():
    header, rows = _load_jsonl("gmail_batch.jsonl")
    notif_events = [r for r in rows if r.get("kind") == "notif"]
    gmail_threads = [r for r in rows if r.get("kind") == "gmail"]
    inp = _build_input(notif_events, gmail_threads=gmail_threads, load_score=42)

    agent = CommsAgent()
    out = agent.tick_timed(inp)

    assert out.payload["top_suggested_action"] == header["expected"]["top_suggested_action"]
    assert len(out.payload["urgent"]) == header["expected"]["urgent_count"]
    kinds = [c.kind for c in out.candidates]
    assert "SHOW_BRIEF" in kinds


# ---------------------------------------------------------------------------
# Insta DM and Slack thread sanity
# ---------------------------------------------------------------------------


def test_insta_dm_is_silent():
    header, rows = _load_jsonl("insta_dm.jsonl")
    out = CommsAgent().tick_timed(_build_input(rows, gmail_threads=[]))
    assert out.payload["top_suggested_action"] == header["expected"]["top_suggested_action"]
    assert len(out.candidates) == 0


def test_slack_thread_show_brief():
    header, rows = _load_jsonl("slack_thread.jsonl")
    out = CommsAgent().tick_timed(_build_input(rows, gmail_threads=[]))
    assert out.payload["top_suggested_action"] == header["expected"]["top_suggested_action"]
    assert len(out.payload["urgent"]) == header["expected"]["urgent_count"]


# ---------------------------------------------------------------------------
# Latency budget
# ---------------------------------------------------------------------------


def test_tick_latency_budget():
    header, rows = _load_jsonl("storm_47.jsonl")
    inp = _build_input(rows, gmail_threads=[], load_score=78, state=WellnessState.STRESSED)
    agent = CommsAgent()

    # Run 5 times, take median; spec target: median < 300 ms.
    samples = []
    for _ in range(5):
        t0 = time.perf_counter()
        agent.tick(inp)
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples.sort()
    median = samples[len(samples) // 2]
    assert median < 300.0, f"median tick latency {median:.1f}ms exceeds 300ms budget"


# ---------------------------------------------------------------------------
# No-PII-leak in trace fragment
# ---------------------------------------------------------------------------


def test_trace_fragment_no_pii_leak():
    header, rows = _load_jsonl("storm_47.jsonl")
    inp = _build_input(rows, gmail_threads=[], load_score=78, state=WellnessState.STRESSED)
    out = CommsAgent().tick_timed(inp)

    # Serialize the trace fragment and search for any actual message preview text.
    serialized = json.dumps(out.trace_fragment.model_dump())
    forbidden_substrings = [
        "schema diagram",
        "merge tonight",
        "deploy slot",
        "@you",
    ]
    for s in forbidden_substrings:
        assert s not in serialized, f"PII leak: '{s}' found in trace fragment"


# ---------------------------------------------------------------------------
# Tool call schema validation
# ---------------------------------------------------------------------------


def test_tools_returned_have_required_fields():
    tools = CommsAgent().tools()
    names = {t["name"] for t in tools}
    assert names == {"classify", "draft_reply", "batch_summarize", "snooze", "triage_inbox"}
    for t in tools:
        assert "description" in t and "parameters" in t
        assert t["parameters"]["type"] == "object"


def test_handle_classify_tool_call():
    agent = CommsAgent()
    call = ToolCall(
        call_id=make_call_id(),
        agent=AgentName.COMMS,
        tool="classify",
        args={"item": {"id": "n_x", "app_pkg": "com.whatsapp", "ts": now_iso(), "preview": "@you can you confirm the deadline tomorrow"}},
        ts=now_iso(),
        confirm_required=False,
        expected_surface=Surface.SILENT,
    )
    res = agent.handle_tool_call(call)
    assert res.ok
    assert res.result["intent"] == "ACTIONABLE"
    assert res.result["urgency"] > 0


def test_handle_snooze_tool_call():
    agent = CommsAgent()
    call = ToolCall(
        call_id=make_call_id(),
        agent=AgentName.COMMS,
        tool="snooze",
        args={"item_id": "n_a01", "ttl_seconds": 1800},
        ts=now_iso(),
        confirm_required=True,
    )
    res = agent.handle_tool_call(call)
    assert res.ok and res.result["acked"] is True


# ---------------------------------------------------------------------------
# Output schema strict-shape
# ---------------------------------------------------------------------------


def test_output_round_trip_json():
    header, rows = _load_jsonl("storm_47.jsonl")
    inp = _build_input(rows, gmail_threads=[], load_score=78, state=WellnessState.STRESSED)
    out = CommsAgent().tick_timed(inp)

    serialized = out.model_dump_json()
    rebuilt = AgentOutput.model_validate_json(serialized)
    assert rebuilt.payload["top_suggested_action"] == out.payload["top_suggested_action"]
    assert len(rebuilt.candidates) == len(out.candidates)


# ---------------------------------------------------------------------------
# Hybrid classifier — held-out 20% macro-F1 gate (>=0.85)
# ---------------------------------------------------------------------------


def test_hybrid_classifier_macro_f1_gate():
    """The hybrid pipeline (regex fast-path + sklearn LR) must hit
    macro-F1 >= 0.85 on the stratified 20% holdout of the 500-example
    synthetic dataset. This is the production accuracy gate.
    """
    metrics = CommsAgent().diagnostic_accuracy()
    assert metrics["macro_f1"] >= 0.85, (
        f"hybrid classifier macro-F1 {metrics['macro_f1']:.3f} below 0.85 gate"
    )
    # Per-class sanity: each class should be present in the test split.
    assert set(metrics["per_class"].keys()) == {"ACTIONABLE", "SOCIAL", "BROADCAST", "SPAM"}
    # Each class F1 must beat random (random = 0.25 over 4 balanced classes).
    for label, stats in metrics["per_class"].items():
        assert stats["f1"] >= 0.5, f"{label} F1 {stats['f1']:.3f} too low"


# ---------------------------------------------------------------------------
# Batch summarize and triage_inbox shape
# ---------------------------------------------------------------------------


def test_batch_summarize_shape():
    _, rows = _load_jsonl("storm_47.jsonl")
    out = CommsAgent().batch_summarize(rows)
    assert "actionable" in out and "muted_count" in out and "digest" in out
    assert out["total"] == 47
    # Top 3 actionable rule
    assert len(out["actionable"]) <= 3
    assert out["muted_count"] == 47 - len(out["actionable"])


def test_triage_inbox_shape():
    _, rows = _load_jsonl("slack_thread.jsonl")
    out = CommsAgent().triage_inbox(scope="unread_24h", notif_events=rows)
    # AgentOutput payload contract from agents/core/types.py
    assert set(out.keys()) == {"scope", "urgent", "drafts", "muted_count", "top_suggested_action"}
    assert out["top_suggested_action"] in {"SHOW_BRIEF", "BATCH_DIGEST", "DO_NOTHING"}
    assert isinstance(out["urgent"], list)
    # The slack fixture has exactly one @you mention -> 1 urgent
    assert len(out["urgent"]) == 1


def test_drafter_uses_sender_name():
    """Deterministic drafter must include the sender name in the opener."""
    draft = CommsAgent._template_draft(
        "@you can you push the merge tonight, deadline tomorrow",
        sender_name="Anu",
    )
    assert "Anu" in draft
    # 1-2 sentence guarantee
    assert draft.count(".") <= 4 and len(draft) <= 200
