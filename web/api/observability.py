"""Prometheus-format metrics for the local daemon.

The orchestrator imports `record_*` helpers directly when available — but
calls are no-ops if the metrics registry hasn't been initialised. This keeps
the agent stack free of operational concerns.
"""

from __future__ import annotations

from typing import Any

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

REGISTRY = CollectorRegistry()

TICK_LATENCY = Histogram(
    "aura_orchestrator_tick_latency_seconds",
    "End-to-end orchestrator tick latency in seconds.",
    buckets=(0.025, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0),
    registry=REGISTRY,
)

TOOL_CALLS = Counter(
    "aura_tool_calls_total",
    "Tool invocations by agent and outcome.",
    labelnames=("agent", "tool", "outcome"),
    registry=REGISTRY,
)

SILENCE_REFUNDS = Counter(
    "aura_silence_budget_refunds_total",
    "Times the orchestrator refunded a Silence Budget surface.",
    registry=REGISTRY,
)

WS_CONNECTIONS = Gauge(
    "aura_ws_connections_active",
    "Active /ws/trace WebSocket clients.",
    registry=REGISTRY,
)

REQUEST_LATENCY = Histogram(
    "aura_http_request_latency_seconds",
    "HTTP request latency by route.",
    labelnames=("method", "route", "status"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=REGISTRY,
)

REQUEST_COUNT = Counter(
    "aura_http_requests_total",
    "HTTP requests by method, route and status.",
    labelnames=("method", "route", "status"),
    registry=REGISTRY,
)


def record_tick(latency_seconds: float) -> None:
    TICK_LATENCY.observe(max(0.0, latency_seconds))


def record_tool_call(agent: str, tool: str, ok: bool) -> None:
    TOOL_CALLS.labels(agent=agent, tool=tool, outcome="ok" if ok else "err").inc()


def record_silence_refund() -> None:
    SILENCE_REFUNDS.inc()


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
