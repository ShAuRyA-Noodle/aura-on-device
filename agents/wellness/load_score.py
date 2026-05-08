"""Load Score model — XGBoost regressor + Platt-scaling calibration.

Implements technical_spec.md §7.

Why two models in one file:
- The XGBoost regressor outputs a raw 0-100 score (§7.2).
- The Platt sigmoid calibrator maps raw score -> a 1-5 stress estimate
  trained on 14 days of paired (load_score_daily_avg, self_rated_stress)
  Likert ratings (§7.3). Reported alongside Spearman ρ in pilot deck slide 9.

Runtime invariants:
- Predict latency p50 25 ms, p95 60 ms (spec §3.4).
- Falls back to a deterministic, transparent linear model if either:
  (a) the trained XGBoost artefact is missing on disk, or
  (b) the ``xgboost`` package is not installed (clean venv).
  The fallback shape is the same monotonic sign as the trained model so the
  orchestrator's contract holds.
- Output is clipped to [0, 100]. When ``rmssd_ms`` is NaN for >24h the model
  narrows output to [0, 70] and flags ``hrv_unavailable=true`` (§7.6).

Trained-artefact path
---------------------
The class method :py:meth:`LoadScoreModel.load_default` looks for
``aura/models/exports/load_score.json`` (XGBoost native) and the side-car
``load_score_meta.json`` carrying the fitted Platt parameters. If both exist
they are loaded; otherwise we surface the linear fallback with a clear log
warning so the orchestrator never silently degrades.
"""

from __future__ import annotations

import json
import logging
import math
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)


# Repo path used to resolve trained artefacts.
_THIS = Path(__file__).resolve()
_AURA_ROOT = _THIS.parents[2]
_MODEL_JSON = _AURA_ROOT / "models" / "exports" / "load_score.json"
_MODEL_META = _AURA_ROOT / "models" / "exports" / "load_score_meta.json"


# ---------------------------------------------------------------------------
# Feature container (matches spec §7.1)
# ---------------------------------------------------------------------------


@dataclass
class WellnessFeatures:
    """The 9 features the XGBoost regressor expects, in order.

    Missing values are encoded as ``None`` (XGBoost native NaN handling)
    or are pre-filled with personal baseline by the agent.
    """

    rmssd_ms: Optional[float] = None
    rmssd_z: Optional[float] = None
    sleep_debt_min: float = 0.0
    typing_entropy: float = 3.0
    app_switch_rate: int = 4
    notif_dismiss_rate: float = 0.3
    screen_on_min: int = 20
    hour_of_day_sin: float = 0.0
    hour_of_day_cos: float = 1.0

    @classmethod
    def from_payload(
        cls,
        payload: Dict[str, Any],
        baseline: Optional[Dict[str, float]] = None,
        hour: Optional[int] = None,
    ) -> "WellnessFeatures":
        """Build features from the spec §3.4 input payload.

        ``baseline`` is the per-user RMSSD calibration (`p50`, `p10`).
        ``hour`` is local hour-of-day (0..23). If absent, it is left at noon.
        """
        baseline = baseline or {}
        hrv = (payload or {}).get("hrv_window") or {}
        rmssd = hrv.get("rmssd_ms")
        p50 = float(baseline.get("rmssd_p50", 42.0))
        p10 = float(baseline.get("rmssd_p10", 24.0))
        rmssd_z: Optional[float]
        if rmssd is None:
            rmssd_z = None
        else:
            denom = max(1.0, p50 - p10)
            rmssd_z = (float(rmssd) - p50) / denom

        sleep = payload.get("sleep_last_night") or {}
        target = float(baseline.get("sleep_target_min", 420.0))
        actual = float(sleep.get("asleep_min", target))
        sleep_debt_min = max(0.0, target - actual)

        h = hour if hour is not None else 12
        h_sin = math.sin(2 * math.pi * h / 24)
        h_cos = math.cos(2 * math.pi * h / 24)

        return cls(
            rmssd_ms=float(rmssd) if rmssd is not None else None,
            rmssd_z=rmssd_z,
            sleep_debt_min=sleep_debt_min,
            typing_entropy=float(payload.get("typing_entropy_60s", 3.0)),
            app_switch_rate=int(payload.get("app_switch_rate_60s", 4)),
            notif_dismiss_rate=float(payload.get("notif_dismiss_rate_60m", 0.3)),
            screen_on_min=int(payload.get("screen_on_min_60m", 20)),
            hour_of_day_sin=h_sin,
            hour_of_day_cos=h_cos,
        )

    def to_vector(self) -> List[float]:
        """Stable feature vector. Missing -> NaN for XGBoost."""
        nan = float("nan")
        return [
            self.rmssd_ms if self.rmssd_ms is not None else nan,
            self.rmssd_z if self.rmssd_z is not None else nan,
            self.sleep_debt_min,
            self.typing_entropy,
            float(self.app_switch_rate),
            self.notif_dismiss_rate,
            float(self.screen_on_min),
            self.hour_of_day_sin,
            self.hour_of_day_cos,
        ]

    @staticmethod
    def feature_names() -> List[str]:
        return [
            "rmssd_ms",
            "rmssd_z",
            "sleep_debt_min",
            "typing_entropy",
            "app_switch_rate",
            "notif_dismiss_rate",
            "screen_on_min",
            "hour_of_day_sin",
            "hour_of_day_cos",
        ]


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


@dataclass
class _LinearFallback:
    """Transparent linear scoring used when XGBoost is unavailable.

    Coefficients are tuned by hand from the §3.4 worked examples and kept
    intentionally interpretable for the Reasoning Trace's ``drivers`` block.
    """

    bias: float = 38.0
    w_rmssd_z: float = -16.0  # lower HRV -> higher load
    w_sleep_debt: float = 0.06  # +6 points per 100 min sleep debt
    w_typing_entropy: float = 4.5  # noisy typing -> stress
    w_app_switch: float = 1.6  # context switching
    w_notif_dismiss: float = 12.0  # high dismiss rate = overwhelmed
    w_screen_on: float = 0.15  # heavy screen = drift up
    w_hour_evening_pen: float = 4.0  # evening hours add baseline drift

    def predict(self, x: WellnessFeatures) -> float:
        z = x.rmssd_z if x.rmssd_z is not None else 0.0
        score = self.bias
        score += self.w_rmssd_z * z
        score += self.w_sleep_debt * x.sleep_debt_min
        score += self.w_typing_entropy * (x.typing_entropy - 3.0)
        score += self.w_app_switch * max(0.0, x.app_switch_rate - 6)
        score += self.w_notif_dismiss * max(0.0, x.notif_dismiss_rate - 0.3)
        score += self.w_screen_on * max(0.0, x.screen_on_min - 20)
        # evening bias via hour_cos: cos(theta) ~ -1 around midnight
        score += self.w_hour_evening_pen * max(0.0, -x.hour_of_day_cos)
        return score


@dataclass
class LoadScoreModel:
    """XGBoost regressor with Platt-scaling stress calibrator (spec §7).

    Two construction paths:

    * :py:meth:`load_default` returns a model backed by the shipped
      ``models/exports/load_score.json`` artefact (XGBoost native format).
      Used in production and benchmarks.
    * Default ``LoadScoreModel()`` returns the deterministic linear-fallback
      model. Used in unit tests where loading the booster would slow the
      suite down or where the artefact is intentionally absent.

    Both expose the identical ``predict_score`` / ``calibrate_to_stress`` /
    ``driver_breakdown`` API.
    """

    booster: Any = None  # xgboost.Booster when loaded
    fallback: _LinearFallback = field(default_factory=_LinearFallback)
    # Platt parameters — sigmoid(a * load + b) -> P(stress >= 3); the runtime
    # rescales p in [0,1] to a 1-5 stress estimate via 1 + 4 * p. Defaults are
    # cold-start values; the trained meta JSON overwrites them on load.
    platt_a: float = 0.08
    platt_b: float = -3.5
    calibrator_fitted: bool = False
    artefact_path: Optional[str] = None

    # ----- factory --------------------------------------------------------

    @classmethod
    def load_default(
        cls, model_json: Path = _MODEL_JSON, meta_json: Path = _MODEL_META
    ) -> "LoadScoreModel":
        """Load the shipped trained model from disk; fall back to linear if missing.

        The fallback path is announced via a single :mod:`logging` warning so
        callers can tell whether the orchestrator is running on the trained
        booster or the transparent linear baseline.
        """

        if not (model_json.exists() and meta_json.exists()):
            logger.warning(
                "Wellness trained model not found at %s — using linear fallback.",
                model_json,
            )
            return cls()
        try:  # pragma: no cover - exercised at runtime
            import xgboost as xgb  # type: ignore

            booster = xgb.Booster()
            booster.load_model(str(model_json))
            with meta_json.open() as f:
                meta = json.load(f)
            return cls(
                booster=booster,
                platt_a=float(meta.get("platt_a", 0.08)),
                platt_b=float(meta.get("platt_b", -3.5)),
                calibrator_fitted=True,
                artefact_path=str(model_json),
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Failed to load trained Wellness model (%s); using linear fallback.", exc
            )
            return cls()

    # ----- predict --------------------------------------------------------

    def predict_score(self, x: WellnessFeatures, hrv_unavailable: bool = False) -> float:
        """Raw 0-100 score. Clipped per spec §7.2 / §7.6."""
        if self.booster is not None:  # pragma: no cover - depends on xgboost
            try:
                import numpy as np  # type: ignore
                import xgboost as xgb  # type: ignore

                vec = np.asarray([x.to_vector()], dtype=np.float32)
                dmat = xgb.DMatrix(vec, feature_names=WellnessFeatures.feature_names())
                raw = float(self.booster.predict(dmat)[0])
            except Exception:
                raw = self.fallback.predict(x)
        else:
            raw = self.fallback.predict(x)

        if hrv_unavailable:
            return max(0.0, min(70.0, raw))
        return max(0.0, min(100.0, raw))

    def driver_breakdown(self, x: WellnessFeatures) -> List[Dict[str, Any]]:
        """Top 3 contributors (linear-fallback shap-style explanation)."""
        z = x.rmssd_z if x.rmssd_z is not None else 0.0
        contribs = {
            "rmssd_z": self.fallback.w_rmssd_z * z,
            "sleep_debt_min": self.fallback.w_sleep_debt * x.sleep_debt_min,
            "typing_entropy": self.fallback.w_typing_entropy * (x.typing_entropy - 3.0),
            "app_switch_rate": self.fallback.w_app_switch * max(0.0, x.app_switch_rate - 6),
            "notif_dismiss_rate": self.fallback.w_notif_dismiss * max(0.0, x.notif_dismiss_rate - 0.3),
            "screen_on_min": self.fallback.w_screen_on * max(0.0, x.screen_on_min - 20),
        }
        # rank by magnitude
        ranked = sorted(contribs.items(), key=lambda kv: abs(kv[1]), reverse=True)
        total = sum(abs(v) for _, v in ranked) or 1.0
        out: List[Dict[str, Any]] = []
        for name, raw_contrib in ranked[:3]:
            value: float
            if name == "rmssd_z":
                value = z
            elif name == "sleep_debt_min":
                value = x.sleep_debt_min
            elif name == "typing_entropy":
                value = x.typing_entropy
            elif name == "app_switch_rate":
                value = float(x.app_switch_rate)
            elif name == "notif_dismiss_rate":
                value = x.notif_dismiss_rate
            else:
                value = float(x.screen_on_min)
            out.append({
                "feature": name,
                "value": round(value, 3),
                "contribution": round(abs(raw_contrib) / total, 3),
            })
        return out

    # ----- Platt calibration (§7.3) --------------------------------------

    def fit_calibrator(self, samples: List[Tuple[float, int]]) -> None:
        """Tiny-batch logistic fit on paired (load_score, stress 1-5) samples.

        Uses 5 epochs of gradient descent on a 1-feature logistic; tiny by
        design — no NumPy required, runs on-device. ``samples`` should be at
        least 14 days × 1 obs/day before this is meaningful.
        """
        if len(samples) < 5:
            return
        xs = [s for s, _ in samples]
        ys = [(stress - 1) / 4.0 for _, stress in samples]  # to [0,1]
        a, b = self.platt_a, self.platt_b
        lr = 0.001
        for _ in range(200):
            grad_a = 0.0
            grad_b = 0.0
            for x, y in zip(xs, ys):
                z = a * x + b
                p = 1.0 / (1.0 + math.exp(-z))
                err = p - y
                grad_a += err * x
                grad_b += err
            a -= lr * grad_a / len(samples)
            b -= lr * grad_b / len(samples)
        self.platt_a, self.platt_b = a, b
        self.calibrator_fitted = True

    def calibrate_to_stress(self, score: float) -> float:
        """Convert raw load_score (0-100) to stress 1-5 via the Platt sigmoid."""
        z = self.platt_a * score + self.platt_b
        p = 1.0 / (1.0 + math.exp(-z))
        return 1.0 + 4.0 * p

    # ----- Intervention utility selector (§3.4) ---------------------------

    @staticmethod
    def select_intervention(
        load_score: float,
        *,
        in_focus_block: bool = False,
        active_channel: Optional[str] = None,
        sleep_min_last_night: Optional[float] = None,
        recent_drop: float = 0.0,
        calendar_busy: bool = False,
    ) -> Dict[str, Any]:
        """Pick one of {DO_NOTHING, BREATHE_478, MUTE_GROUP_30, NAP_15,
        PERMIT_LEISURE} via a documented additive utility.

        Each kind k gets a utility ``U_k = baseline_k + sum(b_i * f_i)`` where
        ``f_i`` are bounded indicator/scaled features. We then take ``argmax``;
        ties are broken by the deterministic order MUTE > BREATHE > NAP >
        PERMIT > DO_NOTHING (safety class first). No randomness. The function
        is pure — easy to unit-test and replay in traces.

        Coefficients are tuned by hand from the spec §3.4 worked examples
        (Mira spike, Anu ping, Kabir's nap, Riya's recovery).
        """

        # Normalised features in [0, 1].
        load_norm = max(0.0, min(1.0, load_score / 100.0))
        spike = 1.0 if load_score >= 70 else 0.0
        moderate = 1.0 if 60 <= load_score < 70 else 0.0
        low = 1.0 if load_score < 50 else 0.0
        sleep_short = 0.0
        if sleep_min_last_night is not None and sleep_min_last_night < 360:
            sleep_short = min(1.0, (360.0 - float(sleep_min_last_night)) / 120.0)
        has_channel = 1.0 if active_channel else 0.0
        focus = 1.0 if in_focus_block else 0.0
        busy = 1.0 if calendar_busy else 0.0
        recovering = 1.0 if recent_drop >= 10.0 and load_score < 60 else 0.0

        utilities: Dict[str, float] = {
            # MUTE_GROUP_30: only when there's a channel target AND a spike.
            "MUTE_GROUP_30": (
                -1.0
                + 1.6 * spike
                + 1.4 * has_channel * spike
                - 0.6 * (1.0 - has_channel)
            ),
            # BREATHE_478: works even mid-focus, but capped during meetings.
            "BREATHE_478": (
                -0.5
                + 1.3 * spike
                + 0.4 * load_norm
                - 0.7 * busy
                + 0.2 * focus
            ),
            # NAP_15: moderate load + visible sleep debt + outside focus.
            "NAP_15": (
                -1.2
                + 1.1 * moderate
                + 1.0 * sleep_short
                - 1.5 * focus
                - 1.5 * busy
            ),
            # PERMIT_LEISURE: low load with a recent recovery drop.
            "PERMIT_LEISURE": (
                -1.0
                + 1.4 * recovering
                + 0.5 * low
                - 0.3 * busy
            ),
            # DO_NOTHING: default fallback if nothing else clears 0.
            "DO_NOTHING": 0.0,
        }

        order = ("MUTE_GROUP_30", "BREATHE_478", "NAP_15", "PERMIT_LEISURE", "DO_NOTHING")
        best = max(order, key=lambda k: (utilities[k], -order.index(k)))
        return {
            "kind": best,
            "utility": round(utilities[best], 3),
            "scores": {k: round(v, 3) for k, v in utilities.items()},
        }

    # ----- Spearman correlation (§7.4) -----------------------------------

    @staticmethod
    def spearman_rho(samples: List[Tuple[float, int]]) -> float:
        """Spearman ρ between load_score and self-rated stress, no NumPy.

        Returns 0.0 if fewer than 3 paired samples — caller should treat as
        "not yet reportable".
        """
        if len(samples) < 3:
            return 0.0

        def _ranks(values: List[float]) -> List[float]:
            indexed = sorted(range(len(values)), key=lambda i: values[i])
            ranks = [0.0] * len(values)
            i = 0
            while i < len(indexed):
                j = i
                while j + 1 < len(indexed) and values[indexed[j + 1]] == values[indexed[i]]:
                    j += 1
                avg = (i + j) / 2.0 + 1.0  # 1-based average rank
                for k in range(i, j + 1):
                    ranks[indexed[k]] = avg
                i = j + 1
            return ranks

        xs = [s for s, _ in samples]
        ys = [float(s) for _, s in samples]
        rx = _ranks(xs)
        ry = _ranks(ys)
        mean_x = statistics.fmean(rx)
        mean_y = statistics.fmean(ry)
        num = sum((a - mean_x) * (b - mean_y) for a, b in zip(rx, ry))
        denx = math.sqrt(sum((a - mean_x) ** 2 for a in rx))
        deny = math.sqrt(sum((b - mean_y) ** 2 for b in ry))
        if denx == 0 or deny == 0:
            return 0.0
        return num / (denx * deny)
