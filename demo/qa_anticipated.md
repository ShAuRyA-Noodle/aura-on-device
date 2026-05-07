# Aura — 30 Anticipated Judge Questions (Rehearsed Answers)

Compiled from `competitive.md` §3. Grouped by judge persona. Every answer is 2–3 sentences for verbatim rehearsal. The slide reference at the end of each answer is the slide we hold up while answering.

---

## Group A — Samsung R&D Engineer (Bangalore SRI-B)

**Q1. What is your inference budget per orchestrator tick on a Galaxy S24, peak and median?**
We target sub-300 ms median per `tick()` per agent (plan §12.5), with the Phi-3-mini orchestrator running in MediaPipe LLM Inference at Q4 quantisation. Peak we accept up to 800 ms during a heavy ranking step with Llama-3-8B fallback; we measure both in the Phase 2 prototype and report on the device-eval slide. — *slide 4 / 4a*

**Q2. Why Phi-3-mini and not Gemma 3 4B, which Samsung's own runtime supports better?**
Phi-3-mini is the orchestrator because of its strong tool-use behaviour at small size and its MIT licence; Gemma 2B is the agent-level model where instruction-tuned chat fluency matters less. We have Gemma 3 4B as a drop-in evaluation candidate and will benchmark it on a Galaxy S24 in Phase 2; the orchestrator interface is model-agnostic by design. — *slide 7*

**Q3. How do you handle thermal throttling during a 5-minute orchestrator-heavy session?**
Three mitigations: orchestrator runs only on event triggers, not every tick; agents stay sub-second and are scheduled cooperatively; and the heavy fallback only routes when battery is above 30% and the device is not in a thermal-warning state, per plan §13. — *slide 4*

**Q4. NotificationListenerService grants are restricted in OneUI 7. How do you justify the permission ask?**
We use NotificationListenerService specifically for triage, with an explanation screen in the permission UX (plan §17.3) that names exactly which agent uses the data and what is stored. We never store message bodies — only `{sender_hash, intent_label, urgency_score, ts}` per plan §12.1. — *slide 4*

**Q5. Health Connect vs Samsung Health SDK — which?**
Health Connect is the substrate because it is Samsung-Google joint and exposes HRV, sleep, and HR uniformly. Samsung Health SDK additions are layered for Galaxy Watch–specific signals if available. The iOS reference build uses HealthKit; HealthKit ↔ Health Connect parity is documented in the slide-4 API table. — *slide 4*

**Q6. What is the typing entropy metric and what is the privacy posture?**
A custom IME on Android (or custom keyboard on iOS, narrower) emits per-minute Shannon entropy buckets of inter-keystroke timing only — never characters, never words. The bucket is one int per minute and is part of the Load Score composite as a frustration proxy. — *slide 4 / 4a*

**Q7. SQLite-vss on-device — what is the embedding cost and the storage growth rate?**
MiniLM-L6 at int8 produces 384-dim vectors at ~1 KB each. With a 90-day structured-event retention default (plan §14), expected graph size for a heavy user is 50–200 MB. Settings → Storage exposes a per-type retention slider. — *slide 4*

**Q8. How do you stop the orchestrator from looping when an agent emits a malformed tool call?**
Inter-agent communication is typed JSON only, validated against the schema in `orchestrator/tools.py` (plan §10.2); a malformed call is rejected before it enters the LangGraph state machine. The state machine has a `Cooldown` state with a hard timeout, so a stuck transition reverts to `Idle` within a defined window. — *slide 4*

**Q9. What is your model update story without cloud?**
Model artefacts ship inside the app bundle for Phase 1; Phase 2 explores delta updates via signed bundles fetched on user-initiated check, never silently. Fine-tunes (LoRA adapters) are small enough to ship as updates of a few MB. — *slide 7 / 8*

**Q10. The Reasoning Trace is structured JSON. How is it rendered without a privacy leak when the user shares it?**
Trace items reference graph node IDs, not content. Sharing a trace exports the trace structure plus optionally redacted node summaries (sender_hash not sender_name, place_id not place_name). The user explicitly chooses redacted or full at export time. — *slide 9*

---

## Group B — Bixby PM

**Q11. Why is this not a Bixby Routine?**
A Bixby Routine is a single trigger-action; Aura is a multi-agent orchestrator that ranks across candidate actions with a learnable cost function and a memory graph. We frame Aura as "what Bixby Routines could become if Bixby had a memory layer and a ranker" — a reference architecture for Galaxy AI's next generation. — *slide 5*

**Q12. Why does the user need four agents instead of one assistant?**
Specialisation lets each agent run the right model at the right size — Gemma 2B for language, XGBoost for Load Score, rule engine for calendar conflicts (plan §12). One unified LLM doing all four would be slower, less testable, and less observable in the Reasoning Trace. The four-agent shape is also the right organising metaphor for the user — Comms, Calendar, Finance, Wellness map to mental models the user already has. — *slide 4*

**Q13. How is this not just a more confusing version of Now Brief?**
Now Brief is a morning summary card; Aura is a continuous orchestrator that runs all day and produces actions, not summaries. The Morning Brief is one of five user journeys, not the product (plan §7). — *slide 3*

**Q14. What stops a user from getting overwhelmed by Reasoning Traces?**
Traces are pull, not push — they live in a drawer behind every action card and in a Memory tab. The user sees a trace only when they choose to look, typically after a wrong or surprising nudge. The default UX is the action card with a one-line "why". — *slide 4 / 9*

**Q15. What is the hook in the first 30 seconds of using Aura?**
The Morning Brief: a single card replacing four app opens, validated against the user's actual sleep, calendar, commute, and conversations. The user sees in 30 seconds that Aura saved them four taps and three context switches. — *slide 3 / 9*

**Q16. How do you prevent the silence contract from making the product feel dead?**
The product is silent when nothing serves the user; it is loud-enough at the moments that matter (Morning Brief, leave-by alert, closed-loop stress mute). Plan §10.3 specifies multi-surface (phone, watch haptic, earbud whisper) so a single proactive surface lands meaningfully. The silence is contrast, not absence. — *slide 4*

**Q17. The market for empathy AI is unproven. Why now?**
The cognitive overload diagnosis is empirically grounded (Pew, WHO, Kantar — plan §16) and the substrate (on-device LLMs at sub-4B with usable latency) crossed the threshold in 2024–2025. We are not asking the market to want empathy AI; we are giving Gen Z India a measurable reduction in tap count and an HRV-confirmed bump in recovery. The willingness-to-pay KPI ≥ 60% is the market test. — *slide 9*

**Q18. Why on-device when Gemini Live runs cloud and is faster and smarter?**
Cloud assistants cannot read NotificationListener, SMS, HealthKit, or HRV streams without sending them off-device — the privacy cost users are increasingly unwilling to pay. On-device is the only architecture that lets us see the signals that matter without becoming a surveillance product, and we accept the latency / model-size trade-off as a feature, not a bug. — *slide 4 / 5*

**Q19. What does cross-surface continuity look like in practice on Galaxy?**
Phone is the orchestrator host; Galaxy Watch surfaces glance + haptic for proactive nudges; Galaxy Buds for whisper TTS; Tab as a continuation pull-tab via Nearby Connections. The same code path on iOS uses Apple Watch, AirPods, and Multipeer Connectivity (plan §10.3). — *slide 4*

**Q20. What is the differentiation versus what Galaxy AI is going to ship in OneUI 8?**
We do not know exactly what OneUI 8 will ship; we expect Galaxy AI to keep moving toward proactive cards and Now Brief depth. Our wedges (glass-box trace, exportable memory graph, silence budget, biometric closed loop, Indian context depth shipped together) remain structurally outside Samsung's current architecture, and we frame Aura as a reference architecture Samsung could adopt. — *slide 5*

---

## Group C — Galaxy AI Lead / Samsung Executive

**Q21. What is the Galaxy ecosystem story and how does Aura fit?**
Galaxy AI is the brand; Aura is an empathetic intelligence layer built on Galaxy AI's substrates — on-device inference via MediaPipe LLM Inference, biometrics via Health Connect, privacy via Knox vault, cross-device via Nearby Connections. We position Aura as a portfolio addition, not a replacement. — *slide 5*

**Q22. What partnerships do you need from Samsung to ship this in production?**
Three: Health Connect SDK access for sub-minute HRV, Knox vault enrolment for the memory-graph encryption keys, and a Galaxy AI integration channel for surfacing actions on Now Brief. None require new APIs; all require existing partner programs. — *slide 9*

**Q23. What is the path from hackathon prototype to Galaxy Store app?**
Phase 2 prototype on Galaxy S-series with Health Connect integration; Phase 3 Galaxy Store soft launch as a beta in India in Q4 2026; broader OneUI surface integration via Galaxy AI partner program in 2027. — *slide 9*

**Q24. The aesthetic looks like a Linear app. Why should a Samsung user respond to it?**
The visual language is editorial and anti-corporate by design (plan §5.1). Indian Gen Z and Gen Alpha users overwhelmingly prefer this aesthetic over the legacy Material/OneUI surface in our pilot research. The art direction is Galaxy-friendly — warm off-white, ink black, single accent — and would fit the Galaxy AI design system with minor token swaps. — *slide 3*

**Q25. What is your moat against Google deciding to ship this in Gemini next quarter?**
Three layers: the Indian context corpus is hard to assemble without on-the-ground research; the silence-budget ranker plus Reasoning Trace is structurally counter to Google's engagement-optimised posture; and the user-owned exportable memory graph is a privacy promise Google's business model cannot make. The moat is uncomfortable for a global incumbent to copy, not uncopyable — and we say so. — *slide 5*

---

## Group D — Samsung Ventures Partner / Indian VC

**Q26. What is the unit economics at scale?**
Free tier with progressive permission ask; paid tier at ₹199 / month for memory-graph export, advanced Wellness analytics, and longer retention. Willingness-to-pay target ≥ 60% in the Phase 2 pilot (plan §22). Server costs are near-zero because inference is on-device; cost-of-goods is dominated by model-artefact bandwidth on update and team salaries. — *slide 9*

**Q27. What is the TAM and the wedge into it?**
Indian Gen Z and Gen Alpha smartphone users — roughly 250 M+ smartphone users under 25 by 2026, weighted toward Galaxy A-series and mid-range Android. The wedge: ~30 M who are heavy WhatsApp + Zomato + UPI + Insta users with measurable cognitive load — the segment that pays for premium experiences. — *slide 9*

**Q28. Distribution strategy — how do you acquire the first 10,000 users?**
Campus-first via the Thapar pilot, then expansion across Christ University (Bangalore), Manipal, and IIITs — campuses are dense graphs where word-of-mouth lifts CAC near zero. A second beat is creator-led on Instagram and YouTube with Indian product reviewers in the productivity / tech aesthetic niche. — *slide 9*

**Q29. Who is the team and why are you the right founders?**
Two engineers from Thapar Institute. Shaurya leads architecture, ML, and on-stage delivery; Shorya leads app build and agent plumbing. Recommendation in plan §25 to add a designer in Week 2. We are the right founders because we are the user — Indian Gen Z, hostel-resident, daily WhatsApp / UPI / Zomato / Insta — and we have the technical depth to execute on-device multi-agent at sub-4B. — *slide 1*

**Q30. What is the risk you are most afraid of?**
The Apple-only device constraint on a Samsung-judged hackathon, named in plan §21 and §27 (R1). We do not buy or borrow Samsung hardware. We mitigate with explicit cross-platform framing on slide 4 (HealthKit ↔ Health Connect API parity), Android-emulator screen-recording for any Phase 2 Galaxy demo, and an honest Phase 3 opening line that names the constraint upfront. We never demo iOS and call it Galaxy. — *slide 4*

---

## Rehearsal protocol

- Each presenter rehearses their assigned half (Shaurya: Q1–Q15, Shorya: Q16–Q30) twice, alone, then once together.
- Time every answer; cap at 30 s spoken.
- Record one full Q&A round to phone audio, listen back, kill any "uh", "like", "basically".
- Bring a printed copy of this file to Bangalore. The judges will ask at least four of these.
