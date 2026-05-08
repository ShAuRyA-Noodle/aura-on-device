"""Locust scenarios — 100 concurrent triage callers.

Run::

    locust -f web/api/load_test.py --host http://localhost:8000 -u 100 -r 20 -t 1m

The default mix simulates the iOS app's typical traffic during a demo:
~70% comms triage, ~20% wellness load score, ~10% orchestrator ticks.
"""

from __future__ import annotations

import os
import random

from locust import FastHttpUser, between, task

_TOKEN = os.environ.get("AURA_TOKEN", "")
_AUTH_HEADERS = {"Authorization": f"Bearer {_TOKEN}"} if _TOKEN else {}


_NOTIFS = [
    {
        "id": "n_001", "app_pkg": "wa", "channel": "ch_class",
        "preview": "@you viva at 4pm please confirm",
        "intent_hint": "actionable",
        "ts": "2026-05-07T08:30:00+00:00",
    },
    {
        "id": "n_002", "app_pkg": "slack", "channel": "ch_team",
        "preview": "please push the merge before 5",
        "intent_hint": "actionable",
        "ts": "2026-05-07T08:30:00+00:00",
    },
]


class AuraUser(FastHttpUser):
    wait_time = between(0.1, 0.6)

    @task(70)
    def comms_triage(self) -> None:
        self.client.post(
            "/api/comms/triage",
            json={
                "notif_events": random.sample(_NOTIFS, k=random.randint(1, 2)),
                "load_score": random.randint(40, 80),
                "tick_ts": "2026-05-07T08:30:00+00:00",
            },
            headers=_AUTH_HEADERS,
            name="POST /api/comms/triage",
        )

    @task(20)
    def wellness_load(self) -> None:
        self.client.post(
            "/api/wellness/load_score",
            json={
                "rmssd_ms": random.uniform(25.0, 60.0),
                "typing_entropy": random.uniform(2.0, 5.5),
                "app_switch_rate": random.randint(2, 14),
                "sleep_debt_min": random.uniform(0, 200),
                "notif_dismiss_rate": random.uniform(0.0, 0.7),
                "screen_on_min": random.randint(5, 60),
                "tick_ts": "2026-05-07T08:30:00+00:00",
            },
            headers=_AUTH_HEADERS,
            name="POST /api/wellness/load_score",
        )

    @task(10)
    def orchestrator_replay(self) -> None:
        self.client.post(
            "/api/orchestrator/run_replay",
            json={"name": random.choice(["morning_brief", "lecture_focus"])},
            headers=_AUTH_HEADERS,
            name="POST /api/orchestrator/run_replay",
        )

    @task(2)
    def health(self) -> None:
        self.client.get("/health", name="GET /health")
