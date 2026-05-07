# Aura Pilot

Index for the Aura n=30 quantitative + n=8 qualitative pilot. iOS-only via TestFlight. All participants are unpaid friends from Thapar Institute of Engineering and Technology.

Reference: `plan.md` sections 22-23, `technical_spec.md` section 7.
Owner: Shaurya Punj, Shorya Gupta — Galaxy Brain.
Last updated: 2026-05-07

---

## What this directory holds

```
pilot/
├── README.md                       # this file
├── consent_form.md                 # participant consent — written, plain-English
├── recruitment_script.md           # WhatsApp + Discord outreach copy
├── qual_protocol.md                # 60-min semi-structured interview script + diary
├── quant_survey.md                 # 29-question post-trial survey (Google Form-ready)
├── task_protocol.md                # the 5 standardised tasks, baseline vs prototype
├── raw_data_template.md            # CSV schema, naming convention, anonymisation rules
├── analysis/
│   ├── README.md                   # how to run the notebooks
│   ├── requirements.txt            # pinned deps
│   ├── setup.py                    # build_derived CLI
│   ├── charts/                     # PNG exports from the notebooks
│   └── notebooks/
│       ├── 01_descriptive.ipynb
│       ├── 02_kpi_uplift.ipynb
│       ├── 03_load_score_validation.ipynb
│       ├── 04_autonomy_quality.ipynb
│       └── 05_wtp.ipynb
└── reporting/
    └── phase2_report_outline.md    # Phase 2 deliverable outline for Samsung judges
```

`raw/` and `coded/` are gitignored. They live only on the team's encrypted local disk per `raw_data_template.md`. Only `derived/` aggregates and the analysis notebooks are committed.

---

## Cohort

- **n = 30 quantitative.** 5 standardised tasks per `task_protocol.md`, run twice (baseline + prototype) per participant. Order counterbalanced.
- **n = 8 qualitative.** Subset of the 30, plus 2 Bangalore-based for context balance. 60-minute semi-structured interview after 7 days of in-the-wild use.
- **Recruitment channel:** Thapar campus WhatsApp groups and Thapar Discord, by personal outreach from the team.
- **Disclosure:** all participants are **unpaid friends** of the team. No incentive paid (locked in `plan.md` section 0). The brief permits friends-and-family for a 30-50 user pilot. Selection bias on enthusiasm and willingness-to-pay is acknowledged in the Phase 2 limitations section.
- **Pilot platform:** iOS only via TestFlight. Galaxy port deferred to Phase 3 emulator screen-record.

---

## Timeline

Anchored on the build plan timeline (`plan.md` section 24).

| Week | Dates (2026) | What happens |
|---|---|---|
| Week 8 | Jun 25 - Jul 1 | Qualitative pilot: 8 participants on TestFlight, daily diary, interview round 1 at end of week. |
| Week 9 | Jul 2 - 8 | Quantitative pilot: 30 participants, 5 standardised tasks logged, surveys collected. |
| Week 10 | Jul 9 - 15 | Analysis: notebooks 01-05 run on real data, raw CSVs published, Phase 2 deliverable submitted. |

Phase 2 submission deadline lands at the end of Week 10 per the EnnovateX timeline.

---

## KPI targets (LOCKED)

| KPI | Target | Notebook |
|---|---|---|
| Effort reduction | >= 30% | `02_kpi_uplift.ipynb` |
| Task completion | >= 90% | `01_descriptive.ipynb` |
| AI autonomy quality | >= 85% | `04_autonomy_quality.ipynb` |
| Satisfaction | >= 4.5 / 5 | `01_descriptive.ipynb` (survey block) |
| Stress reduction (HRV-loop, n=8) | measurable | `03_load_score_validation.ipynb` |
| Willingness to pay at INR 199/mo | >= 60% | `05_wtp.ipynb` |

Statistical reporting standard per `plan.md` section 22.3:

- Means with 95% confidence intervals.
- Paired t-test where data is approximately normal; Wilcoxon signed-rank otherwise.
- Cohen's d for effect size.
- Cohen's kappa for inter-rater agreement.
- Spearman rho with bootstrap 95% CI for Load Score validation.

---

## Ethics — IRB-style standard

The team has no formal IRB available at the undergraduate level at Thapar. We hold ourselves to an IRB-style standard regardless.

1. **Informed consent.** Every participant signs `consent_form.md`. Plain English. Names what Aura reads, where data lives, the right to withdraw, and the right to data deletion.
2. **Voluntary participation.** No coercion. No financial incentive paid (so participation cannot be motivated by money). Friends are explicitly told they may decline without it affecting the friendship.
3. **Right to withdraw.** Any participant may withdraw at any time, no questions asked, with full data deletion on request.
4. **Anonymisation.** Per `raw_data_template.md` section 4. Participant IDs `P001`-`P030` only. No names, phone numbers, emails in any committed file. Place names bucketed; group chat names hashed; free-text fields scrubbed.
5. **Data minimisation.** No raw message body, no raw audio, no raw GPS leaves the participant's device. Aura processes signals on-device and stores structured metadata only.
6. **Storage.** Raw per-participant CSVs live only on the team's encrypted local disk. The repo holds derived aggregates only.
7. **Distress mitigation.** Task 4 (stress recovery) is mild and time-boxed. Any participant who wants to skip it can — Task 4 is optional and noted in their CSV.
8. **Transparency.** Every participant may request a copy of their per-participant CSV before we anonymise and publish.
9. **Disclosure of relationship.** All participants are unpaid friends of the team. This is disclosed in every report and every submission.
10. **Contact.** Any participant or judge with concerns can contact: workwithshaurya10@gmail.com.

---

## How to run the analysis

```bash
cd aura/pilot/analysis
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m ipykernel install --user --name=aura-pilot --display-name "Aura Pilot"
jupyter lab notebooks/
```

Pick the `Aura Pilot` kernel. Run all cells top-to-bottom. Each notebook runs end-to-end on synthetic data when real data is absent — the synthetic blocks are flagged with a `## SYNTHETIC DATA — REPLACE WITH REAL` markdown header.

When real data lands in `pilot/raw/P001/` through `pilot/raw/P030/`:

```bash
python setup.py build_derived
```

This concatenates per-participant CSVs into `pilot/derived/all_*.csv` and writes `_manifest.json` with row counts. The notebooks then prefer real CSVs over synthetic when both exist.

---

## Reporting

The Phase 2 deliverable for Samsung judges is `reporting/phase2_report_outline.md`. It maps directly onto the 6 KPIs and reuses the charts produced by the notebooks.

End of pilot README.
