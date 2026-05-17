"""Aura local-network FastAPI bridge — production-grade upgrade.

Runs the full agent stack in-process and streams Reasoning Traces over a
WebSocket while exposing typed HTTP endpoints for every agent and the memory
graph. Designed to be the Mac-side daemon that the iOS app connects to over
LAN during development and the live demo.

Key invariants
--------------
- 100% async surface area — every handler is `async def`.
- All requests + responses are typed with Pydantic v2 models so the OpenAPI
  spec at `/docs` is the single source of truth for the iOS client.
- Per-session bearer-token auth (see `auth.py`); rotated each `aura serve`.
- Structured request logging + Prometheus metrics (`/metrics`).
"""

import asyncio
import os

# The deterministic Python orchestrator handles agents whose ``name`` attr is
# None (e.g. the dataclass-based FinanceAgent). The LangGraph build assumes
# every agent provides a structured AgentName. We force the deterministic
# path here so the local daemon stays bit-identical across machines that may
# or may not have ``langgraph`` installed. This can be flipped per-process by
# the operator if they want to exercise the LangGraph variant.
os.environ.setdefault("AURA_USE_LANGGRAPH", "0")

import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Literal, Optional

from fastapi import (
    Body,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

# Make the agent stack importable when launched from anywhere.
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agents.calendar.agent import CalendarAgent  # noqa: E402
from agents.comms.agent import CommsAgent  # noqa: E402
from agents.core.types import (  # noqa: E402
    AgentInput,
    AgentName,
    UserState,
    WellnessState,
)
from agents.finance.agent import Category, FinanceAgent  # noqa: E402


class _NamedFinanceAgent(FinanceAgent):
    """FinanceAgent with the AgentName attribute the orchestrator expects.

    The dataclass FinanceAgent doesn't carry ``name`` natively; without it the
    orchestrator's ``_run_agents`` builds an ``AgentInput(agent=None)`` which
    fails Pydantic validation. We just attach the enum.
    """

    name = AgentName.FINANCE
from agents.wellness.agent import WellnessAgent  # noqa: E402
from agents.wellness.load_score import LoadScoreModel  # noqa: E402
from memory.store import MemoryGraph  # noqa: E402
from orchestrator.graph import Orchestrator  # noqa: E402
from orchestrator.policy import Policy  # noqa: E402

from . import __version__
from .auth import (
    auth_disabled,
    current_token,
    init_auth,
    require_token,
)
from .health import HealthReport, collect_health
from .middleware import install_middleware, limiter, logger
from .observability import (
    WS_CONNECTIONS,
    record_silence_refund,
    record_tick,
    record_tool_call,
    render_metrics,
)
from .trace_bus import bus

# ---------------------------------------------------------------------------
# Lifespan — initialise auth, agents, memory, then tear down cleanly.
# ---------------------------------------------------------------------------


_START_TS: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _START_TS
    _START_TS = time.time()
    if current_token() is None and not auth_disabled():
        init_auth()
    mem = MemoryGraph(path=os.environ.get("AURA_MEMORY_PATH", ":memory:"))
    # FastAPI handlers offload sync DB work to threadpool. SQLite connections
    # are bound to their creator thread by default — flip the flag so the
    # worker pool can reuse the connection. The MemoryGraph mutator helpers
    # are already serialised by their own commits.
    try:
        import sqlite3 as _sqlite3

        new_conn = _sqlite3.connect(
            mem.path if mem.path != ":memory:" else ":memory:",
            check_same_thread=False,
        )
        new_conn.row_factory = _sqlite3.Row
        # Re-apply schema on the freshly-opened (thread-safe) connection.
        from memory.store import _SCHEMA_SQL  # type: ignore

        new_conn.executescript(_SCHEMA_SQL)
        new_conn.commit()
        try:
            mem.conn.close()
        except Exception:
            pass
        mem.conn = new_conn
    except Exception:  # pragma: no cover - defensive fallback
        pass
    app.state.memory = mem
    app.state.policy = Policy()
    app.state.bus = bus()
    logger.info("aura_api_start", version=__version__, auth_enabled=not auth_disabled())
    try:
        yield
    finally:
        try:
            app.state.memory.close()
        except Exception:  # pragma: no cover - defensive shutdown
            pass
        logger.info("aura_api_stop")


app = FastAPI(
    title="Aura local API",
    description=(
        "Local-network daemon for the Aura agent stack. The iOS app talks to "
        "this server over LAN; every Reasoning Trace is streamed live via "
        "/ws/trace. Bind to 127.0.0.1 by default; flip AURA_BIND for the demo."
    ),
    version=__version__,
    lifespan=lifespan,
)

# CORS — default to the local LAN origins the iOS client uses. Set AURA_CORS
# to a comma-separated allowlist for staging / demo deploys. A wildcard ("*")
# is rejected so an operator can't accidentally open the daemon to the world.
_cors_env = os.environ.get("AURA_CORS", "").strip()
if _cors_env == "*":
    raise RuntimeError(
        "AURA_CORS=* is not allowed. Provide an explicit comma-separated origin "
        "allowlist (e.g. http://localhost:3000,http://192.168.1.20:3000)."
    )
_cors_origins = (
    [o.strip() for o in _cors_env.split(",") if o.strip()]
    if _cors_env
    else ["http://localhost:3000", "http://127.0.0.1:3000"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Aura-Token"],
    max_age=600,
)

install_middleware(app)


# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------


_WEB_DIR = _HERE.parent / "web"
if _WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(_WEB_DIR), html=True), name="web")


@app.get("/", tags=["meta"], include_in_schema=False)
async def root() -> Dict[str, str]:
    return {
        "service": "aura-local-api",
        "version": __version__,
        "docs": "/docs",
        "frontend": "/web/index.html",
        "metrics": "/metrics",
        "health": "/health",
        "ws_trace": "/ws/trace",
    }


# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TraceFragmentOut(_Base):
    agent: str
    decision: str
    drivers: List[str] = Field(default_factory=list)
    inputs_summary: Dict[str, Any] = Field(default_factory=dict)
    slow: bool = False
    model_low_conf: bool = False


class CandidateOut(_Base):
    kind: str
    agent: str
    confidence: float
    agent_priority: float
    confirm_required: bool
    surface: str
    args: Dict[str, Any] = Field(default_factory=dict)
    rationale_seed: str = ""


class AgentResponse(_Base):
    payload: Dict[str, Any] = Field(default_factory=dict)
    candidates: List[CandidateOut] = Field(default_factory=list)
    trace_fragment: Optional[TraceFragmentOut] = None
    latency_ms: float = 0.0


# ---- Comms ----

class CommsTriageRequest(_Base):
    notif_events: List[Dict[str, Any]] = Field(default_factory=list)
    gmail_threads: List[Dict[str, Any]] = Field(default_factory=list)
    load_score: int = Field(50, ge=0, le=100)
    tick_ts: str = "2026-05-07T09:00:00+00:00"


class CommsTriageResponse(AgentResponse):
    urgent: List[Dict[str, Any]] = Field(default_factory=list)
    drafts: List[Dict[str, Any]] = Field(default_factory=list)
    muted_count: int = 0


# ---- Calendar ----

class CalendarRequest(_Base):
    events_today: List[Dict[str, Any]] = Field(default_factory=list)
    user_loc: Optional[Dict[str, float]] = None
    buffer_minutes: int = 15
    tick_ts: str = "2026-05-07T09:00:00+00:00"


class ConflictSpan(_Base):
    a_id: str
    b_id: str
    overlap_min: float
    suggested_resolution: str = ""


class CalendarResponse(AgentResponse):
    conflicts: List[ConflictSpan] = Field(default_factory=list)


# ---- Finance ----

class FinanceParseRequest(_Base):
    sms: List[str] = Field(default_factory=list)
    fallback_year: int = 2026


class TransactionOut(_Base):
    amount: float
    currency: str
    merchant: str
    merchant_hash: str
    category: str
    bank: str
    account_last4: str
    ts: str
    direction: str


class FinanceParseResponse(_Base):
    transactions: List[TransactionOut] = Field(default_factory=list)
    skipped: List[str] = Field(default_factory=list)
    skipped_count: int = 0
    total: float = 0.0


class FinanceCategorizeRequest(_Base):
    merchants: List[str] = Field(default_factory=list)


class CategorizedMerchant(_Base):
    merchant: str
    category: str


class FinanceCategorizeResponse(_Base):
    items: List[CategorizedMerchant] = Field(default_factory=list)


# ---- Wellness ----

class WellnessRequest(_Base):
    rmssd_ms: float = 45.0
    typing_entropy: float = 4.0
    app_switch_rate: int = 6
    sleep_debt_min: float = 60.0
    notif_dismiss_rate: float = 0.3
    screen_on_min: int = 30
    in_focus_block: bool = False
    tick_ts: str = "2026-05-07T09:00:00+00:00"


class WellnessResponse(AgentResponse):
    load_score: int = 0
    state: str = "BASELINE"
    drivers: List[Dict[str, Any]] = Field(default_factory=list)
    intervention: Optional[Dict[str, Any]] = None


# ---- Orchestrator ----

class UserStateModel(_Base):
    user_id_local: str = "u_self"
    load_score: int = 50
    wellness_state: str = "UNKNOWN"
    in_focus_block: bool = False
    dnd_active: bool = False
    open_app: Optional[str] = None
    local_time: Optional[str] = None
    surfaces_today: int = 0


class TickRequest(_Base):
    user_state: UserStateModel = Field(default_factory=UserStateModel)
    comms: Optional[CommsTriageRequest] = None
    calendar: Optional[CalendarRequest] = None
    finance: Optional[FinanceParseRequest] = None
    wellness: Optional[WellnessRequest] = None
    tick_ts: str = "2026-05-07T09:00:00+00:00"


class TickResponse(_Base):
    chosen_kind: str
    cap_reason: Optional[str] = None
    trace: Dict[str, Any]
    agent_outputs: List[Dict[str, Any]] = Field(default_factory=list)
    latency_ms: float = 0.0


class ReplayRequest(_Base):
    name: Literal["morning_brief", "lecture_focus", "spend_anomaly", "recovery"] = "morning_brief"


# ---- Memory ----

class AddNodeRequest(_Base):
    type: Literal[
        "User", "Event", "App", "Person", "Place", "Transaction",
        "Conversation", "HealthSnapshot", "Action", "Trace",
    ]
    data: Dict[str, Any] = Field(default_factory=dict)
    retention_class: str = "default"


class AddNodeResponse(_Base):
    node_id: str


class MemorySearchRequest(_Base):
    query: str = Field(..., min_length=1, max_length=512)
    k: int = Field(5, ge=1, le=50)
    keyword_filter: Optional[str] = None


class MemorySearchHit(_Base):
    node_id: str
    score: float
    type: str
    ts: int
    data: Dict[str, Any] = Field(default_factory=dict)


class MemorySearchResponse(_Base):
    hits: List[MemorySearchHit] = Field(default_factory=list)


class MemoryDeleteRequest(_Base):
    from_ms: int = Field(..., ge=0)
    to_ms: int = Field(..., ge=0)


class MemoryDeleteResponse(_Base):
    affected: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _user_state(payload: UserStateModel | None, fallback_load: int = 50) -> UserState:
    if payload is None:
        return UserState(load_score=fallback_load)
    try:
        wstate = WellnessState(payload.wellness_state)
    except ValueError:
        wstate = WellnessState.UNKNOWN
    return UserState(
        user_id_local=payload.user_id_local,
        load_score=payload.load_score,
        wellness_state=wstate,
        in_focus_block=payload.in_focus_block,
        dnd_active=payload.dnd_active,
        open_app=payload.open_app,
        local_time=payload.local_time,
        surfaces_today=payload.surfaces_today,
    )


def _agent_output_dict(out) -> Dict[str, Any]:
    return {
        "agent": out.agent.value,
        "payload": out.payload,
        "candidates": [c.model_dump(mode="json") for c in out.candidates],
        "trace_fragment": (
            out.trace_fragment.model_dump(mode="json") if out.trace_fragment else None
        ),
        "latency_ms": out.latency_ms,
    }


async def _publish_trace_events(events: List[Dict[str, Any]]) -> None:
    b = bus()
    for evt in events:
        await b.publish(evt)


# ---------------------------------------------------------------------------
# Health + metrics
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthReport, tags=["meta"])
async def health(request: Request) -> HealthReport:
    mem = getattr(request.app.state, "memory", None)
    return collect_health(
        version=__version__,
        uptime_s=time.time() - _START_TS if _START_TS else 0.0,
        memory=mem,
    )


@app.get("/metrics", tags=["meta"], include_in_schema=False)
async def metrics() -> Response:
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)


@app.get("/api/auth/token_hint", tags=["meta"])
async def token_hint() -> Dict[str, Any]:
    """Return a non-secret hash hint of the active token for QR rotation checks."""
    import hashlib

    tok = current_token() or ""
    return {
        "auth_required": not auth_disabled(),
        "token_hash": hashlib.sha256(tok.encode()).hexdigest()[:12] if tok else None,
    }


# ---------------------------------------------------------------------------
# Comms
# ---------------------------------------------------------------------------


@app.post(
    "/api/comms/triage",
    response_model=CommsTriageResponse,
    tags=["comms"],
    dependencies=[Depends(require_token)],
)
@limiter.limit("120/minute")
async def comms_triage(
    request: Request, body: CommsTriageRequest = Body(...)
) -> CommsTriageResponse:
    agent = CommsAgent()
    inp = AgentInput(
        tick_ts=body.tick_ts,
        agent=AgentName.COMMS,
        user_state=UserState(load_score=body.load_score),
        payload={"notif_events": body.notif_events, "gmail_threads": body.gmail_threads},
    )
    out = await asyncio.to_thread(agent.tick, inp)
    record_tool_call("comms", "triage", True)
    payload = out.payload or {}
    return CommsTriageResponse(
        payload=payload,
        candidates=[CandidateOut(**_cand_dict(c)) for c in out.candidates],
        trace_fragment=_frag(out.trace_fragment),
        latency_ms=out.latency_ms,
        urgent=payload.get("urgent", []),
        drafts=payload.get("drafts", []),
        muted_count=payload.get("muted_count", 0),
    )


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------


@app.post(
    "/api/calendar/conflicts",
    response_model=CalendarResponse,
    tags=["calendar"],
    dependencies=[Depends(require_token)],
)
@limiter.limit("120/minute")
async def calendar_conflicts(
    request: Request, body: CalendarRequest = Body(...)
) -> CalendarResponse:
    agent = CalendarAgent()
    payload: Dict[str, Any] = {
        "events_today": body.events_today,
        "preferences": {"buffer_minutes": body.buffer_minutes},
    }
    if body.user_loc:
        payload["user_loc"] = body.user_loc
    inp = AgentInput(
        tick_ts=body.tick_ts,
        agent=AgentName.CALENDAR,
        user_state=UserState(load_score=50),
        payload=payload,
    )
    out = await asyncio.to_thread(agent.tick, inp)
    record_tool_call("calendar", "conflicts", True)
    raw_conflicts = (out.payload or {}).get("conflicts", [])
    conflicts = [
        ConflictSpan(
            a_id=str(c.get("a_id", "")),
            b_id=str(c.get("b_id", "")),
            overlap_min=float(c.get("overlap_min", 0)),
            suggested_resolution=str(c.get("suggested_resolution", c.get("resolution", ""))),
        )
        for c in raw_conflicts
    ]
    return CalendarResponse(
        payload=out.payload,
        candidates=[CandidateOut(**_cand_dict(c)) for c in out.candidates],
        trace_fragment=_frag(out.trace_fragment),
        latency_ms=out.latency_ms,
        conflicts=conflicts,
    )


# ---------------------------------------------------------------------------
# Finance
# ---------------------------------------------------------------------------


@app.post(
    "/api/finance/parse_sms",
    response_model=FinanceParseResponse,
    tags=["finance"],
    dependencies=[Depends(require_token)],
)
@limiter.limit("120/minute")
async def finance_parse_sms(
    request: Request, body: FinanceParseRequest = Body(...)
) -> FinanceParseResponse:
    agent = FinanceAgent()
    txns: List[TransactionOut] = []
    skipped: List[str] = []
    for line in body.sms:
        line = (line or "").strip()
        if not line:
            continue
        txn = await asyncio.to_thread(agent.parse_sms, line, body.fallback_year)
        if txn is None:
            skipped.append(line[:80])
            continue
        txns.append(
            TransactionOut(
                amount=txn.amount,
                currency=txn.currency,
                merchant=txn.merchant_raw,
                merchant_hash=txn.merchant_hash,
                category=(txn.category.value if txn.category else "other"),
                bank=txn.bank,
                account_last4=txn.account_last4,
                ts=txn.ts.isoformat(),
                direction=txn.direction,
            )
        )
    record_tool_call("finance", "parse_sms", True)
    return FinanceParseResponse(
        transactions=txns,
        skipped=skipped,
        skipped_count=len(skipped),
        total=round(sum(t.amount for t in txns), 2),
    )


@app.post(
    "/api/finance/categorize",
    response_model=FinanceCategorizeResponse,
    tags=["finance"],
    dependencies=[Depends(require_token)],
)
@limiter.limit("120/minute")
async def finance_categorize(
    request: Request, body: FinanceCategorizeRequest = Body(...)
) -> FinanceCategorizeResponse:
    agent = FinanceAgent()
    items: List[CategorizedMerchant] = []
    from agents.finance.agent import Transaction

    now = datetime.now(timezone.utc)
    for m in body.merchants:
        clean = (m or "").strip()
        if not clean:
            continue
        stub = Transaction(
            amount=0.0, currency="INR", account_last4="", ts=now, merchant_raw=clean
        )
        cat = await asyncio.to_thread(agent.categorize, stub)
        items.append(
            CategorizedMerchant(
                merchant=clean,
                category=(cat.value if cat else Category.OTHER.value),
            )
        )
    record_tool_call("finance", "categorize", True)
    return FinanceCategorizeResponse(items=items)


# ---------------------------------------------------------------------------
# Wellness
# ---------------------------------------------------------------------------


@app.post(
    "/api/wellness/load_score",
    response_model=WellnessResponse,
    tags=["wellness"],
    dependencies=[Depends(require_token)],
)
@limiter.limit("120/minute")
async def wellness_load_score(
    request: Request, body: WellnessRequest = Body(...)
) -> WellnessResponse:
    payload = body.model_dump()
    payload["rmssd_z"] = (body.rmssd_ms - 45.0) / 12.0
    agent = WellnessAgent(model=LoadScoreModel())
    inp = AgentInput(
        tick_ts=body.tick_ts,
        agent=AgentName.WELLNESS,
        user_state=UserState(load_score=50, in_focus_block=body.in_focus_block),
        payload=payload,
    )
    out = await asyncio.to_thread(agent.tick, inp)
    record_tool_call("wellness", "load_score", True)
    p = out.payload or {}
    return WellnessResponse(
        payload=p,
        candidates=[CandidateOut(**_cand_dict(c)) for c in out.candidates],
        trace_fragment=_frag(out.trace_fragment),
        latency_ms=out.latency_ms,
        load_score=int(p.get("load_score", 0)),
        state=str(p.get("state", "BASELINE")),
        drivers=p.get("drivers", []),
        intervention=p.get("suggested_intervention"),
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def _replay_payload(name: str) -> TickRequest:
    common_ts = "2026-05-07T08:30:00+00:00"
    if name == "lecture_focus":
        return TickRequest(
            user_state=UserStateModel(load_score=68, in_focus_block=True),
            comms=CommsTriageRequest(
                notif_events=[
                    {
                        "id": "n_001", "app_pkg": "wa", "channel": "ch_class",
                        "preview": "@you reminder viva at 4pm please confirm",
                        "intent_hint": "actionable",
                        "ts": common_ts,
                    }
                ],
                load_score=68,
                tick_ts=common_ts,
            ),
            calendar=CalendarRequest(
                events_today=[
                    {"id": "ev_class", "title": "DSA class",
                     "start": "2026-05-07T10:00:00+00:00", "end": "2026-05-07T11:00:00+00:00"},
                ],
                tick_ts=common_ts,
            ),
            wellness=WellnessRequest(
                rmssd_ms=32.0, typing_entropy=4.7, app_switch_rate=12,
                sleep_debt_min=120.0, notif_dismiss_rate=0.5, screen_on_min=40,
                in_focus_block=True, tick_ts=common_ts,
            ),
            tick_ts=common_ts,
        )
    if name == "spend_anomaly":
        return TickRequest(
            finance=FinanceParseRequest(
                sms=[
                    "Sent Rs.2400.00 from A/c **1234 to ZOMATO via UPI on 07-MAY",
                    "INR 1500.00 spent on ICICI Bank Card XX9921 at SWIGGY on 07-May-26",
                ],
                fallback_year=2026,
            ),
            tick_ts=common_ts,
        )
    if name == "recovery":
        return TickRequest(
            wellness=WellnessRequest(
                rmssd_ms=58.0, typing_entropy=2.5, app_switch_rate=2,
                sleep_debt_min=10.0, notif_dismiss_rate=0.1, screen_on_min=10,
                tick_ts=common_ts,
            ),
            tick_ts=common_ts,
        )
    # default: morning_brief
    return TickRequest(
        comms=CommsTriageRequest(
            notif_events=[
                {"id": "n_001", "app_pkg": "wa", "channel": "ch_friends",
                 "preview": "lol same", "intent_hint": "social", "ts": common_ts},
                {"id": "n_002", "app_pkg": "wa", "channel": "ch_class",
                 "preview": "@you reminder viva at 4pm please confirm",
                 "intent_hint": "actionable", "ts": common_ts},
            ],
            tick_ts=common_ts,
        ),
        calendar=CalendarRequest(
            events_today=[
                {"id": "ev_morning", "title": "Standup",
                 "start": "2026-05-07T09:00:00+00:00", "end": "2026-05-07T09:30:00+00:00"},
            ],
            tick_ts=common_ts,
        ),
        wellness=WellnessRequest(
            rmssd_ms=42.0, typing_entropy=4.1, app_switch_rate=7,
            sleep_debt_min=80.0, notif_dismiss_rate=0.3, screen_on_min=25,
            tick_ts=common_ts,
        ),
        tick_ts=common_ts,
    )


async def _run_orchestrator(body: TickRequest) -> TickResponse:
    started = time.perf_counter()
    user_state = _user_state(body.user_state)

    comms_p = (body.comms.model_dump() if body.comms else
               {"notif_events": [], "gmail_threads": []})
    cal_p = (body.calendar.model_dump() if body.calendar else
             {"events_today": [], "buffer_minutes": 15})
    fin_p = body.finance.model_dump() if body.finance else {"sms": []}
    well_p = body.wellness.model_dump() if body.wellness else {}

    sms_unprocessed = [
        {"id": f"s_{i:03d}", "body": s} for i, s in enumerate(fin_p.get("sms", []) or [])
    ]

    orch = Orchestrator(
        agents=[CommsAgent(), CalendarAgent(), _NamedFinanceAgent(), WellnessAgent()],
        policy=Policy(),
    )

    await bus().publish({"type": "tick.start", "tick_ts": body.tick_ts,
                         "user_state": user_state.model_dump(mode="json")})

    def _do() -> Any:
        return orch.tick(
            user_state=user_state,
            agent_payloads={
                "comms": {
                    "notif_events": comms_p.get("notif_events", []),
                    "gmail_threads": comms_p.get("gmail_threads", []),
                },
                "calendar": {
                    "events_today": cal_p.get("events_today", []),
                    "preferences": {"buffer_minutes": cal_p.get("buffer_minutes", 15)},
                },
                "finance": {"sms_unprocessed": sms_unprocessed, "gmail_receipts": []},
                "wellness": {
                    "rmssd_ms": well_p.get("rmssd_ms", 45.0),
                    "rmssd_z": (well_p.get("rmssd_ms", 45.0) - 45.0) / 12.0,
                    "sleep_debt_min": well_p.get("sleep_debt_min", 60.0),
                    "typing_entropy": well_p.get("typing_entropy", 4.0),
                    "app_switch_rate": well_p.get("app_switch_rate", 6),
                    "notif_dismiss_rate": well_p.get("notif_dismiss_rate", 0.3),
                    "screen_on_min": well_p.get("screen_on_min", 30),
                },
            },
            tick_ts=body.tick_ts,
        )

    result = await asyncio.to_thread(_do)

    # Fan out per-agent events.
    for out in result.agent_outputs:
        await bus().publish({
            "type": "agent.output",
            "agent": out.agent.value,
            "payload": out.payload,
            "candidates": [c.model_dump(mode="json") for c in out.candidates],
            "trace_fragment": (
                out.trace_fragment.model_dump(mode="json") if out.trace_fragment else None
            ),
        })
    await bus().publish({
        "type": "policy.decision",
        "chosen_kind": result.chosen_kind,
        "cap_reason": result.cap_reason,
    })
    trace_dict = result.trace.model_dump(mode="json")
    await bus().publish({"type": "trace.emitted", "trace": trace_dict})

    # Persist the trace to memory if available.
    try:
        app.state.memory.add_trace(trace_dict)
    except Exception:  # pragma: no cover - non-fatal
        pass
    if result.cap_reason == "silence_budget":
        record_silence_refund()

    elapsed = time.perf_counter() - started
    record_tick(elapsed)
    await bus().publish({"type": "tick.end", "latency_ms": round(elapsed * 1000, 2)})

    return TickResponse(
        chosen_kind=result.chosen_kind,
        cap_reason=result.cap_reason,
        trace=trace_dict,
        agent_outputs=[_agent_output_dict(o) for o in result.agent_outputs],
        latency_ms=round(elapsed * 1000, 2),
    )


@app.post(
    "/api/orchestrator/tick",
    response_model=TickResponse,
    tags=["orchestrator"],
    dependencies=[Depends(require_token)],
)
@limiter.limit("60/minute")
async def orchestrator_tick(
    request: Request, body: TickRequest = Body(...)
) -> TickResponse:
    return await _run_orchestrator(body)


@app.post(
    "/api/orchestrator/run_replay",
    response_model=TickResponse,
    tags=["orchestrator"],
    dependencies=[Depends(require_token)],
)
@limiter.limit("60/minute")
async def orchestrator_run_replay(
    request: Request, body: ReplayRequest = Body(...)
) -> TickResponse:
    payload = _replay_payload(body.name)
    return await _run_orchestrator(payload)


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------


@app.post(
    "/api/memory/add_node",
    response_model=AddNodeResponse,
    tags=["memory"],
    dependencies=[Depends(require_token)],
)
@limiter.limit("240/minute")
async def memory_add_node(
    request: Request, body: AddNodeRequest = Body(...)
) -> AddNodeResponse:
    mem: MemoryGraph = request.app.state.memory
    nid = await asyncio.to_thread(
        mem.add_node, body.type, body.data, None, body.retention_class
    )
    return AddNodeResponse(node_id=nid)


@app.post(
    "/api/memory/search",
    response_model=MemorySearchResponse,
    tags=["memory"],
    dependencies=[Depends(require_token)],
)
@limiter.limit("240/minute")
async def memory_search(
    request: Request, body: MemorySearchRequest = Body(...)
) -> MemorySearchResponse:
    mem: MemoryGraph = request.app.state.memory
    raw = await asyncio.to_thread(mem.search, body.query, body.k)
    if body.keyword_filter:
        kw = body.keyword_filter.lower()
        raw = [r for r in raw if kw in str(r.get("data", "")).lower()]
    return MemorySearchResponse(hits=[MemorySearchHit(**r) for r in raw])


@app.delete(
    "/api/memory/by_time_range",
    response_model=MemoryDeleteResponse,
    tags=["memory"],
    dependencies=[Depends(require_token)],
)
@limiter.limit("60/minute")
async def memory_delete(
    request: Request,
    from_ms: int = Query(..., ge=0),
    to_ms: int = Query(..., ge=0),
) -> MemoryDeleteResponse:
    if to_ms < from_ms:
        raise HTTPException(status_code=400, detail="to_ms < from_ms")
    mem: MemoryGraph = request.app.state.memory
    affected = await asyncio.to_thread(mem.delete_by_time_range, from_ms, to_ms)
    return MemoryDeleteResponse(affected=affected)


@app.get(
    "/api/memory/export",
    tags=["memory"],
    dependencies=[Depends(require_token)],
)
@limiter.limit("30/minute")
async def memory_export(request: Request, redaction_profile: str = "raw") -> JSONResponse:
    mem: MemoryGraph = request.app.state.memory
    data = await asyncio.to_thread(mem.export_json, redaction_profile)
    return JSONResponse(
        content=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )


@app.get(
    "/api/memory/audit_log",
    tags=["memory"],
    dependencies=[Depends(require_token)],
)
@limiter.limit("60/minute")
async def memory_audit_log(
    request: Request, limit: int = Query(100, ge=1, le=2000)
) -> Dict[str, Any]:
    mem: MemoryGraph = request.app.state.memory

    def _read() -> List[Dict[str, Any]]:
        rows = mem.conn.execute(
            "SELECT seq, ts, op, target_type, target_id, agent, hash_chain "
            "FROM audit_log ORDER BY seq DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    rows = await asyncio.to_thread(_read)
    return {"count": len(rows), "rows": rows}


# ---------------------------------------------------------------------------
# WebSocket — /ws/trace
# ---------------------------------------------------------------------------


@app.websocket("/ws/trace")
async def ws_trace(websocket: WebSocket, token: Optional[str] = Query(default=None)) -> None:
    """Live Reasoning Trace stream. Authenticates via ?token=<bearer>."""
    if not auth_disabled():
        expected = current_token()
        if expected is None:
            await websocket.close(code=1011, reason="auth not initialised")
            return
        candidate = token or websocket.headers.get("authorization", "").removeprefix("Bearer ").strip()
        if candidate != expected:
            await websocket.close(code=4401, reason="invalid token")
            return
    await websocket.accept()
    queue = await bus().subscribe()
    WS_CONNECTIONS.inc()
    try:
        await websocket.send_json({
            "type": "hello",
            "version": __version__,
            "subscriber_count": bus().subscriber_count,
        })
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                # Heartbeat keeps NAT timeouts at bay.
                await websocket.send_json({"type": "heartbeat", "ts": time.time()})
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("ws_trace_error", error=str(exc))
    finally:
        await bus().unsubscribe(queue)
        WS_CONNECTIONS.dec()


# ---------------------------------------------------------------------------
# Helpers (private)
# ---------------------------------------------------------------------------


def _cand_dict(c: Any) -> Dict[str, Any]:
    return {
        "kind": c.kind,
        "agent": c.agent.value,
        "confidence": c.confidence,
        "agent_priority": c.agent_priority,
        "confirm_required": c.confirm_required,
        "surface": c.surface.value,
        "args": c.args,
        "rationale_seed": c.rationale_seed,
    }


def _frag(f: Any) -> Optional[TraceFragmentOut]:
    if f is None:
        return None
    return TraceFragmentOut(
        agent=f.agent.value,
        decision=f.decision,
        drivers=f.drivers,
        inputs_summary=f.inputs_summary,
        slow=f.slow,
        model_low_conf=f.model_low_conf,
    )


__all__ = ["app"]
