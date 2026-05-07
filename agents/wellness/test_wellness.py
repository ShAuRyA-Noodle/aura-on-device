"""WellnessAgent unit tests (technical_spec.md §3.4).

Worked examples:
- A: stress-driven mute (Mira). rmssd 28.4, switch 14, entropy 4.91 -> load >= 70,
  intervention = MUTE_GROUP_30 because an active channel is in payload.
- B: recovery nudge. Score history shows >=10 point drop -> RECOVERING + PERMIT_LEISURE.

Plus:
- HRV-missing path clamps load score to <=70 and flags hrv_unavailable.
- Calibration: Spearman ρ between load_score and self_rated_stress on
  monotonically increasing pairs returns ~1.0.
- Latency budget (60 ms p50).
- Tool surface and ToolCall round-trip.
"""

from __future__ import annotations

import csv
import math
import time
from pathlib import Path
from typing import Dict, List

import pytest

from agents.core.types import (
    AgentInput,
    AgentName,
    AgentOutput,
    Surface,
    ToolCall,
    UserState,
    WellnessState,
    now_iso,
)
from agents.wellness.agent import WellnessAgent
from agents.wellness.load_score import LoadScoreModel, WellnessFeatures


FIXTURES = Path(__file__).parent / "fixtures"


def _read_csv(name: str) -> List[Dict[str, str]]:
    with (FIXTURES / name).open() as f:
        return list(csv.DictReader(f))


def _build_input(payload: Dict, load_score: int = 50) -> AgentInput:
    return AgentInput(
        tick_ts="2026-05-07T14:32:00+05:30",
        agent=AgentName.WELLNESS,
        user_state=UserState(load_score=load_score),
        payload=payload,
    )


# --------------------------------------------------------------------------
# Worked example A — stress-driven mute (Mira)
# --------------------------------------------------------------------------


def test_mira_stress_yields_mute_group():
    payload = {
        "hrv_window": {"rmssd_ms": 28.4, "samples": 12, "window_min": 5},
        "sleep_last_night": {"asleep_min": 312, "rem_min": 41, "deep_min": 33, "efficiency": 0.82},
        "typing_entropy_60s": 4.91,
        "app_switch_rate_60s": 14,
        "notif_dismiss_rate_60m": 0.78,
        "screen_on_min_60m": 47,
        "personal_baseline": {"rmssd_p50": 38.2, "rmssd_p10": 22.1, "switch_p50": 6},
        "active_channel": "group:Thapar-DSA-Project",
    }
    out = WellnessAgent().tick_timed(_build_input(payload, load_score=78))
    assert isinstance(out, AgentOutput)
    assert out.payload["load_score"] >= 70
    assert out.payload["state"] == WellnessState.STRESSED.value
    assert out.payload["suggested_intervention"]["kind"] == "MUTE_GROUP_30"
    assert any(c.kind == "MUTE_GROUP_30" for c in out.candidates)


def test_baseline_emits_no_candidate():
    payload = {
        "hrv_window": {"rmssd_ms": 42.0, "samples": 12, "window_min": 5},
        "sleep_last_night": {"asleep_min": 420, "rem_min": 80, "deep_min": 60, "efficiency": 0.92},
        "typing_entropy_60s": 3.0,
        "app_switch_rate_60s": 4,
        "notif_dismiss_rate_60m": 0.2,
        "screen_on_min_60m": 18,
        "personal_baseline": {"rmssd_p50": 38.2, "rmssd_p10": 22.1},
    }
    out = WellnessAgent().tick_timed(_build_input(payload))
    assert out.payload["load_score"] < 70
    assert out.payload["suggested_intervention"]["kind"] in ("DO_NOTHING", "NAP_15", "PERMIT_LEISURE")


# --------------------------------------------------------------------------
# HRV missing
# --------------------------------------------------------------------------


def test_hrv_missing_caps_at_70():
    payload = {
        "hrv_window": {},
        "sleep_last_night": {"asleep_min": 200},
        "typing_entropy_60s": 5.5,
        "app_switch_rate_60s": 18,
        "notif_dismiss_rate_60m": 0.9,
        "screen_on_min_60m": 80,
        "personal_baseline": {"rmssd_p50": 38.2, "rmssd_p10": 22.1},
    }
    out = WellnessAgent().tick_timed(_build_input(payload))
    assert out.payload["load_score"] <= 70
    assert out.trace_fragment.inputs_summary["hrv_unavailable"] is True


# --------------------------------------------------------------------------
# Spearman ρ
# --------------------------------------------------------------------------


def test_spearman_monotonic_pairs():
    samples = [(20.0, 1), (40.0, 2), (55.0, 3), (70.0, 4), (90.0, 5)]
    rho = LoadScoreModel.spearman_rho(samples)
    assert math.isclose(rho, 1.0, abs_tol=1e-6)


def test_spearman_anticorrelated():
    samples = [(20.0, 5), (40.0, 4), (55.0, 3), (70.0, 2), (90.0, 1)]
    rho = LoadScoreModel.spearman_rho(samples)
    assert math.isclose(rho, -1.0, abs_tol=1e-6)


# --------------------------------------------------------------------------
# Platt calibration
# --------------------------------------------------------------------------


def test_platt_calibrator_runs():
    model = LoadScoreModel()
    samples = [(20.0, 1), (35.0, 2), (50.0, 2), (65.0, 3), (80.0, 4), (95.0, 5)] * 3
    model.fit_calibrator(samples)
    assert model.calibrator_fitted
    s_low = model.calibrate_to_stress(20.0)
    s_high = model.calibrate_to_stress(95.0)
    assert s_low < s_high


# --------------------------------------------------------------------------
# Recovery
# --------------------------------------------------------------------------


def test_recovery_check_via_tool():
    agent = WellnessAgent()
    history = [
        {"ts": "2026-05-07T13:00:00+05:30", "score": 78},
        {"ts": "2026-05-07T13:30:00+05:30", "score": 70},
        {"ts": "2026-05-07T14:00:00+05:30", "score": 60},
        {"ts": "2026-05-07T14:30:00+05:30", "score": 52},
    ]
    call = ToolCall(
        call_id="t_" + "r" * 10,
        agent=AgentName.WELLNESS,
        tool="recovery_check",
        args={"history": history},
        ts=now_iso(),
        confirm_required=False,
    )
    res = agent.handle_tool_call(call)
    assert res.ok and res.result["recovered"] is True


# --------------------------------------------------------------------------
# Tool calls
# --------------------------------------------------------------------------


def test_tools_listed():
    tools = WellnessAgent().tools()
    names = {t["name"] for t in tools}
    assert names == {"compute_load_score", "intervention_select", "correlation_check", "recovery_check"}


def test_compute_load_score_tool():
    agent = WellnessAgent()
    feats = WellnessFeatures(
        rmssd_ms=28.4,
        rmssd_z=-1.4,
        sleep_debt_min=108.0,
        typing_entropy=4.91,
        app_switch_rate=14,
        notif_dismiss_rate=0.78,
        screen_on_min=47,
        hour_of_day_sin=0.5,
        hour_of_day_cos=-0.86,
    )
    call = ToolCall(
        call_id="t_" + "s" * 10,
        agent=AgentName.WELLNESS,
        tool="compute_load_score",
        args={
            "features": {
                "rmssd_ms": feats.rmssd_ms,
                "rmssd_z": feats.rmssd_z,
                "sleep_debt_min": feats.sleep_debt_min,
                "typing_entropy": feats.typing_entropy,
                "app_switch_rate": feats.app_switch_rate,
                "notif_dismiss_rate": feats.notif_dismiss_rate,
                "screen_on_min": feats.screen_on_min,
                "hour_of_day_sin": feats.hour_of_day_sin,
                "hour_of_day_cos": feats.hour_of_day_cos,
            }
        },
        ts=now_iso(),
        confirm_required=False,
    )
    res = agent.handle_tool_call(call)
    assert res.ok
    assert 60 <= res.result["load_score"] <= 100


def test_correlation_check_tool():
    agent = WellnessAgent()
    samples = [[20.0, 1], [40.0, 2], [55.0, 3], [70.0, 4], [90.0, 5]]
    call = ToolCall(
        call_id="t_" + "c" * 10,
        agent=AgentName.WELLNESS,
        tool="correlation_check",
        args={"samples": samples},
        ts=now_iso(),
        confirm_required=False,
    )
    res = agent.handle_tool_call(call)
    assert res.ok and res.result["rho"] >= 0.99


# --------------------------------------------------------------------------
# Latency
# --------------------------------------------------------------------------


def test_tick_latency_budget():
    payload = {
        "hrv_window": {"rmssd_ms": 28.4, "samples": 12, "window_min": 5},
        "sleep_last_night": {"asleep_min": 312},
        "typing_entropy_60s": 4.91,
        "app_switch_rate_60s": 14,
        "notif_dismiss_rate_60m": 0.78,
        "screen_on_min_60m": 47,
        "personal_baseline": {"rmssd_p50": 38.2, "rmssd_p10": 22.1},
    }
    agent = WellnessAgent()
    samples = []
    for _ in range(7):
        t0 = time.perf_counter()
        agent.tick(_build_input(payload))
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples.sort()
    median = samples[len(samples) // 2]
    assert median < 60.0, f"median tick latency {median:.1f}ms exceeds 60ms"


# --------------------------------------------------------------------------
# Fixture-driven sanity (CSV files exist and parse)
# --------------------------------------------------------------------------


def test_csv_fixtures_present_and_parse():
    for name in ("hrv_5days.csv", "typing_entropy.csv", "app_switch.csv", "sleep.csv"):
        rows = _read_csv(name)
        assert rows, f"{name} parsed empty"


# --------------------------------------------------------------------------
# Output shape
# --------------------------------------------------------------------------


def test_output_round_trip():
    payload = {
        "hrv_window": {"rmssd_ms": 38.0},
        "sleep_last_night": {"asleep_min": 380},
        "typing_entropy_60s": 3.4,
        "app_switch_rate_60s": 6,
        "notif_dismiss_rate_60m": 0.3,
        "screen_on_min_60m": 22,
        "personal_baseline": {"rmssd_p50": 38.2, "rmssd_p10": 22.1},
    }
    out = WellnessAgent().tick_timed(_build_input(payload))
    s = out.model_dump_json()
    rebuilt = AgentOutput.model_validate_json(s)
    assert "load_score" in rebuilt.payload
