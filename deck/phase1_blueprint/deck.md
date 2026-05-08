---
slide: 1
title: Team Details
---
## BODY
Galaxy Brain.
Aura — Anticipate. Act. Stay quiet.
Shaurya Punj — 102486013, ECE 3rd, spunj_be23@thapar.edu.
Shorya Gupta — 1024037521, CompE 2nd, sgupta9_be24@thapar.edu.

## SPEAKER NOTES
Hi. We are Galaxy Brain. I am Shaurya, third-year ECE at Thapar. This is Shorya, second-year Computer Engineering at Thapar. We are building Aura, an on-device empathetic intelligence layer for Indian Gen Z and Gen Alpha. The locked tagline is anticipate, act, stay quiet, and the third beat is the one nobody else commits to. This deck is our Phase 1 blueprint for the EnnovateX problem statement on Empathetic Intelligence User Experience for Everyday Life. Two people, no faculty mentor, two-thousand-rupee total budget, twelve-week runway. We have mapped the Samsung roadmap from Galaxy AI to Knox to Health Connect, and we will show you in nine slides why a four-agent on-device system with a glass-box reasoning trace is the way to do this, not another chatbot. Eighty seconds, let us go.

## CITATIONS
None on slide. Roll numbers, emails, and team name verified by team and locked.

## VISUAL BRIEF
Editorial cover. Cols 1-6 hold a single 240 pt Fraunces numeral 01 flush top-left, with kicker ENNOVATEX 2026 / PHASE 1 BLUEPRINT in 18 pt sans tracked +40 below. Cols 7-12 hold two stacked member cards, each 480x280 px, no stroke, separated by a 1 px hairline. Member names in Fraunces 56 pt; role label in Inter Tight 22 pt at 60% opacity; roll, dept, year, email in JetBrains Mono 16 pt with labels at 50% opacity. Bottom-left lockup: Aura in Fraunces 96 pt with hand-drawn-feel sunset-orange #FF5B2E underline 4 px under the word, then tagline Anticipate. Act. Stay quiet. in Inter Tight 22 pt. Bottom-right small line: Thapar Institute of Engineering and Technology, Patiala in 14 pt sans. No photos, no logos, no university crest, no flag. Reference: Linear About page header, Apple HIG opener.

## PERSUASION JOB
Establish the team as serious operators with editorial taste in the first three seconds.

---

---
slide: 2
title: Problem Statement
---
## BODY
237 notifications a day. Four matter.
The brief asks for AI that anticipates, respects privacy, evolves with the user.
Today's assistants react. Aura closes the gap.

## SPEAKER NOTES
Eleven-forty-eight on a Tuesday. DBMS submission due at nine. My project WhatsApp group has fired one-thirty-seven messages in twelve minutes, none of them about DBMS. My phone has buzzed forty-one times. I have read zero. My watch says HRV is twenty-eight. I have not started the assignment. Aura would have read all one-thirty-seven, surfaced the one from Anu about the schema diagram, muted the rest until 1am, and told me to breathe before opening the laptop. Instead I am here, pitching this. The brief asks for AI that anticipates, integrates personal and contextual data, reduces cognitive load, ensures privacy, evolves with the user. KPIs are explicit: thirty percent effort reduction, ninety task completion, eighty-five autonomy quality, four-point-five satisfaction, sixty willingness to pay. The friction in one number: Common Sense Media measures 237 notifications a day for an Indian Gen Z phone. Four matter. The other 233 are noise nobody triages. Gemini, Siri, Bixby, Pixel, all reactive. None close the loop from biometric to action. None show their work. That is the gap.

## CITATIONS
[1] Common Sense Media 2023, Constant Companion: A Week in the Life of a Young Person's Smartphone Use. Median 237 notifications/day for tweens and teens.
[2] Pew Research, teens and technology, https://www.pewresearch.org/topic/internet-technology/teens-internet-technology/.
[3] WHO adolescent mental health, https://www.who.int/news-room/fact-sheets/detail/adolescent-mental-health.

## VISUAL BRIEF
Number-as-hero. Cols 1-4 hold a single 240 pt Fraunces 237 in #0E0E0E, kicker AVERAGE NOTIFICATIONS / DAY / GEN Z PHONE in 18 pt sans tracked +40 above, citation footnote Common Sense Media 2023 in 14 pt below. Cols 5-8 hold a 5x7 dot grid, each dot representing seven notifications. Four dots are sunset-orange #FF5B2E, the remaining 31 are #0E0E0E at 25% opacity. A hand-drawn #FF5B2E arrow points from the four orange dots to a 14 pt italic Inter Tight annotation: the four that mattered. Cols 9-12 stack three short paragraphs prefaced by 8x8 px #FF5B2E square bullets: What the brief asks for / What current AI does instead / The gap we close. Each paragraph max 18 words in Inter Tight 22 pt. No icons, no chat-bubble illustrations, no phone mockup. Reference: Nothing spec pages, Linear changelog by-the-numbers sections.

## PERSUASION JOB
Anchor the problem in a concrete citable number and force the judge to feel the noise-to-signal ratio.

---

---
slide: 3
title: Proposed Solution
---
## BODY
Aura is an on-device, multi-agent empathetic intelligence layer.
Four agents: Comms, Calendar, Finance, Wellness.
One orchestrator. One Reasoning Trace.
Anticipate. Act. Stay quiet.

## SPEAKER NOTES
Aura is on-device, multi-agent, and silent by design. Four specialist agents — Communications, Calendar, Finance, Wellness — coordinated by a Phi-3-mini orchestrator on top of an encrypted local memory graph. The screen on the left is the Morning Brief, the first thing our pilot user sees at 7:45 AM. It already knows she slept 5.2 hours from Health Connect, that her DSA quiz is at 9, that she should leave at 8:15 because the BMTC bus on her route is running late from a Google Maps live feed. She did not ask for any of this. She taps once to accept the leave-time alert. If she ignores it, Aura logs the dismissal and learns. The three beats are the locked tagline. Anticipate, surface before the user reaches for the phone. Act, one tap, never a chat thread. Stay quiet, capped at three proactive surfaces a day, learnable down to zero. The Silence Budget is a first-class state variable in the orchestrator, visible to the user. That third beat is the one nobody else commits to.

## CITATIONS
[3] Health Connect API, https://developer.android.com/health-and-fitness/guides/health-connect.
[4] Phi-3-mini, https://arxiv.org/abs/2404.14219.
UPI, IRCTC, Zomato, BMTC referenced as named real artefacts.

## VISUAL BRIEF
Bento grid, six tiles, asymmetric. Top row spans cols 1-12, height 320 px, single tile: a Figma mockup of the Aura Morning Brief card on a neutral phone frame in #0E0E0E 1.5 px stroke, no glow, no shadow, no isometric. Three hand-drawn #FF5B2E annotations point to: anticipated, not asked / one tap to confirm / Reasoning Trace. Annotation text in Inter Tight italic 14 pt. Second row is three tiles cols 1-4, 5-8, 9-12, each 380 px tall: tile 1 ANTICIPATE with sample agent output in JetBrains Mono 16 pt; tile 2 ACT with a one-tap UI fragment; tile 3 STAY QUIET with a Today: 0 notifications counter in 96 pt Fraunces. Bottom strip cols 1-12 height 80 px holds the locked one-liner centred in Inter Tight 22 pt. Reference: Linear changelog hero, Things 3 marketing.

## PERSUASION JOB
Force the judge to see a real product with one screen they recognise, not a concept slide.

---

---
slide: 4
title: Proposed Solution – Technical Details
---
## BODY
Three layers. Four agents. One orchestrator.
Sense reads on-device signals. Intelligence ranks candidate actions.
Experience surfaces one tap, with a Reasoning Trace.

## SPEAKER NOTES
Three layers: Sense, Intelligence, Experience. Sense reads on-device signals only. On Android: UsageStatsManager for app-launch sequences, NotificationListenerService for cross-app notifications, the SMS read permission for UPI and bank texts, Health Connect for HRV, sleep, and heart rate, Calendar Provider for events, and a custom IME for typing-entropy buckets, entropy only, never characters. iOS gives us HealthKit and EventKit but takes SMS and most cross-app notifications away. We name that limit on slide 4a. Intelligence is four agents: Comms on Gemma 2B with a LoRA, Calendar as a rule engine plus Phi-3, Finance on a distilled SMS classifier, Wellness on XGBoost feeding a Phi-3 prompt. They never chat in free-form. Every inter-agent call is a typed JSON tool invocation through the orchestrator. That single design choice kills hallucinations and renders the Reasoning Trace cleanly. Experience surfaces one card with one tap. The orange edge is the orchestrator. The orange arrow points at the Reasoning Trace, the glass box. That is the visual signature of the product.

## CITATIONS
[3] Health Connect, [5] UsageStatsManager https://developer.android.com/reference/android/app/usage/UsageStatsManager, [6] NotificationListenerService https://developer.android.com/reference/android/service/notification/NotificationListenerService, [4] Phi-3-mini https://arxiv.org/abs/2404.14219, [7] LangGraph https://langchain-ai.github.io/langgraph/, [8] Gemma https://ai.google.dev/gemma, [9] HealthKit https://developer.apple.com/documentation/healthkit.

## VISUAL BRIEF
Architecture diagram dominates. Cols 1-9 hold the three-layer Sense to Intelligence to Experience diagram at 1700 px wide x 720 px tall. Lane kickers SENSE / INTELLIGENCE / EXPERIENCE in 14 pt sans tracked +40 in #FF5B2E. Sense lane: seven small node boxes, each 220x56, no fill, 1 px #0E0E0E stroke, JetBrains Mono 14 pt labels (Health Connect, NotifListener, UsageStats, Calendar Provider, SMS Read, IME entropy, Gmail OAuth). Intelligence lane: orchestrator node 320x120 dead-centre with a 4 px #FF5B2E left edge accent, four agent nodes 240x96 in the corners, Memory Graph node centred at lane bottom. Experience lane: four surface nodes for Phone, Watch, Earbuds, Tablet/Laptop. Arrows are 1.5 px #0E0E0E orthogonal with simple triangular heads, never curved. One single sunset-orange arrow from Orchestrator to Trace drawer labelled the glass box. Cols 10-12 hold the Plausibility strip with six rows of Capability to Android API to iOS API in JetBrains Mono 14 pt. Bottom strip height 60 px collapses the eleven-step stress-driven mute path to one sentence. No glow, no neuron, no isometric.

## PERSUASION JOB
Convince the Engineer judge that the team has thought through runtime, APIs, and failure modes.

---

---
slide: 4a
title: Plausibility & Constraints (extended)
---
## BODY
Twelve capabilities. Two platforms. Three honest limits.
iOS blocks SMS and cross-app notifications.
Android primary, iOS reference. We never claim a kernel hook we don't have.

## SPEAKER NOTES
This is the honest table. Twelve capabilities Aura needs, mapped to Android and iOS APIs. Three places we cannot do on iOS what Android lets us do: SMS read does not exist on iOS, cross-app notifications are limited to our own app on iOS, and DeviceActivity gives us only partial app-launch data. We do not pretend otherwise. Production target is the Galaxy ecosystem with Health Connect as the substrate and Knox vault for memory-graph encryption. iOS reference build proves the algorithms are cross-platform on the hardest privacy substrate first. The line at the bottom is our promise to a Samsung engineer in the room: we will never claim a kernel hook we do not have, never quote a Galaxy Watch HRV number we measured on an Apple Watch, never show an iOS screenshot and call it One UI. That honesty is the credibility beat.

## CITATIONS
[3] Health Connect, [5] UsageStatsManager, [6] NotificationListenerService, [9] HealthKit. iOS DeviceActivity reference doc URL [TEAM TO VERIFY].

## VISUAL BRIEF
Full-width data table. Cols 1-12, single table, no shadow, no header fill, only a 2 px #0E0E0E rule under the header row and 1 px hairlines at 20% opacity between data rows. Header row Inter Tight 18 pt bold tracked +40, sunset-orange underline 4 px under the column Known limit. Capability column Inter Tight 18 pt regular, API columns JetBrains Mono 14 pt. Twelve rows covering app-launch, cross-app notifications, SMS, calendar, health, typing entropy, location, ambient audio level, battery, screen state, ringer, Gmail. Limit cells use a hand-drawn-feel sunset-orange triangle vector when a limit exists, blank when none, followed by 14 pt italic text. Bottom strip cols 1-12: a single Fraunces 32 pt line: We never claim a kernel hook we don't have. Reference: Stripe API tables, Apple HIG reference tables.

## PERSUASION JOB
Trust signal to Engineer and Samsung Exec — the team is honest about the Apple-vs-Samsung gap.

---

---
slide: 5
title: Novelty & Innovation
---
## BODY
Seven systems. Seven dimensions. One row that lights up.
Indian context depth, biometric closed loop, glass-box reasoning, Silence Budget, owned memory graph.

## SPEAKER NOTES
This is the only slide where I will name names. Gemini Live and Nano are reactive, partial anticipation, no biometric, weak Indian context. Apple Intelligence is privacy-strong but US-centric and has no glass-box. Samsung Bixby 2.0 is command-driven, low daily-active, no Reasoning Trace. Pixel Assistant is reactive and cloud-bound. Rabbit R1 had an action layer but shipped everything to the cloud. Humane Pin was abandoned. ChatGPT has no system access. Seven systems, seven dimensions: anticipatory, multi-agent, on-device LLM, biometric closed-loop, glass-box, Indian context, cross-surface. Aura is the only row with seven filled circles. Five wedges. Indian life-OS depth: UPI, IRCTC, Zomato, Swiggy, Blinkit, BMTC. Biometric closed loop via Health Connect or HealthKit HRV. Glass-box, every action emits a structured Reasoning Trace. Silence Budget, three proactive surfaces a day, capped, learnable down to zero, instrumented in the orchestrator. And a user-owned memory graph, exportable to JSON in one tap, deletable by node, edge, or time-range. Those five together are unbuyable in twelve weeks by anyone else in this room.

## CITATIONS
[10] Gemini / Gemma family, https://ai.google.dev/gemma.
[11] Apple Intelligence, https://www.apple.com/apple-intelligence/.
[12] Samsung Galaxy AI, https://www.samsung.com/global/galaxy/galaxy-ai/.
[13] Samsung Knox whitepapers, https://www.samsungknox.com/en/knox-platform/whitepapers.
[3] Health Connect. [9] HealthKit.
[14] UPI, https://www.npci.org.in/what-we-do/upi/product-overview.

## VISUAL BRIEF
Comparison table is the hero. Cols 1-12, single table at 1700 px wide x 760 px tall. Row labels in Inter Tight 22 pt regular. Column headers in Inter Tight 14 pt tracked +40: ANT / MULTI / ON-DEV / BIO / GLASS / IND / X-S. Cells use a vector glyph system: filled circle for yes/strong, half-circle for partial, empty ring for no. All glyphs in #0E0E0E except the Aura row, where every glyph is sunset-orange #FF5B2E. The Aura row has a 4 px #FF5B2E left edge accent and 1 px #FF5B2E top and bottom rules. The Aura label is set in Fraunces 32 pt instead of 22 pt sans, a deliberate type-scale break that makes the row read as the answer. Right-edge column carries a 14 pt italic wedge annotation per row. Footer 14 pt sans: Five wedges to Indian depth, biometric loop, glass-box, Silence Budget, owned memory. Reference: Stripe pricing comparison page, Linear vs-Jira table.

## PERSUASION JOB
Earn the unbuyable-wedge claim visually for the Business judge and Samsung Exec.

---

---
slide: 6
title: Open Datasets planned to be used / published
---
## BODY
Six datasets in. Three datasets out.
LSApp, Tsinghua, Melbourne for training. Pew, WHO, Kantar for framing.
Pilot CSV publishes with submission.

## SPEAKER NOTES
Six datasets we use. LSApp from arxiv 1911.04026 trains the next-app LSTM, public, research license. Tsinghua App Usage Trace augments it with geographic and temporal features. Melbourne Context Query Logs we use as adversarial input, heterogeneous queries that stress-test the orchestrator's decision routing. Pew Research, WHO adolescent mental health, and Kantar Gen Z India are framing citations only, no model touches them. Health Connect synthetic and real HRV samples come from per-user opt-in collection. Crucially, three datasets we will publish: anonymised pilot telemetry from thirty users, the Indian SMS and Gmail receipt parser corpus assembled with consent, and the Load Score versus self-rated stress correlation table. That is the verifiable raw evidence the brief asks for. Every figure in this deck has a citation tag. Every number we cannot yet measure carries a [TEAM TO VERIFY] tag instead of a guess.

## CITATIONS
[15] LSApp, https://arxiv.org/abs/1911.04026.
[16] Pew teens and technology, https://www.pewresearch.org/topic/internet-technology/teens-internet-technology/.
[17] WHO adolescent mental health, https://www.who.int/news-room/fact-sheets/detail/adolescent-mental-health.
[18] Kantar Gen Z, https://www.kantar.com/inspiration/research-services/genz.
[3] Health Connect. [9] HealthKit.
Tsinghua App Usage Trace and Melbourne Context Query Logs [TEAM TO VERIFY exact source URLs; add to plan.md §37.1 before submission].

## VISUAL BRIEF
Two-column index card. Cols 1-7 list six datasets, each as a 96 px row: dataset name in Fraunces 32 pt, role in Inter Tight 18 pt at 60% opacity, license in JetBrains Mono 14 pt right-aligned, 1 px hairline at 20% between rows. Rows: LSApp / Tsinghua App Usage Trace / Melbourne Context Query Logs / Pew, WHO, Kantar (framing) / Health Connect samples / Custom 30-user pilot telemetry. Cols 8-12 hold a single highlighted block with sunset-orange #FF5B2E top edge 4 px: heading Data we will publish in Fraunces 32 pt, then three lines: 30-user pilot telemetry (anonymised CSV), Indian SMS and Gmail receipt parser corpus, Load Score to self-rated stress correlation table. Bottom strip 14 pt sans: Every figure has a citation tag. Raw data publishes with submission. Reference: Hugging Face dataset cards, arxiv abstract pages.

## PERSUASION JOB
Show verifiable raw evidence and lift the team out of the demo-only category for the Engineer and Business judges.

---

---
slide: 7
title: Open Models planned to be used / developed / trained / fine-tuned
---
## BODY
Eight models. Three trained by us.
Gemma 2B Q4 with LoRA for Comms and Finance.
Phi-3-mini Q4 orchestrator. Llama-3-8B Q4 fallback. All on device.

## SPEAKER NOTES
Eight models, three trained by us. Gemma 2B quantised to Q4 underpins Communications and Finance, each with its own LoRA. Comms is fine-tuned on Enron-classified-public plus a small consented Indian email and notification corpus. Finance is fine-tuned on UPI SMS samples and Gmail receipt threads from Zomato, Swiggy, Blinkit, IRCTC, and Amazon India. Phi-3-mini Q4 is the orchestrator and the Calendar agent's prose engine, off-the-shelf with a system prompt for Phase 1, LoRA in Phase 2 if needed. Llama-3-8B Q4 is the heavy fallback, only routed to on devices with at least eight gigabytes of RAM and battery above thirty percent. The LSTM next-app predictor is one million parameters, our own training, trained on LSApp plus Tsinghua. MiniLM does embeddings into sqlite-vss. Whisper-tiny is encoder-only, we use prosody features, never store transcripts. Load Score is an XGBoost regressor, two hundred trees, calibrated against self-rated stress. Runtime is MediaPipe LLM Inference on Android, MLX on iOS for development, llama.cpp as cross-platform fallback. ExecuTorch evaluated for production Android.

## CITATIONS
[4] Phi-3-mini, https://arxiv.org/abs/2404.14219.
[8] Gemma, https://ai.google.dev/gemma.
[10] MediaPipe LLM Inference, https://ai.google.dev/edge/mediapipe/solutions/genai/llm_inference.
[19] llama.cpp, https://github.com/ggml-org/llama.cpp.
[20] ExecuTorch, https://pytorch.org/executorch/.
[15] LSApp for the next-app LSTM training corpus, https://arxiv.org/abs/1911.04026.
Llama-3 license terms [TEAM TO VERIFY].

## VISUAL BRIEF
Single full-width spec table. Same visual grammar as slide 4a so the deck reads as a system. Cols 1-12, table 1700x760 px. Eight rows. Header row Inter Tight 18 pt bold tracked +40: Role / Model / Size / Quantization / License / Training plan. Role in Inter Tight 22 pt, Model in JetBrains Mono 18 pt. License column uses a small #0E0E0E square glyph for permissive (MIT, Apache, Gemma) and a #FF5B2E square for vendor-licensed check before ship, applied to Gemma terms and Llama license. Right-edge thin column Owned weights with a sunset-orange dot for any row where Aura's LoRA delta is the team's own training output: CommsAgent, FinanceAgent, App-prediction LSTM, and Load Score XGBoost. Rows: CommsAgent Gemma 2B Q4 LoRA / FinanceAgent Gemma 2B distil Q4 LoRA / CalendarAgent Phi-3-mini Q4 sysprompt / Orchestrator Phi-3-mini Q4 sysprompt / Heavy fallback Llama-3-8B Q4 off-the-shelf / App-pred LSTM 2L 128h fp16 trained / Embeddings all-MiniLM-L6-v2 int8 off-the-shelf / Prosody Whisper-tiny encoder int8 encoder only. Footer 14 pt: Runtime: MediaPipe LLM Inference (Android), MLX (iOS dev), llama.cpp. Reference: Hugging Face model index, Replicate.

## PERSUASION JOB
Engineering credibility through named models, sizes, quantisations, and an Owned weights column for the Engineer judge.

---

---
slide: 8
title: AI / GenAI / Agentic tools used / developed
---
## BODY
Six tools. Two built by us. Four open.
LangGraph state machine. sqlite-vss memory. MediaPipe and llama.cpp runtimes. PEFT for LoRA. ExecuTorch for Android prod.

## SPEAKER NOTES
Six tools. The two with the orange edge are the ones we extend ourselves. LangGraph runs the orchestrator as a deterministic state machine: Idle, Listening, Deliberating, AwaitingConfirm, Executing, LoggingTrace, Cooldown. Every transition is guarded. We can fuzz it. sqlite-vss is the on-device vector store inside the encrypted memory graph. We built the schema, the typed node and edge model, the Merkle audit log, and the per-day root display. MediaPipe LLM Inference is our Android runtime for the Q4 models. llama.cpp is our cross-platform fallback with Swift bindings on iOS. PEFT plus QLoRA at rank sixteen is the training pipeline, runs locally on the Alienware RTX 4080, no cloud GPU spend. ExecuTorch is the production Android target evaluated as a successor to MediaPipe LLM. Cursor and Claude Code are the development glue for code generation. Nothing here is exotic. The discipline is in the glue, typed JSON tool schemas between agents, never free-form chat.

## CITATIONS
[7] LangGraph, https://langchain-ai.github.io/langgraph/.
[10] MediaPipe LLM Inference, https://ai.google.dev/edge/mediapipe/solutions/genai/llm_inference.
[19] llama.cpp, https://github.com/ggml-org/llama.cpp.
[20] ExecuTorch, https://pytorch.org/executorch/.
[21] CrewAI reference, https://docs.crewai.com/.
[22] AutoGen tool-calling reference, https://arxiv.org/abs/2308.08155.
PEFT Hugging Face reference and sqlite-vss [TEAM TO VERIFY exact URLs].

## VISUAL BRIEF
Bento grid, six tiles, three rows by two columns. Each tile 800 px wide x 200 px tall. Inside each tile: tool name in Fraunces 32 pt top-left, one-line role in Inter Tight 18 pt directly under, then a 14 pt mono row showing the call-site or class. The orchestrator-related tiles LangGraph and sqlite-vss carry a 4 px sunset-orange top edge, mirroring the architecture diagram. Other tiles are neutral. Tile separators are 16 px gaps, no card strokes, no shadows. Six tiles: LangGraph deterministic state machine / MediaPipe LLM Inference Android runtime / sqlite-vss vector store on-device encrypted / llama.cpp cross-platform inference / PEFT LoRA training pipeline QLoRA r=16 local RTX 4080 / ExecuTorch production Android target. Bottom strip 14 pt sans colour key: team-built / open-source / vendor-licensed / trained by us. Reference: GitHub README badges page, Linear engineering blog tile layout.

## PERSUASION JOB
Engineering taste signal: name the exact glue, not generic AI agents and orchestration.

---

---
slide: 8a
title: Best Practices & Creative AI Use (extended)
---
## BODY
One action, one trace. Every time.
Deterministic state machine. Typed JSON tool calls. Confirm-required by default.
No black box. No free-form chatter.

## SPEAKER NOTES
Three discipline choices that matter more than model selection. One: deterministic state machine. The orchestrator runs as a LangGraph DAG with seven named states: Idle, Listening, Deliberating, AwaitingConfirm, Executing, LoggingTrace, Cooldown. No state can be entered without a guarded transition. We can fuzz it with synthetic input fixtures committed to the repo. Two: typed JSON tool calls between agents. The LLM never produces free-form prose to talk to another agent. Every inter-agent call validates against a schema in orchestrator/tools.py. That kills hallucinated tool calls and lets us render the Reasoning Trace deterministically. Three: confirm-required by default. No non-trivial autonomous action without one user tap. The trace on the left is from a real stress-driven mute on Tuesday: Load Score crossed seventy from HRV and app-switch rate, candidate set ranked, mute selected, user tapped accept. The trace is local-only, immutable, and the user can inspect, edit, or reject every entry. That is the glass box.

## CITATIONS
[7] LangGraph, https://langchain-ai.github.io/langgraph/.
[4] Phi-3-mini, https://arxiv.org/abs/2404.14219.
[22] AutoGen tool-calling pattern reference, https://arxiv.org/abs/2308.08155.

## VISUAL BRIEF
Split layout. Cols 1-6 hold a single Reasoning Trace sample rendered as JetBrains Mono 16 pt code on #FAF8F5, no syntax-highlight colours except sunset-orange #FF5B2E on the keys chosen, rationale, and confirm_required. The trace is the eleven-step stress-driven mute from plan.md §11, collapsed to JSON, about 22 lines. Above the code block, kicker 18 pt sans tracked +40: ONE ACTION, ONE TRACE. Cols 7-12 hold a stack of three best-practice cards, each 540x220 px, separated by 24 px gap. Card 1 Deterministic state machine, with the seven-state list in mono 12 pt below. Card 2 Typed JSON tool calls, never free-form chat between agents. Card 3 Confirm-required by default, no autonomous action without one tap from user. Each card has a 1 px #0E0E0E top hairline, title in Fraunces 32 pt, body Inter Tight 18 pt. Reference: Stripe API docs JSON examples, Linear API reference.

## PERSUASION JOB
Convert the Engineer and Designer judges by making the Reasoning Trace JSON the artefact the team is remembered by.

---

---
slide: 9
title: Optional supporting
---
## BODY
Six KPIs, paired bars, 95% confidence intervals.
Thirty quantitative users. Eight qualitative. Five tasks.
Live demo on Hugging Face. Raw CSV with Phase 2.

## SPEAKER NOTES
Six KPIs match the brief one-for-one: effort reduction, task completion, autonomy quality, satisfaction, stress reduction, willingness to pay. Each bar pair is baseline versus Aura, with ninety-five percent confidence intervals. Solid bars are measured. Dashed bars tagged Phase 2 are not yet collected, we are not painting performance we have not earned. Method: thirty quantitative participants from Thapar campus across years and branches, mixed gender and hostel-versus-day-scholar, plus eight qualitative including two from Bangalore for city balance. Five standardised tasks per user, randomised order, baseline first then prototype. Statistics: means with confidence intervals, paired t-test or Wilcoxon as appropriate, Cohen's d for effect size, Cohen's kappa for inter-rater autonomy score, Spearman correlation for Load Score versus self-rated stress. Raw CSVs publish in the repo behind the QR with the Phase 2 submission. The privacy story stands on a one-tap export, a tamper-evident audit log, and a panic-wipe gesture. We do not promise unbreakable privacy. We promise the user owns the data and can see and erase it. Thank you.

## CITATIONS
KPI targets all from the EnnovateX 2026 problem brief.
[16] Pew teens and technology, https://www.pewresearch.org/topic/internet-technology/teens-internet-technology/.
[17] WHO adolescent mental health, https://www.who.int/news-room/fact-sheets/detail/adolescent-mental-health.
[18] Kantar Gen Z, https://www.kantar.com/inspiration/research-services/genz.
Methodology from plan.md §22 and §23. Phase 1 freeze: all bars dashed at submission [TEAM TO VERIFY any baseline measured before deck freeze].

## VISUAL BRIEF
Three-zone layout. Top zone cols 1-12 height 480 px holds the KPI bar chart at 1700x380 px. Six paired bars, Effort reduction / Task completion / AI autonomy quality / Satisfaction / Stress reduction / Willingness to pay. Baseline bars in #0E0E0E at 30% opacity. Aura bars in solid #FF5B2E for measured, dashed #FF5B2E outline for Phase 2 not yet collected. Error bars only on measured. Legend top-right inline 14 pt sans. Bottom-left zone cols 1-7 height 400 px holds the pilot methodology paragraph in Inter Tight 22 pt with three callout numerals 30, 8, 5 in Fraunces 96 pt for thirty quant, eight qual, five tasks. Bottom-right zone cols 8-12 height 400 px holds the evidence block: 'github.com/ShAuRyA-Noodle/Combobulating' in JetBrains Mono 22 pt, 'huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin' in 18 pt below, two 200x200 QR codes in #0E0E0E on #FAF8F5 (one to repo, one to live HF Space), and a 14 pt sans line 'Phase 2 raw CSV publishes here'. Sunset orange used only on Aura bars and the QR border. Reference: Linear roadmap pages, Notion product analytics.

## PERSUASION JOB
Closing trust signal across all four judge personas: statistics rigour, chart readability, WTP target, raw-CSV publishing commitment.

---

