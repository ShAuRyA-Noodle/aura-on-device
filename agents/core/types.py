"""Shared, JSON-serialisable types for every Aura agent and the orchestrator.

The shapes here are derived directly from technical_spec.md sections 3, 4 and 5.
Every cross-agent payload is one of these models. The orchestrator uses
`ToolCall` and `Trace`; agents use `AgentInput` / `AgentOutput`. Pydantic v2
gives us free JSON schema export for the orchestrator's `tools.py`.

Notes for the iOS / Android port:
- All timestamps are timezone-aware ISO-8601 strings on the wire.
- All ids are short opaque strings the iOS team can mirror as `String`.
- `additionalProperties=false` semantics is enforced via `model_config`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class Surface(str, Enum):
    """Where a candidate action would land if executed."""

    WATCH = "WATCH"
    PHONE_CARD = "PHONE_CARD"
    EARBUD_TTS = "EARBUD_TTS"
    SILENT = "SILENT"


class WellnessState(str, Enum):
    """Coarse-grained wellbeing state — feeds the orchestrator's utility math."""

    BASELINE = "BASELINE"
    STRESSED = "STRESSED"
    RECOVERING = "RECOVERING"
    FOCUSED = "FOCUSED"
    UNKNOWN = "UNKNOWN"


class AgentName(str, Enum):
    COMMS = "comms"
    CALENDAR = "calendar"
    FINANCE = "finance"
    WELLNESS = "wellness"
    ORCHESTRATOR = "orchestrator"


class Outcome(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"
    TIMED_OUT = "timed_out"
    EXECUTED_AUTO = "executed_auto"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# UserState / LoadScore
# ---------------------------------------------------------------------------


class LoadScore(BaseModel):
    """Wellness Agent's primary output. Stored on every UserState snapshot."""

    model_config = ConfigDict(extra="forbid")

    value: int = Field(..., ge=0, le=100, description="0-100 stress proxy")
    state: WellnessState = WellnessState.UNKNOWN
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    drivers: List[Dict[str, Any]] = Field(default_factory=list)
    hrv_available: bool = True


class UserState(BaseModel):
    """Snapshot the orchestrator passes to every agent's tick().

    This is intentionally small. Agents must not mutate it.
    """

    model_config = ConfigDict(extra="forbid")

    user_id_local: str = "u_self"
    load_score: int = 50
    wellness_state: WellnessState = WellnessState.UNKNOWN
    in_focus_block: bool = False
    dnd_active: bool = False
    open_app: Optional[str] = None
    local_time: Optional[str] = None
    surfaces_today: int = 0


# ---------------------------------------------------------------------------
# Agent input / output (per spec §3)
# ---------------------------------------------------------------------------


class AgentInput(BaseModel):
    """Generic envelope. Agent-specific payload lives under `payload`."""

    model_config = ConfigDict(extra="forbid")

    tick_ts: str
    agent: AgentName
    user_state: UserState
    payload: Dict[str, Any] = Field(default_factory=dict)


class TraceFragment(BaseModel):
    """An agent's contribution to the orchestrator's full Trace.

    The orchestrator stitches several `TraceFragment` objects into the final
    `Trace`. Agents are forbidden from emitting raw user content — only
    structured drivers.
    """

    model_config = ConfigDict(extra="forbid")

    agent: AgentName
    inputs_summary: Dict[str, Any] = Field(default_factory=dict)
    decision: str
    drivers: List[str] = Field(default_factory=list)
    slow: bool = False
    model_low_conf: bool = False


class Candidate(BaseModel):
    """A proposed action. Orchestrator ranks these per spec §4.2."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    agent: AgentName
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    agent_priority: float = Field(0.7, ge=0.0, le=1.0)
    confirm_required: bool = True
    surface: Surface = Surface.PHONE_CARD
    args: Dict[str, Any] = Field(default_factory=dict)
    rationale_seed: str = ""


class AgentOutput(BaseModel):
    """Generic agent return. Specific payloads (e.g. CommsOutput) ride in `payload`."""

    model_config = ConfigDict(extra="forbid")

    agent: AgentName
    tick_ts: str
    candidates: List[Candidate] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    trace_fragment: Optional[TraceFragment] = None
    latency_ms: float = 0.0
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Tool call / result (per spec §4.5)
# ---------------------------------------------------------------------------


class ToolCall(BaseModel):
    """Schema-bound, JSON-serialisable invocation. No free-form chat."""

    model_config = ConfigDict(extra="forbid")

    call_id: str = Field(..., pattern=r"^t_[a-z0-9]{10}$")
    agent: AgentName
    tool: str
    args: Dict[str, Any] = Field(default_factory=dict)
    ts: str
    confirm_required: bool = True
    expected_surface: Surface = Surface.PHONE_CARD
    deadline_ms: int = Field(2000, ge=50, le=10000)


class ToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    call_id: str
    ok: bool
    result: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    latency_ms: float = 0.0


# ---------------------------------------------------------------------------
# Action and Trace (per spec §4.6, §5)
# ---------------------------------------------------------------------------


class Action(BaseModel):
    """A scored, chosen action ready for dispatch."""

    model_config = ConfigDict(extra="forbid")

    action_id: str
    kind: str
    agent: AgentName
    score: float
    components: Dict[str, float] = Field(default_factory=dict)
    confirm_required: bool = True
    surface: Surface = Surface.PHONE_CARD
    args: Dict[str, Any] = Field(default_factory=dict)
    ts: str


class TraceCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    score: float
    components: Dict[str, float] = Field(default_factory=dict)
    confirm_required: bool = False


class Trace(BaseModel):
    """Glass-box reasoning trace. Schema mirrors trace.v1.json from spec §4.6."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(..., pattern=r"^tr_[a-z0-9]{12}$")
    ts: str
    trigger: Dict[str, Any]
    signals: List[Dict[str, Any]] = Field(default_factory=list)
    candidates: List[TraceCandidate] = Field(default_factory=list)
    chosen: str
    rationale: str = Field("", max_length=500)
    rationale_source: Literal["template", "llm"] = "template"
    confirm_required: bool = False
    outcome: Outcome = Outcome.PENDING
    redactions: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def now_iso() -> str:
    """ISO-8601 UTC timestamp the iOS team can parse with ISO8601DateFormatter."""

    return datetime.now(timezone.utc).isoformat()
