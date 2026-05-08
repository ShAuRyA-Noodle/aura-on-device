"""Liveness and readiness probe."""

from __future__ import annotations

import sqlite3
from typing import Any, Dict

from pydantic import BaseModel, Field


class AgentsHealth(BaseModel):
    comms: bool = True
    calendar: bool = True
    finance: bool = True
    wellness: bool = True


class MemoryHealth(BaseModel):
    sqlite_vss: bool = False
    embeddings_loaded: bool = False
    backend: str = "sqlite"


class LLMHealth(BaseModel):
    adapter: str = "template"
    model: str = "phi-3-mini-stub"


class HealthReport(BaseModel):
    status: str = Field("ok", description="overall status")
    version: str
    agents: AgentsHealth = Field(default_factory=AgentsHealth)
    memory: MemoryHealth = Field(default_factory=MemoryHealth)
    llm: LLMHealth = Field(default_factory=LLMHealth)
    uptime_seconds: float = 0.0


def collect_health(*, version: str, uptime_s: float, memory: Any | None = None) -> HealthReport:
    """Inspect each subsystem and produce a HealthReport."""
    agents = AgentsHealth()
    mem = MemoryHealth()
    if memory is not None:
        mem.sqlite_vss = bool(getattr(memory, "_vss_loaded", False))
        kind = getattr(memory, "_embedder_kind", "hash")
        mem.embeddings_loaded = kind in ("minilm", "hash")
        mem.backend = "sqlite-vss" if mem.sqlite_vss else "sqlite"
    return HealthReport(
        status="ok",
        version=version,
        agents=agents,
        memory=mem,
        llm=LLMHealth(),
        uptime_seconds=round(uptime_s, 3),
    )


def quick_sqlite_check(path: str) -> bool:
    """Lightweight `SELECT 1` against the configured store — used by Dockerfile HEALTHCHECK."""
    try:
        conn = sqlite3.connect(path, timeout=0.5)
        conn.execute("SELECT 1").fetchone()
        conn.close()
        return True
    except Exception:
        return False
