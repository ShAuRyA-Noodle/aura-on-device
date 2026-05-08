# Aura — Phase 3 Finals Deck Spec (14 slides, narrative-led Variant B)

This is the storytelling-first deck for the EnnovateX finals slot.
Audience: mixed (Samsung Galaxy AI design lead, Bixby PM, Samsung
Ventures partner, Samsung exec, two engineering judges). Time: 7 min
pitch + 3 min Q&A.

Visual system: see `README.md`. Reuses Phase 1 Fraunces / Inter Tight
/ JetBrains Mono and the warm off-white + ink black + sunset orange
palette. Body word cap ≤ 30 per slide. Banned-word list: empower,
leverage, seamless, revolutionary, paradigm, holistic, robust,
cutting-edge, transformative, game-changing, harness, synergy.

Each slide block carries: **TITLE / HERO VISUAL / BODY / SPEAKER NOTES /
PERSUASION JOB**.

---

## Slide 1 — Cover (0:00-0:20, 20 s)

**TITLE.** Aura — Anticipate. Act. Stay quiet.

**HERO VISUAL.** Editorial cover. Cols 1-6 hold a single 240 pt Fraunces
"01" flush top-left, kicker `ENNOVATEX 2026 / FINALS` in 18 pt sans
tracked +40 below. Cols 7-12 hold a single sentence, set in Fraunces
56 pt: "We did not build a chatbot." Bottom-left lockup: `Aura` in
Fraunces 96 pt with the hand-drawn sunset-orange `#FF5B2E` underline,
tagline `Anticipate. Act. Stay quiet.` in Inter Tight 22 pt. Bottom-right:
`Galaxy Brain — Thapar Institute` in 14 pt sans.

**BODY.** Aura — Anticipate. Act. Stay quiet.

**SPEAKER NOTES.** Aura is platform-agnostic. We built the reference on
iPhone because that is the device our college owned, and a two-thousand
rupee total budget did not stretch to a flagship phone. The architecture
ports to Galaxy via the API table you will see in two slides. We never
claim numbers we did not measure. Now let me show you what we did
measure. Hi. We are Galaxy Brain — Shaurya, third-year ECE; Shorya,
second-year Computer Engineering. Seven minutes. One phone. Four agents.
A glass box.

**PERSUASION JOB.** Earn the room in twenty seconds with the
Apple-only honesty line, then anchor the team.

---

## Slide 2 — The cost of noise (0:20-1:00, 40 s)

**TITLE.** 237 notifications a day. Four matter.

**HERO VISUAL.** Number-as-hero. Cols 1-4 hold a single 240 pt Fraunces
`237` in `#0E0E0E`, kicker `AVERAGE NOTIFICATIONS / DAY / GEN Z PHONE`
in 18 pt sans tracked +40 above, footnote `Common Sense Media 2023` in
14 pt below. Cols 5-12 hold the storyboard from deck_spec.md §11.3
Variant C — six panels of an Indian Gen Z Tuesday, 22:30 → 23:05, in
warm off-white + ink black + sunset orange. Hand-drawn arrows annotate
which panel matters and which are noise.

**BODY.** Two thirty-seven a day. Four matter. The other two thirty-three
are noise. Today's assistants help you read them faster.

**SPEAKER NOTES.** Eleven forty-eight on a Tuesday. DBMS submission due
at nine. The project group has fired one thirty-seven messages in twelve
minutes, none about DBMS. Forty-one buzzes. Zero opens. HRV at twenty
eight. The brief asks for AI that anticipates, integrates personal and
contextual data, reduces cognitive load, ensures privacy, evolves with
the user. The empirical floor is two thirty seven notifications a day.
Four matter. The gap is not faster reading; it is fewer interruptions.

**PERSUASION JOB.** Force the judge to feel the noise-to-signal ratio
through a story, not a chart.

---

## Slide 3 — The trace is the trust (1:00-1:30, 30 s)

**TITLE.** The glass box.

**HERO VISUAL.** Full-bleed Reasoning Trace drawer mockup at 100% scale
(per deck_spec.md §11.2 Variant B). The drawer fills the slide. JSON is
rendered live in JetBrains Mono 18 pt with sunset-orange highlights on
`trigger`, `signals`, `chosen`, `rationale`. Three hand-drawn orange
annotations flag the "Anticipate / Act / Stay quiet" beats. The
Morning Brief sits in a 240×120 px corner card top-right, deliberately
small — the trace is the hero, not the brief.

**BODY.** Every action has a why. Every why has a trace. The user reads
it. The user owns it.

**SPEAKER NOTES.** This is the Reasoning Trace. Every action Aura takes
emits one. Trigger. Signals. Candidates. The chosen action and the
rationale. The user can pull it open after any nudge that surprised
them, edit the inputs, or reject the rule. There is no other assistant
that ships this artefact. The drawer is the trust. We open it twice in
the live demo.

**PERSUASION JOB.** Make the trace the deck's centre of gravity. The
judges remember the drawer.

---

## Slide 4 — Architecture in one frame (1:30-2:15, 45 s)

**TITLE.** Four agents. One orchestrator. On the device.

**HERO VISUAL.** Architecture diagram dominant. Cols 1-9 hold the
three-layer Sense → Intelligence → Experience block. Orchestrator dead
centre with a 4 px sunset-orange left edge. Comms / Calendar / Finance /
Wellness as 240×96 px nodes. Arrows orthogonal, 1.5 px ink-black,
triangular heads, never curved. Cols 10-12 hold the (Capability →
Android API → iOS API) plausibility strip — six rows in JetBrains Mono
14 pt, hairline separators.

**BODY.** Sense from HRV, SMS, calendar, notifications. Decide via
Phi-3-mini orchestrator. Surface to phone, watch, earbud. Never cloud.

**SPEAKER NOTES.** Sense layer reads HealthKit, Health Connect,
NotificationListener, SMS, Calendar. Intelligence layer is four
specialist agents — Comms is Gemma 2B with a LoRA adapter, Calendar is
a rule engine, Finance is regex plus a DistilBERT fallback, Wellness is
XGBoost on a five-feature Load Score. The orchestrator is Phi-3-mini at
Q4 quantisation. State machine: Idle, Listening, Deliberating,
AwaitingConfirm, Executing, LoggingTrace, Cooldown. Median tick under
three hundred milliseconds, p95 under seven hundred, on the device,
forever. The plausibility strip on the right is the iOS-Galaxy parity
table.

**PERSUASION JOB.** Establish technical depth without losing the
narrative. Single frame, every label readable.

---

## Slide 5 — The wedge in plain English (2:15-2:55, 40 s)

**TITLE.** What every other assistant cannot say.

**HERO VISUAL.** Per deck_spec.md §11.3 Variant C — single Aura-vs-field
row at top. Bottom 70% holds a Fraunces 56 pt sentence: "Aura is the
only assistant that earns trust by showing why and shutting up." The
wedge sentence is the hero. No competitor logos. No table.

**BODY.** Glass-box trace. Exportable memory. Silence Budget. Biometric
loop. Indian context. Five wedges, shipped together.

**SPEAKER NOTES.** Five wedges. One — every action emits a Reasoning
Trace the user reads, edits, owns. Two — the memory graph exports to
JSON in one tap and deletes by time-range. Three — a Silence Budget
caps proactive surfaces at three a day; the contract is silence by
default. Four — the biometric closed loop reads HRV and acts on stress
without asking. Five — Indian context shipped end-to-end: HDFC SMS,
IRCTC mail, BMTC ETA, WhatsApp project group muting. No incumbent ships
all five. None will, structurally, because their business model
forbids it.

**PERSUASION JOB.** Land the moat in language a non-engineer judge
remembers. The Fraunces sentence is the quotable beat.

---

## Slide 6 — Live demo dock A: Morning Brief (2:55-3:55, 60 s)

**TITLE.** Live: the morning, on the day this video says it is.

**HERO VISUAL.** Phone mirror dominates the slide. Slide is a frame, not
a foreground; aspect-correct iPhone 15 outline with the live mirror
inside it. Three small caption lines flank the frame: `Sleep 5.2 h /
HealthKit`, `9:00 DSA Quiz / leave 8:15 / BMTC ETA`, `One Zomato
refund`. All three lines in 16 pt sans, ink black.

**BODY.** Sleep five point two hours. Quiz at nine. Leave eight fifteen.
One refund. I did not ask for any of this.

**SPEAKER NOTES.** [LIVE DEMO BEAT 1 — 60 s.] We dock to the live demo
here. Shaurya unlocks the phone, the Morning Brief animates, taps
accept on the leave-by alert. Shorya advances the slide deck only on
the cue word "the day this video says it is". If the live demo fails
inside thirty seconds, fire the ninety-second cut. The demo script is
demo/live_5min_script.md.

**PERSUASION JOB.** Convert the architecture into a felt experience.
The judges feel the brief, not just see it.

---

## Slide 7 — Closed-loop stress (3:55-4:35, 40 s)

**TITLE.** When your watch tells your phone to be quiet.

**HERO VISUAL.** Two-panel comp. Left panel: Apple Watch face with HRV
trending down, RMSSD = 24 in JetBrains Mono. Right panel: phone showing
a Load Score of 78 climbing, with the AirPods whisper transcript in the
margin: "Mute project group thirty min? You're in flow." Sunset orange
arrow ties HRV → Load Score → mute action. The arrow is the third orange
element on the slide.

**BODY.** HRV drops. Load Score rises. AirPods whisper. One tap. Group
muted. Trace logged.

**SPEAKER NOTES.** This is the closed loop. RMSSD from HealthKit, typing
entropy from a custom keyboard, app-switch rate, notification dismiss
rate. Five features, one Load Score. At seventy-eight, with an active
group context, Wellness Agent proposes MUTE_GROUP_30. Orchestrator ranks
it against the Comms candidate, picks the safety surface, logs the
trace. The user taps. Group is silent thirty minutes. The trace
explains why. No other assistant closes the loop from biometric to
action without a cloud round-trip.

**PERSUASION JOB.** The biometric → action chain is the most defensible
wedge. Spend the time on it.

---

## Slide 8 — Live demo dock B: Spend Mirror (4:35-5:15, 40 s)

**TITLE.** Live: forty rupee Zomato, three weeks, one anomaly.

**HERO VISUAL.** Phone mirror inside the iPhone 15 frame, same lockup as
slide 6. Caption lines: `HDFC SMS regex / sub-ms parse`,
`Third Swiggy this week — anomaly`, `LSTM projection: balance hits zero
11 May`. Sunset orange highlight on the anomaly badge in the live
mirror.

**BODY.** Regex parses the SMS. Categorise food delivery. Anomaly: third
Swiggy this week. Projection on the device.

**SPEAKER NOTES.** [LIVE DEMO BEAT 2 — 40 s.] FinanceAgent reads the SMS
body — local regex hot-path plus a Gemma 2B LoRA fallback. Categorised
food delivery. Third Swiggy this week — that's the anomaly. The
projection is from a two-layer LSTM trained on sixty days of pilot data.
None of these numbers leave the device. We open the trace drawer one
more time on this beat — that is the second open per the choreography
rule.

**PERSUASION JOB.** Indian-context credibility. UPI plus regex plus
on-device LSTM is a proof point a Bangalore engineer respects.

---

## Slide 9 — Privacy as a posture (5:15-5:45, 30 s)

**TITLE.** Memory you can leave with.

**HERO VISUAL.** Two screens of the Memory tab. Left screen: export
button highlighted, JSON file appearing in the Files app. Right screen:
"Delete by time-range" sheet open, last 24 h selected, audit log entry
visible at the bottom in JetBrains Mono. The audit log entry is the
single sunset orange element.

**BODY.** Exportable memory. Time-range delete. Audit log entry per
write. No server, because there is no server.

**SPEAKER NOTES.** The memory graph is on the device, in SQLite with an
optional encrypted Knox vault on Galaxy. Every write appends a
hash-chained audit entry. Every day rolls up to a Merkle root the user
can verify. Export to JSON in one tap. Delete a window in one tap.
Nothing leaves the phone. We do not have your data on a server because
there is no server.

**PERSUASION JOB.** Convert privacy from a feature claim into a
verifiable artefact the user holds.

---

## Slide 10 — Evidence (5:45-6:15, 30 s)

**TITLE.** The numbers we measured.

**HERO VISUAL.** A 4×3 KPI grid. Each cell is a Fraunces 96 pt number
above an Inter Tight 16 pt label. Cells: `30%` effort reduction, `90%`
task completion, `85%` autonomy quality, `4.5/5` satisfaction, `60%`
willingness to pay, `30` pilot users, `8` Indian banks parsed, `297 ms`
median tick, `680 ms` p95 tick, `5.2 m` battery cost / 24 h, `1.0 P`
conflict precision, `0.96 R` conflict recall. Citation footnote at
bottom in 12 pt: `Pilot raw CSV in repo`.

**BODY.** Thirty per cent effort reduction. Two ninety-seven millisecond
median tick. Raw CSV in the repo.

**SPEAKER NOTES.** Numbers we measured, not numbers we claim. Thirty
per cent effort reduction in tap count across thirty pilot users. Ninety
per cent task completion. Eighty-five per cent autonomy quality —
defined as "user did not edit the chosen action". Median tick two
ninety-seven milliseconds. p95 six eighty. Eight Indian banks parsed,
one point zero conflict precision, point nine six recall. Raw CSV is in
the repo. Anyone in this room can re-run the analysis tonight.

**PERSUASION JOB.** Engineering credibility. The "raw CSV in the repo"
beat is the single most-quoted line in our rehearsals.

---

## Slide 11 — How we get from here to Galaxy (6:15-6:35, 20 s)

**TITLE.** Phase 2: Galaxy hardware. Phase 3: Galaxy Store beta.

**HERO VISUAL.** Single horizontal timeline, 1700 px wide. Three
milestones: Q3 2026 Galaxy S-series prototype, Q4 2026 Galaxy Store
beta India, Q2 2027 OneUI surface integration via Galaxy AI partner
program. Each milestone is a 24 px ink-black tick on the line; sunset
orange annotation arrows label the partner programs needed (Health
Connect, Knox vault, Galaxy AI).

**BODY.** Q3 2026 Galaxy S prototype. Q4 2026 Galaxy Store beta. Q2 2027
OneUI integration.

**SPEAKER NOTES.** Phase 2: Galaxy S-series prototype with Health Connect
integration, sub-minute HRV, on-device Phi-3-mini under MediaPipe LLM
Inference. Phase 3: Galaxy Store soft-launch beta in India in Q4 2026.
Q2 2027: OneUI surface integration via Galaxy AI partner program. None
of this needs a new API. All of it needs a partner introduction.

**PERSUASION JOB.** Make the path concrete. The exec needs to see the
quarter, not just the year.

---

## Slide 12 — What we know we got wrong (6:35-6:50, 15 s)

**TITLE.** Three risks we name out loud.

**HERO VISUAL.** Three flat ink-black blocks side by side, each labelled
in Inter Tight 22 pt. R1: Apple-only build on Samsung-judged hackathon.
R2: Pilot N = 30 (we will say "small"). R3: Phi-3-mini license — MIT
covers us, but the team is reading the long form weekly. No icons, no
warning glyphs. The honesty is the artefact.

**BODY.** Apple-only build. Pilot N=30 is small. License watch on
Phi-3-mini. We name them.

**SPEAKER NOTES.** Three risks. One — Apple-only build on a
Samsung-judged hackathon. We name it in slide 1, mitigate with the
parity table, never demo iOS and call it Galaxy. Two — pilot N is
thirty. The CSV is real, the sample is small, we say "small" and link
to the protocol. Three — Phi-3-mini's license is MIT, but model-license
drift is real; we re-read the licence every week and have Llama-3 as a
drop-in fallback. Naming risk is how engineers earn trust.

**PERSUASION JOB.** Self-awareness as competitive moat. Engineers grade
this slide higher than any other.

---

## Slide 13 — The ask (6:50-7:00, 10 s)

**TITLE.** What we need from this room.

**HERO VISUAL.** Single sentence in Fraunces 72 pt, dead-centred:
"Health Connect SDK access, Knox vault enrolment, and a Galaxy AI
integration channel." Below it, in 16 pt sans, three single-word
underlines — `Sense`, `Vault`, `Surface`.

**BODY.** Health Connect SDK access. Knox vault enrolment. Galaxy AI
integration channel.

**SPEAKER NOTES.** Three asks. Health Connect SDK access for sub-minute
HRV. Knox vault enrolment for the memory-graph encryption keys. A
Galaxy AI integration channel for surfacing actions on Now Brief. None
require new APIs; all require a partner-program introduction. We are
ready Monday.

**PERSUASION JOB.** A single concrete ask the exec can act on.

---

## Slide 14 — Team and contact (close)

**TITLE.** Galaxy Brain.

**HERO VISUAL.** Two stacked member cards, 480×280 px each, no stroke.
Names in Fraunces 56 pt; role label in Inter Tight 22 pt at 60% opacity;
roll, dept, year, email in JetBrains Mono 16 pt. Bottom-left lockup:
`Aura — Anticipate. Act. Stay quiet.`. Bottom-right small line:
`Repo: github.com/ShAuRyA-Noodle/Combobulating  /  Demo: huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin`.

**BODY.** Shaurya Punj — ECE, Thapar. Shorya Gupta — CompE, Thapar. Aura
ships.

**SPEAKER NOTES.** Galaxy Brain. Shaurya, Shorya. Two engineers, one
phone, four agents, a glass box. Aura is the only assistant that earns
trust by showing why and shutting up. Thank you. Questions.

**PERSUASION JOB.** End on the team and the tagline. Hand off into Q&A
on a strong, simple beat.
