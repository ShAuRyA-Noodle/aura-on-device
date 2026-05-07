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
