# Aura Pilot — Qualitative Protocol

8 participants. 60-minute semi-structured interview after 7 days of TestFlight use. Plus a 90-second daily diary across the 7 days. Two coders, thematic analysis with Cohen's κ ≥ 0.7 inter-rater target.

Reference: `plan.md` §23.3, §22.
Last updated: 2026-05-07
Owner: Shaurya Punj (interviewer 1) + Shorya Gupta (interviewer 2 / second coder)

---

## 1. Participant pool

- 8 from the n=30 quant pool, drawn after Day 7 task sessions.
- Mix target: 4 ECE / CompE / CSE, 2 other Thapar branches, 2 Bangalore-based.
- Gender: 4 / 4.
- Hostel / day scholar: 5 / 3.
- Recruit alternates in case of dropouts (2 standby).

## 2. Interview format — 60 minutes total

Semi-structured. Recorded on Voice Memos on a separate iPhone (not the participant's). Transcribed by us within 48 hours, then audio deleted.

### 2.1 Block 1 — Daily diary review (15 min)

Participant has filled the daily diary (see §5) for 7 days. Walk through it together.

**Interviewer prompts:**
- "Read me your Day 1 entry out loud."
- "What was happening that day?"
- "Day 3 you wrote [X]. Tell me about that moment."
- "Was there a day Aura got it right? A day it got it wrong?"
- "Did the diary itself bug you, or did it feel fine?"

**What we are listening for:** week-shape, pattern of trust/distrust, moments of surprise, friction points.

### 2.2 Block 2 — Walkthrough of three Aura moments (30 min)

Ask the participant to recall **three specific moments** from the week when Aura did something they remember — good or bad.

For each moment, work through:
1. **Reconstruct.** "Where were you? What were you doing? What did Aura do?"
2. **Reaction.** "What did you feel in the second after?"
3. **Action.** "What did you do? Did you tap, ignore, swipe away?"
4. **Verdict.** "Looking back, was that the right call by Aura?"
5. **Counterfactual.** "If Aura had not done that, what would you have done instead?"

Use the participant's own phone. Open the **Reasoning Trace** drawer for the moment if they remember when. Let them read the trace out loud. Listen for whether the trace feels like an explanation or a defence.

**What we are listening for:** trust, surprise, friction, silence, value (the 5 themes — see §3).

### 2.3 Block 3 — Think-aloud on one task (15 min)

Pick one of the 5 standardised tasks (see `task_protocol.md`). Ask the participant to perform it on their phone using Aura, narrating every thought aloud.

**Interviewer prompts (only when stuck):**
- "What did you expect just now?"
- "What does this card tell you?"
- "Where would you tap?"

Do not help. Do not prompt for satisfaction. Just listen.

**What we are listening for:** mental model mismatches, friction in the UI, moments where the user predicted Aura's behaviour vs. moments of confusion.

---

## 3. Coding scheme

Five themes locked. Two coders code independently. Disagreements resolved in a third pass.

| Theme | Definition | Example utterance |
|---|---|---|
| **Trust** | Statements about whether the participant believes Aura is correct, fair, or honest. Includes loss of trust. | "I clicked the trace because I didn't believe it knew that." |
| **Surprise** | Statements where the participant expected one thing and got another. Both pleasant and unpleasant. | "Wait — it actually muted the group? I thought it would just show me the messages." |
| **Friction** | Statements describing extra work, confusion, or annoyance caused by Aura. | "I had to tap three times to dismiss that card." |
| **Silence** | Statements about Aura not doing something — either appreciated quiet or perceived absence. | "I didn't even notice it was running on Wednesday. That was nice." |
| **Value** | Statements about whether Aura saved time, attention, money, or mood. | "It caught the IRCTC mail before I did." |

### 3.1 Coding procedure

1. Both coders independently code the full transcript at the **utterance** level (one speaker turn = one or more codes).
2. Coding software: **Taguette** (open source) or a shared Google Sheet with one row per utterance.
3. Cohen's κ computed on the full coded set.
4. **Target: κ ≥ 0.70.** Below 0.6, both coders re-watch a sample, refine theme definitions, recode.
5. Themes are **not exclusive** — one utterance can carry up to two codes.
6. Disagreements arbitrated by a third pass with both coders sitting together.

See `analysis/notebooks/04_autonomy_quality.ipynb` for the κ computation pattern (same statistic, different rater task).

### 3.2 Output

- Per-theme frequency table.
- Top 3 quotes per theme (with participant ID, never name).
- Cross-tab: theme × participant — who experienced which theme.
- Three named "moments" per participant carried forward into Phase 2 report (`reporting/phase2_report_outline.md` §5).

---

## 4. Inter-rater reliability — Cohen's κ target

- **Target**: κ ≥ 0.70 across all five themes.
- **Acceptable floor**: κ ≥ 0.60 with documented disagreement notes.
- **Below 0.60**: theme definitions are not crisp. Refine and recode.
- Reported in Phase 2 deliverable as: "Two independent coders coded N utterances across 8 transcripts. Cohen's κ = X.XX [Y.YY, Z.ZZ] across 5 themes."

---

## 5. Daily diary template

Sent at 21:30 IST every day for 7 days via WhatsApp (link to a 3-question Google Form). Target completion: 90 seconds. Optional skip for any day.

### Question 1 — open
> In one sentence, what did Aura do today that mattered, or fail to do that mattered?

### Question 2 — Likert 1–5
> How stressful was today, on a scale where 1 = a calm day and 5 = a hard day?

> 1. Calm — nothing pressed on me
> 2. Mostly calm
> 3. Average
> 4. Mostly stressful
> 5. Hard — I was overloaded

### Question 3 — open (skippable)
> Anything you would change about Aura today? One sentence is fine. Skip if nothing.

---

### Diary delivery

- Sent 21:30 IST. Reminder at 22:30 if not filled.
- No reminders after 22:30. We are not nagging.
- Stored anonymised under participant ID `P001`–`P030` (qual subset uses same IDs).

### Diary use in Block 1

The 7 diary entries become the timeline the interviewer walks through in Block 1. They are the participant's own words about their week.

---

## 6. Logistics

- Interviews held in the Thapar Library group-study room (booked) or over Google Meet for Bangalore participants.
- Recording on Voice Memos on a researcher iPhone, not the participant's.
- Researcher dress: normal. No "professional".
- Snacks provided (chai + biscuits) — this is hospitality, not incentive.
- Each interview ends with: "Want me to delete the recording right now?" — and we do, if asked.

---

## 7. Ethical guardrails

- Pause and re-confirm consent at the start of every interview. The consent form (`pilot/consent_form.md`) is on the table.
- Skip any question the participant prefers not to answer.
- Stop the recording any time the participant asks. Resume only with verbal yes.
- Quotes used in the Phase 2 report are sent to the participant for approval before submission.
- Audio deleted within 7 days of transcript completion.

---

End of qualitative protocol.
