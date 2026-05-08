"""Aura shared agent core: types, base class, contracts.

This package is the only agreed contact surface between the four specialist
agents (Comms, Calendar, Finance, Wellness) and the orchestrator. Anything
crossing an agent boundary must be expressible as one of the Pydantic models
in `types.py`.
"""

from .types import (
    Action,
    AgentInput,
    AgentOutput,
    Candidate,
    LoadScore,
    Surface,
    ToolCall,
    ToolResult,
    Trace,
    TraceFragment,
    UserState,
    WellnessState,
)
from .agent_base import Agent

__all__ = [
    "Agent",
    "Action",
    "AgentInput",
    "AgentOutput",
    "Candidate",
    "LoadScore",
    "Surface",
    "ToolCall",
    "ToolResult",
    "Trace",
    "TraceFragment",
    "UserState",
    "WellnessState",
]
