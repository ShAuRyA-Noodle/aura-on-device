"""Synthetic dataset generator for the Load Score regressor.

Why synthetic?
- Real HRV/typing/app-switch traces would require multi-day pilot recordings
  that we do not yet have at training time. The fixtures in
  ``agents/wellness/fixtures/*.csv`` are hand-curated for the worked examples
  in tests; we expand them programmatically here using a documented physical
  model so the trained XGBoost regressor has the same monotonic shape that
  the linear fallback encodes.

Documented noise model
----------------------
- Ground-truth load is a hand-tuned linear-plus-mild-interaction function of
  five physical drivers:
    rmssd_ms, typing_entropy, app_switch_rate, sleep_debt_min, notif_dismiss_rate.
- Each draw adds independent Gaussian noise sigma=4 to the load target.
- Self-rated stress (1-5 Likert) is a piecewise function of the *true* load
  with sigma=0.6 Gaussian jitter, then quantised back into [1,5]. This mimics
  the imperfect user-rating channel — the same generator the pilot deck §9
  uses to demonstrate Spearman ρ recovery.

The generator is deterministic given a seed; the default seed (137) is the
one shipped artifacts were trained on.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

import numpy as np


FEATURE_NAMES = (
    "rmssd_ms",
    "rmssd_z",
    "sleep_debt_min",
    "typing_entropy",
    "app_switch_rate",
    "notif_dismiss_rate",
    "screen_on_min",
    "hour_of_day_sin",
    "hour_of_day_cos",
)


@dataclass
class SynthConfig:
    """Knobs for the synthetic generator. Defaults match the shipped model."""

    n_samples: int = 1200
    seed: int = 137
    rmssd_p50: float = 42.0
    rmssd_p10: float = 24.0
    sleep_target_min: float = 420.0
    label_noise_sigma: float = 4.0
    stress_noise_sigma: float = 0.6


def generate_dataset(cfg: SynthConfig | None = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (X, y_load, y_stress) with shapes (N, 9), (N,), (N,).

    ``y_load`` is the continuous 0-100 score, ``y_stress`` is the 1-5 Likert.
    """

    cfg = cfg or SynthConfig()
    rng = np.random.default_rng(cfg.seed)
    n = cfg.n_samples

    # Physical features. Ranges chosen to span the realistic operating window
    # plus a small margin so the trees see the boundary regions.
    rmssd_ms = rng.normal(loc=cfg.rmssd_p50, scale=10.0, size=n).clip(12.0, 90.0)
    sleep_debt_min = rng.gamma(shape=2.0, scale=45.0, size=n).clip(0.0, 360.0)
    typing_entropy = rng.normal(loc=3.2, scale=0.7, size=n).clip(1.5, 6.0)
    app_switch_rate = rng.poisson(lam=5.0, size=n).clip(0, 30).astype(float)
    notif_dismiss_rate = rng.beta(a=2.0, b=4.0, size=n)
    screen_on_min = rng.normal(loc=22.0, scale=10.0, size=n).clip(0.0, 60.0)
    hour = rng.integers(low=0, high=24, size=n).astype(float)

    rmssd_z = (rmssd_ms - cfg.rmssd_p50) / max(1.0, cfg.rmssd_p50 - cfg.rmssd_p10)
    h_sin = np.sin(2 * math.pi * hour / 24.0)
    h_cos = np.cos(2 * math.pi * hour / 24.0)

    # Ground-truth physical load model — same monotonic shape as
    # _LinearFallback in load_score.py, plus a mild HRV * entropy interaction
    # so the tree booster has something non-linear to learn.
    load = (
        38.0
        - 16.0 * rmssd_z
        + 0.06 * sleep_debt_min
        + 4.5 * (typing_entropy - 3.0)
        + 1.6 * np.maximum(0.0, app_switch_rate - 6.0)
        + 12.0 * np.maximum(0.0, notif_dismiss_rate - 0.3)
        + 0.15 * np.maximum(0.0, screen_on_min - 20.0)
        + 4.0 * np.maximum(0.0, -h_cos)
        + 0.6 * np.maximum(0.0, typing_entropy - 3.0) * np.maximum(0.0, -rmssd_z)
    )
    load = load + rng.normal(loc=0.0, scale=cfg.label_noise_sigma, size=n)
    load = load.clip(0.0, 100.0)

    # Self-rated stress 1-5: piecewise sigmoid around mid load, then quantise.
    stress_continuous = 1.0 + 4.0 / (1.0 + np.exp(-(load - 50.0) / 12.0))
    stress_continuous = stress_continuous + rng.normal(0.0, cfg.stress_noise_sigma, size=n)
    stress = np.rint(stress_continuous).clip(1, 5).astype(int)

    X = np.column_stack(
        [
            rmssd_ms,
            rmssd_z,
            sleep_debt_min,
            typing_entropy,
            app_switch_rate,
            notif_dismiss_rate,
            screen_on_min,
            h_sin,
            h_cos,
        ]
    ).astype(np.float32)

    return X, load.astype(np.float32), stress
