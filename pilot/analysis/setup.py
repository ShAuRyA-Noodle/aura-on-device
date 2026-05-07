"""
Aura pilot analysis package — setup and build entry points.

Layout:
    pilot/
    ├── analysis/
    │   ├── setup.py                   <- this file (CLI: build_derived, lint)
    │   ├── aura_pilot/
    │   │   ├── __init__.py
    │   │   ├── io.py                  <- CSV readers + schema checks
    │   │   ├── stats.py               <- paired t / Wilcoxon / Cohen's d / κ / Spearman ρ
    │   │   ├── plots.py               <- matplotlib helpers, single-accent palette
    │   │   └── wtp.py                 <- Van Westendorp price sensitivity
    │   └── notebooks/
    │       ├── 01_descriptive.ipynb
    │       ├── 02_kpi_uplift.ipynb
    │       ├── 03_load_score_validation.ipynb
    │       ├── 04_autonomy_quality.ipynb
    │       └── 05_wtp.ipynb

Reference: plan.md sections 22, 23. technical_spec.md sections 7, 12.

Usage:
    python setup.py build_derived
    python setup.py lint
    pip install -e .
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from setuptools import find_packages, setup

PKG_NAME = "aura_pilot"
PKG_VERSION = "0.1.0"

INSTALL_REQUIRES = [
    "pandas>=2.2",
    "numpy>=1.26",
    "scipy>=1.13",
    "scikit-learn>=1.5",
    "statsmodels>=0.14",
    "matplotlib>=3.9",
    "seaborn>=0.13",
    "jupyterlab>=4.2",
    "pandera>=0.20",
]

EXTRAS_REQUIRE = {
    "dev": [
        "pytest>=8.2",
        "ruff>=0.5",
        "mypy>=1.10",
    ],
}


def _build_derived() -> int:
    """Concatenate per-participant CSVs into pilot/derived/all_*.csv.

    Idempotent. Fails loud on schema mismatch.
    """
    pilot_root = Path(__file__).resolve().parent.parent  # pilot/
    raw_root = pilot_root / "raw"
    derived_root = pilot_root / "derived"
    derived_root.mkdir(exist_ok=True)

    if not raw_root.exists():
        print(f"[build_derived] No raw dir at {raw_root}. Nothing to do.")
        return 0

    import pandas as pd  # local import to keep setup.py importable without deps

    file_types = ["tasks", "survey", "diary", "loadscore", "actions"]
    manifest: dict[str, int] = {}

    for ft in file_types:
        frames = []
        for participant_dir in sorted(raw_root.glob("P*")):
            f = participant_dir / f"{participant_dir.name}_{ft}.csv"
            if f.exists():
                frames.append(pd.read_csv(f))
        if frames:
            combined = pd.concat(frames, ignore_index=True)
            out = derived_root / f"all_{ft}.csv"
            combined.to_csv(out, index=False)
            manifest[ft] = len(combined)
            print(f"[build_derived] wrote {out} rows={len(combined)}")
        else:
            manifest[ft] = 0
            print(f"[build_derived] no {ft} files found.")

    (derived_root / "_manifest.json").write_text(json.dumps(manifest, indent=2))
    return 0


def _lint() -> int:
    """Run ruff + mypy if available."""
    import shutil
    import subprocess

    rc = 0
    for tool in ("ruff", "mypy"):
        if shutil.which(tool) is None:
            print(f"[lint] {tool} not on PATH, skipping.")
            continue
        proc = subprocess.run([tool, str(Path(__file__).parent)])
        rc |= proc.returncode
    return rc


def _cli() -> int:
    parser = argparse.ArgumentParser(prog="aura-pilot")
    parser.add_argument(
        "command",
        choices=["build_derived", "lint"],
        help="Operation to run.",
    )
    args, _ = parser.parse_known_args()
    if args.command == "build_derived":
        return _build_derived()
    if args.command == "lint":
        return _lint()
    return 1


# Allow `python setup.py build_derived` and `python setup.py lint` while still
# supporting `pip install -e .` via setuptools.
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] in {"build_derived", "lint"}:
    sys.exit(_cli())


setup(
    name=PKG_NAME,
    version=PKG_VERSION,
    description="Aura pilot analysis package — KPI stats, Load Score validation, WTP, autonomy κ.",
    author="Galaxy Brain (Shaurya Punj, Shorya Gupta)",
    license="MIT",
    packages=find_packages(include=["aura_pilot", "aura_pilot.*"]),
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "aura-pilot-build = aura_pilot.cli:build_derived_cli",
        ],
    },
)
