# Aura Pilot — Quantitative Survey

Google Form copy-paste-ready. Target n=30. Target completion: ~12 minutes. ~30 questions across 7 sections.

All Likert items use a **5-point scale with both endpoints labelled in plain language.** No leading wording. The brand name "Aura" appears only where the user must distinguish baseline vs prototype.

Reference: `plan.md` §22, §23.4.
Last updated: 2026-05-07

---

## Pre-amble (top of the form)

> Hi. This is the post-trial survey for the Aura pilot. It should take about 12 minutes. There are no right answers. If a question feels off, skip it.
>
> Your answers are anonymised. Your participant ID is on the consent form — please paste it below.
>
> Thanks for the seven days. — Shaurya & Shorya

**Q0. Participant ID** *(short text, required)*
*format: P001–P030*

---

## Section 1 — Demographics (5 Q)

### Q1. Age
*short text, numeric, required*
*range expected: 17–25*

### Q2. Branch / programme
*single-select, required*
- ECE
- CompE
- CSE
- IT
- Mechanical
- Civil
- Biotech
- Other (please specify)

### Q3. Year of study
*single-select, required*
- 1st year
- 2nd year
- 3rd year
- 4th year
- Postgrad
- Working / not a current student

### Q4. Living situation during the pilot
*single-select, required*
- Hostel at Thapar
- Day scholar / off-campus in Patiala
- Bangalore — own home
- Bangalore — PG / shared
- Other

### Q5. Primary phone you used during the pilot
*single-select, required*
- iPhone (the only supported pilot device)
- Other (please describe; note: only iPhone data was logged)

---

## Section 2 — Status quo (5 Q)

Establishes baseline: what the participant used **before** Aura, and what hurt.

### Q6. Before this pilot, which assistant or AI tool did you use most often on your phone?
*single-select, required*
- Apple Siri
- Google Assistant on a different device
- ChatGPT app
- Gemini app
- I did not use any
- Other (please specify)

### Q7. On a normal day before the pilot, roughly how many notifications did your phone show you?
*single-select, required*
- Fewer than 50
- 50–100
- 100–200
- 200–400
- More than 400
- I do not know

### Q8. How often did notifications interrupt something you were trying to focus on, in the week **before** the pilot?
*5-point Likert, required*
- 1 — Almost never
- 2 — Once or twice
- 3 — A few times
- 4 — Many times
- 5 — Almost constantly

### Q9. Pick your top pain point in your phone life over the last month.
*single-select, required*
- Notification overload
- Hard to find the right message in a busy chat
- Spending more than I planned without realising
- Forgetting calendar events or running late
- Stress / sleep / wellbeing
- I am mostly fine
- Other (please specify)

### Q10. Before this pilot, did you trust your phone's existing AI assistant to do useful things on its own?
*5-point Likert, required*
- 1 — Did not trust at all
- 2
- 3 — Neutral
- 4
- 5 — Trusted completely

---

## Section 3 — Task results (5 Q, plus auto-logged metrics)

Auto-logged from the task session app (CSV per participant): time taken (sec), tap count, completion flag (success / partial / abandon). The 5 Q below capture the participant's subjective view per task.

For each task, ask one question. Tasks are defined in `task_protocol.md`.

### Q11. Task 1 (WhatsApp triage) — How easy was this to complete with Aura compared to without?
*5-point Likert, required*
- 1 — Much harder with Aura
- 2 — Slightly harder with Aura
- 3 — About the same
- 4 — Slightly easier with Aura
- 5 — Much easier with Aura

### Q12. Task 2 (morning calendar + travel + leave-time) — same scale as above.
*same 5-point Likert, required*

### Q13. Task 3 (categorise yesterday's spend, identify if over budget) — same scale.
*same 5-point Likert, required*

### Q14. Task 4 (reach a calmer state after a 30-minute stressful period) — same scale.
*same 5-point Likert, required*

### Q15. Task 5 (pick the right two of five received messages to reply to) — same scale.
*same 5-point Likert, required*

---

## Section 4 — Satisfaction across 7 dimensions (7 Q)

All 5-point Likert. Each item names both endpoints. Order is randomised in the live form.

### Q16. **Trust** — When Aura took an action on its own, how often did it match what you would have done?
- 1 — Almost never matched
- 2
- 3 — Matched about half the time
- 4
- 5 — Almost always matched

### Q17. **Speed** — How fast did Aura respond when you tapped a card or opened the app?
- 1 — Slow enough to bother me
- 2
- 3 — Fine
- 4
- 5 — Faster than I expected

### Q18. **Privacy** — How comfortable did you feel with what Aura was reading from your phone during the pilot?
- 1 — Not at all comfortable
- 2
- 3 — Neutral
- 4
- 5 — Completely comfortable

### Q19. **Autonomy** — When Aura made a suggestion or took an action, how often was it the right thing to do at that moment?
- 1 — Rarely the right thing
- 2
- 3 — Right about half the time
- 4
- 5 — Almost always the right thing

### Q20. **Silence** — How often did Aura stay quiet when you wanted it to stay quiet?
- 1 — It interrupted me too much
- 2
- 3 — About what I expected
- 4
- 5 — It was quieter than I expected

### Q21. **Recovery** — When you were stressed and Aura suggested something (a breath, a mute, a nap), did the suggestion help?
- 1 — Did not help
- 2
- 3 — Neutral
- 4
- 5 — Helped clearly
- N/A — Aura never suggested this during my pilot

### Q22. **Indian context** — How well did Aura handle Indian apps and services (UPI, Zomato, Swiggy, Blinkit, IRCTC, BMTC)?
- 1 — Got it wrong / could not handle
- 2
- 3 — Mixed
- 4
- 5 — Handled well
- N/A — I did not use any of these during the pilot

---

## Section 5 — Willingness to pay (5 Q)

Van Westendorp Price Sensitivity Meter (4 Q) plus 1 binary anchor at ₹199/mo.

### Q23. At what monthly price would you consider Aura **so cheap** that you would doubt its quality?
*short text, numeric, required*
*expected unit: rupees per month*

### Q24. At what monthly price would you consider Aura **a bargain — a great buy for the money**?
*short text, numeric, required*

### Q25. At what monthly price would you consider Aura **starting to get expensive** — you would still consider it but you would think twice?
*short text, numeric, required*

### Q26. At what monthly price would Aura be **too expensive — you would not consider buying it**?
*short text, numeric, required*

### Q27. Would you pay **₹199 per month** for Aura, knowing what you know now?
*single-select, required*
- Yes
- No
- Not sure

---

## Section 6 — NPS (1 Q)

### Q28. On a scale of 0 to 10, how likely are you to recommend Aura to a friend?
*single-select 0–11 buttons, required*
*0 = Not at all likely, 10 = Extremely likely*

(Standard NPS scoring: promoters 9–10, passives 7–8, detractors 0–6.)

---

## Section 7 — Open feedback (1 Q)

### Q29. Anything else you want to tell us about Aura — good, bad, or weird?
*long text, optional*

---

## Closing

> That is everything. Thank you. The survey closes here.
>
> If you would like to see your task CSV before we anonymise and publish it, reply yes on WhatsApp and we will send it.

---

## Question-design notes (for the team, not the participant)

- **No leading wording.** "How great was Aura?" is banned. We use neutral verbs (matched, helped, handled).
- **Both Likert endpoints labelled.** Per project lock.
- **N/A allowed where context-dependent.** Q21 (recovery) and Q22 (Indian context) — some users will not encounter these.
- **WTP** uses Van Westendorp because it is the gold standard for unmoored price discovery, plus a binary anchor at the brief's ₹199 target for direct WTP rate reporting.
- **NPS** included because the brief implies satisfaction-style measurement; NPS is the cleanest single-number proxy and easy to compare.
- **No mood-dependent ordering.** Section order is fixed; the only randomisation is within Section 4 (satisfaction items), to break order bias.
- **Question count audit:** Q0 + 5 + 5 + 5 + 7 + 5 + 1 + 1 = **29 questions visible to the participant**. Within the ~30 target.

---

End of survey.
