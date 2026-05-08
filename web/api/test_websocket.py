"""WebSocket smoke tests for /ws/trace.

Strategy
--------
Starlette's TestClient WebSocket session is synchronous, so we cannot run
"send + receive concurrently" the way a real client would. Instead we lean
on the in-process trace bus's small replay buffer: every newly-connected
subscriber gets the last 32 events. The test fires a replay (which fans out
events into the bus history), then opens a WS, and asserts the expected
event sequence is replayed.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_ws_trace_replays_recent_history(client: TestClient) -> None:
    # Trigger the orchestrator first — events are queued in the bus history.
    r = client.post("/api/orchestrator/run_replay", json={"name": "morning_brief"})
    assert r.status_code == 200, r.text

    # Now subscribe — the bus replays the last batch of events.
    seen_types: list[str] = []
    with client.websocket_connect("/ws/trace") as ws:
        hello = ws.receive_json()
        assert hello["type"] == "hello"
        # Pull up to ~10 replayed events.
        for _ in range(10):
            try:
                evt = ws.receive_json()
            except Exception:
                break
            seen_types.append(evt.get("type", ""))
            if evt.get("type") == "tick.end":
                break

    assert "tick.start" in seen_types
    assert "agent.output" in seen_types
    assert "policy.decision" in seen_types
    assert "trace.emitted" in seen_types
    assert "tick.end" in seen_types


def test_ws_trace_hello_envelope(client: TestClient) -> None:
    with client.websocket_connect("/ws/trace") as ws:
        hello = ws.receive_json()
        assert hello["type"] == "hello"
        assert "version" in hello
        assert "subscriber_count" in hello


def test_ws_trace_carries_valid_trace_id(client: TestClient) -> None:
    client.post("/api/orchestrator/run_replay", json={"name": "lecture_focus"})
    with client.websocket_connect("/ws/trace") as ws:
        ws.receive_json()  # hello
        # Drain until we see a trace.emitted envelope.
        for _ in range(15):
            evt = ws.receive_json()
            if evt.get("type") == "trace.emitted":
                trace = evt["trace"]
                assert trace["trace_id"].startswith("tr_")
                assert "candidates" in trace
                return
        raise AssertionError("trace.emitted not seen within 15 events")
