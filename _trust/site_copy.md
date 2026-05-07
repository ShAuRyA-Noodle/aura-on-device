# Aura — Landing Page Copy

Bento-friendly. Sections map 1:1 to landing-page modules.
Voice rules from `deck_spec.md` §0: strict English, no banned words,
named real artefacts only, body copy short, depth in supporting text.
Word count: ~1,950.

---

## Hero

**Aura.**
Anticipate. Act. Stay quiet.

An on-device empathetic intelligence layer for Indian Gen Z and Gen Alpha.
Four agents. One orchestrator. One Reasoning Trace.
Built by Galaxy Brain at Thapar Institute for Samsung EnnovateX 2026.

Repo: github.com/ShAuRyA-Noodle/Combobulating

---

## Problem

The average Gen Z phone receives 237 notifications a day. Four matter.
The other 233 are taxes on attention nobody chose to pay.

Today's assistants make the noise easier to read. Aura makes the four
visible and the rest quiet.

The brief from Samsung EnnovateX 2026 asks for empathetic AI that
anticipates, integrates personal and contextual data, reduces cognitive
load, ensures privacy, and evolves with the user. It also asks for
verifiable raw evidence: 8 to 10 qualitative interviews, 30 to 50
quantitative users, real measurement methods, raw CSV in the open.

The current generation of assistants — Gemini Live, Apple Intelligence,
Bixby, Pixel Assistant, Rabbit, Humane, ChatGPT — are reactive. None
close the loop from on-device biometric signal to a transparent
autonomous action with a memory the user owns. That is the gap Aura
closes.

---

## Solution

Aura is a continuous, on-device orchestrator with four specialist agents:

- **CommsAgent.** Triages WhatsApp project groups, Gmail threads, and
  app notifications. Drafts replies on request. Never stores message bodies.
- **CalendarAgent.** Reconciles Google Calendar, EventKit, and travel
  time. Surfaces leave-by alerts. Detects conflicts.
- **FinanceAgent.** Parses UPI SMS, Gmail receipts from Zomato, Swiggy,
  Blinkit, IRCTC, Amazon. Projects month-end balance. Flags anomalies.
- **WellnessAgent.** Reads HRV, sleep, and step data via HealthKit
  on iOS, Health Connect on Android. Computes a composite Load Score.
  Suggests mute, breathe, or nap interventions.

A Phi-3-mini orchestrator, running as a deterministic LangGraph state
machine, ranks candidate actions and emits a Reasoning Trace for every
decision. Inter-agent communication is typed JSON — never free-form
chat.

Three product principles govern every surface:

1. **Anticipatory by default.** The user should not have to ask.
2. **Silent by design.** Every notification is a tax. Aura caps
   proactive surfaces at three per day, learnable down to zero. The
   Silence Budget is a first-class state variable in the orchestrator.
3. **Glass-box always.** Every action emits a Reasoning Trace —
   trigger, signals, candidates, ranking, chosen, rationale,
   confirm-required — that the user can inspect, edit, or reject.

---

## Architecture

Three layers: Sense, Intelligence, Experience.

Sense reads on-device signals only.
On Android, that is UsageStatsManager, NotificationListenerService,
SMS read permission, Health Connect, Calendar Provider, and a custom
IME for typing-entropy buckets — entropy only, never characters.
On iOS, that is HealthKit, EventKit, App Intents, and Background Tasks.
The plausibility table on slide 4a names the three iOS limits we live
with: SMS read does not exist, cross-app notifications are restricted
to the own-app channel, and DeviceActivity gives only partial app-launch
data. We do not pretend otherwise.

Intelligence runs four agents and one orchestrator on-device.
- CommsAgent: Gemma 2B Q4 with a LoRA adapter.
- FinanceAgent: Gemma 2B Q4 with a LoRA adapter.
- CalendarAgent: rule engine plus Phi-3-mini for prose.
- WellnessAgent: XGBoost regressor for the Load Score plus Phi-3-mini
  for intervention prose.
- Orchestrator: Phi-3-mini Q4 with a system prompt; LangGraph state
  machine across seven named states; typed JSON tool calls; hard cap
  of three proactive surfaces per day per user.

Experience surfaces are phone, watch, earbuds, and tablet.
Phone holds the Morning Brief card, the action card, the Reasoning
Trace drawer, and the Memory tab. Watch surfaces a one-line glance
with a single haptic. Earbuds whisper one TTS prompt per active
session. Tablet picks up cross-surface continuity via Multipeer
Connectivity on iOS, Nearby Connections on Android.

Memory lives in SQLite with sqlite-vss for embeddings, encrypted at
rest with iOS Secure Enclave or Android Keystore. Nine node types —
User, Event, App, Person, Place, Transaction, Conversation,
HealthSnapshot, Action, Trace. Eight edge types. One-tap export to JSON.
Per-day Merkle root for the audit log.

Production target is the Galaxy ecosystem. iOS reference build proves
cross-platform feasibility. We never claim a kernel hook we don't have.

---

## Evidence

We do not claim performance we have not measured.

Phase 2 publishes raw data:
- 30-user quantitative pilot from Thapar campus across years and
  branches, mixed gender, mixed hostel and day-scholar.
- 8-user qualitative pilot, 60-minute semi-structured interviews,
  daily diary entries.
- Five standardised tasks per user, randomised order, baseline
  measured first.

Six KPIs match the EnnovateX brief one-for-one:
- Effort reduction, target ≥30%, measured by stopwatch and tap count.
- Task completion, target ≥90%, measured by in-app telemetry.
- AI autonomy quality, target ≥85%, measured by three raters scoring
  100 random Aura actions on a Likert 1–5 with Cohen's kappa for
  inter-rater agreement.
- Satisfaction, target ≥4.5 of 5, measured by post-trial Likert.
- Stress reduction, measured qualitatively and by HRV trend with
  Spearman correlation against self-rated stress.
- Willingness to pay ₹199 a month, target ≥60%, measured by Van
  Westendorp.

Statistical reporting includes means with 95% confidence intervals,
paired t-test or Wilcoxon as appropriate, Cohen's d for effect size.
The full raw CSV publishes in the repo with the Phase 2 submission.

---

## Privacy

We do not promise unbreakable privacy. We promise the user owns their
data, can see it, can erase it, and that no byte leaves the device
without an explicit user-initiated action.

- All memory storage encrypted at rest with platform Keystore or
  Secure Enclave keys.
- No background cloud sync of personal data; sync only via
  user-initiated export.
- Reasoning Trace local-only.
- Optional panic-wipe gesture: five rapid presses of the side button
  wipes Aura memory and revokes OAuth tokens.
- Per-feature OAuth scopes minimised; revocation visible in Settings.
- Audit log tamper-evidence via a per-day Merkle root displayed in
  Settings.

The threat model covers six adversaries — curious app, lost or stolen
device, malicious notification listener, malicious accessibility
service, OS account compromise, parental coercion — with concrete
mitigations for each. See `docs/threat_model.md` in the repo.

---

## Team

Galaxy Brain. Two undergraduates at Thapar Institute of Engineering
and Technology, Patiala.

**Shaurya Punj** — third-year ECE. Owns architecture, the Wellness
agent, the KPI study, and pitch delivery. Roll 102486013.
**Shorya Gupta** — second-year Computer Engineering. Owns the iOS
app, the Comms / Calendar / Finance agents, and the memory graph
plus audit log. Roll 1024037521.

Both members are part of the user we design for: Indian Gen Z, hostel
resident, daily WhatsApp project groups, daily UPI, daily Zomato,
daily Insta. We are not interpreting from a focus group. We are the
focus group.

---

## FAQ

**Why on-device?**
Cloud assistants cannot see notifications, SMS, or HRV without
sending them off-device. On-device is the only architecture that lets
us see the signals that matter without becoming a surveillance product.
We accept the latency and model-size trade-off as a feature.

**Why four agents and not one bigger model?**
Specialisation lets each agent run the right model at the right size.
Gemma 2B for language, XGBoost for Load Score, a rule engine for
calendar conflicts. One unified LLM doing all four would be slower,
less testable, and less observable in the Reasoning Trace. The
four-agent shape also matches mental models the user already has —
Comms, Calendar, Finance, Wellness.

**You built this on iPhone. The hackathon is Samsung-judged.**
True. Production target is the Galaxy ecosystem. iOS is the
cross-platform reference build. Total budget is ₹2,000 — printing
plus buffer — which does not stretch to a flagship Galaxy phone.
The architecture is platform-agnostic; slide 4a maps every iOS API
1:1 to its Android counterpart. Phase 2 ports Comms and Wellness to
the Android emulator with Health Connect mocked from a synthetic HRV
trace recorded on Apple Watch. We frame the constraint up-front; we
do not apologise for it.

**How is Aura different from Gemini Live or Apple Intelligence?**
Five wedges shipped together: Indian context depth (UPI, IRCTC,
Zomato, Swiggy, Blinkit, BMTC), closed-loop biometric to action via
HRV, glass-box Reasoning Trace, Silence Budget as an instrumented
state variable, and a user-owned exportable memory graph with audit
log. Any incumbent can copy any one wedge in a quarter. Copying the
combination on top of an Indian context corpus is the moat.

**Is the Silence Budget just a notification cap?**
No. It is a cost function — `score = utility − notification_cost −
recent_action_penalty` — baked into the orchestrator's ranker. The
cap of three per day is a hard floor on the cost function, not the
function itself. The orchestrator learns per-user weights from
dismissal feedback. The budget is visible to the user and exposed in
the Reasoning Trace.

**What about hallucinations in autonomous actions?**
Two locks. First, every non-trivial autonomous action is
confirm-required by default. Second, inter-agent communication is
typed JSON validated against a schema; the LLM never produces
free-form prose to talk to another agent. The state machine has a
Cooldown state with a hard timeout, so a stuck transition reverts to
Idle within a defined window.

**Will you publish your weights?**
LoRA adapters trained on the Indian context corpus stay proprietary
during the hackathon. The orchestrator code, the Reasoning Trace
schema, the memory graph schema, the pilot protocol, the consent form,
and the raw CSV publish under MIT in the repo with Phase 2.

**How do I try it?**
Phase 2 ships a TestFlight build to 30 Thapar campus pilot
participants. If you are a Bangalore Gen Z user and would like to be
in the qualitative cohort, write to the address below.

---

## Contact

Shaurya Punj — spunj_be23@thapar.edu
Shorya Gupta — sgupta9_be24@thapar.edu
Repo — github.com/ShAuRyA-Noodle/Combobulating
EnnovateX — www.ennovatex.io

Thapar Institute of Engineering and Technology, Patiala.
