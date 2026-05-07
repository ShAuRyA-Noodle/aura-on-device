# Aura Pilot — Task Protocol

The 5 standardised tasks per `plan.md` §22.2. Each task is run **twice per participant**: once **baseline** (existing tools, no Aura) and once **prototype** (with Aura). The order baseline-vs-prototype is randomised per user. The order of the 5 tasks within each round is also randomised.

Reference: `plan.md` §22, §23.4.
Last updated: 2026-05-07
Owner: Shaurya Punj

---

## 0. Session structure (30 min per participant)

```
00:00 — Brief + consent re-confirm                  (3 min)
00:03 — Baseline round (5 tasks, randomised order) (10 min)
00:13 — 2-min break + water                         (2 min)
00:15 — Prototype round (5 tasks, randomised order) (12 min)
00:27 — Post-task questions on phone                (3 min)
00:30 — End
```

**Coin flip / random.org** decides whether the participant does baseline-first or prototype-first. Half the cohort starts with each — counterbalanced for order effects.

---

## 1. What gets logged

Every task in every round, on every participant, the following is captured to a per-participant CSV (`P001_tasks.csv`, etc., format in `raw_data_template.md`):

| Field | Type | How |
|---|---|---|
| `participant_id` | string | from consent form |
| `round` | enum {baseline, prototype} | session log |
| `task_id` | int 1–5 | session log |
| `task_order_in_round` | int 1–5 | session log |
| `started_at` | iso8601 | researcher stopwatch + auto when prototype |
| `ended_at` | iso8601 | same |
| `duration_sec` | float | derived |
| `tap_count` | int | screen recording (OBS Mac) → manual count, or auto via Aura instrumentation in prototype round |
| `completion_flag` | enum {success, partial, abandon} | researcher judges per success criteria below |
| `self_rating_1to5` | int | participant answers Q11–Q15 in survey |
| `notes` | string | researcher free-text |

Screen recording: **OBS Mac**, capturing the mirrored phone (QuickTime AirPlay receiver). Stored locally; transcribed to tap count by the researcher; deleted after coding.

Aura prototype round also auto-logs taps via in-app instrumentation; this provides cross-validation on tap counts.

---

## 2. The 5 tasks

### Task 1 — Triage 50 unread WhatsApp messages, reply to 3 actionable

**Setup**
- Researcher pre-seeds the participant's test WhatsApp account (or test sandbox group on the participant's own phone, with consent) with 50 unread messages across 3 chats: a study group, a project group, and a friends group. The 50 messages are scripted with **3 plant messages** that demand a real reply (e.g. "are you coming to the lab at 4?", "send me your share for the Zomato order", "did you submit the form?").
- Same 50 messages used for both rounds, but **chat names and sender names are anonymised differently** between baseline and prototype to prevent rote learning.

**Start cue**
- Researcher says: "You have 50 unread messages across 3 WhatsApp groups. Find the 3 that need a reply, and reply to each. Tell me when done."

**End criteria**
- All 3 plant messages have a real text reply (not just a tick or thumbs-up).
- **Success** = all 3 found and replied within 4 minutes.
- **Partial** = 1–2 found and replied within 4 minutes.
- **Abandon** = participant says "I give up" or 4 minutes elapse with 0 found.

**Why this task**
- Indian context: WhatsApp is the dominant comms channel. CommsAgent's batch-summarise + draft-reply tools are tested directly.

---

### Task 2 — See morning's calendar, check travel time, decide leave-time

**Setup**
- Test calendar pre-loaded with one event the next morning: "10:00 — DBMS group meet at LP4" (Thapar) or "10:00 — sprint review at WeWork Galaxy, Residency Road" (Bangalore).
- Researcher gives the participant a **simulated current location** verbally: "Pretend it is 8:45 AM, you are in your hostel room / your PG room. The meet is at 10:00."

**Start cue**
- "Tell me what your morning looks like, how long it takes to get to the meet, and what time you should leave."

**End criteria**
- Participant verbally states: (a) the event time, (b) an estimate of travel time (in minutes), (c) a leave-time.
- **Success** = all 3 stated within 90 seconds AND the leave-time is within ±5 minutes of researcher-computed correct value.
- **Partial** = 2 of 3 stated correctly.
- **Abandon** = participant cannot answer or stops trying.

**Why this task**
- CalendarAgent + travel-aware-alert tool. Tests the morning brief.

---

### Task 3 — Categorise yesterday's spend, identify if over budget

**Setup**
- Test spend data pre-seeded: 7 transactions across yesterday — 2 Zomato (₹420, ₹280), 1 Blinkit (₹650), 1 BMTC / Uber (₹180), 1 UPI peer (₹500), 1 Amazon (₹1,290), 1 Swiggy Instamart (₹220). Total = ₹3,540.
- Stated weekly budget: ₹15,000. Yesterday's expected average: ₹2,142. So yesterday is **over** average by ₹1,398.
- Baseline: participant uses their existing apps (HDFC SMS, GPay history, manual scroll). Prototype: FinanceAgent is loaded.

**Start cue**
- "Tell me what you spent yesterday by category, and whether you were over your usual daily average."

**End criteria**
- Participant verbally states: (a) total amount within ±₹100 of ₹3,540, (b) top category by rupees (Amazon at ₹1,290 or food cluster at ₹1,570 — both accepted), (c) over/under verdict against the daily average.
- **Success** = all 3 within 2 minutes.
- **Partial** = 2 of 3 within 2 minutes.
- **Abandon** = no answer, or only the total stated.

**Why this task**
- FinanceAgent + Indian app context (UPI, Zomato, Blinkit). Tests parse + categorise + anomaly-flag.

---

### Task 4 — Reach a calmer state after a stressful 30-minute period

**Setup**
- This task spans **30 minutes prior** to the measurement. The participant is asked to do something they find stressful for ~30 minutes:
  - **Default**: a timed mock DBMS quiz (10 questions, 25 min limit, hard difficulty) on the test laptop. Quiz adapted from Thapar past papers.
  - **Alternative for non-CS branches**: solve a JEE-level math timed quiz, same length.
- HRV, HR, and self-rated stress (1–5) are captured **before** and **after**, and **after-recovery**.
- Baseline: participant has 5 minutes after the quiz to calm down using whatever they normally do (music, breathing, scrolling). Prototype: WellnessAgent suggests an intervention, participant accepts or rejects.

**Start cue**
- "Take 5 minutes. Try to feel calmer than you do right now. Tell me when you are ready."

**End criteria**
- Participant rates self-stress 1–5 at three points: pre-quiz, post-quiz, post-recovery.
- **Success** = post-recovery rating ≥ 1 point lower than post-quiz, AND HRV trend recovers ≥ 5 ms RMSSD within 5 minutes.
- **Partial** = self-rating drops but HRV does not recover (or vice versa).
- **Abandon** = participant rates self-stress higher post-recovery, or refuses the recovery period.

**Why this task**
- WellnessAgent + closed-loop biometric. The signature wedge.

**Ethics note**: the stressful period is mild and time-bounded. Any participant who wants to skip Task 4 can — Task 4 is optional and noted in their CSV.

---

### Task 5 — Pick the right two of five received messages to reply to immediately

**Setup**
- Pre-seed 5 messages on the participant's notification panel — 1 from a parent ("call me when free"), 1 from a delivery person ("I am at gate, OTP?"), 1 from a project group ("anyone has the slides?"), 1 promotional ("Zomato 50% off!"), 1 friend ("free this weekend?").
- The "right" 2 are: delivery (urgency: time-sensitive) and parent (social weight). All others can wait or be ignored.
- Baseline: participant scrolls through the notification panel manually. Prototype: CommsAgent surfaces a triaged card.

**Start cue**
- "Look at your notifications. Pick the two you would reply to right now and tell me which."

**End criteria**
- Participant verbally names 2 messages.
- **Success** = both delivery and parent are named within 60 seconds.
- **Partial** = 1 of 2 correct within 60 seconds.
- **Abandon** = neither correct or no answer in 60 sec.

**Why this task**
- CommsAgent triage classifier. Tests the urgency-vs-social judgement explicitly.

---

## 3. Order randomisation procedure

Use Python `random.shuffle` with a per-participant seed = participant ID hash. Same seed used at session start so the order is reproducible from the CSV.

```python
import hashlib, random
def task_order(participant_id: str) -> list[int]:
    seed = int(hashlib.sha256(participant_id.encode()).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)
    order = [1, 2, 3, 4, 5]
    rng.shuffle(order)
    return order
```

Round order (baseline-first vs prototype-first) is decided by `seed % 2`.

---

## 4. Researcher conduct rules

- **Do not coach.** If participant asks "should I tap here?", answer "do whatever you would normally do".
- **Do not narrate.** Silent except for start cues and end confirmations.
- **Stopwatch starts on the last word of the start cue.** Stops on participant's spoken end answer or task completion.
- **Repeat the start cue verbatim** if asked. Do not paraphrase.
- **No retries within a round.** A failed task is logged as such. The participant gets one attempt per round per task.

---

## 5. After the session

- Participant fills the survey (`quant_survey.md`) on their phone, present in the room.
- Researcher exports the prototype round's auto-logged CSV from the Aura app via the in-app "Export pilot logs" button.
- Both files (researcher-stopwatch CSV + Aura CSV) saved to `pilot/raw/P0XX/` per `raw_data_template.md`.
- Researcher writes a 5-line "field notes" file describing anything unusual — phone died, participant cancelled mid-Task 4, etc.

---

## 6. Edge cases and recovery

| Situation | Response |
|---|---|
| Participant's phone is not iPhone | Use a researcher-provided iPhone with TestFlight build pre-installed; participant logs in with a test Apple ID. |
| Participant skips Task 4 (stress) | Log as `skipped` in CSV. Do not pressure. |
| Aura crashes mid-task | Log timestamp + crash. Restart app. Skip task. Do not retry in same session. |
| Network drops during Task 1 (WhatsApp test sandbox) | Pause stopwatch; resume when network back. Note in `notes`. |
| Participant clearly games the task | Log honestly in `notes`. Do not manipulate the data. |

---

End of task protocol.
