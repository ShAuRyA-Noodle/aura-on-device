"""TestClient-based suite for every endpoint.

Asserts schemas, status codes, error paths, and the auth contract.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Meta endpoints
# ---------------------------------------------------------------------------


def test_root(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "aura-local-api"
    assert "/docs" in body["docs"]


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert set(body["agents"].keys()) == {"comms", "calendar", "finance", "wellness"}
    assert "memory" in body and "llm" in body


def test_metrics_prometheus(client: TestClient) -> None:
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "aura_orchestrator_tick_latency_seconds" in body
    assert "aura_http_requests_total" in body


def test_openapi(client: TestClient) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert spec["info"]["title"] == "Aura local API"
    paths = spec["paths"]
    # Every required endpoint shows up in the OpenAPI spec.
    for required in (
        "/api/comms/triage",
        "/api/calendar/conflicts",
        "/api/finance/parse_sms",
        "/api/finance/categorize",
        "/api/wellness/load_score",
        "/api/orchestrator/tick",
        "/api/orchestrator/run_replay",
        "/api/memory/add_node",
        "/api/memory/search",
        "/api/memory/by_time_range",
        "/api/memory/export",
        "/api/memory/audit_log",
        "/health",
    ):
        assert required in paths, f"missing path in OpenAPI: {required}"


# ---------------------------------------------------------------------------
# Comms
# ---------------------------------------------------------------------------


def test_comms_triage(client: TestClient) -> None:
    payload = {
        "notif_events": [
            {
                "id": "n_001", "app_pkg": "wa", "channel": "ch_class",
                "preview": "@you reminder viva at 4pm please confirm",
                "intent_hint": "actionable",
                "ts": "2026-05-07T08:30:00+00:00",
            }
        ],
        "load_score": 60,
        "tick_ts": "2026-05-07T08:30:00+00:00",
    }
    r = client.post("/api/comms/triage", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "urgent" in body and "drafts" in body and "muted_count" in body
    assert isinstance(body["candidates"], list)


def test_comms_triage_invalid(client: TestClient) -> None:
    # extra=forbid catches typos.
    r = client.post("/api/comms/triage", json={"unknown_field": True})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------


def test_calendar_conflicts(client: TestClient) -> None:
    payload = {
        "events_today": [
            {"id": "ev_a", "title": "Standup",
             "start": "2026-05-07T09:00:00+00:00", "end": "2026-05-07T09:30:00+00:00"},
            {"id": "ev_b", "title": "Quick chat",
             "start": "2026-05-07T09:15:00+00:00", "end": "2026-05-07T09:45:00+00:00"},
        ],
        "buffer_minutes": 10,
        "tick_ts": "2026-05-07T08:30:00+00:00",
    }
    r = client.post("/api/calendar/conflicts", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "conflicts" in body
    assert len(body["conflicts"]) >= 1


# ---------------------------------------------------------------------------
# Finance
# ---------------------------------------------------------------------------


def test_finance_parse_sms(client: TestClient) -> None:
    payload = {
        "sms": [
            "Sent Rs.350.00 from A/c **1234 to ZOMATO via UPI on 07-MAY",
            "INR 250.00 spent on ICICI Bank Card XX9921 at SWIGGY on 07-May-26",
        ],
        "fallback_year": 2026,
    }
    r = client.post("/api/finance/parse_sms", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 0
    assert "transactions" in body


def test_finance_categorize(client: TestClient) -> None:
    r = client.post(
        "/api/finance/categorize",
        json={"merchants": ["zomato", "uber", "bigbasket"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 3


# ---------------------------------------------------------------------------
# Wellness
# ---------------------------------------------------------------------------


def test_wellness_load_score(client: TestClient) -> None:
    r = client.post(
        "/api/wellness/load_score",
        json={
            "rmssd_ms": 28.0, "typing_entropy": 4.7, "app_switch_rate": 12,
            "sleep_debt_min": 120.0, "notif_dismiss_rate": 0.5, "screen_on_min": 40,
            "tick_ts": "2026-05-07T08:30:00+00:00",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert 0 <= body["load_score"] <= 100
    assert isinstance(body["drivers"], list)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def test_orchestrator_tick(client: TestClient) -> None:
    r = client.post(
        "/api/orchestrator/tick",
        json={
            "wellness": {
                "rmssd_ms": 30.0, "typing_entropy": 4.7, "app_switch_rate": 12,
                "sleep_debt_min": 120.0, "notif_dismiss_rate": 0.5, "screen_on_min": 40,
                "tick_ts": "2026-05-07T08:30:00+00:00",
            }
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "trace" in body and body["trace"]["trace_id"].startswith("tr_")
    assert "agent_outputs" in body


@pytest.mark.parametrize("name", ["morning_brief", "lecture_focus", "spend_anomaly", "recovery"])
def test_orchestrator_run_replay(client: TestClient, name: str) -> None:
    r = client.post("/api/orchestrator/run_replay", json={"name": name})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["chosen_kind"]
    assert body["trace"]["trace_id"].startswith("tr_")


def test_orchestrator_run_replay_invalid_name(client: TestClient) -> None:
    r = client.post("/api/orchestrator/run_replay", json={"name": "does_not_exist"})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------


def test_memory_add_search_and_export(client: TestClient) -> None:
    r = client.post(
        "/api/memory/add_node",
        json={"type": "Conversation", "data": {"label": "morning standup notes"}},
    )
    assert r.status_code == 200
    nid = r.json()["node_id"]
    assert nid.startswith("n_")

    r = client.post("/api/memory/search", json={"query": "morning standup", "k": 5})
    assert r.status_code == 200
    body = r.json()
    assert "hits" in body

    r = client.get("/api/memory/export")
    assert r.status_code == 200
    export = r.json()
    assert export["export_version"]
    assert "nodes" in export and "edges" in export and "traces" in export

    r = client.get("/api/memory/audit_log", params={"limit": 50})
    assert r.status_code == 200
    audit = r.json()
    assert "rows" in audit


def test_memory_delete_by_time_range(client: TestClient) -> None:
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    r = client.delete(
        "/api/memory/by_time_range",
        params={"from_ms": 0, "to_ms": now + 1_000_000},
    )
    assert r.status_code == 200
    assert "affected" in r.json()


def test_memory_delete_invalid_range(client: TestClient) -> None:
    r = client.delete("/api/memory/by_time_range", params={"from_ms": 5000, "to_ms": 1000})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def test_auth_required(monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-import the app with auth ENABLED and verify a 401 without a token."""
    monkeypatch.setenv("AURA_DISABLE_AUTH", "0")
    monkeypatch.setenv("AURA_TOKEN_FILE", os.path.join(os.path.dirname(__file__), ".test_tok"))
    # Reload module so the dependency closure picks up the env change.
    import importlib

    import web.api.main as main_mod

    importlib.reload(main_mod)
    with TestClient(main_mod.app) as c:
        # No token at all -> 401.
        r = c.post("/api/comms/triage", json={"notif_events": [], "load_score": 50})
        assert r.status_code == 401

        token_path = os.environ["AURA_TOKEN_FILE"]
        assert os.path.exists(token_path)
        token = open(token_path).read().strip()
        r = c.post(
            "/api/comms/triage",
            json={"notif_events": [], "load_score": 50},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
    # Cleanup
    try:
        os.unlink(os.environ["AURA_TOKEN_FILE"])
    except OSError:
        pass
    monkeypatch.setenv("AURA_DISABLE_AUTH", "1")
    importlib.reload(main_mod)
