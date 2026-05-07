# Citation Map — Slides 2 through 8

Every numerical or named claim on slides 2 through 8, mapped to its source in plan.md §37.1 (or carrying [TEAM TO VERIFY]).

---

## Slide 2 — Problem Statement

| Claim | Source |
|---|---|
| 237 notifications/day for Gen Z phone | [1] Common Sense Media 2023, "Constant Companion: A Week in the Life of a Young Person's Smartphone Use" — locked per plan.md §0 and §35 row 13 |
| Cognitive overload framing for Gen Z | [2] Pew Research, https://www.pewresearch.org/topic/internet-technology/teens-internet-technology/ — plan.md §37.1 |
| Adolescent mental health context | [3] WHO, https://www.who.int/news-room/fact-sheets/detail/adolescent-mental-health — plan.md §37.1 |
| KPI targets (30%, 90%, 85%, 4.5, 60%) | EnnovateX 2026 problem brief, plan.md §3.1 |
| Gemini, Siri, Bixby, Pixel reactive characterisation | plan.md §3.3 and §8 (competitive table) |

## Slide 3 — Proposed Solution

| Claim | Source |
|---|---|
| On-device multi-agent architecture | plan.md §1.2, §4.1 |
| Four agents (Comms, Calendar, Finance, Wellness) | plan.md §10.2, §12 |
| Phi-3-mini orchestrator | [4] https://arxiv.org/abs/2404.14219 — plan.md §37.1 |
| Health Connect for HRV / sleep | [3] https://developer.android.com/health-and-fitness/guides/health-connect — plan.md §37.1 |
| BMTC, IRCTC, Zomato, UPI named artefacts | plan.md §9.1 — named real artefacts, no citation required per deck_spec.md §2 Indian context rule |
| Silence Budget = 3 proactive surfaces/day, learnable to 0 | plan.md §1.2 and competitive.md §2.6 hardening |

## Slide 4 — Technical Details

| Claim | Source |
|---|---|
| UsageStatsManager for app-launch sequences | [5] https://developer.android.com/reference/android/app/usage/UsageStatsManager — plan.md §37.1 |
| NotificationListenerService for cross-app notifications | [6] https://developer.android.com/reference/android/service/notification/NotificationListenerService — plan.md §37.1 |
| Health Connect for HRV/sleep/HR | [3] plan.md §37.1 |
| HealthKit on iOS | [9] https://developer.apple.com/documentation/healthkit — plan.md §37.1 |
| LangGraph state machine | [7] https://langchain-ai.github.io/langgraph/ — plan.md §37.1 |
| Gemma 2B for agents | [8] https://ai.google.dev/gemma — plan.md §37.1 |
| Phi-3-mini orchestrator | [4] plan.md §37.1 |
| Typed JSON tool calls between agents | plan.md §10.2, §13 |
| Reasoning Trace schema | plan.md §13 |

## Slide 4a — Plausibility & Constraints

| Claim | Source |
|---|---|
| iOS blocks SMS read | plan.md §10.1 (table), §17.2 |
| iOS UNUserNotificationCenter limited to own app | plan.md §10.1 |
| DeviceActivity partial app-launch data on iOS | plan.md §10.1, [TEAM TO VERIFY exact docs URL] |
| Twelve capabilities mapped Android↔iOS | plan.md §10.1 (full table) |
| "We never claim a kernel hook we don't have" | plan.md §21.3, §21.4 framing |

## Slide 5 — Novelty & Innovation

| Claim | Source |
|---|---|
| Comparison cell values (Gemini, Apple, Bixby, Pixel, Rabbit, Humane, ChatGPT) | plan.md §8 (full table) and competitive.md §1.1–1.7 |
| Gemini reactive, weak Indian context | competitive.md §1.1, [10] https://ai.google.dev/gemma — plan.md §37.1 |
| Apple Intelligence privacy-strong, no glass-box | competitive.md §1.2, [11] https://www.apple.com/apple-intelligence/ — plan.md §37.1 |
| Samsung Galaxy AI substrate | [12] https://www.samsung.com/global/galaxy/galaxy-ai/ — plan.md §37.1 |
| Knox as privacy substrate | [13] https://www.samsungknox.com/en/knox-platform/whitepapers — plan.md §37.1 |
| UPI named artefact | [14] https://www.npci.org.in/what-we-do/upi/product-overview — plan.md §37.1 |
| Five wedges (Indian depth, biometric loop, glass-box, Silence Budget, owned memory) | plan.md §9.1–9.5 + competitive.md §2.6 |
| "Unbuyable in twelve weeks" claim | competitive.md §1.8 (cross-cutting) |

## Slide 6 — Open Datasets

| Claim | Source |
|---|---|
| LSApp for next-app LSTM training | [15] https://arxiv.org/abs/1911.04026 — plan.md §37.1 |
| Tsinghua App Usage Trace | plan.md §16, [TEAM TO VERIFY URL — not in §37.1 yet] |
| Melbourne Context Query Logs | plan.md §16 (problem brief reference), [TEAM TO VERIFY URL] |
| Pew teens and technology | [16] https://www.pewresearch.org/topic/internet-technology/teens-internet-technology/ — plan.md §37.1 |
| WHO adolescent mental health | [17] https://www.who.int/news-room/fact-sheets/detail/adolescent-mental-health — plan.md §37.1 |
| Kantar Gen Z | [18] https://www.kantar.com/inspiration/research-services/genz — plan.md §37.1 |
| 30-user pilot telemetry to publish | plan.md §16 and §22 |
| Indian SMS / Gmail receipt parser corpus | plan.md §16 — self-collected with consent |
| Load Score ↔ self-rated stress correlation | plan.md §12.4 validation, §22.3 statistical reporting |

## Slide 7 — Open Models

| Claim | Source |
|---|---|
| Gemma 2B Q4 with LoRA for Comms | plan.md §15, §12.1 — [8] plan.md §37.1 |
| Gemma 2B Q4 with LoRA for Finance | plan.md §15, §12.3 |
| Phi-3-mini Q4 orchestrator | [4] plan.md §37.1 |
| Llama-3-8B Q4 heavy fallback | plan.md §15 — Llama-3 license [TEAM TO VERIFY] |
| LSTM 2-layer 128h next-app | plan.md §15, trained on [15] LSApp |
| all-MiniLM-L6-v2 int8 embeddings | plan.md §15 |
| Whisper-tiny encoder-only | plan.md §15 |
| XGBoost 200 trees Load Score | plan.md §15, §12.4 |
| MediaPipe LLM Inference runtime | [10] https://ai.google.dev/edge/mediapipe/solutions/genai/llm_inference — plan.md §37.1 |
| llama.cpp runtime | [19] https://github.com/ggml-org/llama.cpp — plan.md §37.1 |
| ExecuTorch evaluation | [20] https://pytorch.org/executorch/ — plan.md §37.1 |

## Slide 8 — AI / GenAI / Agentic Tools

| Claim | Source |
|---|---|
| LangGraph deterministic state machine | [7] plan.md §37.1 — see plan.md §13 for state list |
| sqlite-vss vector store, encrypted at rest | plan.md §14, §10.2 — [TEAM TO VERIFY exact upstream URL] |
| MediaPipe LLM Inference (Android) | [10] plan.md §37.1 |
| llama.cpp (cross-platform) | [19] plan.md §37.1 |
| PEFT + QLoRA r=16 training pipeline | plan.md §18.3 — Hugging Face PEFT [TEAM TO VERIFY URL] |
| ExecuTorch (production Android) | [20] plan.md §37.1 |
| CrewAI reference (mentioned only) | [21] https://docs.crewai.com/ — plan.md §37.1 |
| AutoGen tool-calling reference | [22] https://arxiv.org/abs/2308.08155 — plan.md §37.1 |
| Cursor and Claude Code as dev tooling | plan.md §18.4 |

---

## Numbered reference list (one source of truth)

[1] Common Sense Media 2023, "Constant Companion".
[2] Pew Research teens and technology — plan.md §37.1.
[3] Health Connect — plan.md §37.1.
[4] Phi-3-mini — plan.md §37.1.
[5] UsageStatsManager — plan.md §37.1.
[6] NotificationListenerService — plan.md §37.1.
[7] LangGraph — plan.md §37.1.
[8] Gemma — plan.md §37.1.
[9] HealthKit — plan.md §37.1.
[10] MediaPipe LLM Inference — plan.md §37.1.
[11] Apple Intelligence — plan.md §37.1.
[12] Samsung Galaxy AI — plan.md §37.1.
[13] Samsung Knox — plan.md §37.1.
[14] UPI / NPCI — plan.md §37.1.
[15] LSApp arxiv 1911.04026 — plan.md §37.1.
[16] Pew teens — plan.md §37.1.
[17] WHO adolescent mental health — plan.md §37.1.
[18] Kantar Gen Z — plan.md §37.1.
[19] llama.cpp — plan.md §37.1.
[20] ExecuTorch — plan.md §37.1.
[21] CrewAI — plan.md §37.1.
[22] AutoGen — plan.md §37.1.

[TEAM TO VERIFY] gaps before submission: Tsinghua App Usage Trace URL, Melbourne Context Query Logs URL, iOS DeviceActivity exact docs URL, Llama-3 license terms text, PEFT Hugging Face exact URL, sqlite-vss upstream repo URL.
