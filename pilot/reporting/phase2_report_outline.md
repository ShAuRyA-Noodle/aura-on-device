# Aura — Phase 2 Pilot Report Outline

Submission deliverable for Samsung EnnovateX 2026, Phase 2. Anchored on the n=30 quantitative + n=8 qualitative pilot run on iOS via TestFlight, Weeks 8-10 of the build plan.

Reference: `plan.md` sections 22-23, `technical_spec.md` section 7.
Owner: Shaurya Punj, Shorya Gupta — Galaxy Brain, Thapar Institute of Engineering and Technology.
Last updated: 2026-05-07

---

## 0. Cover page

- Title: "Aura — Phase 2 Pilot Evidence"
- Team: Galaxy Brain
- Submission date: Week 10 of plan (Jul 9-15, 2026)
- Repo link: https://github.com/ShAuRyA-Noodle/Combobulating
- Pilot platform: iOS via TestFlight
- Pilot cohort: n=30 quant, n=8 qual, all unpaid friends from Thapar Institute of Engineering and Technology

---

## 1. Executive summary (1 page)

Single-page snapshot for judges who will not read the full report.

- One-line product description.
- One-paragraph headline result per KPI:
  - Effort reduction: X% (95% CI [L, H]) across 5 standardised tasks, n=30 paired.
  - Task completion: Y% on the prototype round vs Z% on baseline.
  - AI autonomy quality: Q% majority-correct on a 100-action sample, Fleiss kappa = K.
  - Satisfaction: M.MM on 5 across the 7 satisfaction dimensions.
  - Stress reduction: Spearman rho(load_score, self_rated_stress) = R, 95% bootstrap CI [L, H].
  - Willingness to pay at INR 199: P% yes (95% CI [L, H]).
- One sentence on the qualitative theme that surprised us most.
- One sentence on the limitation we are most honest about.

## 2. Methodology

### 2.1 Design

- Within-subject paired design. Each participant runs every task twice — baseline (existing toolkit) and prototype (Aura) — with order counterbalanced via per-participant deterministic seed.
- Pilot platform: iOS only via TestFlight. Galaxy port deferred to Phase 3 (emulator screen-record provided per `plan.md` section 21.1).
- Pilot duration: 7 days of in-the-wild use plus a 30-minute supervised task session.

### 2.2 Recruitment

- 30 quantitative participants from Thapar Institute campus, mixed branches and years, hostel and day-scholar mix.
- 8 qualitative participants drawn from the same pool plus 2 Bangalore-based for context balance.
- Disclosure: **all 30 participants are unpaid friends of the team.** This biases satisfaction and WTP upward and is acknowledged in the limitations section. The brief permits friends-and-family for a 30-50 user pilot.

### 2.3 Instrumentation

- 5 standardised tasks per `plan.md` section 22.2 — WhatsApp triage, morning brief, spend categorisation, stress recovery, notification triage.
- Auto-logged duration, tap count, and completion flag per task per round (`P0XX_tasks.csv`).
- Daily diary push at 18:00 (`P0XX_diary.csv`).
- 5-minute Load Score ticks across 7 days (`P0XX_loadscore.csv`).
- One row per Aura action with confirm/reject/ignore response (`P0XX_actions.csv`).
- 29-question post-trial survey (`quant_survey.md`).
- 60-minute semi-structured interview for the 8 qual participants (`qual_protocol.md`).

### 2.4 Statistical methods

- Means and 95% CI for every metric.
- Paired comparison via paired t-test where Shapiro-Wilk on the differences accepts normality (p > 0.05); Wilcoxon signed-rank otherwise.
- Cohen's d for paired effect size on every comparison.
- Spearman rho with 10,000-resample bootstrap percentile CI for Load Score validation.
- Cohen's kappa pairwise and Fleiss' kappa across the 3 raters for autonomy quality on the binary correct flag.
- Van Westendorp price sensitivity meter for the 4 PSM questions plus binary share at INR 199.

### 2.5 Ethics

- Written consent in plain English (`consent_form.md`); participants can withdraw at any time and request data deletion.
- No raw message body, no raw audio, no raw GPS leaves the device.
- All analysis CSVs are anonymised: participant ID `P001`-`P030` only, no names, phone numbers, or emails. Place names bucketed; group chat names hashed; free-text fields scrubbed.
- Raw data lives only on the team's encrypted local disk. The repo holds derived aggregates only.
- Per IRB-style standard despite no formal IRB: information sheet, consent, withdrawal rights, data destruction policy, harm-mitigation plan for Task 4 (stress).

## 3. Findings per KPI

### 3.1 Effort reduction (target >= 30%)

- Headline: pooled mean percent reduction in `duration_sec` across all 5 tasks, with 95% CI.
- Per-task forest plot from notebook 02 (`charts/02_duration_forest.png`).
- Per-task table: mean delta, 95% CI, test name (paired t / Wilcoxon), test statistic, p-value, Cohen's d.
- Same set for `tap_count`.
- Verdict: target met / not met / partially met, with one sentence per task that drives the headline.

### 3.2 Task completion (target >= 90%)

- Per-task per-round completion rate from notebook 01.
- Bar chart, baseline vs prototype.
- Edge cases: Task 4 skips, task abandons, network drops in Task 1.

### 3.3 AI autonomy quality (target >= 85%)

- 100 random actions sampled from `all_actions.csv`. 3-rater scoring on Likert 1-5 plus binary correct.
- Per-rater means and percent-correct.
- Pairwise Cohen's kappa table plus Fleiss' kappa on the binary correct.
- Aggregate majority-correct percentage — the headline number.
- Error analysis: the 14 disagreed-on actions, what went wrong, what the agents misjudged.

### 3.4 Satisfaction (target >= 4.5 of 5)

- Per-dimension Likert mean and 95% CI on the 7 satisfaction items (Q16-Q22 of the survey: trust, speed, privacy, autonomy, silence, recovery, Indian context).
- NPS score from Q28: promoters minus detractors.
- Bar chart of the 7 dimensions sorted by mean.

### 3.5 Stress reduction (n=8 qual, plus diary stress trend on n=30)

- Pre- vs post-pilot HRV summary for the 8 qual participants (mean RMSSD baseline week vs pilot week).
- Daily diary stress 1-5 trend across all 30 — chart from notebook 01.
- Load Score validation against self-rated stress: Spearman rho with bootstrap CI from notebook 03.
- Verdict: closed-loop biometric works as a credible-but-imperfect proxy.

### 3.6 Willingness to pay (target >= 60% at INR 199)

- Binary Q27 share with 95% CI.
- Van Westendorp PSM curves with OPP, IPP, PMC, PME marked (chart from notebook 05).
- Recommended launch price band based on PMC-PME range; positioning of INR 199 inside / above / below the band.

## 4. Qualitative themes

Drawn from the 8 semi-structured interviews and the daily diary entries. Coded by 2 raters per `qual_protocol.md`, thematic analysis with iterative coding.

- Theme 1 — silence as the headline feature. Quote bank.
- Theme 2 — trust in glass-box reasoning. Quote bank.
- Theme 3 — Indian context wins (UPI parsing, Zomato receipt, IRCTC). Quote bank.
- Theme 4 — failure modes. What broke, what felt creepy, what was ignored.
- Theme 5 — Phase 3 wishes — what users want next.

For each theme: 2-3 verbatim quotes with participant ID, plus a one-line researcher reading.

## 5. Limitations

Honest section. Calls out:

- All participants are unpaid friends of the team. Selection bias on enthusiasm and WTP.
- Cohort is single-institution (Thapar) plus 2 Bangalore-based — not representative of pan-India Gen Z.
- Pilot platform is iOS only — Galaxy port shown via emulator screen-record, not on real Galaxy hardware. Per `plan.md` section 21.
- Pilot duration is 7 days, not long enough to detect habituation drift or churn.
- Task 4 (stress) HRV requires consistent Apple Watch wear; not all participants wore the watch every day.
- Synthetic data was used during analysis-pipeline development. The Phase 2 submission replaces all synthetic blocks with real CSVs.
- WTP is a stated preference, not a revealed preference. We do not have payment data.

## 6. Raw data and reproducibility

- Repo: https://github.com/ShAuRyA-Noodle/Combobulating
- Path: `aura/pilot/derived/all_*.csv` — anonymised aggregates committed.
- Path: `aura/pilot/analysis/notebooks/` — 5 notebooks reproduce every number in this report.
- Path: `aura/pilot/raw/` — gitignored, lives on the team's encrypted local disk per `raw_data_template.md`.
- To reproduce: `cd aura/pilot/analysis && pip install -r requirements.txt && jupyter lab notebooks/`.

## 7. Ethics statement

- Voluntary participation; participants signed `consent_form.md`.
- No financial incentive paid (per locked decision in `plan.md` section 0).
- Right to withdraw and right to data deletion exercised at any time, no questions asked.
- No raw personal content (message bodies, emails, GPS coordinates, audio transcripts) left the device.
- Anonymisation rules per `raw_data_template.md` section 4.
- Distress mitigation for Task 4: optional, time-boxed, opt-out logged.
- The team takes responsibility for any harm caused by the pilot. Contact: workwithshaurya10@gmail.com.

## 8. Appendix

- A. Survey instrument verbatim (`quant_survey.md`).
- B. Task protocol verbatim (`task_protocol.md`).
- C. Consent form verbatim (`consent_form.md`).
- D. Data dictionary (`raw_data_template.md`).
- E. Per-notebook output: tables and charts from notebooks 01-05.
- F. Per-participant CSV manifest from `derived/_manifest.json`.

---

End of outline.
