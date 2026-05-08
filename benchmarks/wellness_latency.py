"""WellnessAgent.tick() latency benchmark.

Asserts the spec §3.4 latency budget: a single ``WellnessAgent.tick()`` call
runs in under 50 ms median on the team's Mac. Measured with
``time.perf_counter`` over 200 warm iterations after a 30-iter warm-up.

Outputs:
    benchmarks/results/wellness_YYYY-MM-DD.json

Run as a script:
    python benchmarks/wellness_latency.py
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from datetime import date as _date
from pathlib import Path
from typing import Dict


# Make repo root importable when run as a plain script.
_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO))

from agents.core.types import AgentInput, AgentName, UserState  # noqa: E402
from agents.wellness.agent import WellnessAgent  # noqa: E402
from agents.wellness.load_score import LoadScoreModel  # noqa: E402


_RESULTS_DIR = _REPO / "benchmarks" / "results"


def _payload() -> Dict:
    return {
        "hrv_window": {"rmssd_ms": 28.4, "samples": 12, "window_min": 5},
        "sleep_last_night": {"asleep_min": 312},
        "typing_entropy_60s": 4.91,
        "app_switch_rate_60s": 14,
        "notif_dismiss_rate_60m": 0.78,
        "screen_on_min_60m": 47,
        "personal_baseline": {"rmssd_p50": 38.2, "rmssd_p10": 22.1},
        "active_channel": "group:Thapar-DSA-Project",
    }


def _build_input(payload: Dict) -> AgentInput:
    return AgentInput(
        tick_ts="2026-05-07T14:32:00+05:30",
        agent=AgentName.WELLNESS,
        user_state=UserState(load_score=50),
        payload=payload,
    )


def measure(n_warmup: int = 30, n_iter: int = 200) -> Dict[str, float]:
    """Measure a single ``tick()`` call. Returns latency stats in milliseconds."""

    model = LoadScoreModel.load_default()
    agent = WellnessAgent(model=model)
    agent_input = _build_input(_payload())

    # Warm-up — first calls pay LRU + first-touch costs.
    for _ in range(n_warmup):
        agent.tick(agent_input)

    samples = []
    for _ in range(n_iter):
        t0 = time.perf_counter()
        agent.tick(agent_input)
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples.sort()
    p50 = statistics.median(samples)
    p95 = samples[int(0.95 * (len(samples) - 1))]
    return {
        "n_iter": float(n_iter),
        "n_warmup": float(n_warmup),
        "min_ms": min(samples),
        "p50_ms": p50,
        "p95_ms": p95,
        "max_ms": max(samples),
        "mean_ms": statistics.fmean(samples),
        "stdev_ms": statistics.pstdev(samples),
        "trained_artifact": float(model.booster is not None),
    }


def main() -> Dict[str, float]:
    stats = measure()
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _RESULTS_DIR / f"wellness_{_date.today().isoformat()}.json"
    with out_path.open("w") as f:
        json.dump({"benchmark": "wellness_tick_latency", **stats}, f, indent=2)

    # Latency budget assertion (spec §3.4: 50 ms).
    budget_ms = 50.0
    line = (
        f"WellnessAgent.tick() latency  p50={stats['p50_ms']:.2f}ms  "
        f"p95={stats['p95_ms']:.2f}ms  budget={budget_ms:.0f}ms  "
        f"trained={'yes' if stats['trained_artifact'] else 'no'}"
    )
    print(line)
    print(f"Wrote {out_path}")
    if stats["p50_ms"] > budget_ms:
        raise SystemExit(
            f"FAIL: p50 latency {stats['p50_ms']:.2f}ms exceeds {budget_ms:.0f}ms budget"
        )
    return stats


if __name__ == "__main__":
    main()
