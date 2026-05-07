# Aura — Data Flow Walkthroughs

Three concrete flows. Numbered steps with timestamps. Cross-reference: `plan.md` §11 (stress-driven mute reference flow), `technical_spec.md` §5 (worked traces).

Each flow assumes Tier B device (iPhone 14 / S22 base), Phi-3-mini orchestrator, Gemma 2B with hot-swappable LoRA adapters, all data on-device. Wall-clock timestamps are local IST.

---

## Flow 1 — Morning Brief (Rohan, plan §7 Journey A)

User context: Rohan, 22, junior dev in Bangalore. Slept 5.2 hours. 9:00 AM DSA quiz. Cab ETA from PG to LT-3 is 22 minutes. Twelve unread Gmail threads overnight including one from his prof at 23:11.

| # | Time (IST) | Component | Action | Output |
|---|---|---|---|---|
| 1 | 07:00:00.000 | WellnessAgent | `tick()` triggered by Health Connect HRV poll | `sleep_min_last=312`, `state=BASELINE` |
| 2 | 07:00:00.040 | Watch | Background haptic for sleep brief, glance shows "Slept 5.2h. Push gym to evening." | tile rendered |
| 3 | 07:44:55.000 | Sense Layer | Phone unlock detected via screen-state event | `unlock_event` posted to signal_q |
| 4 | 07:45:00.080 | CalendarAgent | `tick()` reads EventKit `eventsToday()` | `next_event=DSA Quiz @ 09:00 LT-3` |
| 5 | 07:45:00.120 | CommsAgent | `triage_inbox(scope=unread_24h)` over 12 Gmail threads | classified: 1 prof email, 3 receipts, 8 promotional |
| 6 | 07:45:00.310 | CalendarAgent | `travel_aware_alert(e_DSA, user_loc)` via Distance Matrix | `leave_by=08:15`, `travel_min=22` |
| 7 | 07:45:00.430 | Orchestrator | `Listening → Deliberating` after all four agents return | candidate set: `SHOW_BRIEF` (0.82), `LEAVE_BY_ALERT` (0.71), `BATCH_DIGEST` (0.55), `do_nothing` (0.30) |
| 8 | 07:45:00.620 | Orchestrator | Silence Budget check: tokens_today=3, both `SHOW_BRIEF` and `LEAVE_BY_ALERT` selected (auto-execute allowlist) | budget decremented to 1 (two tokens consumed) |
| 9 | 07:45:00.640 | Orchestrator | Trace `tr_a8c12fb091e3` written, `rationale_source=template` | trace persisted to `memory.sqlite` |
| 10 | 07:45:00.880 | Phone | SwiftUI Brief card renders: sleep, quiz, leave-by, prof email | first frame |
| 11 | 07:45:00.900 | Watch | Glance updates with "Leave 8:15 — quiz at 9" | haptic |
| 12 | 07:45:14.000 | User | Taps "Useful" on the Brief card | `useful_tap` event |
| 13 | 07:45:14.030 | Orchestrator | Silence Budget refunded by 1 token | budget=2 |
| 14 | 08:00:00.000 | Orchestrator | `LEAVE_BY_ALERT` fires as scheduled | phone notification |
| 15 | 08:14:50.000 | Orchestrator | `Cooldown` window for `SHOW_BRIEF` kind expires | next surface eligible |

Reasoning Trace excerpt (full schema in `technical_spec.md` §5.6.a):

```json
{
  "trace_id": "tr_a8c12fb091e3",
  "ts": "2026-05-07T07:45:00.640+05:30",
  "trigger": {"source":"phone_unlock","value":{"hour":7.75}},
  "chosen": "SHOW_BRIEF",
  "rationale": "Quiz in 75 min, 22 min travel, prof emailed at 23:11. One card.",
  "rationale_source": "template",
  "confirm_required": false,
  "outcome": "executed_auto"
}
```

Privacy notes: prof email body never persisted. Stored: `{sender_hash=h_prof, intent=ACTIONABLE, urgency=0.78, ts=2026-05-06T23:11}`. Receipt amounts persisted as `Transaction` nodes; subjects discarded.

---

## Flow 2 — Quiet Group Chat (Mira, plan §7 Journey B)

User context: Mira, 20, design student in Mumbai. Studying. WhatsApp project group fires 47 messages in 8 minutes between 22:30 and 22:38. HRV has dropped from 38 ms baseline to 28.4 ms. Typing-entropy bucket spikes.

| # | Time (IST) | Component | Action | Output |
|---|---|---|---|---|
| 1 | 22:30:58.000 | NotificationListener | First of 47 storm notifications posted | `notif_q` enqueued |
| 2 | 22:30:58.012 | Sense Layer | `NotifEvent{id=n_8a01, app=com.whatsapp, channel=g_h_88a, sender_hash=h_a01}` | bus |
| 3 | 22:31:05.000 to 22:38:14.000 | Sense Layer | 46 more `NotifEvent` records, all same channel | `notif_q` at 47/256 |
| 4 | 22:31:00.000 | WellnessAgent | `compute_load_score(features)` from rmssd 28.4, switch_rate 14, entropy 4.91 | `load_score=78`, `state=STRESSED` |
| 5 | 22:31:14.140 | CommsAgent | `tick()` over the 47-message batch | `urgent=3`, `muted=44`, `top_action=BATCH_DIGEST` |
| 6 | 22:31:14.260 | WellnessAgent | `intervention_select(78, ctx)` → `MUTE_GROUP_30` | confidence 0.74 |
| 7 | 22:31:14.310 | Orchestrator | Candidate ranking: `MUTE_GROUP_30` (0.78), `BATCH_DIGEST` (0.62), `BREATHE_478` (0.55), `do_nothing` (0.30) | top above threshold |
| 8 | 22:31:14.330 | Orchestrator | Hard-cap check: window cap clear (no surface in last 30 min), daily cap clear (Wellness safety class is uncapped); Silence Budget unaffected because `MUTE_*` is safety class | proceed |
| 9 | 22:31:14.380 | Orchestrator | `confirm_required=true` on `MUTE_GROUP_30`; `AwaitingConfirm` entered | trace `tr_b1d77ef33c20` started |
| 10 | 22:31:14.620 | Phone | SwiftUI card "Mute project group 30 min? You're in flow." | rendered |
| 11 | 22:31:14.910 | Watch | Haptic + glance "Mute 30 min?" | tap-to-confirm |
| 12 | 22:31:23.000 | User | Taps confirm on Watch | `tap_yes` event |
| 13 | 22:31:23.060 | Orchestrator | `Executing`; tool dispatcher installs notification suppression rule scoped to channel `g_h_88a` for 1800 s | rule active |
| 14 | 22:31:23.110 | Orchestrator | `LoggingTrace`; outcome=`confirmed`; tap_lat_ms=8420 | persisted |
| 15 | 22:31:23.150 | Orchestrator | `Cooldown` for `MUTE_*` kind starts | 30-min window |
| 16 | 22:36:00.000 | CommsAgent | Background `batch_summarize` of suppressed messages | digest one-line ready |
| 17 | 23:01:23.000 | Orchestrator | Mute window ends; one-line digest surface scheduled | passive |
| 18 | 23:01:23.060 | Phone | Card: "While muted: 3 actionable items, 44 social." | tap to expand |
| 19 | 23:01:34.000 | User | Taps "Useful" on the digest | refund |
| 20 | 23:01:34.040 | Orchestrator | Silence Budget refunded by 1 token (from non-safety surfaces earlier in day) | persisted |

Reasoning Trace excerpt (full schema in `technical_spec.md` §5.6.b):

```json
{
  "trace_id": "tr_b1d77ef33c20",
  "ts": "2026-05-07T22:31:14.380+05:30",
  "trigger": {"source":"comms_burst","value":{"count":47,"window_min":8}},
  "chosen": "MUTE_GROUP_30",
  "rationale": "HRV down 1.4 SD, 47 messages in 8 min, 3 actionable. Mute 30 min, digest after.",
  "rationale_source": "llm",
  "confirm_required": true,
  "outcome": "confirmed",
  "redactions": ["signals.channel"]
}
```

Privacy notes: 47 message bodies never persisted. Stored on the `Conversation` node: a 24-hour rolling summary with `actionable_count=3`, `social_count=44`, `channel=g_h_88a` (hashed). The three actionable items are persisted as separate `Conversation` summary chunks with `intent_label=ACTIONABLE` and embeddings derived from the summary, not the raw text.

---

## Flow 3 — Spend Mirror (Kabir, plan §7 Journey D)

User context: Kabir, 24, freelance designer in Delhi. Gig payout of ₹85,000 received Day 0. Across Days 1–3 he spends ₹37,000 over 14 UPI debits — restaurants, Amazon, Uber. FinanceAgent watches for velocity.

| # | Time (IST) | Component | Action | Output |
|---|---|---|---|---|
| 1 | Day 0, 11:14 | Sense Layer | SMS from `VK-HDFCBK` "Credited Rs.85,000 ..." | `s_0` enqueued |
| 2 | Day 0, 11:14:00.045 | FinanceAgent | `parse_sms(s_0)` → `Transaction{amount=85000, type=CREDIT, account=a_hdfc_1234}` | seed balance set |
| 3 | Day 1, 13:10 | Sense Layer | Receipt from `noreply@swiggy.in` arrives | `gmail_thread tg_r01` |
| 4 | Day 1, 13:10:01.120 | FinanceAgent | `parse_gmail_receipt(tg_r01)` → `Transaction{amount=420, merchant=Swiggy, category=food_delivery}` | persisted |
| 5 | Days 1–3 | Sense Layer | 13 more UPI SMS messages and 1 more Gmail receipt | parsed and categorised in turn |
| 6 | Day 3, 20:00:00.000 | FinanceAgent | Daily `tick()` window | aggregates ready |
| 7 | Day 3, 20:00:00.060 | FinanceAgent | `anomaly_flag(history, window_days=14)` → `[{food 6, retail 4, transport 4, rate 3x avg}]` | velocity flag |
| 8 | Day 3, 20:00:00.120 | FinanceAgent | `predict_eom_balance(history, balance)` → `hits_zero=2026-05-11`, confidence 0.62 | LSTM forecast |
| 9 | Day 3, 20:00:00.260 | Orchestrator | Candidate ranking: `SURFACE_ANOMALY` (0.74), `PROJECT_BALANCE` (0.68), `do_nothing` (0.30) | both auto-execute |
| 10 | Day 3, 20:00:00.290 | Orchestrator | Silence Budget check: `tokens_today=3` at start; both surfaces are auto-execute and consume from budget; bundled into a single combined card to spend only one token | budget=2 |
| 11 | Day 3, 20:00:00.310 | Orchestrator | Trace `tr_c7e22a90f418` written, `rationale_source=template` | persisted |
| 12 | Day 3, 20:00:00.560 | Phone | Card: "3-day spend ₹37,000 — 3× your baseline. At this rate, balance hits zero by 11 May." | rendered, no confirm required |
| 13 | Day 3, 20:00:46 | User | Taps "Useful" | refund |
| 14 | Day 3, 20:00:46.030 | Orchestrator | Silence Budget refunded by 1 token | budget=3 |
| 15 | Day 3, 20:01 | User | Taps card → opens Reasoning Trace drawer | drawer renders |
| 16 | Day 3, 20:01:00.080 | Memory Graph | Read of trace + signals; audit row `op=read, target=tr_c7e22a90f418` | hash-chained |

Reasoning Trace excerpt (full schema in `technical_spec.md` §5.6.c):

```json
{
  "trace_id": "tr_c7e22a90f418",
  "ts": "2026-05-09T20:00:00.310+05:30",
  "trigger": {"source":"finance_anomaly","value":{"reason":"velocity_3x"}},
  "chosen": "SURFACE_ANOMALY+PROJECT_BALANCE",
  "rationale": "3-day spend 3x your baseline. At this rate, balance hits zero by 11 May.",
  "rationale_source": "template",
  "confirm_required": false,
  "outcome": "executed_auto",
  "redactions": ["signals.balance_seed"]
}
```

Privacy notes: SMS bodies and Gmail receipt bodies are not persisted. Stored as 14 `Transaction` nodes plus an `anomaly_flag` derived field. Balance is rounded to the nearest ₹500 in the trace export for the `share-with-friend` redaction profile (see `technical_spec.md` §5.4).

---

## Cross-cutting notes

- Every flow above goes through the same orchestrator state machine (`Idle → Listening → Deliberating → AwaitingConfirm | Executing → LoggingTrace → Cooldown → Idle`).
- Every persisted trace satisfies `trace.v1.json` (`technical_spec.md` §4.6).
- The Silence Budget rules: safety-class Wellness interventions never consume tokens; auto-execute Calendar / Comms / Finance surfaces consume one token per surface, with combined cards costing one token total; user "useful" tap refunds one token capped at the daily ceiling of 3.
- All cross-process boundaries (Sense → Intelligence → Memory → Experience) are typed and authenticated as enumerated in `technical_spec.md` §1.

---

End of `data_flow.md`.
