# LinkedIn Post — Aura, Galaxy Brain, EnnovateX 2026

Voice: plain narrative. Confident undergrad. No marketing voice.
No emojis. No exclamation marks. No banned words.
Word count: ~610.

---

We submitted Phase 1 of Samsung EnnovateX 2026 today. The product is
called Aura. The team is called Galaxy Brain. We are two
undergraduates at Thapar Institute of Engineering and Technology in
Patiala — Shaurya Punj, third-year ECE, and Shorya Gupta, second-year
Computer Engineering.

The brief asked for an empathetic intelligence user experience for
everyday life. The framing word everyone in our cohort latched onto
was "empathy". We spent two weeks deciding what that word would mean
operationally before we let ourselves write a slide. The answer we
landed on was three sentences. The right action at the right moment.
The courage to stay silent when no action serves the user. The
willingness to show your work.

Aura is the layer that closes the loop from on-device biometric and
behavioural signal to a transparent autonomous action with a memory
the user owns. Four specialist agents — Communications, Calendar,
Finance, Wellness — coordinated by a Phi-3-mini orchestrator running
on-device, on top of an encrypted local memory graph. Every action
emits a structured Reasoning Trace that the user can inspect, edit,
or reject. Inter-agent communication is typed JSON, never free-form
chat. The orchestrator runs as a deterministic LangGraph state
machine across seven named states. Models are quantised to Q4 and run
through MediaPipe LLM Inference on Android, MLX on iOS for
development, and llama.cpp as the cross-platform fallback.

We named five wedges in the deck. Indian life-OS depth — UPI, IRCTC,
BMTC, Gmail receipts from Zomato, Swiggy, Blinkit, Amazon. Closed-loop
biometric to action via HRV from HealthKit on iOS and Health Connect
on Android. Glass-box Reasoning Trace. A Silence Budget that caps
proactive surfaces at three per day per user, instrumented as a
first-class state variable in the orchestrator. A user-owned
exportable memory graph with a per-day Merkle root for the audit
log. Any incumbent can copy any one of these in a quarter. Copying
the combination on top of an Indian context corpus is the moat.

A constraint we wrote into the deck rather than hide. We are an
Apple-only build on a Samsung-judged hackathon. Total budget is
₹2,000 — printing plus buffer — which does not stretch to a flagship
Galaxy phone. We own iPhones, Apple Watches, AirPods, a Mac, and one
Alienware with an RTX 4080 for LoRA training. No cloud GPU spend, no
paid design tools, no incentives. Production target is the Galaxy
ecosystem; iOS is the cross-platform reference build. The
plausibility table on slide 4a maps every iOS API one-to-one to its
Android counterpart and names the three honest iOS limits we live
with — SMS read does not exist, cross-app notifications are
restricted to the own-app channel, and DeviceActivity gives only
partial app-launch data. We do not pretend otherwise. We frame the
constraint up-front as a credibility beat, not an apology.

Phase 2, if shortlisted, ships a TestFlight build to a 30-user
quantitative pilot from Thapar campus and an 8-user qualitative
cohort. We will publish the raw CSV with the Phase 2 submission. The
metric we want to be measured on is willingness to pay ₹199 a month
across the pilot — Van Westendorp, target sixty percent.

Repo: github.com/ShAuRyA-Noodle/Combobulating
Deck: deck/phase1_blueprint/

Thapar Institute of Engineering and Technology, Patiala.

Onwards.

— Shaurya Punj and Shorya Gupta, Galaxy Brain.
