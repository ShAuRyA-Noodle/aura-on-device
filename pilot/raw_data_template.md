# Aura Pilot — Raw Data Schema and Naming Convention

Single source of truth for the per-participant CSVs the team will collect during the n=30 quant + n=8 qual pilot. One file per participant per data type. Anonymised IDs `P001`–`P030`. No name, phone number, or email anywhere in the CSV body.

Reference: `plan.md` §22.3, §23.5.
Last updated: 2026-05-07

---

## 1. Directory layout

```
pilot/
├── raw/
│   ├── P001/
│   │   ├── P001_consent.pdf            # scanned/photographed signed consent
│   │   ├── P001_tasks.csv              # one row per task attempt (10 rows: 5 tasks × 2 rounds)
│   │   ├── P001_survey.csv             # one row, 30 columns (Q0–Q29)
│   │   ├── P001_diary.csv              # 7 rows, 4 columns (day, q1, q2, q3)
│   │   ├── P001_loadscore.csv          # 7 days × 24h × 12 ticks/h ≈ 2016 rows
│   │   ├── P001_actions.csv            # one row per Aura action emitted in the 7 days
│   │   ├── P001_notes.txt              # researcher field notes, free text
│   │   └── P001_meta.json              # { device_model, ios_version, recruitment_channel, dates }
│   ├── P002/
│   │   └── ... same layout ...
│   └── ...
├── coded/
│   ├── interviews/
│   │   ├── P003_transcript.txt         # qualitative subset only
│   │   ├── P003_codes_rater1.csv
│   │   └── P003_codes_rater2.csv
│   └── autonomy/
│       ├── actions_sample_100.csv      # 100 randomly sampled actions from all P0XX_actions.csv
│       ├── ratings_rater1.csv
│       ├── ratings_rater2.csv
│       └── ratings_rater3.csv
└── derived/
    ├── all_tasks.csv                   # concatenation of every P0XX_tasks.csv
    ├── all_survey.csv
    ├── all_loadscore.csv
    ├── all_actions.csv
    └── all_diary.csv
```

`derived/` is rebuilt by `analysis/setup.py build_derived` and never edited by hand.

---

## 2. Naming convention

- Participant directory: `P\d{3}` zero-padded (e.g. `P001`, `P017`, `P030`).
- All filenames inside a participant folder begin with the participant ID.
- Timestamps: ISO 8601 in UTC (`2026-07-05T14:30:00Z`). Local time conversion done in analysis only.
- File encoding: UTF-8. Line endings: LF.
- CSV dialect: comma-separated, double-quoted strings, header row required.

---

## 3. Per-file schema

### 3.1 `P0XX_tasks.csv`

One row per task attempt. 10 rows expected (5 tasks × 2 rounds).

| column | type | example | notes |
|---|---|---|---|
| `participant_id` | string | `P017` | matches folder |
| `round` | enum | `baseline` / `prototype` | per `task_protocol.md` |
| `task_id` | int | `3` | 1–5 |
| `task_order_in_round` | int | `2` | 1–5, randomised |
| `started_at` | iso8601 | `2026-07-05T14:30:00Z` | UTC |
| `ended_at` | iso8601 | `2026-07-05T14:32:14Z` | UTC |
| `duration_sec` | float | `134.0` | derived but stored |
| `tap_count` | int | `9` | |
| `completion_flag` | enum | `success` / `partial` / `abandon` / `skipped` | |
| `self_rating_1to5` | int / null | `4` | from survey Q11–Q15; null if survey not yet filled |
| `notes` | string | `network dropped at 14:31` | optional |

### 3.2 `P0XX_survey.csv`

One row, columns named `Q0`–`Q29` plus `submitted_at`. Mirrors `quant_survey.md`.

### 3.3 `P0XX_diary.csv`

7 rows expected (one per day). Skips allowed.

| column | type | example |
|---|---|---|
| `participant_id` | string | `P017` |
| `day_index` | int | `3` (1–7) |
| `submitted_at` | iso8601 | `2026-07-03T22:14:00Z` |
| `q1_open` | string | "Aura caught the IRCTC mail before I did." |
| `q2_stress_1to5` | int | `4` |
| `q3_open` | string / null | null if skipped |

### 3.4 `P0XX_loadscore.csv`

Time-series of Load Score across the 7-day window. Tick = 5 min.

| column | type | notes |
|---|---|---|
| `participant_id` | string | |
| `tick_at` | iso8601 | |
| `load_score` | float [0,100] | |
| `rmssd_ms` | float / null | null when watch not worn |
| `typing_entropy` | float | |
| `app_switch_rate` | float | |
| `notif_dismiss_rate` | float | |
| `screen_on_min` | float | |
| `hrv_unavailable` | bool | |

### 3.5 `P0XX_actions.csv`

One row per autonomous or semi-autonomous Aura action emitted in the 7-day window.

| column | type | notes |
|---|---|---|
| `participant_id` | string | |
| `emitted_at` | iso8601 | |
| `action_type` | enum | `mute_group_30min`, `breathe_4_7_8`, `morning_brief`, `spend_alert`, `triage_card`, etc. |
| `agent` | enum | `comms` / `calendar` / `finance` / `wellness` |
| `confirm_required` | bool | |
| `user_response` | enum | `confirmed` / `rejected` / `ignored` / `auto` |
| `latency_ms` | int | orchestrator decision time |
| `load_score_at_emit` | float | |
| `silence_budget_remaining` | int | 0–3 |
| `trace_id` | string | foreign key to local trace store; not exported in raw |

### 3.6 `P0XX_meta.json`

```json
{
  "participant_id": "P017",
  "device_model": "iPhone 14",
  "ios_version": "17.5.1",
  "ram_tier": "B",
  "recruitment_channel": "thapar_whatsapp",
  "branch": "ECE",
  "year": 3,
  "living": "hostel",
  "city": "Patiala",
  "pilot_start": "2026-07-02",
  "pilot_end": "2026-07-09",
  "session_at": "2026-07-09T14:00:00Z",
  "consent_version": "v1.0_2026-05-07",
  "voice_prosody_consented": false
}
```

---

## 4. Anonymisation rules

- **No name, no phone, no email** in any CSV body. Only `participant_id`.
- **Sender names** in `actions.csv` and any derived comm-related field are stored as `sha256(name + per_user_salt)[:8]` — a stable hash that supports cross-event linkage but is not reversible.
- **Place names** are bucketed to {`hostel`, `class`, `mess`, `library`, `home`, `transit`, `other`} — never raw GPS or address.
- **Group chat names** in `tasks.csv` Task 1 are replaced with `chat_a`, `chat_b`, `chat_c`.
- **Free-text fields** (`q1_open`, `q3_open`, `notes`) are scrubbed for personal names by the researcher before commit. Replace with `[NAME]`. Roll numbers replaced with `[ROLL]`. Phone numbers replaced with `[PHONE]`.

---

## 5. Commit policy

- `pilot/raw/` is **gitignored**. Lives only on the Alienware encrypted disk.
- `pilot/coded/` is gitignored.
- `pilot/derived/` files **are committed** after manual review — these are aggregates only, no individual identifying data.
- The `derived/` files plus the analysis notebooks are what judges and the public see.

---

## 6. Build pipeline

`pilot/analysis/setup.py build_derived` does:
1. Iterate every `pilot/raw/P*/`.
2. Concatenate per-type CSVs into `pilot/derived/all_*.csv`.
3. Run schema validation (`pandera` or `jsonschema`) and fail loud on mismatches.
4. Emit a `pilot/derived/_manifest.json` with row counts and timestamps.

---

End of raw data template.
