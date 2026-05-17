"""End-to-end: Monday Brief journey (plan §7 Journey A).

Wires Comms + Calendar + Finance + Wellness into a real Orchestrator and
replays `orchestrator/replays/monday_brief.replay.json`.

Asserts:
- At least one Brief card surfaced (SHOW_BRIEF or LEAVE_BY_ALERT).
- Exactly one Reasoning Trace emitted.
- Silence Budget decremented from 3 to 2 (1 surface consumed).
- No banned actions chosen (must_not_choose from the fixture).
- Per-agent and total tick latency within budget.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

from agents.core.types import UserState
from orchestrator.graph import Orchestrator, OrchestratorState
from orchestrator.trace import validate_trace


# CI runners are shared cold-start VMs that take ~1.5s loading sklearn
# the first time; the bench suite continues to assert the tighter
# §3 numbers on a warm Mac-side daemon.
_IS_CI = bool(os.environ.get("CI"))
_TICK_BUDGET_MS = 6000.0 if _IS_CI else 2500.0  # spec §3 — 4 agents @ 300 ms p50 + slack.
_PER_AGENT_BUDGET_MS = 2000.0 if _IS_CI else 800.0  # spec §3 p95.


def test_monday_brief_e2e_full_run(
    orchestrator: Orchestrator,
    monday_brief_replay: Dict[str, Any],
) -> None:
    fx = monday_brief_replay
    user_state = UserState(**fx["user_state"])

    t0 = time.perf_counter()
    res = orchestrator.tick(
        user_state=user_state,
        agent_payloads=fx["agent_payloads"],
        tick_ts=fx["tick_ts"],
        trigger={"source": "phone_unlock", "value": {"hour": 7.75}},
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    # 1. Final state.
    assert res.final_state == OrchestratorState.COOLDOWN

    # 2. At least one Brief card surfaced.
    assert res.chosen_kind in fx["expected"]["chosen_in"], (
        f"chosen={res.chosen_kind} not in expected={fx['expected']['chosen_in']}"
    )

    # 3. No banned action chosen.
    for banned in fx["expected"]["must_not_choose"]:
        assert res.chosen_kind != banned

    # 4. Exactly one Reasoning Trace emitted, schema-valid.
    assert res.trace is not None
    validate_trace(res.trace)
    assert res.trace.chosen == res.chosen_kind

    # 5. Silence Budget: 1 non-safety surface recorded -> remaining 2.
    daily_used = orchestrator.history.daily_total_excluding_safety(
        _now_from_iso(fx["tick_ts"])
    )
    assert daily_used == 1, f"expected 1 surface used, got {daily_used}"
    remaining = orchestrator.policy.silence_budget_total - daily_used
    assert remaining == 2, f"silence budget should be 2, got {remaining}"

    # 6. Latency budget respected.
    assert elapsed_ms < _TICK_BUDGET_MS, (
        f"orchestrator tick took {elapsed_ms:.0f}ms > budget {_TICK_BUDGET_MS:.0f}ms"
    )
    for out in res.agent_outputs:
        assert out.latency_ms <= _PER_AGENT_BUDGET_MS, (
            f"{out.agent} took {out.latency_ms:.0f}ms"
        )

    # 7. Trace surfaces a non-empty signal set from at least 2 agents.
    agents_in_signals = {s["agent"] for s in res.trace.signals}
    assert len(agents_in_signals) >= 2, agents_in_signals


def test_monday_brief_emits_one_trace_per_tick(
    orchestrator: Orchestrator,
    monday_brief_replay: Dict[str, Any],
) -> None:
    """Each `orchestrator.tick()` must emit exactly one Trace."""
    fx = monday_brief_replay
    user_state = UserState(**fx["user_state"])
    traces = []
    for _ in range(3):
        res = orchestrator.tick(
            user_state=user_state,
            agent_payloads=fx["agent_payloads"],
            tick_ts=fx["tick_ts"],
        )
        if res.trace is not None:
            traces.append(res.trace)
    # 3 ticks -> 3 traces, each with a unique trace_id.
    assert len(traces) == 3
    assert len({t.trace_id for t in traces}) == 3


def test_monday_brief_drivers_are_pii_free(
    orchestrator: Orchestrator,
    monday_brief_replay: Dict[str, Any],
) -> None:
    """Trace drivers must never include raw message text."""
    fx = monday_brief_replay
    user_state = UserState(**fx["user_state"])
    res = orchestrator.tick(
        user_state=user_state,
        agent_payloads=fx["agent_payloads"],
        tick_ts=fx["tick_ts"],
    )
    banned_substrings = ["@you can you confirm", "lol that meme", "Tomorrow's quiz"]
    payload = res.trace.model_dump_json()
    for snippet in banned_substrings:
        assert snippet not in payload, f"PII leak: {snippet}"


def test_monday_brief_matches_canonical_trace(canonical_traces_dir) -> None:
    """The trace JSON must structurally match the canonical artifact.

    Uses ``deepdiff.DeepDiff`` with timestamp fields excluded so the
    comparison is reproducible across machines and clocks.
    """
    from deepdiff import DeepDiff
    from orchestrator.replay import run_replay

    canonical = json.loads((canonical_traces_dir / "monday_brief_trace.json").read_text())
    out = run_replay("monday_brief", write_output=False)
    diff = DeepDiff(
        canonical,
        out["trace"],
        exclude_paths=["root['ts']"],
        ignore_order=False,
    )
    assert not diff, f"trace drift vs canonical: {diff}"


def test_monday_brief_surfaces_three_actions(
    orchestrator: Orchestrator,
    monday_brief_replay: Dict[str, Any],
) -> None:
    """Replay must surface at least 3 candidate actions (sleep alert,
    leave-by alert, professor's slides summary)."""
    fx = monday_brief_replay
    user_state = UserState(**fx["user_state"])
    res = orchestrator.tick(
        user_state=user_state,
        agent_payloads=fx["agent_payloads"],
        tick_ts=fx["tick_ts"],
        trigger=fx.get("trigger"),
    )
    kinds = {c.kind for c in res.trace.candidates}
    expected_kinds = set(fx["expected"]["must_surface_kinds"])
    assert expected_kinds <= kinds, f"missing surfaces: {expected_kinds - kinds}; got {kinds}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_from_iso(s: str):
    from datetime import datetime, timezone

    s = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
