# Aura — Glossary

Defined terms used across the Aura documentation and codebase.

---

**3 layers** — Aura's architectural decomposition: Sense (signal acquisition), Intelligence (four agents + orchestrator), Experience (phone, watch, earbuds, tablet surfaces). See `architecture.md` §2 and `plan.md` §10.

**BMTC** — Bengaluru Metropolitan Transport Corporation. The Bangalore city bus system. Aura ingests BMTC live data into commute reminders for users in Bangalore (`plan.md` §9.1).

**Gemma 2B** — Google's open 2-billion-parameter instruction-tuned LLM. Aura uses Gemma 2B Q4_K_M as the agent-side LLM for CommsAgent and FinanceAgent, with hot-swapped LoRA adapters per agent. License: Gemma terms. https://ai.google.dev/gemma

**GGUF** — GPT-Generated Unified Format. The model file format used by `llama.cpp`. Aura ships GGUF Q4_K_M artifacts for the cross-platform llama.cpp inference path. https://github.com/ggml-org/llama.cpp

**Glass-box** — Adjective describing Aura's commitment to making every autonomous or semi-autonomous action inspectable. Concretised by the Reasoning Trace.

**Health Connect** — Android's unified health data platform. Aura reads HRV, sleep, HR, and steps from Health Connect on Android. https://developer.android.com/health-and-fitness/guides/health-connect

**HealthKit** — iOS's unified health data platform. Aura reads HRV, sleep, HR, and steps from HealthKit on iOS. https://developer.apple.com/documentation/healthkit

**HRV** — Heart Rate Variability. The variation in time between heartbeats. Aura uses HRV (specifically RMSSD) as a Wellness Agent input feature for the Load Score (`technical_spec.md` §7.1).

**IRCTC** — Indian Railway Catering and Tourism Corporation. The Indian Railways ticketing system. Aura parses IRCTC PNR confirmations into the calendar (`plan.md` §9.1).

**Knox** — Samsung's mobile-security platform offering hardware-rooted device protection and a secure execution environment. Aura's Phase 1 deck names Knox-backed memory graph encryption as the production target (ADR-0006). https://www.samsungknox.com/en/knox-platform/whitepapers

**Load Score** — Aura's composite stress / cognitive-load measure, output by the Wellness Agent. Range 0–100. Computed by an XGBoost regressor over nine features: HRV (raw + z-score), sleep debt, typing entropy, app-switch rate, notification dismiss rate, screen-on minutes, and time-of-day sin/cos. Calibrated against self-rated stress 1–5 and reported as Spearman ρ in Phase 2. (`technical_spec.md` §7)

**LoRA** — Low-Rank Adaptation. A parameter-efficient fine-tuning technique that adds small adapter matrices to selected attention projections (`q_proj`, `v_proj`, `o_proj` in Aura's case). Aura trains LoRA adapters on Gemma 2B for CommsAgent and FinanceAgent on the RTX 4080. (`technical_spec.md` §9)

**Memory Graph** — Aura's on-device structured store of the user's history: nodes (User, Event, App, Person, Place, Transaction, Conversation, HealthSnapshot, Action, Trace) and edges (attended, sent_to, located_at, paid_to, talked_about, felt_during, triggered_by, confirmed_by_user). SQLite + sqlite-vss + SQLCipher. (`technical_spec.md` §6)

**MLX** — Apple's array framework for ML on Apple Silicon, similar in spirit to NumPy but GPU-accelerated. Aura uses MLX as the iOS dev-time inference runtime for Gemma 2B and Phi-3-mini. https://github.com/ml-explore/mlx

**NotificationListenerService** — Android's mechanism for letting an app observe system notifications. Aura's CommsAgent reads notification metadata via `NotificationListenerService`. https://developer.android.com/reference/android/service/notification/NotificationListenerService

**Phi-3-mini** — Microsoft's 3.8-billion-parameter compact LLM with strong tool-use behaviour. Aura uses Phi-3-mini-4k-instruct Q4 as the orchestrator's default model (ADR-0002). https://arxiv.org/abs/2404.14219

**Reasoning Trace** — Aura's structured, schema-validated record of a single decision: trigger, signals seen, candidates considered, chosen action, rationale, confirm-required flag, outcome, and any redactions. Schema in `trace.v1.json` (`technical_spec.md` §4.6). User-visible via a drawer attached to the originating action card. Retention 30 days default, user-overridable. ADR-0004.

**RMSSD** — Root Mean Square of Successive Differences. A time-domain heart-rate-variability metric correlated with parasympathetic nervous-system activity. Aura's Wellness Agent reads RMSSD over a 5-minute rolling window from Health Connect / HealthKit. (`technical_spec.md` §7.1)

**Silence Budget** — Aura's named state variable representing the daily quota of proactive non-safety surfaces. Default 3 tokens per local day; each surface consumes one token; user "Useful" tap refunds one token capped at the daily ceiling. Safety-class Wellness actions (mute, breathe, nap) are exempt. Visible as three dots in Settings; Phase 2 KPI alongside effort reduction and satisfaction. ADR-0003.

**UPI** — Unified Payments Interface. India's instant real-time payment system operated by NPCI. Aura parses UPI SMS notifications from Indian banks via a regex template pack with DistilBERT fallback for unknown templates. (`plan.md` §9.1, `technical_spec.md` §3.3) https://www.npci.org.in/what-we-do/upi/product-overview

**Wedge** — One of Aura's five differentiators versus the SOTA comparison row (`plan.md` §9): Indian life-OS depth, closed-loop biometric to action, glass-box Reasoning Trace, silence as a feature, and user-owned memory graph.

---

End of `glossary.md`.
