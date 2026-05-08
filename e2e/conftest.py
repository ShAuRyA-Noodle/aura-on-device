"""Shared fixtures for end-to-end integration tests.

Boots the four agents, the orchestrator, and an in-memory `MemoryGraph`
backed by SQLite `:memory:`. All fixtures are function-scoped so each test
sees a clean state machine and a clean memory store.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest


# Make the repo root importable so `agents.*`, `orchestrator.*`, `memory.*`
# resolve when pytest is invoked from any directory.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


from agents.calendar.agent import CalendarAgent  # noqa: E402
from agents.comms.agent import CommsAgent  # noqa: E402
from agents.core.types import AgentName  # noqa: E402
from agents.finance.agent import FinanceAgent  # noqa: E402
from agents.wellness.agent import WellnessAgent  # noqa: E402
from memory.store import MemoryGraph  # noqa: E402
from orchestrator.graph import Orchestrator  # noqa: E402
from orchestrator.policy import ActionHistory, DNDWindow, Policy  # noqa: E402


# ---------------------------------------------------------------------------
# Finance adapter
# ---------------------------------------------------------------------------
#
# FinanceAgent is a `@dataclass` (spec §3.3 — async tick) whereas the other
# three agents are sync `Agent` subclasses with `name`, `tick_timed`, etc.
# The Orchestrator's `_run_agents` reads `agent.name` and falls back to an
# async-coerce path if there is no `tick_timed`. That works for FinanceAgent
# *only if* `name` is present. We add a thin wrapper that exposes the
# expected surface without modifying the agent itself.


class _FinanceOrchestratorAdapter:
    """Adapter exposing FinanceAgent under the Agent-like contract.

    - `name` is the AgentName.FINANCE enum.
    - `tick(payload)` calls the underlying async tick and returns a dict.
      The Orchestrator's existing async-coerce path turns this into an
      AgentOutput automatically (see `orchestrator/graph.py` lines 232-247).
    """

    name = AgentName.FINANCE
    latency_budget_ms = 350

    def __init__(self, inner: FinanceAgent) -> None:
        self._inner = inner

    def tick(self, payload):  # noqa: D401 — orchestrator calls this with payload
        return self._inner.tick(payload)

    @property
    def inner(self) -> FinanceAgent:
        return self._inner


REPLAYS_DIR = _REPO_ROOT / "orchestrator" / "replays"


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------


@pytest.fixture
def comms_agent() -> CommsAgent:
    return CommsAgent()


@pytest.fixture
def calendar_agent() -> CalendarAgent:
    return CalendarAgent()


@pytest.fixture
def finance_agent() -> FinanceAgent:
    """The bare FinanceAgent (async, dataclass)."""
    return FinanceAgent()


@pytest.fixture
def finance_agent_adapted(finance_agent: FinanceAgent) -> _FinanceOrchestratorAdapter:
    """FinanceAgent wrapped in the orchestrator-compatible adapter."""
    return _FinanceOrchestratorAdapter(finance_agent)


@pytest.fixture
def wellness_agent() -> WellnessAgent:
    return WellnessAgent()


@pytest.fixture
def all_agents(
    comms_agent: CommsAgent,
    calendar_agent: CalendarAgent,
    finance_agent_adapted: _FinanceOrchestratorAdapter,
    wellness_agent: WellnessAgent,
) -> List[Any]:
    """The four-agent fleet, in the order the orchestrator expects.

    FinanceAgent rides under an adapter so it behaves like the other three
    sync agents from the Orchestrator's point of view.
    """
    return [comms_agent, calendar_agent, finance_agent_adapted, wellness_agent]


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


@pytest.fixture
def orchestrator(all_agents: List[Any]) -> Orchestrator:
    """Fresh Orchestrator with a default Policy and empty history."""
    return Orchestrator(
        agents=all_agents,
        policy=Policy(silence_budget_total=3),
        history=ActionHistory(),
        dnd=DNDWindow(),
    )


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------


@pytest.fixture
def memory_graph() -> MemoryGraph:
    """A MemoryGraph backed by a SQLite `:memory:` database.

    Closed automatically at end of test.
    """
    g = MemoryGraph(path=":memory:")
    yield g
    g.close()


# ---------------------------------------------------------------------------
# Replay loaders
# ---------------------------------------------------------------------------


def _load_replay_with_burst(name: str) -> Dict[str, Any]:
    """Load a replay and expand any synthetic burst markers."""
    from orchestrator.replay import _expand_burst  # local import to avoid cycle

    fx = json.loads((REPLAYS_DIR / f"{name}.replay.json").read_text())
    _expand_burst(fx)
    return fx


@pytest.fixture
def monday_brief_replay() -> Dict[str, Any]:
    """Loads `orchestrator/replays/monday_brief.replay.json`."""
    return _load_replay_with_burst("monday_brief")


@pytest.fixture
def quiet_group_chat_replay() -> Dict[str, Any]:
    """Loads `orchestrator/replays/quiet_group_chat.replay.json` (137 msgs)."""
    return _load_replay_with_burst("quiet_group_chat")


@pytest.fixture
def spend_mirror_replay() -> Dict[str, Any]:
    """Loads `orchestrator/replays/spend_mirror.replay.json` (14 UPI SMS)."""
    return _load_replay_with_burst("spend_mirror")


@pytest.fixture
def canonical_traces_dir() -> Path:
    """Path to ``orchestrator/replays/output/`` (the frozen canonical hashes)."""
    return REPLAYS_DIR / "output"
