# Aura Pilot — Analysis

Notebooks for the n=30 quantitative + n=8 qualitative pilot on iOS TestFlight. Reference: `plan.md` sections 22, 23 and `technical_spec.md` section 7.

Last updated: 2026-05-07
Owner: Shaurya Punj, Shorya Gupta (Galaxy Brain — Thapar Institute)

---

## What is here

```
analysis/
├── setup.py                 # build_derived CLI; pip install -e .
├── requirements.txt         # pinned versions
├── README.md                # this file
├── charts/                  # notebook PNG/PDF exports land here
└── notebooks/
    ├── 01_descriptive.ipynb           # demographics, device mix, completion rates
    ├── 02_kpi_uplift.ipynb            # baseline vs prototype paired tests, Cohen's d, 95% CI
    ├── 03_load_score_validation.ipynb # Load Score vs self-rated stress, Spearman rho + bootstrap CI
    ├── 04_autonomy_quality.ipynb      # 3-rater agreement on 100 actions, Cohen's kappa
    └── 05_wtp.ipynb                   # Van Westendorp meter + binary WTP at INR 199
```

Every notebook runs end-to-end on synthetic data. The synthetic blocks are flagged with a `## SYNTHETIC DATA — REPLACE WITH REAL` markdown header. Replace those blocks with `pd.read_csv("../../derived/all_*.csv")` once the raw pilot CSVs are processed via `python setup.py build_derived`.

---

## How to run

### One-time setup

```bash
cd aura/pilot/analysis
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m ipykernel install --user --name=aura-pilot --display-name "Aura Pilot"
```

### Open the notebooks

```bash
jupyter lab notebooks/
```

Pick the `Aura Pilot` kernel. Run all cells top-to-bottom.

### Build derived data from raw

When real participant data lands in `pilot/raw/P001/` through `pilot/raw/P030/`:

```bash
cd aura/pilot/analysis
python setup.py build_derived
```

This concatenates every per-participant CSV into `pilot/derived/all_*.csv` and writes `pilot/derived/_manifest.json` with row counts. The notebooks then prefer real CSVs over synthetic when both exist.

---

## Notebook contract

- Each notebook is a real `.ipynb` (validated by `python -c "import json; json.load(open(...))"`).
- Cells alternate markdown explanation and executable Python.
- Imports: `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `statsmodels` where used.
- Synthetic data is generated from `numpy.random` with a documented seed (default 20260507 — today's date).
- Charts export to `../charts/` as PNG at 200 dpi.
- No banned words.

---

## Statistical reporting standard

Per `plan.md` section 22.3:

- Means with 95% confidence intervals.
- Paired t-test where data is approximately normal; Wilcoxon signed-rank otherwise (Shapiro-Wilk on differences picks).
- Cohen's d for effect size on every paired comparison.
- Cohen's kappa for inter-rater agreement (notebook 04).
- Spearman rho with bootstrap 95% CI for Load Score validation (notebook 03).

---

## Reproducibility

All synthetic seeds, sample sizes, and analysis steps are captured in the notebooks themselves. The version log lives in git history at `Combobulating/aura/pilot/analysis/`.
