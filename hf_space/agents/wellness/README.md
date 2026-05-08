# WellnessAgent

Per `technical_spec.md` §3.4 + §7.

A 9-feature XGBoost regressor with native NaN handling produces a 0-100 Load
Score. A Platt-scaling sigmoid (fit on 14 days of paired Likert ratings)
calibrates the score to a 1-5 stress estimate (§7.3).

When XGBoost isn't installed (clean test venv) the agent transparently falls
back to a hand-tuned linear scorer with the same shape and interpretable
``drivers`` breakdown — the Reasoning Trace renders identically. Production
swaps in the trained booster as a single artefact load.

## Features (§7.1)

| # | Feature | Source | Window |
|---|---|---|---|
| 1 | rmssd_ms | HealthKit / Health Connect | 5-min |
| 2 | rmssd_z | derived | 5-min |
| 3 | sleep_debt_min | last 7d vs target | nightly |
| 4 | typing_entropy | custom IME | 60s |
| 5 | app_switch_rate | UsageStatsManager / DeviceActivityCenter | 60s |
| 6 | notif_dismiss_rate | NotificationListenerService | 60min |
| 7 | screen_on_min | usage stats | 60min |
| 8 | hour_of_day_sin | clock | tick |
| 9 | hour_of_day_cos | clock | tick |

## Tools

| Name | Purpose |
|---|---|
| `compute_load_score` | Predict 0-100 from a 9-feature vector. |
| `intervention_select` | Pick MUTE_GROUP_30 / BREATHE_478 / NAP_15 / PERMIT_LEISURE. |
| `correlation_check` | Spearman ρ on (score, stress 1-5) pairs. |
| `recovery_check` | True if score has dropped >=10 in the recent window. |

## Cold start (§7.5)

For the first 7 days the agent uses pilot population baselines
(`rmssd_p50_pop=42`, `rmssd_p10_pop=24`) and clamps confidence at 0.40. The
orchestrator multiplies utility by confidence so cold-start users get fewer
proactive surfaces.

## HRV missing (§7.6)

If `rmssd_ms` is missing the agent flags `hrv_unavailable=true` and clamps
output to [0, 70]. The orchestrator should never auto-execute a stress-class
intervention with `hrv_unavailable=true`.

## Fixtures

| File | Purpose |
|---|---|
| `fixtures/hrv_5days.csv` | RMSSD samples covering an exam-week stress arc. |
| `fixtures/typing_entropy.csv` | IME entropy bursts including 14:30 spike. |
| `fixtures/app_switch.csv` | Per-minute app-switch rate, peaks at 14/min. |
| `fixtures/sleep.csv` | Nightly asleep_min / rem / deep / efficiency. |

## Run tests

```bash
pytest agents/wellness -q
```
