"""Train the Load Score XGBoost regressor and Platt stress calibrator.

Outputs (relative to the repo root):
    aura/models/exports/load_score.json   — XGBoost native (portable) model.
    aura/models/exports/load_score.pkl    — pickled Booster + Platt params.
    aura/models/exports/load_score_meta.json — Spearman rho + bootstrap CI.
    aura/design/charts/calibration_plot.png — 1920x1080 calibration plot.

Run as a script:
    python -m agents.wellness.training.train
"""

from __future__ import annotations

import json
import pickle
from dataclasses import asdict
from pathlib import Path
from typing import Tuple

import numpy as np
import xgboost as xgb
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from .synth import FEATURE_NAMES, SynthConfig, generate_dataset


# Locked design palette — must match deck/web exports.
PALETTE = {
    "bg": "#FAF8F5",
    "ink": "#0E0E0E",
    "accent": "#FF5B2E",
    "muted": "#7A7A7A",
}


# Repo paths -----------------------------------------------------------------
_PKG = Path(__file__).resolve().parent
_AURA_ROOT = _PKG.parents[2]
EXPORTS_DIR = _AURA_ROOT / "models" / "exports"
CHART_DIR = _AURA_ROOT / "design" / "charts"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)


def train_xgb(
    X: np.ndarray, y_load: np.ndarray, seed: int = 137
) -> Tuple[xgb.Booster, dict]:
    """Fit an XGBoost regressor on the synthetic load targets.

    Returns the booster + a metrics dict {n_train, n_test, rmse_test, r2_test}.
    """

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y_load, test_size=0.25, random_state=seed
    )
    dtrain = xgb.DMatrix(X_tr, label=y_tr, feature_names=list(FEATURE_NAMES))
    dtest = xgb.DMatrix(X_te, label=y_te, feature_names=list(FEATURE_NAMES))
    params = {
        "objective": "reg:squarederror",
        "eta": 0.08,
        "max_depth": 5,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "min_child_weight": 4,
        "reg_lambda": 1.0,
        "seed": seed,
        "verbosity": 0,
    }
    booster = xgb.train(
        params,
        dtrain,
        num_boost_round=300,
        evals=[(dtest, "test")],
        early_stopping_rounds=20,
        verbose_eval=False,
    )
    preds = booster.predict(dtest)
    rmse = float(np.sqrt(np.mean((preds - y_te) ** 2)))
    ss_res = float(np.sum((preds - y_te) ** 2))
    ss_tot = float(np.sum((y_te - y_te.mean()) ** 2))
    r2 = 1.0 - ss_res / max(ss_tot, 1e-9)
    return booster, {
        "n_train": int(X_tr.shape[0]),
        "n_test": int(X_te.shape[0]),
        "rmse_test": rmse,
        "r2_test": r2,
    }


def fit_platt(load_scores: np.ndarray, stress_labels: np.ndarray) -> Tuple[float, float]:
    """Fit a 1-feature logistic mapping load -> P(stress >= 3).

    Returns (a, b) such that p = sigmoid(a * load + b). The runtime then
    rescales p in [0,1] to a 1-5 stress estimate via 1 + 4 * p.
    """

    y = (stress_labels >= 3).astype(int)
    clf = LogisticRegression(solver="lbfgs", max_iter=200)
    clf.fit(load_scores.reshape(-1, 1), y)
    a = float(clf.coef_[0, 0])
    b = float(clf.intercept_[0])
    return a, b


def _bootstrap_spearman_ci(
    pred: np.ndarray, true: np.ndarray, n_boot: int = 1000, seed: int = 137
) -> Tuple[float, float, float]:
    """Return (rho, ci_lo, ci_hi) at the 95% level via percentile bootstrap."""

    rng = np.random.default_rng(seed)
    n = len(pred)
    rho, _ = spearmanr(pred, true)
    boots = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        r, _ = spearmanr(pred[idx], true[idx])
        boots[i] = r if not np.isnan(r) else 0.0
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(rho), float(lo), float(hi)


def render_calibration_plot(
    pred_scores: np.ndarray,
    stress_labels: np.ndarray,
    platt_a: float,
    platt_b: float,
    rho: float,
    rho_ci: Tuple[float, float],
    out_path: Path,
) -> Path:
    """Save the calibration scatter + sigmoid curve at 1920x1080.

    Uses Aura's locked palette. No seaborn theme overrides — straight matplotlib.
    """

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(
        1, 2, figsize=(19.20, 10.80), dpi=100, facecolor=PALETTE["bg"]
    )
    fig.subplots_adjust(left=0.06, right=0.98, top=0.90, bottom=0.10, wspace=0.20)

    # ---- Left: predicted load vs self-rated stress with Platt sigmoid ------
    ax = axes[0]
    ax.set_facecolor(PALETTE["bg"])
    jitter = np.random.default_rng(7).normal(0.0, 0.08, size=len(stress_labels))
    ax.scatter(
        pred_scores,
        stress_labels + jitter,
        s=14,
        alpha=0.35,
        c=PALETTE["ink"],
        linewidths=0,
        label="held-out samples",
    )
    grid = np.linspace(0.0, 100.0, 256)
    sig = 1.0 / (1.0 + np.exp(-(platt_a * grid + platt_b)))
    stress_curve = 1.0 + 4.0 * sig
    ax.plot(
        grid, stress_curve, color=PALETTE["accent"], lw=3.0, label="Platt sigmoid (1-5)"
    )
    ax.set_xlim(0, 100)
    ax.set_ylim(0.5, 5.5)
    ax.set_xlabel("Predicted Load Score (0-100)", color=PALETTE["ink"], fontsize=14)
    ax.set_ylabel("Self-rated stress (1-5 Likert)", color=PALETTE["ink"], fontsize=14)
    ax.set_title(
        "Wellness Load Score - Calibration",
        color=PALETTE["ink"],
        fontsize=18,
        pad=14,
        loc="left",
        weight="bold",
    )
    for spine in ax.spines.values():
        spine.set_color(PALETTE["muted"])
    ax.tick_params(colors=PALETTE["ink"], labelsize=12)
    ax.legend(loc="lower right", frameon=False, fontsize=12, labelcolor=PALETTE["ink"])
    ax.grid(True, color=PALETTE["muted"], alpha=0.18, lw=0.6)

    # ---- Right: reliability bins ------------------------------------------
    ax2 = axes[1]
    ax2.set_facecolor(PALETTE["bg"])
    bins = np.linspace(0.0, 100.0, 11)
    bin_idx = np.digitize(pred_scores, bins) - 1
    bin_idx = np.clip(bin_idx, 0, 9)
    centers, observed, expected = [], [], []
    for k in range(10):
        mask = bin_idx == k
        if mask.sum() < 5:
            continue
        centers.append(0.5 * (bins[k] + bins[k + 1]))
        observed.append(stress_labels[mask].mean())
        sig_mid = 1.0 / (1.0 + np.exp(-(platt_a * centers[-1] + platt_b)))
        expected.append(1.0 + 4.0 * sig_mid)
    centers = np.array(centers)
    ax2.plot(
        centers,
        observed,
        marker="o",
        color=PALETTE["accent"],
        lw=2.5,
        ms=10,
        label="observed mean stress",
    )
    ax2.plot(
        centers,
        expected,
        marker="x",
        color=PALETTE["ink"],
        lw=2.0,
        ms=10,
        label="Platt expected",
    )
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0.5, 5.5)
    ax2.set_xlabel("Predicted Load Score bin (0-100)", color=PALETTE["ink"], fontsize=14)
    ax2.set_ylabel("Mean stress in bin", color=PALETTE["ink"], fontsize=14)
    ax2.set_title(
        "Reliability diagram",
        color=PALETTE["ink"],
        fontsize=18,
        pad=14,
        loc="left",
        weight="bold",
    )
    for spine in ax2.spines.values():
        spine.set_color(PALETTE["muted"])
    ax2.tick_params(colors=PALETTE["ink"], labelsize=12)
    ax2.legend(loc="lower right", frameon=False, fontsize=12, labelcolor=PALETTE["ink"])
    ax2.grid(True, color=PALETTE["muted"], alpha=0.18, lw=0.6)

    fig.suptitle(
        f"Spearman rho = {rho:.3f}   95% CI [{rho_ci[0]:.3f}, {rho_ci[1]:.3f}]",
        color=PALETTE["ink"],
        fontsize=14,
        y=0.965,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, facecolor=PALETTE["bg"], dpi=100)
    plt.close(fig)
    return out_path


def main(seed: int = 137) -> dict:
    cfg = SynthConfig(seed=seed)
    X, y_load, y_stress = generate_dataset(cfg)

    # Held-out split for calibration + Spearman.
    X_train, X_holdout, yL_train, yL_holdout, yS_train, yS_holdout = train_test_split(
        X, y_load, y_stress, test_size=0.30, random_state=seed
    )

    booster, train_metrics = train_xgb(X_train, yL_train, seed=seed)
    feature_names = list(FEATURE_NAMES)
    dholdout = xgb.DMatrix(X_holdout, feature_names=feature_names)
    pred_holdout = booster.predict(dholdout)

    rho, ci_lo, ci_hi = _bootstrap_spearman_ci(pred_holdout, yS_holdout, n_boot=1000, seed=seed)
    platt_a, platt_b = fit_platt(pred_holdout, yS_holdout)

    chart_path = render_calibration_plot(
        pred_holdout, yS_holdout, platt_a, platt_b, rho, (ci_lo, ci_hi),
        out_path=CHART_DIR / "calibration_plot.png",
    )

    # ---- save artifacts ------------------------------------------------
    json_path = EXPORTS_DIR / "load_score.json"
    pkl_path = EXPORTS_DIR / "load_score.pkl"
    meta_path = EXPORTS_DIR / "load_score_meta.json"

    booster.save_model(str(json_path))
    with pkl_path.open("wb") as f:
        pickle.dump(
            {
                "booster": booster,
                "platt_a": platt_a,
                "platt_b": platt_b,
                "feature_names": feature_names,
                "synth_config": asdict(cfg),
            },
            f,
        )

    meta = {
        "feature_names": feature_names,
        "synth_config": asdict(cfg),
        "train_metrics": train_metrics,
        "platt_a": platt_a,
        "platt_b": platt_b,
        "spearman_rho": rho,
        "spearman_ci95_low": ci_lo,
        "spearman_ci95_high": ci_hi,
        "n_holdout": int(len(yS_holdout)),
        "calibration_plot_path": str(chart_path.relative_to(_AURA_ROOT)),
        "model_json_path": str(json_path.relative_to(_AURA_ROOT)),
        "model_pkl_path": str(pkl_path.relative_to(_AURA_ROOT)),
    }
    with meta_path.open("w") as f:
        json.dump(meta, f, indent=2)

    return meta


if __name__ == "__main__":  # pragma: no cover
    out = main()
    print(json.dumps(out, indent=2))
