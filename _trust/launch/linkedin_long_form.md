# LinkedIn Long-Form — Aura v1.0.0

Audience: Indian engineering leads, product managers, design directors,
ML engineers, hackathon community, Samsung partner ecosystem. Voice:
honest undergrad register, no banned words, no hype, citations to real
artefacts in the repo. Target length: ~1,500 words.

Banner image: `aura_20_social_linkedin_banner.png`.

---

## Title

We just shipped Aura v1.0.0 — an on-device empathetic intelligence layer for Indian Gen Z, on a ₹2,000 budget.

---

## Body

We are Shaurya Punj and Shorya Gupta. Two undergraduates at Thapar
Institute of Engineering and Technology in Patiala. Today we are
launching v1.0.0 of Aura, the project we have been quietly building
for the Samsung EnnovateX 2026 hackathon, and which we are now also
shipping as a real product the public can read, install, and audit.
This post is the long version of why it exists, the design decisions
behind it, the constraints we built it inside, and the road ahead.

The repository is at github.com/ShAuRyA-Noodle/Combobulating. The site
lives at shaurya-noodle.github.io/Combobulating. The Gradio demo is at
huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin.

### The friction we set out to answer

The average Indian Gen Z phone receives 237 notifications a day. The
number comes from Common Sense Media's 2023 Constant Companion study.
Four of those buzzes matter. The other 233 are a tax on attention
nobody chose to pay. Our hostel rooms, our group projects, our UPI
debit alerts, our Zomato confirmations — every screen reaches for
attention like the reach is free.

Today's assistants make the noise easier to read. Gemini Live, Apple
Intelligence, Bixby, Pixel Assistant, Rabbit, Humane, ChatGPT — they
all start when the user starts. None of them sees HRV, none reads the
WhatsApp project group, none parses a UPI SMS, and none exposes a
step-by-step trace of what it decided and why. The user is left to
trust a black box, or to keep doing the work by hand.

Aura is the layer that closes the loop from on-device signal to a
single quiet action, and stays silent the rest of the time. Four
agents, one orchestrator, a Reasoning Trace the user can read and
edit, a memory graph the user owns. Nothing leaves the device unless
the user presses export.

### The five product wedges, shipped together

Aura is a single product because we ship five wedges together that
the incumbents have not. Any one wedge is copyable in a quarter. The
combination, on top of an Indian context corpus, is the moat.

**Wedge 1 — Indian context, not bolt-on.** Twelve bank SMS templates
on the hot path. A UPI debit parser. IRCTC PNR lookup. Zomato, Swiggy,
Blinkit, BMTC, Amazon. Gmail thread reconciliation. The Spend Mirror
screen does not ask the user to categorise; it reads the receipts the
user already received.

**Wedge 2 — Closed biometric loop.** HealthKit on iOS, Health Connect
on Android. HRV, sleep, steps. An XGBoost regressor produces a Load
Score that, past a threshold, triggers exactly one quiet intervention:
mute, breathe, or nap. Wellness actions are reversible and do not
spend the Silence Budget.

**Wedge 3 — Glass-box Reasoning Trace.** Every Aura action emits a
Reasoning Trace with eight fields: trigger, signals, candidates,
ranking, chosen, rationale, confirm-required, outcome. The user can
inspect, edit the chosen action, reject the trace, or rewind. We do
not believe in black boxes for an autonomous layer on a personal phone.

**Wedge 4 — Silence as a feature.** A named state variable, the
Silence Budget, caps proactive non-safety surfaces at three per local
day. Each surface decrements the budget by one token. Tapping
"Useful" on a card refunds one token, capped at the daily ceiling.
The cap is a hard floor on a learned cost function, not the function
itself. The default is configurable from one to five.

**Wedge 5 — Owned memory graph.** SQLite plus sqlite-vss for
embeddings, encrypted at rest with the iOS Secure Enclave or Android
Keystore. Nine node types, eight edge types. One tap to export to
JSON, time-range delete, panic-wipe gesture, daily Merkle root for
audit tamper-evidence.

### The architecture decisions we are most proud of

We documented every non-trivial decision as an Architecture Decision
Record. Eleven ADRs, in the repo at `docs/decisions/`. Three of them
shaped everything else.

**ADR-0003 — Silence Budget as a first-class state variable.** Most
notification caps are after-the-fact filters. Aura's cap is inside
the orchestrator's ranker, exposed in the Reasoning Trace, and visible
to the user as three small dots in Settings. It is the difference
between a product that has a quiet mode and a product whose default
posture is quiet.

**ADR-0004 — Glass-box Reasoning Trace.** A schema fixed in
`trace.v1.json`, a five-section drawer UI, retention thirty days by
default. We refused to ship an autonomous action that could not show
its work. The user can edit the rationale string before approving.

**ADR-0009 — Typed JSON tool calls.** The four agents and the
orchestrator never produce free-form prose to talk to each other.
Every inter-agent message is a typed JSON tool call validated against
a schema. This is the single biggest hallucination defence we have.
The state machine has a Cooldown state with a hard timeout so a
stuck transition reverts to Idle within a defined window.

The full ADR list also covers the orchestrator model (Phi-3-mini Q4),
the on-device-only invariant, the platform strategy (iOS as the
cross-platform reference, Galaxy as the production target), the
memory encryption scheme, the LangGraph state machine, the pilot
protocol, and the no-Apple-Developer-Program path that lets evaluators
sideload via a free Apple ID.

### The constraints, said up front

We named the box we built in inside the deck, and we name it again
here.

Two-person team. No advisors, no contractors, no faculty mentor. A
₹2,000 total budget — print plus buffer. No flagship Galaxy phone in
the lab. No paid Apple Developer Program. No cloud GPU. A twelve-week
runway across Phase 1 blueprint, Phase 2 pilot, Phase 3 demo.

We frame those constraints because they shaped the product. The
Wizard-of-Oz pilot exists because we cannot afford a TestFlight cohort
of fifty. The free Apple ID install exists because we cannot afford
an Apple Developer Program for evaluators. The HuggingFace Space exists
because the free CPU tier is the only way we can show a live demo
without a server bill. The Galaxy emulator port stands ready for the
day a venue device shows up.

These are not apologies. They are the design space.

### Pilot study — Wizard-of-Oz, with raw CSV at the end

The Phase 2 pilot is a Wizard-of-Oz study at Thapar campus. Thirty
quantitative users across years and branches. Eight qualitative users
in sixty-minute semi-structured interviews. A human operator drives
the orchestrator behind a 2.5-second p95 latency budget while the user
sees only the action card and the Reasoning Trace. Five standardised
tasks, randomised order, baseline measured first.

Six pre-registered KPIs that match the EnnovateX brief one-for-one.
Effort reduction at least 30 percent, measured by stopwatch and tap
count. Task completion at least 90 percent, measured by in-app
telemetry. Autonomy quality at least 85 percent, measured by three
raters scoring 100 random Aura actions on a Likert scale with
Cohen's kappa. Satisfaction at least 4.5 of 5. Stress reduction by
HRV trend with Spearman correlation against self-rated stress.
Willingness to pay ₹199 a month at least 60 percent, measured by
Van Westendorp.

Statistical reporting includes 95 percent confidence intervals, paired
Wilcoxon, and Cohen's d. The full raw CSV publishes in the repo at
the Phase 2 minor cut.

### Privacy — five plain-English promises

We do not promise unbreakable privacy. We promise the user owns their
data, can see it, can erase it, and that no byte leaves the device
without an explicit user-initiated action. The five promises are on
the site at `/privacy.html`. Each is tested against a documented
threat model with five named adversaries — curious app, lost device,
malicious notification listener, OS account compromise, parental
coercion — and tied to a specific architecture commitment.

The panic-wipe gesture (five rapid presses of the side button within
three seconds) destroys the SQLCipher key, revokes OAuth refresh
tokens, deletes the app sandbox, and relaunches Aura into fresh-install
state. There is a three-second hold-cancel window. Nothing is logged
about the wipe — that absence is a feature.

### The road ahead

Phase 2 lands the pilot data and the LoRA adapters. The plan is to
publish the raw CSV, the LoRA training logs, and a Galaxy emulator
port of the Comms and Wellness agents. Phase 3 is the Bangalore finals
demo, which we have scaffolded under `phase3/` with travel logistics,
stage kit, and contingency plans.

Beyond the hackathon, we are looking for a small group of pilot users
in Bangalore and Patiala who would like to be in the qualitative
cohort. We are also open to short conversations with anyone working
on on-device ML, on-device privacy, or Indian context corpora.

If you read this far, thank you. The repo is open and MIT licensed at
github.com/ShAuRyA-Noodle/Combobulating. The site has the install
guide at shaurya-noodle.github.io/Combobulating/install.html. The
press kit is at `press_kit/` in the repo, building from a single bash
script. We are at spunj_be23@thapar.edu and sgupta9_be24@thapar.edu.

— Shaurya Punj, Shorya Gupta. Galaxy Brain. Thapar Institute, Patiala.

(Word count: approximately 1,510.)
